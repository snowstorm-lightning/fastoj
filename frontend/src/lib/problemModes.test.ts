import { describe, expect, it } from "vitest";

import { buildStarter, getProblemMode } from "./problemModes";

const twoSum = {
  id: "1",
  title: "Two Sum",
  slug: "two-sum",
  difficulty: "easy",
  tags: ["Array", "Function"],
  total_submissions: 0,
  accepted_submissions: 0,
  ac_rate: 0,
  is_public: true,
  created_at: "2026-01-01T00:00:00",
};

describe("problem mode metadata", () => {
  it("detects function-mode problems", () => {
    expect(getProblemMode(twoSum).supportsFunction).toBe(true);
  });

  it("builds a Python function starter", () => {
    expect(buildStarter(twoSum, "python", "function")).toContain("def two_sum");
  });

  it("falls back to ACM starter for unsupported function languages", () => {
    expect(buildStarter(twoSum, "cpp", "function")).toContain("int main");
  });
});
