import { describe, expect, it } from "vitest";

import { buildDiffLines } from "./RunResultPanel";

describe("RunResultPanel diff", () => {
  it("marks only changed text spans", () => {
    const [line] = buildDiffLines("answer: 3", "answer: 4");

    expect(line.different).toBe(true);
    expect(line.expected.some((segment) => segment.text === "3" && segment.different)).toBe(true);
    expect(line.actual.some((segment) => segment.text === "4" && segment.different)).toBe(true);
  });
});
