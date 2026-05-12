import React, { useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";

import "./styles.css";
import { api, makeJudgeSocket } from "./lib/api";
import { type AIExplain, type AIHint, type AIReview, type ProblemDetail, type SubmissionDetail } from "./lib/schemas";
import { LANGUAGES, useAppStore } from "./stores/useAppStore";
import { AICopilotPanel } from "./components/AICopilotPanel";
import { CodeEditor } from "./components/CodeEditor";
import { JudgeTimeline, type JudgeEvent } from "./components/JudgeTimeline";
import { SubmissionTrail } from "./components/SubmissionTrail";
import { TrainingGraph } from "./components/TrainingGraph";
import { CodeBlock } from "./components/CodeBlock";

const queryClient = new QueryClient();

function AuthBar() {
  const [username, setUsername] = useState("demo");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo123456");
  const [message, setMessage] = useState(localStorage.getItem("fastoj.jwt") ? "signed in" : "guest");

  async function register() {
    try {
      await api.register(username, email, password);
      setMessage("registered");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "register failed");
    }
  }

  async function login() {
    try {
      await api.login(username, password);
      setMessage("signed in");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "login failed");
    }
  }

  return (
    <div className="authbar">
      <input value={username} onChange={(event) => setUsername(event.target.value)} aria-label="username" />
      <input value={email} onChange={(event) => setEmail(event.target.value)} aria-label="email" />
      <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" aria-label="password" />
      <button onClick={register}>Register</button>
      <button onClick={login}>Login</button>
      <span>{message}</span>
    </div>
  );
}

function ProblemConsole({
  selectedId,
  onSelect,
  onGraph,
}: {
  selectedId: string | null;
  onSelect: (id: string) => void;
  onGraph: () => void;
}) {
  const [keyword, setKeyword] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [tags, setTags] = useState("");
  const problemsQuery = useQuery({
    queryKey: ["problems", keyword, difficulty, tags],
    queryFn: () => api.problems({ keyword, difficulty, tags }),
  });

  const problems = problemsQuery.data ?? [];
  const solved = problems.filter((problem) => problem.ac_rate > 0).length;

  return (
    <aside className="problem-console">
      <div className="console-header">
        <h1>FastOJ</h1>
        <button onClick={onGraph}>Training Graph</button>
      </div>
      <div className="training-summary">
        <strong>{solved}/{problems.length}</strong>
        <span>training progress</span>
      </div>
      <div className="filters">
        <input placeholder="keyword" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
        <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
          <option value="">all difficulty</option>
          <option value="EASY">easy</option>
          <option value="MEDIUM">medium</option>
          <option value="HARD">hard</option>
        </select>
        <input placeholder="tag" value={tags} onChange={(event) => setTags(event.target.value)} />
      </div>
      <div className="recommendation">Recommended: revisit low AC-rate problems before asking level 3 hints.</div>
      <div className="problem-list">
        {problems.map((problem) => (
          <button
            className={problem.id === selectedId ? "problem-card active" : "problem-card"}
            key={problem.id}
            onClick={() => onSelect(problem.id)}
          >
            <strong>{problem.title}</strong>
            <span>{problem.difficulty}</span>
            <small>{problem.tags.join(", ")}</small>
          </button>
        ))}
      </div>
    </aside>
  );
}

function Workspace({ problemId }: { problemId: string | null }) {
  const { language, setLanguage, getDraft, setDraft, setRecentProblemId, getCachedExplain, setCachedExplain } = useAppStore();
  const [code, setCode] = useState("");
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [events, setEvents] = useState<JudgeEvent[]>([]);
  const [explain, setExplain] = useState<AIExplain | null>(null);
  const [review, setReview] = useState<AIReview | null>(null);
  const [hint, setHint] = useState<AIHint | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

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

  if (!problemId) return <main className="empty-workspace">Select a problem to start training.</main>;

  return (
    <main className="workspace">
      <section className="problem-pane">
        <ProblemStatement problem={problem} solution={solutionsQuery.data?.[0]} />
      </section>
      <section className="editor-pane">
        <div className="editor-toolbar">
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            {LANGUAGES.map((item) => <option key={item}>{item}</option>)}
          </select>
          <button onClick={() => judge(true)}>Run Public</button>
          <button onClick={() => judge(false)}>Submit</button>
          <button onClick={reviewSubmission} disabled={!submission}>AI Review</button>
        </div>
        <CodeEditor language={language} value={code} onChange={updateCode} />
        <SubmissionTrail submissions={trailQuery.data ?? []} />
      </section>
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
      <JudgeTimeline events={events} submission={submission} />
    </main>
  );
}

function ProblemStatement({ problem, solution }: { problem?: ProblemDetail; solution?: any }) {
  if (!problem) return <p className="muted">Loading problem...</p>;
  return (
    <>
      <h2>{problem.title}</h2>
      <div className="chips">
        <span>{problem.difficulty}</span>
        {problem.tags.map((tag) => <span key={tag}>{tag}</span>)}
      </div>
      <p>{problem.description}</p>
      <p className="muted">Time {problem.time_limit}ms · Memory {problem.memory_limit}MB</p>
      <h3>Public Cases</h3>
      {problem.sample_testcases.map((testcase, index) => (
        <pre className="sample" key={`${testcase.input}-${index}`}>input:
{testcase.input}

output:
{testcase.output}</pre>
      ))}
      <h3>Official Hint</h3>
      <p>{problem.hint ?? "No official hint yet."}</p>
      <h3>Official Solution</h3>
      {solution ? (
        <>
          <p>{solution.explanation}</p>
          <CodeBlock code={solution.code} language={solution.language} />
        </>
      ) : (
        <p className="muted">No official solution for the selected language.</p>
      )}
    </>
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
  const [view, setView] = useState<"workspace" | "graph">("workspace");
  const problemsQuery = useQuery({ queryKey: ["problems", "graph"], queryFn: () => api.problems({}) });
  const problems = useMemo(() => problemsQuery.data ?? [], [problemsQuery.data]);

  return (
    <div className="app-shell">
      <AuthBar />
      <div className="app-grid">
        <ProblemConsole selectedId={selectedId} onSelect={(id) => { setSelectedId(id); setView("workspace"); }} onGraph={() => setView("graph")} />
        {view === "graph" ? (
          <TrainingGraph problems={problems} onTag={(tag) => { setView("workspace"); queryClient.invalidateQueries({ queryKey: ["problems"] }); console.info("filter tag", tag); }} />
        ) : (
          <Workspace problemId={selectedId} />
        )}
      </div>
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
