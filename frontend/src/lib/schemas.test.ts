import { describe, expect, test } from "vitest";

import { aiExplainSchema, aiHintSchema, aiReviewSchema } from "./schemas";

describe("AI response schemas", () => {
  test("validates explain, review, and hint payloads", () => {
    expect(() =>
      aiExplainSchema.parse({
        summary: "Wrong answer on public case.",
        verdict: "wrong_answer",
        likely_causes: ["off by one"],
        suspicious_code_regions: [{ line_start: 2, line_end: 3, reason: "index boundary" }],
        public_case_analysis: [{ case_index: 1, observation: "mismatch", expected_summary: "3", actual_summary: "2" }],
        minimal_fix_hint: "Check loop bounds.",
        edge_cases_to_check: ["empty input"],
        complexity_comment: "Linear.",
        next_action: "Run public cases.",
        full_solution_revealed: false,
      }),
    ).not.toThrow();

    expect(() =>
      aiReviewSchema.parse({
        summary: "Readable but risky.",
        risks: ["no input validation"],
        io_format_notes: ["prints extra spaces"],
        edge_cases_to_check: ["single item"],
        complexity_comment: "O(n).",
        suggested_next_action: "Trim output.",
      }),
    ).not.toThrow();

    expect(() =>
      aiHintSchema.parse({ level: 2, hint: "Use a hash map.", focus: ["lookup"], full_solution_revealed: false }),
    ).not.toThrow();
  });
});
