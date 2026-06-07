import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";

import "./styles.css";
import {
  api,
  ApiError,
  isUnauthorized,
  makeJudgeSocket,
  streamAdminAgentRun,
  type AdminSolution,
  type AdminSolutionPayload,
  type AdminTestCase,
  type AdminAgentActionResponse,
  type AgentRun,
  type AgentSession,
  type AgentStep,
  type AdminAgentStreamEvent,
  type AIModelProfile,
  type AIProfile,
  type CurrentUser,
  type ProblemDraft,
  type ProblemFilters,
} from "./lib/api";
import {
  type AIExplain,
  type AIChat,
  type AIHint,
  type AIReview,
  type ProblemDetail,
  type ProblemDiscussion,
  type ProblemListItem,
  type SubmissionDetail,
} from "./lib/schemas";
import {
  buildStarter,
  getFunctionSpec,
  getLocalizedFunctionDescription,
  getProblemMode,
  getVisualSpec,
  isLikelyStaleAcmDraft,
  type JudgeMode,
} from "./lib/problemModes";
import {
  canonicalTagQuery,
  getUI,
  htmlLangForLocale,
  LOCALE_META,
  localizeDifficulty,
  localizeTag,
  localizeTags,
  localeLabel,
  localeText,
  localeValue,
  localizedProblem,
  matchesLocalizedProblem,
  nextLocale,
  normalizeLocale,
  readStoredLocale,
  SUPPORTED_LOCALES,
  type Locale,
  verdictInfo,
  writeStoredLocale,
} from "./lib/i18n";
import { measureTrainingText } from "./lib/textLayout";
import { LANGUAGES, useAppStore } from "./stores/useAppStore";
import type { JudgeEvent } from "./components/JudgeTimeline";
import type { EditableRunCase, RunSnapshot } from "./components/RunResultPanel";
import { MarkdownBlock } from "./components/MarkdownBlock";

const queryClient = new QueryClient();

const CONTENT_PERMISSIONS = {
  createOwnProblem: "problem:create_own",
  updateOwnProblem: "problem:update_own",
  publishOwnProblem: "problem:publish_own",
  manageUsers: "user:manage",
  moderateDiscussion: "discussion:moderate",
} as const;

function hasContentPermission(user: CurrentUser | null, permission: string): boolean {
  if (!user) return false;
  if (user.role === "admin") return true;
  if (user.role !== "content_admin") return false;
  return (user.content_admin_permissions ?? []).includes(permission);
}

function canAccessAdmin(user: CurrentUser | null): boolean {
  return Boolean(user?.role === "admin" || (user?.role === "content_admin" && (user.content_admin_permissions ?? []).length > 0));
}

function roleLabel(role: string, locale: Locale): string {
  if (role === "admin") return localeText(locale, { zh: "最高管理员", en: "Admin" });
  if (role === "content_admin") return localeText(locale, { zh: "内容管理员", en: "Content admin" });
  return localeText(locale, { zh: "用户", en: "User" });
}

function contentPermissionLabel(permission: string, locale: Locale): string {
  const labels: Record<string, { zh: string; en: string }> = {
    [CONTENT_PERMISSIONS.createOwnProblem]: { zh: "增加自己的题目", en: "Create own problems" },
    [CONTENT_PERMISSIONS.updateOwnProblem]: { zh: "修改自己的题目", en: "Edit own problems" },
    [CONTENT_PERMISSIONS.publishOwnProblem]: { zh: "发布自己的题目", en: "Publish own problems" },
    [CONTENT_PERMISSIONS.manageUsers]: { zh: "管理用户账号", en: "Manage users" },
    [CONTENT_PERMISSIONS.moderateDiscussion]: { zh: "删除不当讨论", en: "Moderate discussion" },
  };
  return localeText(locale, labels[permission] ?? { zh: permission, en: permission });
}

function togglePermission(list: string[] | undefined, permission: string): string[] {
  const current = list ?? [];
  return current.includes(permission) ? current.filter((item) => item !== permission) : [...current, permission];
}

const AICopilotPanel = React.lazy(() =>
  import("./components/AICopilotPanel").then(({ AICopilotPanel }) => ({ default: AICopilotPanel })),
);
const AuthPage = React.lazy(() =>
  import("./components/AuthPages").then(({ AuthPage }) => ({ default: AuthPage })),
);
const CodeBlock = React.lazy(() =>
  import("./components/CodeBlock").then(({ CodeBlock }) => ({ default: CodeBlock })),
);
const CodeEditor = React.lazy(() =>
  import("./components/CodeEditor").then(({ CodeEditor }) => ({ default: CodeEditor })),
);
const JudgeTimeline = React.lazy(() =>
  import("./components/JudgeTimeline").then(({ JudgeTimeline }) => ({ default: JudgeTimeline })),
);
const RunResultPanel = React.lazy(() =>
  import("./components/RunResultPanel").then(({ RunResultPanel }) => ({ default: RunResultPanel })),
);
const SettingsPage = React.lazy(() =>
  import("./components/AuthPages").then(({ SettingsPage }) => ({ default: SettingsPage })),
);
const SubmissionTrail = React.lazy(() =>
  import("./components/SubmissionTrail").then(({ SubmissionTrail }) => ({ default: SubmissionTrail })),
);
const TrainingGraph = React.lazy(() =>
  import("./components/TrainingGraph").then(({ TrainingGraph }) => ({ default: TrainingGraph })),
);

type View = "library" | "workbench" | "graph" | "auth" | "settings" | "admin";
type DetailTab = "cases" | "solution" | "judge" | "trail" | "discussion";
type AuthMode = "login" | "register";
type LibraryLayout = "card" | "list";
type AppTheme = "light" | "dark";
type ProblemAuthoringMode = "function" | "acm" | "both";
type AgentTab = "authoring" | "import";
type AdminSection = "agent" | "users" | "problems";
type AIChatLine = { id: string; role: "user" | "assistant"; message: string; suggestions?: string[] };
type AgentFollowUpLine = { id: string; role: "user" | "assistant"; message: string; runId?: string | null };
type DraftEditCase = {
  input: string;
  output: string;
  explanation: string;
  io_metadata?: Record<string, any> | null;
  is_hidden: boolean;
  is_sample: boolean;
  order: number;
};
type DraftOfficialSolution = {
  language: string;
  code: string;
  explanation: string;
  acm_code?: string | null;
  function_code?: string | null;
};
type ProblemSolutionEdit = DraftOfficialSolution & {
  time_complexity: string;
  space_complexity: string;
};
type DraftEditState = {
  title: string;
  slug: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string;
  mode: ProblemAuthoringMode;
  target_languages: string[];
  input_format: string;
  output_format: string;
  function_signature: string;
  time_limit: string;
  memory_limit: string;
  hint: string;
  official_solutions: DraftOfficialSolution[];
  time_complexity: string;
  space_complexity: string;
  testcases: DraftEditCase[];
};
type ProblemEditState = {
  title: string;
  slug: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string;
  mode: ProblemAuthoringMode;
  input_format: string;
  output_format: string;
  function_signature: string;
  time_limit: string;
  memory_limit: string;
  hint: string;
  solutions: ProblemSolutionEdit[];
};

const AI_PROFILE_FALLBACKS: Record<AIModelProfile, AIProfile> = {
  default: {
    value: "default",
    label_zh: "自动选择",
    label_en: "Auto route",
    detail_zh: "使用服务器当前可用的 AI 配置",
    detail_en: "Use the currently available server AI profile",
    configured: false,
    available: false,
    reason: null,
    checked_at: null,
  },
  deepseek: {
    value: "deepseek",
    label_zh: "DeepSeek 云端",
    label_en: "DeepSeek Cloud",
    detail_zh: "调用 DeepSeek 兼容接口",
    detail_en: "Use the DeepSeek-compatible API",
    configured: false,
    available: false,
    reason: null,
    checked_at: null,
  },
  "deepseek-pro": {
    value: "deepseek-pro",
    label_zh: "DeepSeek Pro",
    label_en: "DeepSeek Pro",
    detail_zh: "调用 DeepSeek Pro 长上下文/强模型配置，适合管理员出题和导入题目",
    detail_en: "Use the DeepSeek Pro long-context strong-model profile for admin authoring and imports",
    configured: false,
    available: false,
    reason: null,
    checked_at: null,
  },
  "qwen-local": {
    value: "qwen-local",
    label_zh: "Qwen 本地",
    label_en: "Local Qwen",
    detail_zh: "连接本机兼容 OpenAI 接口的服务",
    detail_en: "Use a local OpenAI-compatible Qwen server",
    configured: false,
    available: false,
    reason: null,
    checked_at: null,
  },
};

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const percent = (value: number) => Math.round(clamp(value, 0, 1) * 100);
const MAX_RUN_CASES = 8;
const DEFAULT_LEFT_PANEL_WIDTH = 390;
const DEFAULT_RIGHT_PANEL_WIDTH = 430;
const DEFAULT_EDITOR_HEIGHT = 390;
const DEFAULT_AGENT_LEFT_DRAWER_WIDTH = 300;
const DEFAULT_AGENT_RIGHT_DRAWER_WIDTH = 540;
const SIDE_PANEL_SNAP_WIDTH = 88;
const SIDE_PANEL_DRAG_MIN = 56;
const AGENT_DRAWER_RAIL_WIDTH = 30;
const AGENT_LEFT_DRAWER_MIN = 220;
const AGENT_LEFT_DRAWER_MAX = 520;
const AGENT_LEFT_DRAWER_SNAP = 180;
const AGENT_RIGHT_DRAWER_MIN = 360;
const AGENT_RIGHT_DRAWER_MAX = 760;
const AGENT_RIGHT_DRAWER_SNAP = 300;
const EDITOR_MIN_HEIGHT = 260;
const EDITOR_MAX_HEIGHT = 720;

function runCasesFromProblem(problem?: ProblemDetail): EditableRunCase[] {
  const samples = problem?.sample_testcases ?? [];
  if (!samples.length) return [{ id: "case-1", input: "", expected_output: "" }];
  return samples.slice(0, MAX_RUN_CASES).map((item, index) => ({
    id: `sample-${problem?.id ?? "problem"}-${index + 1}`,
    input: item.input,
    expected_output: item.output,
  }));
}

function ensureRunCases(cases: EditableRunCase[]): EditableRunCase[] {
  const source = cases.length ? cases : [{ id: "case-1", input: "", expected_output: "" }];
  return source.slice(0, MAX_RUN_CASES).map((item, index) => ({
    id: item.id || `case-${index + 1}`,
    input: item.input,
    expected_output: item.expected_output,
  }));
}

function IconGlyph({ children }: { children: React.ReactNode }) {
  return <span className="icon-glyph" aria-hidden="true">{children}</span>;
}

function ResetTemplateIcon() {
  return (
    <svg className="reset-template-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5.4 9.2a7.2 7.2 0 1 1 1.2 6.9" />
      <path d="M5.4 9.2H2.2V6" />
    </svg>
  );
}

function PanelToggleIcon({ open, side }: { open: boolean; side: "left" | "right" }) {
  return <span aria-hidden="true">{open ? (side === "left" ? "<" : ">") : side === "left" ? ">" : "<"}</span>;
}

function AuthBar({
  view,
  authenticated,
  currentUser,
  locale,
  theme,
  onView,
  onAuth,
  onLogout,
  onLocale,
  onTheme,
}: {
  view: View;
  authenticated: boolean;
  currentUser: CurrentUser | null;
  locale: Locale;
  theme: AppTheme;
  onView: (view: View) => void;
  onAuth: (mode: AuthMode) => void;
  onLogout: () => void;
  onLocale: () => void;
  onTheme: (theme: AppTheme) => void;
}) {
  const text = getUI(locale);
  const nextUiLocale = nextLocale(locale);
  return (
    <header className="topbar">
      <button className="brand-lockup brand-button" title={localeText(locale, { zh: "返回题库首页", en: "Back to problem library" })} onClick={() => onView("library")}>
        <strong>FastOJ</strong>
        <span>{localeText(locale, { zh: "AI 练习判题", en: "AI interview judge" })}</span>
      </button>
      <div className="theme-switch segmented" role="group" aria-label={localeText(locale, { zh: "界面主题", en: "Theme" })}>
        <button type="button" className={theme === "light" ? "active" : ""} aria-pressed={theme === "light"} onClick={() => onTheme("light")}>
          {localeText(locale, { zh: "浅色", en: "Light" })}
        </button>
        <button type="button" className={theme === "dark" ? "active" : ""} aria-pressed={theme === "dark"} onClick={() => onTheme("dark")}>
          {localeText(locale, { zh: "深色", en: "Dark" })}
        </button>
      </div>
      <nav className="topnav" aria-label={localeText(locale, { zh: "主导航", en: "Main navigation" })}>
        <button className={view === "library" ? "active" : ""} onClick={() => onView("library")}>{text.navLibrary}</button>
        <button className={view === "workbench" ? "active" : ""} onClick={() => onView("workbench")}>{text.navWorkbench}</button>
        <button className={view === "graph" ? "active" : ""} onClick={() => onView("graph")}>{text.navGraph}</button>
      </nav>
      <div className="authbar">
        <button
          className="icon-button locale-button tip"
          data-tip={localeText(locale, { zh: `切换到${localeLabel(nextUiLocale)}`, en: `Switch to ${localeLabel(nextUiLocale)}` })}
          onClick={onLocale}
        >
          {LOCALE_META[nextUiLocale].shortLabel}
        </button>
        {authenticated ? (
          <>
            <span className="auth-state">{text.loggedIn}</span>
            {canAccessAdmin(currentUser) ? (
              <button className={view === "admin" ? "icon-button active tip" : "icon-button tip"} data-tip={localeText(locale, { zh: "管理后台", en: "Admin" })} onClick={() => onView("admin")}>
                <IconGlyph>A</IconGlyph>
              </button>
            ) : null}
            <button className={view === "settings" ? "icon-button active tip" : "icon-button tip"} data-tip={text.navSettings} onClick={() => onView("settings")}>
              <IconGlyph>*</IconGlyph>
            </button>
            <button onClick={onLogout}>{text.logout}</button>
          </>
        ) : (
          <>
            <button className={view === "auth" ? "active" : ""} onClick={() => onAuth("login")}>{text.login}</button>
            <button className="primary" onClick={() => onAuth("register")}>{text.register}</button>
          </>
        )}
      </div>
    </header>
  );
}

