import { describe, expect, test } from "vitest";

import {
  SUPPORTED_LOCALES,
  LOCALE_STORAGE_KEY,
  canonicalTagQuery,
  htmlLangForLocale,
  localeText,
  localizedProblem,
  matchesLocalizedProblem,
  nextLocale,
  normalizeLocale,
  readStoredLocale,
  writeStoredLocale,
} from "./i18n";
import type { ProblemDetail, ProblemListItem } from "./schemas";

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

const twoSumDetail: ProblemDetail = {
  ...twoSum,
  description: "Given an integer array nums and an integer target, return indices of the two numbers such that they add up to target.",
  time_limit: 1000,
  memory_limit: 256,
  hint: "Use a hash table.",
  input_format: null,
  output_format: null,
  function_signature: "def two_sum(nums: list[int], target: int) -> list[int]",
  sample_testcases: [],
};

const minPathSumDetail: ProblemDetail = {
  id: "problem-2",
  title: "Minimum Path Sum",
  slug: "minimum-path-sum",
  difficulty: "medium",
  tags: ["Dynamic Programming", "Matrix"],
  total_submissions: 10,
  accepted_submissions: 6,
  ac_rate: 0.6,
  mode: "function",
  created_at: "2026-01-01T00:00:00Z",
  description: "Find the minimum sum along a path from top-left to bottom-right, moving only right or down.",
  time_limit: 1000,
  memory_limit: 256,
  hint: "Use grid DP.",
  input_format: null,
  output_format: null,
  function_signature: "def min_path_sum(grid: list[list[int]]) -> int",
  sample_testcases: [],
};

describe("localized problem search", () => {
  test("matches Chinese localized titles without requiring backend testcase data", () => {
    expect(localizedProblem(twoSum, "zh")?.title).toBe("\u4e24\u6570\u4e4b\u548c");
    expect(matchesLocalizedProblem(twoSum, "zh", "\u4e24\u6570\u4e4b\u548c")).toBe(true);
    expect(matchesLocalizedProblem(twoSum, "zh", "Two Sum")).toBe(true);
  });

  test("expands Chinese problem details with problem meaning instead of platform contracts", () => {
    const localized = localizedProblem(twoSumDetail, "zh");

    expect(localized?.title).toBe("\u4e24\u6570\u4e4b\u548c");
    expect(localized?.description).toContain("\u4e24\u4e2a\u4e0d\u540c\u4f4d\u7f6e");
    expect(localized?.description).toContain("\u76ee\u6807\u503c");
    expect(localized?.description).not.toContain("\u51fd\u6570\u5951\u7ea6");
    expect(localized?.description).not.toContain("def two_sum(nums: list[int], target: int) -> list[int]");
    expect(localized?.description).not.toContain("JSON-line");
  });

  test("describes minimum path sum as a route problem in Chinese", () => {
    const localized = localizedProblem(minPathSumDetail, "zh");

    expect(localized?.description).toContain("\u5de6\u4e0a\u89d2");
    expect(localized?.description).toContain("\u53f3\u4e0b\u89d2");
    expect(localized?.description).toContain("\u8def\u5f84\u548c");
    expect(localized?.description).toContain("\u6700\u5c0f");
  });

  test("normalizes and persists supported interface locales", () => {
    localStorage.removeItem(LOCALE_STORAGE_KEY);
    expect(normalizeLocale("zh")).toBe("zh");
    expect(normalizeLocale("en")).toBe("en");
    expect(normalizeLocale("fr")).toBeNull();

    writeStoredLocale("en");
    expect(readStoredLocale()).toBe("en");
  });

  test("keeps locale metadata and fallback copy centralized", () => {
    expect(SUPPORTED_LOCALES).toContain("zh");
    expect(htmlLangForLocale("zh")).toBe("zh-CN");
    expect(nextLocale("zh")).toBe("en");
    expect(localeText("en", { zh: "默认" })).toBe("默认");
  });

  test("canonical tag search accepts Chinese comma and case variants", () => {
    expect(canonicalTagQuery("数组，双指针", "zh")).toBe("Array, Two Pointers");
    expect(canonicalTagQuery("array, two pointers", "en")).toBe("Array, Two Pointers");
  });
});
