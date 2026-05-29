import { measureTrainingText } from "../lib/textLayout";
import { type Locale, verdictInfo } from "../lib/i18n";

type TrailItem = {
  id: string;
  language: string;
  result?: string | null;
  execute_time?: number | null;
  created_at: string;
  error_message?: string | null;
};

export function SubmissionTrail({ submissions, locale }: { submissions: TrailItem[]; locale: Locale }) {
  return (
    <section className="trail">
      <h3>{locale === "zh" ? "提交轨迹" : "Submission Trail"}</h3>
      {submissions.length === 0 ? <p className="muted">{locale === "zh" ? "这道题还没有提交记录。" : "No attempts for this problem yet."}</p> : null}
      {submissions.map((item, index) => {
        const previous = submissions[index + 1];
        const verdict = verdictInfo(item.result ?? "pending", locale);
        const previousVerdict = verdictInfo(previous?.result ?? "pending", locale);
        const summary = item.error_message ?? `${verdict.label} · ${item.execute_time ?? 0}ms`;
        const metrics = measureTrainingText(summary, 300);
        return (
          <article className="trail-item" key={item.id} style={{ minHeight: metrics.height + 42 }}>
            <strong title={verdict.description}>{verdict.label}</strong>
            <span>{new Date(item.created_at).toLocaleString()}</span>
            <span>{item.language}</span>
            <p>{summary}</p>
            {previous ? (
              <small>{locale === "zh" ? "上次结果" : "Changed from"} {previousVerdict.label}</small>
            ) : (
              <small>{locale === "zh" ? "第一次尝试" : "First attempt"}</small>
            )}
          </article>
        );
      })}
    </section>
  );
}
