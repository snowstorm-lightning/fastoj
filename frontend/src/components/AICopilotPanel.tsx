import { type FormEvent, useState } from "react";

import type { AIExplain, AIHint, AIReview, SubmissionDetail } from "../lib/schemas";
import { localeText, type Locale, verdictInfo } from "../lib/i18n";
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
  disabled?: boolean;
  disabledReason?: string | null;
  onExplain: () => void;
  onReview: () => void;
  onHint: (level: 1 | 2 | 3) => void;
  onChat: (message: string) => void;
  locale: Locale;
};

function List({ items, locale }: { items: string[]; locale: Locale }) {
  if (!items.length) return <p className="muted">{localeText(locale, { zh: "暂无具体备注。", en: "No specific notes yet." })}</p>;
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
  disabled = false,
  disabledReason = null,
  onExplain,
  onReview,
  onHint,
  onChat,
  locale,
}: Props) {
  const current = verdictInfo(submission?.result ?? submission?.status ?? "idle", locale);
  const [draft, setDraft] = useState("");
  const placeholder = localeText(locale, { zh: "追问 AI：为什么错、怎么优化、边界怎么测...", en: "Ask AI about failures, optimization, or edge cases..." });

  function submitChat(event: FormEvent) {
    event.preventDefault();
    const message = draft.trim();
    if (!message) return;
    setDraft("");
    onChat(message);
  }

  return (
    <aside className="copilot-panel" aria-label={localeText(locale, { zh: "AI 判题助手", en: "AI Judge Copilot" })}>
      <div className="panel-heading">
        <span>{localeText(locale, { zh: "AI 判题助手", en: "AI Judge Copilot" })}</span>
        <strong title={current.description}>{current.label}</strong>
      </div>
      {disabled && disabledReason ? <div className="recoverable-error">{disabledReason}</div> : null}
      {error ? <div className="recoverable-error">{error}</div> : null}

      <section>
        <h3>{localeText(locale, { zh: "当前结果", en: "Current Verdict" })}</h3>
        <p className="verdict" title={current.description}>{explain?.verdict ?? current.label}</p>
      </section>

      <section>
        <h3>{localeText(locale, { zh: "下一步", en: "Next Action" })}</h3>
        <p>{explain?.next_action ?? review?.suggested_next_action ?? hint?.hint ?? localeText(locale, { zh: "选择下面的 AI 操作。", en: "Choose an AI action below." })}</p>
      </section>

      <details className="copilot-details" open={Boolean(explain?.summary || review?.summary)}>
        <summary>{localeText(locale, { zh: "错误原因", en: "Error Cause" })}</summary>
        <p>{explain?.summary ?? submission?.error_message ?? localeText(locale, { zh: "运行或提交代码后，会显示基于结果的建议。", en: "Run or submit code to unlock result-aware guidance." })}</p>
        {submission?.error_message ? <CodeBlock code={submission.error_message} language="text" /> : null}
      </details>

      <details className="copilot-details">
        <summary>{localeText(locale, { zh: "可疑代码区域", en: "Suspicious Regions" })}</summary>
        {explain?.suspicious_code_regions.length ? (
          <ul className="compact-list">
            {explain.suspicious_code_regions.map((region) => (
              <li key={`${region.line_start}-${region.reason}`}>
                {region.line_start ? `L${region.line_start}-${region.line_end ?? region.line_start}: ` : ""}
                {region.reason}
              </li>
            ))}
          </ul>
        ) : <p className="muted">{localeText(locale, { zh: "暂无行级可疑区域。", en: "No line-level suspicion yet." })}</p>}
      </details>

      <details className="copilot-details">
        <summary>{localeText(locale, { zh: "边界检查", en: "Boundary Checks" })}</summary>
        <List items={explain?.edge_cases_to_check ?? review?.edge_cases_to_check ?? []} locale={locale} />
      </details>

      <details className="copilot-details">
        <summary>{localeText(locale, { zh: "复杂度", en: "Complexity" })}</summary>
        <p>{explain?.complexity_comment ?? review?.complexity_comment ?? localeText(locale, { zh: "暂无复杂度分析。", en: "No complexity review yet." })}</p>
      </details>

      <div className="copilot-actions">
        <button title={localeText(locale, { zh: "解释最近一次判题结果", en: "Explain latest judge result" })} onClick={onExplain} disabled={disabled || !submission}>{localeText(locale, { zh: "解释", en: "Explain" })}</button>
        <button title={localeText(locale, { zh: "审查最近一次提交代码", en: "Review latest submitted code" })} onClick={onReview} disabled={disabled || !submission}>{localeText(locale, { zh: "审查", en: "Review" })}</button>
        <button title={localeText(locale, { zh: "轻提示", en: "Light hint" })} onClick={() => onHint(1)} disabled={disabled}>{localeText(locale, { zh: "提示 1", en: "Hint 1" })}</button>
        <button title={localeText(locale, { zh: "方向提示", en: "Directional hint" })} onClick={() => onHint(2)} disabled={disabled}>{localeText(locale, { zh: "提示 2", en: "Hint 2" })}</button>
        <button title={localeText(locale, { zh: "强提示", en: "Strong hint" })} onClick={() => onHint(3)} disabled={disabled}>{localeText(locale, { zh: "提示 3", en: "Hint 3" })}</button>
      </div>

      <section className="ai-chat-box">
        <h3>{localeText(locale, { zh: "AI 对话", en: "AI Chat" })}</h3>
        <div className="ai-chat-log" aria-live="polite">
          {chatLines.length ? chatLines.map((line) => (
            <div className={`chat-line ${line.role}`} key={line.id}>
              <strong>{line.role === "user" ? localeText(locale, { zh: "你", en: "You" }) : "AI"}</strong>
              <p>{line.message}</p>
              {line.suggestions?.length ? <List items={line.suggestions} locale={locale} /> : null}
            </div>
          )) : <p className="muted">{localeText(locale, { zh: "运行或提交后，可以继续追问 AI。", en: "Run or submit, then continue with follow-up questions." })}</p>}
        </div>
        <form className="ai-chat-form" onSubmit={submitChat}>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={placeholder} disabled={disabled} />
          <button className="primary" disabled={disabled || !draft.trim()}>{localeText(locale, { zh: "发送", en: "Send" })}</button>
        </form>
      </section>
    </aside>
  );
}