function DifficultyDropdown({
  value,
  locale,
  onChange,
}: {
  value: string;
  locale: Locale;
  onChange: (value: string) => void;
}) {
  const text = getUI(locale);
  const [open, setOpen] = useState(false);
  const options = [
    { value: "", label: text.allDifficulty },
    { value: "easy", label: localizeDifficulty("easy", locale) },
    { value: "medium", label: localizeDifficulty("medium", locale) },
    { value: "hard", label: localizeDifficulty("hard", locale) },
  ];
  const selected = options.find((item) => item.value === value) ?? options[0];
  return (
    <div
      className={`custom-select ${open ? "open" : ""}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button type="button" className="custom-select-button" title={localeText(locale, { zh: "选择难度", en: "Choose difficulty" })} onClick={() => setOpen((current) => !current)}>
        <span>{selected.label}</span>
        <span aria-hidden="true">v</span>
      </button>
      <div className="custom-select-menu" role="listbox">
        {options.map((item) => (
          <button
            type="button"
            role="option"
            aria-selected={item.value === value}
            className={item.value === value ? "selected" : ""}
            key={item.value || "all"}
            onClick={() => {
              onChange(item.value);
              setOpen(false);
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function aiProfileLabel(profile: AIProfile, locale: Locale) {
  return localeText(locale, { zh: profile.label_zh, en: profile.label_en });
}

function aiProfileDetail(profile: AIProfile, locale: Locale) {
  return localeText(locale, { zh: profile.detail_zh, en: profile.detail_en });
}

function aiUnavailableText(locale: Locale, reason?: string | null) {
  const base = localeText(locale, { zh: "AI 未配置或不可用", en: "AI is not configured or unavailable" });
  return reason ? `${base}: ${reason}` : `${base}.`;
}

function preferredAIProfile(profiles: AIProfile[]): AIModelProfile | null {
  const available = profiles.filter((profile) => profile.available);
  return available.find((profile) => profile.value === "default")?.value ?? available[0]?.value ?? null;
}

function preferredAdminAIProfile(profiles: AIProfile[]): AIModelProfile | null {
  const available = profiles.filter((profile) => profile.available);
  return (
    available.find((profile) => profile.value === "deepseek-pro")?.value
    ?? available.find((profile) => profile.value === "default")?.value
    ?? available.find((profile) => profile.value === "deepseek")?.value
    ?? available[0]?.value
    ?? null
  );
}

function AIModelDropdown({
  value,
  locale,
  onChange,
  profiles,
  disabledReason,
}: {
  value: AIModelProfile;
  locale: Locale;
  onChange: (value: AIModelProfile) => void;
  profiles: AIProfile[];
  disabledReason?: string | null;
}) {
  const [open, setOpen] = useState(false);
  const options = profiles.filter((profile) => profile.available);
  const selected = options.find((item) => item.value === value) ?? AI_PROFILE_FALLBACKS[value] ?? AI_PROFILE_FALLBACKS.default;
  const label = disabledReason ? localeText(locale, { zh: "AI 不可用", en: "AI unavailable" }) : aiProfileLabel(selected, locale);
  const detail = disabledReason ?? aiProfileDetail(selected, locale);
  return (
    <div
      className={`custom-select ai-model-picker ${open ? "open" : ""}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button type="button" className="custom-select-button model-select-button" title={detail} disabled={Boolean(disabledReason)} onClick={() => setOpen((current) => !current)}>
        <span className="model-spark" aria-hidden="true">✦</span>
        <span className="model-copy">
          <strong>{label}</strong>
          <small>{detail}</small>
        </span>
        <span aria-hidden="true">⌄</span>
      </button>
      <div className="custom-select-menu model-select-menu" role="listbox">
        {options.map((item) => {
          const itemLabel = aiProfileLabel(item, locale);
          const itemDetail = aiProfileDetail(item, locale);
          return (
            <button
              type="button"
              role="option"
              aria-selected={item.value === value}
              className={item.value === value ? "selected" : ""}
              key={item.value}
              onClick={() => {
                onChange(item.value);
                setOpen(false);
              }}
            >
              <span>{itemLabel}</span>
              <small>{itemDetail}</small>
            </button>
          );
        })}
        {!options.length ? (
          <button type="button" disabled>
            <span>{localeText(locale, { zh: "无可用模型", en: "No available model" })}</span>
            <small>{disabledReason ?? localeText(locale, { zh: "请检查 AI 配置", en: "Check AI configuration" })}</small>
          </button>
        ) : null}
      </div>
    </div>
  );
}

function LibraryPage({
  selectedId,
  selectedTag,
  locale,
  onSelect,
  onGraph,
}: {
  selectedId: string | null;
  selectedTag: string;
  locale: Locale;
  onSelect: (id: string) => void;
  onGraph: () => void;
}) {
  const text = getUI(locale);
  const [keyword, setKeyword] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [tags, setTags] = useState(selectedTag);
  const [page, setPage] = useState(1);
  const [layout, setLayout] = useState<LibraryLayout>(() => {
    const saved = localStorage.getItem("fastoj.libraryLayout");
    return saved === "list" || saved === "card" ? saved : "card";
  });
  const [sidebarOpen, setSidebarOpen] = useState(() => localStorage.getItem("fastoj.librarySidebarOpen") !== "false");
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = Number(localStorage.getItem("fastoj.librarySidebarWidth") ?? 218);
    return clamp(Number.isFinite(saved) ? saved : 218, 176, 320);
  });
  const [sidebarResizing, setSidebarResizing] = useState(false);

  useEffect(() => {
    setTags(selectedTag);
    setPage(1);
  }, [selectedTag]);

  useEffect(() => {
    localStorage.setItem("fastoj.libraryLayout", layout);
  }, [layout]);

  useEffect(() => {
    localStorage.setItem("fastoj.librarySidebarOpen", String(sidebarOpen));
  }, [sidebarOpen]);

  useEffect(() => {
    localStorage.setItem("fastoj.librarySidebarWidth", String(sidebarWidth));
  }, [sidebarWidth]);

  const trimmedKeyword = keyword.trim();
  const needsLocalizedSearch = !LOCALE_META[locale].sourceText && Array.from(trimmedKeyword).some((char) => char.charCodeAt(0) > 127);
  const filters: ProblemFilters = { keyword: needsLocalizedSearch ? "" : keyword, difficulty, tags: canonicalTagQuery(tags, locale), page };
  const problemsQuery = useQuery({
    queryKey: ["problems", filters, needsLocalizedSearch],
    queryFn: async () => {
      if (!needsLocalizedSearch) return api.problems(filters);
      const localizedFilters = { ...filters, page: 1, page_size: 100 };
      const [firstPage, secondPage] = await Promise.all([
        api.problems(localizedFilters),
        api.problems({ ...localizedFilters, page: 2 }),
      ]);
      const seen = new Set<string>();
      return [...firstPage, ...secondPage].filter((item) => {
        if (seen.has(item.id)) return false;
        seen.add(item.id);
        return true;
      });
    },
  });
  const problems = (problemsQuery.data ?? []).filter((problem) => matchesLocalizedProblem(problem, locale, keyword));
  const aiCount = problems.filter((problem) => getProblemMode(problem).isAiPractice).length;
  const functionCount = problems.filter((problem) => getProblemMode(problem).supportsFunction).length;
  const averageAc = problems.length
    ? percent(problems.reduce((sum, problem) => sum + clamp(problem.ac_rate, 0, 1), 0) / problems.length)
    : 0;
  const recommendation = problems.find((problem) => problem.ac_rate < 0.45) ?? problems[0];

  function resetFilters() {
    setKeyword("");
    setDifficulty("");
    setTags("");
    setPage(1);
  }

  function startSidebarResize(event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = sidebarWidth;
    setSidebarResizing(true);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    const onMove = (moveEvent: PointerEvent) => {
      setSidebarWidth(clamp(startWidth + moveEvent.clientX - startX, 176, 320));
    };
    const onUp = () => {
      setSidebarResizing(false);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  const libraryStyle = {
    "--library-sidebar": sidebarOpen ? `${sidebarWidth}px` : "46px",
  } as React.CSSProperties;

  return (
    <main className={`library-page ${sidebarOpen ? "" : "library-sidebar-collapsed"} ${sidebarResizing ? "is-resizing" : ""}`} style={libraryStyle}>
      <aside className="library-sidebar">
        <div className="library-sidebar-header">
          <button
            className="icon-button library-sidebar-toggle"
            aria-label={sidebarOpen
              ? localeText(locale, { zh: "收起筛选", en: "Collapse filters" })
              : localeText(locale, { zh: "展开筛选", en: "Expand filters" })}
            aria-expanded={sidebarOpen}
            onClick={() => setSidebarOpen((value) => !value)}
          >
            <PanelToggleIcon open={sidebarOpen} side="left" />
          </button>
          <strong className="library-sidebar-title" aria-hidden={!sidebarOpen}>{text.filters}</strong>
        </div>
        <div className="library-sidebar-content" aria-hidden={!sidebarOpen}>
          <div className="filter-group">
            <input placeholder={text.keyword} value={keyword} onChange={(event) => { setKeyword(event.target.value); setPage(1); }} tabIndex={sidebarOpen ? 0 : -1} />
            <DifficultyDropdown value={difficulty} locale={locale} onChange={(value) => { setDifficulty(value); setPage(1); }} />
            <input placeholder={text.tagsPlaceholder} value={tags} onChange={(event) => { setTags(event.target.value); setPage(1); }} tabIndex={sidebarOpen ? 0 : -1} />
            <button title={text.resetFilters} onClick={resetFilters} tabIndex={sidebarOpen ? 0 : -1}>{text.resetFilters}</button>
          </div>
          <div className="side-metrics">
            <Metric label={text.currentProblems} value={problems.length} />
            <Metric label={text.functionMode} value={functionCount} />
            <Metric label={text.aiAlgorithms} value={aiCount} />
            <Metric label={text.averageAc} value={`${averageAc}%`} />
          </div>
        </div>
        <span className="library-sidebar-rail" aria-hidden={sidebarOpen}>{text.filters}</span>
        <div
          className="library-sidebar-resize"
          role="separator"
          aria-label={localeText(locale, { zh: "调整筛选栏宽度", en: "Resize filters" })}
          title={localeText(locale, { zh: "拖动调整筛选栏宽度", en: "Drag to resize filters" })}
          onPointerDown={(event) => sidebarOpen && startSidebarResize(event)}
        />
      </aside>
      <section className="library-main">
        <div className="library-header">
          <div>
            <p className="eyebrow">{localeText(locale, { zh: "题库集合", en: "Problem set" })}</p>
            <h1>{text.library}</h1>
            <p className="muted">{text.libraryCopy}</p>
          </div>
          <div className="recommendation">
            <span>{text.recommendation}</span>
            <strong>{localizedProblem(recommendation, locale)?.title ?? localeText(locale, { zh: "暂无题目", en: "No problem" })}</strong>
            <button disabled={!recommendation} onClick={() => recommendation && onSelect(recommendation.id)}>{text.start}</button>
            <button onClick={onGraph}>{text.graph}</button>
          </div>
        </div>
        <div className="library-controls">
          <span className="muted">{text.layout}</span>
          <div className="segmented layout-toggle" role="group" aria-label={text.layoutOptions}>
            <button className={layout === "card" ? "active" : ""} aria-pressed={layout === "card"} onClick={() => setLayout("card")}>
              {text.cardLayout}
            </button>
            <button className={layout === "list" ? "active" : ""} aria-pressed={layout === "list"} onClick={() => setLayout("list")}>
              {text.listLayout}
            </button>
          </div>
        </div>
        <div className={layout === "list" ? "problem-list problem-list-rows" : "problem-list"} aria-label={localeText(locale, { zh: "题目列表", en: "Problem list" })}>
          {problemsQuery.isLoading ? <p className="muted">{localeText(locale, { zh: "加载题库中...", en: "Loading problems..." })}</p> : null}
          {problems.map((problem) => (
            layout === "list"
              ? <ProblemRow key={problem.id} problem={problem} locale={locale} active={problem.id === selectedId} onSelect={() => onSelect(problem.id)} />
              : <ProblemCard key={problem.id} problem={problem} locale={locale} active={problem.id === selectedId} onSelect={() => onSelect(problem.id)} />
          ))}
        </div>
        <div className="pager">
          <button disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>{text.previous}</button>
          <span>{text.page} {page}</span>
          <button disabled={problems.length === 0} onClick={() => setPage((value) => value + 1)}>{text.next}</button>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return <div className="metric"><strong>{value}</strong><span>{label}</span></div>;
}

function ProblemModeBadges({ problem, locale }: { problem: ProblemListItem; locale: Locale }) {
  const text = getUI(locale);
  const mode = getProblemMode(problem);
  return (
    <>
      {mode.supportsFunction ? <span>{text.functionMode}</span> : null}
      {mode.supportsAcm ? <span>{text.acmMode}</span> : null}
      {mode.isAiPractice ? <span>{text.aiAlgorithms}</span> : null}
    </>
  );
}

function ProblemCard({ problem, locale, active, onSelect }: { problem: ProblemListItem; locale: Locale; active: boolean; onSelect: () => void }) {
  const displayProblem = localizedProblem(problem, locale);
  const text = getUI(locale);
  const titleLayout = measureTrainingText(`${displayProblem.title} ${displayProblem.tags.join(" ")}`, 260, "13px Inter, system-ui, sans-serif", 17);
  return (
    <button
      className={active ? "problem-card active" : "problem-card"}
      title={localeText(locale, { zh: `打开 ${displayProblem.title}`, en: `Open ${displayProblem.title}` })}
      onClick={onSelect}
      style={{ minHeight: Math.max(92, titleLayout.height + 54) }}
    >
      <span className={`difficulty ${displayProblem.difficulty.toLowerCase()}`}>{localizeDifficulty(displayProblem.difficulty, locale)}</span>
      <strong>{displayProblem.title}</strong>
      <span className="tag-line">{localizeTags(displayProblem.tags, locale).join(" / ") || text.noTags}</span>
      <span className="mode-line">
        <ProblemModeBadges problem={displayProblem} locale={locale} />
      </span>
      <span className="card-meta">{text.solved} {displayProblem.accepted_submissions}/{displayProblem.total_submissions} - {text.acceptance} {percent(displayProblem.ac_rate)}%</span>
    </button>
  );
}

function ProblemRow({ problem, locale, active, onSelect }: { problem: ProblemListItem; locale: Locale; active: boolean; onSelect: () => void }) {
  const displayProblem = localizedProblem(problem, locale);
  const text = getUI(locale);
  return (
    <button
      className={active ? "problem-row active" : "problem-row"}
      title={`${text.openProblem}: ${displayProblem.title}`}
      onClick={onSelect}
    >
      <span className="problem-row-title">
        <strong>{displayProblem.title}</strong>
        <small>{displayProblem.slug}</small>
      </span>
      <span className={`difficulty ${displayProblem.difficulty.toLowerCase()}`}>{localizeDifficulty(displayProblem.difficulty, locale)}</span>
      <span className="problem-row-tags" aria-label={text.tags}>{localizeTags(displayProblem.tags, locale).join(" / ") || text.noTags}</span>
      <span className="mode-line problem-row-modes" aria-label={text.modes}>
        <ProblemModeBadges problem={displayProblem} locale={locale} />
      </span>
      <span className="problem-row-stats">
        <span>{text.solved} {displayProblem.accepted_submissions}/{displayProblem.total_submissions}</span>
        <span>{text.acceptance} {percent(displayProblem.ac_rate)}%</span>
      </span>
      <span className="problem-row-open">{text.openProblem}</span>
    </button>
  );
}

function recordValue(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : [];
}

function draftSourceMetadata(draft: Pick<ProblemDraft, "source_metadata"> | null | undefined): Record<string, unknown> {
  return recordValue(draft?.source_metadata);
}

function isImportedDraft(draft: Pick<ProblemDraft, "source_metadata"> | null | undefined): boolean {
  return draftSourceMetadata(draft).kind === "imported";
}

function draftTimestamp(draft: ProblemDraft): number {
  const value = draft.updated_at ?? draft.created_at ?? "";
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function mergeDrafts(...sources: Array<ProblemDraft[] | ProblemDraft | null | undefined>): ProblemDraft[] {
  const byId = new Map<string, ProblemDraft>();
  for (const source of sources) {
    const items = Array.isArray(source) ? source : source ? [source] : [];
    for (const draft of items) {
      if (!draft?.id) continue;
      byId.set(draft.id, { ...byId.get(draft.id), ...draft });
    }
  }
  return Array.from(byId.values()).sort((left, right) => draftTimestamp(right) - draftTimestamp(left));
}

function sourceText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function validationLabel(name: string, locale: Locale): string {
  const labels: Record<string, { zh: string; en: string }> = {
    title: { zh: "题目标题", en: "Title" },
    description: { zh: "题目描述", en: "Description" },
    official_solutions: { zh: "多语言官方解法", en: "Official solutions" },
    official_solution_languages: { zh: "目标语言解法", en: "Target language solutions" },
    official_solution_code: { zh: "官方解法代码", en: "Official solution code" },
    official_solution_explanation: { zh: "官方解法说明", en: "Official solution explanation" },
    time_complexity: { zh: "时间复杂度", en: "Time complexity" },
    space_complexity: { zh: "空间复杂度", en: "Space complexity" },
    function_signature: { zh: "函数签名", en: "Function signature" },
    function_testcase_inputs: { zh: "函数用例参数格式", en: "Function testcase input shape" },
    input_format: { zh: "输入格式", en: "Input format" },
    output_format: { zh: "输出格式", en: "Output format" },
    testcase_count: { zh: "用例数量", en: "Testcase count" },
    public_sample_count: { zh: "公开样例数量", en: "Public sample count" },
    hidden_testcase_count: { zh: "隐藏用例数量", en: "Hidden testcase count" },
    non_empty_outputs: { zh: "期望输出非空", en: "Non-empty expected outputs" },
    official_solution: { zh: "官方解法沙箱验证", en: "Official solution sandbox run" },
  };
  return labels[name] ? localeText(locale, labels[name]) : name;
}

function draftStatusLabel(status: string, locale: Locale): string {
  const labels: Record<string, { zh: string; en: string }> = {
    validated: { zh: "已通过", en: "Validated" },
    validation_failed: { zh: "校验失败", en: "Validation failed" },
    approved: { zh: "已发布", en: "Approved" },
    rejected: { zh: "已拒绝", en: "Rejected" },
    draft: { zh: "草稿", en: "Draft" },
  };
  return labels[status] ? localeText(locale, labels[status]) : status;
}

function draftStatusClass(status: string): string {
  return `draft-status-${status.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}

function draftIsReadOnly(status: string): boolean {
  return status === "approved" || status === "rejected";
}

function authoringModeLabel(mode: string, locale: Locale): string {
  const labels: Record<string, { zh: string; en: string }> = {
    both: { zh: "双模式", en: "both" },
    function: { zh: "函数模式", en: "function" },
    acm: { zh: "ACM 模式", en: "acm" },
  };
  return labels[mode] ? localeText(locale, labels[mode]) : mode;
}

function modeRequiresFunction(mode: string): boolean {
  return mode === "function" || mode === "both";
}

function modeRequiresAcmContract(mode: string): boolean {
  return mode === "acm" || mode === "both";
}

function languageLabel(language: string): string {
  const labels: Record<string, string> = {
    python: "Python",
    c: "C",
    cpp: "C++",
    java: "Java",
    javascript: "JavaScript",
    typescript: "TypeScript",
    golang: "Go",
  };
  return labels[language] ?? language;
}

function normalizeLanguageList(values: string[]): string[] {
  const supported = new Set<string>(LANGUAGES);
  const result: string[] = [];
  for (const value of values) {
    const language = String(value || "").trim().toLowerCase();
    if (supported.has(language) && !result.includes(language)) {
      result.push(language);
    }
  }
  return result;
}

function solutionListFromDraft(draft: ProblemDraft): DraftOfficialSolution[] {
  const raw = Array.isArray(draft.official_solutions) ? draft.official_solutions : [];
  const solutions = raw
    .map((solution) => ({
      language: String(solution.language ?? "").trim() || "python",
      code: String(solution.code ?? ""),
      explanation: String(solution.explanation ?? ""),
      acm_code: typeof (solution as any).acm_code === "string" ? (solution as any).acm_code : null,
      function_code: typeof (solution as any).function_code === "string" ? (solution as any).function_code : null,
    }))
    .filter((solution, index, list) => (
      solution.code.trim() && list.findIndex((item) => item.language === solution.language) === index
    ));
  if (solutions.length) return solutions;
  return [{
    language: draft.official_solution_language ?? "python",
    code: draft.official_solution_code ?? "",
    explanation: draft.official_solution_explanation ?? "",
  }];
}

function draftEditFromDraft(draft: ProblemDraft): DraftEditState {
  const targetLanguages = normalizeLanguageList(draft.target_languages ?? []);
  const solutions = solutionListFromDraft(draft);
  return {
    title: draft.title ?? "",
    slug: draft.slug ?? "",
    description: draft.description ?? "",
    difficulty: ["easy", "medium", "hard"].includes(draft.difficulty) ? draft.difficulty as "easy" | "medium" | "hard" : "medium",
    tags: (draft.tags ?? []).join(", "),
    mode: draft.mode === "acm" || draft.mode === "both" ? draft.mode : "function",
    target_languages: targetLanguages.length ? targetLanguages : normalizeLanguageList(solutions.map((solution) => solution.language)),
    input_format: draft.input_format ?? "",
    output_format: draft.output_format ?? "",
    function_signature: draft.function_signature ?? "",
    time_limit: String(draft.time_limit ?? 1000),
    memory_limit: String(draft.memory_limit ?? 256),
    hint: draft.hint ?? "",
    official_solutions: solutions,
    time_complexity: draft.time_complexity ?? "",
    space_complexity: draft.space_complexity ?? "",
    testcases: (draft.testcases ?? []).map((testcase, index) => ({
      input: String(testcase.input ?? ""),
      output: String(testcase.output ?? ""),
      explanation: String(testcase.explanation ?? ""),
      io_metadata: typeof testcase.io_metadata === "object" && testcase.io_metadata !== null ? testcase.io_metadata : null,
      is_hidden: testcase.is_hidden === true,
      is_sample: testcase.is_sample === true,
      order: Number(testcase.order ?? index + 1) || index + 1,
    })),
  };
}

function draftEditPayload(edit: DraftEditState) {
  const targetLanguages = normalizeLanguageList(edit.target_languages);
  const officialSolutions = edit.official_solutions
    .map((solution) => ({
      language: solution.language.trim() || "python",
      code: solution.code,
      explanation: solution.explanation.trim(),
      ...(solution.acm_code ? { acm_code: solution.acm_code } : {}),
      ...(solution.function_code ? { function_code: solution.function_code } : {}),
    }))
    .filter((solution, index, list) => (
      solution.code.trim()
      && solution.explanation
      && list.findIndex((item) => item.language === solution.language) === index
    ));
  const primary = officialSolutions[0] ?? { language: "python", code: "", explanation: "" };
  return {
    title: edit.title.trim(),
    slug: edit.slug.trim(),
    description: edit.description.trim(),
    difficulty: edit.difficulty,
    tags: edit.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
    mode: edit.mode,
    target_languages: targetLanguages,
    input_format: edit.input_format.trim() || null,
    output_format: edit.output_format.trim() || null,
    function_signature: edit.function_signature.trim() || null,
    time_limit: Number(edit.time_limit) || 1000,
    memory_limit: Number(edit.memory_limit) || 256,
    hint: edit.hint.trim() || null,
    official_solution_language: primary.language,
    official_solution_code: primary.code,
    official_solution_explanation: primary.explanation,
    official_solutions: officialSolutions,
    time_complexity: edit.time_complexity.trim() || null,
    space_complexity: edit.space_complexity.trim() || null,
    testcases: edit.testcases.map((testcase, index) => ({
      input: testcase.input,
      output: testcase.output,
      explanation: testcase.explanation.trim() || null,
      io_metadata: testcase.io_metadata ?? null,
      is_hidden: testcase.is_hidden,
      is_sample: testcase.is_sample,
      order: Number(testcase.order) || index + 1,
    })),
  };
}

function draftEditKey(edit: DraftEditState): string {
  return JSON.stringify(draftEditPayload(edit));
}

function isDraftEditDirty(draft: ProblemDraft | null, edit: DraftEditState | null): boolean {
  if (!draft || !edit) return false;
  return draftEditKey(edit) !== draftEditKey(draftEditFromDraft(draft));
}

function draftEditValidationError(edit: DraftEditState, locale: Locale): string | null {
  const targetLanguages = normalizeLanguageList(edit.target_languages);
  if (!edit.title.trim()) return localeText(locale, { zh: "标题不能为空。", en: "Title is required." });
  if (!edit.description.trim()) return localeText(locale, { zh: "描述不能为空。", en: "Description is required." });
  if (modeRequiresFunction(edit.mode) && !edit.function_signature.trim()) {
    return localeText(locale, { zh: "函数模式和双模式都需要函数签名。", en: "Function and dual mode require a function signature." });
  }
  if (modeRequiresAcmContract(edit.mode) && !edit.input_format.trim()) {
    return localeText(locale, { zh: "ACM 模式和双模式都需要输入格式。", en: "ACM and dual mode require an input format." });
  }
  if (modeRequiresAcmContract(edit.mode) && !edit.output_format.trim()) {
    return localeText(locale, { zh: "ACM 模式和双模式都需要输出格式。", en: "ACM and dual mode require an output format." });
  }
  if (!targetLanguages.length) return localeText(locale, { zh: "至少选择一种目标语言。", en: "Select at least one target language." });
  const seen = new Set<string>();
  for (const solution of edit.official_solutions) {
    const language = solution.language.trim().toLowerCase();
    if (!language) return localeText(locale, { zh: "官方解法语言不能为空。", en: "Official solution language is required." });
    if (seen.has(language)) return localeText(locale, { zh: "官方解法语言不能重复。", en: "Official solution languages must be unique." });
    seen.add(language);
  }
  for (const language of targetLanguages) {
    const solution = edit.official_solutions.find((item) => item.language === language);
    if (!solution?.code.trim()) return localeText(locale, { zh: `${languageLabel(language)} 官方解法代码不能为空。`, en: `${languageLabel(language)} solution code is required.` });
    if (!solution?.explanation.trim()) return localeText(locale, { zh: `${languageLabel(language)} 官方解法说明不能为空。`, en: `${languageLabel(language)} solution explanation is required.` });
  }
  if (!edit.testcases.length) return localeText(locale, { zh: "至少需要一个用例。", en: "At least one testcase is required." });
  if (!edit.testcases.some((testcase) => !testcase.is_hidden)) return localeText(locale, { zh: "至少需要一个公开用例。", en: "At least one public testcase is required." });
  return null;
}

function validationStatusMessage(status: string, summary: unknown, locale: Locale): string {
  const report = recordValue(summary);
  const failedChecks = stringList(report.failed_checks).length
    ? stringList(report.failed_checks)
    : (Array.isArray(report.checks) ? report.checks.map(recordValue).filter((check) => check.passed === false).map((check) => String(check.name ?? "")).filter(Boolean) : []);
  const caseSummary = recordValue(report.case_summary);
  const failedCases = Number(caseSummary.failed ?? 0);
  if (status === "validated" || report.passed === true) {
    return localeText(locale, { zh: "草稿已通过结构校验和官方解法验证。", en: "Draft passed schema and official-solution validation." });
  }
  if (status === "running") {
    return localeText(locale, { zh: "Agent 已开始执行，执行路径会实时更新。", en: "Agent run started. The timeline will update live." });
  }
  if (failedChecks.length) {
    const labels = failedChecks.slice(0, 3).map((name) => validationLabel(name, locale)).join(localeText(locale, { zh: "、", en: ", " }));
    const suffix = failedChecks.length > 3 ? localeText(locale, { zh: " 等", en: ", ..." }) : "";
    return localeText(locale, { zh: `校验未通过：${labels}${suffix}`, en: `Validation failed: ${labels}${suffix}` });
  }
  if (failedCases > 0) {
    return localeText(locale, { zh: `官方解法有 ${failedCases} 个用例未通过。`, en: `Official solution failed ${failedCases} testcase(s).` });
  }
  return localeText(locale, { zh: "草稿校验未通过，请查看下方安全摘要。", en: "Draft validation failed. Check the safe summary below." });
}

function draftSaveErrorMessage(error: unknown, locale: Locale): string {
  const message = error instanceof Error ? error.message : localeText(locale, { zh: "草稿保存失败。", en: "Draft save failed." });
  const slugMatch = message.match(/Slug already exists:?\s*([A-Za-z0-9-]+)?/i);
  if (slugMatch) {
    const slug = slugMatch[1] ? `：${slugMatch[1]}` : "";
    return localeText(locale, {
      zh: `Slug 已被占用${slug}。请换一个唯一的 slug。`,
      en: message,
    });
  }
  return message;
}

function solutionEditFromAdmin(solution: AdminSolution): ProblemSolutionEdit {
  return {
    language: solution.language,
    code: solution.code ?? "",
    explanation: solution.explanation ?? "",
    time_complexity: solution.time_complexity ?? "",
    space_complexity: solution.space_complexity ?? "",
  };
}

function problemEditFromProblem(problem: any, solutions: AdminSolution[] = []): ProblemEditState {
  return {
    title: problem?.title ?? "",
    slug: problem?.slug ?? "",
    description: problem?.description ?? "",
    difficulty: ["easy", "medium", "hard"].includes(problem?.difficulty) ? problem.difficulty : "medium",
    tags: (problem?.tags ?? []).join(", "),
    mode: problem?.mode === "function" || problem?.mode === "both" ? problem.mode : "acm",
    input_format: problem?.input_format ?? "",
    output_format: problem?.output_format ?? "",
    function_signature: problem?.function_signature ?? "",
    time_limit: String(problem?.time_limit ?? 1000),
    memory_limit: String(problem?.memory_limit ?? 256),
    hint: problem?.hint ?? "",
    solutions: solutions.map(solutionEditFromAdmin),
  };
}

function problemEditValidationError(edit: ProblemEditState, locale: Locale): string | null {
  if (!edit.title.trim()) return localeText(locale, { zh: "标题不能为空。", en: "Title is required." });
  if (!edit.slug.trim()) return localeText(locale, { zh: "Slug 不能为空。", en: "Slug is required." });
  if (!edit.description.trim()) return localeText(locale, { zh: "描述不能为空。", en: "Description is required." });
  if (modeRequiresFunction(edit.mode) && !edit.function_signature.trim()) {
    return localeText(locale, { zh: "函数模式和双模式都需要函数签名。", en: "Function and dual mode require a function signature." });
  }
  if (modeRequiresAcmContract(edit.mode) && !edit.input_format.trim()) {
    return localeText(locale, { zh: "ACM 模式和双模式都需要输入格式。", en: "ACM and dual mode require an input format." });
  }
  if (modeRequiresAcmContract(edit.mode) && !edit.output_format.trim()) {
    return localeText(locale, { zh: "ACM 模式和双模式都需要输出格式。", en: "ACM and dual mode require an output format." });
  }
  const seen = new Set<string>();
  for (const solution of edit.solutions) {
    const language = solution.language.trim().toLowerCase();
    if (!language) return localeText(locale, { zh: "官方解法语言不能为空。", en: "Official solution language is required." });
    if (seen.has(language)) return localeText(locale, { zh: "官方解法语言不能重复。", en: "Official solution languages must be unique." });
    seen.add(language);
    if (!solution.code.trim()) return localeText(locale, { zh: `${languageLabel(language)} 官方解法代码不能为空。`, en: `${languageLabel(language)} solution code is required.` });
    if (!solution.explanation.trim()) return localeText(locale, { zh: `${languageLabel(language)} 官方解法说明不能为空。`, en: `${languageLabel(language)} solution explanation is required.` });
  }
  return null;
}

function problemEditPayload(edit: ProblemEditState): Record<string, unknown> {
  return {
    title: edit.title.trim(),
    slug: edit.slug.trim(),
    description: edit.description.trim(),
    difficulty: edit.difficulty,
    tags: edit.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
    mode: edit.mode,
    input_format: edit.input_format.trim() || null,
    output_format: edit.output_format.trim() || null,
    function_signature: edit.function_signature.trim() || null,
    time_limit: Number(edit.time_limit) || 1000,
    memory_limit: Number(edit.memory_limit) || 256,
    hint: edit.hint.trim() || null,
  };
}

function problemSolutionPayloads(edit: ProblemEditState): AdminSolutionPayload[] {
  return edit.solutions.map((solution) => ({
    language: solution.language.trim().toLowerCase(),
    code: solution.code,
    explanation: solution.explanation,
    time_complexity: solution.time_complexity.trim() || null,
    space_complexity: solution.space_complexity.trim() || null,
  }));
}

function ValidationReport({ draft, locale }: { draft: ProblemDraft; locale: Locale }) {
  const report = recordValue(draft.validation_report ?? draft.validation_summary);
  const checks = Array.isArray(report.checks) ? report.checks.map(recordValue) : [];
  const failedChecks = stringList(report.failed_checks);
  const caseSummary = recordValue(report.case_summary);
  const passed = report.passed === true || draft.status === "validated" || draft.status === "approved";
  const publicCount = Number(report.public_sample_count ?? 0);
  const hiddenCount = Number(report.hidden_testcase_count ?? 0);
  const failedCases = Number(caseSummary.failed ?? 0);
  const failedStatuses = stringList(caseSummary.failed_statuses);
  return (
    <div className="validation-report">
      <div className="validation-head">
        <span className={`status-badge ${passed ? "ac" : "wa"}`}>{passed ? "OK" : "Needs review"}</span>
        <strong>{validationStatusMessage(draft.status, report, locale)}</strong>
      </div>
      <div className="validation-metrics">
        <span><strong>{publicCount}</strong>{localeText(locale, { zh: "公开样例", en: "public samples" })}</span>
        <span><strong>{hiddenCount}</strong>{localeText(locale, { zh: "隐藏用例", en: "hidden cases" })}</span>
        <span><strong>{failedCases}</strong>{localeText(locale, { zh: "失败用例", en: "failed cases" })}</span>
      </div>
      {failedChecks.length ? (
        <div className="validation-failures">
          <strong>{localeText(locale, { zh: "失败检查", en: "Failed checks" })}</strong>
          <ul>
            {failedChecks.map((name) => <li key={name}>{validationLabel(name, locale)}</li>)}
          </ul>
        </div>
      ) : null}
      {failedStatuses.length ? (
        <p className="muted">{localeText(locale, { zh: "沙箱状态", en: "Sandbox statuses" })}: {failedStatuses.join(", ")}</p>
      ) : null}
      {checks.length ? (
        <div className="validation-checks">
          {checks.map((check) => {
            const name = String(check.name ?? "check");
            const ok = check.passed === true;
            return (
              <span className={ok ? "validation-check passed" : "validation-check failed"} key={name}>
                {ok ? "✓" : "!"} {validationLabel(name, locale)}
              </span>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

function ProblemValidationReport({ report, locale }: { report: Record<string, any> | null; locale: Locale }) {
  if (!report) return null;
  const normalized = recordValue(report);
  const status = normalized.passed === true ? "validated" : "validation_failed";
  const checks = Array.isArray(normalized.checks) ? normalized.checks.map(recordValue) : [];
  const failedChecks = stringList(normalized.failed_checks);
  const caseSummary = recordValue(normalized.case_summary);
  const failedCases = Number(caseSummary.failed ?? 0);
  return (
    <div className="validation-report problem-validation-report">
      <div className="validation-head">
        <span className={`status-badge ${normalized.passed === true ? "ac" : "wa"}`}>
          {normalized.passed === true ? "OK" : "Needs review"}
        </span>
        <strong>{validationStatusMessage(status, normalized, locale)}</strong>
      </div>
      <div className="validation-metrics">
        <span><strong>{Number(normalized.public_sample_count ?? 0)}</strong>{localeText(locale, { zh: "公开样例", en: "public samples" })}</span>
        <span><strong>{Number(normalized.hidden_testcase_count ?? 0)}</strong>{localeText(locale, { zh: "隐藏用例", en: "hidden cases" })}</span>
        <span><strong>{failedCases}</strong>{localeText(locale, { zh: "失败用例", en: "failed cases" })}</span>
      </div>
      {checks.length ? (
        <div className="validation-checks">
          {checks.map((check, index) => {
            const name = String(check.name ?? `check-${index}`);
            const ok = check.passed === true;
            return (
              <span className={ok ? "validation-check passed" : "validation-check failed"} key={`${name}-${index}`}>
                {ok ? "✓" : "!"} {validationLabel(name, locale)}
              </span>
            );
          })}
        </div>
      ) : null}
      {failedChecks.length ? (
        <div className="validation-failures">
          <strong>{localeText(locale, { zh: "失败检查", en: "Failed checks" })}</strong>
          <ul>
            {failedChecks.map((name) => <li key={name}>{validationLabel(name, locale)}</li>)}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

type DraftCaseFilter = "all" | "public" | "hidden" | "failed";

function DraftTestcasePanel({ draft, locale }: { draft: ProblemDraft; locale: Locale }) {
  const [filter, setFilter] = useState<DraftCaseFilter>("all");
  const report = recordValue(draft.validation_report ?? draft.validation_summary);
  const caseResults = Array.isArray(report.case_results) ? report.case_results.map(recordValue) : [];
  const resultsByIndex = new Map<number, Record<string, unknown>[]>();
  for (const result of caseResults) {
    const index = Number(result.case_index);
    if (!Number.isFinite(index) || index <= 0) continue;
    resultsByIndex.set(index, [...(resultsByIndex.get(index) ?? []), result]);
  }
  const testcases = (draft.testcases ?? []).map(recordValue);
  const labels = {
    title: localeText(locale, { zh: "用例详情", en: "Testcase details" }),
    all: localeText(locale, { zh: "全部", en: "All" }),
    public: localeText(locale, { zh: "公开", en: "Public" }),
    hidden: localeText(locale, { zh: "隐藏", en: "Hidden" }),
    failed: localeText(locale, { zh: "失败", en: "Failed" }),
    input: localeText(locale, { zh: "输入", en: "Input" }),
    output: localeText(locale, { zh: "预期输出", en: "Expected output" }),
    explanation: localeText(locale, { zh: "解释", en: "Explanation" }),
    noCases: localeText(locale, { zh: "没有用例数据。", en: "No testcase data." }),
  };
  const visibleCases = testcases
    .map((testcase, index) => ({ testcase, index: index + 1, results: resultsByIndex.get(index + 1) ?? [] }))
    .filter(({ testcase, results }) => {
      const hidden = testcase.is_hidden === true;
      if (filter === "public") return !hidden;
      if (filter === "hidden") return hidden;
      if (filter === "failed") return results.some((result) => result.passed !== true);
      return true;
    });
  return (
    <div className="draft-testcases">
      <div className="testcase-panel-head">
        <h3>{labels.title}</h3>
        <div className="testcase-filter-row">
          {(["all", "public", "hidden", "failed"] as DraftCaseFilter[]).map((item) => (
            <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>
              {labels[item]}
            </button>
          ))}
        </div>
      </div>
      {visibleCases.length ? visibleCases.map(({ testcase, index, results }) => {
        const hidden = testcase.is_hidden === true;
        const hasResults = results.length > 0;
        return (
          <article className="testcase-card" key={`${index}-${String(testcase.input ?? "")}`}>
            <div className="testcase-card-head">
              <strong>{localeText(locale, { zh: "用例", en: "Case" })} {index}</strong>
              <span className={hidden ? "case-chip hidden" : "case-chip public"}>{hidden ? labels.hidden : labels.public}</span>
              {hasResults ? results.map((result) => {
                const passed = result.passed === true;
                const language = String(result.solution_language ?? draft.official_solution_language ?? "python");
                const statusText = String(result.status ?? (passed ? "ac" : "wa"));
                return (
                  <span className={passed ? "case-chip passed" : "case-chip failed"} key={`${language}-${statusText}`}>
                    {languageLabel(language)} {statusText}
                  </span>
                );
              }) : null}
            </div>
            <div className="testcase-code-grid">
              <label>{labels.input}<pre>{String(testcase.input ?? "")}</pre></label>
              <label>{labels.output}<pre>{String(testcase.output ?? "")}</pre></label>
            </div>
            {testcase.explanation ? (
              <p className="muted"><strong>{labels.explanation}: </strong>{String(testcase.explanation)}</p>
            ) : null}
            {results.map((result) => result.error_message ? (
              <p className="muted" key={`${String(result.solution_language ?? "")}-${String(result.error_message)}`}>
                {String(result.solution_language ?? draft.official_solution_language ?? "python")}: {String(result.error_message)}
              </p>
            ) : null)}
          </article>
        );
      }) : <p className="muted">{labels.noCases}</p>}
    </div>
  );
}

function Workspace({
  problemId,
  locale,
  theme,
  currentUser,
  onBackToLibrary,
  onRequireAuth,
  authenticated,
}: {
  problemId: string | null;
  locale: Locale;
  theme: AppTheme;
  currentUser: CurrentUser | null;
  onBackToLibrary: () => void;
  onRequireAuth: () => void;
  authenticated: boolean;
}) {
  const text = getUI(locale);
  const { language, setLanguage, getDraft, setDraft, setRecentProblemId, getCachedExplain, setCachedExplain } = useAppStore();
  const [code, setCode] = useState("");
  const [judgeMode, setJudgeMode] = useState<JudgeMode>("acm");
  const [aiModel, setAiModel] = useState<AIModelProfile>(() => (localStorage.getItem("fastoj.aiModel") as AIModelProfile | null) ?? "default");
  const [leftOpen, setLeftOpen] = useState(() => localStorage.getItem("fastoj.leftOpen") !== "false");
  const [rightOpen, setRightOpen] = useState(() => localStorage.getItem("fastoj.rightOpen") !== "false");
  const [leftWidth, setLeftWidth] = useState(() => Number(localStorage.getItem("fastoj.leftWidth") ?? DEFAULT_LEFT_PANEL_WIDTH));
  const [rightWidth, setRightWidth] = useState(() => Number(localStorage.getItem("fastoj.rightWidth") ?? DEFAULT_RIGHT_PANEL_WIDTH));
  const [editorHeight, setEditorHeight] = useState(() => clamp(Number(localStorage.getItem("fastoj.editorHeight") ?? DEFAULT_EDITOR_HEIGHT), EDITOR_MIN_HEIGHT, EDITOR_MAX_HEIGHT));
  const [completionEnabled, setCompletionEnabled] = useState(() => localStorage.getItem("fastoj.completionEnabled") !== "false");
  const [resizing, setResizing] = useState<"left" | "right" | "editor" | null>(null);
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [events, setEvents] = useState<JudgeEvent[]>([]);
  const [runCases, setRunCases] = useState<EditableRunCase[]>([]);
  const [activeRunCase, setActiveRunCase] = useState(0);
  const [runSnapshot, setRunSnapshot] = useState<RunSnapshot | null>(null);
  const [explain, setExplain] = useState<AIExplain | null>(null);
  const [review, setReview] = useState<AIReview | null>(null);
  const [hint, setHint] = useState<AIHint | null>(null);
  const [chatLines, setChatLines] = useState<AIChatLine[]>([]);
  const [aiError, setAiError] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("cases");
  const activeProblemIdRef = useRef<string | null>(problemId);
  const activeSubmissionIdRef = useRef<string | null>(null);
  const judgeRequestRef = useRef(0);
  const pollRef = useRef<number | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const problemQuery = useQuery({ queryKey: ["problem", problemId, locale, judgeMode], queryFn: () => api.problem(problemId ?? "", locale, judgeMode), enabled: Boolean(problemId) });
  const trailQuery = useQuery({ queryKey: ["submissions", problemId, submission?.id], queryFn: () => api.submissions(problemId ?? ""), enabled: Boolean(problemId && authenticated) });
  const solutionsQuery = useQuery({ queryKey: ["solutions", problemId, language, locale], queryFn: () => api.solutions(problemId ?? "", language, locale), enabled: Boolean(problemId) });
  const aiProfilesQuery = useQuery({
    queryKey: ["ai-profiles", currentUser?.id],
    queryFn: () => api.aiProfiles(),
    enabled: Boolean(authenticated && currentUser),
    staleTime: 60_000,
  });

  const problem = problemQuery.data;
  const displayProblem = localizedProblem(problem, locale);
  const modeInfo = getProblemMode(problem);
  const draftKey = `${language}.${judgeMode}`;
  const aiProfiles = aiProfilesQuery.data ?? [];
  const aiPreferredProfile = preferredAIProfile(aiProfiles);
  const aiDisabledReason = !authenticated
    ? localeText(locale, { zh: "请先登录后使用 AI。", en: "Sign in to use AI." })
    : aiProfilesQuery.isLoading
      ? localeText(locale, { zh: "正在检查 AI 模型...", en: "Checking AI profiles..." })
      : aiPreferredProfile
        ? null
        : aiUnavailableText(locale);
  const aiReady = Boolean(aiPreferredProfile && !aiDisabledReason);

  useEffect(() => { localStorage.setItem("fastoj.leftOpen", String(leftOpen)); }, [leftOpen]);
  useEffect(() => { localStorage.setItem("fastoj.rightOpen", String(rightOpen)); }, [rightOpen]);
  useEffect(() => { localStorage.setItem("fastoj.leftWidth", String(leftWidth)); }, [leftWidth]);
  useEffect(() => { localStorage.setItem("fastoj.rightWidth", String(rightWidth)); }, [rightWidth]);
  useEffect(() => { localStorage.setItem("fastoj.editorHeight", String(editorHeight)); }, [editorHeight]);
  useEffect(() => { localStorage.setItem("fastoj.completionEnabled", String(completionEnabled)); }, [completionEnabled]);
  useEffect(() => { localStorage.setItem("fastoj.aiModel", aiModel); }, [aiModel]);
  useEffect(() => { if (problemId) setRecentProblemId(problemId); }, [problemId, setRecentProblemId]);
  useEffect(() => { clearCopilotState(); }, [locale]);
  useEffect(() => {
    if (!aiProfiles.length) return;
    if (!aiProfiles.some((profile) => profile.available && profile.value === aiModel)) {
      const next = preferredAIProfile(aiProfiles);
      if (next) setAiModel(next);
    }
  }, [aiProfiles, aiModel]);

  function editorCodeFor(targetLanguage: string, targetMode: JudgeMode): string {
    if (!problemId || !problem) return "";
    const starter = buildStarter(problem, targetLanguage, targetMode, locale);
    const draft = getDraft(problemId, `${targetLanguage}.${targetMode}`);
    if (!draft.trim()) return starter;
    if (targetMode === "function" && isLikelyStaleAcmDraft(problem, targetLanguage, draft)) return starter;
    if (targetMode === "function" && targetLanguage !== "python" && draft.trim()) {
      if (/^\s*(import\s+\w+\s*\n\s*)*def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(/.test(draft)) return starter;
      const stalePythonStarters = SUPPORTED_LOCALES.map((item) => buildStarter(problem, "python", "function", item).trim());
      if (stalePythonStarters.includes(draft.trim())) return starter;
    }
    return draft;
  }

  function resetEditorTemplate() {
    const starter = buildStarter(problem, language, judgeMode, locale);
    setCode(starter);
    if (problemId) setDraft(problemId, draftKey, starter);
  }

  useEffect(() => {
    activeProblemIdRef.current = problemId;
    activeSubmissionIdRef.current = null;
    stopStatusStream();
    setSubmission(null);
    setEvents([]);
    setRunSnapshot(null);
    setActiveRunCase(0);
    clearCopilotState();
    setDetailTab("cases");
  }, [problemId]);

  useEffect(() => () => stopStatusStream(), []);

  useEffect(() => {
    if (!problem) {
      setRunCases([]);
      setActiveRunCase(0);
      return;
    }
    setRunCases(runCasesFromProblem(problem));
    setActiveRunCase(0);
  }, [problem?.id, problem?.sample_testcases]);

  useEffect(() => {
    if (!problemId || !problem) return;
    const nextMode = modeInfo.defaultMode;
    setJudgeMode(nextMode);
    setCode(editorCodeFor(language, nextMode));
  }, [problemId, problem?.slug, locale]);

  useEffect(() => {
    if (!problemId || !problem) return;
    setCode(editorCodeFor(language, judgeMode));
  }, [language, judgeMode, locale]);

  function updateCode(next: string) {
    setCode(next);
    if (problemId) setDraft(problemId, draftKey, next);
  }

  function toggleJudgeMode() {
    if (judgeMode === "function" && !modeInfo.supportsAcm) return;
    if (judgeMode === "acm" && !modeInfo.supportsFunction) return;
    setJudgeMode(judgeMode === "function" ? "acm" : "function");
  }

  function startResize(side: "left" | "right", event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startX = event.clientX;
    const panelOpen = side === "left" ? leftOpen : rightOpen;
    const startWidth = panelOpen ? (side === "left" ? leftWidth : rightWidth) : SIDE_PANEL_DRAG_MIN;
    const maxWidth = side === "left" ? 860 : 820;
    const defaultWidth = side === "left" ? DEFAULT_LEFT_PANEL_WIDTH : DEFAULT_RIGHT_PANEL_WIDTH;
    let latestWidth = startWidth;
    if (!panelOpen) {
      if (side === "left") {
        setLeftOpen(true);
        setLeftWidth(startWidth);
      } else {
        setRightOpen(true);
        setRightWidth(startWidth);
      }
    }
    setResizing(side);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    const onMove = (moveEvent: PointerEvent) => {
      const delta = side === "left" ? moveEvent.clientX - startX : startX - moveEvent.clientX;
      const next = clamp(startWidth + delta, SIDE_PANEL_DRAG_MIN, maxWidth);
      latestWidth = next;
      if (side === "left") setLeftWidth(next);
      else setRightWidth(next);
    };
    const onUp = () => {
      if (latestWidth <= SIDE_PANEL_SNAP_WIDTH) {
        if (side === "left") {
          setLeftOpen(false);
          setLeftWidth(defaultWidth);
        } else {
          setRightOpen(false);
          setRightWidth(defaultWidth);
        }
      }
      setResizing(null);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  function startEditorResize(event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startY = event.clientY;
    const startHeight = editorHeight;
    setResizing("editor");
    document.body.style.cursor = "row-resize";
    document.body.style.userSelect = "none";
    const onMove = (moveEvent: PointerEvent) => {
      setEditorHeight(clamp(startHeight + moveEvent.clientY - startY, EDITOR_MIN_HEIGHT, EDITOR_MAX_HEIGHT));
    };
    const onUp = () => {
      setResizing(null);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  function clearCopilotState() {
    setExplain(null);
    setReview(null);
    setHint(null);
    setChatLines([]);
    setAiError(null);
  }

  function stopStatusStream() {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  }

  async function judge(runOnly: boolean) {
    if (!problemId) return;
    if (!authenticated || !localStorage.getItem("fastoj.jwt")) {
      onRequireAuth();
      return;
    }
    const requestId = judgeRequestRef.current + 1;
    judgeRequestRef.current = requestId;
    const requestProblemId = problemId;
    const panelCases = runOnly ? ensureRunCases(runCases) : runCasesFromProblem(problem);
    const runPayload = runOnly
      ? panelCases.map((item) => ({ input: item.input }))
      : undefined;
    stopStatusStream();
    activeSubmissionIdRef.current = null;
    clearCopilotState();
    setSubmission(null);
    setRunSnapshot({ submissionId: "", cases: panelCases });
    setDetailTab("judge");
    setLeftOpen(true);
    setEvents([{ type: "pending", status: "pending", progress: 0 }]);
    try {
      const created = await api.submit(problemId, language, code, runOnly, judgeMode, runPayload);
      if (activeProblemIdRef.current !== requestProblemId || judgeRequestRef.current !== requestId) return;
      activeSubmissionIdRef.current = created.id;
      setRunSnapshot({ submissionId: created.id, cases: panelCases });
      setSubmission(created as SubmissionDetail);
      connectStatus(created.id);
    } catch (error) {
      if (activeProblemIdRef.current !== requestProblemId || judgeRequestRef.current !== requestId) return;
      if (isUnauthorized(error)) {
        localStorage.removeItem("fastoj.jwt");
        setEvents([{ type: "error", status: "finished", result: "se", message: text.authExpired }]);
        window.alert(text.authExpired);
        onRequireAuth();
        return;
      }
      setEvents([{ type: "error", status: "finished", result: "se", message: error instanceof Error ? error.message : "Submit failed" }]);
    }
  }

  function connectStatus(submissionId: string) {
    stopStatusStream();
    activeSubmissionIdRef.current = submissionId;
    const socket = makeJudgeSocket(submissionId);
    let polling = false;
    const poll = window.setInterval(async () => {
      if (activeSubmissionIdRef.current !== submissionId) {
        window.clearInterval(poll);
        if (pollRef.current === poll) pollRef.current = null;
        return;
      }
      if (polling) return;
      polling = true;
      try {
        const detail = await api.submission(submissionId);
        if (activeSubmissionIdRef.current !== submissionId) return;
        setSubmission(detail);
        if (detail.status === "finished") {
          setEvents((items) => (
            items.some((item) => item.type === "result" || item.type === "error")
              ? items
              : [...items, {
                  type: detail.result === "se" ? "error" : "result",
                  status: "finished",
                  result: detail.result ?? "finished",
                  message: detail.error_message ?? undefined,
                }]
          ));
          window.clearInterval(poll);
          if (pollRef.current === poll) pollRef.current = null;
        }
      } finally {
        polling = false;
      }
    }, 1600);
    pollRef.current = poll;
    if (!socket) return;
    socketRef.current = socket;
    socket.onmessage = (event) => {
      if (activeSubmissionIdRef.current !== submissionId) return;
      const payload = JSON.parse(event.data);
      const data = payload.data ?? {};
      setEvents((items) => [...items, { type: payload.type, ...data }]);
      if (payload.type === "result") {
        window.clearInterval(poll);
        if (pollRef.current === poll) pollRef.current = null;
        api.submission(submissionId).then((detail) => {
          if (activeSubmissionIdRef.current === submissionId) setSubmission(detail);
        }).catch(() => undefined);
      }
    };
    socket.onerror = () => socket.close();
  }

  async function explainSubmission() {
    if (!submission) return;
    if (!aiReady) {
      setAiError(aiDisabledReason ?? aiUnavailableText(locale));
      return;
    }
    const submissionId = submission.id;
    const cached = getCachedExplain(`${submissionId}.${aiModel}.${locale}`);
    if (cached) {
      if (activeSubmissionIdRef.current !== submissionId) return;
      setExplain(cached);
      return;
    }
    try {
      setAiError(null);
      const result = await api.explain(submissionId, aiModel, locale);
      if (activeSubmissionIdRef.current !== submissionId) return;
      setExplain(result);
      setCachedExplain(`${submissionId}.${aiModel}.${locale}`, result);
    } catch (error) {
      if (activeSubmissionIdRef.current !== submissionId) return;
      setAiError(error instanceof Error ? error.message : "AI explain failed");
    }
  }

  async function reviewSubmission() {
    if (!submission) return;
    if (!aiReady) {
      setAiError(aiDisabledReason ?? aiUnavailableText(locale));
      return;
    }
    const submissionId = submission.id;
    try {
      setAiError(null);
      const result = await api.review(submissionId, aiModel, locale);
      if (activeSubmissionIdRef.current !== submissionId) return;
      setReview(result);
    } catch (error) {
      if (activeSubmissionIdRef.current !== submissionId) return;
      setAiError(error instanceof Error ? error.message : "AI review failed");
    }
  }

  async function requestHint(level: 1 | 2 | 3) {
    if (!problemId) return;
    if (!aiReady) {
      setAiError(aiDisabledReason ?? aiUnavailableText(locale));
      return;
    }
    const requestProblemId = problemId;
    try {
      setAiError(null);
      const result = await api.hint(problemId, level, language, code, aiModel, locale);
      if (activeProblemIdRef.current !== requestProblemId) return;
      setHint(result);
    } catch (error) {
      if (activeProblemIdRef.current !== requestProblemId) return;
      setAiError(error instanceof Error ? error.message : "AI hint failed");
    }
  }

  async function sendChat(message: string) {
    if (!aiReady) {
      setAiError(aiDisabledReason ?? aiUnavailableText(locale));
      return;
    }
    if (!submission) {
      setAiError(localeText(locale, { zh: "请先运行或提交一次代码，再开始对话。", en: "Run or submit once before starting a chat." }));
      return;
    }
    const submissionId = submission.id;
    const userLine: AIChatLine = { id: `${Date.now()}.user`, role: "user", message };
    setChatLines((items) => [...items, userLine]);
    try {
      setAiError(null);
      const result: AIChat = await api.chat(submissionId, message, aiModel, locale);
      if (activeSubmissionIdRef.current !== submissionId) return;
      setChatLines((items) => [
        ...items,
        { id: `${Date.now()}.assistant`, role: "assistant", message: result.message, suggestions: result.suggested_actions },
      ]);
    } catch (error) {
      if (activeSubmissionIdRef.current !== submissionId) return;
      setAiError(error instanceof Error ? error.message : "AI chat failed");
    }
  }

  function updateRunCase(index: number, value: string) {
    setRunCases((items) => (
      items.map((item, itemIndex) => (
        itemIndex === index ? { ...item, input: value, expected_output: "" } : item
      ))
    ));
  }

  function addRunCase() {
    if (runCases.length >= MAX_RUN_CASES) return;
    setRunCases((items) => [...items, { id: `custom-${Date.now()}`, input: "", expected_output: "" }]);
    setActiveRunCase(runCases.length);
  }

  function removeRunCase(index: number) {
    const nextLength = Math.max(1, runCases.length - 1);
    setRunCases((items) => {
      const next = items.filter((_, itemIndex) => itemIndex !== index);
      return next.length ? next : [{ id: `custom-${Date.now()}`, input: "", expected_output: "" }];
    });
    setActiveRunCase(Math.max(0, Math.min(index, nextLength - 1)));
  }

  function resetRunCases() {
    setRunCases(runCasesFromProblem(problem));
    setActiveRunCase(0);
    setRunSnapshot(null);
  }

  if (!problemId) {
    return (
      <main className="empty-workspace">
        <div>
          <h1>{text.chooseProblem}</h1>
          <p className="muted">{text.chooseProblemCopy}</p>
          <button onClick={onBackToLibrary}>{text.backLibrary}</button>
        </div>
      </main>
    );
  }

  const gridStyle = {
    "--left-panel": leftOpen ? `${leftWidth}px` : "18px",
    "--right-panel": rightOpen ? `${rightWidth}px` : "18px",
  } as React.CSSProperties;
  const codingStyle = {
    "--editor-height": `${editorHeight}px`,
  } as React.CSSProperties;

  return (
    <main className={`workbench-page ${leftOpen ? "" : "left-collapsed"} ${rightOpen ? "" : "right-collapsed"} ${resizing ? "is-resizing" : ""}`} style={gridStyle}>
      <section className="workbench-header">
        <button className="icon-button" title={text.backLibrary} onClick={onBackToLibrary}><IconGlyph>{"<"}</IconGlyph></button>
        <div>
          <p className="eyebrow">{text.workbench}</p>
          <h1>{displayProblem?.title ?? text.loadingProblem}</h1>
          <div className="chips">
            {problem ? <span className={`difficulty ${problem.difficulty.toLowerCase()}`}>{localizeDifficulty(problem.difficulty, locale)}</span> : null}
            {problem?.tags.map((tag) => <span key={tag}>{localizeTag(tag, locale)}</span>)}
            {problem ? <span>{problem.time_limit}ms / {problem.memory_limit}MB</span> : null}
          </div>
        </div>
        <StatusBadge submission={submission} locale={locale} />
      </section>

      <section className="workbench-grid">
        <aside className="statement-sidebar feature-frame statement-frame">
          {leftOpen ? (
            <>
              <ProblemStatement problem={problem} locale={locale} />
              <DetailDock
                detailTab={detailTab}
                setDetailTab={setDetailTab}
                problem={problem}
                solution={solutionsQuery.data?.[0]}
                events={events}
                submission={submission}
                theme={theme}
                trail={trailQuery.data ?? []}
                problemId={problemId}
                locale={locale}
                authenticated={authenticated}
                currentUser={currentUser}
                onRequireAuth={onRequireAuth}
              />
            </>
          ) : null}
        </aside>
        <div className="panel-edge left-edge">
          <button className="edge-toggle" title={leftOpen ? text.collapseLeft : text.expandLeft} onClick={() => setLeftOpen((value) => !value)}>
            <PanelToggleIcon open={leftOpen} side="left" />
          </button>
          <div
            className="resize-handle"
            role="separator"
            aria-label={localeText(locale, { zh: "调整题面面板宽度", en: "Resize statement panel" })}
            title={localeText(locale, { zh: "拖动调整题面宽度", en: "Drag to resize statement" })}
            onPointerDown={(event) => startResize("left", event)}
          />
        </div>

        <section className="coding-panel feature-frame code-frame" style={codingStyle}>
          <div className="editor-toolbar">
            <button
              className={`mode-toggle ${judgeMode === "function" ? "active function-mode" : "active acm-mode"}`}
              title={
                judgeMode === "function"
                  ? modeInfo.supportsAcm
                    ? text.modeAcmTitle
                    : text.modeFunctionOnlyTitle
                  : modeInfo.supportsFunction
                    ? text.modeFunctionTitle
                    : text.modeAcmOnlyTitle
              }
              disabled={judgeMode === "function" ? !modeInfo.supportsAcm : !modeInfo.supportsFunction}
              onClick={toggleJudgeMode}
            >
              <span className="mode-dot" />
              {judgeMode === "function" ? text.functionMode : text.acmMode}
            </button>
            <select title={text.pickLanguage} value={language} onChange={(event) => setLanguage(event.target.value)}>
              {LANGUAGES.map((item) => <option key={item}>{item}</option>)}
            </select>
            <AIModelDropdown value={aiModel} locale={locale} profiles={aiProfiles} disabledReason={aiDisabledReason} onChange={setAiModel} />
            <label
              className={completionEnabled ? "completion-toggle active tip" : "completion-toggle tip"}
              data-tip={completionEnabled ? text.codeCompletionOn : text.codeCompletionOff}
            >
              <input
                type="checkbox"
                checked={completionEnabled}
                aria-label={text.codeCompletion}
                onChange={(event) => setCompletionEnabled(event.target.checked)}
              />
              <span className="completion-switch" aria-hidden="true" />
              <span>{text.codeCompletion}</span>
            </label>
            <button type="button" className="icon-button reset-template-button tip" data-tip={text.resetTemplate} aria-label={text.resetTemplate} onClick={resetEditorTemplate}>
              <ResetTemplateIcon />
            </button>
            <button className="icon-button run-action tip" data-tip={text.runTitle} onClick={() => judge(true)}><IconGlyph>▶</IconGlyph></button>
            <button className="icon-button primary submit-action tip" data-tip={text.submitTitle} onClick={() => judge(false)}><IconGlyph>↑</IconGlyph></button>
          </div>
          <FunctionFrame problem={problem} mode={judgeMode} language={language} locale={locale} />
          <Suspense fallback={<LazySurface className="code-editor" label={localeText(locale, { zh: "正在加载编辑器...", en: "Loading editor..." })} />}>
            <CodeEditor language={language} value={code} onChange={updateCode} theme={theme} completionEnabled={completionEnabled} />
          </Suspense>
          <div
            className="editor-result-resizer"
            role="separator"
            aria-orientation="horizontal"
            aria-label={localeText(locale, { zh: "调整代码编辑器高度", en: "Resize code editor height" })}
            title={localeText(locale, { zh: "拖动调整代码编辑器高度", en: "Drag to resize editor height" })}
            onPointerDown={startEditorResize}
          />
          <Suspense fallback={<LazySurface className="run-result-panel" label={localeText(locale, { zh: "正在加载运行结果...", en: "Loading run results..." })} />}>
            <RunResultPanel
              locale={locale}
              cases={runCases}
              activeIndex={activeRunCase}
              submission={submission}
              snapshot={runSnapshot}
              canRun={Boolean(problem)}
              onActiveIndex={setActiveRunCase}
              onChangeInput={updateRunCase}
              onAddCase={addRunCase}
              onRemoveCase={removeRunCase}
              onResetCases={resetRunCases}
              onRun={() => judge(true)}
            />
          </Suspense>
        </section>

        <div className="panel-edge right-edge">
          <div
            className="resize-handle"
            role="separator"
            aria-label={localeText(locale, { zh: "调整 AI 辅助面板宽度", en: "Resize AI panel" })}
            title={localeText(locale, { zh: "拖动调整 AI 辅助宽度", en: "Drag to resize AI panel" })}
            onPointerDown={(event) => startResize("right", event)}
          />
          <button className="edge-toggle" title={rightOpen ? text.collapseRight : text.expandRight} onClick={() => setRightOpen((value) => !value)}>
            <PanelToggleIcon open={rightOpen} side="right" />
          </button>
        </div>

        <aside className="result-sidebar feature-frame result-frame">
          {rightOpen ? (
            <div className="ai-region">
              <Suspense fallback={<LazySurface className="copilot-panel" label={localeText(locale, { zh: "正在加载 AI 面板...", en: "Loading AI panel..." })} />}>
                <AICopilotPanel submission={submission} explain={explain} review={review} hint={hint} chatLines={chatLines} error={aiError} disabled={!aiReady} disabledReason={aiDisabledReason} onExplain={explainSubmission} onReview={reviewSubmission} onHint={requestHint} onChat={sendChat} locale={locale} />
              </Suspense>
            </div>
          ) : null}
        </aside>
      </section>
    </main>
  );
}

function StatusBadge({ submission, locale }: { submission: SubmissionDetail | null; locale: Locale }) {
  const label = submission?.result ?? submission?.status ?? "idle";
  const verdict = verdictInfo(label, locale);
  return <strong className={`status-badge ${label.toLowerCase()}`} title={verdict.description}>{verdict.label}</strong>;
}

function TabButton({ tab, active, onClick, children }: { tab: DetailTab; active: DetailTab; onClick: (tab: DetailTab) => void; children: React.ReactNode }) {
  return <button title={String(children)} className={active === tab ? "active" : ""} role="tab" aria-selected={active === tab} onClick={() => onClick(tab)}>{children}</button>;
}

function LazySurface({ label, className = "" }: { label: string; className?: string }) {
  return <div className={className ? `lazy-surface ${className}` : "lazy-surface"}>{label}</div>;
}

function DetailDock({
  detailTab,
  setDetailTab,
  problem,
  solution,
  events,
  submission,
  theme,
  trail,
  problemId,
  locale,
  authenticated,
  currentUser,
  onRequireAuth,
}: {
  detailTab: DetailTab;
  setDetailTab: (tab: DetailTab) => void;
  problem?: ProblemDetail;
  solution?: { explanation: string; code: string; language: string };
  events: JudgeEvent[];
  submission: SubmissionDetail | null;
  theme: AppTheme;
  trail: SubmissionDetail[];
  problemId: string;
  locale: Locale;
  authenticated: boolean;
  currentUser: CurrentUser | null;
  onRequireAuth: () => void;
}) {
  const text = getUI(locale);
  return (
    <section className="detail-dock statement-detail-dock judge-region">
      <div className="tabs" role="tablist" aria-label={localeText(locale, { zh: "题目详情", en: "Problem details" })}>
        <TabButton tab="cases" active={detailTab} onClick={setDetailTab}>{text.publicCases}</TabButton>
        <TabButton tab="solution" active={detailTab} onClick={setDetailTab}>{text.solution}</TabButton>
        <TabButton tab="judge" active={detailTab} onClick={setDetailTab}>{text.judge}</TabButton>
        <TabButton tab="trail" active={detailTab} onClick={setDetailTab}>{text.trail}</TabButton>
        <TabButton tab="discussion" active={detailTab} onClick={setDetailTab}>{text.discussion}</TabButton>
      </div>
      <div className="detail-panel">
        {detailTab === "cases" ? <SampleCases problem={problem} locale={locale} /> : null}
        {detailTab === "solution" ? <OfficialSolution problem={problem} solution={solution} locale={locale} /> : null}
        {detailTab === "judge" ? (
          <Suspense fallback={<LazySurface className="timeline" label={localeText(locale, { zh: "正在加载判题记录...", en: "Loading judge timeline..." })} />}>
            <JudgeTimeline events={events} submission={submission} theme={theme} />
          </Suspense>
        ) : null}
        {detailTab === "trail" ? (
          <Suspense fallback={<LazySurface className="trail" label={localeText(locale, { zh: "正在加载提交轨迹...", en: "Loading submission trail..." })} />}>
            <SubmissionTrail submissions={trail} locale={locale} />
          </Suspense>
        ) : null}
        {detailTab === "discussion" ? <DiscussionPanel problemId={problemId} locale={locale} authenticated={authenticated} currentUser={currentUser} onRequireAuth={onRequireAuth} /> : null}
      </div>
    </section>
  );
}

function ProblemStatement({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = getUI(locale);
  const displayProblem = localizedProblem(problem, locale);
  if (!displayProblem) return <p className="muted">{text.loadingProblem}</p>;
  return (
    <article className="prose-panel">
      <MarkdownBlock value={displayProblem.description} />
      <p className="muted">{text.acceptance} {percent(displayProblem.ac_rate)}%, {text.submissions} {displayProblem.total_submissions}</p>
    </article>
  );
}

function ProblemGuidance({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = getUI(locale);
  const displayProblem = localizedProblem(problem, locale);
  return (
    <section className="problem-guidance">
      <ProblemVisual problem={problem} locale={locale} />
      <article className="prose-panel hint-panel">
        <h3>{text.officialHint}</h3>
        {displayProblem?.hint ? <MarkdownBlock value={displayProblem.hint} /> : <p>{text.noHint}</p>}
      </article>
    </section>
  );
}

function ProblemVisual({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const visual = getVisualSpec(problem);
  return (
    <section className="visual-panel" aria-label={localeText(locale, { zh: "图形化讲解", en: "Visual explanation" })}>
      <h3>{localeText(locale, visual.title)}</h3>
      <div className="visual-flow">
        {localeValue(locale, visual.steps).map((step, index) => (
          <div className="visual-step" key={step}>
            <span>{index + 1}</span>
            <p>{step}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function functionSignaturePreview(starter: string, language: string, fallback: string): string {
  const lines = starter.split("\n").map((line) => line.trim()).filter(Boolean);
  const line = lines.find((item) => {
    if (item.startsWith("#") || item.startsWith("using ") || item.startsWith("import ") || item.startsWith("class ")) return false;
    if (language === "java") return /^(public|private|protected)\s+/.test(item);
    if (language === "golang") return item.startsWith("func ");
    if (language === "javascript" || language === "typescript") return item.startsWith("function ");
    return item.includes("(") && item.includes(")");
  });
  return (line ?? fallback).replace(/\s*\{\s*$/, "");
}

function FunctionFrame({ problem, mode, language, locale }: { problem?: ProblemDetail; mode: JudgeMode; language: string; locale: Locale }) {
  const text = getUI(locale);
  if (mode !== "function") return <div className="function-frame">{text.acmFrame}</div>;
  const spec = getFunctionSpec(problem);
  if (!spec) return <div className="function-frame warning">{text.noFunctionFrame}</div>;
  const starter = buildStarter(problem, language, "function", locale);
  const signature = language === "python"
    ? spec.signature
    : functionSignaturePreview(starter, language, spec.signature);
  return (
    <div className="function-frame">
      <strong>{signature}</strong>
      <span>{getLocalizedFunctionDescription(problem, locale)}</span>
    </div>
  );
}

function SampleCases({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = getUI(locale);
  if (!problem) return <p className="muted">{text.loadingCases}</p>;
  return (
    <div className="sample-cases">
      <div className="case-grid">
        {problem.sample_testcases.map((testcase, index) => (
          <article className="sample-card" key={`${testcase.input}-${index}`}>
            <h3>
              {localeText(locale, { zh: "示例", en: "Example" })} {index + 1}
              {testcase.display_mode ? <span className="case-chip sample">{authoringModeLabel(testcase.display_mode, locale)}</span> : null}
            </h3>
            <div className="sample-row">
              <span>{text.input}</span>
              <pre>{testcase.input}</pre>
            </div>
            <div className="sample-row">
              <span>{text.output}</span>
              <pre>{testcase.output}</pre>
            </div>
            {testcase.explanation ? (
              <div className="sample-row">
                <span>{text.explanation}</span>
                <MarkdownBlock value={testcase.explanation} className="sample-explanation" />
              </div>
            ) : null}
          </article>
        ))}
      </div>
      <ProblemGuidance problem={problem} locale={locale} />
    </div>
  );
}

function OfficialSolution({ problem, solution, locale }: { problem?: ProblemDetail; solution?: { explanation: string; code: string; language: string }; locale: Locale }) {
  if (!solution) {
    return (
      <article className="prose-panel solution-fallback">
        <h3>{localeText(locale, { zh: "题解思路", en: "Solution approach" })}</h3>
        <p>{getUI(locale).noSolution}</p>
      </article>
    );
  }
  return (
    <article className="prose-panel">
      <MarkdownBlock value={solution.explanation} />
      {solution.code.trim() ? (
        <Suspense fallback={<pre className="sample">{solution.code}</pre>}>
          <CodeBlock code={solution.code} language={solution.language} />
        </Suspense>
      ) : null}
    </article>
  );
}

function visibleDiscussionPosts(posts: ProblemDiscussion[]): ProblemDiscussion[] {
  return posts
    .filter((post) => !post.is_template)
    .map((post) => ({ ...post, replies: visibleDiscussionPosts(post.replies ?? []) }));
}

function addDiscussionToTree(posts: ProblemDiscussion[], created: ProblemDiscussion, parentId?: string | null): ProblemDiscussion[] {
  if (!parentId) return [created, ...posts.filter((post) => post.id !== created.id)];
  return posts.map((post) => {
    if (post.id === parentId) {
      const replies = [created, ...(post.replies ?? []).filter((reply) => reply.id !== created.id)];
      return { ...post, replies, reply_count: Math.max(post.reply_count + 1, replies.length) };
    }
    return { ...post, replies: addDiscussionToTree(post.replies ?? [], created, parentId) };
  });
}

function updateDiscussionInTree(
  posts: ProblemDiscussion[],
  discussionId: string,
  updater: (post: ProblemDiscussion) => ProblemDiscussion,
): ProblemDiscussion[] {
  return posts.map((post) => {
    const next = post.id === discussionId ? updater(post) : post;
    return { ...next, replies: updateDiscussionInTree(next.replies ?? [], discussionId, updater) };
  });
}

function DiscussionItem({
  post,
  depth,
  locale,
  authenticated,
  currentUser,
  activeReplyId,
  replyDraft,
  busyId,
  onReplyStart,
  onReplyChange,
  onReplySubmit,
  onLikeToggle,
  onDelete,
}: {
  post: ProblemDiscussion;
  depth: number;
  locale: Locale;
  authenticated: boolean;
  currentUser: CurrentUser | null;
  activeReplyId: string | null;
  replyDraft: string;
  busyId: string | null;
  onReplyStart: (postId: string) => void;
  onReplyChange: (postId: string, value: string) => void;
  onReplySubmit: (postId: string) => void;
  onLikeToggle: (post: ProblemDiscussion) => void;
  onDelete: (post: ProblemDiscussion) => void;
}) {
  const canDelete = Boolean(post.can_delete || currentUser?.id === post.user_id || currentUser?.role === "admin");
  const deleted = post.is_deleted;
  const labels = {
    reply: localeText(locale, { zh: "回复", en: "Reply" }),
    send: localeText(locale, { zh: "发送回复", en: "Send reply" }),
    cancel: localeText(locale, { zh: "取消", en: "Cancel" }),
    like: localeText(locale, { zh: "赞", en: "Like" }),
    unlike: localeText(locale, { zh: "取消赞", en: "Unlike" }),
    delete: localeText(locale, { zh: "删除", en: "Delete" }),
    deleted: localeText(locale, { zh: "评论已删除", en: "Comment deleted" }),
    placeholder: localeText(locale, { zh: "回复这条讨论。不要粘贴隐藏用例。", en: "Reply to this thread. Do not paste hidden cases." }),
  };
  const replies = visibleDiscussionPosts(post.replies ?? []);
  return (
    <article className={`discussion-post ${deleted ? "deleted" : ""}`} style={{ "--discussion-depth": Math.min(depth, 6) } as React.CSSProperties}>
      <div className="discussion-post-header">
        <strong>{post.author}</strong>
        <small>{new Date(post.created_at).toLocaleString()}</small>
      </div>
      {deleted ? <p>{labels.deleted}</p> : <MarkdownBlock value={post.body} className="discussion-markdown" />}
      {!deleted ? (
        <div className="discussion-actions">
          <button type="button" className={post.liked_by_me ? "active" : ""} disabled={busyId === post.id} onClick={() => onLikeToggle(post)}>
            {post.liked_by_me ? labels.unlike : labels.like} {post.like_count ? post.like_count : ""}
          </button>
          <button type="button" onClick={() => onReplyStart(post.id)}>{labels.reply}</button>
          {canDelete ? <button type="button" className="danger-text" disabled={busyId === post.id} onClick={() => onDelete(post)}>{labels.delete}</button> : null}
        </div>
      ) : null}
      {activeReplyId === post.id ? (
        <div className="discussion-reply-box">
          <textarea
            value={activeReplyId === post.id ? replyDraft : ""}
            onChange={(event) => onReplyChange(post.id, event.target.value)}
            placeholder={labels.placeholder}
            disabled={!authenticated || busyId === post.id}
            maxLength={2000}
          />
          <div className="discussion-actions">
            <button className="primary" type="button" disabled={!authenticated || !replyDraft.trim() || busyId === post.id} onClick={() => onReplySubmit(post.id)}>{labels.send}</button>
            <button type="button" onClick={() => onReplyStart("")}>{labels.cancel}</button>
          </div>
        </div>
      ) : null}
      {replies.length ? (
        <div className="discussion-replies">
          {replies.map((reply) => (
            <DiscussionItem
              key={reply.id}
              post={reply}
              depth={depth + 1}
              locale={locale}
              authenticated={authenticated}
              currentUser={currentUser}
              activeReplyId={activeReplyId}
              replyDraft={replyDraft}
              busyId={busyId}
              onReplyStart={onReplyStart}
              onReplyChange={onReplyChange}
              onReplySubmit={onReplySubmit}
              onLikeToggle={onLikeToggle}
              onDelete={onDelete}
            />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function DiscussionPanel({
  problemId,
  locale,
  authenticated,
  currentUser,
  onRequireAuth,
}: {
  problemId: string;
  locale: Locale;
  authenticated: boolean;
  currentUser: CurrentUser | null;
  onRequireAuth: () => void;
}) {
  const text = getUI(locale);
  const [body, setBody] = useState("");
  const [activeReplyId, setActiveReplyId] = useState<string | null>(null);
  const [replyDraft, setReplyDraft] = useState("");
  const [posting, setPosting] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const discussionsQuery = useQuery({
    queryKey: ["problem-discussions", problemId],
    queryFn: () => api.discussions(problemId),
    enabled: Boolean(problemId),
  });
  const posts = visibleDiscussionPosts(discussionsQuery.data ?? []);

  function setDiscussionCache(updater: (items: ProblemDiscussion[]) => ProblemDiscussion[]) {
    queryClient.setQueryData<ProblemDiscussion[]>(["problem-discussions", problemId], (items = []) => updater(items));
  }

  async function post(parentId?: string | null) {
    if (!authenticated) {
      onRequireAuth();
      return;
    }
    const source = parentId ? replyDraft : body;
    const trimmed = source.trim();
    if (!trimmed) return;
    try {
      setPosting(true);
      setError(null);
      const created = await api.createDiscussion(problemId, trimmed, parentId);
      setDiscussionCache((items) => addDiscussionToTree(items, created, parentId));
      if (parentId) {
        setActiveReplyId(null);
        setReplyDraft("");
      } else {
        setBody("");
      }
    } catch (postError) {
      if (isUnauthorized(postError)) {
        localStorage.removeItem("fastoj.jwt");
        onRequireAuth();
      }
      setError(postError instanceof Error ? postError.message : localeText(locale, { zh: "发布失败。", en: "Post failed." }));
    } finally {
      setPosting(false);
    }
  }

  async function toggleLike(post: ProblemDiscussion) {
    if (!authenticated) {
      onRequireAuth();
      return;
    }
    setBusyId(post.id);
    setError(null);
    try {
      const updated = post.liked_by_me
        ? await api.unlikeDiscussion(problemId, post.id)
        : await api.likeDiscussion(problemId, post.id);
      setDiscussionCache((items) => updateDiscussionInTree(items, post.id, () => updated));
    } catch (likeError) {
      if (isUnauthorized(likeError)) {
        localStorage.removeItem("fastoj.jwt");
        onRequireAuth();
      }
      setError(likeError instanceof Error ? likeError.message : localeText(locale, { zh: "操作失败。", en: "Action failed." }));
    } finally {
      setBusyId(null);
    }
  }

  async function deletePost(post: ProblemDiscussion) {
    setBusyId(post.id);
    setError(null);
    try {
      await api.deleteDiscussion(problemId, post.id);
      setDiscussionCache((items) => updateDiscussionInTree(items, post.id, (item) => ({
        ...item,
        body: "",
        is_deleted: true,
      })));
    } catch (deleteError) {
      if (isUnauthorized(deleteError)) {
        localStorage.removeItem("fastoj.jwt");
        onRequireAuth();
      }
      setError(deleteError instanceof Error ? deleteError.message : localeText(locale, { zh: "删除失败。", en: "Delete failed." }));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="discussion-panel">
      <h3>{text.discussionTitle}</h3>
      <p className="muted">{authenticated ? text.discussionLocalNotice : text.discussionLoginRequired}</p>
      {discussionsQuery.isLoading ? <p className="muted">{localeText(locale, { zh: "正在加载讨论...", en: "Loading discussion..." })}</p> : null}
      {discussionsQuery.isError ? <p className="muted">{localeText(locale, { zh: "讨论加载失败。", en: "Discussion failed to load." })}</p> : null}
      {error ? <p className="muted">{error}</p> : null}
      <textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        placeholder={text.discussionPlaceholder}
        disabled={!authenticated || posting}
        maxLength={2000}
      />
      <button className="primary" onClick={() => post()} disabled={!authenticated || !body.trim() || posting}>
        {posting ? localeText(locale, { zh: "发布中...", en: "Posting..." }) : text.postDiscussion}
      </button>
      {posts.length ? posts.map((item) => (
        <DiscussionItem
          key={item.id}
          post={item}
          depth={0}
          locale={locale}
          authenticated={authenticated}
          currentUser={currentUser}
          activeReplyId={activeReplyId}
          replyDraft={replyDraft}
          busyId={busyId}
          onReplyStart={(postId) => {
            setActiveReplyId(postId || null);
            setReplyDraft("");
          }}
          onReplyChange={(_, value) => setReplyDraft(value)}
          onReplySubmit={(postId) => post(postId)}
          onLikeToggle={toggleLike}
          onDelete={deletePost}
        />
      )) : null}
      {!discussionsQuery.isLoading && !discussionsQuery.isError && !posts.length ? <p className="muted">{text.noDiscussion}</p> : null}
    </section>
  );
}

const ADMIN_TEXT_BY_LOCALE = {
  zh: {
    title: "管理后台",
    copy: "管理题目、官方题解、测试用例和用户权限。隐藏用例仅在管理员界面显示。",
    users: "用户",
    problems: "题目与内容",
    noAccess: "当前账号没有管理权限。",
    back: "返回题库",
    active: "启用",
    disabled: "停用",
    admin: "管理员",
    user: "用户",
    cases: "用例",
    hidden: "隐藏",
    solutions: "题解",
    public: "公开",
    private: "隐藏",
    problemAgent: "出题 Agent",
    adminAgentSection: "出题 Agent",
    adminUsersSection: "用户与权限",
    adminProblemsSection: "已发布题目",
    agentNotice: "AI 生成内容只保存为草稿，管理员审批前不会发布。",
    authoringTab: "原创出题",
    importTab: "导入题目",
    generateDraft: "生成草稿",
    importDraft: "导入为草稿",
    sourceUrlLabel: "来源链接（可选）",
    rawMaterialLabel: "原始材料",
    rawMaterialPlaceholder: "粘贴网上看到的题面、示例、解释、代码或笔记。原文只在管理员草稿中可见，不会发布给普通用户。",
    importNotesLabel: "适配要求",
    importNotesPlaceholder: "补充希望如何改写和适配，例如函数签名偏好、输入规模、必须保留的样例、需要规避的解法或输出顺序。",
    importedDraft: "导入",
    importSource: "导入来源",
    rawMaterialLength: "原始材料长度",
    rawMaterialPreview: "原始材料预览",
    rawMaterialRequired: "请粘贴至少 20 个字符的原始材料。",
    agentFollowUp: "追问与重试",
    agentFollowUpPlaceholder: "补充希望 Agent 如何修复、改写或重试的要求。",
    sendFollowUp: "发送追问",
    retryRun: "重试运行",
    followUpRequired: "请先填写追问内容。",
    followUpSent: "追问已发送，已刷新执行路径。",
    retryStarted: "重试已提交，已刷新执行路径。",
    approveDraft: "批准发布",
    rejectDraft: "拒绝草稿",
    draftPreview: "草稿预览",
    draftEdit: "草稿编辑",
    revalidateDraft: "保存并重新校验",
    resetDraftEdit: "取消更改",
    confirmApproveDraft: "确定发布当前已保存并通过校验的草稿吗？未保存的更改不会被发布。",
    confirmRejectDraft: "确定拒绝这个草稿吗？",
    addPublicCase: "新增公开用例",
    addHiddenCase: "新增隐藏用例",
    validation: "验证报告",
    steps: "执行轨迹",
    searchUsers: "搜索用户名或邮箱",
    searchProblems: "搜索题名或 slug",
    allRoles: "全部角色",
    allStatus: "全部状态",
    allDifficulty: "全部难度",
    allVisibility: "全部可见性",
    manage: "管理",
    edit: "编辑",
    save: "保存",
    cancel: "取消",
    previous: "上一页",
    next: "下一页",
    noResults: "没有匹配结果。",
    pageSummary: "第 {page} / {totalPages} 页，共 {total} 条",
    titleLabel: "标题",
    slugLabel: "Slug",
    descriptionLabel: "描述",
    hintLabel: "提示",
    tagsLabel: "标签（逗号分隔）",
    modeLabel: "模式",
    targetLanguagesLabel: "目标语言",
    timeLimitLabel: "时间限制",
    memoryLimitLabel: "内存限制",
    functionSignatureLabel: "函数签名",
    inputFormatLabel: "输入格式",
    outputFormatLabel: "输出格式",
    officialSolutionsLabel: "多语言官方解法",
    officialCodeLabel: "官方解法代码",
    functionOfficialCodeLabel: "函数式官方解法代码",
    acmOfficialCodeLabel: "ACM 官方程序代码",
    officialExplanationLabel: "官方解法说明",
    dualModeSolutionNote: "双模式使用一份函数式规范解法；ACM 练习会用相同的函数 JSON 参数输入和期望输出合同。",
    aiFillSolution: "AI 填充",
    aiFillingSolution: "正在填充...",
    aiFillSolutionDone: "AI 已填充该语言解法，请检查后保存并重新校验。",
    timeComplexityLabel: "时间复杂度",
    spaceComplexityLabel: "空间复杂度",
    testcaseDetails: "用例管理",
    newTestcase: "新增用例",
    inputLabel: "输入",
    outputLabel: "输出",
    scoreLabel: "分数",
    orderLabel: "顺序",
    sample: "样例",
    add: "新增",
    delete: "删除",
    deleteProblem: "删除题目",
    confirmDeleteProblem: "确定删除“{title}”吗？相关提交记录、题解、测试用例和用例结果都会被删除。",
    loading: "加载中...",
    noTestcases: "还没有测试用例。",
  },
  en: {
    title: "Admin",
    copy: "Manage problems, official solutions, test cases, and user permissions. Hidden cases are visible only to admins.",
    users: "Users",
    problems: "Problems and content",
    noAccess: "This account does not have admin access.",
    back: "Back to problems",
    active: "Active",
    disabled: "Disabled",
    admin: "Admin",
    user: "User",
    cases: "cases",
    hidden: "hidden",
    solutions: "solutions",
    public: "Public",
    private: "Private",
    problemAgent: "Problem Agent",
    adminAgentSection: "Problem Agent",
    adminUsersSection: "Users and permissions",
    adminProblemsSection: "Published problems",
    agentNotice: "AI-generated content is saved as a draft and is never published before admin approval.",
    authoringTab: "Original",
    importTab: "Import",
    generateDraft: "Generate draft",
    importDraft: "Import draft",
    sourceUrlLabel: "Source URL (optional)",
    rawMaterialLabel: "Raw material",
    rawMaterialPlaceholder: "Paste the statement, examples, explanations, code, or notes you found. Raw source text stays admin-only and is not published to users.",
    importNotesLabel: "Adaptation notes",
    importNotesPlaceholder: "Add rewrite and adaptation requirements, such as signature preference, input scale, samples to preserve, algorithms to avoid, or output ordering.",
    importedDraft: "Imported",
    importSource: "Import source",
    rawMaterialLength: "Raw material length",
    rawMaterialPreview: "Raw material preview",
    rawMaterialRequired: "Paste at least 20 characters of raw material.",
    agentFollowUp: "Follow-up and retry",
    agentFollowUpPlaceholder: "Add what the agent should fix, rewrite, or retry.",
    sendFollowUp: "Send follow-up",
    retryRun: "Retry run",
    followUpRequired: "Enter a follow-up first.",
    followUpSent: "Follow-up sent. Agent runs refreshed.",
    retryStarted: "Retry submitted. Agent runs refreshed.",
    approveDraft: "Approve",
    rejectDraft: "Reject",
    draftPreview: "Draft preview",
    draftEdit: "Draft editor",
    revalidateDraft: "Save and revalidate",
    resetDraftEdit: "Discard changes",
    confirmApproveDraft: "Publish the current saved and validated draft? Unsaved edits will not be published.",
    confirmRejectDraft: "Reject this draft?",
    addPublicCase: "Add public case",
    addHiddenCase: "Add hidden case",
    validation: "Validation report",
    steps: "Run steps",
    searchUsers: "Search username or email",
    searchProblems: "Search title or slug",
    allRoles: "All roles",
    allStatus: "All status",
    allDifficulty: "All difficulty",
    allVisibility: "All visibility",
    manage: "Manage",
    edit: "Edit",
    save: "Save",
    cancel: "Cancel",
    previous: "Previous",
    next: "Next",
    noResults: "No matching results.",
    pageSummary: "Page {page} / {totalPages}, {total} total",
    titleLabel: "Title",
    slugLabel: "Slug",
    descriptionLabel: "Description",
    hintLabel: "Hint",
    tagsLabel: "Tags, comma separated",
    modeLabel: "Mode",
    targetLanguagesLabel: "Target languages",
    timeLimitLabel: "Time limit",
    memoryLimitLabel: "Memory limit",
    functionSignatureLabel: "Function signature",
    inputFormatLabel: "Input format",
    outputFormatLabel: "Output format",
    officialSolutionsLabel: "Official solutions by language",
    officialCodeLabel: "Official solution code",
    functionOfficialCodeLabel: "Canonical function solution code",
    acmOfficialCodeLabel: "ACM official program code",
    officialExplanationLabel: "Official solution explanation",
    dualModeSolutionNote: "Dual mode uses one canonical function solution. ACM practice shares the same function JSON argument input and expected-output contract.",
    aiFillSolution: "AI fill",
    aiFillingSolution: "Filling...",
    aiFillSolutionDone: "AI filled this language solution. Review it, then save and revalidate.",
    timeComplexityLabel: "Time complexity",
    spaceComplexityLabel: "Space complexity",
    testcaseDetails: "Testcase manager",
    newTestcase: "New testcase",
    inputLabel: "Input",
    outputLabel: "Output",
    scoreLabel: "Score",
    orderLabel: "Order",
    sample: "Sample",
    add: "Add",
    delete: "Delete",
    deleteProblem: "Delete problem",
    confirmDeleteProblem: "Delete \"{title}\"? Related submissions, solutions, testcases, and testcase results will also be deleted.",
    loading: "Loading...",
    noTestcases: "No testcases yet.",
  },
} as const;

type AdminText = Record<keyof (typeof ADMIN_TEXT_BY_LOCALE)["zh"], string>;
const ADMIN_TEXT_LOOKUP: Partial<Record<Locale, AdminText>> & Record<"zh", AdminText> = ADMIN_TEXT_BY_LOCALE;

export function getAdminText(locale: Locale): AdminText {
  return ADMIN_TEXT_LOOKUP[locale] ?? ADMIN_TEXT_LOOKUP.zh;
}

function agentRunTypeLabel(runType: string, locale: Locale): string {
  const labels: Record<string, { zh: string; en: string }> = {
    problem_authoring: { zh: "原创出题", en: "Problem authoring" },
    problem_import: { zh: "题目导入", en: "Problem import" },
    problem_authoring_solution: { zh: "AI 填充题解", en: "Solution generation" },
  };
  return labels[runType] ? localeText(locale, labels[runType]) : runType;
}

function agentRunStatusLabel(status: string, locale: Locale): string {
  const labels: Record<string, { zh: string; en: string }> = {
    running: { zh: "运行中", en: "Running" },
    succeeded: { zh: "成功", en: "Succeeded" },
    failed: { zh: "失败", en: "Failed" },
  };
  return labels[status] ? localeText(locale, labels[status]) : status;
}

function agentStatusClass(status: string): string {
  return `agent-status-${status.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}

function shortDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function truncateTraceText(value: string, limit = 720): string {
  return value.length > limit ? `${value.slice(0, limit - 3)}...` : value;
}

const TRACE_REDACT_KEYWORDS = [
  "raw_material",
  "code",
  "official_solution_code",
  "current_code",
  "hidden_testcases",
  "testcases_json",
  "prompt",
  "token",
  "secret",
  "password",
];

function shouldRedactTraceKey(key: string | undefined): boolean {
  if (!key) return false;
  const normalized = key.toLowerCase();
  return TRACE_REDACT_KEYWORDS.some((keyword) => normalized.includes(keyword));
}

function sanitizeTraceValue(value: unknown, key?: string, depth = 0): unknown {
  if (shouldRedactTraceKey(key)) {
    const length = typeof value === "string" ? value.length : JSON.stringify(value ?? "").length;
    return `[redacted ${key ?? "value"}; ${length} chars]`;
  }
  if (typeof value === "string") {
    return truncateTraceText(value);
  }
  if (typeof value !== "object" || value === null) {
    return value;
  }
  if (depth >= 4) {
    return "[truncated nested value]";
  }
  if (Array.isArray(value)) {
    const items = value.slice(0, 20).map((item) => sanitizeTraceValue(item, key, depth + 1));
    if (value.length > 20) {
      items.push(`[truncated ${value.length - 20} more items]`);
    }
    return items;
  }
  const entries = Object.entries(value as Record<string, unknown>).slice(0, 40);
  const output: Record<string, unknown> = {};
  for (const [entryKey, entryValue] of entries) {
    output[entryKey] = sanitizeTraceValue(entryValue, entryKey, depth + 1);
  }
  const extraCount = Object.keys(value as Record<string, unknown>).length - entries.length;
  if (extraCount > 0) {
    output.__truncated = `${extraCount} more fields`;
  }
  return output;
}

function traceField(source: Record<string, unknown> | undefined, name: string): unknown {
  return source && Object.prototype.hasOwnProperty.call(source, name) ? source[name] : undefined;
}

function agentStepSummary(step: AgentStep, locale: Locale): string {
  const input = recordValue(step.input);
  const output = recordValue(step.output);
  const parts: string[] = [];
  if (step.tool_name) parts.push(step.tool_name);
  const attempt = traceField(input, "attempt") ?? traceField(output, "attempt");
  if (attempt !== undefined) {
    parts.push(localeText(locale, { zh: `第 ${String(attempt)} 次尝试`, en: `attempt ${String(attempt)}` }));
  }
  const repairAttempt = traceField(input, "repair_attempt");
  if (typeof repairAttempt === "number" && repairAttempt > 0) {
    parts.push(localeText(locale, { zh: `修复 ${repairAttempt}`, en: `repair ${repairAttempt}` }));
  }
  const rawLength = traceField(output, "raw_length");
  if (typeof rawLength === "number") {
    parts.push(localeText(locale, { zh: `模型返回 ${rawLength} 字符`, en: `${rawLength} raw chars` }));
  }
  const caseCount = traceField(input, "case_count");
  if (typeof caseCount === "number") {
    parts.push(localeText(locale, { zh: `${caseCount} 个用例`, en: `${caseCount} cases` }));
  }
  const summary = traceField(output, "summary");
  if (typeof summary === "string" && summary.trim()) parts.push(summary);
  const passed = traceField(output, "passed");
  if (typeof passed === "boolean") {
    parts.push(passed ? localeText(locale, { zh: "校验通过", en: "validation passed" }) : localeText(locale, { zh: "校验未通过", en: "validation failed" }));
  }
  if (step.error_message) parts.push(truncateTraceText(step.error_message, 140));
  return parts.join(" · ") || localeText(locale, { zh: "查看该步骤的输入和输出摘要。", en: "View this step's input and output summary." });
}

function agentRunSummary(run: AgentRun, locale: Locale): string {
  const stepCount = run.steps?.length ?? 0;
  return [
    agentRunTypeLabel(run.run_type, locale),
    run.model_profile,
    agentRunStatusLabel(run.status, locale),
    localeText(locale, { zh: `${stepCount} 步`, en: `${stepCount} steps` }),
  ].filter(Boolean).join(" · ");
}

function mergeAgentRuns(...groups: Array<AgentRun[] | undefined>): AgentRun[] {
  const byId = new Map<string, AgentRun>();
  for (const group of groups) {
    for (const run of group ?? []) {
      byId.set(run.id, run);
    }
  }
  return [...byId.values()].sort((left, right) => (
    new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
  ));
}

function upsertAgentRun(runs: AgentRun[] | undefined, run: AgentRun): AgentRun[] {
  return mergeAgentRuns([run], runs);
}

function mergeAgentStepIntoRun(run: AgentRun, step: AgentStep): AgentRun {
  const steps = [...(run.steps ?? []).filter((item) => item.id !== step.id), step].sort(
    (left, right) => left.step_index - right.step_index,
  );
  const nextStatus = run.status === "running" && step.status === "failed" ? run.status : run.status;
  return { ...run, status: nextStatus, steps };
}

function mergeAgentStepIntoRuns(runs: AgentRun[] | undefined, step: AgentStep): AgentRun[] {
  const current = runs ?? [];
  return current.map((run) => run.id === step.run_id ? mergeAgentStepIntoRun(run, step) : run);
}

function latestAgentRunId(runs: AgentRun[] | undefined): string | null {
  const sorted = mergeAgentRuns(runs);
  return sorted[0]?.id ?? null;
}

function sessionTimestamp(session: AgentSession): number {
  const timestamp = Date.parse(session.updated_at || session.created_at || "");
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function mergeAgentSessions(...groups: Array<AgentSession[] | AgentSession | null | undefined>): AgentSession[] {
  const byId = new Map<string, AgentSession>();
  for (const group of groups) {
    const items = Array.isArray(group) ? group : group ? [group] : [];
    for (const session of items) {
      if (!session?.id) continue;
      const current = byId.get(session.id);
      byId.set(session.id, current ? { ...current, ...session } : session);
    }
  }
  return [...byId.values()].sort((left, right) => sessionTimestamp(right) - sessionTimestamp(left));
}

function agentSessionDrafts(session: AgentSession | null | undefined): ProblemDraft[] {
  return mergeDrafts(session?.drafts, session?.latest_draft);
}

function agentSessionRuns(session: AgentSession | null | undefined): AgentRun[] {
  return mergeAgentRuns(session?.runs, session?.latest_run ? [session.latest_run] : undefined);
}

function agentRunSessionId(run: AgentRun | null | undefined): string | null {
  const inputSession = typeof run?.input?.agent_session_id === "string" ? run.input.agent_session_id : "";
  const outputSession = typeof run?.output?.agent_session_id === "string" ? run.output.agent_session_id : "";
  return inputSession || outputSession || null;
}

function latestAgentDraft(session: AgentSession | null | undefined): ProblemDraft | null {
  return session?.latest_draft ?? agentSessionDrafts(session)[0] ?? null;
}

function agentSessionSourceLabel(session: AgentSession, locale: Locale): string | null {
  if (session.source_kind === "imported") {
    return localeText(locale, { zh: "导入", en: "Imported" });
  }
  if (session.source_kind) {
    return session.source_kind;
  }
  return null;
}

function TraceJsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="trace-json-block">
      <strong>{label}</strong>
      <pre>{JSON.stringify(sanitizeTraceValue(value), null, 2)}</pre>
    </div>
  );
}

function agentFailureAdvice(run: AgentRun, locale: Locale): string | null {
  const message = run.error_message ?? "";
  if (/without a problem draft object/i.test(message) || /did not return a JSON object for the problem draft/i.test(message)) {
    return localeText(locale, {
      zh: "模型没有返回 FastOJ 需要的 problem draft JSON。可以重试、切换模型，或把原始题面拆得更结构化一些。",
      en: "The model did not return the problem draft JSON FastOJ expected. Retry, switch models, or shorten and structure the source material.",
    });
  }
  return null;
}

type AgentTimelineItem =
  | { kind: "message"; id: string; createdAt: string; role: "user" | "assistant" | "system"; message: string; runId?: string | null; pending?: boolean }
  | { kind: "run"; id: string; createdAt: string; run: AgentRun }
  | { kind: "draft"; id: string; createdAt: string; draft: ProblemDraft };

function agentTimelineTime(value: string | null | undefined): number {
  if (!value) return 0;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function localFollowUpCreatedAt(id: string): string {
  const timestamp = Number(id.split(".")[0]);
  return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : new Date().toISOString();
}

function AgentRunStepDetail({
  run,
  locale,
  expandedStepIds,
  onToggleStep,
}: {
  run: AgentRun;
  locale: Locale;
  expandedStepIds: Set<string>;
  onToggleStep: (stepId: string) => void;
}) {
  return (
    <section className="agent-run-detail">
      <div className="agent-run-detail-head">
        <strong>{agentRunSummary(run, locale)}</strong>
        <span className="muted">{shortDateTime(run.created_at)} - {shortDateTime(run.finished_at)}</span>
      </div>
      {run.error_message ? <p className="agent-run-error">{run.error_message}</p> : null}
      {agentFailureAdvice(run, locale) ? <p className="muted">{agentFailureAdvice(run, locale)}</p> : null}
      <div className="agent-step-list">
        {(run.steps ?? []).map((step) => {
          const expanded = expandedStepIds.has(step.id);
          return (
            <article className={`agent-step ${agentStatusClass(step.status)}`} key={step.id}>
              <button className="agent-step-summary" onClick={() => onToggleStep(step.id)}>
                <span>
                  <strong>{step.step_index}. {step.step_type}</strong>
                  <small>{agentStepSummary(step, locale)}</small>
                </span>
                <span className={`agent-status-chip ${agentStatusClass(step.status)}`}>{agentRunStatusLabel(step.status, locale)}</span>
              </button>
              {expanded ? (
                <div className="agent-step-details">
                  <TraceJsonBlock label={localeText(locale, { zh: "输入", en: "Input" })} value={step.input} />
                  <TraceJsonBlock label={localeText(locale, { zh: "输出", en: "Output" })} value={step.output} />
                  {step.error_message ? <TraceJsonBlock label={localeText(locale, { zh: "错误", en: "Error" })} value={step.error_message} /> : null}
                </div>
              ) : null}
            </article>
          );
        })}
        {run.steps?.length ? null : <p className="muted">{localeText(locale, { zh: "该运行还没有步骤记录。", en: "This run has no recorded steps." })}</p>}
      </div>
    </section>
  );
}

function AgentSessionTimeline({
  locale,
  text,
  session,
  runs,
  selectedRunId,
  selectedDraftId,
  expandedStepIds,
  loading,
  followUpDraft,
  followUpLines,
  followUpBusy,
  canFollowUp,
  emptyMessage,
  onSelectRun,
  onSelectDraft,
  onToggleStep,
  onFollowUpDraftChange,
  onFollowUpSubmit,
  onRetryRun,
}: {
  locale: Locale;
  text: AdminText;
  session: AgentSession | null;
  runs: AgentRun[];
  selectedRunId: string | null;
  selectedDraftId: string | null;
  expandedStepIds: Set<string>;
  loading: boolean;
  followUpDraft: string;
  followUpLines: AgentFollowUpLine[];
  followUpBusy: "chat" | "retry" | null;
  canFollowUp: boolean;
  emptyMessage: string;
  onSelectRun: (runId: string) => void;
  onSelectDraft: (draft: ProblemDraft) => void;
  onToggleStep: (stepId: string) => void;
  onFollowUpDraftChange: (value: string) => void;
  onFollowUpSubmit: () => void;
  onRetryRun: () => void;
}) {
  const selectedRun = runs.find((run) => run.id === selectedRunId) ?? null;
  const drafts = agentSessionDrafts(session);
  const knownMessages = new Set((session?.messages ?? []).map((message) => (
    `${message.role}:${message.run_id ?? ""}:${message.message}`
  )));
  const timelineItems: AgentTimelineItem[] = [
    ...(session?.messages ?? []).map((message): AgentTimelineItem => ({
      kind: "message",
      id: `message-${message.id}`,
      createdAt: message.created_at,
      role: message.role,
      message: message.message,
      runId: message.run_id,
    })),
    ...followUpLines
      .filter((line) => !knownMessages.has(`${line.role}:${line.runId ?? ""}:${line.message}`))
      .map((line): AgentTimelineItem => ({
        kind: "message",
        id: `local-${line.id}`,
        createdAt: localFollowUpCreatedAt(line.id),
        role: line.role,
        message: line.message,
        runId: line.runId,
        pending: true,
      })),
    ...runs.map((run): AgentTimelineItem => ({
      kind: "run",
      id: `run-${run.id}`,
      createdAt: run.created_at,
      run,
    })),
    ...drafts.map((draft): AgentTimelineItem => ({
      kind: "draft",
      id: `draft-${draft.id}`,
      createdAt: draft.updated_at ?? draft.created_at ?? "",
      draft,
    })),
  ].sort((left, right) => {
    const diff = agentTimelineTime(left.createdAt) - agentTimelineTime(right.createdAt);
    if (diff !== 0) return diff;
    const order = { message: 0, run: 1, draft: 2 };
    return order[left.kind] - order[right.kind];
  });
  const sourceLabel = session ? agentSessionSourceLabel(session, locale) : null;
  const hasTimeline = Boolean(session) || timelineItems.length > 0;

  return (
    <div className="agent-preview agent-runs-panel agent-session-panel">
      <div className="testcase-panel-head">
        <div>
          <h3>{localeText(locale, { zh: "会话时间线", en: "Session Timeline" })}</h3>
          {session ? (
            <span className="muted">
              {agentRunTypeLabel(session.run_type, locale)} · {session.run_count} {localeText(locale, { zh: "次运行", en: "runs" })} · {session.draft_count} {localeText(locale, { zh: "个草稿", en: "drafts" })}
            </span>
          ) : null}
        </div>
        {session ? <span className={`agent-status-chip ${agentStatusClass(session.status)}`}>{agentRunStatusLabel(session.status, locale)}</span> : null}
      </div>
      {loading ? <p className="muted">{localeText(locale, { zh: "正在加载会话...", en: "Loading session..." })}</p> : null}
      {!hasTimeline && !loading ? <p className="muted">{emptyMessage}</p> : null}
      {hasTimeline ? (
        <>
          {session ? (
            <section className="agent-session-summary">
              <strong>{session.title || localeText(locale, { zh: "未命名会话", en: "Untitled session" })}</strong>
              <span className="muted">{shortDateTime(session.updated_at)}</span>
              <span className="draft-status-line">
                {sourceLabel ? <span className="draft-status-chip imported">{sourceLabel}</span> : null}
                {session.mode ? <span>{authoringModeLabel(session.mode, locale)}</span> : null}
              </span>
            </section>
          ) : null}
          <div className="agent-timeline">
            {timelineItems.length ? timelineItems.map((item) => {
              if (item.kind === "message") {
                const label = item.role === "user"
                  ? localeText(locale, { zh: "管理员", en: "Admin" })
                  : item.role === "assistant"
                    ? "Agent"
                    : localeText(locale, { zh: "系统", en: "System" });
                return (
                  <article className={`agent-timeline-item message ${item.role}`} key={item.id}>
                    <div className="agent-message-bubble">
                      <strong>{label}</strong>
                      <MarkdownBlock value={item.message} className="agent-message-markdown" />
                      <small>{shortDateTime(item.createdAt)}{item.pending ? ` · ${localeText(locale, { zh: "待同步", en: "pending" })}` : ""}</small>
                    </div>
                  </article>
                );
              }
              if (item.kind === "draft") {
                const statusClass = draftStatusClass(item.draft.status);
                return (
                  <article className="agent-timeline-item draft" key={item.id}>
                    <button
                      type="button"
                      className={`agent-timeline-draft ${selectedDraftId === item.draft.id ? "active" : ""}`}
                      onClick={() => onSelectDraft(item.draft)}
                    >
                      <span>
                        <strong>{item.draft.title}</strong>
                        <small>{item.draft.slug || shortDateTime(item.createdAt)}</small>
                      </span>
                      <span className={`draft-status-chip ${statusClass}`}>{draftStatusLabel(item.draft.status, locale)}</span>
                    </button>
                  </article>
                );
              }
              const run = item.run;
              return (
                <article className={`agent-timeline-item run ${agentStatusClass(run.status)} ${selectedRunId === run.id ? "active" : ""}`} key={item.id}>
                  <button type="button" className="agent-timeline-run" onClick={() => onSelectRun(run.id)}>
                    <span className="agent-run-row-title">
                      <strong>{agentRunTypeLabel(run.run_type, locale)}</strong>
                      <span className={`agent-status-chip ${agentStatusClass(run.status)}`}>{agentRunStatusLabel(run.status, locale)}</span>
                    </span>
                    <span className="agent-run-meta">{run.model_profile} · {shortDateTime(run.created_at)}</span>
                    <span className="agent-run-meta">{run.draft_id ? localeText(locale, { zh: "已关联草稿", en: "linked draft" }) : localeText(locale, { zh: "未生成草稿", en: "no draft" })}</span>
                    {run.error_message ? <span className="agent-run-error">{truncateTraceText(run.error_message, 110)}</span> : null}
                  </button>
                  {selectedRunId === run.id ? (
                    <AgentRunStepDetail
                      run={run}
                      locale={locale}
                      expandedStepIds={expandedStepIds}
                      onToggleStep={onToggleStep}
                    />
                  ) : null}
                </article>
              );
            }) : <p className="muted">{localeText(locale, { zh: "这个会话还没有消息或运行记录。", en: "This session has no messages or runs yet." })}</p>}
          </div>
          <div className="agent-follow-up">
            <div>
              <strong>{text.agentFollowUp}</strong>
              <span className="muted">{selectedRun?.id ?? session?.id ?? ""}</span>
            </div>
            <textarea
              value={followUpDraft}
              onChange={(event) => onFollowUpDraftChange(event.target.value)}
              placeholder={text.agentFollowUpPlaceholder}
              maxLength={2000}
              disabled={!canFollowUp || Boolean(followUpBusy)}
            />
            <div className="agent-actions">
              <button className="primary" disabled={!canFollowUp || !followUpDraft.trim() || Boolean(followUpBusy)} onClick={onFollowUpSubmit}>
                {followUpBusy === "chat" ? text.loading : text.sendFollowUp}
              </button>
              <button disabled={!canFollowUp || Boolean(followUpBusy)} onClick={onRetryRun}>
                {followUpBusy === "retry" ? text.loading : text.retryRun}
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

function AgentDifficultyField({
  value,
  locale,
  onChange,
}: {
  value: "easy" | "medium" | "hard";
  locale: Locale;
  onChange: (value: "easy" | "medium" | "hard") => void;
}) {
  return (
    <label>{localeText(locale, { zh: "难度", en: "Difficulty" })}
      <select value={value} onChange={(event) => onChange(event.target.value as "easy" | "medium" | "hard")}>
        <option value="easy">easy</option>
        <option value="medium">medium</option>
        <option value="hard">hard</option>
      </select>
    </label>
  );
}

function AgentModeField({
  value,
  locale,
  onChange,
}: {
  value: ProblemAuthoringMode;
  locale: Locale;
  onChange: (value: ProblemAuthoringMode) => void;
}) {
  return (
    <label>{localeText(locale, { zh: "模式", en: "Mode" })}
      <select value={value} onChange={(event) => onChange(event.target.value as ProblemAuthoringMode)}>
        <option value="both">{authoringModeLabel("both", locale)}</option>
        <option value="function">{authoringModeLabel("function", locale)}</option>
        <option value="acm">{authoringModeLabel("acm", locale)}</option>
      </select>
    </label>
  );
}

function AgentLanguageField({
  languages,
  text,
  onToggle,
}: {
  languages: string[];
  text: AdminText;
  onToggle: (language: string) => void;
}) {
  return (
    <div className="agent-field language-checklist-label"><span>{text.targetLanguagesLabel}</span>
      <div className="language-checklist">
        {LANGUAGES.map((item) => (
          <label className="checkbox-label language-chip" key={item}>
            <input
              type="checkbox"
              checked={languages.includes(item)}
              onChange={() => onToggle(item)}
            />
            {languageLabel(item)}
          </label>
        ))}
      </div>
    </div>
  );
}

function AgentModelField({
  profiles,
  value,
  locale,
  onChange,
}: {
  profiles: AIProfile[];
  value: AIModelProfile;
  locale: Locale;
  onChange: (value: AIModelProfile) => void;
}) {
  return (
    <label>{localeText(locale, { zh: "模型", en: "Model" })}
      <select value={value} onChange={(event) => onChange(event.target.value as AIModelProfile)}>
        {(profiles.length ? profiles : [AI_PROFILE_FALLBACKS["deepseek-pro"], AI_PROFILE_FALLBACKS.default]).map((profile) => (
          <option key={profile.value} value={profile.value} disabled={!profile.available}>
            {aiProfileLabel(profile, locale)}{profile.available ? "" : ` (${localeText(locale, { zh: "不可用", en: "unavailable" })})`}
          </option>
        ))}
      </select>
    </label>
  );
}

export function DraftSourceSummary({ draft, locale, text }: { draft: ProblemDraft; locale: Locale; text: AdminText }) {
  const metadata = draftSourceMetadata(draft);
  const sourceUrl = sourceText(metadata.source_url);
  const rawMaterial = sourceText(metadata.raw_material);
  const rawLength = Number(metadata.raw_material_length ?? rawMaterial.length);
  const importNotes = sourceText(metadata.import_notes);
  return (
    <div className="draft-source-summary">
      <div className="draft-status-line">
        <span className="draft-status-chip imported">{text.importedDraft}</span>
        <span>{text.importSource}: {sourceUrl || localeText(locale, { zh: "未填写", en: "not provided" })}</span>
        <span>{text.rawMaterialLength}: {Number.isFinite(rawLength) ? rawLength : rawMaterial.length}</span>
      </div>
      {importNotes ? <p className="muted">{text.importNotesLabel}: {importNotes}</p> : null}
      {rawMaterial ? (
        <details>
          <summary>{text.rawMaterialPreview}</summary>
          <pre>{rawMaterial}</pre>
        </details>
      ) : null}
    </div>
  );
}

export function ProblemImportForm({
  locale,
  text,
  sourceUrl,
  rawMaterial,
  importNotes,
  difficulty,
  tags,
  mode,
  model,
  languages,
  profiles,
  canImport,
  onSourceUrlChange,
  onRawMaterialChange,
  onImportNotesChange,
  onDifficultyChange,
  onTagsChange,
  onModeChange,
  onModelChange,
  onToggleLanguage,
  onSubmit,
}: {
  locale: Locale;
  text: AdminText;
  sourceUrl: string;
  rawMaterial: string;
  importNotes: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string;
  mode: ProblemAuthoringMode;
  model: AIModelProfile;
  languages: string[];
  profiles: AIProfile[];
  canImport: boolean;
  onSourceUrlChange: (value: string) => void;
  onRawMaterialChange: (value: string) => void;
  onImportNotesChange: (value: string) => void;
  onDifficultyChange: (value: "easy" | "medium" | "hard") => void;
  onTagsChange: (value: string) => void;
  onModeChange: (value: ProblemAuthoringMode) => void;
  onModelChange: (value: AIModelProfile) => void;
  onToggleLanguage: (language: string) => void;
  onSubmit: () => void;
}) {
  return (
    <div className="agent-form import-agent-form">
      <label className="import-source-field">{text.sourceUrlLabel}<input value={sourceUrl} onChange={(event) => onSourceUrlChange(event.target.value)} /></label>
      <AgentDifficultyField value={difficulty} locale={locale} onChange={onDifficultyChange} />
      <label>
        {localeText(locale, { zh: "题目标签（Tag）", en: "Problem Tags" })}
        <input
          value={tags}
          placeholder={localeText(locale, { zh: "逗号分隔，如 Math, Data Stream, 最小二乘回归", en: "Comma separated, e.g. Math, Data Stream, Regression" })}
          onChange={(event) => onTagsChange(event.target.value)}
        />
      </label>
      <AgentModeField value={mode} locale={locale} onChange={onModeChange} />
      <AgentModelField profiles={profiles} value={model} locale={locale} onChange={onModelChange} />
      <AgentLanguageField languages={languages} text={text} onToggle={onToggleLanguage} />
      <label className="agent-raw-material-field">
        {text.rawMaterialLabel}
        <textarea
          value={rawMaterial}
          maxLength={30000}
          placeholder={text.rawMaterialPlaceholder}
          onChange={(event) => onRawMaterialChange(event.target.value)}
        />
      </label>
      <label className="agent-constraints-field">
        {text.importNotesLabel}
        <textarea
          value={importNotes}
          maxLength={2000}
          placeholder={text.importNotesPlaceholder}
          onChange={(event) => onImportNotesChange(event.target.value)}
        />
      </label>
      <button className="primary agent-generate-button" onClick={onSubmit} disabled={!canImport}>{text.importDraft}</button>
    </div>
  );
}

function AdminPage({ locale, currentUser, onBack }: { locale: Locale; currentUser: CurrentUser | null; onBack: () => void }) {
  const text = getAdminText(locale);
  const adminAccess = canAccessAdmin(currentUser);
  const [adminSection, setAdminSection] = useState<AdminSection>("agent");
  const [userSearch, setUserSearch] = useState("");
  const [userRoleFilter, setUserRoleFilter] = useState("");
  const [userStatusFilter, setUserStatusFilter] = useState("");
  const [userPage, setUserPage] = useState(1);
  const [problemSearch, setProblemSearch] = useState("");
  const [problemDifficultyFilter, setProblemDifficultyFilter] = useState("");
  const [problemVisibilityFilter, setProblemVisibilityFilter] = useState("");
  const [problemPage, setProblemPage] = useState(1);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);
  const [problemEdit, setProblemEdit] = useState<ProblemEditState>(() => problemEditFromProblem(null));
  const [problemSaveMessage, setProblemSaveMessage] = useState("");
  const [problemValidationReport, setProblemValidationReport] = useState<Record<string, any> | null>(null);
  const [problemSaving, setProblemSaving] = useState(false);
  const [problemSolutionGenerating, setProblemSolutionGenerating] = useState<string | null>(null);
  const [testcaseEdits, setTestcaseEdits] = useState<Record<string, AdminTestCase>>({});
  const [newTestcase, setNewTestcase] = useState({
    input: "",
    output: "",
    is_hidden: false,
    is_sample: false,
    score: "10",
    order: "",
  });
  const [agentTab, setAgentTab] = useState<AgentTab>("authoring");
  const [agentTopic, setAgentTopic] = useState("");
  const [agentTags, setAgentTags] = useState("");
  const [agentDifficulty, setAgentDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [agentMode, setAgentMode] = useState<ProblemAuthoringMode>("both");
  const [agentLanguages, setAgentLanguages] = useState<string[]>(["python", "cpp", "java"]);
  const [agentModel, setAgentModel] = useState<AIModelProfile>("deepseek-pro");
  const [agentConstraints, setAgentConstraints] = useState("");
  const [importSourceUrl, setImportSourceUrl] = useState("");
  const [importRawMaterial, setImportRawMaterial] = useState("");
  const [importNotes, setImportNotes] = useState("");
  const [agentMessage, setAgentMessage] = useState("");
  const [selectedAgentSessionId, setSelectedAgentSessionId] = useState<string | null>(null);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [localAgentDrafts, setLocalAgentDrafts] = useState<ProblemDraft[]>([]);
  const [selectedAgentRunId, setSelectedAgentRunId] = useState<string | null>(null);
  const [expandedAgentStepIds, setExpandedAgentStepIds] = useState<Set<string>>(() => new Set());
  const [agentFollowUpDraft, setAgentFollowUpDraft] = useState("");
  const [agentFollowUpLines, setAgentFollowUpLines] = useState<AgentFollowUpLine[]>([]);
  const [agentFollowUpBusy, setAgentFollowUpBusy] = useState<"chat" | "retry" | null>(null);
  const [agentLeftOpen, setAgentLeftOpen] = useState(true);
  const [agentRightOpen, setAgentRightOpen] = useState(true);
  const [agentLeftWidth, setAgentLeftWidth] = useState(DEFAULT_AGENT_LEFT_DRAWER_WIDTH);
  const [agentRightWidth, setAgentRightWidth] = useState(DEFAULT_AGENT_RIGHT_DRAWER_WIDTH);
  const [agentDrawerResizing, setAgentDrawerResizing] = useState<"left" | "right" | null>(null);
  const [draftSaving, setDraftSaving] = useState(false);
  const [draftSolutionGenerating, setDraftSolutionGenerating] = useState<string | null>(null);
  const [selectedDraft, setSelectedDraft] = useState<ProblemDraft | null>(null);
  const [draftEdit, setDraftEdit] = useState<DraftEditState | null>(null);
  const [draftSaveMessage, setDraftSaveMessage] = useState("");
  const initializedProblemEditIdRef = useRef<string | null>(null);
  const agentStreamAbortRef = useRef<AbortController | null>(null);
  const activeAgentStreamRunRef = useRef<string | null>(null);
  const overviewQuery = useQuery({
    queryKey: [
      "admin-overview",
      currentUser?.id,
      userSearch,
      userRoleFilter,
      userStatusFilter,
      userPage,
      problemSearch,
      problemDifficultyFilter,
      problemVisibilityFilter,
      problemPage,
    ],
    queryFn: () => api.adminOverview({
      userQuery: userSearch.trim() || undefined,
      userRole: userRoleFilter || undefined,
      userStatus: userStatusFilter || undefined,
      userPage,
      userPageSize: 8,
      problemQuery: problemSearch.trim() || undefined,
      problemDifficulty: problemDifficultyFilter || undefined,
      problemVisibility: problemVisibilityFilter || undefined,
      problemPage,
      problemPageSize: 8,
    }),
    enabled: adminAccess,
  });
  const draftsQuery = useQuery({
    queryKey: ["admin-problem-drafts", currentUser?.id],
    queryFn: () => api.adminProblemDrafts({ pageSize: 20 }),
    enabled: hasContentPermission(currentUser, CONTENT_PERMISSIONS.createOwnProblem),
  });
  const agentSessionsQuery = useQuery({
    queryKey: ["admin-agent-sessions", currentUser?.id],
    queryFn: () => api.adminAgentSessions({ pageSize: 20 }),
    enabled: hasContentPermission(currentUser, CONTENT_PERMISSIONS.createOwnProblem),
  });
  const selectedAgentSessionQuery = useQuery({
    queryKey: ["admin-agent-session", selectedAgentSessionId],
    queryFn: () => api.adminAgentSession(selectedAgentSessionId ?? ""),
    enabled: hasContentPermission(currentUser, CONTENT_PERMISSIONS.createOwnProblem) && Boolean(selectedAgentSessionId),
  });
  const agentRunsQuery = useQuery({
    queryKey: ["admin-agent-runs", currentUser?.id],
    queryFn: () => api.adminAgentRuns({ pageSize: 20 }),
    enabled: hasContentPermission(currentUser, CONTENT_PERMISSIONS.createOwnProblem),
  });
  const testcasesQuery = useQuery({
    queryKey: ["admin-problem-testcases", selectedProblemId],
    queryFn: () => api.adminProblemTestcases(selectedProblemId ?? ""),
    enabled: hasContentPermission(currentUser, CONTENT_PERMISSIONS.updateOwnProblem) && Boolean(selectedProblemId),
  });
  const problemSolutionsQuery = useQuery({
    queryKey: ["admin-problem-solutions", selectedProblemId],
    queryFn: () => api.adminProblemSolutions(selectedProblemId ?? ""),
    enabled: hasContentPermission(currentUser, CONTENT_PERMISSIONS.updateOwnProblem) && Boolean(selectedProblemId),
  });
  const adminAiProfilesQuery = useQuery({
    queryKey: ["ai-profiles", "admin", currentUser?.id],
    queryFn: () => api.aiProfiles(),
    enabled: adminAccess,
    staleTime: 60_000,
  });
  const adminAiProfiles = adminAiProfilesQuery.data ?? [];
  const agentPreferredProfile = preferredAdminAIProfile(adminAiProfiles);
  const selectedAgentProfile = adminAiProfiles.find((profile) => profile.value === agentModel);
  const agentModelAvailable = Boolean(selectedAgentProfile?.available);
  const agentModelUnavailableReason = adminAiProfilesQuery.isLoading
    ? localeText(locale, { zh: "正在检查 AI 模型...", en: "Checking AI profiles..." })
    : selectedAgentProfile && !selectedAgentProfile.available
      ? aiUnavailableText(locale, selectedAgentProfile.reason)
      : !agentPreferredProfile
        ? aiUnavailableText(locale)
        : null;
  const agentCanGenerate = Boolean(agentPreferredProfile && agentModelAvailable && agentTopic.trim());
  const importCanGenerate = Boolean(agentPreferredProfile && agentModelAvailable && importRawMaterial.trim().length >= 20);

  useEffect(() => {
    const next: Record<string, AdminTestCase> = {};
    for (const testcase of testcasesQuery.data ?? []) {
      next[testcase.id] = testcase;
    }
    setTestcaseEdits(next);
  }, [testcasesQuery.data]);

  useEffect(() => {
    if (!selectedProblemId) return;
    if (initializedProblemEditIdRef.current === selectedProblemId) return;
    const problem = (overviewQuery.data?.problems ?? []).find((item: any) => item.id === selectedProblemId);
    if (!problem || !problemSolutionsQuery.data) return;
    initializedProblemEditIdRef.current = selectedProblemId;
    setProblemEdit(problemEditFromProblem(problem, problemSolutionsQuery.data));
  }, [selectedProblemId, overviewQuery.data, problemSolutionsQuery.data]);

  useEffect(() => {
    if (!adminAiProfiles.length) return;
    if (!adminAiProfiles.some((profile) => profile.available && profile.value === agentModel)) {
      const next = preferredAdminAIProfile(adminAiProfiles);
      if (next) setAgentModel(next);
    }
  }, [adminAiProfiles, agentModel]);

  useEffect(() => () => stopAgentRunStream(), []);

  useEffect(() => {
    if (!selectedAgentSessionId) return;
    const session = selectedAgentSessionQuery.data
      ?? (agentSessionsQuery.data ?? []).find((item) => item.id === selectedAgentSessionId)
      ?? null;
    if (!session) return;
    const sessionRuns = agentSessionRuns(session);
    setAgentRuns(sessionRuns);
    if (!selectedAgentRunId || !sessionRuns.some((run) => run.id === selectedAgentRunId)) {
      setSelectedAgentRunId(latestAgentRunId(sessionRuns));
      setExpandedAgentStepIds(new Set());
    }
    const runningRun = sessionRuns.find((run) => run.status === "running");
    if (runningRun) connectAgentRunStream(runningRun.id);
    const sessionDrafts = agentSessionDrafts(session);
    const selectedDraftInSession = selectedDraft ? sessionDrafts.some((draft) => draft.id === selectedDraft.id) : false;
    const nextDraft = latestAgentDraft(session);
    const selectedDraftStale = Boolean(
      selectedDraft
      && nextDraft
      && selectedDraft.id === nextDraft.id
      && selectedDraft.updated_at !== nextDraft.updated_at,
    );
    if ((!selectedDraftInSession || selectedDraftStale) && nextDraft) {
      void previewAgentDraft(nextDraft);
    } else if (!sessionDrafts.length && selectedDraft) {
      setSelectedDraft(null);
      setDraftEdit(null);
      setDraftSaveMessage("");
    }
  }, [
    agentSessionsQuery.data,
    selectedAgentSessionId,
    selectedAgentSessionQuery.data,
    selectedAgentRunId,
    selectedDraft,
  ]);

  if (!adminAccess) {
    return (
      <main className="settings-page">
        <section className="settings-card">
          <button className="icon-button close-button tip" data-tip={text.back} onClick={onBack}><IconGlyph>x</IconGlyph></button>
          <p className="eyebrow">{text.title}</p>
          <h1>{text.title}</h1>
          <p className="muted">{text.noAccess}</p>
        </section>
      </main>
    );
  }

  async function updateUser(userId: string, payload: Record<string, unknown>) {
    await api.adminUpdateUser(userId, payload);
    await overviewQuery.refetch();
  }

  async function updateProblem(problemId: string, payload: Record<string, unknown>) {
    await api.adminUpdateProblem(problemId, payload);
    await overviewQuery.refetch();
  }

  async function deleteProblem(problemId: string) {
    const problem = problems.find((item: any) => item.id === problemId);
    const title = problem?.title ?? problemId;
    const confirmed = window.confirm(text.confirmDeleteProblem.replace("{title}", title));
    if (!confirmed) return;
    await api.adminDeleteProblem(problemId);
    if (selectedProblemId === problemId) {
      cancelProblemEdit();
    }
    if (problems.length <= 1 && problemPage > 1) {
      setProblemPage((page) => Math.max(1, page - 1));
    }
    await overviewQuery.refetch();
  }

  function toggleAgentLanguage(language: string) {
    setAgentLanguages((value) => {
      if (value.includes(language)) {
        return value.length > 1 ? value.filter((item) => item !== language) : value;
      }
      return [...value, language];
    });
  }

  function startAgentDrawerResize(side: "left" | "right", event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startX = event.clientX;
    const isLeft = side === "left";
    const open = isLeft ? agentLeftOpen : agentRightOpen;
    const startWidth = open
      ? (isLeft ? agentLeftWidth : agentRightWidth)
      : AGENT_DRAWER_RAIL_WIDTH;
    const minWidth = isLeft ? AGENT_LEFT_DRAWER_MIN : AGENT_RIGHT_DRAWER_MIN;
    const maxWidth = isLeft ? AGENT_LEFT_DRAWER_MAX : AGENT_RIGHT_DRAWER_MAX;
    const snapWidth = isLeft ? AGENT_LEFT_DRAWER_SNAP : AGENT_RIGHT_DRAWER_SNAP;
    const defaultWidth = isLeft ? DEFAULT_AGENT_LEFT_DRAWER_WIDTH : DEFAULT_AGENT_RIGHT_DRAWER_WIDTH;
    let latestWidth = startWidth;

    if (!open) {
      if (isLeft) {
        setAgentLeftOpen(true);
        setAgentLeftWidth(startWidth);
      } else {
        setAgentRightOpen(true);
        setAgentRightWidth(startWidth);
      }
    }

    setAgentDrawerResizing(side);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const onMove = (moveEvent: PointerEvent) => {
      const delta = isLeft ? moveEvent.clientX - startX : startX - moveEvent.clientX;
      const next = clamp(startWidth + delta, AGENT_DRAWER_RAIL_WIDTH, maxWidth);
      latestWidth = next;
      if (isLeft) setAgentLeftWidth(next);
      else setAgentRightWidth(next);
    };
    const onUp = () => {
      if (latestWidth <= snapWidth) {
        if (isLeft) {
          setAgentLeftOpen(false);
          setAgentLeftWidth(defaultWidth);
        } else {
          setAgentRightOpen(false);
          setAgentRightWidth(defaultWidth);
        }
      } else if (isLeft) {
        setAgentLeftWidth(clamp(latestWidth, minWidth, maxWidth));
      } else {
        setAgentRightWidth(clamp(latestWidth, minWidth, maxWidth));
      }
      setAgentDrawerResizing(null);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  function selectAgentSession(sessionId: string) {
    setSelectedAgentSessionId(sessionId);
    setSelectedAgentRunId(null);
    setExpandedAgentStepIds(new Set());
    setAgentFollowUpDraft("");
    setAgentFollowUpLines([]);
    setSelectedDraft(null);
    setDraftEdit(null);
    setDraftSaveMessage("");
  }

  function selectAgentRun(runId: string) {
    setSelectedAgentRunId(runId);
    setExpandedAgentStepIds(new Set());
    setAgentFollowUpDraft("");
  }

  function stopAgentRunStream() {
    if (agentStreamAbortRef.current) {
      agentStreamAbortRef.current.abort();
      agentStreamAbortRef.current = null;
    }
    activeAgentStreamRunRef.current = null;
  }

  function updateCachedAgentRun(run: AgentRun) {
    setAgentRuns((value) => upsertAgentRun(value, run));
    const sessionId = agentRunSessionId(run) ?? selectedAgentSessionId;
    if (sessionId) {
      queryClient.setQueryData<AgentSession | undefined>(["admin-agent-session", sessionId], (session) => (
        session ? {
          ...session,
          status: run.draft_id ? session.status : run.status,
          latest_run: run,
          runs: upsertAgentRun(session.runs, run),
          updated_at: run.finished_at ?? run.created_at ?? session.updated_at,
        } : session
      ));
      queryClient.setQueryData<AgentSession[] | undefined>(["admin-agent-sessions", currentUser?.id], (sessions) => (
        sessions?.map((session) => session.id === sessionId ? {
          ...session,
          status: run.draft_id ? session.status : run.status,
          latest_run: run,
          runs: upsertAgentRun(session.runs, run),
          updated_at: run.finished_at ?? run.created_at ?? session.updated_at,
        } : session)
      ));
    }
  }

  function updateCachedAgentStep(step: AgentStep) {
    setAgentRuns((value) => mergeAgentStepIntoRuns(value, step));
    const sessionId = selectedAgentSessionId;
    if (!sessionId) return;
    queryClient.setQueryData<AgentSession | undefined>(["admin-agent-session", sessionId], (session) => {
      if (!session) return session;
      const runs = mergeAgentStepIntoRuns(session.runs, step);
      const currentLatestRun = session.latest_run ?? null;
      const latestRun = currentLatestRun && currentLatestRun.id === step.run_id
        ? mergeAgentStepIntoRun(currentLatestRun, step)
        : currentLatestRun;
      return { ...session, runs, latest_run: latestRun ?? null };
    });
  }

  function handleAgentStreamEvent(streamEvent: AdminAgentStreamEvent) {
    if (streamEvent.event === "snapshot" || streamEvent.event === "run_status") {
      const run = streamEvent.data.run as AgentRun | undefined;
      if (run?.id) {
        updateCachedAgentRun(run);
        setSelectedAgentRunId((value) => value ?? run.id);
        if (streamEvent.event === "run_status") {
          void agentRunsQuery.refetch();
          void agentSessionsQuery.refetch();
          const sessionId = agentRunSessionId(run) ?? selectedAgentSessionId;
          if (sessionId) void selectedAgentSessionQuery.refetch();
          if (run.draft_id) {
            void api.adminProblemDraft(run.draft_id).then((draft) => {
              rememberAgentDraft(draft);
              setSelectedDraft(draft);
              setDraftEdit(draftEditFromDraft(draft));
            }).catch(() => undefined);
          }
        }
      }
      return;
    }
    if (streamEvent.event === "step") {
      const step = streamEvent.data.step as AgentStep | undefined;
      if (step?.id) updateCachedAgentStep(step);
      return;
    }
    if (streamEvent.event === "draft_ready") {
      const draftId = typeof streamEvent.data.draft_id === "string" ? streamEvent.data.draft_id : "";
      if (draftId) {
        void api.adminProblemDraft(draftId).then((draft) => {
          rememberAgentDraft(draft);
          setSelectedDraft(draft);
          setDraftEdit(draftEditFromDraft(draft));
          setDraftSaveMessage("");
        }).catch(() => undefined);
      }
    }
  }

  function connectAgentRunStream(runId: string | null | undefined) {
    if (!runId) return;
    if (activeAgentStreamRunRef.current === runId) return;
    stopAgentRunStream();
    const controller = new AbortController();
    agentStreamAbortRef.current = controller;
    activeAgentStreamRunRef.current = runId;
    void streamAdminAgentRun(runId, handleAgentStreamEvent, { signal: controller.signal }).catch((error) => {
      if (controller.signal.aborted) return;
      setAgentMessage(error instanceof Error ? error.message : localeText(locale, { zh: "执行路径实时连接已断开。", en: "Agent stream disconnected." }));
      void agentRunsQuery.refetch();
      void agentSessionsQuery.refetch();
    });
  }

  function toggleAgentStep(stepId: string) {
    setExpandedAgentStepIds((value) => {
      const next = new Set(value);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  }

  function rememberAgentDraft(draft: ProblemDraft | null | undefined) {
    if (!draft?.id) return;
    setLocalAgentDrafts((value) => mergeDrafts(value, draft));
  }

  async function previewAgentDraft(draft: ProblemDraft) {
    let nextDraft = draft;
    if (!draft.description && draft.id) {
      try {
        nextDraft = await api.adminProblemDraft(draft.id);
      } catch {
        nextDraft = draft;
      }
    }
    rememberAgentDraft(nextDraft);
    setSelectedDraft(nextDraft);
    setDraftEdit(draftEditFromDraft(nextDraft));
    setDraftSaveMessage("");
  }

  function applyDraftRuns(draft: ProblemDraft, fallbackRun?: AgentRun) {
    const runs = draft.runs?.length ? draft.runs : fallbackRun ? [fallbackRun] : [];
    rememberAgentDraft(draft);
    setAgentRuns(runs);
    setSelectedAgentRunId(fallbackRun?.id ?? latestAgentRunId(runs));
    setExpandedAgentStepIds(new Set());
  }

  async function handleAgentFailure(error: unknown, fallback: string) {
    const message = error instanceof Error ? error.message : fallback;
    setAgentMessage(message);
    const runId = error instanceof ApiError ? error.run_id : null;
    if (!runId) return;
    try {
      const run = await api.adminAgentRun(runId);
      setAgentRuns([run]);
      setSelectedAgentRunId(run.id);
      setExpandedAgentStepIds(new Set());
      const sessionId = agentRunSessionId(run);
      if (sessionId) {
        setSelectedAgentSessionId(sessionId);
        try {
          const session = await api.adminAgentSession(sessionId);
          queryClient.setQueryData(["admin-agent-session", sessionId], session);
        } catch {
          // Keep the fetched run visible even if the grouped session is not available yet.
        }
      }
      await agentRunsQuery.refetch();
      await agentSessionsQuery.refetch();
    } catch {
      await agentRunsQuery.refetch();
      await agentSessionsQuery.refetch();
    }
  }

  async function applyAgentActionResponse(response: AdminAgentActionResponse): Promise<AgentRun | null> {
    const sessionId = response.session_id ?? null;
    let responseSession: AgentSession | null = null;
    if (sessionId) {
      setSelectedAgentSessionId(sessionId);
      try {
        responseSession = await api.adminAgentSession(sessionId);
        queryClient.setQueryData(["admin-agent-session", sessionId], responseSession);
      } catch {
        responseSession = null;
      }
    }
    const responseRun = response.run ?? null;
    const runId = response.run_id ?? responseRun?.id ?? null;
    let run = responseRun;
    if (!run && runId) {
      run = await api.adminAgentRun(runId);
    }
    if (run) {
      updateCachedAgentRun(run);
      setAgentRuns([run]);
      setSelectedAgentRunId(run.id);
      setExpandedAgentStepIds(new Set());
      if (run.status === "running") connectAgentRunStream(run.id);
    }
    const responseDraft = response.draft ?? null;
    const draftId = response.draft_id ?? responseDraft?.id ?? run?.draft_id ?? null;
    if (responseDraft) {
      setSelectedDraft(responseDraft);
      setDraftEdit(draftEditFromDraft(responseDraft));
      applyDraftRuns(responseDraft, run ?? undefined);
      setDraftSaveMessage("");
    } else if (draftId) {
      try {
        const draft = await api.adminProblemDraft(draftId);
        setSelectedDraft(draft);
        setDraftEdit(draftEditFromDraft(draft));
        applyDraftRuns(draft, run ?? undefined);
        setDraftSaveMessage("");
      } catch {
        // The run is still useful even if its draft was not created or is unavailable.
      }
    }
    if (responseSession) {
      const sessionRuns = agentSessionRuns(responseSession);
      const sessionDraft = latestAgentDraft(responseSession);
      setAgentRuns(sessionRuns);
      setSelectedAgentRunId(run?.id ?? latestAgentRunId(sessionRuns));
      setExpandedAgentStepIds(new Set());
      const streamRun = run ?? sessionRuns.find((item) => item.status === "running") ?? null;
      if (streamRun?.status === "running") connectAgentRunStream(streamRun.id);
      if (sessionDraft) {
        await previewAgentDraft(sessionDraft);
      }
    }
    await draftsQuery.refetch();
    await agentRunsQuery.refetch();
    await agentSessionsQuery.refetch();
    return run;
  }

  async function sendAgentFollowUp() {
    const selectedRun = visibleAgentRuns.find((run) => run.id === selectedAgentRunId) ?? null;
    if (!selectedRun) return;
    const message = agentFollowUpDraft.trim();
    if (!message) {
      setAgentMessage(text.followUpRequired);
      return;
    }
    setAgentFollowUpBusy("chat");
    setAgentMessage("");
    const lineId = `${Date.now()}`;
    setAgentFollowUpLines((value) => [...value, { id: `${lineId}.user`, role: "user", message, runId: selectedRun.id }]);
    try {
      const result = await api.adminAgentFollowUp(selectedRun.id, {
        message,
        locale,
        model_profile: agentModel,
        draft_id: selectedDraft?.id ?? selectedRun.draft_id ?? null,
      });
      const run = await applyAgentActionResponse(result);
      setAgentFollowUpLines((value) => [...value, {
        id: `${lineId}.assistant`,
        role: "assistant",
        message: result.message ?? text.followUpSent,
        runId: run?.id ?? result.run_id ?? null,
      }]);
      setAgentFollowUpDraft("");
      setAgentMessage(result.message ?? text.followUpSent);
    } catch (error) {
      await handleAgentFailure(error, localeText(locale, { zh: "追问失败。", en: "Follow-up failed." }));
    } finally {
      setAgentFollowUpBusy(null);
    }
  }

  async function retrySelectedAgentRun() {
    const selectedRun = visibleAgentRuns.find((run) => run.id === selectedAgentRunId) ?? null;
    if (!selectedRun) return;
    const retryMessage = agentFollowUpDraft.trim();
    setAgentFollowUpBusy("retry");
    setAgentMessage("");
    const lineId = `${Date.now()}`;
    if (retryMessage) {
      setAgentFollowUpLines((value) => [...value, { id: `${lineId}.retry-user`, role: "user", message: retryMessage, runId: selectedRun.id }]);
    }
    try {
      const result = await api.adminRetryAgentRun(selectedRun.id, {
        locale,
        model_profile: agentModel,
        draft_id: selectedDraft?.id ?? selectedRun.draft_id ?? null,
        message: retryMessage || null,
      });
      const run = await applyAgentActionResponse(result);
      setAgentFollowUpLines((value) => [...value, {
        id: `${lineId}.retry`,
        role: "assistant",
        message: result.message ?? text.retryStarted,
        runId: run?.id ?? result.run_id ?? null,
      }]);
      setAgentFollowUpDraft("");
      setAgentMessage(result.message ?? text.retryStarted);
    } catch (error) {
      await handleAgentFailure(error, localeText(locale, { zh: "重试失败。", en: "Retry failed." }));
    } finally {
      setAgentFollowUpBusy(null);
    }
  }

  async function createAgentDraft() {
    if (!agentTopic.trim()) {
      setAgentMessage(localeText(locale, { zh: "请先填写主题。", en: "Enter a topic first." }));
      return;
    }
    if (!agentCanGenerate) {
      setAgentMessage(agentModelUnavailableReason ?? aiUnavailableText(locale));
      return;
    }
    setAgentMessage(localeText(locale, { zh: "正在生成并验证草稿...", en: "Generating and validating draft..." }));
    try {
      const result = await api.adminCreateProblemDraft({
        topic: agentTopic,
        difficulty: agentDifficulty,
        tags: agentTags.split(",").map((tag) => tag.trim()).filter(Boolean),
        mode: agentMode,
        target_language: agentLanguages[0] ?? "python",
        target_languages: agentLanguages,
        locale,
        model_profile: agentModel,
        constraints: agentConstraints.trim() || null,
      });
      await applyAgentActionResponse(result);
      setAgentMessage(result.status
        ? validationStatusMessage(result.status, result.validation_summary, locale)
        : result.message ?? localeText(locale, { zh: "草稿已创建。", en: "Draft created." }));
    } catch (error) {
      await handleAgentFailure(error, localeText(locale, { zh: "生成失败。", en: "Generation failed." }));
    }
  }

  async function createImportDraft() {
    if (importRawMaterial.trim().length < 20) {
      setAgentMessage(text.rawMaterialRequired);
      return;
    }
    if (!importCanGenerate) {
      setAgentMessage(agentModelUnavailableReason ?? aiUnavailableText(locale));
      return;
    }
    setAgentMessage(localeText(locale, { zh: "正在导入、改写并验证草稿...", en: "Importing, rewriting, and validating draft..." }));
    try {
      const result = await api.adminCreateProblemImport({
        raw_material: importRawMaterial.trim(),
        source_url: importSourceUrl.trim() || null,
        difficulty: agentDifficulty,
        tags: agentTags.split(",").map((tag) => tag.trim()).filter(Boolean),
        mode: agentMode,
        target_language: agentLanguages[0] ?? "python",
        target_languages: agentLanguages,
        locale,
        model_profile: agentModel,
        import_notes: importNotes.trim() || null,
      });
      await applyAgentActionResponse(result);
      setAgentMessage(result.status
        ? validationStatusMessage(result.status, result.validation_summary, locale)
        : result.message ?? localeText(locale, { zh: "草稿已导入。", en: "Draft imported." }));
    } catch (error) {
      await handleAgentFailure(error, localeText(locale, { zh: "导入失败。", en: "Import failed." }));
    }
  }

  async function loadDraft(draftId: string) {
    const draft = await api.adminProblemDraft(draftId);
    setSelectedDraft(draft);
    setDraftEdit(draftEditFromDraft(draft));
    applyDraftRuns(draft);
    setDraftSaveMessage("");
  }

  async function approveSelectedDraft() {
    if (!selectedDraft) return;
    if (isDraftEditDirty(selectedDraft, draftEdit)) {
      setDraftSaveMessage(localeText(locale, { zh: "请先保存并重新校验当前更改，再批准发布。", en: "Save and revalidate the current edits before approving." }));
      return;
    }
    if (!window.confirm(text.confirmApproveDraft)) return;
    try {
      const draft = await api.adminApproveProblemDraft(selectedDraft.id);
      setSelectedDraft(draft);
      setDraftEdit(draftEditFromDraft(draft));
      applyDraftRuns(draft);
      setDraftSaveMessage("");
      await overviewQuery.refetch();
      await draftsQuery.refetch();
      await agentRunsQuery.refetch();
      await agentSessionsQuery.refetch();
    } catch (error) {
      setDraftSaveMessage(error instanceof Error ? error.message : localeText(locale, { zh: "发布失败。", en: "Approval failed." }));
    }
  }

  async function rejectSelectedDraft() {
    if (!selectedDraft) return;
    if (!window.confirm(text.confirmRejectDraft)) return;
    try {
      const draft = await api.adminRejectProblemDraft(selectedDraft.id);
      setSelectedDraft(draft);
      setDraftEdit(draftEditFromDraft(draft));
      applyDraftRuns(draft);
      setDraftSaveMessage("");
      await draftsQuery.refetch();
      await agentRunsQuery.refetch();
      await agentSessionsQuery.refetch();
    } catch (error) {
      setDraftSaveMessage(error instanceof Error ? error.message : localeText(locale, { zh: "拒绝失败。", en: "Rejection failed." }));
    }
  }

  function updateDraftEdit(patch: Partial<DraftEditState>) {
    if (draftSaving) return;
    setDraftEdit((value) => value ? { ...value, ...patch } : value);
  }

  function updateDraftCase(index: number, patch: Partial<DraftEditCase>) {
    if (draftSaving) return;
    setDraftEdit((value) => {
      if (!value) return value;
      return {
        ...value,
        testcases: value.testcases.map((testcase, itemIndex) => (
          itemIndex === index ? { ...testcase, ...patch } : testcase
        )),
      };
    });
  }

  function updateDraftSolution(index: number, patch: Partial<DraftOfficialSolution>) {
    if (draftSaving) return;
    setDraftEdit((value) => {
      if (!value) return value;
      const current = value.official_solutions[index];
      if (!current) return value;
      let targetLanguages = value.target_languages;
      const nextLanguage = patch.language;
      if (nextLanguage && nextLanguage !== current.language) {
        if (value.official_solutions.some((solution, itemIndex) => itemIndex !== index && solution.language === nextLanguage)) {
          return value;
        }
        targetLanguages = value.target_languages.map((language) => language === current.language ? nextLanguage : language);
      }
      return {
        ...value,
        target_languages: normalizeLanguageList(targetLanguages),
        official_solutions: value.official_solutions.map((solution, itemIndex) => (
          itemIndex === index ? { ...solution, ...patch } : solution
        )),
      };
    });
  }

  function toggleDraftTargetLanguage(language: string) {
    if (draftSaving) return;
    setDraftEdit((value) => {
      if (!value) return value;
      const exists = value.target_languages.includes(language);
      const target_languages = exists
        ? value.target_languages.filter((item) => item !== language)
        : [...value.target_languages, language];
      const official_solutions = exists || value.official_solutions.some((solution) => solution.language === language)
        ? value.official_solutions
        : [...value.official_solutions, { language, code: "", explanation: "" }];
      return { ...value, target_languages, official_solutions };
    });
  }

  function addDraftSolution(language: string) {
    if (draftSaving) return;
    setDraftEdit((value) => {
      if (!value || value.official_solutions.some((solution) => solution.language === language)) return value;
      return {
        ...value,
        target_languages: normalizeLanguageList([...value.target_languages, language]),
        official_solutions: [
          ...value.official_solutions,
          { language, code: "", explanation: "" },
        ],
      };
    });
  }

  function removeDraftSolution(index: number) {
    if (draftSaving) return;
    setDraftEdit((value) => {
      if (!value || value.official_solutions.length <= 1) return value;
      const removedLanguage = value.official_solutions[index]?.language;
      return {
        ...value,
        target_languages: removedLanguage
          ? value.target_languages.filter((language) => language !== removedLanguage)
          : value.target_languages,
        official_solutions: value.official_solutions.filter((_, itemIndex) => itemIndex !== index),
      };
    });
  }

  function addDraftCase(hidden: boolean) {
    if (draftSaving) return;
    setDraftEdit((value) => {
      if (!value) return value;
      const order = value.testcases.length + 1;
      return {
        ...value,
        testcases: [
          ...value.testcases,
          { input: "", output: "", explanation: "", is_hidden: hidden, is_sample: !hidden, order },
        ],
      };
    });
  }

  function removeDraftCase(index: number) {
    if (draftSaving) return;
    setDraftEdit((value) => {
      if (!value) return value;
      return {
        ...value,
        testcases: value.testcases.filter((_, itemIndex) => itemIndex !== index).map((testcase, itemIndex) => ({
          ...testcase,
          order: itemIndex + 1,
        })),
      };
    });
  }

  async function saveSelectedDraftEdit() {
    if (!selectedDraft || !draftEdit) return;
    const validationError = draftEditValidationError(draftEdit, locale);
    if (validationError) {
      setDraftSaveMessage(validationError);
      return;
    }
    setDraftSaving(true);
    try {
      const draft = await api.adminUpdateProblemDraft(selectedDraft.id, draftEditPayload(draftEdit));
      setSelectedDraft(draft);
      setDraftEdit(draftEditFromDraft(draft));
      applyDraftRuns(draft);
      setDraftSaveMessage(validationStatusMessage(draft.status, draft.validation_report ?? draft.validation_summary, locale));
      setAgentMessage(validationStatusMessage(draft.status, draft.validation_report ?? draft.validation_summary, locale));
      await draftsQuery.refetch();
      await agentRunsQuery.refetch();
      await agentSessionsQuery.refetch();
    } catch (error) {
      setDraftSaveMessage(draftSaveErrorMessage(error, locale));
    } finally {
      setDraftSaving(false);
    }
  }

  async function generateDraftSolution(index: number) {
    if (!selectedDraft || !draftEdit) return;
    const solution = draftEdit.official_solutions[index];
    if (!solution) return;
    const language = solution.language.trim().toLowerCase();
    if (!language) return;
    if (!agentModelAvailable) {
      setDraftSaveMessage(agentModelUnavailableReason ?? aiUnavailableText(locale));
      return;
    }
    setDraftSolutionGenerating(language);
    setDraftSaveMessage(localeText(locale, { zh: `正在生成 ${languageLabel(language)} 官方解法...`, en: `Generating ${languageLabel(language)} official solution...` }));
    try {
      const generated = await api.adminGenerateProblemDraftSolution(selectedDraft.id, {
        language,
        locale,
        model_profile: agentModel,
        draft: draftEditPayload(draftEdit),
      });
      setDraftEdit((value) => {
        if (!value) return value;
        return {
          ...value,
          target_languages: normalizeLanguageList([...value.target_languages, generated.language]),
          official_solutions: value.official_solutions.map((item, itemIndex) => (
            itemIndex === index
              ? { language: generated.language, code: generated.code, explanation: generated.explanation }
              : item
          )),
        };
      });
      const refreshed = await api.adminProblemDraft(selectedDraft.id);
      setSelectedDraft(refreshed);
      applyDraftRuns(refreshed);
      setDraftSaveMessage(text.aiFillSolutionDone);
      await agentRunsQuery.refetch();
      await agentSessionsQuery.refetch();
    } catch (error) {
      setDraftSaveMessage(error instanceof Error ? error.message : localeText(locale, { zh: "AI 填充失败。", en: "AI fill failed." }));
      await handleAgentFailure(error, localeText(locale, { zh: "AI 填充失败。", en: "AI fill failed." }));
    } finally {
      setDraftSolutionGenerating(null);
    }
  }

  const users = overviewQuery.data?.users ?? [];
  const problems = overviewQuery.data?.problems ?? [];
  const userPagination = overviewQuery.data?.pagination?.users ?? { page: userPage, page_size: 8, total: 0, total_pages: 0 };
  const problemPagination = overviewQuery.data?.pagination?.problems ?? { page: problemPage, page_size: 8, total: 0, total_pages: 0 };
  const queriedAgentSessions = agentSessionsQuery.data ?? [];
  const selectedAgentSessionFromList = queriedAgentSessions.find((session) => session.id === selectedAgentSessionId) ?? null;
  const selectedAgentSession = selectedAgentSessionQuery.data ?? selectedAgentSessionFromList;
  const visibleAgentSessions = mergeAgentSessions(queriedAgentSessions, selectedAgentSession);
  const visibleAgentRuns = selectedAgentSession ? agentSessionRuns(selectedAgentSession) : agentRuns;
  const selectedAgentRun = visibleAgentRuns.find((run) => run.id === selectedAgentRunId) ?? null;
  const agentRunsEmptyMessage = visibleAgentSessions.length
    ? localeText(locale, { zh: "请选择左侧的出题会话。", en: "Select an authoring session on the left." })
    : localeText(locale, {
        zh: "还没有出题会话。生成或导入草稿后会在这里出现。",
        en: "No authoring sessions yet. Generate or import a draft to start one.",
      });
  const draftHasUnsavedChanges = isDraftEditDirty(selectedDraft, draftEdit);
  const draftEditLocked = draftSaving || Boolean(draftSolutionGenerating) || (selectedDraft ? draftIsReadOnly(selectedDraft.status) : false);
  const selectedUser = users.find((user: any) => user.id === selectedUserId) ?? null;
  const selectedProblem = problems.find((problem: any) => problem.id === selectedProblemId) ?? null;
  const problemEditLocked = problemSaving || Boolean(problemSolutionGenerating);
  const agentWorkspaceStyle = {
    "--agent-left-panel": agentLeftOpen ? `${agentLeftWidth}px` : `${AGENT_DRAWER_RAIL_WIDTH}px`,
    "--agent-right-panel": agentRightOpen ? `${agentRightWidth}px` : `${AGENT_DRAWER_RAIL_WIDTH}px`,
  } as React.CSSProperties;

  function pageSummary(pagination: any) {
    const totalPages = Math.max(Number(pagination.total_pages ?? 0), 1);
    return text.pageSummary
      .replace("{page}", String(pagination.page ?? 1))
      .replace("{totalPages}", String(totalPages))
      .replace("{total}", String(pagination.total ?? 0));
  }

  function chooseProblem(problem: any) {
    initializedProblemEditIdRef.current = null;
    setSelectedProblemId(problem.id);
    setProblemEdit(problemEditFromProblem(problem));
    setProblemSaveMessage("");
    setProblemValidationReport(null);
  }

  function cancelProblemEdit() {
    initializedProblemEditIdRef.current = null;
    setSelectedProblemId(null);
    setProblemEdit(problemEditFromProblem(null));
    setProblemSaveMessage("");
    setProblemValidationReport(null);
    setTestcaseEdits({});
    setNewTestcase({ input: "", output: "", is_hidden: false, is_sample: false, score: "10", order: "" });
  }

  function updateTestcaseEdit(testcaseId: string, patch: Partial<AdminTestCase>) {
    setTestcaseEdits((value) => ({
      ...value,
      [testcaseId]: {
        ...value[testcaseId],
        ...patch,
        ...(patch.is_hidden ? { is_sample: false } : {}),
        ...(patch.is_sample ? { is_hidden: false } : {}),
      },
    }));
  }

  async function refreshProblemTestcases() {
    await testcasesQuery.refetch();
    await overviewQuery.refetch();
  }

  function updateProblemSolution(index: number, patch: Partial<ProblemSolutionEdit>) {
    if (problemEditLocked) return;
    setProblemEdit((value) => ({
      ...value,
      solutions: value.solutions.map((solution, itemIndex) => (
        itemIndex === index ? { ...solution, ...patch } : solution
      )),
    }));
  }

  function addProblemSolution(language: string) {
    if (problemEditLocked) return;
    setProblemEdit((value) => {
      if (value.solutions.some((solution) => solution.language === language)) return value;
      return {
        ...value,
        solutions: [...value.solutions, { language, code: "", explanation: "", time_complexity: "", space_complexity: "" }],
      };
    });
  }

  function removeProblemSolution(index: number) {
    if (problemEditLocked) return;
    setProblemEdit((value) => ({
      ...value,
      solutions: value.solutions.filter((_, itemIndex) => itemIndex !== index),
    }));
  }

  async function generateProblemSolution(index: number) {
    if (!selectedProblemId) return;
    const solution = problemEdit.solutions[index];
    if (!solution) return;
    const language = solution.language.trim().toLowerCase();
    if (!language) return;
    if (!agentModelAvailable) {
      setProblemSaveMessage(agentModelUnavailableReason ?? aiUnavailableText(locale));
      return;
    }
    setProblemSolutionGenerating(language);
    setProblemSaveMessage(localeText(locale, { zh: `正在生成 ${languageLabel(language)} 官方解法...`, en: `Generating ${languageLabel(language)} official solution...` }));
    try {
      const generated = await api.adminGenerateProblemSolution(selectedProblemId, {
        language,
        locale,
        model_profile: agentModel,
        problem: problemEditPayload(problemEdit),
        solutions: problemSolutionPayloads(problemEdit),
      });
      setProblemEdit((value) => ({
        ...value,
        solutions: value.solutions.map((item, itemIndex) => (
          itemIndex === index
            ? { ...item, language: generated.language, code: generated.code, explanation: generated.explanation }
            : item
        )),
      }));
      setProblemSaveMessage(text.aiFillSolutionDone);
    } catch (error) {
      setProblemSaveMessage(error instanceof Error ? error.message : localeText(locale, { zh: "AI 填充失败。", en: "AI fill failed." }));
    } finally {
      setProblemSolutionGenerating(null);
    }
  }

  async function saveProblemEdit(revalidate = false) {
    if (!selectedProblemId) return;
    const validationError = problemEditValidationError(problemEdit, locale);
    if (validationError) {
      setProblemSaveMessage(validationError);
      return;
    }
    setProblemSaving(true);
    try {
      await updateProblem(selectedProblemId, problemEditPayload(problemEdit));
      const existingLanguages = new Set((problemSolutionsQuery.data ?? []).map((solution) => solution.language));
      const nextLanguages = new Set(problemEdit.solutions.map((solution) => solution.language));
      for (const solution of problemEdit.solutions) {
        await api.adminUpsertSolution(selectedProblemId, {
          language: solution.language,
          code: solution.code,
          explanation: solution.explanation,
          time_complexity: solution.time_complexity.trim() || null,
          space_complexity: solution.space_complexity.trim() || null,
        });
      }
      for (const language of existingLanguages) {
        if (!nextLanguages.has(language)) {
          await api.adminDeleteSolution(selectedProblemId, language);
        }
      }
      const report = revalidate ? await api.adminRevalidateProblem(selectedProblemId) : null;
      if (report) setProblemValidationReport(report);
      setProblemSaveMessage(revalidate
        ? validationStatusMessage(report?.passed ? "validated" : "validation_failed", report, locale)
        : localeText(locale, { zh: "题目已保存，建议重新校验。", en: "Problem saved. Revalidation is recommended." }));
      await problemSolutionsQuery.refetch();
      await overviewQuery.refetch();
    } catch (error) {
      setProblemSaveMessage(error instanceof Error ? error.message : localeText(locale, { zh: "题目保存失败。", en: "Problem save failed." }));
    } finally {
      setProblemSaving(false);
    }
  }

  async function createProblemTestcase() {
    if (!selectedProblemId) return;
    await api.adminCreateTestcase(selectedProblemId, {
      input: newTestcase.input,
      output: newTestcase.output,
      is_hidden: newTestcase.is_hidden,
      is_sample: newTestcase.is_sample,
      score: Number(newTestcase.score) || 0,
      order: newTestcase.order.trim() ? Number(newTestcase.order) : null,
    });
    setNewTestcase({ input: "", output: "", is_hidden: false, is_sample: false, score: "10", order: "" });
    setProblemSaveMessage(localeText(locale, { zh: "用例已新增，建议重新校验。", en: "Testcase added. Revalidation is recommended." }));
    await refreshProblemTestcases();
  }

  async function saveProblemTestcase(testcaseId: string) {
    const testcase = testcaseEdits[testcaseId];
    if (!testcase) return;
    await api.adminUpdateTestcase(testcaseId, {
      input: testcase.input,
      output: testcase.output,
      is_hidden: testcase.is_hidden,
      is_sample: testcase.is_sample,
      score: Number(testcase.score) || 0,
      order: Number(testcase.order) || 0,
    });
    setProblemSaveMessage(localeText(locale, { zh: "用例已保存，建议重新校验。", en: "Testcase saved. Revalidation is recommended." }));
    await refreshProblemTestcases();
  }

  async function deleteProblemTestcase(testcaseId: string) {
    await api.adminDeleteTestcase(testcaseId);
    setProblemSaveMessage(localeText(locale, { zh: "用例已删除，建议重新校验。", en: "Testcase deleted. Revalidation is recommended." }));
    await refreshProblemTestcases();
  }

  return (
    <main className="admin-page">
      <section className="admin-shell">
        <button className="icon-button close-button tip" data-tip={text.back} onClick={onBack}><IconGlyph>x</IconGlyph></button>
        <p className="eyebrow">{text.title}</p>
        <h1>{text.title}</h1>
        <p className="muted">{text.copy}</p>
        <nav className="admin-section-tabs segmented" aria-label={text.title}>
          <button type="button" className={adminSection === "agent" ? "active" : ""} aria-pressed={adminSection === "agent"} onClick={() => setAdminSection("agent")}>{text.adminAgentSection}</button>
          <button type="button" className={adminSection === "users" ? "active" : ""} aria-pressed={adminSection === "users"} onClick={() => setAdminSection("users")}>{text.adminUsersSection}</button>
          <button type="button" className={adminSection === "problems" ? "active" : ""} aria-pressed={adminSection === "problems"} onClick={() => setAdminSection("problems")}>{text.adminProblemsSection}</button>
        </nav>
        {adminSection === "agent" ? <section className="admin-panel problem-agent-panel">
          <div>
            <h2>{text.problemAgent}</h2>
            <p className="muted">{text.agentNotice}</p>
          </div>
          <div className="agent-tabs segmented" role="tablist" aria-label={text.problemAgent}>
            <button type="button" className={agentTab === "authoring" ? "active" : ""} aria-selected={agentTab === "authoring"} onClick={() => setAgentTab("authoring")}>{text.authoringTab}</button>
            <button type="button" className={agentTab === "import" ? "active" : ""} aria-selected={agentTab === "import"} onClick={() => setAgentTab("import")}>{text.importTab}</button>
          </div>
          {agentTab === "authoring" ? (
            <div className="agent-form">
              <label>{localeText(locale, { zh: "主题", en: "Topic" })}<input value={agentTopic} onChange={(event) => setAgentTopic(event.target.value)} /></label>
              <AgentDifficultyField value={agentDifficulty} locale={locale} onChange={setAgentDifficulty} />
              <label>
                {localeText(locale, { zh: "题目标签（Tag）", en: "Problem Tags" })}
                <input
                  value={agentTags}
                  placeholder={localeText(locale, { zh: "逗号分隔，如 Graph, DP, 在线学习", en: "Comma separated, e.g. Graph, DP, Online Learning" })}
                  onChange={(event) => setAgentTags(event.target.value)}
                />
              </label>
              <AgentModeField value={agentMode} locale={locale} onChange={setAgentMode} />
              <AgentLanguageField languages={agentLanguages} text={text} onToggle={toggleAgentLanguage} />
              <AgentModelField profiles={adminAiProfiles} value={agentModel} locale={locale} onChange={setAgentModel} />
              <label className="agent-constraints-field">
                {localeText(locale, { zh: "额外约束", en: "Constraints" })}
                <textarea
                  value={agentConstraints}
                  maxLength={2000}
                  placeholder={localeText(locale, {
                    zh: "补充题目要求，例如：业务背景、输入规模、必须覆盖的边界、期望考察的算法、不要出现的套路或样例风格。",
                    en: "Add requirements such as story context, input scale, required boundaries, target algorithm, patterns to avoid, or sample style.",
                  })}
                  onChange={(event) => setAgentConstraints(event.target.value)}
                />
              </label>
              <button className="primary agent-generate-button" onClick={createAgentDraft} disabled={!agentCanGenerate}>{text.generateDraft}</button>
            </div>
          ) : (
            <ProblemImportForm
              locale={locale}
              text={text}
              sourceUrl={importSourceUrl}
              rawMaterial={importRawMaterial}
              importNotes={importNotes}
              difficulty={agentDifficulty}
              tags={agentTags}
              mode={agentMode}
              model={agentModel}
              languages={agentLanguages}
              profiles={adminAiProfiles}
              canImport={importCanGenerate}
              onSourceUrlChange={setImportSourceUrl}
              onRawMaterialChange={setImportRawMaterial}
              onImportNotesChange={setImportNotes}
              onDifficultyChange={setAgentDifficulty}
              onTagsChange={setAgentTags}
              onModeChange={setAgentMode}
              onModelChange={setAgentModel}
              onToggleLanguage={toggleAgentLanguage}
              onSubmit={createImportDraft}
            />
          )}
          {agentTab === "authoring" && !agentTopic.trim() ? <p className="muted model-unavailable-note">{localeText(locale, { zh: "填写主题后才能生成草稿。", en: "Enter a topic to generate a draft." })}</p> : null}
          {agentTab === "import" && importRawMaterial.trim().length < 20 ? <p className="muted model-unavailable-note">{text.rawMaterialRequired}</p> : null}
          {agentModelUnavailableReason ? <p className="muted model-unavailable-note">{agentModelUnavailableReason}</p> : null}
          {agentMessage ? <p className="muted">{agentMessage}</p> : null}
          <div
            className={`agent-workspace ${agentLeftOpen ? "" : "agent-left-collapsed"} ${agentRightOpen ? "" : "agent-right-collapsed"} ${agentDrawerResizing ? "agent-is-resizing" : ""}`}
            style={agentWorkspaceStyle}
          >
            <aside className="agent-drawer agent-left-drawer">
              <div className="agent-drawer-content">
                <div className="agent-drafts">
                  <div className="agent-list-title">
                    <strong>{localeText(locale, { zh: "出题会话", en: "Sessions" })}</strong>
                    <span className="muted">{visibleAgentSessions.length}</span>
                  </div>
                  {visibleAgentSessions.map((session) => {
                    const sessionDraft = latestAgentDraft(session);
                    const sourceLabel = agentSessionSourceLabel(session, locale);
                    return (
                      <button
                        key={session.id}
                        className={`agent-session-row ${agentStatusClass(session.status)} ${selectedAgentSessionId === session.id ? "active" : ""}`}
                        onClick={() => selectAgentSession(session.id)}
                      >
                        <strong>{session.title || sessionDraft?.title || localeText(locale, { zh: "未命名会话", en: "Untitled session" })}</strong>
                          <span className="draft-status-line">
                            <span className={`agent-status-chip ${agentStatusClass(session.status)}`}>{agentRunStatusLabel(session.status, locale)}</span>
                            {sourceLabel ? <span className="draft-status-chip imported">{sourceLabel}</span> : null}
                            {session.mode ? <span>{authoringModeLabel(session.mode, locale)}</span> : null}
                            <span>{session.run_count} {localeText(locale, { zh: "运行", en: "runs" })}</span>
                            <span>{session.draft_count} {localeText(locale, { zh: "草稿", en: "drafts" })}</span>
                          </span>
                          {sessionDraft ? <span className="agent-run-meta">{sessionDraft.title} · {shortDateTime(session.updated_at)}</span> : null}
                      </button>
                    );
                  })}
                  {!visibleAgentSessions.length && !agentSessionsQuery.isLoading ? <p className="muted">{localeText(locale, { zh: "还没有出题会话。", en: "No sessions yet." })}</p> : null}
                </div>
              </div>
              <span className="agent-drawer-rail" aria-hidden={agentLeftOpen}>
                <span>{localeText(locale, { zh: "会", en: "S" })}</span>
                <span>{localeText(locale, { zh: "话", en: "N" })}</span>
              </span>
            </aside>
            <div className="agent-drawer-edge agent-left-edge">
              <button
                type="button"
                className="agent-drawer-toggle"
                aria-label={agentLeftOpen
                  ? localeText(locale, { zh: "收起出题会话", en: "Collapse sessions" })
                  : localeText(locale, { zh: "展开出题会话", en: "Expand sessions" })}
                aria-expanded={agentLeftOpen}
                title={agentLeftOpen
                  ? localeText(locale, { zh: "收起出题会话", en: "Collapse sessions" })
                  : localeText(locale, { zh: "展开出题会话", en: "Expand sessions" })}
                onClick={() => setAgentLeftOpen((value) => !value)}
              >
                <PanelToggleIcon open={agentLeftOpen} side="left" />
              </button>
              <div
                className="agent-drawer-resize"
                role="separator"
                aria-label={localeText(locale, { zh: "调整出题会话宽度", en: "Resize sessions" })}
                title={localeText(locale, { zh: "拖动调整出题会话宽度", en: "Drag to resize sessions" })}
                onPointerDown={(event) => startAgentDrawerResize("left", event)}
              />
            </div>
            <AgentSessionTimeline
              locale={locale}
              text={text}
              session={selectedAgentSession}
              runs={visibleAgentRuns}
              selectedRunId={selectedAgentRunId}
              selectedDraftId={selectedDraft?.id ?? null}
              expandedStepIds={expandedAgentStepIds}
              loading={agentSessionsQuery.isLoading || selectedAgentSessionQuery.isLoading}
              followUpDraft={agentFollowUpDraft}
              followUpLines={agentFollowUpLines}
              followUpBusy={agentFollowUpBusy}
              canFollowUp={Boolean(selectedAgentRun && agentModelAvailable)}
              emptyMessage={agentRunsEmptyMessage}
              onSelectRun={selectAgentRun}
              onSelectDraft={previewAgentDraft}
              onToggleStep={toggleAgentStep}
              onFollowUpDraftChange={setAgentFollowUpDraft}
              onFollowUpSubmit={sendAgentFollowUp}
              onRetryRun={retrySelectedAgentRun}
            />
            <div className="agent-drawer-edge agent-right-edge">
              <div
                className="agent-drawer-resize"
                role="separator"
                aria-label={localeText(locale, { zh: "调整草稿预览宽度", en: "Resize draft preview" })}
                title={localeText(locale, { zh: "拖动调整草稿预览宽度", en: "Drag to resize draft preview" })}
                onPointerDown={(event) => startAgentDrawerResize("right", event)}
              />
              <button
                type="button"
                className="agent-drawer-toggle"
                aria-label={agentRightOpen
                  ? localeText(locale, { zh: "收起草稿预览", en: "Collapse draft preview" })
                  : localeText(locale, { zh: "展开草稿预览", en: "Expand draft preview" })}
                aria-expanded={agentRightOpen}
                title={agentRightOpen
                  ? localeText(locale, { zh: "收起草稿预览", en: "Collapse draft preview" })
                  : localeText(locale, { zh: "展开草稿预览", en: "Expand draft preview" })}
                onClick={() => setAgentRightOpen((value) => !value)}
              >
                <PanelToggleIcon open={agentRightOpen} side="right" />
              </button>
            </div>
            <aside className="agent-drawer agent-right-drawer">
              <div className="agent-drawer-content">
                <div className="agent-preview">
                  <h3>{text.draftPreview}</h3>
                  {selectedDraft ? (
                    <>
                  <div className="testcase-panel-head">
                    <div>
                      <strong>{selectedDraft.title}</strong>
                      <span className="muted">{selectedDraft.slug} / {authoringModeLabel(selectedDraft.mode, locale)} / {draftStatusLabel(selectedDraft.status, locale)}</span>
                    </div>
                    <span className={`draft-status-chip ${draftStatusClass(selectedDraft.status)}`}>{draftStatusLabel(selectedDraft.status, locale)}</span>
                  </div>
                  {isImportedDraft(selectedDraft) ? <DraftSourceSummary draft={selectedDraft} locale={locale} text={text} /> : null}
                  <details className="markdown-preview-panel">
                    <summary>{localeText(locale, { zh: "Markdown 预览", en: "Markdown preview" })}</summary>
                    <MarkdownBlock value={selectedDraft.description} />
                    {selectedDraft.hint ? <MarkdownBlock value={selectedDraft.hint} className="markdown-preview-muted" /> : null}
                  </details>
                  {draftSaveMessage ? <p className="muted">{draftSaveMessage}</p> : null}
                  {draftEdit ? (
                    <div className="draft-edit-panel">
                      <div className="testcase-panel-head">
                        <h3>{text.draftEdit}</h3>
                        <button className="primary" disabled={draftEditLocked} onClick={saveSelectedDraftEdit}>{draftSaving ? text.loading : text.revalidateDraft}</button>
                      </div>
                      <div className="admin-edit-grid draft-edit-grid">
                        <label>{text.titleLabel}<input value={draftEdit.title} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ title: event.target.value })} /></label>
                        <label>{text.slugLabel}<input value={draftEdit.slug} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ slug: event.target.value })} /></label>
                        <label>{text.modeLabel}
                          <select value={draftEdit.mode} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ mode: event.target.value as ProblemAuthoringMode })}>
                            <option value="both">{authoringModeLabel("both", locale)}</option>
                            <option value="function">{authoringModeLabel("function", locale)}</option>
                            <option value="acm">{authoringModeLabel("acm", locale)}</option>
                          </select>
                        </label>
                        <div className="agent-field language-checklist-label"><span>{text.targetLanguagesLabel}</span>
                          <div className="language-checklist">
                            {LANGUAGES.map((item) => (
                              <label className="checkbox-label language-chip" key={item}>
                                <input
                                  type="checkbox"
                                  checked={draftEdit.target_languages.includes(item)}
                                  disabled={draftEditLocked}
                                  onChange={() => toggleDraftTargetLanguage(item)}
                                />
                                {languageLabel(item)}
                              </label>
                            ))}
                          </div>
                        </div>
                        <label>{localeText(locale, { zh: "难度", en: "Difficulty" })}
                          <select value={draftEdit.difficulty} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ difficulty: event.target.value as "easy" | "medium" | "hard" })}>
                            <option value="easy">easy</option>
                            <option value="medium">medium</option>
                            <option value="hard">hard</option>
                          </select>
                        </label>
                        <label>{text.tagsLabel}<input value={draftEdit.tags} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ tags: event.target.value })} /></label>
                        <label>{text.functionSignatureLabel}<input value={draftEdit.function_signature} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ function_signature: event.target.value })} /></label>
                        <label>{text.timeLimitLabel}<input type="number" min="100" value={draftEdit.time_limit} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ time_limit: event.target.value })} /></label>
                        <label>{text.memoryLimitLabel}<input type="number" min="16" value={draftEdit.memory_limit} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ memory_limit: event.target.value })} /></label>
                        <label>{text.descriptionLabel}<textarea value={draftEdit.description} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ description: event.target.value })} /></label>
                        <label>{text.hintLabel}<textarea value={draftEdit.hint} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ hint: event.target.value })} /></label>
                        <label>{text.inputFormatLabel}<textarea value={draftEdit.input_format} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ input_format: event.target.value })} /></label>
                        <label>{text.outputFormatLabel}<textarea value={draftEdit.output_format} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ output_format: event.target.value })} /></label>
                        <label>{text.timeComplexityLabel}<input value={draftEdit.time_complexity} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ time_complexity: event.target.value })} /></label>
                        <label>{text.spaceComplexityLabel}<input value={draftEdit.space_complexity} disabled={draftEditLocked} onChange={(event) => updateDraftEdit({ space_complexity: event.target.value })} /></label>
                      </div>
                      <div className="testcase-panel-head">
                        <h3>{text.officialSolutionsLabel}</h3>
                        <div className="agent-actions">
                          {LANGUAGES.filter((item) => !draftEdit.official_solutions.some((solution) => solution.language === item)).map((item) => (
                            <button key={item} disabled={draftEditLocked} onClick={() => addDraftSolution(item)}>
                              + {languageLabel(item)}
                            </button>
                          ))}
                        </div>
                      </div>
                      {draftEdit.mode === "both" ? <p className="muted">{text.dualModeSolutionNote}</p> : null}
                      <div className="admin-testcase-list official-solution-list">
                        {draftEdit.official_solutions.map((solution, index) => (
                          <article className="testcase-card admin-testcase-card official-solution-card" key={`${solution.language}-${index}`}>
                            <div className="testcase-card-head">
                              <strong>{languageLabel(solution.language)}</strong>
                              {index === 0 ? <span className="case-chip sample">{localeText(locale, { zh: "主解法", en: "Primary" })}</span> : null}
                            </div>
                            <div className="admin-edit-grid official-solution-grid">
                              <label>{localeText(locale, { zh: "语言", en: "Language" })}
                                <select value={solution.language} disabled={draftEditLocked} onChange={(event) => updateDraftSolution(index, { language: event.target.value })}>
                                  {LANGUAGES.map((item) => (
                                    <option
                                      key={item}
                                      value={item}
                                      disabled={item !== solution.language && draftEdit.official_solutions.some((candidate) => candidate.language === item)}
                                    >
                                      {languageLabel(item)}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label>{text.officialExplanationLabel}<textarea value={solution.explanation} disabled={draftEditLocked} onChange={(event) => updateDraftSolution(index, { explanation: event.target.value })} /></label>
                              <label>{draftEdit.mode === "acm" ? text.acmOfficialCodeLabel : text.functionOfficialCodeLabel}<textarea value={solution.code} disabled={draftEditLocked} onChange={(event) => updateDraftSolution(index, { code: event.target.value })} /></label>
                            </div>
                            <div className="agent-actions">
                              <button
                                disabled={draftEditLocked || !agentModelAvailable}
                                title={!agentModelAvailable ? (agentModelUnavailableReason ?? undefined) : undefined}
                                onClick={() => generateDraftSolution(index)}
                              >
                                {draftSolutionGenerating === solution.language ? text.aiFillingSolution : text.aiFillSolution}
                              </button>
                              <button disabled={draftEditLocked || draftEdit.official_solutions.length <= 1} onClick={() => removeDraftSolution(index)}>{text.delete}</button>
                            </div>
                          </article>
                        ))}
                      </div>
                      <div className="testcase-panel-head">
                        <h3>{text.testcaseDetails}</h3>
                        <div className="agent-actions">
                          <button disabled={draftEditLocked} onClick={() => addDraftCase(false)}>{text.addPublicCase}</button>
                          <button disabled={draftEditLocked} onClick={() => addDraftCase(true)}>{text.addHiddenCase}</button>
                        </div>
                      </div>
                      <div className="admin-testcase-list">
                        {draftEdit.testcases.map((testcase, index) => (
                          <article className="testcase-card admin-testcase-card" key={`${index}-${testcase.order}`}>
                            <div className="testcase-card-head">
                              <strong>{localeText(locale, { zh: "用例", en: "Case" })} {index + 1}</strong>
                              <span className={testcase.is_hidden ? "case-chip hidden" : "case-chip public"}>{testcase.is_hidden ? text.hidden : text.public}</span>
                              {testcase.is_sample ? <span className="case-chip sample">{text.sample}</span> : null}
                            </div>
                            <div className="testcase-edit-grid">
                              <label>{text.inputLabel}<textarea value={testcase.input} disabled={draftEditLocked} onChange={(event) => updateDraftCase(index, { input: event.target.value })} /></label>
                              <label>{text.outputLabel}<textarea value={testcase.output} disabled={draftEditLocked} onChange={(event) => updateDraftCase(index, { output: event.target.value })} /></label>
                              <label>{text.orderLabel}<input type="number" min="1" value={testcase.order} disabled={draftEditLocked} onChange={(event) => updateDraftCase(index, { order: Number(event.target.value) || index + 1 })} /></label>
                              <label>{localeText(locale, { zh: "解释", en: "Explanation" })}<input value={testcase.explanation} disabled={draftEditLocked} onChange={(event) => updateDraftCase(index, { explanation: event.target.value })} /></label>
                              <label className="checkbox-label"><input type="checkbox" checked={testcase.is_hidden} disabled={draftEditLocked} onChange={(event) => updateDraftCase(index, { is_hidden: event.target.checked, is_sample: event.target.checked ? false : testcase.is_sample })} />{text.hidden}</label>
                              <label className="checkbox-label"><input type="checkbox" checked={testcase.is_sample} disabled={draftEditLocked} onChange={(event) => updateDraftCase(index, { is_sample: event.target.checked, is_hidden: event.target.checked ? false : testcase.is_hidden })} />{text.sample}</label>
                            </div>
                            <div className="agent-actions">
                              <button disabled={draftEditLocked} onClick={() => removeDraftCase(index)}>{text.delete}</button>
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <h3>{text.validation}</h3>
                  <ValidationReport draft={selectedDraft} locale={locale} />
                  <DraftTestcasePanel draft={selectedDraft} locale={locale} />
                  <div className="agent-actions">
                    <button className="primary" disabled={draftEditLocked || !draftEdit} onClick={saveSelectedDraftEdit}>{draftSaving ? text.loading : text.revalidateDraft}</button>
                    <button disabled={draftSaving || !draftHasUnsavedChanges} onClick={() => selectedDraft && setDraftEdit(draftEditFromDraft(selectedDraft))}>{text.resetDraftEdit}</button>
                    <button className="primary" disabled={draftSaving || selectedDraft.status !== "validated" || draftHasUnsavedChanges} onClick={approveSelectedDraft}>{text.approveDraft}</button>
                    <button disabled={draftEditLocked || selectedDraft.status === "rejected"} onClick={rejectSelectedDraft}>{text.rejectDraft}</button>
                  </div>
                </>
                  ) : <p className="muted">{localeText(locale, { zh: "还没有选中的草稿。", en: "No draft selected." })}</p>}
                </div>
              </div>
              <span className="agent-drawer-rail" aria-hidden={agentRightOpen}>
                <span>{localeText(locale, { zh: "预", en: "P" })}</span>
                <span>{localeText(locale, { zh: "览", en: "V" })}</span>
              </span>
            </aside>
          </div>
        </section> : null}
        {adminSection === "users" ? (
          <section className="admin-panel admin-section-panel">
            <div className="admin-panel-header">
              <h2>{text.users}</h2>
              <span className="muted">{pageSummary(userPagination)}</span>
            </div>
            <div className="admin-filters">
              <input
                value={userSearch}
                onChange={(event) => {
                  setUserSearch(event.target.value);
                  setUserPage(1);
                }}
                placeholder={text.searchUsers}
              />
              <select
                value={userRoleFilter}
                onChange={(event) => {
                  setUserRoleFilter(event.target.value);
                  setUserPage(1);
                }}
              >
                <option value="">{text.allRoles}</option>
                <option value="user">{roleLabel("user", locale)}</option>
                <option value="content_admin">{roleLabel("content_admin", locale)}</option>
                <option value="admin">{roleLabel("admin", locale)}</option>
              </select>
              <select
                value={userStatusFilter}
                onChange={(event) => {
                  setUserStatusFilter(event.target.value);
                  setUserPage(1);
                }}
              >
                <option value="">{text.allStatus}</option>
                <option value="active">{text.active}</option>
                <option value="disabled">{text.disabled}</option>
              </select>
            </div>
            {users.length ? users.map((user: any) => (
              <article className={selectedUserId === user.id ? "admin-row active" : "admin-row"} key={user.id}>
                <div>
                  <strong>{user.username}</strong>
                  <span>{user.email}</span>
                </div>
                <select
                  value={user.role}
                  disabled={currentUser?.role !== "admin"}
                  onChange={(event) => updateUser(user.id, { role: event.target.value })}
                >
                  <option value="user">{roleLabel("user", locale)}</option>
                  <option value="content_admin">{roleLabel("content_admin", locale)}</option>
                  <option value="admin">{roleLabel("admin", locale)}</option>
                </select>
                <button onClick={() => updateUser(user.id, { is_active: !user.is_active })}>
                  {user.is_active ? text.active : text.disabled}
                </button>
                <button onClick={() => setSelectedUserId(selectedUserId === user.id ? null : user.id)}>{text.manage}</button>
              </article>
            )) : <p className="muted">{text.noResults}</p>}
            <div className="admin-pagination">
              <button disabled={userPage <= 1} onClick={() => setUserPage((page) => Math.max(1, page - 1))}>{text.previous}</button>
              <button disabled={userPage >= Math.max(Number(userPagination.total_pages ?? 0), 1)} onClick={() => setUserPage((page) => page + 1)}>{text.next}</button>
            </div>
            {selectedUser ? (
              <div className="admin-edit-panel">
                <h3>{selectedUser.username}</h3>
                <span className="muted">{selectedUser.id}</span>
                <div className="admin-edit-grid">
                  <label>{localeText(locale, { zh: "角色", en: "Role" })}
                    <select
                      value={selectedUser.role}
                      disabled={currentUser?.role !== "admin"}
                      onChange={(event) => updateUser(selectedUser.id, { role: event.target.value })}
                    >
                      <option value="user">{roleLabel("user", locale)}</option>
                      <option value="content_admin">{roleLabel("content_admin", locale)}</option>
                      <option value="admin">{roleLabel("admin", locale)}</option>
                    </select>
                  </label>
                  {selectedUser.role === "content_admin" ? (
                    <div className="agent-field language-checklist-label">
                      <span>{localeText(locale, { zh: "内容管理员权限", en: "Content admin permissions" })}</span>
                      <div className="language-checklist">
                        {Object.values(CONTENT_PERMISSIONS).map((permission) => (
                          <label className="checkbox-label language-chip" key={permission}>
                            <input
                              type="checkbox"
                              checked={(selectedUser.content_admin_permissions ?? []).includes(permission)}
                              disabled={currentUser?.role !== "admin"}
                              onChange={() => updateUser(selectedUser.id, {
                                content_admin_permissions: togglePermission(selectedUser.content_admin_permissions, permission),
                              })}
                            />
                            {contentPermissionLabel(permission, locale)}
                          </label>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <button onClick={() => updateUser(selectedUser.id, { is_active: !selectedUser.is_active })}>
                    {selectedUser.is_active ? text.disabled : text.active}
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        ) : null}
        {adminSection === "problems" ? (
          <section className="admin-panel admin-section-panel">
            <div className="admin-panel-header">
              <h2>{text.problems}</h2>
              <span className="muted">{pageSummary(problemPagination)}</span>
            </div>
            <div className="admin-filters problem-filters">
              <input
                value={problemSearch}
                onChange={(event) => {
                  setProblemSearch(event.target.value);
                  setProblemPage(1);
                }}
                placeholder={text.searchProblems}
              />
              <select
                value={problemDifficultyFilter}
                onChange={(event) => {
                  setProblemDifficultyFilter(event.target.value);
                  setProblemPage(1);
                }}
              >
                <option value="">{text.allDifficulty}</option>
                <option value="easy">easy</option>
                <option value="medium">medium</option>
                <option value="hard">hard</option>
              </select>
              <select
                value={problemVisibilityFilter}
                onChange={(event) => {
                  setProblemVisibilityFilter(event.target.value);
                  setProblemPage(1);
                }}
              >
                <option value="">{text.allVisibility}</option>
                <option value="public">{text.public}</option>
                <option value="private">{text.private}</option>
              </select>
            </div>
            {problems.length ? problems.map((problem: any) => (
              <article className={selectedProblemId === problem.id ? "admin-row problem-admin-row active" : "admin-row problem-admin-row"} key={problem.id}>
                <div>
                  <strong>{problem.title}</strong>
                <span>{problem.slug} · {problem.difficulty} · {problem.tags.join(", ")}</span>
              </div>
                <select value={problem.difficulty} onChange={(event) => updateProblem(problem.id, { difficulty: event.target.value })}>
                  <option value="easy">easy</option>
                  <option value="medium">medium</option>
                  <option value="hard">hard</option>
                </select>
                <button onClick={() => updateProblem(problem.id, { is_public: !problem.is_public })}>
                  {problem.is_public ? text.public : text.private}
                </button>
                <span>{problem.testcase_count} {text.cases}</span>
                <span>{problem.hidden_testcase_count} {text.hidden}</span>
                <span>{problem.solution_count} {text.solutions}</span>
                <button onClick={() => selectedProblemId === problem.id ? cancelProblemEdit() : chooseProblem(problem)}>
                  {selectedProblemId === problem.id ? text.cancel : text.edit}
                </button>
              </article>
            )) : <p className="muted">{text.noResults}</p>}
            <div className="admin-pagination">
              <button disabled={problemPage <= 1} onClick={() => setProblemPage((page) => Math.max(1, page - 1))}>{text.previous}</button>
              <button disabled={problemPage >= Math.max(Number(problemPagination.total_pages ?? 0), 1)} onClick={() => setProblemPage((page) => page + 1)}>{text.next}</button>
            </div>
            {selectedProblem ? (
              <div className="admin-edit-panel problem-edit-panel">
                <div className="admin-edit-panel-header">
                  <div>
                    <h3>{selectedProblem.title}</h3>
                    <span className="muted">{selectedProblem.slug} · {selectedProblem.mode} · {selectedProblem.testcase_count} {text.cases} · {selectedProblem.hidden_testcase_count} {text.hidden}</span>
                  </div>
                  <div className="agent-actions">
                    <button className="primary" disabled={problemEditLocked} onClick={() => saveProblemEdit(false)}>{problemSaving ? text.loading : text.save}</button>
                    <button className="primary" disabled={problemEditLocked} onClick={() => saveProblemEdit(true)}>{problemSaving ? text.loading : text.revalidateDraft}</button>
                    <button disabled={problemEditLocked} onClick={cancelProblemEdit}>{text.cancel}</button>
                    <button className="danger" disabled={problemEditLocked} onClick={() => deleteProblem(selectedProblem.id)}>{text.deleteProblem}</button>
                  </div>
                </div>
                {problemSaveMessage ? <p className="muted">{problemSaveMessage}</p> : null}
                <ProblemValidationReport report={problemValidationReport} locale={locale} />
                <div className="admin-edit-grid problem-core-grid">
                  <label>{text.titleLabel}<input value={problemEdit.title} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, title: event.target.value }))} /></label>
                  <label>{text.slugLabel}<input value={problemEdit.slug} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, slug: event.target.value }))} /></label>
                  <label>{localeText(locale, { zh: "难度", en: "Difficulty" })}
                    <select value={problemEdit.difficulty} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, difficulty: event.target.value as "easy" | "medium" | "hard" }))}>
                      <option value="easy">easy</option>
                      <option value="medium">medium</option>
                      <option value="hard">hard</option>
                    </select>
                  </label>
                  <label>{text.modeLabel}
                    <select value={problemEdit.mode} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, mode: event.target.value as ProblemAuthoringMode }))}>
                      <option value="both">{authoringModeLabel("both", locale)}</option>
                      <option value="function">{authoringModeLabel("function", locale)}</option>
                      <option value="acm">{authoringModeLabel("acm", locale)}</option>
                    </select>
                  </label>
                  <label>{text.tagsLabel}<input value={problemEdit.tags} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, tags: event.target.value }))} /></label>
                  <label>{text.functionSignatureLabel}<input value={problemEdit.function_signature} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, function_signature: event.target.value }))} /></label>
                  <label>{text.timeLimitLabel}<input type="number" min="100" value={problemEdit.time_limit} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, time_limit: event.target.value }))} /></label>
                  <label>{text.memoryLimitLabel}<input type="number" min="16" value={problemEdit.memory_limit} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, memory_limit: event.target.value }))} /></label>
                  <label>{text.descriptionLabel}<textarea value={problemEdit.description} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, description: event.target.value }))} /></label>
                  <label>{text.hintLabel}<textarea value={problemEdit.hint} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, hint: event.target.value }))} /></label>
                  <label>{text.inputFormatLabel}<textarea value={problemEdit.input_format} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, input_format: event.target.value }))} /></label>
                  <label>{text.outputFormatLabel}<textarea value={problemEdit.output_format} disabled={problemEditLocked} onChange={(event) => setProblemEdit((value) => ({ ...value, output_format: event.target.value }))} /></label>
                </div>
                <div className="testcase-panel-head">
                  <h3>{text.officialSolutionsLabel}</h3>
                  <div className="agent-actions">
                    {LANGUAGES.filter((item) => !problemEdit.solutions.some((solution) => solution.language === item)).map((item) => (
                      <button key={item} disabled={problemEditLocked} onClick={() => addProblemSolution(item)}>+ {languageLabel(item)}</button>
                    ))}
                  </div>
                </div>
                {problemEdit.mode === "both" ? <p className="muted">{text.dualModeSolutionNote}</p> : null}
                <div className="admin-testcase-list official-solution-list">
                  {problemEdit.solutions.length ? problemEdit.solutions.map((solution, index) => (
                    <article className="testcase-card admin-testcase-card official-solution-card" key={`${solution.language}-${index}`}>
                      <div className="testcase-card-head">
                        <strong>{languageLabel(solution.language)}</strong>
                      </div>
                      <div className="admin-edit-grid official-solution-grid">
                        <label>{localeText(locale, { zh: "语言", en: "Language" })}
                          <select value={solution.language} disabled={problemEditLocked} onChange={(event) => updateProblemSolution(index, { language: event.target.value })}>
                            {LANGUAGES.map((item) => (
                              <option
                                key={item}
                                value={item}
                                disabled={item !== solution.language && problemEdit.solutions.some((candidate) => candidate.language === item)}
                              >
                                {languageLabel(item)}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>{text.timeComplexityLabel}<input value={solution.time_complexity} disabled={problemEditLocked} onChange={(event) => updateProblemSolution(index, { time_complexity: event.target.value })} /></label>
                        <label>{text.spaceComplexityLabel}<input value={solution.space_complexity} disabled={problemEditLocked} onChange={(event) => updateProblemSolution(index, { space_complexity: event.target.value })} /></label>
                        <label>{text.officialExplanationLabel}<textarea value={solution.explanation} disabled={problemEditLocked} onChange={(event) => updateProblemSolution(index, { explanation: event.target.value })} /></label>
                        <label>{problemEdit.mode === "acm" ? text.acmOfficialCodeLabel : text.functionOfficialCodeLabel}<textarea value={solution.code} disabled={problemEditLocked} onChange={(event) => updateProblemSolution(index, { code: event.target.value })} /></label>
                      </div>
                      <div className="agent-actions">
                        <button
                          disabled={problemEditLocked || !agentModelAvailable}
                          title={!agentModelAvailable ? (agentModelUnavailableReason ?? undefined) : undefined}
                          onClick={() => generateProblemSolution(index)}
                        >
                          {problemSolutionGenerating === solution.language ? text.aiFillingSolution : text.aiFillSolution}
                        </button>
                        <button disabled={problemEditLocked} onClick={() => removeProblemSolution(index)}>{text.delete}</button>
                      </div>
                    </article>
                  )) : <p className="muted">{localeText(locale, { zh: "还没有官方解法。请至少新增一个语言解法后再重新校验。", en: "No official solutions yet. Add at least one language before revalidation." })}</p>}
                </div>
                <div className="agent-actions">
                  <button className="primary" disabled={problemEditLocked} onClick={() => saveProblemEdit(false)}>{problemSaving ? text.loading : text.save}</button>
                  <button className="primary" disabled={problemEditLocked} onClick={() => saveProblemEdit(true)}>{problemSaving ? text.loading : text.revalidateDraft}</button>
                  <button disabled={problemEditLocked} onClick={cancelProblemEdit}>{text.cancel}</button>
                  <button disabled={problemEditLocked} onClick={() => updateProblem(selectedProblem.id, { is_public: !selectedProblem.is_public })}>
                    {selectedProblem.is_public ? text.private : text.public}
                  </button>
                  <button className="danger" disabled={problemEditLocked} onClick={() => deleteProblem(selectedProblem.id)}>{text.deleteProblem}</button>
                </div>
                <div className="testcase-manager">
                  <div className="testcase-panel-head">
                    <h3>{text.testcaseDetails}</h3>
                    <span className="muted">{testcasesQuery.isLoading ? text.loading : `${testcasesQuery.data?.length ?? 0} ${text.cases}`}</span>
                  </div>
                  <div className="testcase-create-panel">
                    <strong>{text.newTestcase}</strong>
                    <div className="testcase-edit-grid">
                      <label>{text.inputLabel}<textarea value={newTestcase.input} onChange={(event) => setNewTestcase((value) => ({ ...value, input: event.target.value }))} /></label>
                      <label>{text.outputLabel}<textarea value={newTestcase.output} onChange={(event) => setNewTestcase((value) => ({ ...value, output: event.target.value }))} /></label>
                      <label>{text.scoreLabel}<input type="number" min="0" value={newTestcase.score} onChange={(event) => setNewTestcase((value) => ({ ...value, score: event.target.value }))} /></label>
                      <label>{text.orderLabel}<input type="number" min="0" value={newTestcase.order} onChange={(event) => setNewTestcase((value) => ({ ...value, order: event.target.value }))} /></label>
                      <label className="checkbox-label"><input type="checkbox" checked={newTestcase.is_hidden} onChange={(event) => setNewTestcase((value) => ({ ...value, is_hidden: event.target.checked, is_sample: event.target.checked ? false : value.is_sample }))} />{text.hidden}</label>
                      <label className="checkbox-label"><input type="checkbox" checked={newTestcase.is_sample} onChange={(event) => setNewTestcase((value) => ({ ...value, is_sample: event.target.checked, is_hidden: event.target.checked ? false : value.is_hidden }))} />{text.sample}</label>
                    </div>
                    <div className="agent-actions">
                      <button className="primary" onClick={createProblemTestcase}>{text.add}</button>
                    </div>
                  </div>
                  <div className="admin-testcase-list">
                    {(testcasesQuery.data ?? []).length ? (testcasesQuery.data ?? []).map((testcase) => {
                      const edit = testcaseEdits[testcase.id] ?? testcase;
                      return (
                        <article className="testcase-card admin-testcase-card" key={testcase.id}>
                          <div className="testcase-card-head">
                            <strong>{localeText(locale, { zh: "用例", en: "Case" })} {edit.order}</strong>
                            <span className={edit.is_hidden ? "case-chip hidden" : "case-chip public"}>{edit.is_hidden ? text.hidden : text.public}</span>
                            {edit.is_sample ? <span className="case-chip sample">{text.sample}</span> : null}
                          </div>
                          <div className="testcase-edit-grid">
                            <label>{text.inputLabel}<textarea value={edit.input} onChange={(event) => updateTestcaseEdit(testcase.id, { input: event.target.value })} /></label>
                            <label>{text.outputLabel}<textarea value={edit.output} onChange={(event) => updateTestcaseEdit(testcase.id, { output: event.target.value })} /></label>
                            <label>{text.scoreLabel}<input type="number" min="0" value={edit.score} onChange={(event) => updateTestcaseEdit(testcase.id, { score: Number(event.target.value) || 0 })} /></label>
                            <label>{text.orderLabel}<input type="number" min="0" value={edit.order} onChange={(event) => updateTestcaseEdit(testcase.id, { order: Number(event.target.value) || 0 })} /></label>
                            <label className="checkbox-label"><input type="checkbox" checked={edit.is_hidden} onChange={(event) => updateTestcaseEdit(testcase.id, { is_hidden: event.target.checked })} />{text.hidden}</label>
                            <label className="checkbox-label"><input type="checkbox" checked={edit.is_sample} onChange={(event) => updateTestcaseEdit(testcase.id, { is_sample: event.target.checked })} />{text.sample}</label>
                          </div>
                          <div className="agent-actions">
                            <button className="primary" onClick={() => saveProblemTestcase(testcase.id)}>{text.save}</button>
                            <button onClick={() => deleteProblemTestcase(testcase.id)}>{text.delete}</button>
                          </div>
                        </article>
                      );
                    }) : <p className="muted">{testcasesQuery.isLoading ? text.loading : text.noTestcases}</p>}
                  </div>
                </div>
              </div>
            ) : null}
          </section>
        ) : null}
      </section>
    </main>
  );
}

