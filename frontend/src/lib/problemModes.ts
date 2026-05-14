import type { ProblemDetail, ProblemListItem } from "./schemas";

export type JudgeMode = "function" | "acm";

type AnyProblem = Pick<ProblemDetail | ProblemListItem, "slug" | "title" | "tags">;

type FunctionSpec = {
  functionName: string;
  signature: string;
  description: string;
  starter: string;
};

type VisualSpec = {
  title: string;
  steps: string[];
};

const FUNCTION_SPECS: Record<string, FunctionSpec> = {
  "two-sum": {
    functionName: "two_sum",
    signature: "def two_sum(nums: list[int], target: int) -> list[int]",
    description: "返回两个下标，提交区只需要补全函数体。",
    starter: `def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}
    for index, value in enumerate(nums):
        need = target - value
        if need in seen:
            return [seen[need], index]
        seen[value] = index
    return []
`,
  },
  "add-two-numbers": {
    functionName: "add_two_numbers",
    signature: "def add_two_numbers(l1: list[int], l2: list[int]) -> list[int]",
    description: "这里用列表模拟逆序链表节点，便于先练核心进位逻辑。",
    starter: `def add_two_numbers(l1: list[int], l2: list[int]) -> list[int]:
    carry = 0
    output: list[int] = []
    i = j = 0
    while i < len(l1) or j < len(l2) or carry:
        value = carry
        if i < len(l1):
            value += l1[i]
            i += 1
        if j < len(l2):
            value += l2[j]
            j += 1
        output.append(value % 10)
        carry = value // 10
    return output
`,
  },
  "longest-substring-without-repeating": {
    functionName: "length_of_longest_substring",
    signature: "def length_of_longest_substring(s: str) -> int",
    description: "维护无重复窗口，返回最长长度。",
    starter: `def length_of_longest_substring(s: str) -> int:
    left = 0
    last_seen: dict[str, int] = {}
    best = 0
    for right, ch in enumerate(s):
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best
`,
  },
  "logistic-regression-sigmoid": {
    functionName: "predict_probability",
    signature: "def predict_probability(weights: list[float], bias: float, features: list[float]) -> float",
    description: "实现 sigmoid(w·x+b)，输出概率会按 4 位小数比较。",
    starter: `import math


def predict_probability(weights: list[float], bias: float, features: list[float]) -> float:
    z = bias + sum(w * x for w, x in zip(weights, features))
    return 1.0 / (1.0 + math.exp(-z))
`,
  },
  "knn-majority-vote": {
    functionName: "predict_knn",
    signature: "def predict_knn(points: list[list[float]], labels: list[str], query: list[float], k: int) -> str",
    description: "按欧氏距离找 k 个近邻，票数相同按标签字典序稳定决策。",
    starter: `def predict_knn(points: list[list[float]], labels: list[str], query: list[float], k: int) -> str:
    distances = []
    for index, point in enumerate(points):
        dist = sum((a - b) ** 2 for a, b in zip(point, query))
        distances.append((dist, labels[index]))
    votes: dict[str, int] = {}
    for _, label in sorted(distances)[:k]:
        votes[label] = votes.get(label, 0) + 1
    return sorted(votes.items(), key=lambda item: (-item[1], item[0]))[0][0]
`,
  },
  "kmeans-one-iteration": {
    functionName: "assign_clusters",
    signature: "def assign_clusters(points: list[list[float]], centroids: list[list[float]]) -> list[int]",
    description: "完成一次 KMeans 分配步骤，返回每个样本最近的中心编号。",
    starter: `def assign_clusters(points: list[list[float]], centroids: list[list[float]]) -> list[int]:
    assignments: list[int] = []
    for point in points:
        best_index = 0
        best_distance = float("inf")
        for index, centroid in enumerate(centroids):
            distance = sum((a - b) ** 2 for a, b in zip(point, centroid))
            if distance < best_distance:
                best_distance = distance
                best_index = index
        assignments.append(best_index)
    return assignments
`,
  },
  "scaled-dot-product-attention": {
    functionName: "attention_row",
    signature: "def attention_row(query: list[float], keys: list[list[float]], values: list[list[float]]) -> list[float]",
    description: "手写单个 query 的 scaled dot-product attention，输出向量按 4 位小数比较。",
    starter: `import math


def attention_row(query: list[float], keys: list[list[float]], values: list[list[float]]) -> list[float]:
    scale = math.sqrt(len(query))
    scores = [sum(q * k for q, k in zip(query, key)) / scale for key in keys]
    max_score = max(scores)
    weights = [math.exp(score - max_score) for score in scores]
    total = sum(weights)
    weights = [weight / total for weight in weights]
    return [
        sum(weight * value[col] for weight, value in zip(weights, values))
        for col in range(len(values[0]))
    ]
`,
  },
  "softmax-cross-entropy": {
    functionName: "cross_entropy_loss",
    signature: "def cross_entropy_loss(logits: list[float], target: int) -> float",
    description: "实现稳定 softmax cross entropy，输出按 4 位小数比较。",
    starter: `import math


def cross_entropy_loss(logits: list[float], target: int) -> float:
    shifted = [value - max(logits) for value in logits]
    total = sum(math.exp(value) for value in shifted)
    return -shifted[target] + math.log(total)
`,
  },
  "attention-mask-apply": {
    functionName: "masked_softmax",
    signature: "def masked_softmax(scores: list[float], mask: list[int]) -> list[float]",
    description: "对注意力分数应用 mask，被 mask 的位置概率必须为 0。",
    starter: `import math


def masked_softmax(scores: list[float], mask: list[int]) -> list[float]:
    active = [score for score, keep in zip(scores, mask) if keep]
    max_score = max(active)
    exps = [math.exp(score - max_score) if keep else 0.0 for score, keep in zip(scores, mask)]
    total = sum(exps)
    return [value / total for value in exps]
`,
  },
};

