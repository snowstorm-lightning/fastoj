import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";
import { useEffect, useRef } from "react";

import type { SubmissionDetail } from "../lib/schemas";

export type JudgeEvent = {
  type: string;
  status?: string;
  result?: string;
  progress?: number;
  message?: string;
};

export function JudgeTimeline({
  events,
  submission,
  theme = "dark",
}: {
  events: JudgeEvent[];
  submission: SubmissionDetail | null;
  theme?: "light" | "dark";
}) {
  const terminalRef = useRef<HTMLDivElement | null>(null);
  const terminal = useRef<Terminal | null>(null);

  useEffect(() => {
    if (!terminalRef.current || terminal.current) return;
    const term = new Terminal({
      convertEol: true,
      rows: 8,
      theme: terminalTheme("dark"),
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(terminalRef.current);
    fit.fit();
    terminal.current = term;
  }, []);

  useEffect(() => {
    if (!terminal.current) return;
    terminal.current.options.theme = terminalTheme(theme);
  }, [theme]);

  useEffect(() => {
    const term = terminal.current;
    if (!term) return;
    term.clear();
    events.forEach((event) => term.writeln(`[${event.type}] ${event.result ?? event.status ?? ""} ${event.message ?? ""}`));
    submission?.testcase_results.forEach((item, index) => {
      term.writeln(`case ${index + 1}: ${item.status} ${item.execute_time ?? 0}ms`);
    });
  }, [events, submission]);

  return (
    <section className="timeline">
      <div className="timeline-events">
        {events.map((event, index) => (
          <span className="timeline-chip" key={`${event.type}-${index}`}>
            {event.type} {event.progress ? `${event.progress}%` : event.result ?? event.status}
          </span>
        ))}
      </div>
      <div className="terminal" ref={terminalRef} />
    </section>
  );
}

function terminalTheme(theme: "light" | "dark") {
  return theme === "light"
    ? { background: "#f8fafc", foreground: "#1e293b", cursor: "#2563eb", selectionBackground: "#bfdbfe" }
    : { background: "#10151f", foreground: "#dbeafe", cursor: "#34d399", selectionBackground: "#334155" };
}
