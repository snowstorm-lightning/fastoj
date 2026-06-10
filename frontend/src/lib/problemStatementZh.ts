import type { ProblemDetail, ProblemListItem } from "./schemas";

type StatementProblem = Pick<ProblemDetail | ProblemListItem, "slug">;

const OLD_GENERATED_MARKERS = [
  "函数契约",
  "参数说明",
  "返回要求",
  "评测与表示约定",
  "需要覆盖的边界情况",
];

const SLUG_DETAILS: Record<string, string[]> = {
  "two-sum": [
    "需要选择数组中两个不同位置的数，使它们的和等于目标值。题目保证存在一组有效答案，因此答案就是这两个位置的 0 基下标。",
  ],
  "add-two-numbers": [
    "两个数组都按从低位到高位保存一个非负整数，也就是下标 0 是个位。按竖式加法逐位相加，并把进位带到下一位。",
  ],
  "longest-substring-without-repeating-characters": [
    "子串必须是原字符串中的连续片段。目标是找到最长的一段，使这一段内部没有任何字符出现两次。",
  ],
  "valid-parentheses": [
    "一个括号串合法，当且仅当每个左括号都被同类型右括号关闭，并且关闭顺序与打开顺序相反。",
  ],
  "maximum-subarray": [
    "子数组必须非空，并且由连续位置组成。数组里可以有负数，所以最优答案也可能只包含一个元素。",
  ],
  "group-anagrams": [
    "两个字符串如果每种字符的出现次数完全相同，就属于同一组。为了让答案稳定，每组内部按字典序排列，所有分组再按组内第一个字符串排序。",
  ],
  "merge-intervals": [
    "区间包含左右端点。两个区间只要重叠或端点相接，就合并为一个覆盖二者范围的新区间。",
  ],
  "climbing-stairs": [
    "统计的是不同的走法序列，而不只是步数总和。例如先走 1 阶再走 2 阶，与先走 2 阶再走 1 阶是两种走法。",
  ],
  "container-with-most-water": [
    "选择两条竖线后，容器宽度是它们的下标距离，高度由较短的那条线决定。目标是让宽度乘高度最大。",
  ],
  "logistic-regression-sigmoid": [
    "先把每个权重和对应特征相乘并求和，再加上偏置，得到线性得分。最后用 sigmoid 把这个得分转换为 0 到 1 之间的概率。",
  ],
  "knn-majority-vote": [
    "样本之间的远近按欧氏距离判断，使用平方距离排序也等价。距离相同优先选择原下标更小的样本；投票数相同优先选择字典序更小的标签。",
  ],
  "kmeans-one-iteration": [
    "本题只做 k-means 的分配步骤。对每个点找到距离最近的中心点，并记录该中心点的 0 基编号；距离相同选编号更小的中心点。",
  ],
  "scaled-dot-product-attention": [
    "每个 key 的分数等于 query 与 key 的点积除以向量维度的平方根。对这些分数做 softmax 后，用得到的权重对 value 向量加权求和。",
  ],
  "softmax-cross-entropy": [
    "logits 是未归一化的类别分数。先通过 softmax 得到类别概率，再取目标类别概率的负对数作为损失。",
  ],
  "attention-mask-apply": [
    "只有 mask 标记为可见的位置参与 softmax。被屏蔽的位置不分配概率，最终概率保持为 0。",
  ],
  "longest-consecutive-sequence": [
    "连续指的是数值上相差 1，和这些数在原数组中的位置无关。要找的是最长的 x、x+1、x+2 这样的数值连续段。",
  ],
  "move-zeroes": [
    "所有非零元素必须保持原来的相对顺序。数组长度不变，剩余位置全部由 0 填在末尾。",
  ],
  "3sum": [
    "一个有效三元组使用三个不同下标，且三个值之和为 0。相同值组合只保留一次，三元组内部和外层结果都按稳定顺序组织。",
  ],
  "trapping-rain-water": [
    "某个位置能接多少水，取决于它左侧最高墙和右侧最高墙中较矮的那个。把每个位置能接的水量加起来就是答案。",
  ],
  "find-all-anagrams-in-a-string": [
    "只检查长度与 p 相同的连续子串。一个匹配子串需要和 p 拥有完全相同的字符计数，答案按起始下标从小到大排列。",
  ],
  "subarray-sum-equals-k": [
    "子数组是连续片段。需要统计所有元素和恰好为 k 的片段数量，片段之间可以重叠。",
  ],
  "sliding-window-maximum": [
    "第一个窗口覆盖前 k 个元素，之后每次向右移动一格。按从左到右的窗口顺序，给出每个窗口中的最大值。",
  ],
  "minimum-window-substring": [
    "窗口必须包含 t 中每个字符需要的次数。如果有多个最短窗口，选择起点最靠前的那个；如果不存在这样的窗口，结果为空字符串。",
  ],
  "rotate-array": [
    "向右轮转表示每个元素向数组末尾方向移动 k 个位置，越过末尾的元素从开头继续出现。k 大于数组长度时，只需要考虑取模后的步数。",
  ],
  "product-of-array-except-self": [
    "对每个位置，计算除当前位置以外所有元素的乘积。不能依赖除法，因此包含 0 的数组也必须得到正确结果。",
  ],
  "first-missing-positive": [
    "答案是从 1 开始第一个没有出现在数组中的正整数。0、负数和特别大的数不会直接填补这个最小正数空缺。",
  ],
  "set-matrix-zeroes": [
    "哪些行列需要置零，只由原始矩阵中的 0 决定。更新过程中写出的新 0 不应该继续影响其他行列。",
  ],
  "spiral-matrix": [
    "从左上角开始，沿当前外圈按顺时针方向走完一圈；然后收缩到内层，重复这个过程，直到每个单元格都访问一次。",
  ],
  "rotate-image": [
    "把矩阵当作图像顺时针旋转 90 度：原来的第一行会变成最后一列，原来的最后一列会变成最后一行。",
  ],
  "search-a-2d-matrix-ii": [
    "矩阵的行和列都有序，因此每次比较后可以排除一整行或一整列。问题只关心目标值是否至少出现一次。",
  ],
  "intersection-of-two-linked-lists": [
    "函数会收到两个链表头节点 headA 和 headB。样例数组用于构造链表；相交表示两条链表真实共享同一段尾部节点。返回公共尾部的第一个节点；如果没有公共节点，返回 null。",
  ],
  "reverse-linked-list": [
    "函数会收到链表头节点 head。需要原地或新建节点反转 next 指针并返回新的头节点；样例数组只是按从头到尾展示节点值。",
  ],
  "palindrome-linked-list": [
    "如果从头到尾读取的节点值序列，与从尾到头读取的序列完全一致，这个链表就是回文链表。",
  ],
  "linked-list-cycle": [
    "pos 表示尾节点会连回列表中的哪个下标。pos 为 -1 表示尾节点不再指向任何已有节点，因此无环。",
  ],
  "linked-list-cycle-ii": [
    "如果存在环，入环点是从头节点沿 next 指针前进时第一个会再次进入循环的节点。平台会把你返回的节点显示成样例中的 pos 下标。",
  ],
  "merge-two-sorted-lists": [
    "两个输入链表已经按非降序排列。合并后需要保留两个链表里的所有值，包括重复值，并形成一个新的非降序序列。",
  ],
  "remove-nth-node-from-end-of-list": [
    "从尾部计数要删除的节点：n = 1 删除最后一个节点，n = 2 删除倒数第二个节点，以此类推。",
  ],
  "swap-nodes-in-pairs": [
    "依次交换第 1 个和第 2 个节点、第 3 个和第 4 个节点。最后如果剩下单独一个节点，它保持原位。",
  ],
  "reverse-nodes-in-k-group": [
    "只翻转长度完整为 k 的连续节点块。最后不足 k 个节点的一段保持原顺序。",
  ],
  "copy-list-with-random-pointer": [
    "每个节点除了 next 指针还有 random 指针。结果需要描述一个深拷贝链表：节点值和 random 关系相同，但不是复用原节点。",
  ],
  "sort-list": [
    "把链表中的所有节点值按非降序排列，不能丢失或新增任何值。",
  ],
  "merge-k-sorted-lists": [
    "每个输入链表都已经有序。需要把所有链表中的所有值合并成一个有序序列，重复值也要保留。",
  ],
  "lru-cache": [
    "LRU 缓存容量满时，会淘汰最久没有被使用的 key。一次成功的 get 或 put 都会让该 key 变成最近使用。",
  ],
  "binary-tree-inorder-traversal": [
    "函数会收到二叉树根节点 root。样例中的带 null 层序数组用于展示和构造树；中序遍历的访问顺序是左子树、当前节点、右子树。",
  ],
  "maximum-depth-of-binary-tree": [
    "深度是从根节点到最深叶子节点路径上的节点数量。空树深度为 0。",
  ],
  "invert-binary-tree": [
    "翻转二叉树表示交换每个节点的左孩子和右孩子，最终整棵树以根节点为中心镜像。",
  ],
  "symmetric-tree": [
    "一棵树对称，当且仅当左子树和右子树互为镜像：外侧分支对应外侧分支，内侧分支对应内侧分支。",
  ],
  "diameter-of-binary-tree": [
    "直径是任意两个节点之间最长路径包含的边数。这条路径可以经过根节点，也可以完全位于某个子树中。",
  ],
  "binary-tree-level-order-traversal": [
    "从根节点开始按层访问节点。同一层的值放在同一个列表中，层与层按从上到下排列。",
  ],
  "convert-sorted-array-to-binary-search-tree": [
    "从升序数组构造高度平衡的二叉搜索树。本题约定每个区间选择较低的中点作为根节点，从而让答案确定。",
  ],
  "validate-binary-search-tree": [
    "每个节点必须严格大于左子树中的所有值，并严格小于右子树中的所有值。相等的值不满足二叉搜索树规则。",
  ],
  "kth-smallest-element-in-a-bst": [
    "二叉搜索树的中序遍历会按从小到大得到节点值。第 k 小使用 1 基计数。",
  ],
  "binary-tree-right-side-view": [
    "想象从树的右侧观察。每一层能看到的是该层最靠右的节点值。",
  ],
  "flatten-binary-tree-to-linked-list": [
    "展开顺序遵循前序遍历。展开后，每个节点的右指针指向前序遍历中的下一个节点，左指针不再参与结果。",
  ],
  "construct-binary-tree-from-preorder-and-inorder-traversal": [
    "前序遍历先给出每棵子树的根，中序遍历把这棵子树分成左侧和右侧。节点值互不相同，因此可以唯一还原整棵树。",
  ],
  "path-sum-iii": [
    "有效路径只能从父节点向子节点方向前进，但可以从任意节点开始，并在任意后代节点结束。统计所有路径和等于目标值的路径数量。",
  ],
  "lowest-common-ancestor-of-a-binary-tree": [
    "最近公共祖先是同时包含两个目标节点的最深节点。一个节点也可以是它自己的祖先。",
  ],
  "binary-tree-maximum-path-sum": [
    "路径可以从任意节点开始、在任意节点结束，沿父子边连接，不能分叉，并且至少包含一个节点。",
  ],
  "number-of-islands": [
    "岛屿是一组通过上下左右相连的陆地格子。斜向接触不算连通。",
  ],
  "rotting-oranges": [
    "腐烂会从所有当前腐烂橘子同时向四个方向扩散，每分钟感染相邻的新鲜橘子。如果有新鲜橘子永远无法被感染，答案为 -1。",
  ],
  "course-schedule": [
    "每个先修关系表示一门课必须在另一门课之前完成。只有这些依赖关系不存在环时，所有课程才可能全部完成。",
  ],
  "alien-dictionary": [
    "只能从相邻单词之间推断字母顺序。每一对相邻单词中，首个不同字符给出一条先后关系；这对单词后面的字符不再提供新的关系。",
    "如果较长单词排在自己的完整前缀前面，任何字母表都无法让这个列表有序。若字母关系图中存在环，也无法得到合法顺序。",
  ],
  "implement-trie-prefix-tree": [
    "Trie 通过共享公共前缀来存储单词。search 只在完整单词被插入过时成功，startsWith 只要求存在这条前缀路径。",
  ],
  permutations: [
    "每个排列都必须使用所有输入数字且每个数字使用一次。返回所有可能排列，并保持字典序。",
  ],
  subsets: [
    "对每个数字都可以选择放入或不放入当前子集。需要包含空集、所有部分子集和全集，并保持稳定顺序。",
  ],
  "letter-combinations-of-a-phone-number": [
    "使用电话键盘中数字 2 到 9 的标准字母映射。每个数字选择一个对应字母，按数字顺序拼成字符串。",
  ],
  "combination-sum": [
    "每个候选数字可以重复选择。每个组合内部保持非降序，这样同一组数字不会因为排列顺序不同而重复出现。",
  ],
  "generate-parentheses": [
    "一个括号串合法，要求任意前缀中左括号数量都不少于右括号数量，并且最终左右括号数量相等。",
  ],
  "word-search": [
    "单词的字符必须按顺序由相邻格子组成，相邻只包含上下左右。同一条匹配路径里，一个格子最多使用一次。",
  ],
  "palindrome-partitioning": [
    "把字符串切成若干连续片段。只有每个片段都是回文串时，这个切分方案才有效。",
  ],
  "n-queens": [
    "皇后会攻击同一行、同一列和两条对角线上的其他皇后。一个合法棋盘需要每行放一个皇后，并且互不攻击。",
  ],
  "search-insert-position": [
    "如果目标值已经存在，返回它当前的位置；如果不存在，返回把它插入后仍能保持数组有序的位置。",
  ],
  "search-a-2d-matrix": [
    "这个矩阵可以看作按行展开后的一个有序数组：每行有序，并且下一行的开头大于上一行的结尾。",
  ],
  "find-first-and-last-position-of-element-in-sorted-array": [
    "需要找到目标值最左侧和最右侧的出现位置。如果目标值不存在，两个位置都为 -1。",
  ],
  "search-in-rotated-sorted-array": [
    "数组原本升序且元素互不相同，后来在某个位置发生旋转。目标是找到 target 的下标；不存在则为 -1。",
  ],
  "find-minimum-in-rotated-sorted-array": [
    "输入来自一个升序数组在未知位置旋转后的结果。最小值就是原始升序数组的第一个值。",
  ],
  "median-of-two-sorted-arrays": [
    "把两个有序数组视为合并后的一个有序序列。总长度为偶数时，中位数是中间两个数的平均值。",
  ],
  "min-stack": [
    "MinStack 像普通栈一样支持入栈、出栈和查看栈顶，同时还能查询当前栈中最小的元素。",
  ],
  "decode-string": [
    "括号前的数字表示整个括号内容重复多少次。嵌套编码需要先解析内部，再作为外层内容的一部分继续展开。",
  ],
  "daily-temperatures": [
    "对每一天，向右寻找第一个温度严格更高的日子。答案是相隔天数；如果之后再也没有更高温，答案为 0。",
  ],
  "largest-rectangle-in-histogram": [
    "矩形必须覆盖连续的柱子，高度由这一段中最矮的柱子决定。目标是最大化宽度乘高度。",
  ],
  "kth-largest-element-in-an-array": [
    "把数组按降序排列后看位置，重复值占据多个位置。第 k 大使用 1 基计数。",
  ],
  "top-k-frequent-elements": [
    "先统计每个值出现的次数。频率越高越靠前；频率相同时，数值更小的排在前面。",
  ],
  "find-median-from-data-stream": [
    "数字会不断加入数据流。每次查询中位数时，都基于目前已经加入的所有数字；数量为偶数时取中间两个数的平均值。",
  ],
  "best-time-to-buy-and-sell-stock": [
    "最多完成一次买入和一次卖出，并且买入日期必须早于卖出日期。如果无法获利，最大利润为 0。",
  ],
  "jump-game": [
    "每个位置的值表示从这里最多能向右跳多少步。判断是否存在某种跳法能到达最后一个位置。",
  ],
  "jump-game-ii": [
    "每个位置的值表示从这里最多能向右跳多少步。目标是用尽可能少的跳跃次数到达最后一个位置。",
  ],
  "partition-labels": [
    "每个字符最终只能出现在一个片段里。扫描时尽早切分，但必须确保当前片段内出现过的字符不会再出现在后面的片段。",
  ],
  "pascals-triangle": [
    "第一行是 [1]。之后每一行首尾都是 1，中间每个数等于上一行相邻两个数之和。",
  ],
  "house-robber": [
    "选择某一间房屋后，左右相邻房屋都不能再选。目标是在不选择相邻房屋的前提下，让金额总和最大。",
  ],
  "perfect-squares": [
    "可以使用 1、4、9、16 这类完全平方数作为组成部分。目标是用最少数量的完全平方数凑出 n。",
  ],
  "coin-change": [
    "每种面额的硬币可以重复使用。目标是用最少硬币数恰好凑出 amount；如果凑不出，返回 -1。",
  ],
  "word-break": [
    "需要把整个字符串切分为若干连续的字典单词。字典中的单词可以重复使用，每个字符都必须属于某个选中的单词。",
  ],
  "longest-increasing-subsequence": [
    "子序列保持原数组顺序，但可以跳过元素。合法子序列要求每个选择的值都严格大于前一个选择的值。",
  ],
  "maximum-product-subarray": [
    "子数组必须连续且非空。负数会改变乘积符号，因此一个很小的负乘积后续可能变成很大的正乘积。",
  ],
  "partition-equal-subset-sum": [
    "判断能否把所有数字分成两个组，使两个组的元素和相等。每个数字必须且只能属于其中一个组。",
  ],
  "longest-valid-parentheses": [
    "合法括号子串必须是连续片段，并且内部括号完全匹配。答案是最长合法片段的长度。",
  ],
  "unique-paths": [
    "从左上角出发，到右下角结束。每一步只能向右移动一格或向下移动一格。",
  ],
  "minimum-path-sum": [
    "从左上角出发，到右下角结束。路径和是经过的所有格子数值之和，包括起点和终点；目标是选择路径和最小的路线。",
  ],
  "longest-palindromic-substring": [
    "答案必须是连续子串。如果存在多个同样长的最长回文子串，选择起点最靠前的那个。",
  ],
  "longest-common-subsequence": [
    "子序列保留字符相对顺序，但可以跳过字符。目标是找到两个字符串都能形成的最长公共子序列长度。",
  ],
  "edit-distance": [
    "一次操作可以插入一个字符、删除一个字符或替换一个字符。目标是用最少操作数把第一个单词变成第二个单词。",
  ],
  "single-number": [
    "除了一个数字只出现一次以外，其他数字都恰好出现两次。答案就是出现次数为 1 的那个数字。",
  ],
  "majority-element": [
    "多数元素指出现次数严格超过数组长度一半的值。题目保证这样的值存在且唯一。",
  ],
  "sort-colors": [
    "可以把 0、1、2 看作三种有序颜色标签。排序后所有 0 在前，其次是 1，最后是 2。",
  ],
  "next-permutation": [
    "排列按字典序排序。需要找到使用同一组数字的下一个更大排列；如果已经是最大排列，就回到最小排列。",
  ],
  "find-the-duplicate-number": [
    "数组有 n + 1 个位置，但数值只在 1 到 n 之间，因此至少有一个值重复。返回这个重复值。",
  ],
};

function stripOldGeneratedContent(description: string): string {
  const base = description.trim();
  const positions = OLD_GENERATED_MARKERS
    .map((marker) => base.indexOf(marker))
    .filter((position) => position >= 0);
  if (!positions.length) return base;
  return base.slice(0, Math.min(...positions)).trim();
}

export function detailedZhProblemDescription(problem: StatementProblem, baseDescription: string): string {
  const base = stripOldGeneratedContent(baseDescription);
  const details = SLUG_DETAILS[problem.slug];
  if (!details?.length) return base;
  return [base, ...details].join("\n\n").trim();
}
