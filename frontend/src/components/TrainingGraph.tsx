import { Background, Controls, ReactFlow, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { measureTrainingText } from "../lib/textLayout";
import type { ProblemListItem } from "../lib/schemas";
import type { Locale } from "../lib/i18n";

const TAGS = [
  "Array",
  "Hash Table",
  "Two Pointers",
  "String",
  "Tree",
  "Graph",
  "Dynamic Programming",
  "Greedy",
  "Heap",
];

const TAG_LABELS: Record<string, Record<Locale, string>> = {
  Array: { zh: "数组", en: "Array" },
  "Hash Table": { zh: "哈希表", en: "Hash Table" },
  "Two Pointers": { zh: "双指针", en: "Two Pointers" },
  String: { zh: "字符串", en: "String" },
  Tree: { zh: "树", en: "Tree" },
  Graph: { zh: "图", en: "Graph" },
  "Dynamic Programming": { zh: "动态规划", en: "Dynamic Programming" },
  Greedy: { zh: "贪心", en: "Greedy" },
  Heap: { zh: "堆", en: "Heap" },
};

export function TrainingGraph({
  problems,
  locale,
  onTag,
}: {
  problems: ProblemListItem[];
  locale: Locale;
  onTag: (tag: string) => void;
}) {
  const nodes: Node[] = TAGS.map((tag, index) => {
    const label = TAG_LABELS[tag]?.[locale] ?? tag;
    const count = problems.filter((problem) =>
      problem.tags.some((value) => value.toLowerCase() === tag.toLowerCase()),
    ).length;
    const accepted = problems.filter((problem) =>
      problem.tags.some((value) => value.toLowerCase() === tag.toLowerCase()) && problem.ac_rate > 0,
    ).length;
    const metrics = measureTrainingText(`${label} ${count} ${accepted}`);
    return {
      id: tag,
      type: "default",
      position: { x: (index % 3) * 300, y: Math.floor(index / 3) * 170 },
      data: {
        label: (
          <button
            className="graph-node"
            title={locale === "zh" ? `筛选 ${label} 标签题目` : `Filter ${label} problems`}
            style={{ minWidth: metrics.width + 32 }}
            onClick={() => onTag(tag)}
          >
            <strong>{label}</strong>
            <span>{count} {locale === "zh" ? "道题" : "problems"}</span>
            <span>{accepted}/{Math.max(count, 1)} {locale === "zh" ? "进度" : "progress"}</span>
          </button>
        ),
      },
    };
  });

  return (
    <div className="graph-page" data-testid="training-graph">
      <div className="graph-hero">
        <p className="eyebrow">{locale === "zh" ? "AI training map" : "AI training map"}</p>
        <h1>{locale === "zh" ? "知识图谱" : "Knowledge Graph"}</h1>
        <p>{locale === "zh" ? "点击节点回到题库筛选对应知识点。越靠近中心的卡片越适合先练。" : "Click a node to filter the problem set. Central cards are good next practice targets."}</p>
      </div>
      <ReactFlow nodes={nodes} edges={[]} fitView>
        <Background gap={28} size={1.4} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
