import type { AIExplain, AIHint, AIReview, SubmissionDetail } from "../lib/schemas";
import { type Locale, verdictInfo } from "../lib/i18n";
import { CodeBlock } from "./CodeBlock";

type Props = {
  submission: SubmissionDetail | null;
  explain: AIExplain | null;
  review: AIReview | null;
  hint: AIHint | null;
  error: string | null;
  onExplain: () => void;
  onReview: () => void;
  onHint: (level: 1 | 2 | 3) => void;
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
  error,
  onExplain,
  onReview,
  onHint,
  locale,
}: Props) {
  const current = verdictInfo(submission?.result ?? submission?.status ?? "idle", locale);
  return (
    <aside className="copilot-panel" aria-label="AI Judge Copilot">
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
        <summary>{locale === "zh" ? "公开用例对比" : "Public Case Comparison"}</summary>
        {explain?.public_case_analysis.length ? explain.public_case_analysis.map((item) => (
          <div className="case-card" key={item.case_index}>
            <strong>{locale === "zh" ? "用例" : "Case"} {item.case_index}</strong>
            <p>{item.observation}</p>
            <code>{locale === "zh" ? "期望" : "expected"}: {item.expected_summary}</code>
            <code>{locale === "zh" ? "实际" : "actual"}: {item.actual_summary}</code>
          </div>
        )) : <p className="muted">{locale === "zh" ? "这里只展示公开用例细节。" : "Only public testcase details will appear here."}</p>}
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
    </aside>
  );
}
