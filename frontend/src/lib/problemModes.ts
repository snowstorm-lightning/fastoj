import type { ProblemDetail, ProblemListItem } from "./schemas";
import { DEFAULT_LOCALE, localeText, localeValue, SUPPORTED_LOCALES, type Locale } from "./i18n";

export type JudgeMode = "function" | "acm";

type AnyProblem = Pick<ProblemDetail | ProblemListItem, "slug" | "title" | "tags"> & {
  sample_testcases?: Array<{
    input: string;
    output: string;
    explanation?: string | null;
    acm_input?: string | null;
    acm_output?: string | null;
    function_input?: string | null;
    function_output?: string | null;
    display_mode?: string | null;
  }>;
  mode?: string;
  function_signature?: string | null;
};

type LocalizedString = Partial<Record<Locale, string>> & { zh: string };
type LocalizedStringList = Partial<Record<Locale, string[]>> & { zh: string[] };

type FunctionSpec = {
  signature: string;
  description: LocalizedString;
  starter: string;
  dynamic?: boolean;
};

type VisualSpec = {
  title: LocalizedString;
  steps: LocalizedStringList;
};

const TODO = "    # TODO: implement your solution here\n";
const TODO_ZH = "TODO: 在这里实现你的解法";

const FUNCTION_SPECS: Record<string, FunctionSpec> = {
  "two-sum": {
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
    signature: "def addTwoNumbers(l1: ListNode | None, l2: ListNode | None) -> ListNode | None",
    description: {
      zh: "按链表节点接口补全函数体；测试输入仍以数组展示。",
      en: "Complete the linked-node function. Test input is still shown as arrays.",
    },
    starter: `# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

def addTwoNumbers(l1: ListNode | None, l2: ListNode | None) -> ListNode | None:
${TODO}    return None
`,
  },
  "longest-substring-without-repeating": {
    signature: "def length_of_longest_substring(s: str) -> int",
    description: {
      zh: "维护无重复窗口，返回最长长度。",
      en: "Maintain a non-repeating window and return the best length.",
    },
    starter: `def length_of_longest_substring(s: str) -> int:
${TODO}    return 0
`,
  },
  "valid-parentheses": {
    signature: "def is_valid_parentheses(s: str) -> bool",
    description: {
      zh: "判断括号串是否有效，提交区只需要补全函数体。",
      en: "Return whether the bracket string is valid. Only complete the function body.",
    },
    starter: `def is_valid_parentheses(s: str) -> bool:
${TODO}    return False
`,
  },
  "alien-dictionary": {
    signature: "def alienOrder(words: list[str]) -> str",
    description: {
      zh: "根据已排序单词推断外星字母顺序；矛盾时返回空字符串。",
      en: "Infer the alien letter order from sorted words; return an empty string on contradiction.",
    },
    starter: `def alienOrder(words: list[str]) -> str:
${TODO}    return ""
`,
  },
  "logistic-regression-sigmoid": {
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

FUNCTION_SPECS["longest-substring-without-repeating-characters"] =
  FUNCTION_SPECS["longest-substring-without-repeating"];

export const ACM_STARTERS: Record<string, string> = {
  python: "import sys\n\n# Read stdin and print the exact required answer.\ndata = sys.stdin.read().strip()\n# TODO: parse input and solve\nprint(data)\n",
  cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    // TODO: parse stdin and print the answer\n    return 0;\n}\n",
  java: "import java.io.*;\nimport java.util.*;\n\nclass Main {\n    public static void main(String[] args) throws Exception {\n        // TODO: parse stdin and print the answer\n    }\n}\n",
  javascript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\n// TODO: parse input and solve\nconsole.log(input);\n",
  typescript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\n// TODO: parse input and solve\nconsole.log(input);\n",
  golang: "package main\n\nimport \"fmt\"\n\nfunc main() {\n    // TODO: parse stdin and print the answer\n    fmt.Println(\"\")\n}\n",
  c: "#include <stdio.h>\n\nint main(void) {\n    /* TODO: parse stdin and print the answer */\n    return 0;\n}\n",
};

const ACM_STARTERS_ZH: Record<string, string> = {
  python: "import sys\n\n# 读取标准输入，并输出题目要求的精确答案。\ndata = sys.stdin.read().strip()\n# TODO: 解析输入并完成求解\nprint(data)\n",
  cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    // TODO: 解析标准输入并输出答案\n    return 0;\n}\n",
  java: "import java.io.*;\nimport java.util.*;\n\nclass Main {\n    public static void main(String[] args) throws Exception {\n        // TODO: 解析标准输入并输出答案\n    }\n}\n",
  javascript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\n// TODO: 解析输入并完成求解\nconsole.log(input);\n",
  typescript: "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\n// TODO: 解析输入并完成求解\nconsole.log(input);\n",
  golang: "package main\n\nimport \"fmt\"\n\nfunc main() {\n    // TODO: 解析标准输入并输出答案\n    fmt.Println(\"\")\n}\n",
  c: "#include <stdio.h>\n\nint main(void) {\n    /* TODO: 解析标准输入并输出答案 */\n    return 0;\n}\n",
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
  "valid-parentheses": {
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nbool is_valid_parentheses(string s) {\n    // TODO\n    return false;\n}\n",
    java: "class Solution {\n    public boolean isValidParentheses(String s) {\n        // TODO\n        return false;\n    }\n}\n",
    javascript: "function isValidParentheses(s) {\n  // TODO\n  return false;\n}\n",
    typescript: "function isValidParentheses(s: string): boolean {\n  // TODO\n  return false;\n}\n",
    golang: "package main\n\nfunc isValidParentheses(s string) bool {\n\t// TODO\n\treturn false\n}\n",
    c: "int is_valid_parentheses(const char* s) {\n    // TODO\n    return 0;\n}\n",
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

FUNCTION_STARTERS["longest-substring-without-repeating-characters"] =
  FUNCTION_STARTERS["longest-substring-without-repeating"];

type NodeStarterKind =
  | "list_to_list"
  | "two_lists_to_list"
  | "list_to_bool"
  | "cycle_to_bool"
  | "cycle_to_index"
  | "intersection_node_value"
  | "list_int_to_list"
  | "random_to_random"
  | "list_array_to_list"
  | "tree_to_vector"
  | "tree_to_matrix"
  | "tree_to_scalar_int"
  | "tree_to_scalar_bool"
  | "tree_int_to_scalar"
  | "tree_to_tree"
  | "array_to_tree"
  | "two_arrays_to_tree"
  | "flatten_tree"
  | "tree_lca_to_value";

type NodeStarterProfile = {
  functionName: string;
  kind: NodeStarterKind;
};

const NODE_STARTER_PROFILES: Record<string, NodeStarterProfile> = {
  "add-two-numbers": { functionName: "addTwoNumbers", kind: "two_lists_to_list" },
  "intersection-of-two-linked-lists": { functionName: "getIntersectionNode", kind: "intersection_node_value" },
  "reverse-linked-list": { functionName: "reverseList", kind: "list_to_list" },
  "palindrome-linked-list": { functionName: "isPalindrome", kind: "list_to_bool" },
  "linked-list-cycle": { functionName: "hasCycle", kind: "cycle_to_bool" },
  "linked-list-cycle-ii": { functionName: "detectCycle", kind: "cycle_to_index" },
  "merge-two-sorted-lists": { functionName: "mergeTwoLists", kind: "two_lists_to_list" },
  "remove-nth-node-from-end-of-list": { functionName: "removeNthFromEnd", kind: "list_int_to_list" },
  "swap-nodes-in-pairs": { functionName: "swapPairs", kind: "list_to_list" },
  "reverse-nodes-in-k-group": { functionName: "reverseKGroup", kind: "list_int_to_list" },
  "copy-list-with-random-pointer": { functionName: "copyRandomList", kind: "random_to_random" },
  "sort-list": { functionName: "sortList", kind: "list_to_list" },
  "merge-k-sorted-lists": { functionName: "mergeKLists", kind: "list_array_to_list" },
  "binary-tree-inorder-traversal": { functionName: "inorderTraversal", kind: "tree_to_vector" },
  "maximum-depth-of-binary-tree": { functionName: "maxDepth", kind: "tree_to_scalar_int" },
  "invert-binary-tree": { functionName: "invertTree", kind: "tree_to_tree" },
  "symmetric-tree": { functionName: "isSymmetric", kind: "tree_to_scalar_bool" },
  "diameter-of-binary-tree": { functionName: "diameterOfBinaryTree", kind: "tree_to_scalar_int" },
  "binary-tree-level-order-traversal": { functionName: "levelOrder", kind: "tree_to_matrix" },
  "convert-sorted-array-to-binary-search-tree": { functionName: "sortedArrayToBST", kind: "array_to_tree" },
  "validate-binary-search-tree": { functionName: "isValidBST", kind: "tree_to_scalar_bool" },
  "kth-smallest-element-in-a-bst": { functionName: "kthSmallest", kind: "tree_int_to_scalar" },
  "binary-tree-right-side-view": { functionName: "rightSideView", kind: "tree_to_vector" },
  "flatten-binary-tree-to-linked-list": { functionName: "flatten", kind: "flatten_tree" },
  "construct-binary-tree-from-preorder-and-inorder-traversal": { functionName: "buildTree", kind: "two_arrays_to_tree" },
  "path-sum-iii": { functionName: "pathSum", kind: "tree_int_to_scalar" },
  "lowest-common-ancestor-of-a-binary-tree": { functionName: "lowestCommonAncestor", kind: "tree_lca_to_value" },
  "binary-tree-maximum-path-sum": { functionName: "maxPathSum", kind: "tree_to_scalar_int" },
};

function nodeParams(profile: NodeStarterProfile, language: string): string {
  const name = profile.functionName;
  const pointer = language === "cpp" ? "*" : "";
  if (language === "cpp") {
    if (profile.kind === "two_lists_to_list") return "ListNode* l1, ListNode* l2";
    if (profile.kind === "intersection_node_value") return "ListNode* headA, ListNode* headB";
    if (profile.kind === "list_int_to_list") return `${name === "removeNthFromEnd" ? "ListNode* head, int n" : "ListNode* head, int k"}`;
    if (profile.kind === "list_array_to_list") return "vector<ListNode*> lists";
    if (profile.kind === "array_to_tree") return "vector<int> nums";
    if (profile.kind === "two_arrays_to_tree") return "vector<int> preorder, vector<int> inorder";
    if (profile.kind === "tree_int_to_scalar") return name === "kthSmallest" ? "TreeNode* root, int k" : "TreeNode* root, int targetSum";
    if (profile.kind === "tree_lca_to_value") return "TreeNode* root, TreeNode* p, TreeNode* q";
    return `${profile.kind.startsWith("tree") || profile.kind === "flatten_tree" ? "TreeNode" : profile.kind === "random_to_random" ? "Node" : "ListNode"}${pointer} ${profile.kind.startsWith("tree") || profile.kind === "flatten_tree" ? "root" : "head"}`;
  }
  if (language === "java") {
    if (profile.kind === "two_lists_to_list") return "ListNode l1, ListNode l2";
    if (profile.kind === "intersection_node_value") return "ListNode headA, ListNode headB";
    if (profile.kind === "list_int_to_list") return name === "removeNthFromEnd" ? "ListNode head, int n" : "ListNode head, int k";
    if (profile.kind === "list_array_to_list") return "ListNode[] lists";
    if (profile.kind === "array_to_tree") return "int[] nums";
    if (profile.kind === "two_arrays_to_tree") return "int[] preorder, int[] inorder";
    if (profile.kind === "tree_int_to_scalar") return name === "kthSmallest" ? "TreeNode root, int k" : "TreeNode root, int targetSum";
    if (profile.kind === "tree_lca_to_value") return "TreeNode root, TreeNode p, TreeNode q";
    return `${profile.kind.startsWith("tree") || profile.kind === "flatten_tree" ? "TreeNode" : profile.kind === "random_to_random" ? "Node" : "ListNode"} ${profile.kind.startsWith("tree") || profile.kind === "flatten_tree" ? "root" : "head"}`;
  }
  if (language === "golang") {
    if (profile.kind === "two_lists_to_list") return "l1 *ListNode, l2 *ListNode";
    if (profile.kind === "intersection_node_value") return "headA *ListNode, headB *ListNode";
    if (profile.kind === "list_int_to_list") return name === "removeNthFromEnd" ? "head *ListNode, n int" : "head *ListNode, k int";
    if (profile.kind === "list_array_to_list") return "lists []*ListNode";
    if (profile.kind === "array_to_tree") return "nums []int";
    if (profile.kind === "two_arrays_to_tree") return "preorder []int, inorder []int";
    if (profile.kind === "tree_int_to_scalar") return name === "kthSmallest" ? "root *TreeNode, k int" : "root *TreeNode, targetSum int";
    if (profile.kind === "tree_lca_to_value") return "root *TreeNode, p *TreeNode, q *TreeNode";
    return `${profile.kind.startsWith("tree") || profile.kind === "flatten_tree" ? "root *TreeNode" : profile.kind === "random_to_random" ? "head *Node" : "head *ListNode"}`;
  }
  if (language === "c") {
    if (profile.kind === "two_lists_to_list") return "struct ListNode* l1, struct ListNode* l2";
    if (profile.kind === "intersection_node_value") return "struct ListNode* headA, struct ListNode* headB";
    if (profile.kind === "list_int_to_list") return name === "removeNthFromEnd" ? "struct ListNode* head, int n" : "struct ListNode* head, int k";
    if (profile.kind === "list_array_to_list") return "struct ListNode** lists, int listsSize";
    if (profile.kind === "array_to_tree") return "int* nums, int numsSize";
    if (profile.kind === "two_arrays_to_tree") return "int* preorder, int preorderSize, int* inorder, int inorderSize";
    if (profile.kind === "tree_int_to_scalar") return name === "kthSmallest" ? "struct TreeNode* root, int k" : "struct TreeNode* root, int targetSum";
    if (profile.kind === "tree_lca_to_value") return "struct TreeNode* root, struct TreeNode* p, struct TreeNode* q";
    if (profile.kind === "tree_to_vector") return "struct TreeNode* root, int* returnSize";
    if (profile.kind === "tree_to_matrix") return "struct TreeNode* root, int* returnSize, int** returnColumnSizes";
    return `${profile.kind.startsWith("tree") || profile.kind === "flatten_tree" ? "struct TreeNode* root" : profile.kind === "random_to_random" ? "struct Node* head" : "struct ListNode* head"}`;
  }
  if (profile.kind === "two_lists_to_list") return "l1, l2";
  if (profile.kind === "intersection_node_value") return "headA, headB";
  if (profile.kind === "list_int_to_list") return name === "removeNthFromEnd" ? "head, n" : "head, k";
  if (profile.kind === "list_array_to_list") return "lists";
  if (profile.kind === "array_to_tree") return "nums";
  if (profile.kind === "two_arrays_to_tree") return "preorder, inorder";
  if (profile.kind === "tree_int_to_scalar") return name === "kthSmallest" ? "root, k" : "root, targetSum";
  if (profile.kind === "tree_lca_to_value") return "root, p, q";
  return profile.kind.startsWith("tree") || profile.kind === "flatten_tree" ? "root" : "head";
}

function nodeReturn(profile: NodeStarterProfile, language: string): string {
  const kind = profile.kind;
  if (language === "cpp") {
    if (kind === "list_to_bool" || kind === "cycle_to_bool" || kind === "tree_to_scalar_bool") return "bool";
    if (kind === "tree_to_scalar_int" || kind === "tree_int_to_scalar") return "int";
    if (kind === "tree_to_vector") return "vector<int>";
    if (kind === "tree_to_matrix") return "vector<vector<int>>";
    if (kind === "flatten_tree") return "void";
    if (kind.includes("tree")) return "TreeNode*";
    return kind === "random_to_random" ? "Node*" : "ListNode*";
  }
  if (language === "java") {
    if (kind === "list_to_bool" || kind === "cycle_to_bool" || kind === "tree_to_scalar_bool") return "boolean";
    if (kind === "tree_to_scalar_int" || kind === "tree_int_to_scalar") return "int";
    if (kind === "tree_to_vector") return "int[]";
    if (kind === "tree_to_matrix") return "int[][]";
    if (kind === "flatten_tree") return "void";
    if (kind.includes("tree")) return "TreeNode";
    return kind === "random_to_random" ? "Node" : "ListNode";
  }
  if (language === "golang") {
    if (kind === "list_to_bool" || kind === "cycle_to_bool" || kind === "tree_to_scalar_bool") return "bool";
    if (kind === "tree_to_scalar_int" || kind === "tree_int_to_scalar") return "int";
    if (kind === "tree_to_vector") return "[]int";
    if (kind === "tree_to_matrix") return "[][]int";
    if (kind === "flatten_tree") return "";
    if (kind.includes("tree")) return "*TreeNode";
    return kind === "random_to_random" ? "*Node" : "*ListNode";
  }
  if (language === "c") {
    if (kind === "list_to_bool" || kind === "cycle_to_bool" || kind === "tree_to_scalar_bool" || kind === "tree_to_scalar_int" || kind === "tree_int_to_scalar") return "int";
    if (kind === "tree_to_vector") return "int*";
    if (kind === "tree_to_matrix") return "int**";
    if (kind === "flatten_tree") return "void";
    if (kind.includes("tree")) return "struct TreeNode*";
    return kind === "random_to_random" ? "struct Node*" : "struct ListNode*";
  }
  if (kind === "list_to_bool" || kind === "cycle_to_bool" || kind === "tree_to_scalar_bool") return "boolean";
  if (kind === "tree_to_scalar_int" || kind === "tree_int_to_scalar") return "number";
  if (kind === "tree_to_vector") return "number[]";
  if (kind === "tree_to_matrix") return "number[][]";
  if (kind === "flatten_tree") return "void";
  if (kind.includes("tree")) return "TreeNode | null";
  return kind === "random_to_random" ? "Node | null" : "ListNode | null";
}

function nodeDefault(profile: NodeStarterProfile, language: string): string {
  const returnType = nodeReturn(profile, language);
  if (returnType === "void" || returnType === "") return "";
  if (["bool", "boolean"].includes(returnType)) return language === "python" ? "False" : "false";
  if (returnType === "int" || returnType === "number") return "0";
  if (returnType.includes("[]") || returnType.startsWith("vector")) {
    if (language === "java") return returnType === "int[][]" ? "new int[0][0]" : "new int[0]";
    if (language === "golang") return `${returnType}{}`;
    if (language === "c") return "NULL";
    return "[]";
  }
  if (language === "golang") return "nil";
  if (language === "c") return "NULL";
  if (language === "cpp") return "nullptr";
  if (language === "java") return "null";
  return "null";
}

function buildNodeStarter(slug: string | undefined, language: string, locale: Locale): string | null {
  const profile = slug ? NODE_STARTER_PROFILES[slug] : undefined;
  if (!profile) return null;
  const todoLine = localeText(locale, { zh: TODO_ZH, en: "TODO" });
  const params = nodeParams(profile, language);
  const returnType = nodeReturn(profile, language);
  const defaultValue = nodeDefault(profile, language);
  const returnLine = defaultValue ? `return ${defaultValue};` : "";
  if (language === "python") {
    const className = profile.kind.startsWith("tree") || profile.kind === "flatten_tree" || profile.kind === "array_to_tree" || profile.kind === "two_arrays_to_tree" ? "TreeNode" : profile.kind === "random_to_random" ? "Node" : "ListNode";
    const classComment = className === "TreeNode"
      ? "# Definition for a binary tree node.\n# class TreeNode:\n#     def __init__(self, val=0, left=None, right=None):\n#         self.val = val\n#         self.left = left\n#         self.right = right"
      : className === "Node"
        ? "# Definition for a Node.\n# class Node:\n#     def __init__(self, x: int, next: 'Node' = None, random: 'Node' = None):\n#         self.val = int(x)\n#         self.next = next\n#         self.random = random"
        : "# Definition for singly-linked list.\n# class ListNode:\n#     def __init__(self, val=0, next=None):\n#         self.val = val\n#         self.next = next";
    const pyReturn = returnType === "boolean" ? "bool" : returnType === "number" ? "int" : returnType.replace(" | null", " | None").replace("number[]", "list[int]").replace("number[][]", "list[list[int]]");
    const annotation = pyReturn === "void" ? "" : ` -> ${pyReturn}`;
    return `${classComment}\n\ndef ${profile.functionName}(${params})${annotation}:\n    # ${todoLine}${returnLine ? `\n    ${returnLine.replace("null", "None").replace("false", "False")}` : ""}\n`;
  }
  if (language === "cpp") {
    return `// Definition for singly-linked list / binary tree nodes is provided by the judge.\nclass Solution {\npublic:\n    ${returnType} ${profile.functionName}(${params}) {\n        // ${todoLine}${returnLine ? `\n        ${returnLine}` : ""}\n    }\n};\n`;
  }
  if (language === "java") {
    return `// Definition for ListNode / TreeNode / Node is provided by the judge.\nclass Solution {\n    public ${returnType} ${profile.functionName}(${params}) {\n        // ${todoLine}${returnLine ? `\n        ${returnLine}` : ""}\n    }\n}\n`;
  }
  if (language === "javascript") {
    return `function ${profile.functionName}(${params}) {\n  // ${todoLine}${returnLine ? `\n  ${returnLine}` : ""}\n}\n`;
  }
  if (language === "typescript") {
    const tsParams = params.split(", ").filter(Boolean).map((param) => `${param}: any`).join(", ");
    return `function ${profile.functionName}(${tsParams}): ${returnType} {\n  // ${todoLine}${returnLine ? `\n  ${returnLine}` : ""}\n}\n`;
  }
  if (language === "golang") {
    const returnSuffix = returnType ? ` ${returnType}` : "";
    return `package main\n\nfunc ${profile.functionName}(${params})${returnSuffix} {\n\t// ${todoLine}${returnLine ? `\n\t${returnLine}` : ""}\n}\n`;
  }
  if (language === "c") {
    return `${returnType} ${profile.functionName}(${params}) {\n    /* ${todoLine} */${returnLine ? `\n    ${returnLine}` : ""}\n}\n`;
  }
  return null;
}

type ParameterSpec = {
  name: string;
  annotation: string;
};

type ParsedFunctionSignature = {
  functionName: string;
  params: ParameterSpec[];
  returnType: string;
};

function splitTopLevel(text: string, separator: string): string[] {
  const parts: string[] = [];
  let start = 0;
  let depth = 0;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if ("([{".includes(char)) depth += 1;
    else if (")]}".includes(char) && depth > 0) depth -= 1;
    else if (char === separator && depth === 0) {
      parts.push(text.slice(start, index));
      start = index + 1;
    }
  }
  parts.push(text.slice(start));
  return parts;
}

function parseFunctionSignature(signature: string): ParsedFunctionSignature {
  const cleaned = signature.replace(/:\s*$/, "").trim();
  const match = cleaned.match(/^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([\s\S]*?)\)\s*(?:->\s*(.+))?$/);
  if (!match) {
    return { functionName: "solve", params: [], returnType: "None" };
  }
  const params = splitTopLevel(match[2], ",")
    .map((part) => part.trim())
    .filter(Boolean)
    .filter((part) => !part.startsWith("*"))
    .map((part) => {
      const left = part.split("=", 1)[0].trim();
      const [rawName, rawAnnotation] = left.split(":").map((item) => item.trim());
      return { name: rawName, annotation: rawAnnotation || "Any" };
    })
    .filter((param) => param.name !== "self" && param.name !== "cls" && /^[A-Za-z_][A-Za-z0-9_]*$/.test(param.name));
  return {
    functionName: match[1],
    params,
    returnType: (match[3] ?? "None").trim(),
  };
}

function toCamelCase(name: string): string {
  return name.replace(/_([a-zA-Z0-9])/g, (_, char: string) => char.toUpperCase());
}

function compactAnnotation(annotation: string): string {
  return annotation.trim().replace(/\s+/g, " ");
}

function withoutTopLevelNone(annotation: string): { annotation: string; nullable: boolean } {
  const parts = splitTopLevel(compactAnnotation(annotation), "|").map((part) => part.trim()).filter(Boolean);
  const concrete = parts.filter((part) => !["none", "null"].includes(part.toLowerCase()));
  return {
    annotation: concrete[0] ?? "None",
    nullable: concrete.length !== parts.length,
  };
}

function listInner(annotation: string): string | null {
  const { annotation: concrete } = withoutTopLevelNone(annotation);
  const match = concrete.match(/^(?:list|List|Sequence|tuple|Tuple)\[(.*)\]$/);
  return match ? match[1].trim() : null;
}

function isNoneType(annotation: string): boolean {
  return ["none", "null", "void"].includes(compactAnnotation(annotation).toLowerCase());
}

function tsType(annotation: string): string {
  const { annotation: concrete, nullable } = withoutTopLevelNone(annotation);
  const inner = listInner(concrete);
  let type: string;
  if (inner) {
    const innerType = tsType(inner);
    type = innerType.includes("|") ? `Array<${innerType}>` : `${innerType}[]`;
  } else {
    const key = concrete.toLowerCase();
    if (key === "int" || key === "float") type = "number";
    else if (key === "bool") type = "boolean";
    else if (key === "str") type = "string";
    else if (isNoneType(key)) type = "void";
    else if (key === "list") type = "unknown[]";
    else type = "unknown";
  }
  return nullable && type !== "void" ? `${type} | null` : type;
}

function jsDefault(annotation: string): string {
  const { annotation: concrete, nullable } = withoutTopLevelNone(annotation);
  if (nullable || isNoneType(concrete)) return "null";
  if (listInner(concrete) || concrete.toLowerCase() === "list") return "[]";
  const key = concrete.toLowerCase();
  if (key === "bool") return "false";
  if (key === "str") return "\"\"";
  if (key === "dict") return "{}";
  return "0";
}

function cppType(annotation: string): string {
  const { annotation: concrete, nullable } = withoutTopLevelNone(annotation);
  const inner = listInner(concrete);
  let type: string;
  if (inner) type = `vector<${cppType(inner)}>`;
  else {
    const key = concrete.toLowerCase();
    if (key === "int") type = "int";
    else if (key === "float") type = "double";
    else if (key === "bool") type = "bool";
    else if (key === "str") type = "string";
    else if (isNoneType(key)) type = "void";
    else if (key === "list") type = "vector<int>";
    else type = "int";
  }
  return nullable && type !== "void" ? `optional<${type}>` : type;
}

function cppDefault(annotation: string): string {
  const type = cppType(annotation);
  if (type === "void") return "";
  if (type === "bool") return "false";
  if (type === "string") return "\"\"";
  if (type === "double") return "0.0";
  if (type.startsWith("optional<")) return "nullopt";
  if (type.startsWith("vector<")) return "{}";
  return "0";
}

function javaType(annotation: string): string {
  const { annotation: concrete, nullable } = withoutTopLevelNone(annotation);
  const inner = listInner(concrete);
  if (inner) return `${javaType(inner)}[]`;
  const key = concrete.toLowerCase();
  if (key === "int") return nullable ? "Integer" : "int";
  if (key === "float") return nullable ? "Double" : "double";
  if (key === "bool") return nullable ? "Boolean" : "boolean";
  if (key === "str") return "String";
  if (isNoneType(key)) return "void";
  if (key === "list") return "Object[]";
  return "Object";
}

function javaDefault(type: string): string {
  if (type === "void") return "";
  if (type === "boolean") return "false";
  if (type === "int") return "0";
  if (type === "double") return "0.0";
  if (type === "String") return "\"\"";
  if (type.endsWith("[][]")) return `new ${type.replaceAll("[]", "")}[0][0]`;
  if (type.endsWith("[]")) return `new ${type.slice(0, -2)}[0]`;
  return "null";
}

function goType(annotation: string): string {
  const { annotation: concrete, nullable } = withoutTopLevelNone(annotation);
  const inner = listInner(concrete);
  let type: string;
  if (inner) type = `[]${goType(inner)}`;
  else {
    const key = concrete.toLowerCase();
    if (key === "int") type = "int";
    else if (key === "float") type = "float64";
    else if (key === "bool") type = "bool";
    else if (key === "str") type = "string";
    else if (isNoneType(key)) type = "";
    else if (key === "list") type = "[]interface{}";
    else type = "interface{}";
  }
  return nullable && type && !type.startsWith("[]") ? `*${type}` : type;
}

function goDefault(annotation: string): string {
  const type = goType(annotation);
  if (!type) return "";
  if (type === "bool") return "false";
  if (type === "string") return "\"\"";
  if (type === "float64") return "0.0";
  if (type.startsWith("[]")) return `${type}{}`;
  if (type.startsWith("*") || type === "interface{}") return "nil";
  return "0";
}

function cScalarType(annotation: string): string {
  const { annotation: concrete } = withoutTopLevelNone(annotation);
  const key = concrete.toLowerCase();
  if (key === "float") return "double";
  if (key === "str") return "const char*";
  if (key === "bool") return "int";
  if (key === "int") return "int";
  if (isNoneType(key)) return "void";
  return "int";
}

function cValueType(annotation: string): string {
  const type = cScalarType(annotation);
  return type === "const char*" ? "char*" : type;
}

function cListInner(annotation: string): string | null {
  const inner = listInner(annotation);
  if (inner) return inner;
  const { annotation: concrete } = withoutTopLevelNone(annotation);
  return concrete.toLowerCase() === "list" ? "int" : null;
}

function cPointerType(baseType: string, dimensions: number): string {
  return `${baseType}${"*".repeat(dimensions)}`;
}

function cParams(params: ParameterSpec[]): string {
  return params.flatMap((param) => {
    const firstInner = cListInner(param.annotation);
    const secondInner = firstInner ? cListInner(firstInner) : null;
    if (firstInner && secondInner) {
      const nullable = withoutTopLevelNone(secondInner).nullable;
      return nullable
        ? [`${cPointerType(cValueType(secondInner), 2)} ${param.name}`, `int** ${param.name}_is_null`, `int ${param.name}_rows`, `int* ${param.name}_cols`]
        : [`${cPointerType(cValueType(secondInner), 2)} ${param.name}`, `int ${param.name}_rows`, `int* ${param.name}_cols`];
    }
    if (firstInner) {
      const nullable = withoutTopLevelNone(firstInner).nullable;
      return nullable
        ? [`${cPointerType(cValueType(firstInner), 1)} ${param.name}`, `int* ${param.name}_is_null`, `int ${param.name}_len`]
        : [`${cPointerType(cValueType(firstInner), 1)} ${param.name}`, `int ${param.name}_len`];
    }
    if (withoutTopLevelNone(param.annotation).nullable) {
      return [`${cScalarType(param.annotation)} ${param.name}`, `int ${param.name}_is_null`];
    }
    return [`${cScalarType(param.annotation)} ${param.name}`];
  }).join(", ");
}

function cReturnSignature(parsed: ParsedFunctionSignature, functionName: string): { signature: string; defaultBody: string } {
  const params = cParams(parsed.params);
  const firstInner = cListInner(parsed.returnType);
  const secondInner = firstInner ? cListInner(firstInner) : null;
  if (firstInner && secondInner) {
    const base = cValueType(secondInner);
    const returnType = cPointerType(base, 2);
    const nullable = withoutTopLevelNone(secondInner).nullable;
    const returnParams = nullable
      ? "int* return_size, int** return_column_sizes, int*** return_nulls"
      : "int* return_size, int** return_column_sizes";
    const allParams = params ? `${params}, ${returnParams}` : returnParams;
    return {
      signature: `${returnType} ${functionName}(${allParams})`,
      defaultBody: nullable
        ? "    *return_size = 0;\n    *return_column_sizes = NULL;\n    *return_nulls = NULL;\n    return NULL;"
        : "    *return_size = 0;\n    *return_column_sizes = NULL;\n    return NULL;",
    };
  }
  if (firstInner) {
    const base = cValueType(firstInner);
    const returnType = cPointerType(base, 1);
    const nullable = withoutTopLevelNone(firstInner).nullable;
    const returnParams = nullable ? "int* return_size, int** return_nulls" : "int* return_size";
    const allParams = params ? `${params}, ${returnParams}` : returnParams;
    return {
      signature: `${returnType} ${functionName}(${allParams})`,
      defaultBody: nullable
        ? "    *return_size = 0;\n    *return_nulls = NULL;\n    return NULL;"
        : "    *return_size = 0;\n    return NULL;",
    };
  }
  const returnType = cScalarType(parsed.returnType);
  if (returnType === "void") return { signature: `void ${functionName}(${params || "void"})`, defaultBody: "" };
  const nullable = withoutTopLevelNone(parsed.returnType).nullable;
  if (nullable) {
    const allParams = params ? `${params}, int* return_is_null` : "int* return_is_null";
    const defaultValue = returnType === "double" ? "0.0" : returnType === "const char*" ? "\"\"" : "0";
    return { signature: `${returnType} ${functionName}(${allParams})`, defaultBody: `    *return_is_null = 1;\n    return ${defaultValue};` };
  }
  const defaultValue = returnType === "double" ? "0.0" : returnType === "const char*" ? "\"\"" : "0";
  return { signature: `${returnType} ${functionName}(${params || "void"})`, defaultBody: `    return ${defaultValue};` };
}

function localizeFunctionStarter(starter: string, locale: Locale): string {
  const todoText = localeText(locale, { zh: TODO_ZH, en: "TODO" });
  if (todoText === "TODO") return starter;
  return starter
    .replace(/# TODO: implement your solution here/g, `# ${todoText}`)
    .replace(/\/\/ TODO(?:: implement your solution here)?/g, `// ${todoText}`)
    .replace(/\/\* TODO(?:: implement your solution here)? \*\//g, `/* ${todoText} */`);
}

function buildDynamicFunctionStarter(spec: FunctionSpec, language: string, locale: Locale): string {
  const parsed = parseFunctionSignature(spec.signature);
  const snakeName = parsed.functionName;
  const camelName = toCamelCase(snakeName);
  const todoLine = localeText(locale, { zh: TODO_ZH, en: "TODO" });
  if (language === "python") return localizeFunctionStarter(spec.starter, locale);
  if (language === "javascript") {
    return `function ${camelName}(${parsed.params.map((param) => param.name).join(", ")}) {\n  // ${todoLine}\n  return ${jsDefault(parsed.returnType)};\n}\n`;
  }
  if (language === "typescript") {
    const params = parsed.params.map((param) => `${param.name}: ${tsType(param.annotation)}`).join(", ");
    const returnType = tsType(parsed.returnType);
    const returnLine = returnType === "void" ? "" : `\n  return ${jsDefault(parsed.returnType)};`;
    return `function ${camelName}(${params}): ${returnType} {\n  // ${todoLine}${returnLine}\n}\n`;
  }
  if (language === "cpp") {
    const params = parsed.params.map((param) => `${cppType(param.annotation)} ${param.name}`).join(", ");
    const returnType = cppType(parsed.returnType);
    const defaultValue = cppDefault(parsed.returnType);
    const returnLine = returnType === "void" ? "" : `\n    return ${defaultValue};`;
    return `#include <bits/stdc++.h>\nusing namespace std;\n\n${returnType} ${snakeName}(${params}) {\n    // ${todoLine}${returnLine}\n}\n`;
  }
  if (language === "java") {
    const params = parsed.params.map((param) => `${javaType(param.annotation)} ${param.name}`).join(", ");
    const returnType = javaType(parsed.returnType);
    const defaultValue = javaDefault(returnType);
    const returnLine = returnType === "void" ? "" : `\n        return ${defaultValue};`;
    return `class Solution {\n    public ${returnType} ${camelName}(${params}) {\n        // ${todoLine}${returnLine}\n    }\n}\n`;
  }
  if (language === "golang") {
    const params = parsed.params.map((param) => `${param.name} ${goType(param.annotation)}`).join(", ");
    const returnType = goType(parsed.returnType);
    const defaultValue = goDefault(parsed.returnType);
    const returnSuffix = returnType ? ` ${returnType}` : "";
    const returnLine = returnType ? `\n\treturn ${defaultValue}` : "";
    return `package main\n\nfunc ${camelName}(${params})${returnSuffix} {\n\t// ${todoLine}${returnLine}\n}\n`;
  }
  if (language === "c") {
    const { signature, defaultBody } = cReturnSignature(parsed, snakeName);
    const returnLine = defaultBody ? `\n${defaultBody}` : "";
    return `#include <stdlib.h>\n\n${signature} {\n    // ${todoLine}${returnLine}\n}\n`;
  }
  return localizeFunctionStarter(spec.starter, locale);
}

function defaultReturnForSignature(signature: string): string {
  const returnType = signature.split("->")[1]?.trim().toLowerCase() ?? "";
  if (returnType.startsWith("bool")) return "False";
  if (returnType.startsWith("int")) return "0";
  if (returnType.startsWith("float")) return "0.0";
  if (returnType.startsWith("str")) return "\"\"";
  if (returnType.startsWith("dict")) return "{}";
  if (returnType.startsWith("list")) return "[]";
  return "None";
}

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
  "alien-dictionary": {
    title: { zh: "拓扑排序", en: "Topological Sort" },
    steps: {
      zh: ["比较相邻单词首个不同字符", "把字母先后关系建成有向图", "入度为 0 的字母依次出队生成顺序"],
      en: ["Compare the first differing character in adjacent words", "Build directed precedence edges", "Pop zero-indegree letters to produce the order"],
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

VISUALS["longest-substring-without-repeating-characters"] =
  VISUALS["longest-substring-without-repeating"];

export function getFunctionSpec(problem?: AnyProblem | null): FunctionSpec | null {
  if (!problem) return null;
  const fixed = FUNCTION_SPECS[problem.slug];
  if (fixed) return fixed;
  if ((problem.mode === "function" || problem.mode === "both") && problem.function_signature) {
    const signature = problem.function_signature.replace(/:\s*$/, "");
    return {
      signature,
      description: {
        zh: "按函数签名补全函数体；测试数据使用 JSON-line 参数输入。",
        en: "Complete the function body. Test data is provided as JSON-line arguments.",
      },
      starter: `${signature}:\n${TODO}    return ${defaultReturnForSignature(signature)}\n`,
      dynamic: true,
    };
  }
  return null;
}

export function getProblemMode(problem?: AnyProblem | null) {
  const functionSpec = getFunctionSpec(problem);
  const tags = problem?.tags ?? [];
  const isAiPractice = tags.some((tag) => ["AI", "ML", "Deep Learning"].includes(tag));
  const supportsFunction = Boolean(functionSpec);
  const sampleSupportsAcm = Boolean(
    problem?.sample_testcases?.some((testcase) => {
      if (testcase.display_mode === "acm") return true;
      return Boolean(testcase.acm_input);
    }),
  );
  const isAcmPrimary = problem?.mode === "acm";
  const hasSampleMetadata = Array.isArray(problem?.sample_testcases);
  const supportsAcm = isAcmPrimary || (problem?.mode === "both" && (!hasSampleMetadata || sampleSupportsAcm));
  return {
    defaultMode: functionSpec ? "function" as JudgeMode : "acm" as JudgeMode,
    supportsFunction,
    supportsAcm,
    isAiPractice,
    functionSpec,
  };
}

function sampleComment(problem: AnyProblem | null | undefined, language: string, locale: Locale): string {
  const sample = problem?.sample_testcases?.[0];
  if (!sample) return "";
  const inputLabel = localeText(locale, { zh: "示例输入：", en: "Sample input:" });
  const outputLabel = localeText(locale, { zh: "示例输出：", en: "Sample output:" });
  const lines = [
    inputLabel,
    sample.input,
    "",
    outputLabel,
    sample.output,
  ].join("\n");
  if (language === "python") return `# ${lines.replaceAll("\n", "\n# ")}\n\n`;
  if (["cpp", "java", "c", "golang", "javascript", "typescript"].includes(language)) {
    return `/*\n${lines}\n*/\n\n`;
  }
  return "";
}

export function buildStarter(problem: AnyProblem | null | undefined, language: string, mode: JudgeMode, locale: Locale = DEFAULT_LOCALE): string {
  const spec = getFunctionSpec(problem);
  if (mode === "function" && spec) {
    const nodeStarter = buildNodeStarter(problem?.slug, language, locale);
    if (nodeStarter) return localizeFunctionStarter(nodeStarter, locale);
    const fixedStarter = FUNCTION_STARTERS[problem?.slug ?? ""]?.[language];
    return localizeFunctionStarter(fixedStarter ?? buildDynamicFunctionStarter(spec, language, locale), locale);
  }
  const starter = localeText(locale, {
    zh: ACM_STARTERS_ZH[language] ?? ACM_STARTERS[language] ?? "",
    en: ACM_STARTERS[language] ?? "",
  });
  return `${sampleComment(problem, language, locale)}${starter ?? ""}`;
}

function normalizedCode(code: string): string {
  return code.replace(/\r\n/g, "\n").trim();
}

export function isStarterCode(problem: AnyProblem | null | undefined, language: string, mode: JudgeMode, code: string): boolean {
  const normalized = normalizedCode(code);
  if (!normalized) return false;
  return SUPPORTED_LOCALES.some((locale) => normalizedCode(buildStarter(problem, language, mode, locale)) === normalized);
}

export function isLikelyStaleAcmDraft(problem: AnyProblem | null | undefined, language: string, code: string): boolean {
  if (isStarterCode(problem, language, "acm", code)) return true;
  if (language !== "python") return false;
  const normalized = normalizedCode(code);
  return /\bimport\s+sys\b/.test(normalized)
    && /sys\.stdin\.read\(\)\.strip\(\)/.test(normalized)
    && /\bprint\(\s*data\s*\)/.test(normalized);
}

export function getLocalizedFunctionDescription(problem: AnyProblem | null | undefined, locale: Locale): string | null {
  const description = getFunctionSpec(problem)?.description;
  return description ? localeValue(locale, description) : null;
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
