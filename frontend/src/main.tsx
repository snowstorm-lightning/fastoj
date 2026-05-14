import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";

import "./styles.css";
import { api, isUnauthorized, makeJudgeSocket, type ProblemFilters } from "./lib/api";
import {
  type AIExplain,
  type AIHint,
  type AIReview,
  type ProblemDetail,
  type ProblemListItem,
  type SubmissionDetail,
} from "./lib/schemas";
import {
  buildStarter,
  getFunctionSpec,
  getProblemMode,
  getVisualSpec,
  type JudgeMode,
} from "./lib/problemModes";
import { localizedProblem, type Locale, UI, verdictInfo } from "./lib/i18n";
import { measureTrainingText } from "./lib/textLayout";
import { LANGUAGES, useAppStore } from "./stores/useAppStore";
import { AICopilotPanel } from "./components/AICopilotPanel";
import { CodeBlock } from "./components/CodeBlock";
import { CodeEditor } from "./components/CodeEditor";
import { JudgeTimeline, type JudgeEvent } from "./components/JudgeTimeline";
import { SubmissionTrail } from "./components/SubmissionTrail";
import { TrainingGraph } from "./components/TrainingGraph";

const queryClient = new QueryClient();

type View = "library" | "workbench" | "graph" | "auth";
type DetailTab = "cases" | "solution" | "judge" | "trail";
type AuthMode = "login" | "register";

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const MenuIcon = () => (
  <span className="menu-icon" aria-hidden="true">
    <span />
    <span />
    <span />
  </span>
);

