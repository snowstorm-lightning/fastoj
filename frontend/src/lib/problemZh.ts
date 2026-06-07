export const PROBLEM_ZH_EXTRA: Record<string, { title: string; description?: string; hint?: string }> = {
  "longest-consecutive-sequence": {
    title: "最长连续序列",
    description: "给定一个未排序整数数组，返回数值连续的最长序列长度。",
    hint: "把数字放入集合，只从没有前驱的数字开始向后计数。",
  },
  "move-zeroes": {
    title: "移动零",
    description: "将数组中的所有 0 移到末尾，同时保持非零元素的相对顺序。",
    hint: "用写指针顺序放置非零元素，再把后缀填成 0。",
  },
  "3sum": {
    title: "三数之和",
    description: "返回所有和为 0 的不重复三元组，三元组和外层列表都按升序组织。",
    hint: "先排序，固定一个数后用双指针扫描剩余区间。",
  },
  "trapping-rain-water": {
    title: "接雨水",
    description: "给定柱子高度，计算下雨后最多能接住多少水。",
    hint: "维护两侧最高墙，从较低的一侧向内收缩。",
  },
  "find-all-anagrams-in-a-string": {
    title: "找到字符串中所有字母异位词",
    description: "返回 s 中所有与 p 互为字母异位词的子串起始下标。",
    hint: "维护长度固定为 p 的滑动窗口字符计数。",
  },
  "subarray-sum-equals-k": {
    title: "和为 K 的子数组",
    description: "统计数组中和恰好等于 k 的连续子数组数量。",
    hint: "用前缀和计数，查找当前前缀和减 k 出现过多少次。",
  },
  "sliding-window-maximum": {
    title: "滑动窗口最大值",
    description: "返回每个长度为 k 的滑动窗口中的最大值。",
    hint: "用单调队列保存可能成为最大值的下标。",
  },
  "minimum-window-substring": {
    title: "最小覆盖子串",
    description: "在 s 中找到包含 t 所有字符的最短子串。",
    hint: "右指针扩张满足需求后，左指针尽量收缩窗口。",
  },
  "rotate-array": {
    title: "轮转数组",
    description: "将数组向右轮转 k 步并返回结果。",
    hint: "k 对数组长度取模，可用三次反转或下标映射完成。",
  },
  "product-of-array-except-self": {
    title: "除自身以外数组的乘积",
    description: "返回数组中除当前元素以外其余元素的乘积，不能使用除法。",
    hint: "分别累积左侧乘积和右侧乘积。",
  },
  "first-missing-positive": {
    title: "缺失的第一个正数",
    description: "返回数组中没有出现的最小正整数。",
    hint: "把值 x 尽量放到下标 x-1 的位置。",
  },
  "set-matrix-zeroes": {
    title: "矩阵置零",
    description: "如果矩阵某个元素为 0，则将它所在行和列全部置为 0。",
    hint: "先记录需要置零的行列，再统一修改。",
  },
  "spiral-matrix": {
    title: "螺旋矩阵",
    description: "按顺时针螺旋顺序返回矩阵中的所有元素。",
    hint: "维护上下左右四个边界，每走完一圈收缩边界。",
  },
  "rotate-image": {
    title: "旋转图像",
    description: "将 n x n 矩阵顺时针旋转 90 度并返回结果。",
    hint: "先转置矩阵，再翻转每一行。",
  },
  "search-a-2d-matrix-ii": {
    title: "搜索二维矩阵 II",
    description: "在每行每列均升序的矩阵中判断目标值是否存在。",
    hint: "从右上角或左下角开始，每一步排除一行或一列。",
  },
  "intersection-of-two-linked-lists": {
    title: "相交链表",
    description: "两个链表用数组表示，返回它们后缀首次相同的节点值；不存在则返回 null。",
    hint: "可以把这里的数组模型看作公共后缀匹配问题。",
  },
  "reverse-linked-list": {
    title: "反转链表",
    description: "链表用数组表示，返回反转后的节点值数组。",
    hint: "数组模型下直接反向输出；链表模型中维护 prev 和 cur。",
  },
  "palindrome-linked-list": {
    title: "回文链表",
    description: "判断链表节点值从前往后和从后往前是否一致。",
    hint: "可用双指针找中点后反转后半段，或用数组双指针比较。",
  },
  "linked-list-cycle": {
    title: "环形链表",
    description: "给定节点数组和入环位置，判断链表是否存在环。",
    hint: "真实链表可用快慢指针；这里 pos 不为 -1 即表示有环。",
  },
  "linked-list-cycle-ii": {
    title: "环形链表 II",
    description: "给定节点数组和入环位置，返回入环下标；无环返回 -1。",
    hint: "真实链表中快慢指针相遇后，从头和相遇点同步走可找到入口。",
  },
  "merge-two-sorted-lists": {
    title: "合并两个有序链表",
    description: "合并两个升序链表数组，返回一个新的升序数组。",
    hint: "用两个指针每次取较小值追加到答案。",
  },
  "remove-nth-node-from-end-of-list": {
    title: "删除链表的倒数第 N 个节点",
    description: "删除链表数组中倒数第 n 个节点并返回结果数组。",
    hint: "数组可直接计算删除下标；链表中常用快慢指针保持 n 步距离。",
  },
  "swap-nodes-in-pairs": {
    title: "两两交换链表中的节点",
    description: "每两个相邻节点交换一次，返回交换后的链表数组。",
    hint: "按步长 2 处理相邻位置。",
  },
  "reverse-nodes-in-k-group": {
    title: "K 个一组翻转链表",
    description: "每 k 个节点翻转一次，剩余不足 k 个时保持原序。",
    hint: "按块处理，只有完整块才反转。",
  },
  "copy-list-with-random-pointer": {
    title: "复制带随机指针的链表",
    description: "节点以 [值, 随机指针下标] 表示，返回深拷贝后的同结构数组。",
    hint: "用哈希表建立旧节点到新节点的映射。",
  },
  "sort-list": {
    title: "排序链表",
    description: "将链表节点值排序并返回升序数组。",
    hint: "链表模型适合归并排序；数组模型可直接排序。",
  },
  "merge-k-sorted-lists": {
    title: "合并 K 个升序链表",
    description: "合并多个升序链表数组，返回一个升序数组。",
    hint: "可用最小堆，也可以分治两两合并。",
  },
  "lru-cache": {
    title: "LRU 缓存",
    description: "按操作序列模拟 LRU 缓存，写操作输出 null，get 输出对应值或 -1。",
    hint: "哈希表负责 O(1) 查询，双向链表维护最近使用顺序。",
  },
  "binary-tree-inorder-traversal": {
    title: "二叉树中序遍历",
    description: "二叉树用含 null 的层序数组表示，返回中序遍历结果。",
    hint: "递归顺序是左子树、根节点、右子树。",
  },
  "maximum-depth-of-binary-tree": {
    title: "二叉树的最大深度",
    description: "返回二叉树从根到最深叶子的节点数。",
    hint: "递归返回左右子树深度的较大值加一。",
  },
  "invert-binary-tree": {
    title: "翻转二叉树",
    description: "交换二叉树每个节点的左右子树，返回层序数组。",
    hint: "对每个节点递归或 BFS 交换左右孩子。",
  },
  "symmetric-tree": {
    title: "对称二叉树",
    description: "判断二叉树是否关于根节点左右镜像对称。",
    hint: "比较左子树的左侧与右子树的右侧，左子树的右侧与右子树的左侧。",
  },
  "diameter-of-binary-tree": {
    title: "二叉树的直径",
    description: "返回二叉树中任意两节点路径的最大边数。",
    hint: "DFS 计算高度时同步更新左右高度之和。",
  },
  "binary-tree-level-order-traversal": {
    title: "二叉树的层序遍历",
    description: "按层返回二叉树节点值。",
    hint: "用队列逐层 BFS。",
  },
  "convert-sorted-array-to-binary-search-tree": {
    title: "将有序数组转换为二叉搜索树",
    description: "把升序数组转换为高度平衡的二叉搜索树，并返回层序数组。",
    hint: "每次选中点作为根节点，递归构造左右子树。",
  },
  "validate-binary-search-tree": {
    title: "验证二叉搜索树",
    description: "判断二叉树是否满足严格的二叉搜索树约束。",
    hint: "递归传递每个节点允许的取值上下界。",
  },
  "kth-smallest-element-in-a-bst": {
    title: "二叉搜索树中第 K 小的元素",
    description: "返回二叉搜索树中第 k 小的节点值。",
    hint: "BST 的中序遍历结果是升序序列。",
  },
  "binary-tree-right-side-view": {
    title: "二叉树的右视图",
    description: "返回从右侧能看到的每一层最后一个节点值。",
    hint: "层序遍历时取每层最后一个非空节点。",
  },
  "flatten-binary-tree-to-linked-list": {
    title: "二叉树展开为链表",
    description: "把二叉树按前序遍历顺序展开，并返回展开后的右链值数组。",
    hint: "前序遍历结果就是展开后的顺序。",
  },
  "construct-binary-tree-from-preorder-and-inorder-traversal": {
    title: "从前序与中序遍历序列构造二叉树",
    description: "根据前序和中序遍历数组重建二叉树，返回层序数组。",
    hint: "前序第一个值是根，在中序中把左右子树分开。",
  },
  "path-sum-iii": {
    title: "路径总和 III",
    description: "统计二叉树中向下路径和等于目标值的数量。",
    hint: "用前缀和统计当前路径上出现过的和。",
  },
  "lowest-common-ancestor-of-a-binary-tree": {
    title: "二叉树的最近公共祖先",
    description: "给定二叉树和两个节点值，返回它们最近公共祖先的节点值。",
    hint: "若两个目标分别出现在左右子树，当前节点就是最近公共祖先。",
  },
  "binary-tree-maximum-path-sum": {
    title: "二叉树中的最大路径和",
    description: "返回二叉树任意非空路径的最大节点值之和。",
    hint: "DFS 返回可向父节点延伸的最大贡献，同时更新全局答案。",
  },
  "number-of-islands": {
    title: "岛屿数量",
    description: "给定 0/1 网格，统计由相邻陆地组成的岛屿数量。",
    hint: "遇到未访问陆地后用 DFS 或 BFS 标记整座岛。",
  },
  "rotting-oranges": {
    title: "腐烂的橘子",
    description: "每分钟腐烂橘子会感染相邻新鲜橘子，返回全部腐烂所需时间，无法完成则返回 -1。",
    hint: "把所有初始腐烂橘子作为多源 BFS 起点。",
  },
  "course-schedule": {
    title: "课程表",
    description: "判断给定先修关系下是否可以完成所有课程。",
    hint: "检测有向图是否存在环，可用拓扑排序或 DFS 状态标记。",
  },
  "alien-dictionary": {
    title: "外星文字典",
    description: "给定按外星字典序排序的单词列表，推断一种合法字母顺序；若存在矛盾则返回空字符串。",
    hint: "比较相邻单词的首个不同字符得到有向边，再做拓扑排序。",
  },
  "implement-trie-prefix-tree": {
    title: "实现 Trie 前缀树",
    description: "模拟 insert、search 和 startsWith 操作，插入输出 null，查询输出布尔值。",
    hint: "每个节点维护子节点映射和是否为单词结尾。",
  },
  "permutations": {
    title: "全排列",
    description: "返回数组所有可能的排列。",
    hint: "回溯时记录已使用元素，构造长度等于 n 的路径。",
  },
  "subsets": {
    title: "子集",
    description: "返回数组所有可能子集，结果按题目约定排序。",
    hint: "每个元素都有选或不选两种状态。",
  },
  "letter-combinations-of-a-phone-number": {
    title: "电话号码的字母组合",
    description: "给定数字字符串，返回电话键盘上所有可能的字母组合。",
    hint: "按数字逐层回溯拼接对应字母。",
  },
  "combination-sum": {
    title: "组合总和",
    description: "返回所有和为 target 的组合，每个候选数字可以重复使用。",
    hint: "排序后回溯，递归时允许继续使用当前下标。",
  },
  "generate-parentheses": {
    title: "括号生成",
    description: "生成 n 对括号的所有合法组合。",
    hint: "只有左括号数量不足 n 时可放左括号，右括号少于左括号时可放右括号。",
  },
  "word-search": {
    title: "单词搜索",
    description: "判断单词是否可以由网格中相邻单元格顺序组成，每个格子最多使用一次。",
    hint: "从每个起点 DFS，并在路径中临时标记已访问格子。",
  },
  "palindrome-partitioning": {
    title: "分割回文串",
    description: "返回把字符串切分成若干回文子串的所有方案。",
    hint: "回溯枚举切割点，只有当前片段是回文才继续递归。",
  },
  "n-queens": {
    title: "N 皇后",
    description: "返回所有合法的 n 皇后棋盘方案。",
    hint: "逐行放置皇后，并维护列、主对角线、副对角线占用情况。",
  },
  "search-insert-position": {
    title: "搜索插入位置",
    description: "返回目标值在有序数组中的下标；不存在时返回应插入的位置。",
    hint: "二分查找第一个大于等于 target 的位置。",
  },
  "search-a-2d-matrix": {
    title: "搜索二维矩阵",
    description: "判断目标值是否存在于按行展开后整体有序的矩阵中。",
    hint: "把矩阵视为一维有序数组进行二分。",
  },
  "find-first-and-last-position-of-element-in-sorted-array": {
    title: "在排序数组中查找元素的第一个和最后一个位置",
    description: "返回目标值在升序数组中的左右边界，不存在则返回 [-1,-1]。",
    hint: "分别二分第一个不小于 target 和第一个大于 target 的位置。",
  },
  "search-in-rotated-sorted-array": {
    title: "搜索旋转排序数组",
    description: "在无重复的旋转升序数组中查找目标值下标，不存在返回 -1。",
    hint: "二分时判断哪一半仍然有序，再决定保留区间。",
  },
  "find-minimum-in-rotated-sorted-array": {
    title: "寻找旋转排序数组中的最小值",
    description: "返回旋转升序数组中的最小元素。",
    hint: "比较中点与右端点，判断最小值在哪一侧。",
  },
  "median-of-two-sorted-arrays": {
    title: "寻找两个正序数组的中位数",
    description: "返回两个有序数组合并后的中位数。",
    hint: "可二分较短数组的切分位置，使左右两侧数量和值域都满足条件。",
  },
  "min-stack": {
    title: "最小栈",
    description: "模拟支持 push、pop、top 和 getMin 的栈操作。",
    hint: "额外维护一个同步最小值栈。",
  },
  "decode-string": {
    title: "字符串解码",
    description: "解码形如 k[encoded] 的嵌套字符串。",
    hint: "用栈保存进入括号前的字符串和重复次数。",
  },
  "daily-temperatures": {
    title: "每日温度",
    description: "返回每一天还要等待多少天才会出现更高温度，没有则为 0。",
    hint: "用单调递减栈保存还没找到更高温的下标。",
  },
  "largest-rectangle-in-histogram": {
    title: "柱状图中最大的矩形",
    description: "返回柱状图中能形成的最大矩形面积。",
    hint: "用单调栈找到每根柱子作为最矮高度时的左右边界。",
  },
  "kth-largest-element-in-an-array": {
    title: "数组中的第 K 个最大元素",
    description: "返回数组排序后第 k 大的元素。",
    hint: "可用大小为 k 的小根堆或快速选择。",
  },
  "top-k-frequent-elements": {
    title: "前 K 个高频元素",
    description: "返回出现频率最高的 k 个元素。",
    hint: "先计数，再用桶排序或堆选出最高频元素。",
  },
  "find-median-from-data-stream": {
    title: "数据流的中位数",
    description: "模拟数据流中加入数字和查询中位数的操作。",
    hint: "用大根堆保存较小一半，小根堆保存较大一半。",
  },
  "best-time-to-buy-and-sell-stock": {
    title: "买卖股票的最佳时机",
    description: "给定每日股价，返回一次买入卖出能获得的最大利润。",
    hint: "遍历时维护历史最低买入价和当前最大利润。",
  },
  "jump-game": {
    title: "跳跃游戏",
    description: "判断能否从数组起点跳到最后一个位置。",
    hint: "贪心维护当前能到达的最远位置。",
  },
  "jump-game-ii": {
    title: "跳跃游戏 II",
    description: "返回从起点到最后位置所需的最少跳跃次数。",
    hint: "按当前跳跃覆盖范围逐层扩展最远可达位置。",
  },
  "partition-labels": {
    title: "划分字母区间",
    description: "把字符串划分为尽可能多的片段，使每个字母最多出现在一个片段中。",
    hint: "先记录每个字符最后出现位置，扫描时维护当前片段右边界。",
  },
  "pascals-triangle": {
    title: "杨辉三角",
    description: "生成前 numRows 行杨辉三角。",
    hint: "每行首尾为 1，中间由上一行相邻两数相加得到。",
  },
  "house-robber": {
    title: "打家劫舍",
    description: "不能偷相邻房屋，返回能偷到的最大金额。",
    hint: "状态只依赖前一间和前两间，可以滚动维护。",
  },
  "perfect-squares": {
    title: "完全平方数",
    description: "返回和为 n 的完全平方数的最少数量。",
    hint: "可做完全背包 DP，也可用 BFS 按层搜索。",
  },
  "coin-change": {
    title: "零钱兑换",
    description: "给定硬币面额和金额，返回凑成金额所需最少硬币数，无法凑成返回 -1。",
    hint: "令 dp[x] 表示凑成金额 x 的最少硬币数。",
  },
  "word-break": {
    title: "单词拆分",
    description: "判断字符串是否可以被字典中的单词拼接出来。",
    hint: "dp[i] 表示前 i 个字符是否可拆分。",
  },
  "longest-increasing-subsequence": {
    title: "最长递增子序列",
    description: "返回数组中严格递增子序列的最大长度。",
    hint: "维护每个长度的递增子序列最小结尾值，并用二分更新。",
  },
  "maximum-product-subarray": {
    title: "乘积最大子数组",
    description: "返回非空连续子数组的最大乘积。",
    hint: "同时维护以当前位置结尾的最大乘积和最小乘积。",
  },
  "partition-equal-subset-sum": {
    title: "分割等和子集",
    description: "判断数组是否能分成两个元素和相等的子集。",
    hint: "问题等价于是否能选出若干数使和为总和的一半。",
  },
  "longest-valid-parentheses": {
    title: "最长有效括号",
    description: "返回最长合法括号子串的长度。",
    hint: "可用栈保存未匹配位置，也可用 DP 连接有效区间。",
  },
  "unique-paths": {
    title: "不同路径",
    description: "机器人只能向右或向下移动，返回从左上到右下的路径数。",
    hint: "可用组合数学，也可用网格 DP。",
  },
  "minimum-path-sum": {
    title: "最小路径和",
    description: "在网格中只能向右或向下移动，返回路径数字和的最小值。",
    hint: "dp[i][j] 等于当前格子值加上方或左方较小路径和。",
  },
  "longest-palindromic-substring": {
    title: "最长回文子串",
    description: "返回字符串中最长的回文子串。",
    hint: "以每个位置为中心向两侧扩展，分别处理奇偶长度。",
  },
  "longest-common-subsequence": {
    title: "最长公共子序列",
    description: "返回两个字符串的最长公共子序列长度。",
    hint: "dp[i][j] 表示两个前缀的最长公共子序列长度。",
  },
  "edit-distance": {
    title: "编辑距离",
    description: "返回把 word1 转换成 word2 所需的最少插入、删除、替换次数。",
    hint: "dp[i][j] 表示两个前缀互相转换的最小操作数。",
  },
  "single-number": {
    title: "只出现一次的数字",
    description: "数组中除一个元素只出现一次外，其余都出现两次，返回只出现一次的元素。",
    hint: "相同数字异或后为 0，所有数字异或即可得到答案。",
  },
  "majority-element": {
    title: "多数元素",
    description: "返回数组中出现次数超过一半的元素。",
    hint: "Boyer-Moore 投票算法可以 O(1) 空间完成。",
  },
  "sort-colors": {
    title: "颜色分类",
    description: "将只包含 0、1、2 的数组按升序排序。",
    hint: "用三个指针分别维护 0 区、1 区和 2 区。",
  },
  "next-permutation": {
    title: "下一个排列",
    description: "返回字典序中的下一个排列；若不存在更大排列则返回最小排列。",
    hint: "从右向左找第一个下降位置，再交换并反转后缀。",
  },
  "find-the-duplicate-number": {
    title: "寻找重复数",
    description: "数组包含 n+1 个数且取值在 1..n，返回重复的那个数。",
    hint: "可把数组视为链表，用快慢指针找环入口。",
  },
};
