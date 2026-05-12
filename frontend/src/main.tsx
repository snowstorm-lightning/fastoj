import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";

import "./styles.css";
import { api, makeJudgeSocket, type ProblemFilters } from "./lib/api";
import {
  type AIExplain,
  type AIHint,
  type AIReview,
  type ProblemDetail,
  type ProblemListItem,
  type SubmissionDetail,
} from "./lib/schemas";
import { measureTrainingText } from "./lib/textLayout";
import { LANGUAGES, useAppStore } from "./stores/useAppStore";
import { AICopilotPanel } from "./components/AICopilotPanel";
import { CodeBlock } from "./components/CodeBlock";
import { CodeEditor } from "./components/CodeEditor";
import { JudgeTimeline, type JudgeEvent } from "./components/JudgeTimeline";
import { SubmissionTrail } from "./components/SubmissionTrail";
import { TrainingGraph } from "./components/TrainingGraph";

const queryClient = new QueryClient();

type View = "library" | "workbench" | "graph";
type DetailTab = "statement" | "samples" | "solution" | "judge" | "trail";

function AuthBar({ view, onView }: { view: View; onView: (view: View) => void }) {
  const [username, setUsername] = useState("demo");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo123456");
  const [message, setMessage] = useState(localStorage.getItem("fastoj.jwt") ? "已登录" : "访客");

  async function register() {
    try {
      await api.register(username, email, password);
      setMessage("注册成功");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "注册失败");
    }
  }

  async function login() {
    try {
      await api.login(username, password);
      setMessage("已登录");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "登录失败");
    }
  }

  return (
    <header className="topbar">
      <div className="brand-lockup">
        <strong>FastOJ</strong>
        <span>AI 面试训练</span>
      </div>
      <nav className="topnav" aria-label="主导航">
        <button className={view === "library" ? "active" : ""} onClick={() => onView("library")}>题库</button>
        <button className={view === "workbench" ? "active" : ""} onClick={() => onView("workbench")}>刷题</button>
        <button className={view === "graph" ? "active" : ""} onClick={() => onView("graph")}>图谱</button>
      </nav>
      <div className="authbar">
        <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="username" />
        <input value={email} onChange={(event) => setEmail(event.target.value)} aria-label="email" />
        <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="password" />
        <button onClick={register}>注册</button>
        <button onClick={login}>登录</button>
        <span>{message}</span>
      </div>
    </header>
  );
}

