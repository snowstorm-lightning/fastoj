import { Background, Controls, ReactFlow, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { measureTrainingText } from "../lib/textLayout";
import type { ProblemListItem } from "../lib/schemas";

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

export function TrainingGraph({
  problems,
  onTag,
}: {
  problems: ProblemListItem[];
  onTag: (tag: string) => void;
}) {
  const nodes: Node[] = TAGS.map((tag, index) => {
    const count = problems.filter((problem) =>
      problem.tags.some((value) => value.toLowerCase() === tag.toLowerCase()),
    ).length;
    const accepted = problems.filter((problem) =>
      problem.tags.some((value) => value.toLowerCase() === tag.toLowerCase()) && problem.ac_rate > 0,
    ).length;
    const metrics = measureTrainingText(`${tag} ${count} problems ${accepted} practiced`);
    return {
      id: tag,
      type: "default",
      position: { x: (index % 3) * 260, y: Math.floor(index / 3) * 150 },
      data: {
        label: (
          <button className="graph-node" style={{ minWidth: metrics.width }} onClick={() => onTag(tag)}>
            <strong>{tag}</strong>
            <span>{count} problems</span>
            <span>{accepted}/{Math.max(count, 1)} progress</span>
          </button>
        ),
      },
    };
  });

  return (
    <div className="graph-page" data-testid="training-graph">
      <ReactFlow nodes={nodes} edges={[]} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
