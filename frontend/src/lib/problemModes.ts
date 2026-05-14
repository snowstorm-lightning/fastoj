import type { ProblemDetail, ProblemListItem } from "./schemas";
import type { Locale } from "./i18n";

export type JudgeMode = "function" | "acm";

type AnyProblem = Pick<ProblemDetail | ProblemListItem, "slug" | "title" | "tags"> & {
  sample_testcases?: Array<{ input: string; output: string }>;
};

type FunctionSpec = {
  functionName: string;
  signature: string;
  description: Record<Locale, string>;
  starter: string;
};

type VisualSpec = {
  title: Record<Locale, string>;
  steps: Record<Locale, string[]>;
};

const TODO = "    # TODO: implement your solution here\n";

const FUNCTION_SPECS: Record<string, FunctionSpec> = {
  "two-sum": {
    functionName: "two_sum",
    signature: "def two_sum(nums: list[int], target: int) -> list[int]",
    description: {
      zh: "返回两个下标，提交区只需要补全函数体。",
      en: "Return two indices. Only complete the function body.",
    },
    starter: `def two_sum(nums: list[int], target: int) -> list[int]:
${TODO}    return []
`,
  },
  "add-two-numbers": {
    functionName: "add_two_numbers",
    signature: "def add_two_numbers(l1: list[int], l2: list[int]) -> list[int]",
    description: {
      zh: "这里用数组模拟逆序链表节点，专注练习进位逻辑。",
      en: "Arrays simulate reversed linked lists so you can focus on carry handling.",
    },
    starter: `def add_two_numbers(l1: list[int], l2: list[int]) -> list[int]:
${TODO}    return []
`,
  },
  "longest-substring-without-repeating": {
    functionName: "length_of_longest_substring",
    signature: "def length_of_longest_substring(s: str) -> int",
    description: {
      zh: "维护无重复窗口，返回最长长度。",
      en: "Maintain a non-repeating window and return the best length.",
    },
    starter: `def length_of_longest_substring(s: str) -> int:
${TODO}    return 0
`,
  },
  "logistic-regression-sigmoid": {
    functionName: "predict_probability",
    signature: "def predict_probability(weights: list[float], bias: float, features: list[float]) -> float",
    description: {
      zh: "实现 sigmoid(w dot x + b)，输出概率会按 4 位小数比较。",
      en: "Implement sigmoid(w dot x + b). The probability is compared to 4 decimals.",
    },
    starter: `import math


def predict_probability(weights: list[float], bias: float, features: list[float]) -> float:
${TODO}    return 0.0
`,
  },
  "knn-majority-vote": {
    functionName: "predict_knn",
    signature: "def predict_knn(points: list[list[float]], labels: list[str], query: list[float], k: int) -> str",
    description: {
      zh: "按欧氏距离找 k 个近邻，票数相同按标签字典序稳定决策。",
      en: "Find k nearest neighbors by Euclidean distance; break ties by label order.",
    },
    starter: `def predict_knn(points: list[list[float]], labels: list[str], query: list[float], k: int) -> str:
${TODO}    return ""
`,
  },
  "kmeans-one-iteration": {
    functionName: "assign_clusters",
    signature: "def assign_clusters(points: list[list[float]], centroids: list[list[float]]) -> list[int]",
    description: {
      zh: "完成一次 KMeans 分配步骤，返回每个样本最近的中心编号。",
      en: "Run one KMeans assignment step and return the nearest centroid index for each point.",
    },
    starter: `def assign_clusters(points: list[list[float]], centroids: list[list[float]]) -> list[int]:
${TODO}    return []
`,
  },
  "scaled-dot-product-attention": {
    functionName: "attention_row",
    signature: "def attention_row(query: list[float], keys: list[list[float]], values: list[list[float]]) -> list[float]",
    description: {
      zh: "手写单个 query 的 scaled dot-product attention，输出向量按 4 位小数比较。",
      en: "Implement scaled dot-product attention for one query. Output is compared to 4 decimals.",
    },
    starter: `import math


def attention_row(query: list[float], keys: list[list[float]], values: list[list[float]]) -> list[float]:
${TODO}    return []
`,
  },
  "softmax-cross-entropy": {
    functionName: "cross_entropy_loss",
    signature: "def cross_entropy_loss(logits: list[float], target: int) -> float",
    description: {
      zh: "实现稳定 softmax cross entropy，输出按 4 位小数比较。",
      en: "Implement stable softmax cross entropy. Output is compared to 4 decimals.",
    },
    starter: `import math


def cross_entropy_loss(logits: list[float], target: int) -> float:
${TODO}    return 0.0
`,
  },
  "attention-mask-apply": {
    functionName: "masked_softmax",
    signature: "def masked_softmax(scores: list[float], mask: list[int]) -> list[float]",
    description: {
      zh: "对注意力分数应用 mask，被 mask 的位置概率必须为 0。",
      en: "Apply a mask to attention scores; masked positions must have probability 0.",
    },
    starter: `import math


def masked_softmax(scores: list[float], mask: list[int]) -> list[float]:
${TODO}    return []
`,
  },
};

