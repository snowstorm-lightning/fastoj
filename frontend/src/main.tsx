import React, { useEffect, useMemo, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";

import "./styles.css";
import {
  api,
  isUnauthorized,
  makeJudgeSocket,
  type AgentStep,
  type AIModelProfile,
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
  type ProblemListItem,
  type SubmissionDetail,
} from "./lib/schemas";
import {
  buildStarter,
  getFunctionSpec,
  getLocalizedFunctionDescription,
  getProblemMode,
  getVisualSpec,
  type JudgeMode,
} from "./lib/problemModes";
import {
  canonicalTagQuery,
  localizeDifficulty,
  localizeTag,
  localizeTags,
  localizedProblem,
  matchesLocalizedProblem,
  type Locale,
  UI,
  verdictInfo,
} from "./lib/i18n";
import { measureTrainingText } from "./lib/textLayout";
import { LANGUAGES, useAppStore } from "./stores/useAppStore";
import { AICopilotPanel } from "./components/AICopilotPanel";
import { CodeBlock } from "./components/CodeBlock";
import { CodeEditor } from "./components/CodeEditor";
import { JudgeTimeline, type JudgeEvent } from "./components/JudgeTimeline";
import { SubmissionTrail } from "./components/SubmissionTrail";
import { TrainingGraph } from "./components/TrainingGraph";

const queryClient = new QueryClient();

type View = "library" | "workbench" | "graph" | "auth" | "settings" | "admin";
type DetailTab = "cases" | "solution" | "judge" | "trail" | "discussion";
type AuthMode = "login" | "register";
type LibraryLayout = "card" | "list";
type AppTheme = "light" | "dark";
type DiscussionPost = { id: string; author: string; body: string; createdAt: string };
type AIChatLine = { id: string; role: "user" | "assistant"; message: string; suggestions?: string[] };

const AI_MODEL_OPTIONS: Array<{ value: AIModelProfile; zh: string; en: string; detailZh: string; detailEn: string }> = [
  { value: "default", zh: "自动选择", en: "Auto route", detailZh: "使用服务器默认 AI 配置", detailEn: "Use the server default AI profile" },
  { value: "deepseek", zh: "DeepSeek 云端", en: "DeepSeek Cloud", detailZh: "调用 DeepSeek 兼容接口", detailEn: "Use the DeepSeek-compatible API" },
  { value: "qwen-local", zh: "Qwen 本地", en: "Local Qwen", detailZh: "连接本机兼容 OpenAI 接口的服务", detailEn: "Use a local OpenAI-compatible Qwen server" },
];

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const percent = (value: number) => Math.round(clamp(value, 0, 1) * 100);

function IconGlyph({ children }: { children: React.ReactNode }) {
  return <span className="icon-glyph" aria-hidden="true">{children}</span>;
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
  const text = UI[locale];
  return (
    <header className="topbar">
      <button className="brand-lockup brand-button" title={locale === "zh" ? "返回题库首页" : "Back to problem library"} onClick={() => onView("library")}>
        <strong>FastOJ</strong>
        <span>{locale === "zh" ? "AI 练习判题" : "AI interview judge"}</span>
      </button>
      <div className="theme-switch segmented" role="group" aria-label={locale === "zh" ? "界面主题" : "Theme"}>
        <button type="button" className={theme === "light" ? "active" : ""} aria-pressed={theme === "light"} onClick={() => onTheme("light")}>
          {locale === "zh" ? "浅色" : "Light"}
        </button>
        <button type="button" className={theme === "dark" ? "active" : ""} aria-pressed={theme === "dark"} onClick={() => onTheme("dark")}>
          {locale === "zh" ? "深色" : "Dark"}
        </button>
      </div>
      <nav className="topnav" aria-label={locale === "zh" ? "主导航" : "Main navigation"}>
        <button className={view === "library" ? "active" : ""} onClick={() => onView("library")}>{text.navLibrary}</button>
        <button className={view === "workbench" ? "active" : ""} onClick={() => onView("workbench")}>{text.navWorkbench}</button>
        <button className={view === "graph" ? "active" : ""} onClick={() => onView("graph")}>{text.navGraph}</button>
      </nav>
      <div className="authbar">
        <button className="icon-button locale-button tip" data-tip={locale === "zh" ? "Switch to English" : "切换到中文"} onClick={onLocale}>
          {locale === "zh" ? "EN" : "中"}
        </button>
        {authenticated ? (
          <>
            <span className="auth-state">{text.loggedIn}</span>
            {currentUser?.role === "admin" ? (
              <button className={view === "admin" ? "icon-button active tip" : "icon-button tip"} data-tip={locale === "zh" ? "管理后台" : "Admin"} onClick={() => onView("admin")}>
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

function AuthPage({
  mode,
  locale,
  onMode,
  onDone,
}: {
  mode: AuthMode;
  locale: Locale;
  onMode: (mode: AuthMode) => void;
  onDone: () => void;
}) {
  const text = UI[locale];
  const [username, setUsername] = useState("demo");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo123456");
  const [message, setMessage] = useState<string>(text.authMessage);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setMessage(text.authMessage);
  }, [text.authMessage]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register(username, email, password);
      }
      await api.login(username, password);
      setMessage(text.authSuccess);
      onDone();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : text.authFailure);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-copy">
          <p className="eyebrow">{locale === "zh" ? "FastOJ 账号" : "FastOJ Account"}</p>
          <h1>{mode === "login" ? text.loginTitle : text.registerTitle}</h1>
          <p>{text.accountCopy}</p>
          <div className="auth-proof">
            <span>{locale === "zh" ? "Docker 沙箱" : "Docker sandbox"}</span>
            <span>{locale === "zh" ? "Redis 队列" : "Redis Streams"}</span>
            <span>{locale === "zh" ? "隐藏用例隔离" : "Hidden case isolation"}</span>
          </div>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <div className="auth-tabs" role="tablist" aria-label={locale === "zh" ? "认证方式" : "Authentication mode"}>
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => onMode("login")}>{text.login}</button>
            <button type="button" className={mode === "register" ? "active" : ""} onClick={() => onMode("register")}>{text.register}</button>
          </div>
          <label>{text.username}<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" /></label>
          {mode === "register" ? <label>{text.email}<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" /></label> : null}
          <label>{text.password}<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
          <button className="primary auth-submit" disabled={busy}>
            {busy ? text.processing : mode === "login" ? text.loginContinue : text.registerContinue}
          </button>
          <p className="muted">{message}</p>
        </form>
      </section>
    </main>
  );
}

function SettingsPage({
  locale,
  currentUser,
  theme,
  onTheme,
  onClose,
  onProfileSaved,
}: {
  locale: Locale;
  currentUser: CurrentUser | null;
  theme: AppTheme;
  onTheme: (theme: AppTheme) => void;
  onClose: () => void;
  onProfileSaved: (user: CurrentUser) => void;
}) {
  const text = UI[locale];
  const [displayName, setDisplayName] = useState(localStorage.getItem("fastoj.displayName") ?? currentUser?.username ?? "FastOJ User");
  const [username, setUsername] = useState(currentUser?.username ?? "");
  const [email, setEmail] = useState(currentUser?.email ?? "");
  const [avatarUrl, setAvatarUrl] = useState(currentUser?.avatar_url ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [compact, setCompact] = useState(localStorage.getItem("fastoj.compactMode") === "true");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    setDisplayName(localStorage.getItem("fastoj.displayName") ?? currentUser?.username ?? "FastOJ User");
    setUsername(currentUser?.username ?? "");
    setEmail(currentUser?.email ?? "");
    setAvatarUrl(currentUser?.avatar_url ?? "");
  }, [currentUser?.id, currentUser?.username, currentUser?.email, currentUser?.avatar_url]);

  async function save() {
    localStorage.setItem("fastoj.displayName", displayName);
    localStorage.setItem("fastoj.compactMode", String(compact));
    const payload: Record<string, unknown> = {
      username: username.trim(),
      email: email.trim(),
      avatar_url: avatarUrl.trim() || null,
    };
    if (newPassword) {
      payload.current_password = currentPassword;
      payload.new_password = newPassword;
    }
    try {
      const updated = await api.updateMe(payload);
      onProfileSaved(updated);
      setCurrentPassword("");
      setNewPassword("");
      setSaved(locale === "zh" ? "已保存。" : "Saved.");
    } catch (error) {
      setSaved(error instanceof Error ? error.message : locale === "zh" ? "保存失败。" : "Save failed.");
    }
  }

  return (
    <main className="settings-page">
      <section className="settings-card account-card">
        <button className="icon-button close-button tip" data-tip={locale === "zh" ? "关闭" : "Close"} onClick={onClose}>
          <IconGlyph>x</IconGlyph>
        </button>
        <p className="eyebrow">{locale === "zh" ? "账号" : "Account"}</p>
        <h1>{text.settingsTitle}</h1>
        <p className="muted">{text.settingsCopy}</p>
        <div className="account-profile">
          <div className="avatar-preview">{avatarUrl ? <img src={avatarUrl} alt="" /> : displayName.slice(0, 1).toUpperCase()}</div>
          <div>
            <strong>{displayName || username}</strong>
            <span>{currentUser?.role === "admin" ? (locale === "zh" ? "管理员" : "Admin") : (locale === "zh" ? "用户" : "User")}</span>
          </div>
        </div>
        <div className="settings-grid">
          <label>{text.displayName}<input value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></label>
          <label>{text.username}<input value={username} onChange={(event) => setUsername(event.target.value)} /></label>
          <label>{text.email}<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" /></label>
          <label>{locale === "zh" ? "头像 URL" : "Avatar URL"}<input value={avatarUrl} onChange={(event) => setAvatarUrl(event.target.value)} /></label>
          <label>{locale === "zh" ? "当前密码" : "Current password"}<input value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} type="password" autoComplete="current-password" /></label>
          <label>{locale === "zh" ? "新密码" : "New password"}<input value={newPassword} onChange={(event) => setNewPassword(event.target.value)} type="password" autoComplete="new-password" /></label>
        </div>
        <label className="toggle-row">
          <input type="checkbox" checked={compact} onChange={(event) => setCompact(event.target.checked)} />
          {text.compactMode}
        </label>
        <div className="theme-settings">
          <span>{locale === "zh" ? "界面主题" : "Theme"}</span>
          <div className="segmented theme-segmented" role="group" aria-label={locale === "zh" ? "界面主题" : "Theme"}>
            <button type="button" className={theme === "light" ? "active" : ""} aria-pressed={theme === "light"} onClick={() => onTheme("light")}>
              {locale === "zh" ? "浅色" : "Light"}
            </button>
            <button type="button" className={theme === "dark" ? "active" : ""} aria-pressed={theme === "dark"} onClick={() => onTheme("dark")}>
              {locale === "zh" ? "深色" : "Dark"}
            </button>
          </div>
        </div>
        <button className="primary" onClick={save}>{text.saveSettings}</button>
        {saved ? <p className="muted">{saved}</p> : null}
      </section>
    </main>
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
  const text = UI[locale];
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
      <button type="button" className="custom-select-button" title={locale === "zh" ? "选择难度" : "Choose difficulty"} onClick={() => setOpen((current) => !current)}>
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

function AIModelDropdown({
  value,
  locale,
  onChange,
}: {
  value: AIModelProfile;
  locale: Locale;
  onChange: (value: AIModelProfile) => void;
}) {
  const [open, setOpen] = useState(false);
  const selected = AI_MODEL_OPTIONS.find((item) => item.value === value) ?? AI_MODEL_OPTIONS[0];
  const label = locale === "zh" ? selected.zh : selected.en;
  const detail = locale === "zh" ? selected.detailZh : selected.detailEn;
  return (
    <div
      className={`custom-select ai-model-picker ${open ? "open" : ""}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button type="button" className="custom-select-button model-select-button" title={detail} onClick={() => setOpen((current) => !current)}>
        <span className="model-spark" aria-hidden="true">✦</span>
        <span className="model-copy">
          <strong>{label}</strong>
          <small>{detail}</small>
        </span>
        <span aria-hidden="true">⌄</span>
      </button>
      <div className="custom-select-menu model-select-menu" role="listbox">
        {AI_MODEL_OPTIONS.map((item) => {
          const itemLabel = locale === "zh" ? item.zh : item.en;
          const itemDetail = locale === "zh" ? item.detailZh : item.detailEn;
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
  const text = UI[locale];
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
  const needsLocalizedSearch = locale === "zh" && Array.from(trimmedKeyword).some((char) => char.charCodeAt(0) > 127);
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
            aria-label={sidebarOpen ? (locale === "zh" ? "收起筛选" : "Collapse filters") : (locale === "zh" ? "展开筛选" : "Expand filters")}
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
          aria-label={locale === "zh" ? "调整筛选栏宽度" : "Resize filters"}
          title={locale === "zh" ? "拖动调整筛选栏宽度" : "Drag to resize filters"}
          onPointerDown={(event) => sidebarOpen && startSidebarResize(event)}
        />
      </aside>
      <section className="library-main">
        <div className="library-header">
          <div>
            <p className="eyebrow">{locale === "zh" ? "题库集合" : "Problem set"}</p>
            <h1>{text.library}</h1>
            <p className="muted">{text.libraryCopy}</p>
          </div>
          <div className="recommendation">
            <span>{text.recommendation}</span>
            <strong>{localizedProblem(recommendation, locale)?.title ?? (locale === "zh" ? "暂无题目" : "No problem")}</strong>
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
        <div className={layout === "list" ? "problem-list problem-list-rows" : "problem-list"} aria-label={locale === "zh" ? "题目列表" : "Problem list"}>
          {problemsQuery.isLoading ? <p className="muted">{locale === "zh" ? "加载题库中..." : "Loading problems..."}</p> : null}
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
  const text = UI[locale];
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
  const text = UI[locale];
  const titleLayout = measureTrainingText(`${displayProblem.title} ${displayProblem.tags.join(" ")}`, 260, "13px Inter, system-ui, sans-serif", 17);
  return (
    <button
      className={active ? "problem-card active" : "problem-card"}
      title={locale === "zh" ? `打开 ${displayProblem.title}` : `Open ${displayProblem.title}`}
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
  const text = UI[locale];
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

function validationLabel(name: string, locale: Locale): string {
  const labels: Record<string, { zh: string; en: string }> = {
    title: { zh: "题目标题", en: "Title" },
    description: { zh: "题目描述", en: "Description" },
    official_solution_code: { zh: "官方解法代码", en: "Official solution code" },
    official_solution_explanation: { zh: "官方解法说明", en: "Official solution explanation" },
    time_complexity: { zh: "时间复杂度", en: "Time complexity" },
    space_complexity: { zh: "空间复杂度", en: "Space complexity" },
    function_signature: { zh: "函数签名", en: "Function signature" },
    function_testcase_inputs: { zh: "函数用例参数格式", en: "Function testcase input shape" },
    input_format: { zh: "输入格式", en: "Input format" },
    output_format: { zh: "输出格式", en: "Output format" },
    public_sample_count: { zh: "公开样例数量", en: "Public sample count" },
    hidden_testcase_count: { zh: "隐藏用例数量", en: "Hidden testcase count" },
    non_empty_outputs: { zh: "期望输出非空", en: "Non-empty expected outputs" },
    official_solution: { zh: "官方解法沙箱验证", en: "Official solution sandbox run" },
  };
  return labels[name]?.[locale] ?? name;
}

function validationStatusMessage(status: string, summary: unknown, locale: Locale): string {
  const report = recordValue(summary);
  const failedChecks = stringList(report.failed_checks);
  const caseSummary = recordValue(report.case_summary);
  const failedCases = Number(caseSummary.failed ?? 0);
  if (status === "validated" || report.passed === true) {
    return locale === "zh" ? "草稿已通过结构校验和官方解法验证。" : "Draft passed schema and official-solution validation.";
  }
  if (failedChecks.length) {
    const labels = failedChecks.slice(0, 3).map((name) => validationLabel(name, locale)).join(locale === "zh" ? "、" : ", ");
    const suffix = failedChecks.length > 3 ? (locale === "zh" ? " 等" : ", ...") : "";
    return locale === "zh" ? `校验未通过：${labels}${suffix}` : `Validation failed: ${labels}${suffix}`;
  }
  if (failedCases > 0) {
    return locale === "zh" ? `官方解法有 ${failedCases} 个用例未通过。` : `Official solution failed ${failedCases} testcase(s).`;
  }
  return locale === "zh" ? "草稿校验未通过，请查看下方安全摘要。" : "Draft validation failed. Check the safe summary below.";
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
        <span><strong>{publicCount}</strong>{locale === "zh" ? "公开样例" : "public samples"}</span>
        <span><strong>{hiddenCount}</strong>{locale === "zh" ? "隐藏用例" : "hidden cases"}</span>
        <span><strong>{failedCases}</strong>{locale === "zh" ? "失败用例" : "failed cases"}</span>
      </div>
      {failedChecks.length ? (
        <div className="validation-failures">
          <strong>{locale === "zh" ? "失败检查" : "Failed checks"}</strong>
          <ul>
            {failedChecks.map((name) => <li key={name}>{validationLabel(name, locale)}</li>)}
          </ul>
        </div>
      ) : null}
      {failedStatuses.length ? (
        <p className="muted">{locale === "zh" ? "沙箱状态" : "Sandbox statuses"}: {failedStatuses.join(", ")}</p>
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

function Workspace({
  problemId,
  locale,
  theme,
  onBackToLibrary,
  onRequireAuth,
  authenticated,
}: {
  problemId: string | null;
  locale: Locale;
  theme: AppTheme;
  onBackToLibrary: () => void;
  onRequireAuth: () => void;
  authenticated: boolean;
}) {
  const text = UI[locale];
  const { language, setLanguage, getDraft, setDraft, setRecentProblemId, getCachedExplain, setCachedExplain } = useAppStore();
  const [code, setCode] = useState("");
  const [judgeMode, setJudgeMode] = useState<JudgeMode>("acm");
  const [aiModel, setAiModel] = useState<AIModelProfile>(() => (localStorage.getItem("fastoj.aiModel") as AIModelProfile | null) ?? "default");
  const [leftOpen, setLeftOpen] = useState(() => localStorage.getItem("fastoj.leftOpen") !== "false");
  const [rightOpen, setRightOpen] = useState(() => localStorage.getItem("fastoj.rightOpen") !== "false");
  const [leftWidth, setLeftWidth] = useState(() => Number(localStorage.getItem("fastoj.leftWidth") ?? 390));
  const [rightWidth, setRightWidth] = useState(() => Number(localStorage.getItem("fastoj.rightWidth") ?? 430));
  const [resizing, setResizing] = useState<"left" | "right" | null>(null);
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [events, setEvents] = useState<JudgeEvent[]>([]);
  const [explain, setExplain] = useState<AIExplain | null>(null);
  const [review, setReview] = useState<AIReview | null>(null);
  const [hint, setHint] = useState<AIHint | null>(null);
  const [chatLines, setChatLines] = useState<AIChatLine[]>([]);
  const [aiError, setAiError] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("cases");
  const activeProblemIdRef = useRef<string | null>(problemId);
  const activeSubmissionIdRef = useRef<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const problemQuery = useQuery({ queryKey: ["problem", problemId], queryFn: () => api.problem(problemId ?? ""), enabled: Boolean(problemId) });
  const trailQuery = useQuery({ queryKey: ["submissions", problemId, submission?.id], queryFn: () => api.submissions(problemId ?? ""), enabled: Boolean(problemId && authenticated) });
  const solutionsQuery = useQuery({ queryKey: ["solutions", problemId, language, locale], queryFn: () => api.solutions(problemId ?? "", language, locale), enabled: Boolean(problemId) });

  const problem = problemQuery.data;
  const displayProblem = localizedProblem(problem, locale);
  const modeInfo = getProblemMode(problem);
  const draftKey = `${language}.${judgeMode}`;
  const functionBlocked = false;

  useEffect(() => { localStorage.setItem("fastoj.leftOpen", String(leftOpen)); }, [leftOpen]);
  useEffect(() => { localStorage.setItem("fastoj.rightOpen", String(rightOpen)); }, [rightOpen]);
  useEffect(() => { localStorage.setItem("fastoj.leftWidth", String(leftWidth)); }, [leftWidth]);
  useEffect(() => { localStorage.setItem("fastoj.rightWidth", String(rightWidth)); }, [rightWidth]);
  useEffect(() => { localStorage.setItem("fastoj.aiModel", aiModel); }, [aiModel]);
  useEffect(() => { if (problemId) setRecentProblemId(problemId); }, [problemId, setRecentProblemId]);

  function editorCodeFor(targetLanguage: string, targetMode: JudgeMode): string {
    if (!problemId || !problem) return "";
    const starter = buildStarter(problem, targetLanguage, targetMode, locale);
    const draft = getDraft(problemId, `${targetLanguage}.${targetMode}`);
    if (targetMode === "function" && targetLanguage !== "python" && draft.trim()) {
      if (/^\s*(import\s+\w+\s*\n\s*)*def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(/.test(draft)) return starter;
      const stalePythonStarters = [
        buildStarter(problem, "python", "function", "en").trim(),
        buildStarter(problem, "python", "function", "zh").trim(),
      ];
      if (stalePythonStarters.includes(draft.trim())) return starter;
    }
    return draft || starter;
  }

  useEffect(() => {
    activeProblemIdRef.current = problemId;
    activeSubmissionIdRef.current = null;
    stopStatusStream();
    setSubmission(null);
    setEvents([]);
    clearCopilotState();
    setDetailTab("cases");
  }, [problemId]);

  useEffect(() => () => stopStatusStream(), []);

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
    if (!modeInfo.supportsFunction) return;
    setJudgeMode(judgeMode === "function" ? "acm" : "function");
  }

  function startResize(side: "left" | "right", event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = side === "left" ? leftWidth : rightWidth;
    setResizing(side);
    const onMove = (moveEvent: PointerEvent) => {
      const delta = side === "left" ? moveEvent.clientX - startX : startX - moveEvent.clientX;
      const next = clamp(startWidth + delta, side === "left" ? 260 : 320, side === "left" ? 680 : 700);
      if (side === "left") setLeftWidth(next);
      else setRightWidth(next);
    };
    const onUp = () => {
      setResizing(null);
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
    if (!problemId || functionBlocked) return;
    if (!authenticated || !localStorage.getItem("fastoj.jwt")) {
      onRequireAuth();
      return;
    }
    const requestProblemId = problemId;
    stopStatusStream();
    activeSubmissionIdRef.current = null;
    clearCopilotState();
    setSubmission(null);
    setDetailTab("judge");
    setLeftOpen(true);
    setRightOpen(true);
    setEvents([{ type: "pending", status: "pending", progress: 0 }]);
    try {
      const created = await api.submit(problemId, language, code, runOnly, judgeMode);
      if (activeProblemIdRef.current !== requestProblemId) return;
      activeSubmissionIdRef.current = created.id;
      setSubmission(created as SubmissionDetail);
      connectStatus(created.id);
    } catch (error) {
      if (activeProblemIdRef.current !== requestProblemId) return;
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
    if (!submission) {
      setAiError(locale === "zh" ? "请先运行或提交一次代码，再开始对话。" : "Run or submit once before starting a chat.");
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
                onRequireAuth={onRequireAuth}
              />
              <ProblemGuidance problem={problem} locale={locale} />
            </>
          ) : null}
        </aside>
        <div className="panel-edge left-edge">
          <button className="edge-toggle" title={leftOpen ? text.collapseLeft : text.expandLeft} onClick={() => setLeftOpen((value) => !value)}>
            <PanelToggleIcon open={leftOpen} side="left" />
          </button>
          <div className="resize-handle" role="separator" aria-label={locale === "zh" ? "调整题面面板宽度" : "Resize statement panel"} title={locale === "zh" ? "拖动调整题面宽度" : "Drag to resize statement"} onPointerDown={(event) => leftOpen && startResize("left", event)} />
        </div>

        <section className="coding-panel feature-frame code-frame">
          <div className="editor-toolbar">
            <button className={`mode-toggle ${judgeMode === "function" ? "active function-mode" : "active acm-mode"}`} title={!modeInfo.supportsFunction ? text.modeAcmOnlyTitle : judgeMode === "function" ? text.modeFunctionTitle : text.modeAcmTitle} disabled={!modeInfo.supportsFunction} onClick={toggleJudgeMode}>
              <span className="mode-dot" />
              {judgeMode === "function" ? text.functionMode : text.acmMode}
            </button>
            <select title={text.pickLanguage} value={language} onChange={(event) => setLanguage(event.target.value)}>
              {LANGUAGES.map((item) => <option key={item}>{item}</option>)}
            </select>
            <AIModelDropdown value={aiModel} locale={locale} onChange={setAiModel} />
            <button className="icon-button tip" data-tip={text.resetTemplate} onClick={() => setCode(buildStarter(problem, language, judgeMode, locale))}><IconGlyph>R</IconGlyph></button>
            <button className="icon-button run-action tip" data-tip={text.runTitle} onClick={() => judge(true)} disabled={functionBlocked}><IconGlyph>▶</IconGlyph></button>
            <button className="icon-button primary submit-action tip" data-tip={text.submitTitle} onClick={() => judge(false)} disabled={functionBlocked}><IconGlyph>↑</IconGlyph></button>
          </div>
          <FunctionFrame problem={problem} mode={judgeMode} language={language} blocked={functionBlocked} locale={locale} />
          <CodeEditor language={language} value={code} onChange={updateCode} theme={theme} />
        </section>

        <div className="panel-edge right-edge">
          <div className="resize-handle" role="separator" aria-label={locale === "zh" ? "调整 AI 辅助面板宽度" : "Resize AI panel"} title={locale === "zh" ? "拖动调整 AI 辅助宽度" : "Drag to resize AI panel"} onPointerDown={(event) => rightOpen && startResize("right", event)} />
          <button className="edge-toggle" title={rightOpen ? text.collapseRight : text.expandRight} onClick={() => setRightOpen((value) => !value)}>
            <PanelToggleIcon open={rightOpen} side="right" />
          </button>
        </div>

        <aside className="result-sidebar feature-frame result-frame">
          {rightOpen ? (
            <div className="ai-region">
              <AICopilotPanel submission={submission} explain={explain} review={review} hint={hint} chatLines={chatLines} error={aiError} onExplain={explainSubmission} onReview={reviewSubmission} onHint={requestHint} onChat={sendChat} locale={locale} />
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
  onRequireAuth: () => void;
}) {
  const text = UI[locale];
  return (
    <section className="detail-dock statement-detail-dock judge-region">
      <div className="tabs" role="tablist" aria-label={locale === "zh" ? "题目详情" : "Problem details"}>
        <TabButton tab="cases" active={detailTab} onClick={setDetailTab}>{text.publicCases}</TabButton>
        <TabButton tab="solution" active={detailTab} onClick={setDetailTab}>{text.solution}</TabButton>
        <TabButton tab="judge" active={detailTab} onClick={setDetailTab}>{text.judge}</TabButton>
        <TabButton tab="trail" active={detailTab} onClick={setDetailTab}>{text.trail}</TabButton>
        <TabButton tab="discussion" active={detailTab} onClick={setDetailTab}>{text.discussion}</TabButton>
      </div>
      <div className="detail-panel">
        {detailTab === "cases" ? <SampleCases problem={problem} locale={locale} /> : null}
        {detailTab === "solution" ? <OfficialSolution problem={problem} solution={solution} locale={locale} /> : null}
        {detailTab === "judge" ? <JudgeTimeline events={events} submission={submission} theme={theme} /> : null}
        {detailTab === "trail" ? <SubmissionTrail submissions={trail} locale={locale} /> : null}
        {detailTab === "discussion" ? <DiscussionPanel problemId={problemId} locale={locale} authenticated={authenticated} onRequireAuth={onRequireAuth} /> : null}
      </div>
    </section>
  );
}

function ProblemStatement({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = UI[locale];
  const displayProblem = localizedProblem(problem, locale);
  if (!displayProblem) return <p className="muted">{text.loadingProblem}</p>;
  return (
    <article className="prose-panel">
      <p>{displayProblem.description}</p>
      <p className="muted">{text.acceptance} {percent(displayProblem.ac_rate)}%, {text.submissions} {displayProblem.total_submissions}</p>
    </article>
  );
}

function ProblemGuidance({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = UI[locale];
  const displayProblem = localizedProblem(problem, locale);
  return (
    <section className="problem-guidance">
      <ProblemVisual problem={problem} locale={locale} />
      <article className="prose-panel hint-panel">
        <h3>{text.officialHint}</h3>
        <p>{displayProblem?.hint ?? text.noHint}</p>
      </article>
    </section>
  );
}

function ProblemVisual({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const visual = getVisualSpec(problem);
  return (
    <section className="visual-panel" aria-label={locale === "zh" ? "图形化讲解" : "Visual explanation"}>
      <h3>{visual.title[locale]}</h3>
      <div className="visual-flow">
        {visual.steps[locale].map((step, index) => (
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

function FunctionFrame({ problem, mode, language, blocked, locale }: { problem?: ProblemDetail; mode: JudgeMode; language: string; blocked: boolean; locale: Locale }) {
  const text = UI[locale];
  if (mode !== "function") return <div className="function-frame">{text.acmFrame}</div>;
  const spec = getFunctionSpec(problem);
  if (!spec) return <div className="function-frame warning">{text.noFunctionFrame}</div>;
  const starter = buildStarter(problem, language, "function", locale);
  const signature = language === "python"
    ? spec.signature
    : functionSignaturePreview(starter, language, spec.signature);
  return (
    <div className={blocked ? "function-frame warning" : "function-frame"}>
      <strong>{signature}</strong>
      <span>{blocked ? text.functionPythonOnly : getLocalizedFunctionDescription(problem, locale)}</span>
    </div>
  );
}

function SampleCases({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = UI[locale];
  if (!problem) return <p className="muted">{text.loadingCases}</p>;
  return (
    <div className="case-grid">
      {problem.sample_testcases.map((testcase, index) => (
        <article className="sample-card" key={`${testcase.input}-${index}`}>
          <h3>{locale === "zh" ? "示例" : "Example"} {index + 1}</h3>
          <div className="sample-row">
            <span>{text.input}</span>
            <pre>{testcase.input}</pre>
          </div>
          <div className="sample-row">
            <span>{text.output}</span>
            <pre>{testcase.output}</pre>
          </div>
          <div className="sample-row">
            <span>{text.explanation}</span>
            <p>{sampleExplanation(problem.slug, index, locale)}</p>
          </div>
        </article>
      ))}
    </div>
  );
}

function sampleExplanation(slug: string, index: number, locale: Locale): string {
  const zh: Record<string, string[]> = {
    "two-sum": ["nums[0] + nums[1] = 9，所以返回这两个下标。", "nums[1] + nums[2] = 6，所以返回 [1,2]。"],
    "softmax-cross-entropy": ["先对 logits 做稳定 softmax，再取目标类别概率的负对数。", "两个类别得分相同，目标类别概率为 1/2，损失为 ln 2。"],
    "valid-parentheses": ["每个左括号都能按正确顺序被匹配并弹出栈。", "右括号类型与栈顶左括号不同，因此不是有效括号串。"],
  };
  const en: Record<string, string[]> = {
    "two-sum": ["nums[0] + nums[1] equals 9, so those indices are returned.", "nums[1] + nums[2] equals 6, so [1,2] is returned."],
    "softmax-cross-entropy": ["Apply stable softmax to logits, then take the negative log probability of the target class.", "Both logits are equal, so the target probability is 1/2 and the loss is ln 2."],
    "valid-parentheses": ["Every opening bracket is matched and popped in the correct order.", "The closing bracket type does not match the stack top, so the string is invalid."],
  };
  const fallback = locale === "zh" ? "该输出是此输入下的标准答案；评测会按相同输入/输出格式比较。" : "The output is the canonical expected answer for this input; judging compares the same I/O format.";
  return (locale === "zh" ? zh : en)[slug]?.[index] ?? fallback;
}

function OfficialSolution({ problem, solution, locale }: { problem?: ProblemDetail; solution?: { explanation: string; code: string; language: string }; locale: Locale }) {
  if (!solution) {
    const displayProblem = localizedProblem(problem, locale);
    const tags = localizeTags(displayProblem?.tags.filter((tag) => tag !== "Hot 100"), locale).join(" / ");
    return (
      <article className="prose-panel solution-fallback">
        <h3>{locale === "zh" ? "题解思路" : "Solution approach"}</h3>
        <p>{displayProblem?.hint ?? UI[locale].noSolution}</p>
        <p className="muted">
          {locale === "zh"
            ? `建议先根据 ${tags || "题目标签"} 选择核心数据结构或状态定义，再用公开样例逐步核对边界。`
            : `Start from ${tags || "the listed tags"}, choose the core data structure or state definition, then validate edge cases with the public samples.`}
        </p>
      </article>
    );
  }
  return (
    <article className="prose-panel">
      <p>{solution.explanation}</p>
      {solution.code.trim() ? <CodeBlock code={solution.code} language={solution.language} /> : null}
    </article>
  );
}

function DiscussionPanel({ problemId, locale, authenticated, onRequireAuth }: { problemId: string; locale: Locale; authenticated: boolean; onRequireAuth: () => void }) {
  const text = UI[locale];
  const key = `fastoj.discussion.${problemId}`;
  const [body, setBody] = useState("");
  const [posts, setPosts] = useState<DiscussionPost[]>(() => JSON.parse(localStorage.getItem(key) ?? "[]"));

  function post() {
    if (!authenticated) {
      onRequireAuth();
      return;
    }
    const trimmed = body.trim();
    if (!trimmed) return;
    const next = [
      { id: crypto.randomUUID(), author: localStorage.getItem("fastoj.displayName") ?? "FastOJ User", body: trimmed, createdAt: new Date().toISOString() },
      ...posts,
    ];
    setPosts(next);
    localStorage.setItem(key, JSON.stringify(next));
    setBody("");
  }

  return (
    <section className="discussion-panel">
      <h3>{text.discussionTitle}</h3>
      <textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder={text.discussionPlaceholder} />
      <button className="primary" onClick={post}>{text.postDiscussion}</button>
      {posts.length ? posts.map((item) => (
        <article className="discussion-post" key={item.id}>
          <strong>{item.author}</strong>
          <small>{new Date(item.createdAt).toLocaleString()}</small>
          <p>{item.body}</p>
        </article>
      )) : <p className="muted">{text.noDiscussion}</p>}
    </section>
  );
}

function AdminPage({ locale, currentUser, onBack }: { locale: Locale; currentUser: CurrentUser | null; onBack: () => void }) {
  const text = locale === "zh"
    ? {
      title: "管理后台",
      copy: "管理题目、官方题解、测试用例和用户权限。隐藏用例只显示数量，不在页面暴露内容。",
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
      saveSolution: "保存 Python 题解",
      problemAgent: "出题 Agent",
      agentNotice: "AI 生成内容只保存为草稿，管理员审批前不会发布。",
      generateDraft: "生成草稿",
      approveDraft: "批准发布",
      rejectDraft: "拒绝草稿",
      draftPreview: "草稿预览",
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
      previous: "上一页",
      next: "下一页",
      noResults: "没有匹配结果。",
      pageSummary: "第 {page} / {totalPages} 页，共 {total} 条",
      titleLabel: "标题",
      descriptionLabel: "描述",
      hintLabel: "提示",
      tagsLabel: "标签（逗号分隔）",
    }
    : {
      title: "Admin",
      copy: "Manage problems, official solutions, test cases, and user permissions. Hidden cases are shown as counts only.",
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
      saveSolution: "Save Python solution",
      problemAgent: "Problem Agent",
      agentNotice: "AI-generated content is saved as a draft and is never published before admin approval.",
      generateDraft: "Generate draft",
      approveDraft: "Approve",
      rejectDraft: "Reject",
      draftPreview: "Draft preview",
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
      previous: "Previous",
      next: "Next",
      noResults: "No matching results.",
      pageSummary: "Page {page} / {totalPages}, {total} total",
      titleLabel: "Title",
      descriptionLabel: "Description",
      hintLabel: "Hint",
      tagsLabel: "Tags, comma separated",
    };
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
  const [problemEdit, setProblemEdit] = useState({ title: "", description: "", tags: "", hint: "" });
  const [agentTopic, setAgentTopic] = useState("array two pointers");
  const [agentTags, setAgentTags] = useState("array,two-pointers");
  const [agentDifficulty, setAgentDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [agentMode, setAgentMode] = useState<"function" | "acm">("function");
  const [agentModel, setAgentModel] = useState<AIModelProfile>("default");
  const [agentConstraints, setAgentConstraints] = useState("");
  const [agentMessage, setAgentMessage] = useState("");
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [selectedDraft, setSelectedDraft] = useState<ProblemDraft | null>(null);
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
    enabled: currentUser?.role === "admin",
  });
  const draftsQuery = useQuery({
    queryKey: ["admin-problem-drafts", currentUser?.id],
    queryFn: () => api.adminProblemDrafts({ pageSize: 8 }),
    enabled: currentUser?.role === "admin",
  });

  if (currentUser?.role !== "admin") {
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

  async function savePythonSolution(problemId: string) {
    await api.adminUpsertSolution(problemId, {
      language: "python",
      explanation: locale === "zh" ? "请在数据库或后续编辑器中补充完整官方题解。" : "Fill in the full official explanation in the database or the next editor pass.",
      code: "# TODO: add official solution\n",
      time_complexity: null,
      space_complexity: null,
    });
    await overviewQuery.refetch();
  }

  async function createAgentDraft() {
    setAgentMessage(locale === "zh" ? "正在生成并验证草稿..." : "Generating and validating draft...");
    try {
      const result = await api.adminCreateProblemDraft({
        topic: agentTopic,
        difficulty: agentDifficulty,
        tags: agentTags.split(",").map((tag) => tag.trim()).filter(Boolean),
        mode: agentMode,
        target_language: "python",
        locale,
        model_profile: agentModel,
        constraints: agentConstraints.trim() || null,
      });
      const run = await api.adminAgentRun(result.run_id);
      const draft = await api.adminProblemDraft(result.draft_id);
      setAgentSteps(run.steps ?? []);
      setSelectedDraft(draft);
      setAgentMessage(validationStatusMessage(result.status, result.validation_summary, locale));
      await draftsQuery.refetch();
    } catch (error) {
      setAgentMessage(error instanceof Error ? error.message : locale === "zh" ? "生成失败。" : "Generation failed.");
    }
  }

  async function loadDraft(draftId: string) {
    const draft = await api.adminProblemDraft(draftId);
    setSelectedDraft(draft);
  }

  async function approveSelectedDraft() {
    if (!selectedDraft) return;
    const draft = await api.adminApproveProblemDraft(selectedDraft.id);
    setSelectedDraft(draft);
    await overviewQuery.refetch();
    await draftsQuery.refetch();
  }

  async function rejectSelectedDraft() {
    if (!selectedDraft) return;
    const draft = await api.adminRejectProblemDraft(selectedDraft.id);
    setSelectedDraft(draft);
    await draftsQuery.refetch();
  }

  const users = overviewQuery.data?.users ?? [];
  const problems = overviewQuery.data?.problems ?? [];
  const userPagination = overviewQuery.data?.pagination?.users ?? { page: userPage, page_size: 8, total: 0, total_pages: 0 };
  const problemPagination = overviewQuery.data?.pagination?.problems ?? { page: problemPage, page_size: 8, total: 0, total_pages: 0 };
  const drafts = draftsQuery.data ?? [];
  const selectedUser = users.find((user: any) => user.id === selectedUserId) ?? null;
  const selectedProblem = problems.find((problem: any) => problem.id === selectedProblemId) ?? null;

  function pageSummary(pagination: any) {
    const totalPages = Math.max(Number(pagination.total_pages ?? 0), 1);
    return text.pageSummary
      .replace("{page}", String(pagination.page ?? 1))
      .replace("{totalPages}", String(totalPages))
      .replace("{total}", String(pagination.total ?? 0));
  }

  function chooseProblem(problem: any) {
    setSelectedProblemId(problem.id);
    setProblemEdit({
      title: problem.title ?? "",
      description: problem.description ?? "",
      tags: (problem.tags ?? []).join(", "),
      hint: problem.hint ?? "",
    });
  }

  async function saveProblemEdit() {
    if (!selectedProblemId) return;
    await updateProblem(selectedProblemId, {
      title: problemEdit.title,
      description: problemEdit.description,
      tags: problemEdit.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
      hint: problemEdit.hint,
    });
  }

  return (
    <main className="admin-page">
      <section className="admin-shell">
        <button className="icon-button close-button tip" data-tip={text.back} onClick={onBack}><IconGlyph>x</IconGlyph></button>
        <p className="eyebrow">{text.title}</p>
        <h1>{text.title}</h1>
        <p className="muted">{text.copy}</p>
        <section className="admin-panel problem-agent-panel">
          <div>
            <h2>{text.problemAgent}</h2>
            <p className="muted">{text.agentNotice}</p>
          </div>
          <div className="agent-form">
            <label>{locale === "zh" ? "主题" : "Topic"}<input value={agentTopic} onChange={(event) => setAgentTopic(event.target.value)} /></label>
            <label>{locale === "zh" ? "难度" : "Difficulty"}
              <select value={agentDifficulty} onChange={(event) => setAgentDifficulty(event.target.value as "easy" | "medium" | "hard")}>
                <option value="easy">easy</option>
                <option value="medium">medium</option>
                <option value="hard">hard</option>
              </select>
            </label>
            <label>{locale === "zh" ? "标签" : "Tags"}<input value={agentTags} onChange={(event) => setAgentTags(event.target.value)} /></label>
            <label>{locale === "zh" ? "模式" : "Mode"}
              <select value={agentMode} onChange={(event) => setAgentMode(event.target.value as "function" | "acm")}>
                <option value="function">function</option>
                <option value="acm">acm</option>
              </select>
            </label>
            <label>{locale === "zh" ? "模型" : "Model"}
              <select value={agentModel} onChange={(event) => setAgentModel(event.target.value as AIModelProfile)}>
                <option value="default">default</option>
                <option value="deepseek">deepseek</option>
                <option value="qwen-local">qwen-local</option>
              </select>
            </label>
            <label>{locale === "zh" ? "额外约束" : "Constraints"}<input value={agentConstraints} onChange={(event) => setAgentConstraints(event.target.value)} /></label>
            <button className="primary" onClick={createAgentDraft}>{text.generateDraft}</button>
          </div>
          {agentMessage ? <p className="muted">{agentMessage}</p> : null}
          <div className="agent-workspace">
            <div className="agent-drafts">
              {drafts.map((draft) => (
                <button key={draft.id} className={selectedDraft?.id === draft.id ? "active" : ""} onClick={() => loadDraft(draft.id)}>
                  <strong>{draft.title}</strong>
                  <span>{draft.status} / {draft.mode}</span>
                </button>
              ))}
            </div>
            <div className="agent-preview">
              <h3>{text.steps}</h3>
              {agentSteps.length ? agentSteps.map((step) => (
                <article className="agent-step" key={step.id}>
                  <strong>{step.step_index}. {step.step_type}</strong>
                  <span>{step.status}{step.error_message ? `: ${step.error_message}` : ""}</span>
                </article>
              )) : <p className="muted">{locale === "zh" ? "选择或生成草稿后显示执行轨迹。" : "Generate a draft to see the run timeline."}</p>}
            </div>
            <div className="agent-preview">
              <h3>{text.draftPreview}</h3>
              {selectedDraft ? (
                <>
                  <strong>{selectedDraft.title}</strong>
                  <span>{selectedDraft.slug} / {selectedDraft.status}</span>
                  <p>{selectedDraft.description}</p>
                  <h3>{text.validation}</h3>
                  <ValidationReport draft={selectedDraft} locale={locale} />
                  <div className="agent-actions">
                    <button className="primary" disabled={selectedDraft.status !== "validated"} onClick={approveSelectedDraft}>{text.approveDraft}</button>
                    <button disabled={selectedDraft.status === "approved" || selectedDraft.status === "rejected"} onClick={rejectSelectedDraft}>{text.rejectDraft}</button>
                  </div>
                </>
              ) : <p className="muted">{locale === "zh" ? "还没有选中的草稿。" : "No draft selected."}</p>}
            </div>
          </div>
        </section>
        <div className="admin-grid">
          <section className="admin-panel">
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
                <option value="user">{text.user}</option>
                <option value="admin">{text.admin}</option>
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
                <select value={user.role} onChange={(event) => updateUser(user.id, { role: event.target.value })}>
                  <option value="user">{text.user}</option>
                  <option value="admin">{text.admin}</option>
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
                  <label>{locale === "zh" ? "角色" : "Role"}
                    <select value={selectedUser.role} onChange={(event) => updateUser(selectedUser.id, { role: event.target.value })}>
                      <option value="user">{text.user}</option>
                      <option value="admin">{text.admin}</option>
                    </select>
                  </label>
                  <button onClick={() => updateUser(selectedUser.id, { is_active: !selectedUser.is_active })}>
                    {selectedUser.is_active ? text.disabled : text.active}
                  </button>
                </div>
              </div>
            ) : null}
          </section>
          <section className="admin-panel">
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
                <button onClick={() => savePythonSolution(problem.id)} disabled={problem.solution_count > 0}>
                  {problem.solution_count} {text.solutions}
                </button>
                <button onClick={() => selectedProblemId === problem.id ? setSelectedProblemId(null) : chooseProblem(problem)}>{text.edit}</button>
              </article>
            )) : <p className="muted">{text.noResults}</p>}
            <div className="admin-pagination">
              <button disabled={problemPage <= 1} onClick={() => setProblemPage((page) => Math.max(1, page - 1))}>{text.previous}</button>
              <button disabled={problemPage >= Math.max(Number(problemPagination.total_pages ?? 0), 1)} onClick={() => setProblemPage((page) => page + 1)}>{text.next}</button>
            </div>
            {selectedProblem ? (
              <div className="admin-edit-panel problem-edit-panel">
                <h3>{selectedProblem.title}</h3>
                <span className="muted">{selectedProblem.slug} · {selectedProblem.mode} · {selectedProblem.testcase_count} {text.cases} · {selectedProblem.hidden_testcase_count} {text.hidden}</span>
                <div className="admin-edit-grid">
                  <label>{text.titleLabel}<input value={problemEdit.title} onChange={(event) => setProblemEdit((value) => ({ ...value, title: event.target.value }))} /></label>
                  <label>{text.tagsLabel}<input value={problemEdit.tags} onChange={(event) => setProblemEdit((value) => ({ ...value, tags: event.target.value }))} /></label>
                  <label>{text.descriptionLabel}<textarea value={problemEdit.description} onChange={(event) => setProblemEdit((value) => ({ ...value, description: event.target.value }))} /></label>
                  <label>{text.hintLabel}<textarea value={problemEdit.hint} onChange={(event) => setProblemEdit((value) => ({ ...value, hint: event.target.value }))} /></label>
                </div>
                <div className="agent-actions">
                  <button className="primary" onClick={saveProblemEdit}>{text.save}</button>
                  <button onClick={() => updateProblem(selectedProblem.id, { is_public: !selectedProblem.is_public })}>
                    {selectedProblem.is_public ? text.private : text.public}
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </main>
  );
}

function App() {
  const recentProblemId = useAppStore((state) => state.recentProblemId);
  const [selectedId, setSelectedId] = useState<string | null>(recentProblemId);
  const [view, setView] = useState<View>(recentProblemId ? "workbench" : "library");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem("fastoj.locale") === "en" ? "en" : "zh"));
  const [theme, setTheme] = useState<AppTheme>(() => (localStorage.getItem("fastoj.theme") === "light" ? "light" : "dark"));
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem("fastoj.jwt")));
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [graphTag, setGraphTag] = useState("");
  const problemsQuery = useQuery({ queryKey: ["problems", "graph"], queryFn: () => api.problems({}) });
  const problems = useMemo(() => problemsQuery.data ?? [], [problemsQuery.data]);

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
    api.me()
      .then(setCurrentUser)
      .catch((error) => {
        if (isUnauthorized(error)) {
          localStorage.removeItem("fastoj.jwt");
          setAuthenticated(false);
          setView("auth");
        }
      });
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
    setLocale((current) => {
      const next = current === "zh" ? "en" : "zh";
      localStorage.setItem("fastoj.locale", next);
      return next;
    });
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
      {view === "auth" ? <AuthPage mode={authMode} locale={locale} onMode={setAuthMode} onDone={() => { setAuthenticated(true); setView("library"); }} /> : null}
      {view === "settings" ? <SettingsPage locale={locale} currentUser={currentUser} theme={theme} onTheme={setTheme} onClose={() => setView("library")} onProfileSaved={setCurrentUser} /> : null}
      {view === "admin" ? <AdminPage locale={locale} currentUser={currentUser} onBack={() => setView("library")} /> : null}
      {view === "library" ? <LibraryPage selectedId={selectedId} selectedTag={graphTag} locale={locale} onSelect={openProblem} onGraph={() => setView("graph")} /> : null}
      {view === "workbench" ? (
        <Workspace
          problemId={selectedId}
          locale={locale}
          theme={theme}
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
        <TrainingGraph
          problems={problems}
          locale={locale}
          onTag={(tag) => {
            setGraphTag(tag);
            setView("library");
          }}
        />
      ) : null}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