function AuthBar({
  view,
  authenticated,
  locale,
  onView,
  onAuth,
  onLogout,
  onLocale,
}: {
  view: View;
  authenticated: boolean;
  locale: Locale;
  onView: (view: View) => void;
  onAuth: (mode: AuthMode) => void;
  onLogout: () => void;
  onLocale: () => void;
}) {
  const text = UI[locale];
  return (
    <header className="topbar">
      <button className="brand-lockup brand-button" title={locale === "zh" ? "返回题库首页" : "Back to problem library"} onClick={() => onView("library")}>
        <strong>FastOJ</strong>
        <span>AI interview judge</span>
      </button>
      <nav className="topnav" aria-label={locale === "zh" ? "主导航" : "Main navigation"}>
        <button className={view === "library" ? "active" : ""} onClick={() => onView("library")}>{text.navLibrary}</button>
        <button className={view === "workbench" ? "active" : ""} onClick={() => onView("workbench")}>{text.navWorkbench}</button>
        <button className={view === "graph" ? "active" : ""} onClick={() => onView("graph")}>{text.navGraph}</button>
      </nav>
      <div className="authbar">
        <button className="locale-button" title={locale === "zh" ? "Switch to English" : "切换到中文"} onClick={onLocale}>
          {locale === "zh" ? "EN" : "中"}
        </button>
        {authenticated ? (
          <>
            <span className="auth-state">{text.loggedIn}</span>
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
  }, [locale]);

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
          <p className="eyebrow">FastOJ Account</p>
          <h1>{mode === "login" ? text.loginTitle : text.registerTitle}</h1>
          <p>{text.accountCopy}</p>
          <div className="auth-proof">
            <span>Docker 沙箱</span>
            <span>Redis Streams</span>
            <span>隐藏用例隔离</span>
          </div>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <div className="auth-tabs" role="tablist" aria-label={locale === "zh" ? "认证方式" : "Authentication mode"}>
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => onMode("login")}>{text.login}</button>
            <button type="button" className={mode === "register" ? "active" : ""} onClick={() => onMode("register")}>{text.register}</button>
          </div>
          <label>
            {text.username}
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          {mode === "register" ? (
            <label>
              {text.email}
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" />
            </label>
          ) : null}
          <label>
            {text.password}
            <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} />
          </label>
          <button className="primary auth-submit" disabled={busy}>
            {busy ? text.processing : mode === "login" ? text.loginContinue : text.registerContinue}
          </button>
          <p className="muted">{message}</p>
        </form>
      </section>
    </main>
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

  useEffect(() => {
    setTags(selectedTag);
    setPage(1);
  }, [selectedTag]);

  const filters: ProblemFilters = { keyword, difficulty, tags, page };
  const problemsQuery = useQuery({ queryKey: ["problems", filters], queryFn: () => api.problems(filters) });
  const problems = problemsQuery.data ?? [];
  const aiCount = problems.filter((problem) => getProblemMode(problem).isAiPractice).length;
  const functionCount = problems.filter((problem) => getProblemMode(problem).supportsFunction).length;
  const averageAc = problems.length
    ? Math.round((problems.reduce((sum, problem) => sum + problem.ac_rate, 0) / problems.length) * 100)
    : 0;
  const recommendation = problems.find((problem) => problem.ac_rate < 0.45) ?? problems[0];

  function resetFilters() {
    setKeyword("");
    setDifficulty("");
    setTags("");
    setPage(1);
  }

  return (
    <main className="library-page">
      <aside className="library-sidebar">
        <div className="filter-group">
          <strong>{text.filters}</strong>
          <input placeholder={text.keyword} value={keyword} onChange={(event) => setKeyword(event.target.value)} />
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
            <option value="">{text.allDifficulty}</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <input placeholder={text.tagsPlaceholder} value={tags} onChange={(event) => { setTags(event.target.value); setPage(1); }} />
          <button title={text.resetFilters} onClick={resetFilters}>{text.resetFilters}</button>
        </div>
        <div className="side-metrics">
          <Metric label={text.currentProblems} value={problems.length} />
          <Metric label={text.functionMode} value={functionCount} />
          <Metric label={text.aiAlgorithms} value={aiCount} />
          <Metric label={text.averageAc} value={`${averageAc}%`} />
        </div>
      </aside>

      <section className="library-main">
        <div className="library-header">
          <div>
            <p className="eyebrow">Problem set</p>
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

        <div className="problem-list" aria-label="题目列表">
          {problemsQuery.isLoading ? <p className="muted">{locale === "zh" ? "加载题库中..." : "Loading problems..."}</p> : null}
          {problems.map((problem) => (
            <ProblemCard
              key={problem.id}
              problem={problem}
              locale={locale}
              active={problem.id === selectedId}
              onSelect={() => onSelect(problem.id)}
            />
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
  return (
    <div className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function ProblemCard({ problem, locale, active, onSelect }: { problem: ProblemListItem; locale: Locale; active: boolean; onSelect: () => void }) {
  const displayProblem = localizedProblem(problem, locale);
  const text = UI[locale];
  const titleLayout = measureTrainingText(`${displayProblem.title} ${displayProblem.tags.join(" ")}`, 280, "14px Inter, system-ui, sans-serif", 18);
  const mode = getProblemMode(displayProblem);

  return (
    <button
      className={active ? "problem-card active" : "problem-card"}
      title={locale === "zh" ? `打开 ${displayProblem.title} 的刷题工作台` : `Open ${displayProblem.title}`}
      onClick={onSelect}
      style={{ minHeight: Math.max(128, titleLayout.height + 92) }}
    >
      <span className={`difficulty ${displayProblem.difficulty.toLowerCase()}`}>{displayProblem.difficulty}</span>
      <strong>{displayProblem.title}</strong>
      <span className="tag-line">{displayProblem.tags.join(" / ") || "General"}</span>
      <span className="mode-line">
        <span>{mode.supportsFunction ? text.functionMode : text.acmMode}</span>
        {mode.isAiPractice ? <span>{text.aiAlgorithms}</span> : null}
      </span>
      <span className="card-meta">{displayProblem.accepted_submissions}/{displayProblem.total_submissions} accepted · {Math.round(displayProblem.ac_rate * 100)}%</span>
    </button>
  );
}

function Workspace({
  problemId,
  locale,
  onBackToLibrary,
  onRequireAuth,
  authenticated,
}: {
  problemId: string | null;
  locale: Locale;
  onBackToLibrary: () => void;
  onRequireAuth: () => void;
  authenticated: boolean;
}) {
  const text = UI[locale];
  const { language, setLanguage, getDraft, setDraft, setRecentProblemId, getCachedExplain, setCachedExplain } = useAppStore();
  const [code, setCode] = useState("");
  const [judgeMode, setJudgeMode] = useState<JudgeMode>("acm");
  const [leftOpen, setLeftOpen] = useState(() => localStorage.getItem("fastoj.leftOpen") !== "false");
  const [rightOpen, setRightOpen] = useState(() => localStorage.getItem("fastoj.rightOpen") !== "false");
  const [leftWidth, setLeftWidth] = useState(() => Number(localStorage.getItem("fastoj.leftWidth") ?? 360));
  const [rightWidth, setRightWidth] = useState(() => Number(localStorage.getItem("fastoj.rightWidth") ?? 420));
  const [resizing, setResizing] = useState<"left" | "right" | null>(null);
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [events, setEvents] = useState<JudgeEvent[]>([]);
  const [explain, setExplain] = useState<AIExplain | null>(null);
  const [review, setReview] = useState<AIReview | null>(null);
  const [hint, setHint] = useState<AIHint | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("cases");

  const problemQuery = useQuery({
    queryKey: ["problem", problemId],
    queryFn: () => api.problem(problemId ?? ""),
    enabled: Boolean(problemId),
  });
  const trailQuery = useQuery({
    queryKey: ["submissions", problemId, submission?.id],
    queryFn: () => api.submissions(problemId ?? ""),
    enabled: Boolean(problemId && authenticated),
  });
  const solutionsQuery = useQuery({
    queryKey: ["solutions", problemId, language],
    queryFn: () => api.solutions(problemId ?? "", language),
    enabled: Boolean(problemId),
  });

  const problem = problemQuery.data;
  const displayProblem = localizedProblem(problem, locale);
  const modeInfo = getProblemMode(problem);
  const draftKey = `${language}.${judgeMode}`;
  const functionBlocked = judgeMode === "function" && language !== "python";

  useEffect(() => {
    localStorage.setItem("fastoj.leftOpen", String(leftOpen));
  }, [leftOpen]);

  useEffect(() => {
    localStorage.setItem("fastoj.rightOpen", String(rightOpen));
  }, [rightOpen]);

  useEffect(() => {
    localStorage.setItem("fastoj.leftWidth", String(leftWidth));
  }, [leftWidth]);

  useEffect(() => {
    localStorage.setItem("fastoj.rightWidth", String(rightWidth));
  }, [rightWidth]);

  useEffect(() => {
    if (!problemId) return;
    setRecentProblemId(problemId);
  }, [problemId, setRecentProblemId]);

  useEffect(() => {
    if (!problemId || !problem) return;
    const nextMode = modeInfo.defaultMode;
    setJudgeMode(nextMode);
    const key = `${language}.${nextMode}`;
    setCode(getDraft(problemId, key) || buildStarter(problem, language, nextMode));
  }, [problemId, problem?.slug]);

  useEffect(() => {
    if (!problemId || !problem) return;
    setCode(getDraft(problemId, draftKey) || buildStarter(problem, language, judgeMode));
  }, [language, judgeMode]);

  function updateCode(next: string) {
    setCode(next);
    if (problemId) setDraft(problemId, draftKey, next);
  }

  function switchMode(mode: JudgeMode) {
    if (mode === "function" && !modeInfo.supportsFunction) return;
    setJudgeMode(mode);
  }

  function toggleJudgeMode() {
    if (!modeInfo.supportsFunction) return;
    switchMode(judgeMode === "function" ? "acm" : "function");
  }

  function startResize(side: "left" | "right", event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = side === "left" ? leftWidth : rightWidth;
    setResizing(side);
    const onMove = (moveEvent: PointerEvent) => {
      const delta = side === "left" ? moveEvent.clientX - startX : startX - moveEvent.clientX;
      const next = clamp(startWidth + delta, side === "left" ? 240 : 300, side === "left" ? 620 : 660);
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

  async function judge(runOnly: boolean) {
    if (!problemId || functionBlocked) return;
    if (!authenticated || !localStorage.getItem("fastoj.jwt")) {
      onRequireAuth();
      return;
    }
    setDetailTab("judge");
    setRightOpen(true);
    setEvents([{ type: "pending", status: "pending", progress: 0 }]);
    try {
      const created = await api.submit(problemId, language, code, runOnly, judgeMode);
      setSubmission(created as SubmissionDetail);
      connectStatus(created.id);
    } catch (error) {
      if (isUnauthorized(error)) {
        localStorage.removeItem("fastoj.jwt");
        setEvents([{ type: "error", status: "finished", result: "se", message: text.authMessage }]);
        window.alert(locale === "zh" ? "登录已过期，请重新登录。" : "Your session has expired. Please log in again.");
        onRequireAuth();
        return;
      }
      setEvents([
        {
          type: "error",
          status: "finished",
          result: "se",
          message: error instanceof Error ? error.message : "Submit failed",
        },
      ]);
    }
  }

  function connectStatus(submissionId: string) {
    const socket = makeJudgeSocket(submissionId);
    let polling = false;
    const poll = window.setInterval(async () => {
      if (polling) return;
      polling = true;
      try {
        const detail = await api.submission(submissionId);
        setSubmission(detail);
        if (detail.status === "finished") window.clearInterval(poll);
      } finally {
        polling = false;
      }
    }, 1600);
    if (!socket) return;
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      const data = payload.data ?? {};
      setEvents((items) => [...items, { type: payload.type, ...data }]);
      if (payload.type === "result") {
        window.clearInterval(poll);
        api.submission(submissionId).then(setSubmission).catch(() => undefined);
      }
    };
    socket.onerror = () => socket.close();
  }

  async function explainSubmission() {
    if (!submission) return;
    const cached = getCachedExplain(submission.id);
    if (cached) {
      setExplain(cached);
      return;
    }
    try {
      setAiError(null);
      const result = await api.explain(submission.id);
      setExplain(result);
      setCachedExplain(submission.id, result);
    } catch (error) {
      setAiError(error instanceof Error ? error.message : "AI explain failed");
    }
  }

  async function reviewSubmission() {
    if (!submission) return;
    try {
      setAiError(null);
      setReview(await api.review(submission.id));
    } catch (error) {
      setAiError(error instanceof Error ? error.message : "AI review failed");
    }
  }

  async function requestHint(level: 1 | 2 | 3) {
    if (!problemId) return;
    try {
      setAiError(null);
      setHint(await api.hint(problemId, level, language, code));
    } catch (error) {
      setAiError(error instanceof Error ? error.message : "AI hint failed");
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
    "--left-panel": leftOpen ? `${leftWidth}px` : "48px",
    "--right-panel": rightOpen ? `${rightWidth}px` : "48px",
  } as React.CSSProperties;

  return (
    <main
      className={`workbench-page ${leftOpen ? "" : "left-collapsed"} ${rightOpen ? "" : "right-collapsed"} ${resizing ? "is-resizing" : ""}`}
      style={gridStyle}
    >
      <section className="workbench-header">
        <button title={text.backLibrary} onClick={onBackToLibrary}>{text.backLibrary}</button>
        <div>
          <p className="eyebrow">{text.workbench}</p>
          <h1>{displayProblem?.title ?? text.loadingProblem}</h1>
          <div className="chips">
            {problem ? <span className={`difficulty ${problem.difficulty.toLowerCase()}`}>{problem.difficulty}</span> : null}
            {problem?.tags.map((tag) => <span key={tag}>{tag}</span>)}
            {problem ? <span>{problem.time_limit}ms / {problem.memory_limit}MB</span> : null}
          </div>
        </div>
        <StatusBadge submission={submission} locale={locale} />
      </section>

      <section className="leetcode-grid">
        <aside className="statement-sidebar">
          <button className="drawer-toggle" title={leftOpen ? "收起左侧题面面板" : "展开左侧题面面板"} onClick={() => setLeftOpen((value) => !value)}>
            {leftOpen ? text.statement : <MenuIcon />}
          </button>
          {leftOpen ? (
            <>
              <ProblemStatement problem={problem} locale={locale} />
              <ProblemVisual problem={problem} />
            </>
          ) : null}
        </aside>

        <div
          className="resize-handle"
          role="separator"
          aria-label="调整题面面板宽度"
          title="拖动调整题面面板宽度"
          onPointerDown={(event) => leftOpen && startResize("left", event)}
        />

        <section className="coding-panel">
          <div className="editor-toolbar">
            <button
              className={`mode-toggle ${judgeMode === "function" ? "active function-mode" : "active acm-mode"}`}
              title={!modeInfo.supportsFunction ? text.modeAcmOnlyTitle : judgeMode === "function" ? text.modeFunctionTitle : text.modeAcmTitle}
              disabled={!modeInfo.supportsFunction}
              onClick={toggleJudgeMode}
            >
              <span className="mode-dot" />
              {judgeMode === "function" ? text.functionMode : text.acmMode}
            </button>
            <select title="选择提交语言" value={language} onChange={(event) => setLanguage(event.target.value)}>
              {LANGUAGES.map((item) => <option key={item}>{item}</option>)}
            </select>
            <button onClick={() => setCode(buildStarter(problem, language, judgeMode))}>{text.resetTemplate}</button>
            <button onClick={() => judge(true)} disabled={functionBlocked}>{text.runPublic}</button>
            <button className="primary" onClick={() => judge(false)} disabled={functionBlocked}>{text.submitJudge}</button>
          </div>
          <FunctionFrame problem={problem} mode={judgeMode} blocked={functionBlocked} locale={locale} />
          <CodeEditor language={language} value={code} onChange={updateCode} />
        </section>

        <div
          className="resize-handle"
          role="separator"
          aria-label="调整结果面板宽度"
          title="拖动调整结果面板宽度"
          onPointerDown={(event) => rightOpen && startResize("right", event)}
        />

        <aside className="result-sidebar">
          <button className="drawer-toggle" title={rightOpen ? "收起右侧 AI 和判题面板" : "展开右侧 AI 和判题面板"} onClick={() => setRightOpen((value) => !value)}>
            {rightOpen ? text.result : <MenuIcon />}
          </button>
          {rightOpen ? (
            <>
              <AICopilotPanel
                submission={submission}
                explain={explain}
                review={review}
                hint={hint}
                error={aiError}
                onExplain={explainSubmission}
                onReview={reviewSubmission}
                onHint={requestHint}
                locale={locale}
              />
              <section className="detail-dock">
                <div className="tabs" role="tablist" aria-label="工作台详情">
                  <TabButton tab="cases" active={detailTab} onClick={setDetailTab}>{text.publicCases}</TabButton>
                  <TabButton tab="solution" active={detailTab} onClick={setDetailTab}>{text.solution}</TabButton>
                  <TabButton tab="judge" active={detailTab} onClick={setDetailTab}>{text.judge}</TabButton>
                  <TabButton tab="trail" active={detailTab} onClick={setDetailTab}>{text.trail}</TabButton>
                </div>
                <div className="detail-panel">
                  {detailTab === "cases" ? <SampleCases problem={problem} locale={locale} /> : null}
                  {detailTab === "solution" ? <OfficialSolution solution={solutionsQuery.data?.[0]} locale={locale} /> : null}
                  {detailTab === "judge" ? <JudgeTimeline events={events} submission={submission} /> : null}
                  {detailTab === "trail" ? <SubmissionTrail submissions={trailQuery.data ?? []} locale={locale} /> : null}
                </div>
              </section>
            </>
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

function TabButton({
  tab,
  active,
  onClick,
  children,
}: {
  tab: DetailTab;
  active: DetailTab;
  onClick: (tab: DetailTab) => void;
  children: React.ReactNode;
}) {
  return (
    <button title={`切换到${children}面板`} className={active === tab ? "active" : ""} role="tab" aria-selected={active === tab} onClick={() => onClick(tab)}>
      {children}
    </button>
  );
}

function ProblemStatement({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = UI[locale];
  const displayProblem = localizedProblem(problem, locale);
  if (!displayProblem) return <p className="muted">{text.loadingProblem}</p>;
  return (
    <article className="prose-panel">
      <p>{displayProblem.description}</p>
      <p className="muted">{text.acceptance} {Math.round(displayProblem.ac_rate * 100)}%，{text.submissions} {displayProblem.total_submissions}</p>
      <h3>{text.officialHint}</h3>
      <p>{displayProblem.hint ?? text.noHint}</p>
    </article>
  );
}

function ProblemVisual({ problem }: { problem?: ProblemDetail }) {
  const visual = getVisualSpec(problem);
  return (
    <section className="visual-panel" aria-label="图形化讲解">
      <h3>{visual.title}</h3>
      <div className="visual-flow">
        {visual.steps.map((step, index) => (
          <div className="visual-step" key={step}>
            <span>{index + 1}</span>
            <p>{step}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function FunctionFrame({ problem, mode, blocked, locale }: { problem?: ProblemDetail; mode: JudgeMode; blocked: boolean; locale: Locale }) {
  const text = UI[locale];
  if (mode !== "function") {
    return <div className="function-frame">{text.acmFrame}</div>;
  }
  const spec = getFunctionSpec(problem);
  if (!spec) return <div className="function-frame warning">{text.noFunctionFrame}</div>;
  return (
    <div className={blocked ? "function-frame warning" : "function-frame"}>
      <strong>{spec.signature}</strong>
      <span>{blocked ? text.functionPythonOnly : spec.description}</span>
    </div>
  );
}

function SampleCases({ problem, locale }: { problem?: ProblemDetail; locale: Locale }) {
  const text = UI[locale];
  if (!problem) return <p className="muted">{text.loadingCases}</p>;
  return (
    <div className="case-grid">
      {problem.sample_testcases.map((testcase, index) => (
        <pre className="sample" key={`${testcase.input}-${index}`}>Example {index + 1}

{text.input}:
{testcase.input}

{text.output}:
{testcase.output}

{locale === "zh" ? "解释" : "Explanation"}:
{sampleExplanation(problem.slug, index, locale)}</pre>
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
  const fallback =
    locale === "zh"
      ? "该输出是此输入下的标准答案；评测会按相同输入/输出格式比较。"
      : "The output is the canonical expected answer for this input; judging compares the same I/O format.";
  return (locale === "zh" ? zh : en)[slug]?.[index] ?? fallback;
}

function OfficialSolution({ solution, locale }: { solution?: { explanation: string; code: string; language: string }; locale: Locale }) {
  if (!solution) return <p className="muted">{UI[locale].noSolution}</p>;
  return (
    <article className="prose-panel">
      <p>{solution.explanation}</p>
      <CodeBlock code={solution.code} language={solution.language} />
    </article>
  );
}

function App() {
  const recentProblemId = useAppStore((state) => state.recentProblemId);
  const [selectedId, setSelectedId] = useState<string | null>(recentProblemId);
  const [view, setView] = useState<View>(recentProblemId ? "workbench" : "library");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem("fastoj.locale") === "en" ? "en" : "zh"));
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem("fastoj.jwt")));
  const [graphTag, setGraphTag] = useState("");
  const problemsQuery = useQuery({ queryKey: ["problems", "graph"], queryFn: () => api.problems({}) });
  const problems = useMemo(() => problemsQuery.data ?? [], [problemsQuery.data]);

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
    setView("library");
  }

  return (
    <div className="app-shell">
      <AuthBar
        view={view}
        authenticated={authenticated}
        locale={locale}
        onView={setView}
        onAuth={openAuth}
        onLogout={logout}
        onLocale={toggleLocale}
      />
      {view === "auth" ? (
        <AuthPage
          mode={authMode}
          locale={locale}
          onMode={setAuthMode}
          onDone={() => {
            setAuthenticated(true);
            setView("library");
          }}
        />
      ) : null}
      {view === "library" ? (
        <LibraryPage selectedId={selectedId} selectedTag={graphTag} locale={locale} onSelect={openProblem} onGraph={() => setView("graph")} />
      ) : null}
      {view === "workbench" ? (
        <Workspace
          problemId={selectedId}
          locale={locale}
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