export const ACM_STARTERS: Record<string, string> = {
  python: "import sys\n\n# Read stdin and print the exact required answer.\ndata = sys.stdin.read().strip()\n# TODO: parse input and solve\nprint(data)\n",
  cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    // TODO: parse stdin and print the answer\n    return 0;\n}\n",
  java: "import java.io.*;\nimport java.util.*;\n\nclass Main {\n    public static void main(String[] args) throws Exception {\n        // TODO: parse stdin and print the answer\n    }\n}\n",
  javascript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\n// TODO: parse input and solve\nconsole.log(input);\n",
  typescript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\n// TODO: parse input and solve\nconsole.log(input);\n",
  golang: "package main\n\nimport \"fmt\"\n\nfunc main() {\n    // TODO: parse stdin and print the answer\n    fmt.Println(\"\")\n}\n",
  c: "#include <stdio.h>\n\nint main(void) {\n    /* TODO: parse stdin and print the answer */\n    return 0;\n}\n",
};

const FUNCTION_STARTERS: Record<string, Partial<Record<string, string>>> = {
  "two-sum": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<int> two_sum(vector<int> nums, int target) {\n    // TODO\n    return {};\n}\n",
    java: "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // TODO\n        return new int[0];\n    }\n}\n",
    javascript: "function twoSum(nums, target) {\n  // TODO\n  return [];\n}\n",
    typescript: "function twoSum(nums: number[], target: number): number[] {\n  // TODO\n  return [];\n}\n",
    golang: "package main\n\nfunc twoSum(nums []int, target int) []int {\n\t// TODO\n\treturn []int{}\n}\n",
    c: "#include <stdlib.h>\n\nint* two_sum(int* nums, int nums_len, int target, int* return_size) {\n    // TODO\n    *return_size = 0;\n    return NULL;\n}\n",
  },
  "add-two-numbers": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<int> add_two_numbers(vector<int> l1, vector<int> l2) {\n    // TODO\n    return {};\n}\n",
    java: "class Solution {\n    public int[] addTwoNumbers(int[] l1, int[] l2) {\n        // TODO\n        return new int[0];\n    }\n}\n",
    javascript: "function addTwoNumbers(l1, l2) {\n  // TODO\n  return [];\n}\n",
    typescript: "function addTwoNumbers(l1: number[], l2: number[]): number[] {\n  // TODO\n  return [];\n}\n",
    golang: "package main\n\nfunc addTwoNumbers(l1 []int, l2 []int) []int {\n\t// TODO\n\treturn []int{}\n}\n",
    c: "#include <stdlib.h>\n\nint* add_two_numbers(int* l1, int l1_len, int* l2, int l2_len, int* return_size) {\n    // TODO\n    *return_size = 0;\n    return NULL;\n}\n",
  },
  "longest-substring-without-repeating": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nint length_of_longest_substring(string s) {\n    // TODO\n    return 0;\n}\n",
    java: "class Solution {\n    public int lengthOfLongestSubstring(String s) {\n        // TODO\n        return 0;\n    }\n}\n",
    javascript: "function lengthOfLongestSubstring(s) {\n  // TODO\n  return 0;\n}\n",
    typescript: "function lengthOfLongestSubstring(s: string): number {\n  // TODO\n  return 0;\n}\n",
    golang: "package main\n\nfunc lengthOfLongestSubstring(s string) int {\n\t// TODO\n\treturn 0\n}\n",
    c: "int length_of_longest_substring(const char* s) {\n    // TODO\n    return 0;\n}\n",
  },
  "logistic-regression-sigmoid": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\ndouble predict_probability(vector<double> weights, double bias, vector<double> features) {\n    // TODO\n    return 0.0;\n}\n",
    java: "class Solution {\n    public double predictProbability(double[] weights, double bias, double[] features) {\n        // TODO\n        return 0.0;\n    }\n}\n",
    javascript: "function predictProbability(weights, bias, features) {\n  // TODO\n  return 0;\n}\n",
    typescript: "function predictProbability(weights: number[], bias: number, features: number[]): number {\n  // TODO\n  return 0;\n}\n",
    golang: "package main\n\nfunc predictProbability(weights []float64, bias float64, features []float64) float64 {\n\t// TODO\n\treturn 0\n}\n",
    c: "double predict_probability(double* weights, int weights_len, double bias, double* features, int features_len) {\n    // TODO\n    return 0.0;\n}\n",
  },
  "knn-majority-vote": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nstring predict_knn(vector<vector<double>> points, vector<string> labels, vector<double> query, int k) {\n    // TODO\n    return \"\";\n}\n",
    java: "class Solution {\n    public String predictKnn(double[][] points, String[] labels, double[] query, int k) {\n        // TODO\n        return \"\";\n    }\n}\n",
    javascript: "function predictKnn(points, labels, query, k) {\n  // TODO\n  return \"\";\n}\n",
    typescript: "function predictKnn(points: number[][], labels: string[], query: number[], k: number): string {\n  // TODO\n  return \"\";\n}\n",
    golang: "package main\n\nfunc predictKnn(points [][]float64, labels []string, query []float64, k int) string {\n\t// TODO\n\treturn \"\"\n}\n",
  },
  "kmeans-one-iteration": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<int> assign_clusters(vector<vector<double>> points, vector<vector<double>> centroids) {\n    // TODO\n    return {};\n}\n",
    java: "class Solution {\n    public int[] assignClusters(double[][] points, double[][] centroids) {\n        // TODO\n        return new int[0];\n    }\n}\n",
    javascript: "function assignClusters(points, centroids) {\n  // TODO\n  return [];\n}\n",
    typescript: "function assignClusters(points: number[][], centroids: number[][]): number[] {\n  // TODO\n  return [];\n}\n",
    golang: "package main\n\nfunc assignClusters(points [][]float64, centroids [][]float64) []int {\n\t// TODO\n\treturn []int{}\n}\n",
  },
  "scaled-dot-product-attention": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<double> attention_row(vector<double> query, vector<vector<double>> keys, vector<vector<double>> values) {\n    // TODO\n    return {};\n}\n",
    java: "class Solution {\n    public double[] attentionRow(double[] query, double[][] keys, double[][] values) {\n        // TODO\n        return new double[0];\n    }\n}\n",
    javascript: "function attentionRow(query, keys, values) {\n  // TODO\n  return [];\n}\n",
    typescript: "function attentionRow(query: number[], keys: number[][], values: number[][]): number[] {\n  // TODO\n  return [];\n}\n",
    golang: "package main\n\nfunc attentionRow(query []float64, keys [][]float64, values [][]float64) []float64 {\n\t// TODO\n\treturn []float64{}\n}\n",
  },
  "softmax-cross-entropy": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\ndouble cross_entropy_loss(vector<double> logits, int target) {\n    // TODO\n    return 0.0;\n}\n",
    java: "class Solution {\n    public double crossEntropyLoss(double[] logits, int target) {\n        // TODO\n        return 0.0;\n    }\n}\n",
    javascript: "function crossEntropyLoss(logits, target) {\n  // TODO\n  return 0;\n}\n",
    typescript: "function crossEntropyLoss(logits: number[], target: number): number {\n  // TODO\n  return 0;\n}\n",
    golang: "package main\n\nfunc crossEntropyLoss(logits []float64, target int) float64 {\n\t// TODO\n\treturn 0\n}\n",
  },
  "attention-mask-apply": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nvector<double> masked_softmax(vector<double> scores, vector<int> mask) {\n    // TODO\n    return {};\n}\n",
    java: "class Solution {\n    public double[] maskedSoftmax(double[] scores, int[] mask) {\n        // TODO\n        return new double[0];\n    }\n}\n",
    javascript: "function maskedSoftmax(scores, mask) {\n  // TODO\n  return [];\n}\n",
    typescript: "function maskedSoftmax(scores: number[], mask: number[]): number[] {\n  // TODO\n  return [];\n}\n",
    golang: "package main\n\nfunc maskedSoftmax(scores []float64, mask []int) []float64 {\n\t// TODO\n\treturn []float64{}\n}\n",
  },
};

