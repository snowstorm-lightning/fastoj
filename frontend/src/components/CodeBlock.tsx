import { useEffect, useState } from "react";
import type { HighlighterCore, LanguageInput, ThemeInput } from "shiki/core";

const SUPPORTED_LANGUAGES = ["c", "cpp", "go", "java", "javascript", "python", "typescript"] as const;
type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];
type HighlightLanguage = SupportedLanguage | "text";

const LANGUAGE_ALIASES: Record<string, SupportedLanguage> = {
  "c++": "cpp",
  golang: "go",
  js: "javascript",
  py: "python",
  ts: "typescript",
};

const LANGUAGE_LOADERS: Record<SupportedLanguage, () => Promise<LanguageInput>> = {
  c: () => import("shiki/langs/c.mjs").then((module) => module.default),
  cpp: () => import("shiki/langs/cpp.mjs").then((module) => module.default),
  go: () => import("shiki/langs/go.mjs").then((module) => module.default),
  java: () => import("shiki/langs/java.mjs").then((module) => module.default),
  javascript: () => import("shiki/langs/javascript.mjs").then((module) => module.default),
  python: () => import("shiki/langs/python.mjs").then((module) => module.default),
  typescript: () => import("shiki/langs/typescript.mjs").then((module) => module.default),
};

const highlighterCache = new Map<HighlightLanguage, Promise<HighlighterCore>>();

function getHighlighter(language: HighlightLanguage) {
  const cached = highlighterCache.get(language);
  if (cached) return cached;
  const highlighter = createHighlighter(language);
  highlighterCache.set(language, highlighter);
  return highlighter;
}

async function createHighlighter(language: HighlightLanguage) {
  const [{ createHighlighterCore }, { createJavaScriptRegexEngine }, githubDark, grammar] = await Promise.all([
    import("shiki/core"),
    import("shiki/engine/javascript"),
    import("shiki/themes/github-dark.mjs").then((module) => module.default as ThemeInput),
    language === "text" ? Promise.resolve(null) : LANGUAGE_LOADERS[language](),
  ]);
  return createHighlighterCore({
    engine: createJavaScriptRegexEngine(),
    langs: grammar ? [grammar] : [],
    themes: [githubDark],
  });
}

function normalizeLanguage(language: string): HighlightLanguage {
  const normalized = language.trim().toLowerCase();
  if ((SUPPORTED_LANGUAGES as readonly string[]).includes(normalized)) {
    return normalized as SupportedLanguage;
  }
  return LANGUAGE_ALIASES[normalized] ?? "text";
}

export function CodeBlock({ code, language = "text" }: { code: string; language?: string }) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const highlightLanguage = normalizeLanguage(language);
    getHighlighter(highlightLanguage)
      .then((highlighter) => highlighter.codeToHtml(code || "", {
        lang: highlightLanguage,
        theme: "github-dark",
      }))
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
