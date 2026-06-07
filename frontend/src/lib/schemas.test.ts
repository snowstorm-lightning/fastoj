import { describe, expect, test } from "vitest";

import { aiExplainSchema, aiHintSchema, aiReviewSchema, problemDetailSchema, problemDiscussionSchema } from "./schemas";

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

describe("problem schemas", () => {
  test("keeps optional sample explanations", () => {
    const detail = problemDetailSchema.parse({
      id: "problem-1",
      title: "Two Sum",
      slug: "two-sum",
      description: "Find two indices.",
      difficulty: "easy",
      tags: ["Array"],
      time_limit: 1000,
      memory_limit: 256,
      hint: null,
      mode: "function",
      function_signature: "def two_sum(nums: list[int], target: int) -> list[int]",
      total_submissions: 0,
      accepted_submissions: 0,
      ac_rate: 0,
      sample_testcases: [{ input: "[2,7,11,15]\n9", output: "[0,1]", explanation: "中文示例解释" }],
      created_at: "2026-06-07T00:00:00Z",
    });

    expect(detail.sample_testcases[0]?.explanation).toBe("中文示例解释");
  });

  test("parses nested discussion replies with action metadata defaults", () => {
    const discussion = problemDiscussionSchema.parse({
      id: "comment-1",
      problem_id: "problem-1",
      user_id: "user-1",
      author: "alice",
      body: "Root",
      created_at: "2026-06-07T00:00:00Z",
      replies: [{
        id: "comment-2",
        problem_id: "problem-1",
        user_id: "user-2",
        author: "bob",
        body: "Reply",
        parent_id: "comment-1",
        like_count: 2,
        liked_by_me: true,
        reply_count: 0,
        can_delete: false,
        is_deleted: false,
        is_template: false,
        created_at: "2026-06-07T00:01:00Z",
      }],
    });

    expect(discussion.like_count).toBe(0);
    expect(discussion.liked_by_me).toBe(false);
    expect(discussion.replies[0]?.parent_id).toBe("comment-1");
    expect(discussion.replies[0]?.replies).toEqual([]);
  });
});
