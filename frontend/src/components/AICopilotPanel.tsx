import { type FormEvent, useState } from "react";

import type { AIExplain, AIHint, AIReview, SubmissionDetail } from "../lib/schemas";
import { type Locale, verdictInfo } from "../lib/i18n";
import { CodeBlock } from "./CodeBlock";

type ChatLine = {
  id: string;
  role: "user" | "assistant";
  message: string;
  suggestions?: string[];
};

type Props = {
  submission: SubmissionDetail | null;
  explain: AIExplain | null;
  review: AIReview | null;
  hint: AIHint | null;
  chatLines: ChatLine[];
  error: string | null;
  onExplain: () => void;
  onReview: () => void;
  onHint: (level: 1 | 2 | 3) => void;
  onChat: (message: string) => void;
  locale: Locale;
};

function List({ items, locale }: { items: string[]; locale: Locale }) {
  if (!items.length) return <p className="muted">{locale === "zh" ? "暂无具体备注。" : "No specific notes yet."}</p>;
  return (
    <ul className="compact-list">
      {items.map((item) => <li key={item}>{item}</li>)}
    </ul>
  );
}

export function AICopilotPanel({
  submission,
  explain,
  review,
  hint,
  chatLines,
  error,
  onExplain,
  onReview,
  onHint,
  onChat,
  locale,
}: Props) {
  const current = verdictInfo(submission?.result ?? submission?.status ?? "idle", locale);
  const [draft, setDraft] = useState("");
  const placeholder = locale === "zh" ? "追问 AI：为什么错、怎么优化、边界怎么测..." : "Ask AI about failures, optimization, or edge cases...";

  function submitChat(event: FormEvent) {
    event.preventDefault();
    const message = draft.trim();
    if (!message) return;
    setDraft("");
    onChat(message);
  }

  return (
    <aside className="copilot-panel" aria-label={locale === "zh" ? "AI 判题助手" : "AI Judge Copilot"}>
      <div className="panel-heading">
        <span>{locale === "zh" ? "AI 判题助手" : "AI Judge Copilot"}</span>
        <strong title={current.description}>{current.label}</strong>
      </div>
      {error ? <div className="recoverable-error">{error}</div> : null}

      <section>
        <h3>{locale === "zh" ? "当前结果" : "Current Verdict"}</h3>
        <p className="verdict" title={current.description}>{explain?.verdict ?? current.label}</p>
      </section>

      <section>
        <h3>{locale === "zh" ? "下一步" : "Next Action"}</h3>
        <p>{explain?.next_action ?? review?.suggested_next_action ?? hint?.hint ?? (locale === "zh" ? "选择下面的 AI 操作。" : "Choose an AI action below.")}</p>
      </section>

      <details className="copilot-details" open={Boolean(explain?.summary || review?.summary)}>
        <summary>{locale === "zh" ? "错误原因" : "Error Cause"}</summary>
        <p>{explain?.summary ?? submission?.error_message ?? (locale === "zh" ? "运行或提交代码后，会显示基于结果的建议。" : "Run or submit code to unlock result-aware guidance.")}</p>
        {submission?.error_message ? <CodeBlock code={submission.error_message} language="text" /> : null}
      </details>

      <details className="copilot-details">
        <summary>{locale === "zh" ? "可疑代码区域" : "Suspicious Regions"}</summary>
        {explain?.suspicious_code_regions.length ? (
          <ul className="compact-list">
            {explain.suspicious_code_regions.map((region) => (
              <li key={`${region.line_start}-${region.reason}`}>
                {region.line_start ? `L${region.line_start}-${region.line_end ?? region.line_start}: ` : ""}
                {region.reason}
              </li>
            ))}
          </ul>
        ) : <p className="muted">{locale === "zh" ? "暂无行级可疑区域。" : "No line-level suspicion yet."}</p>}
      </details>

      <details className="copilot-details">
        <summary>{locale === "zh" ? "边界检查" : "Boundary Checks"}</summary>
        <List items={explain?.edge_cases_to_check ?? review?.edge_cases_to_check ?? []} locale={locale} />
      </details>

      <details className="copilot-details">
        <summary>{locale === "zh" ? "复杂度" : "Complexity"}</summary>
        <p>{explain?.complexity_comment ?? review?.complexity_comment ?? (locale === "zh" ? "暂无复杂度分析。" : "No complexity review yet.")}</p>
      </details>

      <div className="copilot-actions">
        <button title={locale === "zh" ? "解释最近一次判题结果" : "Explain latest judge result"} onClick={onExplain} disabled={!submission}>{locale === "zh" ? "解释" : "Explain"}</button>
        <button title={locale === "zh" ? "审查最近一次提交代码" : "Review latest submitted code"} onClick={onReview} disabled={!submission}>{locale === "zh" ? "审查" : "Review"}</button>
        <button title={locale === "zh" ? "轻提示" : "Light hint"} onClick={() => onHint(1)}>{locale === "zh" ? "提示 1" : "Hint 1"}</button>
        <button title={locale === "zh" ? "方向提示" : "Directional hint"} onClick={() => onHint(2)}>{locale === "zh" ? "提示 2" : "Hint 2"}</button>
        <button title={locale === "zh" ? "强提示" : "Strong hint"} onClick={() => onHint(3)}>{locale === "zh" ? "提示 3" : "Hint 3"}</button>
      </div>

      <section className="ai-chat-box">
        <h3>{locale === "zh" ? "AI 对话" : "AI Chat"}</h3>
        <div className="ai-chat-log" aria-live="polite">
          {chatLines.length ? chatLines.map((line) => (
            <div className={`chat-line ${line.role}`} key={line.id}>
              <strong>{line.role === "user" ? (locale === "zh" ? "你" : "You") : "AI"}</strong>
              <p>{line.message}</p>
              {line.suggestions?.length ? <List items={line.suggestions} locale={locale} /> : null}
            </div>
          )) : <p className="muted">{locale === "zh" ? "运行或提交后，可以继续追问 AI。" : "Run or submit, then continue with follow-up questions."}</p>}
        </div>
        <form className="ai-chat-form" onSubmit={submitChat}>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={placeholder} />
          <button className="primary" disabled={!draft.trim()}>{locale === "zh" ? "发送" : "Send"}</button>
        </form>
      </section>
    </aside>
  );
}