function App() {
  const recentProblemId = useAppStore((state) => state.recentProblemId);
  const [selectedId, setSelectedId] = useState<string | null>(recentProblemId);
  const [view, setView] = useState<View>(recentProblemId ? "workbench" : "library");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [locale, setLocale] = useState<Locale>(() => readStoredLocale());
  const [theme, setTheme] = useState<AppTheme>(() => (localStorage.getItem("fastoj.theme") === "light" ? "light" : "dark"));
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem("fastoj.jwt")));
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [graphTag, setGraphTag] = useState("");
  const problemsQuery = useQuery({ queryKey: ["problems", "graph"], queryFn: () => api.problems({}) });
  const problems = useMemo(() => problemsQuery.data ?? [], [problemsQuery.data]);

  useEffect(() => {
    document.documentElement.lang = htmlLangForLocale(locale);
    writeStoredLocale(locale);
  }, [locale]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    localStorage.setItem("fastoj.theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!authenticated) {
      setCurrentUser(null);
      return;
    }
    let cancelled = false;
    const authToken = localStorage.getItem("fastoj.jwt");
    if (!authToken) {
      setCurrentUser(null);
      setAuthenticated(false);
      setView("auth");
      return;
    }
    api.me()
      .then((user) => {
        if (!cancelled && localStorage.getItem("fastoj.jwt") === authToken) {
          setCurrentUser(user);
          const userLocale = normalizeLocale(user.locale);
          if (userLocale) setLocale(userLocale);
        }
      })
      .catch((error) => {
        if (!cancelled && isUnauthorized(error) && localStorage.getItem("fastoj.jwt") === authToken) {
          localStorage.removeItem("fastoj.jwt");
          setAuthenticated(false);
          setView("auth");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [authenticated]);

  function openProblem(id: string) {
    setSelectedId(id);
    setView("workbench");
  }

  function openAuth(mode: AuthMode) {
    setAuthMode(mode);
    setView("auth");
  }

  function toggleLocale() {
    setLocalePreference(nextLocale(locale));
  }

  function setLocalePreference(next: Locale) {
    setLocale(next);
    if (!currentUser) return;
    setCurrentUser({ ...currentUser, locale: next });
    api.updateMe({ locale: next })
      .then(setCurrentUser)
      .catch(() => undefined);
  }

  function logout() {
    localStorage.removeItem("fastoj.jwt");
    setAuthenticated(false);
    setCurrentUser(null);
    setView("library");
  }

  return (
    <div className="app-shell" data-theme={theme}>
      <AuthBar view={view} authenticated={authenticated} currentUser={currentUser} locale={locale} theme={theme} onView={setView} onAuth={openAuth} onLogout={logout} onLocale={toggleLocale} onTheme={setTheme} />
      {view === "auth" ? (
        <Suspense fallback={<LazySurface className="auth-page" label={localeText(locale, { zh: "正在加载账号页面...", en: "Loading account page..." })} />}>
          <AuthPage mode={authMode} locale={locale} onMode={setAuthMode} onDone={() => { setAuthenticated(true); setView("library"); }} />
        </Suspense>
      ) : null}
      {view === "settings" ? (
        <Suspense fallback={<LazySurface className="settings-page" label={localeText(locale, { zh: "正在加载设置...", en: "Loading settings..." })} />}>
          <SettingsPage locale={locale} currentUser={currentUser} theme={theme} onTheme={setTheme} onLocaleChange={setLocalePreference} onClose={() => setView("library")} onProfileSaved={setCurrentUser} />
        </Suspense>
      ) : null}
      {view === "admin" ? <AdminPage locale={locale} currentUser={currentUser} onBack={() => setView("library")} /> : null}
      {view === "library" ? <LibraryPage selectedId={selectedId} selectedTag={graphTag} locale={locale} onSelect={openProblem} onGraph={() => setView("graph")} /> : null}
      {view === "workbench" ? (
        <Workspace
          problemId={selectedId}
          locale={locale}
          theme={theme}
          currentUser={currentUser}
          onBackToLibrary={() => setView("library")}
          authenticated={authenticated}
          onRequireAuth={() => {
            localStorage.removeItem("fastoj.jwt");
            setAuthenticated(false);
            openAuth("login");
          }}
        />
      ) : null}
      {view === "graph" ? (
        <Suspense fallback={<LazySurface className="graph-page" label={localeText(locale, { zh: "正在加载知识图谱...", en: "Loading knowledge graph..." })} />}>
          <TrainingGraph
            problems={problems}
            locale={locale}
            onTag={(tag) => {
              setGraphTag(tag);
              setView("library");
            }}
          />
        </Suspense>
      ) : null}
    </div>
  );
}

const rootElement = document.getElementById("root");

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </React.StrictMode>,
  );
}
