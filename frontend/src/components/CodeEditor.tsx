import * as monaco from "monaco-editor";
import { useEffect, useRef } from "react";

const LANGUAGE_MAP: Record<string, string> = {
  python: "python",
  c: "c",
  cpp: "cpp",
  java: "java",
  javascript: "javascript",
  typescript: "typescript",
  golang: "go",
};

export function CodeEditor({
  language,
  value,
  onChange,
  theme = "dark",
}: {
  language: string;
  value: string;
  onChange: (value: string) => void;
  theme?: "light" | "dark";
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const onChangeRef = useRef(onChange);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!containerRef.current || editorRef.current) return;
    const editor = monaco.editor.create(containerRef.current, {
      value,
      language: LANGUAGE_MAP[language] ?? "plaintext",
      theme: theme === "light" ? "vs" : "vs-dark",
      minimap: { enabled: false },
      fontSize: 14,
      automaticLayout: true,
      scrollBeyondLastLine: false,
    });
    editor.onDidChangeModelContent(() => onChangeRef.current(editor.getValue()));
    editorRef.current = editor;
    return () => editor.dispose();
    // Monaco must be created exactly once for this DOM node.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    monaco.editor.setTheme(theme === "light" ? "vs" : "vs-dark");
  }, [theme]);

  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const model = editor.getModel();
    if (model && model.getValue() !== value) model.setValue(value);
  }, [value]);

  useEffect(() => {
    const model = editorRef.current?.getModel();
    if (model) monaco.editor.setModelLanguage(model, LANGUAGE_MAP[language] ?? "plaintext");
  }, [language]);

  return <div className="code-editor" ref={containerRef} />;
}
