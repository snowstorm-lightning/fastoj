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

const validParentheses = {
  ...twoSum,
  id: "2",
  title: "Valid Parentheses",
  slug: "valid-parentheses",
  tags: ["Stack", "String"],
};

describe("problem mode metadata", () => {
  it("detects function-mode problems", () => {
    expect(getProblemMode(twoSum).supportsFunction).toBe(true);
  });

  it("builds a Python function starter", () => {
    expect(buildStarter(twoSum, "python", "function")).toContain("def two_sum");
  });

  it("builds a C++ function starter", () => {
    expect(buildStarter(twoSum, "cpp", "function")).toContain("vector<int> two_sum");
  });

  it("detects valid parentheses as both function and ACM capable", () => {
    const mode = getProblemMode(validParentheses);
    expect(mode.supportsFunction).toBe(true);
    expect(mode.supportsAcm).toBe(true);
    expect(buildStarter(validParentheses, "python", "function")).toContain("def is_valid_parentheses");
  });

  it("builds a dynamic Python starter from approved agent metadata", () => {
    const generated = {
      ...twoSum,
      slug: "agent-echo-number",
      mode: "function",
      function_signature: "def echo_value(value: int) -> int",
    };
    const mode = getProblemMode(generated);
    expect(mode.supportsFunction).toBe(true);
    expect(mode.functionSpec?.dynamic).toBe(true);
    expect(buildStarter(generated, "python", "function")).toContain("def echo_value");
  });
});
