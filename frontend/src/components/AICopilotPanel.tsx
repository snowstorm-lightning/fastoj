import type { AIExplain, AIHint, AIReview, SubmissionDetail } from "../lib/schemas";
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
};

function List({ items }: { items: string[] }) {
  if (!items.length) return <p className="muted">No specific notes yet.</p>;
  return (
    <ul className="compact-list">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
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
}: Props) {
  return (
    <aside className="copilot-panel" aria-label="AI Judge Copilot">
      <div className="panel-heading">
        <span>AI Judge Copilot</span>
        <strong>{submission?.result ?? submission?.status ?? "idle"}</strong>
      </div>
      {error ? <div className="recoverable-error">{error}</div> : null}
      <section>
        <h3>Current Verdict</h3>
        <p className="verdict">{explain?.verdict ?? submission?.result ?? "No submission selected"}</p>
      </section>
      <section>
        <h3>Next Action</h3>
        <p>{explain?.next_action ?? review?.suggested_next_action ?? hint?.hint ?? "Choose an AI action below."}</p>
      </section>
      <details className="copilot-details" open={Boolean(explain?.summary || review?.summary)}>
        <summary>Error Cause</summary>
        <p>{explain?.summary ?? submission?.error_message ?? "Run or submit code to unlock result-aware guidance."}</p>
        {submission?.error_message ? <CodeBlock code={submission.error_message} language="text" /> : null}
      </details>
      <details className="copilot-details">
        <summary>Suspicious Regions</summary>
        {explain?.suspicious_code_regions.length ? (
          <ul className="compact-list">
            {explain.suspicious_code_regions.map((region) => (
              <li key={`${region.line_start}-${region.reason}`}>
                {region.line_start ? `L${region.line_start}-${region.line_end ?? region.line_start}: ` : ""}
                {region.reason}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No line-level suspicion yet.</p>
        )}
      </details>
      <details className="copilot-details">
        <summary>Public Case Comparison</summary>
        {explain?.public_case_analysis.length ? (
          explain.public_case_analysis.map((item) => (
            <div className="case-card" key={item.case_index}>
              <strong>Case {item.case_index}</strong>
              <p>{item.observation}</p>
              <code>expected: {item.expected_summary}</code>
              <code>actual: {item.actual_summary}</code>
            </div>
          ))
        ) : (
          <p className="muted">Only public testcase details will appear here.</p>
        )}
      </details>
      <details className="copilot-details">
        <summary>Boundary Checks</summary>
        <List items={explain?.edge_cases_to_check ?? review?.edge_cases_to_check ?? []} />
      </details>
      <details className="copilot-details">
        <summary>Complexity</summary>
        <p>{explain?.complexity_comment ?? review?.complexity_comment ?? "No complexity review yet."}</p>
      </details>
      <div className="copilot-actions">
        <button onClick={onExplain} disabled={!submission}>Explain</button>
        <button onClick={onReview} disabled={!submission}>Review Code</button>
        <button onClick={() => onHint(1)}>Hint 1</button>
        <button onClick={() => onHint(2)}>Hint 2</button>
        <button onClick={() => onHint(3)}>Hint 3</button>
      </div>
    </aside>
  );
}