function LibraryPage({
  selectedId,
  selectedTag,
  onSelect,
  onGraph,
}: {
  selectedId: string | null;
  selectedTag: string;
  onSelect: (id: string) => void;
  onGraph: () => void;
}) {
  const [keyword, setKeyword] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [tags, setTags] = useState(selectedTag);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setTags(selectedTag);
    setPage(1);
  }, [selectedTag]);

  const filters: ProblemFilters = { keyword, difficulty, tags, page };
  const problemsQuery = useQuery({
    queryKey: ["problems", filters],
    queryFn: () => api.problems(filters),
  });

  const problems = problemsQuery.data ?? [];
  const practiced = problems.filter((problem) => problem.ac_rate > 0).length;
  const averageAc = problems.length
    ? Math.round((problems.reduce((sum, problem) => sum + problem.ac_rate, 0) / problems.length) * 100)
    : 0;
  const recommendation = problems.find((problem) => problem.ac_rate < 0.45) ?? problems[0];

  function updateTags(value: string) {
    setTags(value);
    setPage(1);
  }

  return (
    <main className="library-page">
      <section className="library-hero">
        <div>
          <p className="eyebrow">训练控制台</p>
          <h1>从题库进入一次专注训练</h1>
          <p className="hero-copy">先筛选题目，再进入刷题工作台；AI 解释、判题时间线和提交轨迹在工作台里按需展开。</p>
        </div>
        <div className="summary-grid" aria-label="训练摘要">
          <Metric label="当前题目" value={problems.length} />
          <Metric label="已练习" value={practiced} />
          <Metric label="平均 AC" value={`${averageAc}%`} />
        </div>
      </section>

      <section className="library-tools">
        <div className="filters">
          <input placeholder="关键词" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
            <option value="">全部难度</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
          <input placeholder="标签，例如 Array" value={tags} onChange={(event) => updateTags(event.target.value)} />
          <button onClick={() => { setKeyword(""); setDifficulty(""); updateTags(""); }}>重置</button>
          <button onClick={onGraph}>打开图谱</button>
        </div>
        <div className="recommendation">
          <span>推荐</span>
          <strong>{recommendation?.title ?? "暂无题目"}</strong>
          <button disabled={!recommendation} onClick={() => recommendation && onSelect(recommendation.id)}>开始</button>
        </div>
      </section>

      <section className="problem-list" aria-label="题目列表">
        {problemsQuery.isLoading ? <p className="muted">加载题库中...</p> : null}
        {problems.map((problem) => (
          <ProblemCard
            key={problem.id}
            problem={problem}
            active={problem.id === selectedId}
            onSelect={() => onSelect(problem.id)}
          />
        ))}
      </section>

      <div className="pager">
        <button disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>上一页</button>
        <span>第 {page} 页</span>
        <button disabled={problems.length === 0} onClick={() => setPage((value) => value + 1)}>下一页</button>
      </div>
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

function ProblemCard({ problem, active, onSelect }: { problem: ProblemListItem; active: boolean; onSelect: () => void }) {
  const titleLayout = measureTrainingText(`${problem.title} ${problem.tags.join(" ")}`, 280, "14px Inter, system-ui, sans-serif", 18);

  return (
    <button
      className={active ? "problem-card active" : "problem-card"}
      onClick={onSelect}
      style={{ minHeight: Math.max(118, titleLayout.height + 82) }}
    >
      <span className={`difficulty ${problem.difficulty.toLowerCase()}`}>{problem.difficulty}</span>
      <strong>{problem.title}</strong>
      <span className="tag-line">{problem.tags.join(" / ") || "General"}</span>
      <span className="card-meta">{problem.accepted_submissions}/{problem.total_submissions} accepted · {Math.round(problem.ac_rate * 100)}%</span>
    </button>
  );
}

function Workspace({ problemId, onBackToLibrary }: { problemId: string | null; onBackToLibrary: () => void }) {
  const { language, setLanguage, getDraft, setDraft, setRecentProblemId, getCachedExplain, setCachedExplain } = useAppStore();
  const [code, setCode] = useState("");
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [events, setEvents] = useState<JudgeEvent[]>([]);
  const [explain, setExplain] = useState<AIExplain | null>(null);
  const [review, setReview] = useState<AIReview | null>(null);
  const [hint, setHint] = useState<AIHint | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("statement");

  const problemQuery = useQuery({
    queryKey: ["problem", problemId],
    queryFn: () => api.problem(problemId ?? ""),
    enabled: Boolean(problemId),
  });
  const trailQuery = useQuery({
    queryKey: ["submissions", problemId, submission?.id],
    queryFn: () => api.submissions(problemId ?? ""),
    enabled: Boolean(problemId),
  });
  const solutionsQuery = useQuery({
    queryKey: ["solutions", problemId, language],
    queryFn: () => api.solutions(problemId ?? "", language),
    enabled: Boolean(problemId),
  });

  const problem = problemQuery.data;

  useEffect(() => {
    if (!problemId) return;
    setRecentProblemId(problemId);
    setCode(getDraft(problemId, language) || starter(language));
  }, [problemId, language]);

  function updateCode(next: string) {
    setCode(next);
    if (problemId) setDraft(problemId, language, next);
  }

  async function judge(runOnly: boolean) {
    if (!problemId) return;
    setDetailTab("judge");
    setEvents([{ type: "pending", status: "pending", progress: 0 }]);
    const created = await api.submit(problemId, language, code, runOnly);
    setSubmission(created as SubmissionDetail);
    connectStatus(created.id);
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
          <h1>选择一道题开始</h1>
          <p className="muted">题面、编辑器、AI 辅助和判题轨迹会分区显示。</p>
          <button onClick={onBackToLibrary}>返回题库</button>
        </div>
      </main>
    );
  }

  return (
    <main className="workbench-page">
      <section className="workbench-header">
        <button onClick={onBackToLibrary}>返回题库</button>
        <div>
          <p className="eyebrow">刷题工作台</p>
          <h1>{problem?.title ?? "加载题目中..."}</h1>
          <div className="chips">
            {problem ? <span className={`difficulty ${problem.difficulty.toLowerCase()}`}>{problem.difficulty}</span> : null}
            {problem?.tags.map((tag) => <span key={tag}>{tag}</span>)}
            {problem ? <span>{problem.time_limit}ms / {problem.memory_limit}MB</span> : null}
          </div>
        </div>
        <StatusBadge submission={submission} />
      </section>

      <section className="focus-grid">
        <div className="coding-panel">
          <div className="editor-toolbar">
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              {LANGUAGES.map((item) => <option key={item}>{item}</option>)}
            </select>
            <button onClick={() => judge(true)}>运行公开用例</button>
            <button className="primary" onClick={() => judge(false)}>提交评测</button>
            <button onClick={reviewSubmission} disabled={!submission}>AI 体检</button>
          </div>
          <CodeEditor language={language} value={code} onChange={updateCode} />
        </div>
        <AICopilotPanel
          submission={submission}
          explain={explain}
          review={review}
          hint={hint}
          error={aiError}
          onExplain={explainSubmission}
          onReview={reviewSubmission}
          onHint={requestHint}
        />
      </section>

      <section className="detail-dock">
        <div className="tabs" role="tablist" aria-label="工作台详情">
          <TabButton tab="statement" active={detailTab} onClick={setDetailTab}>题面</TabButton>
          <TabButton tab="samples" active={detailTab} onClick={setDetailTab}>公开用例</TabButton>
          <TabButton tab="solution" active={detailTab} onClick={setDetailTab}>题解</TabButton>
          <TabButton tab="judge" active={detailTab} onClick={setDetailTab}>判题</TabButton>
          <TabButton tab="trail" active={detailTab} onClick={setDetailTab}>轨迹</TabButton>
        </div>
        <div className="detail-panel">
          {detailTab === "statement" ? <ProblemStatement problem={problem} /> : null}
          {detailTab === "samples" ? <SampleCases problem={problem} /> : null}
          {detailTab === "solution" ? <OfficialSolution solution={solutionsQuery.data?.[0]} /> : null}
          {detailTab === "judge" ? <JudgeTimeline events={events} submission={submission} /> : null}
          {detailTab === "trail" ? <SubmissionTrail submissions={trailQuery.data ?? []} /> : null}
        </div>
      </section>
    </main>
  );
}

