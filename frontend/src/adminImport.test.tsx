import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { DraftSourceSummary, getAdminText, ProblemImportForm } from "./main";
import type { AIProfile, ProblemDraft } from "./lib/api";

const profiles: AIProfile[] = [
  {
    value: "default",
    label_zh: "自动选择",
    label_en: "Auto",
    detail_zh: "",
    detail_en: "",
    configured: true,
    available: true,
  },
];

function ImportFormHarness({ onSubmit }: { onSubmit: () => void }) {
  const text = getAdminText("zh");
  const [sourceUrl, setSourceUrl] = useState("");
  const [rawMaterial, setRawMaterial] = useState("");
  const [importNotes, setImportNotes] = useState("");
  const [tags, setTags] = useState("");
  return (
    <ProblemImportForm
      locale="zh"
      text={text}
      sourceUrl={sourceUrl}
      rawMaterial={rawMaterial}
      importNotes={importNotes}
      difficulty="medium"
      tags={tags}
      mode="both"
      model="default"
      languages={["python"]}
      profiles={profiles}
      canImport={rawMaterial.trim().length >= 20}
      onSourceUrlChange={setSourceUrl}
      onRawMaterialChange={setRawMaterial}
      onImportNotesChange={setImportNotes}
      onDifficultyChange={vi.fn()}
      onTagsChange={setTags}
      onModeChange={vi.fn()}
      onModelChange={vi.fn()}
      onToggleLanguage={vi.fn()}
      onSubmit={onSubmit}
    />
  );
}

describe("problem import admin UI", () => {
  it("fills imported material and submits the import form", () => {
    const onSubmit = vi.fn();
    render(<ImportFormHarness onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("来源链接（可选）"), { target: { value: "https://example.com/problem" } });
    fireEvent.change(screen.getByLabelText("题目标签（Tag）"), { target: { value: "数组,双指针" } });
    fireEvent.change(screen.getByLabelText("原始材料"), {
      target: { value: "给定一个整数数组，要求返回满足条件的下标对，并说明样例。" },
    });
    fireEvent.change(screen.getByLabelText("适配要求"), {
      target: { value: "改成函数模式，样例解释要更清楚。" },
    });

    fireEvent.click(screen.getByRole("button", { name: "导入为草稿" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("renders imported draft source summary for admins", () => {
    const draft = {
      id: "draft-1",
      title: "导入题",
      slug: "imported-problem",
      description: "rewritten",
      difficulty: "medium",
      tags: ["数组"],
      mode: "function",
      status: "validated",
      source_metadata: {
        kind: "imported",
        source_url: "https://example.com/problem",
        raw_material: "原始题面和样例材料",
        raw_material_length: 9,
        import_notes: "重写为函数题",
      },
    } as ProblemDraft;

    render(<DraftSourceSummary draft={draft} locale="zh" text={getAdminText("zh")} />);

    expect(screen.getByText("导入")).toBeInTheDocument();
    expect(screen.getByText(/https:\/\/example\.com\/problem/)).toBeInTheDocument();
    expect(screen.getByText(/原始材料长度: 9/)).toBeInTheDocument();
    expect(screen.getByText("原始材料预览")).toBeInTheDocument();
    expect(screen.getByText("原始题面和样例材料")).toBeInTheDocument();
  });
});
