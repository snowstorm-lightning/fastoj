import { codeToHtml } from "shiki";
import { useEffect, useState } from "react";

export function CodeBlock({ code, language = "text" }: { code: string; language?: string }) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    codeToHtml(code || "", { lang: language, theme: "github-dark" })
      .then((value) => {
        if (!cancelled) setHtml(value);
      })
      .catch(() => {
        if (!cancelled) setHtml(null);
      });
    return () => {
      cancelled = true;
    };
  }, [code, language]);

  if (!html) return <pre className="sample">{code}</pre>;
  return <div className="shiki-block" dangerouslySetInnerHTML={{ __html: html }} />;
}
