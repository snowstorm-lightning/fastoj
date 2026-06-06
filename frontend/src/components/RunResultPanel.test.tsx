import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildDiffLines, RunResultPanel, type EditableRunCase } from "./RunResultPanel";

describe("RunResultPanel diff", () => {
  it("marks only changed text spans", () => {
    const [line] = buildDiffLines("answer: 3", "answer: 4");

    expect(line.different).toBe(true);
    expect(line.expected.some((segment) => segment.text === "3" && segment.different)).toBe(true);
    expect(line.actual.some((segment) => segment.text === "4" && segment.different)).toBe(true);
  });
});

describe("RunResultPanel cases", () => {
  const cases: EditableRunCase[] = [
    { id: "case-1", input: "[1]", expected_output: "1" },
    { id: "case-2", input: "[2]", expected_output: "2" },
  ];

  it("deletes cases from the case tab control", () => {
    const onRemoveCase = vi.fn();
    render(
      <RunResultPanel
        locale="zh"
        cases={cases}
        activeIndex={1}
        submission={null}
        snapshot={null}
        canRun
        onActiveIndex={vi.fn()}
        onChangeInput={vi.fn()}
        onAddCase={vi.fn()}
        onRemoveCase={onRemoveCase}
        onResetCases={vi.fn()}
        onRun={vi.fn()}
      />,
    );

    expect(screen.queryByRole("button", { name: "删除" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "删除 用例 2" }));

    expect(onRemoveCase).toHaveBeenCalledWith(1);
  });
});
