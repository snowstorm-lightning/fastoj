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
