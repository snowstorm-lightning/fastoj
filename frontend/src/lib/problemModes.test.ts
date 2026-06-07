import { describe, expect, it } from "vitest";

import { buildStarter, getProblemMode, isLikelyStaleAcmDraft } from "./problemModes";

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

const canonicalLongestSubstring = {
  ...twoSum,
  id: "3",
  title: "Longest Substring Without Repeating Characters",
  slug: "longest-substring-without-repeating-characters",
  tags: ["String", "Sliding Window", "Function"],
};

const alienDictionary = {
  ...twoSum,
  id: "4",
  title: "Alien Dictionary",
  slug: "alien-dictionary",
  tags: ["Graph", "Topological Sort", "Function"],
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

  it("supports the canonical Hot 100 slug for longest substring", () => {
    expect(getProblemMode(canonicalLongestSubstring).supportsFunction).toBe(true);
    expect(buildStarter(canonicalLongestSubstring, "python", "function")).toContain(
      "def length_of_longest_substring",
    );
  });

  it("builds the Alien Dictionary LeetCode-style Python starter", () => {
    expect(getProblemMode(alienDictionary).supportsFunction).toBe(true);
    expect(buildStarter(alienDictionary, "python", "function")).toContain("def alienOrder");
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

  it("treats approved dual-mode agent metadata as both ACM and function capable", () => {
    const generated = {
      ...twoSum,
      slug: "agent-dual-echo",
      mode: "both",
      function_signature: "def echo_value(value: int) -> int",
    };
    const mode = getProblemMode(generated);

    expect(mode.supportsFunction).toBe(true);
    expect(mode.supportsAcm).toBe(true);
    expect(mode.functionSpec?.dynamic).toBe(true);
    expect(buildStarter(generated, "python", "function")).toContain("def echo_value");
  });

  it("builds dynamic function starters for the selected language", () => {
    const generated = {
      ...twoSum,
      slug: "agent-echo-number",
      mode: "function",
      function_signature: "def echo_value(value: int) -> int",
    };

    expect(buildStarter(generated, "cpp", "function")).toContain("int echo_value(int value)");
    expect(buildStarter(generated, "java", "function")).toContain("public int echoValue(int value)");
    expect(buildStarter(generated, "javascript", "function")).toContain("function echoValue(value)");
    expect(buildStarter(generated, "typescript", "function")).toContain("function echoValue(value: number): number");
    expect(buildStarter(generated, "golang", "function")).toContain("func echoValue(value int) int");
    expect(buildStarter(generated, "c", "function")).toContain("int echo_value(int value)");
  });

  it("builds C starters for matrix and string matrix signatures", () => {
    const matrixProblem = {
      ...twoSum,
      slug: "agent-merge-intervals",
      mode: "function",
      function_signature: "def merge_intervals(intervals: list[list[int]]) -> list[list[int]]",
    };
    const stringMatrixProblem = {
      ...twoSum,
      slug: "agent-group-anagrams",
      mode: "function",
      function_signature: "def group_anagrams(strs: list[str]) -> list[list[str]]",
    };

    expect(buildStarter(matrixProblem, "c", "function")).toContain(
      "int** merge_intervals(int** intervals, int intervals_rows, int* intervals_cols, int* return_size, int** return_column_sizes)",
    );
    expect(buildStarter(stringMatrixProblem, "c", "function")).toContain(
      "char*** group_anagrams(char** strs, int strs_len, int* return_size, int** return_column_sizes)",
    );
  });

  it("builds nullable list function starters for static languages", () => {
    const generated = {
      ...twoSum,
      slug: "agent-min-stack",
      mode: "function",
      function_signature: "def run_min_stack(operations: list[str], args: list[list[int]]) -> list[int | None]",
    };

    expect(buildStarter(generated, "cpp", "function")).toContain("vector<optional<int>> run_min_stack");
    expect(buildStarter(generated, "java", "function")).toContain("public Integer[] runMinStack");
    expect(buildStarter(generated, "typescript", "function")).toContain("Array<number | null>");
    expect(buildStarter(generated, "golang", "function")).toContain("[]*int");
    expect(buildStarter(generated, "c", "function")).toContain("int* run_min_stack(char** operations, int operations_len, int** args, int args_rows, int* args_cols, int* return_size, int** return_nulls)");
  });

  it("localizes function starter todos in Chinese mode", () => {
    const starter = buildStarter(twoSum, "cpp", "function", "zh");
    expect(starter).toContain("TODO: 在这里实现你的解法");
    expect(starter).not.toContain("implement your solution here");
  });

  it("identifies stale ACM templates cached under function mode", () => {
    const majority = {
      ...twoSum,
      id: "4",
      title: "Majority Element",
      slug: "majority-element",
      mode: "function",
      function_signature: "def majority_element(nums: list[int]) -> int",
      sample_testcases: [{ input: "[3,2,3]", output: "3" }],
    };
    const staleAcm = buildStarter(majority, "python", "acm", "zh");
    const functionStarter = buildStarter(majority, "python", "function", "zh");

    expect(isLikelyStaleAcmDraft(majority, "python", staleAcm)).toBe(true);
    expect(isLikelyStaleAcmDraft(majority, "python", functionStarter)).toBe(false);
  });
});