function StatusBadge({ submission }: { submission: SubmissionDetail | null }) {
  const label = submission?.result ?? submission?.status ?? "idle";
  return <strong className={`status-badge ${label.toLowerCase()}`}>{label}</strong>;
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
    <button className={active === tab ? "active" : ""} role="tab" aria-selected={active === tab} onClick={() => onClick(tab)}>
      {children}
    </button>
  );
}

function ProblemStatement({ problem }: { problem?: ProblemDetail }) {
  if (!problem) return <p className="muted">加载题目中...</p>;
  return (
    <article className="prose-panel">
      <p>{problem.description}</p>
      <p className="muted">通过率 {Math.round(problem.ac_rate * 100)}%，累计提交 {problem.total_submissions} 次。</p>
      <h3>官方提示</h3>
      <p>{problem.hint ?? "暂无官方提示。"}</p>
    </article>
  );
}

function SampleCases({ problem }: { problem?: ProblemDetail }) {
  if (!problem) return <p className="muted">加载公开用例中...</p>;
  return (
    <div className="case-grid">
      {problem.sample_testcases.map((testcase, index) => (
        <pre className="sample" key={`${testcase.input}-${index}`}>input:
{testcase.input}

output:
{testcase.output}</pre>
      ))}
    </div>
  );
}

function OfficialSolution({ solution }: { solution?: { explanation: string; code: string; language: string } }) {
  if (!solution) return <p className="muted">当前语言暂无官方题解。</p>;
  return (
    <article className="prose-panel">
      <p>{solution.explanation}</p>
      <CodeBlock code={solution.code} language={solution.language} />
    </article>
  );
}

function starter(language: string) {
  if (language === "python") return "import sys\n\nprint(sys.stdin.read().strip())\n";
  if (language === "cpp") return "#include <bits/stdc++.h>\nusing namespace std;\nint main(){ios::sync_with_stdio(false);cin.tie(nullptr);return 0;}\n";
  if (language === "java") return "class Solution { public static void main(String[] args) { } }\n";
  return "";
}

function App() {
  const recentProblemId = useAppStore((state) => state.recentProblemId);
  const [selectedId, setSelectedId] = useState<string | null>(recentProblemId);
  const [view, setView] = useState<View>(recentProblemId ? "workbench" : "library");
  const [graphTag, setGraphTag] = useState("");
  const problemsQuery = useQuery({ queryKey: ["problems", "graph"], queryFn: () => api.problems({}) });
  const problems = useMemo(() => problemsQuery.data ?? [], [problemsQuery.data]);

  function openProblem(id: string) {
    setSelectedId(id);
    setView("workbench");
  }

  return (
    <div className="app-shell">
      <AuthBar view={view} onView={setView} />
      {view === "library" ? (
        <LibraryPage selectedId={selectedId} selectedTag={graphTag} onSelect={openProblem} onGraph={() => setView("graph")} />
      ) : null}
      {view === "workbench" ? (
        <Workspace problemId={selectedId} onBackToLibrary={() => setView("library")} />
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
