import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import type { AIExplain } from "../lib/schemas";
import { AICopilotPanel } from "./AICopilotPanel";

test("renders AI copilot controls", () => {
  render(
    <AICopilotPanel
      submission={null}
      explain={null}
      review={null}
      hint={null}
      chatLines={[]}
      error={null}
      onExplain={vi.fn()}
      onReview={vi.fn()}
      onHint={vi.fn()}
      onChat={vi.fn()}
      locale="en"
    />,
  );
  expect(screen.getByLabelText("AI Judge Copilot")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Hint 1" })).toBeEnabled();
});

test("keeps public case diff out of the AI copilot", () => {
  const explain: AIExplain = {
    summary: "The result differs on a sample.",
    verdict: "wrong_answer",
    likely_causes: ["The return value is hard-coded."],
    suspicious_code_regions: [{ line_start: 3, line_end: 3, reason: "Always returns the same value." }],
    public_case_analysis: [
      { case_index: 1, observation: "Mismatch", expected_summary: "2", actual_summary: "3" },
    ],
    minimal_fix_hint: "Use the input values.",
    edge_cases_to_check: ["Longer input"],
    complexity_comment: "Constant time because the algorithm is incomplete.",
    next_action: "Fix the return value and rerun.",
    full_solution_revealed: false,
  };

  render(
    <AICopilotPanel
      submission={null}
      explain={explain}
      review={null}
      hint={null}
      chatLines={[]}
      error={null}
      onExplain={vi.fn()}
      onReview={vi.fn()}
      onHint={vi.fn()}
      onChat={vi.fn()}
      locale="en"
    />,
  );

  expect(screen.queryByText("Public Case Comparison")).not.toBeInTheDocument();
  expect(screen.getByText("Suspicious Regions")).toBeInTheDocument();
});
