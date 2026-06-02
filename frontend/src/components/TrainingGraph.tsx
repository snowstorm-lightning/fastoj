import { Background, Controls, ReactFlow, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { measureTrainingText } from "../lib/textLayout";
import type { ProblemListItem } from "../lib/schemas";
import { localeText, type Locale } from "../lib/i18n";

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

type LocalizedTagLabel = Partial<Record<Locale, string>> & { zh: string };

const TAG_LABELS: Record<string, LocalizedTagLabel> = {
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
    const label = localeText(locale, TAG_LABELS[tag] ?? { zh: tag, en: tag });
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
            title={localeText(locale, { zh: `筛选 ${label} 标签题目`, en: `Filter ${label} problems` })}
            style={{ minWidth: metrics.width + 32 }}
            onClick={() => onTag(tag)}
          >
            <strong>{label}</strong>
            <span>{count} {localeText(locale, { zh: "道题", en: "problems" })}</span>
            <span>{accepted}/{Math.max(count, 1)} {localeText(locale, { zh: "进度", en: "progress" })}</span>
          </button>
        ),
      },
    };
  });

  return (
    <div className="graph-page" data-testid="training-graph">
      <div className="graph-hero">
        <p className="eyebrow">{localeText(locale, { zh: "AI training map", en: "AI training map" })}</p>
        <h1>{localeText(locale, { zh: "知识图谱", en: "Knowledge Graph" })}</h1>
        <p>{localeText(locale, { zh: "点击节点回到题库筛选对应知识点。越靠近中心的卡片越适合先练。", en: "Click a node to filter the problem set. Central cards are good next practice targets." })}</p>
      </div>
      <ReactFlow nodes={nodes} edges={[]} fitView>
        <Background gap={28} size={1.4} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
