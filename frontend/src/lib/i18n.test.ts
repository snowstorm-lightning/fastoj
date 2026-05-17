import { describe, expect, test } from "vitest";

import { localizedProblem, matchesLocalizedProblem } from "./i18n";
import type { ProblemListItem } from "./schemas";

const twoSum: ProblemListItem = {
  id: "problem-1",
  title: "Two Sum",
  slug: "two-sum",
  difficulty: "easy",
  tags: ["array", "hash-table"],
  total_submissions: 10,
  accepted_submissions: 6,
  ac_rate: 0.6,
  is_public: true,
  mode: "function",
  created_at: "2026-01-01T00:00:00Z",
};

describe("localized problem search", () => {
  test("matches Chinese localized titles without requiring backend testcase data", () => {
    expect(localizedProblem(twoSum, "zh")?.title).toBe("\u4e24\u6570\u4e4b\u548c");
    expect(matchesLocalizedProblem(twoSum, "zh", "\u4e24\u6570\u4e4b\u548c")).toBe(true);
    expect(matchesLocalizedProblem(twoSum, "zh", "Two Sum")).toBe(true);
  });
});
