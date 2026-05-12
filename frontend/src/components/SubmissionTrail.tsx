import { measureTrainingText } from "../lib/textLayout";

type TrailItem = {
  id: string;
  language: string;
  result?: string | null;
  execute_time?: number | null;
  memory_used?: number | null;
  created_at: string;
  error_message?: string | null;
};

export function SubmissionTrail({ submissions }: { submissions: TrailItem[] }) {
  return (
    <section className="trail">
      <h3>Submission Trail</h3>
      {submissions.length === 0 ? <p className="muted">No attempts for this problem yet.</p> : null}
      {submissions.map((item, index) => {
        const previous = submissions[index + 1];
        const summary = item.error_message ?? `${item.result ?? "pending"} in ${item.execute_time ?? 0}ms`;
        const metrics = measureTrainingText(summary, 300);
        return (
          <article className="trail-item" key={item.id} style={{ minHeight: metrics.height + 42 }}>
            <strong>{item.result ?? "pending"}</strong>
            <span>{new Date(item.created_at).toLocaleString()}</span>
            <span>{item.language}</span>
            <p>{summary}</p>
            {previous ? <small>Changed from {previous.result ?? "pending"}</small> : <small>First attempt</small>}
          </article>
        );
      })}
    </section>
  );
}
