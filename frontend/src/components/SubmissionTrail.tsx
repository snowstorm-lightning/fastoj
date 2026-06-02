import { measureTrainingText } from "../lib/textLayout";
import { localeText, type Locale, verdictInfo } from "../lib/i18n";

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
      <h3>{localeText(locale, { zh: "提交轨迹", en: "Submission Trail" })}</h3>
      {submissions.length === 0 ? <p className="muted">{localeText(locale, { zh: "这道题还没有提交记录。", en: "No attempts for this problem yet." })}</p> : null}
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
              <small>{localeText(locale, { zh: "上次结果", en: "Changed from" })} {previousVerdict.label}</small>
            ) : (
              <small>{localeText(locale, { zh: "第一次尝试", en: "First attempt" })}</small>
            )}
          </article>
        );
      })}
    </section>
  );
}
