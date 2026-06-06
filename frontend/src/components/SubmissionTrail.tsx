import { useState } from "react";

import { api } from "../lib/api";
import { measureTrainingText } from "../lib/textLayout";
import { localeText, type Locale, verdictInfo } from "../lib/i18n";
import type { SubmissionDetail } from "../lib/schemas";

type TrailItem = {
  id: string;
  language: string;
  result?: string | null;
  execute_time?: number | null;
  created_at: string;
  error_message?: string | null;
};

type DetailState = {
  loading: boolean;
  detail?: SubmissionDetail;
  error?: string;
};

export function SubmissionTrail({ submissions, locale }: { submissions: TrailItem[]; locale: Locale }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, DetailState>>({});

  async function toggle(item: TrailItem) {
    if (expandedId === item.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(item.id);
    if (details[item.id]?.detail || details[item.id]?.loading) return;
    setDetails((items) => ({ ...items, [item.id]: { loading: true } }));
    try {
      const detail = await api.submission(item.id);
      setDetails((items) => ({ ...items, [item.id]: { loading: false, detail } }));
    } catch (error) {
      setDetails((items) => ({
        ...items,
        [item.id]: {
          loading: false,
          error: error instanceof Error ? error.message : localeText(locale, { zh: "提交详情加载失败。", en: "Submission detail failed to load." }),
        },
      }));
    }
  }

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
        const expanded = expandedId === item.id;
        const state = details[item.id];
        return (
          <article className="trail-item" key={item.id} style={{ minHeight: metrics.height + 42 }}>
            <button
              type="button"
              className="trail-item-main"
              aria-expanded={expanded}
              onClick={() => toggle(item)}
            >
              <strong title={verdict.description}>{verdict.label}</strong>
              <span>{new Date(item.created_at).toLocaleString()}</span>
              <span>{item.language}</span>
              <p>{summary}</p>
              {previous ? (
                <small>{localeText(locale, { zh: "上次结果", en: "Changed from" })} {previousVerdict.label}</small>
              ) : (
                <small>{localeText(locale, { zh: "第一次尝试", en: "First attempt" })}</small>
              )}
              <small>{expanded ? localeText(locale, { zh: "收起代码", en: "Hide code" }) : localeText(locale, { zh: "查看代码", en: "View code" })}</small>
            </button>
            {expanded ? (
              <div className="trail-code-panel">
                {state?.loading ? <p className="muted">{localeText(locale, { zh: "正在加载提交代码...", en: "Loading submitted code..." })}</p> : null}
                {state?.error ? <p className="muted">{state.error}</p> : null}
                {state?.detail ? <pre className="submission-code-block">{state.detail.code}</pre> : null}
              </div>
            ) : null}
          </article>
        );
      })}
    </section>
  );
}
