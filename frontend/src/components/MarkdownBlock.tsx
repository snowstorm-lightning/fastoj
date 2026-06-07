import { useMemo } from "react";
import DOMPurify from "dompurify";
import { marked } from "marked";

type MarkdownBlockProps = {
  value?: string | null;
  className?: string;
};

marked.setOptions({
  breaks: true,
  gfm: true,
});

export function MarkdownBlock({ value, className }: MarkdownBlockProps) {
  const html = useMemo(() => {
    const source = String(value ?? "").trim();
    if (!source) return "";
    const rendered = marked.parse(source, { async: false }) as string;
    return DOMPurify.sanitize(rendered, {
      USE_PROFILES: { html: true },
      ADD_ATTR: ["target", "rel"],
    });
  }, [value]);

  if (!html) return null;
  return <div className={["markdown-body", className].filter(Boolean).join(" ")} dangerouslySetInnerHTML={{ __html: html }} />;
}