export const ACM_STARTERS: Record<string, string> = {
  python: "import sys\n\n# Read stdin and print the exact required answer.\ndata = sys.stdin.read().strip()\nprint(data)\n",
  cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    return 0;\n}\n",
  java: "import java.io.*;\nimport java.util.*;\n\nclass Main {\n    public static void main(String[] args) throws Exception {\n    }\n}\n",
  javascript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\nconsole.log(input);\n",
  typescript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\nconsole.log(input);\n",
  golang: "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(\"\")\n}\n",
  c: "#include <stdio.h>\n\nint main(void) {\n    return 0;\n}\n",
};

const VISUALS: Record<string, VisualSpec> = {
  "two-sum": {
    title: "哈希表扫描",
    steps: ["读到 2，记录 2 -> 0", "读到 7，发现 9 - 7 = 2", "返回两个下标 [0,1]"],
  },
  "longest-substring-without-repeating": {
    title: "滑动窗口",
    steps: ["右指针扩张窗口", "遇到重复字符时移动左边界", "每一步更新最长长度"],
  },
  "logistic-regression-sigmoid": {
    title: "线性打分到概率",
    steps: ["计算 w·x+b", "送入 sigmoid 压到 0..1", "按阈值或概率解释分类倾向"],
  },
  "knn-majority-vote": {
    title: "近邻投票",
    steps: ["计算 query 到训练点距离", "取最近的 k 个点", "多数标签成为预测结果"],
  },
  "kmeans-one-iteration": {
    title: "样本归簇",
    steps: ["固定当前中心点", "每个样本找最近中心", "输出簇编号，下一步才能更新中心"],
  },
  "scaled-dot-product-attention": {
    title: "注意力权重",
    steps: ["query 与每个 key 点积", "缩放后 softmax 得到权重", "用权重加权 value 得到输出"],
  },
  "softmax-cross-entropy": {
    title: "分类损失",
    steps: ["logits 减最大值防止溢出", "计算 softmax 分母", "取目标类别负对数概率"],
  },
  "attention-mask-apply": {
    title: "Mask 后的注意力",
    steps: ["屏蔽不可见位置", "只在可见分数上 softmax", "被屏蔽位置输出 0 概率"],
  },
};

export function getFunctionSpec(problem?: AnyProblem | null): FunctionSpec | null {
  if (!problem) return null;
  return FUNCTION_SPECS[problem.slug] ?? null;
}

export function getProblemMode(problem?: AnyProblem | null) {
  const functionSpec = getFunctionSpec(problem);
  const tags = problem?.tags ?? [];
  const isAiPractice = tags.some((tag) => ["AI", "ML", "Deep Learning"].includes(tag));
  return {
    defaultMode: functionSpec ? "function" as JudgeMode : "acm" as JudgeMode,
    supportsFunction: Boolean(functionSpec),
    isAiPractice,
    functionSpec,
  };
}

export function buildStarter(problem: AnyProblem | null | undefined, language: string, mode: JudgeMode): string {
  const spec = getFunctionSpec(problem);
  if (mode === "function" && language === "python" && spec) return spec.starter;
  return ACM_STARTERS[language] ?? "";
}

export function getVisualSpec(problem?: AnyProblem | null): VisualSpec {
  if (!problem) {
    return { title: "解题流程", steps: ["阅读题面", "拆分输入输出", "提交后观察公开用例"] };
  }
  return VISUALS[problem.slug] ?? {
    title: "解题流程",
    steps: ["先确认输入输出格式", "写出主流程", "用公开用例验证边界"],
  };
}