const VISUALS: Record<string, VisualSpec> = {
  "two-sum": {
    title: { zh: "哈希表扫描", en: "Hash Table Scan" },
    steps: {
      zh: ["读到 2，记录 2 -> 0", "读到 7，发现 9 - 7 = 2", "返回两个下标 [0,1]"],
      en: ["Read 2 and store 2 -> 0", "Read 7 and find 9 - 7 = 2", "Return indices [0,1]"],
    },
  },
  "longest-substring-without-repeating": {
    title: { zh: "滑动窗口", en: "Sliding Window" },
    steps: {
      zh: ["右指针扩张窗口", "遇到重复字符时移动左边界", "每一步更新最长长度"],
      en: ["Expand with the right pointer", "Move the left boundary on duplicate characters", "Update the best length at each step"],
    },
  },
  "logistic-regression-sigmoid": {
    title: { zh: "线性打分到概率", en: "Linear Score To Probability" },
    steps: {
      zh: ["计算 w dot x + b", "送入 sigmoid 压到 0..1", "按概率解释分类倾向"],
      en: ["Compute w dot x + b", "Apply sigmoid to squash into 0..1", "Interpret the class tendency as probability"],
    },
  },
  "knn-majority-vote": {
    title: { zh: "近邻投票", en: "Nearest Neighbor Vote" },
    steps: {
      zh: ["计算 query 到训练点距离", "取最近的 k 个点", "多数标签成为预测结果"],
      en: ["Measure distance to each training point", "Take the nearest k points", "Use the majority label as prediction"],
    },
  },
  "kmeans-one-iteration": {
    title: { zh: "样本归簇", en: "Cluster Assignment" },
    steps: {
      zh: ["固定当前中心点", "每个样本找最近中心", "输出簇编号，下一步才更新中心"],
      en: ["Keep current centroids fixed", "Find the nearest centroid for each point", "Return cluster ids before centroid update"],
    },
  },
  "scaled-dot-product-attention": {
    title: { zh: "注意力权重", en: "Attention Weights" },
    steps: {
      zh: ["query 与每个 key 点积", "缩放后 softmax 得到权重", "用权重加权 value 得到输出"],
      en: ["Dot the query with every key", "Scale and softmax to get weights", "Weight the values to produce output"],
    },
  },
  "softmax-cross-entropy": {
    title: { zh: "分类损失", en: "Classification Loss" },
    steps: {
      zh: ["logits 减最大值防止溢出", "计算 softmax 分母", "取目标类别负对数概率"],
      en: ["Subtract max logit for stability", "Compute the softmax denominator", "Take negative log probability of target"],
    },
  },
  "attention-mask-apply": {
    title: { zh: "Mask 后的注意力", en: "Masked Attention" },
    steps: {
      zh: ["屏蔽不可见位置", "只在可见分数中 softmax", "被屏蔽位置输出 0 概率"],
      en: ["Hide unavailable positions", "Softmax only visible scores", "Return probability 0 for masked positions"],
    },
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

function sampleComment(problem: AnyProblem | null | undefined, language: string): string {
  const sample = problem?.sample_testcases?.[0];
  if (!sample) return "";
  const lines = [
    "Sample input:",
    sample.input,
    "",
    "Sample output:",
    sample.output,
  ].join("\n");
  if (language === "python") return `# ${lines.replaceAll("\n", "\n# ")}\n\n`;
  if (["cpp", "java", "c", "golang", "javascript", "typescript"].includes(language)) {
    return `/*\n${lines}\n*/\n\n`;
  }
  return "";
}

export function buildStarter(problem: AnyProblem | null | undefined, language: string, mode: JudgeMode): string {
  const spec = getFunctionSpec(problem);
  if (mode === "function" && spec) return FUNCTION_STARTERS[problem?.slug ?? ""]?.[language] ?? spec.starter;
  return `${sampleComment(problem, language)}${ACM_STARTERS[language] ?? ""}`;
}

export function getLocalizedFunctionDescription(problem: AnyProblem | null | undefined, locale: Locale): string | null {
  return getFunctionSpec(problem)?.description[locale] ?? null;
}

export function getVisualSpec(problem?: AnyProblem | null): VisualSpec {
  if (!problem) {
    return {
      title: { zh: "解题流程", en: "Solving Flow" },
      steps: {
        zh: ["阅读题面", "拆分输入输出", "提交后观察公开用例"],
        en: ["Read the statement", "Separate input and output", "Run public samples before submitting"],
      },
    };
  }
  return VISUALS[problem.slug] ?? {
    title: { zh: "解题流程", en: "Solving Flow" },
    steps: {
      zh: ["先确认输入输出格式", "写出主流程", "用公开用例验证边界"],
      en: ["Confirm the I/O format", "Write the main flow", "Validate boundaries with public samples"],
    },
  };
}
