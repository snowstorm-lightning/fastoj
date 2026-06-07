"""Localized explanations for bundled seed problems."""

from __future__ import annotations

from dataclasses import dataclass

from backend.core.locales import normalize_locale, uses_source_text


@dataclass(frozen=True)
class LocalizedSeedExplanation:
    zh: str
    en: str


SEED_EXPLANATIONS: dict[str, LocalizedSeedExplanation] = {
    "two-sum": LocalizedSeedExplanation(
        "用哈希表记录已经扫描过的数字和下标。遍历到当前数字时立即查找 target - nums[i]，一旦补数已经出现，就能在线性时间返回这两个下标。",
        "Store each visited value and index in a hash table. For every element, check whether target - nums[i] was seen earlier; the first matching complement gives the answer in one pass.",
    ),
    "add-two-numbers": LocalizedSeedExplanation(
        "按逆序数字逐位相加，同时维护 carry。每一位写入 total % 10，进位进入下一轮，最后如果 carry 仍存在就追加一位。",
        "Simulate digit-by-digit addition on the reversed digit arrays. Each step writes total % 10 and carries total // 10 to the next digit, appending the final carry when needed.",
    ),
    "longest-substring-without-repeating-characters": LocalizedSeedExplanation(
        "使用滑动窗口维护当前无重复子串。右指针扩张窗口，遇到重复字符时把左边界移动到该字符上次出现位置之后，并持续更新最大长度。",
        "Use a sliding window whose contents contain no duplicate characters. When a repeated character reappears inside the window, move the left boundary after its previous index and update the best length.",
    ),
    "valid-parentheses": LocalizedSeedExplanation(
        "用栈保存每个左括号期望匹配的右括号。读取右括号时必须等于栈顶期望值，遍历结束后栈为空才说明所有括号都按正确顺序闭合。",
        "Push the expected closing bracket for each opener. Every closing bracket must match the stack top, and the stack must be empty after scanning the string.",
    ),
    "alien-dictionary": LocalizedSeedExplanation(
        "比较相邻单词的第一个不同字符建立有向边，并先排除长单词排在自身前缀前面的非法情况。随后用 Kahn 拓扑排序输出字母序，若无法处理全部字母则存在环。",
        "Compare each adjacent word pair and use the first differing character as a directed ordering edge, while rejecting invalid prefix ordering. Kahn topological sort then emits the alphabet order, or an empty string when a cycle remains.",
    ),
    "two-car-parking-lot": LocalizedSeedExplanation(
        "把两辆车的位置合成一个 BFS 状态。每一步只移动一辆车，过滤越界、撞墙和占用同一格的状态；当 A 到达 a 且 B 到达 b 时返回真。",
        "Run BFS over the combined positions of both cars. Each step moves one car, discarding states that leave the grid, hit a wall, or overlap; reaching A on a and B on b at the same time returns true.",
    ),
    "maximum-subarray": LocalizedSeedExplanation(
        "Kadane 算法维护“必须以当前位置结尾”的最大子数组和。当前位置要么单独开始新段，要么接在前一段之后，同时更新全局最大值。",
        "Kadane's algorithm tracks the best subarray that must end at the current position. Each value either starts a new segment or extends the previous segment, while a global best is maintained.",
    ),
    "group-anagrams": LocalizedSeedExplanation(
        "把每个字符串排序后的字符序列作为分组 key，key 相同的单词互为异位词。最后对组内和组间排序，使多答案题的输出稳定可比较。",
        "Use the sorted letters of each word as the group key, because anagrams share the same sorted signature. Sort within and across groups to make the multi-answer output deterministic.",
    ),
    "merge-intervals": LocalizedSeedExplanation(
        "先按左端点排序区间，再顺序合并。新区间若与结果末尾重叠就扩展右端点，否则作为新的不相交区间加入。",
        "Sort intervals by start position and scan them in order. If the next interval overlaps the current merged tail, extend its end; otherwise start a new interval.",
    ),
    "climbing-stairs": LocalizedSeedExplanation(
        "到达第 n 阶的最后一步只能来自 n-1 或 n-2，因此答案满足斐波那契递推。用两个滚动变量即可避免保存整张 DP 表。",
        "The last move to step n comes from step n-1 or n-2, so the count follows the Fibonacci recurrence. Two rolling variables are enough.",
    ),
    "container-with-most-water": LocalizedSeedExplanation(
        "双指针从两端向内收缩，当前面积由较短边决定。移动较短边才可能找到更高的限制边，从而得到更大面积。",
        "Use two pointers at the ends. The shorter line limits the current area, so moving that pointer is the only move that can improve the limiting height.",
    ),
    "logistic-regression-sigmoid": LocalizedSeedExplanation(
        "先计算线性得分 w·x+b，再做 sigmoid。实现时按得分正负分支计算指数，避免极大正数或负数导致溢出，返回四位小数格式下可比较的概率。",
        "Compute the linear score w·x+b and pass it through sigmoid. Branching by score sign keeps the exponential stable for very large positive or negative values, producing the probability expected by the four-decimal judge format.",
    ),
    "knn-majority-vote": LocalizedSeedExplanation(
        "计算查询点到所有训练点的欧氏距离，按距离选出最近的 k 个样本投票。票数相同按标签字典序决胜，保证结果确定。",
        "Compute Euclidean distances from the query to every training point, take the nearest k labels, and vote. Ties are resolved by lexicographic label order for deterministic output.",
    ),
    "kmeans-one-iteration": LocalizedSeedExplanation(
        "这是 KMeans 的一次分配步骤：每个点分别计算到所有中心的距离，并选择最近中心的下标。距离相同保留较小中心下标。",
        "This is the assignment step of KMeans. For each point, compute its distance to every centroid and choose the nearest centroid index, keeping the smaller index on ties.",
    ),
    "scaled-dot-product-attention": LocalizedSeedExplanation(
        "先计算 query 与每个 key 的点积并除以 sqrt(d)，再用稳定 softmax 得到注意力权重，最后对 value 向量加权求和。",
        "Compute query-key dot products scaled by sqrt(d), apply a numerically stable softmax to get attention weights, then return the weighted sum of value vectors.",
    ),
    "softmax-cross-entropy": LocalizedSeedExplanation(
        "对 logits 先减去最大值再计算 softmax，避免指数溢出。目标类别概率的负对数就是交叉熵损失，按浮点格式输出。",
        "Subtract the maximum logit before softmax to avoid exponential overflow. The cross-entropy loss is the negative log probability of the target class.",
    ),
    "attention-mask-apply": LocalizedSeedExplanation(
        "只在 mask 为 1 的位置上做稳定 softmax，被屏蔽位置输出 0。若全部位置被屏蔽，则返回全 0 分布。",
        "Apply stable softmax only to positions whose mask is 1, and output 0 for masked positions. If every position is masked, return an all-zero distribution.",
    ),
    "longest-consecutive-sequence": LocalizedSeedExplanation(
        "把数字放入集合后，只从没有前驱 x-1 的数字开始扩展连续段。每个数字最多被检查常数次，因此能在线性时间找到最长长度。",
        "Put all values in a set and only start counting from numbers with no predecessor x-1. Each value is checked a constant number of times, giving linear time.",
    ),
    "move-zeroes": LocalizedSeedExplanation(
        "用写指针依次放置非零元素，保持它们原来的相对顺序。剩余位置统一补 0，得到稳定的原地移动效果。",
        "Use a write pointer to place nonzero values in their original order. Fill the remaining suffix with zeros to preserve stable movement.",
    ),
    "3sum": LocalizedSeedExplanation(
        "排序后枚举第一个数，再用左右双指针寻找和为相反数的两数。跳过重复值，返回按字典序稳定排序的不重复三元组。",
        "Sort the array, fix the first value, and use two pointers to find the complementary pair. Skip duplicates and return unique triplets in deterministic order.",
    ),
    "trapping-rain-water": LocalizedSeedExplanation(
        "双指针维护左右两侧见过的最高墙。较低一侧的最高墙决定当前位置可接水量，因此每次处理较低侧并累加差值。",
        "Maintain the highest wall seen from both ends with two pointers. The lower side determines the trapped water at that position, so process that side and add the height gap.",
    ),
    "find-all-anagrams-in-a-string": LocalizedSeedExplanation(
        "用固定长度滑动窗口维护字符计数，并与模式串计数比较。窗口长度等于 p 时若计数一致，当前左端点就是异位词起点。",
        "Use a fixed-size sliding window with character counts and compare it with the pattern counts. Whenever the window length equals p and counts match, record the left index.",
    ),
    "subarray-sum-equals-k": LocalizedSeedExplanation(
        "维护前缀和出现次数。当前位置前缀和为 cur 时，所有 cur-k 的历史前缀都能与当前位置组成和为 k 的子数组。",
        "Track frequencies of prefix sums. At prefix sum cur, every previous prefix cur-k forms a subarray ending here with sum k.",
    ),
    "sliding-window-maximum": LocalizedSeedExplanation(
        "单调队列保存窗口内可能成为最大值的下标，并保持对应值递减。窗口右移时移除过期下标，队首就是当前最大值。",
        "Maintain a deque of candidate indices whose values are decreasing. Remove expired indices as the window moves; the deque front is the current maximum.",
    ),
    "minimum-window-substring": LocalizedSeedExplanation(
        "用滑动窗口统计已覆盖的目标字符数量。右端扩张直到覆盖 t，再不断收缩左端以得到最短有效窗口。",
        "Use a sliding window that counts covered target characters. Expand right until all requirements are met, then shrink left to keep the shortest valid window.",
    ),
    "rotate-array": LocalizedSeedExplanation(
        "把 k 对数组长度取模后，右旋结果等于后 k 个元素接到前面，前 n-k 个元素顺序后移。直接切片即可表达这个变换。",
        "Reduce k modulo the array length. A right rotation is the last k elements followed by the first n-k elements, preserving internal order.",
    ),
    "product-of-array-except-self": LocalizedSeedExplanation(
        "先把每个位置左侧元素乘积写入答案，再从右向左乘上右侧元素乘积。整个过程不需要除法，也能处理 0。",
        "Write the product of all elements to the left of each index, then scan from the right and multiply by the product of all elements to the right. No division is needed, so zeros are handled naturally.",
    ),
    "first-missing-positive": LocalizedSeedExplanation(
        "把值 x 尽量交换到下标 x-1 的位置。整理后第一个不满足 nums[i] == i+1 的位置，对应缺失的最小正整数。",
        "Place each value x into index x-1 whenever possible. After rearrangement, the first index where nums[i] != i+1 reveals the smallest missing positive.",
    ),
    "set-matrix-zeroes": LocalizedSeedExplanation(
        "先记录哪些行和列出现 0，再第二次遍历把这些行列全部置 0。这样每个原始 0 的影响都会传播到整行整列。",
        "Record which rows and columns contain an original zero, then make every cell in those rows or columns zero in a second pass.",
    ),
    "spiral-matrix": LocalizedSeedExplanation(
        "维护上下左右四个边界，按右、下、左、上的顺序逐层收缩。每访问完一条边就移动对应边界，直到全部元素输出。",
        "Maintain top, bottom, left, and right boundaries. Traverse right, down, left, and up while shrinking the used boundary after each side.",
    ),
    "rotate-image": LocalizedSeedExplanation(
        "顺时针旋转 90 度可以先转置矩阵，再反转每一行。转置交换行列位置，行反转完成水平镜像。",
        "A 90-degree clockwise rotation is achieved by transposing the matrix and then reversing each row.",
    ),
    "search-a-2d-matrix-ii": LocalizedSeedExplanation(
        "从右上角开始搜索。当前值过大就左移，过小就下移，每一步都能排除一整行或一整列。",
        "Start from the top-right cell. Move left when the value is too large and down when it is too small, eliminating one row or column each step.",
    ),
    "intersection-of-two-linked-lists": LocalizedSeedExplanation(
        "在数组表示中寻找两条链表共享的后缀段，交点值就是公共后缀的入口。若不存在公共尾部，则返回 null。",
        "In the array representation, find the shared suffix of the two lists; the intersection value is the entry of that common suffix. Return null when no common tail exists.",
    ),
    "reverse-linked-list": LocalizedSeedExplanation(
        "链表题在 seed 中用数组表达节点顺序，反转链表等价于把节点值顺序整体反向输出。",
        "The seed represents the list by node values in order, so reversing the list means returning those values in reverse order.",
    ),
    "palindrome-linked-list": LocalizedSeedExplanation(
        "比较链表值序列和它的反转序列。两者完全一致说明从前往后和从后往前读相同，是回文链表。",
        "Compare the list values with their reversed order. If they match exactly, the list reads the same forward and backward.",
    ),
    "linked-list-cycle": LocalizedSeedExplanation(
        "seed 输入用 pos 表示尾节点连接回的下标。pos 为 -1 没有环，否则尾节点会指回该位置形成环。",
        "The seed input uses pos as the index where the tail links back. pos = -1 means no cycle; any other index creates a cycle.",
    ),
    "linked-list-cycle-ii": LocalizedSeedExplanation(
        "根据 pos 返回环入口下标。没有环时 pos 为 -1，存在环时该下标就是快慢指针最终会定位到的入口。",
        "Return the cycle entry index represented by pos. When pos is -1 there is no cycle; otherwise that index is the entry a fast/slow pointer solution would locate.",
    ),
    "merge-two-sorted-lists": LocalizedSeedExplanation(
        "双指针分别扫描两个有序链表，每次取较小节点接到结果后面。某一条链表耗尽后追加另一条剩余部分。",
        "Use two pointers over the sorted lists, repeatedly appending the smaller current value. Append the remaining suffix once one list is exhausted.",
    ),
    "remove-nth-node-from-end-of-list": LocalizedSeedExplanation(
        "要删除倒数第 n 个节点，可以先计算长度并转换成正向下标，或用快慢指针保持 n 的间距。数组结果移除对应值后返回。",
        "Delete the nth node from the end by converting it to a forward index or by using two pointers n steps apart. The returned array omits that node.",
    ),
    "swap-nodes-in-pairs": LocalizedSeedExplanation(
        "每两个相邻节点为一组交换顺序，奇数长度时最后一个节点保持原位。数组表达中就是按两两分块翻转。",
        "Swap every adjacent pair of nodes; if the length is odd, the final node stays in place. In the array representation this is pairwise reversal.",
    ),
    "reverse-nodes-in-k-group": LocalizedSeedExplanation(
        "每满 k 个节点就整体反转，不足 k 个的尾部保持原顺序。实现时按块处理并拼接结果。",
        "Reverse each complete block of k nodes and leave the remaining tail unchanged if it has fewer than k nodes.",
    ),
    "copy-list-with-random-pointer": LocalizedSeedExplanation(
        "用下标表示 random 指针时，深拷贝需要保留每个节点的值和 random 目标下标。返回的新结构应与原结构值相同但逻辑独立。",
        "With random pointers represented by indices, the deep copy preserves each node value and random target index while producing an independent logical list.",
    ),
    "sort-list": LocalizedSeedExplanation(
        "链表排序在数组表示中返回升序值序列。真实链表可用归并排序保持 O(n log n)，seed 输出关注最终有序顺序。",
        "The array representation returns the list values in ascending order. A linked-list implementation would use merge sort for O(n log n), while the seed output checks the sorted order.",
    ),
    "merge-k-sorted-lists": LocalizedSeedExplanation(
        "用最小堆保存每条链表的当前最小元素，每次弹出全局最小值并推进对应链表。这样能按升序合并所有节点。",
        "Use a min-heap containing the current value from each list. Pop the global minimum, append it, and advance that list to merge all values in sorted order.",
    ),
    "lru-cache": LocalizedSeedExplanation(
        "哈希表负责 O(1) 定位 key，使用顺序结构维护最近使用次序。get 和 put 都会把 key 标记为最新，容量超限时淘汰最久未使用项。",
        "A hash map gives O(1) key lookup, while an order structure tracks recency. Both get and put mark a key as most recently used, and capacity overflow evicts the least recently used key.",
    ),
    "binary-tree-inorder-traversal": LocalizedSeedExplanation(
        "中序遍历按左子树、根节点、右子树的顺序访问。level-order 数组先还原树形关系，再递归或栈遍历输出节点值。",
        "Inorder traversal visits left subtree, root, then right subtree. The level-order array is interpreted as the tree structure before recursively or iteratively collecting values.",
    ),
    "maximum-depth-of-binary-tree": LocalizedSeedExplanation(
        "树的最大深度等于从根到最深叶子的节点数。递归时每个节点深度为左右子树最大深度加一。",
        "The maximum depth is the number of nodes on the longest root-to-leaf path. Recursively, a node contributes one plus the deeper child depth.",
    ),
    "invert-binary-tree": LocalizedSeedExplanation(
        "对每个节点交换左右子树，整棵树就完成镜像翻转。返回时再按 level-order 数组序列化镜像后的树。",
        "Swap the left and right child of every node to mirror the tree, then serialize the mirrored tree back to level-order form.",
    ),
    "symmetric-tree": LocalizedSeedExplanation(
        "判断根的左右子树是否互为镜像：外侧节点相等、内侧节点相等，并且递归结构也匹配。",
        "Check whether the left and right subtrees are mirrors: outer values match, inner values match, and the recursive structures align.",
    ),
    "diameter-of-binary-tree": LocalizedSeedExplanation(
        "DFS 返回每个节点向下的最大深度，同时用左右深度之和更新经过该节点的最长路径。全局最大值就是直径边数。",
        "DFS returns each node's downward depth and updates the best path through that node as left depth plus right depth. The global maximum is the diameter in edges.",
    ),
    "binary-tree-level-order-traversal": LocalizedSeedExplanation(
        "用队列按层 BFS。每轮处理当前队列长度对应的一整层，并把下一层节点加入队列。",
        "Use a queue for breadth-first traversal. Each round processes the current queue size as one level and enqueues the next level's children.",
    ),
    "convert-sorted-array-to-binary-search-tree": LocalizedSeedExplanation(
        "递归选择当前有序区间的中点作为根节点，左半区间构造左子树，右半区间构造右子树，从而得到高度平衡 BST。",
        "Recursively choose the midpoint of the sorted range as the root, build the left subtree from the left half and the right subtree from the right half to keep the BST height-balanced.",
    ),
    "validate-binary-search-tree": LocalizedSeedExplanation(
        "递归传递每个节点允许的开区间上下界。节点值必须严格落在区间内，左子树收紧上界，右子树收紧下界。",
        "Carry an open lower and upper bound for every node. Each value must lie strictly within its bounds; the left subtree tightens the upper bound and the right subtree tightens the lower bound.",
    ),
    "kth-smallest-element-in-a-bst": LocalizedSeedExplanation(
        "BST 的中序遍历是升序序列，因此按中序访问并计数，第 k 个访问到的值就是答案。",
        "Inorder traversal of a BST yields values in ascending order. Count visited nodes during inorder traversal and return the kth value.",
    ),
    "binary-tree-right-side-view": LocalizedSeedExplanation(
        "按层 BFS 时，每一层最后访问到的节点就是从右侧能看到的节点。收集每层末尾值即可。",
        "During level-order traversal, the last node processed in each level is visible from the right side. Collect that value for every level.",
    ),
    "flatten-binary-tree-to-linked-list": LocalizedSeedExplanation(
        "展平顺序等同于前序遍历：根、左、右。返回这个前序序列即可表达展平后的单链表节点顺序。",
        "Flattening follows preorder order: root, left, right. Returning that preorder sequence represents the linked-list order after flattening.",
    ),
    "construct-binary-tree-from-preorder-and-inorder-traversal": LocalizedSeedExplanation(
        "前序数组首元素是根，在中序数组中定位根后即可划分左右子树。递归构造后按 level-order 输出树。",
        "The first preorder value is the root. Its position in inorder splits left and right subtrees, which are recursively built and serialized level-order.",
    ),
    "path-sum-iii": LocalizedSeedExplanation(
        "DFS 过程中维护从根到当前节点的前缀和计数。若当前前缀和减 target 已出现，就说明存在以当前节点结尾的目标路径。",
        "Maintain counts of prefix sums along the current root-to-node path. If current_sum - target has appeared, those prefixes form target-sum paths ending here.",
    ),
    "lowest-common-ancestor-of-a-binary-tree": LocalizedSeedExplanation(
        "递归搜索 p 和 q。若两个目标分别出现在当前节点左右子树，当前节点就是最近公共祖先；若只在一侧，则向上传递该侧结果。",
        "Search recursively for p and q. If the targets appear in different subtrees of a node, that node is the lowest common ancestor; otherwise propagate the found side upward.",
    ),
    "binary-tree-maximum-path-sum": LocalizedSeedExplanation(
        "DFS 返回从当前节点向父节点延伸的最大贡献，并丢弃负贡献。用 left + node + right 更新可在当前节点拐弯的全局最大路径。",
        "DFS returns the best gain that can extend upward from each node, ignoring negative gains. The path bending at a node uses left gain + node value + right gain to update the global best.",
    ),
    "number-of-islands": LocalizedSeedExplanation(
        "扫描网格，遇到未访问的陆地就计数并用 DFS/BFS 淹没整座岛。每座连通陆地只会被计数一次。",
        "Scan the grid; when an unvisited land cell is found, count one island and flood-fill all connected land by DFS or BFS.",
    ),
    "rotting-oranges": LocalizedSeedExplanation(
        "多源 BFS 从所有腐烂橘子同时扩散，每一层代表一分钟。最后若仍有新鲜橘子无法到达则返回 -1，否则返回扩散分钟数。",
        "Run multi-source BFS from all initially rotten oranges, where each layer is one minute. If fresh oranges remain unreachable, return -1; otherwise return the elapsed minutes.",
    ),
    "course-schedule": LocalizedSeedExplanation(
        "把先修关系建成有向图，用入度和队列做拓扑排序。能取完所有课程说明无环，否则存在循环依赖。",
        "Build a directed prerequisite graph and run topological sorting with indegrees. Finishing all courses means no cycle; leftover courses indicate a cycle.",
    ),
    "implement-trie-prefix-tree": LocalizedSeedExplanation(
        "Trie 的每条边代表一个字符，节点记录是否为完整单词结尾。insert 建路径，search 要求结尾标记为真，startsWith 只要求前缀路径存在。",
        "A trie edge represents one character, and nodes mark whether a full word ends there. insert builds paths, search requires the terminal marker, and startsWith only requires the prefix path.",
    ),
    "permutations": LocalizedSeedExplanation(
        "回溯时维护已选择元素和 used 标记，每层选择一个未使用数字。完成长度为 n 的路径后加入答案，并排序保证输出稳定。",
        "Backtracking keeps the chosen path and used flags, picking one unused number per level. A length-n path is a permutation, and results are sorted for deterministic comparison.",
    ),
    "subsets": LocalizedSeedExplanation(
        "从空集开始，对每个元素选择加入或不加入。回溯枚举所有选择路径，并按长度和字典序整理输出。",
        "Start from the empty subset and decide for each element whether to include it. Backtracking enumerates all choices, then results are ordered deterministically.",
    ),
    "letter-combinations-of-a-phone-number": LocalizedSeedExplanation(
        "把每个数字映射到电话键盘字母，回溯逐位选择一个字母。输入为空时没有组合，非空时每条路径形成一个字符串。",
        "Map each digit to its phone keypad letters and backtrack one digit at a time. Empty input has no combinations; otherwise each full path forms one string.",
    ),
    "combination-sum": LocalizedSeedExplanation(
        "先排序候选数，再回溯选择当前数或后续数；同一个数可以重复使用。当前和超过 target 时剪枝，等于 target 时记录组合。",
        "Sort candidates and backtrack over choices, allowing the same candidate to be reused. Prune when the sum exceeds target and record paths whose sum equals target.",
    ),
    "generate-parentheses": LocalizedSeedExplanation(
        "回溯维护已经放入的左括号和右括号数量。只要左括号未超过 n 可继续放左括号，右括号数量小于左括号时才可放右括号。",
        "Backtrack with counts of opened and closed parentheses. Add '(' while opens < n, and add ')' only when closes < opens.",
    ),
    "word-search": LocalizedSeedExplanation(
        "从每个可能起点做 DFS，按单词字符顺序向四邻格扩展。当前路径中的格子不能重复使用，匹配完整单词即成功。",
        "Start DFS from every possible cell and follow the word character by character through four-neighbor moves. A cell cannot be reused in the current path.",
    ),
    "palindrome-partitioning": LocalizedSeedExplanation(
        "回溯枚举切分点，只在当前片段是回文时继续递归。到达字符串末尾时，一个完整的回文分割方案加入答案。",
        "Backtrack over cut positions and recurse only when the current segment is a palindrome. Reaching the end records one full palindrome partition.",
    ),
    "n-queens": LocalizedSeedExplanation(
        "逐行放置皇后，并用列、主对角线、副对角线集合判断冲突。放满 n 行后生成棋盘，最终排序保证多解输出稳定。",
        "Place queens row by row, using sets for occupied columns and both diagonal directions. When all rows are filled, build the board and sort solutions deterministically.",
    ),
    "search-insert-position": LocalizedSeedExplanation(
        "在有序数组上二分查找第一个大于等于 target 的位置。若 target 存在返回其下标，否则该位置就是插入下标。",
        "Binary search for the first position whose value is greater than or equal to target. If target exists this is its index; otherwise it is the insertion point.",
    ),
    "search-a-2d-matrix": LocalizedSeedExplanation(
        "矩阵每行有序且行首大于上一行行尾，可把它看作一个一维有序数组。二分时通过下标换算到行列位置。",
        "Because rows are sorted and each row starts after the previous row ends, treat the matrix as one sorted array and binary search with index-to-row/column conversion.",
    ),
    "find-first-and-last-position-of-element-in-sorted-array": LocalizedSeedExplanation(
        "分别二分 target 的左边界和右边界。左边界是第一个大于等于 target 的位置，右边界可由第一个大于 target 的位置减一得到。",
        "Run two binary searches: one for the first position >= target and one for the first position > target minus one.",
    ),
    "search-in-rotated-sorted-array": LocalizedSeedExplanation(
        "二分时至少有一半区间仍然有序。判断 target 是否落在有序半边内，决定保留哪一半继续搜索。",
        "During binary search, at least one half is still sorted. Check whether target lies in the sorted half to decide which half to keep.",
    ),
    "find-minimum-in-rotated-sorted-array": LocalizedSeedExplanation(
        "比较中点和右端点：若 mid 大于右端，最小值在右侧；否则最小值在左侧含 mid。不断收缩到最小元素。",
        "Compare the middle value with the right endpoint. If mid is greater, the minimum is to the right; otherwise it is on the left including mid.",
    ),
    "median-of-two-sorted-arrays": LocalizedSeedExplanation(
        "合并两个有序数组后，中位数位于中间一个或两个位置。实现直接合并保持顺序，再按总长度奇偶返回对应值。",
        "Merge the two sorted arrays while preserving order. The median is the middle value for odd total length or the average of the two middle values for even length.",
    ),
    "min-stack": LocalizedSeedExplanation(
        "主栈保存所有元素，辅助栈同步保存当前位置的最小值。push 时更新最小值，pop 时两个栈同时弹出，getMin 可 O(1) 返回。",
        "Keep a value stack and a parallel minimum stack. push records the new running minimum, pop removes from both stacks, and getMin reads the current minimum in O(1).",
    ),
    "decode-string": LocalizedSeedExplanation(
        "用栈保存进入括号前的字符串和重复次数。遇到右括号时弹出上下文，把当前片段重复 k 次后接回前缀。",
        "Use a stack for the previous string and repeat count before each bracket. On ']', repeat the current segment k times and append it to the saved prefix.",
    ),
    "daily-temperatures": LocalizedSeedExplanation(
        "单调递减栈保存还没找到更高温度的日期下标。当前温度更高时弹出栈顶，并用下标差填入等待天数。",
        "Use a decreasing stack of indices whose next warmer day is unknown. When the current temperature is warmer, pop indices and fill the day difference.",
    ),
    "largest-rectangle-in-histogram": LocalizedSeedExplanation(
        "单调递增栈保存柱子下标。遇到更矮柱子时，弹出的柱子高度确定，左右边界由当前下标和新栈顶决定，从而计算最大矩形。",
        "Maintain an increasing stack of bar indices. When a shorter bar appears, popped bars get their final height and width boundaries, allowing area updates.",
    ),
    "kth-largest-element-in-an-array": LocalizedSeedExplanation(
        "用大小为 k 的最小堆保存目前最大的 k 个数。遍历结束后堆顶就是第 k 大元素。",
        "Maintain a min-heap of size k containing the k largest values seen so far. After scanning, the heap root is the kth largest element.",
    ),
    "top-k-frequent-elements": LocalizedSeedExplanation(
        "先统计每个数字频率，再按频率降序、数值升序排序取前 k 个。这个排序规则让频率相同的答案稳定。",
        "Count frequencies, then sort by descending frequency and ascending value before taking k elements. The value tie-breaker makes output deterministic.",
    ),
    "find-median-from-data-stream": LocalizedSeedExplanation(
        "维护已加入数字的有序序列或双堆结构。每次 addNum 后更新数据结构，findMedian 根据元素个数奇偶返回中间值或中间两值平均。",
        "Maintain the inserted numbers in sorted form or with two heaps. After each addNum, findMedian returns the middle value or the average of the two middle values.",
    ),
    "best-time-to-buy-and-sell-stock": LocalizedSeedExplanation(
        "遍历价格时维护历史最低买入价。每天尝试以当前价格卖出并更新最大利润，若当前价更低则更新买入价。",
        "Track the lowest buy price seen so far. For each day, try selling at the current price to update profit, then update the minimum buy price if needed.",
    ),
    "jump-game": LocalizedSeedExplanation(
        "贪心维护当前能到达的最远下标。扫描过程中若当前位置超过最远可达下标则失败，否则不断扩展最远距离。",
        "Greedily track the farthest reachable index. If the scan reaches an index beyond it, the end is unreachable; otherwise keep extending the reach.",
    ),
    "jump-game-ii": LocalizedSeedExplanation(
        "贪心按层扩展跳跃范围。当前层边界内的点都可以用相同步数到达，扫描完边界后步数加一并进入下一层最远范围。",
        "Greedily expand jump ranges by layers. All indices within the current boundary are reachable in the same number of jumps; crossing the boundary increments the jump count.",
    ),
    "partition-labels": LocalizedSeedExplanation(
        "先记录每个字符最后出现位置。扫描字符串时维护当前片段必须覆盖的最远位置，当前位置到达该最远位置时即可切分。",
        "Record the last occurrence of each character. While scanning, track the farthest last occurrence required by the current partition; cut when the scan reaches it.",
    ),
    "pascals-triangle": LocalizedSeedExplanation(
        "逐行生成杨辉三角。每行两端为 1，中间位置等于上一行相邻两个数之和。",
        "Build Pascal's Triangle row by row. The ends are 1, and each inner value is the sum of the two adjacent values from the previous row.",
    ),
    "house-robber": LocalizedSeedExplanation(
        "动态规划维护到当前房屋为止的最优收益。每间房只有抢或不抢两种选择，抢它就不能抢前一间。",
        "Dynamic programming tracks the best profit up to each house. For each house, choose between skipping it or robbing it plus the best profit before the previous house.",
    ),
    "perfect-squares": LocalizedSeedExplanation(
        "令 dp[i] 表示组成 i 的最少完全平方数个数。枚举所有 j*j <= i，用 dp[i-j*j]+1 更新最小值。",
        "Let dp[i] be the fewest perfect squares summing to i. For every square j*j <= i, update dp[i] from dp[i-j*j] + 1.",
    ),
    "coin-change": LocalizedSeedExplanation(
        "完全背包 DP：dp[x] 表示凑成金额 x 的最少硬币数。对每个金额尝试每枚硬币，取可达状态的最小值。",
        "Use complete-knapsack DP where dp[x] is the fewest coins needed for amount x. Try every coin for each amount and keep the minimum reachable count.",
    ),
    "word-break": LocalizedSeedExplanation(
        "dp[i] 表示前 i 个字符能否被字典切分。若存在 j 使 dp[j] 为真且 s[j:i] 在词典中，则 dp[i] 为真。",
        "Let dp[i] mean the prefix of length i can be segmented. If some dp[j] is true and s[j:i] is in the dictionary, then dp[i] is true.",
    ),
    "longest-increasing-subsequence": LocalizedSeedExplanation(
        "维护 tails 数组，tails[len] 是长度 len+1 的递增子序列可能的最小结尾。每个数用二分替换位置，tails 长度就是答案。",
        "Maintain tails, where tails[len] is the smallest possible tail of an increasing subsequence of length len+1. Binary search replacement keeps tails optimal.",
    ),
    "maximum-product-subarray": LocalizedSeedExplanation(
        "因为负数会交换最大和最小乘积，需要同时维护以当前位置结尾的最大乘积和最小乘积。每步用当前数更新全局最大值。",
        "Because a negative value can turn the smallest product into the largest, track both maximum and minimum products ending at each position.",
    ),
    "partition-equal-subset-sum": LocalizedSeedExplanation(
        "若总和为奇数必然不能平分；否则问题变成是否存在子集和为 total/2。用一维背包布尔 DP 判断可达金额。",
        "If the total sum is odd, equal partition is impossible. Otherwise solve subset-sum for total/2 using one-dimensional boolean knapsack DP.",
    ),
    "longest-valid-parentheses": LocalizedSeedExplanation(
        "栈中保存可能作为合法段起点前一位的下标。遇到无法匹配的右括号时重置基准，匹配成功时用当前下标减栈顶更新长度。",
        "Use a stack of indices, with the top marking the position before the current valid segment. Reset on unmatched ')' and update length after successful matches.",
    ),
    "unique-paths": LocalizedSeedExplanation(
        "从左上到右下总共要走 m-1 次向下和 n-1 次向右。答案是这些步数排列的组合数，也可用 DP 逐格累加。",
        "A path from top-left to bottom-right consists of m-1 down moves and n-1 right moves. The answer is the number of ways to arrange those moves, equivalently grid DP.",
    ),
    "minimum-path-sum": LocalizedSeedExplanation(
        "dp[i][j] 表示到达当前格子的最小路径和，只能从上方或左方转移。每格取两者较小值加当前代价。",
        "Let dp[i][j] be the minimum path sum to a cell. Since moves only come from above or left, add the current cost to the smaller predecessor.",
    ),
    "longest-palindromic-substring": LocalizedSeedExplanation(
        "枚举每个字符和字符间隙作为中心向两侧扩展，记录最长回文区间。奇数和偶数长度回文都能覆盖。",
        "Expand around every character and every gap between characters as centers, recording the longest palindrome interval. This covers odd and even lengths.",
    ),
    "longest-common-subsequence": LocalizedSeedExplanation(
        "二维 DP 中 dp[i][j] 表示两个前缀的最长公共子序列长度。字符相等时来自左上加一，否则取上方和左方最大值。",
        "Use 2D DP where dp[i][j] is the LCS length of two prefixes. Equal characters extend dp[i-1][j-1]; otherwise take the max of top and left.",
    ),
    "edit-distance": LocalizedSeedExplanation(
        "dp[i][j] 表示把 word1 前 i 个字符变成 word2 前 j 个字符的最少操作。插入、删除、替换分别对应三个相邻状态。",
        "Let dp[i][j] be the minimum operations to convert the first i characters of word1 into the first j characters of word2. Insert, delete, and replace come from the three neighboring states.",
    ),
    "single-number": LocalizedSeedExplanation(
        "异或满足 x^x=0 且 x^0=x。把所有数字异或起来，成对出现的数字会抵消，只剩出现一次的数字。",
        "XOR cancels equal pairs because x^x=0 and leaves x when XORed with 0. XORing all values leaves the number that appears once.",
    ),
    "majority-element": LocalizedSeedExplanation(
        "Boyer-Moore 投票维护候选值和计数。多数元素出现次数超过一半，抵消掉不同元素后最终候选就是多数元素。",
        "Boyer-Moore voting keeps a candidate and count. Since the majority appears more than half the time, canceling different values leaves it as the final candidate.",
    ),
    "sort-colors": LocalizedSeedExplanation(
        "荷兰国旗算法用三个指针维护 0 区、1 区和 2 区。扫描时把 0 交换到前面，把 2 交换到后面，1 留在中间。",
        "Dutch National Flag partitioning keeps regions for 0s, 1s, and 2s. Swap 0s to the front, 2s to the back, and leave 1s in the middle.",
    ),
    "next-permutation": LocalizedSeedExplanation(
        "从右向左找第一个下降位置作为 pivot，再在右侧找刚好更大的元素交换。最后反转右侧后缀，使它成为最小的更大排列。",
        "Find the first descending pivot from the right, swap it with the smallest larger value in the suffix, then reverse the suffix to get the next lexicographic permutation.",
    ),
    "find-the-duplicate-number": LocalizedSeedExplanation(
        "把数组看作从下标到值的链表映射，重复数字会形成环。Floyd 快慢指针先相遇，再从起点和相遇点同步前进定位环入口。",
        "View the array as a linked structure from index to value; the duplicate creates a cycle. Floyd's slow/fast pointers meet inside the cycle and then locate the cycle entry.",
    ),
}


def solution_explanation_for_slug(slug: str, locale: str | None = None) -> str | None:
    explanation = SEED_EXPLANATIONS.get(slug)
    if explanation is None:
        return None
    return explanation.en if uses_source_text(normalize_locale(locale)) else explanation.zh


def sample_explanation_for_slug(
    slug: str,
    index: int,
    input_text: str,
    output_text: str,
    locale: str | None = None,
) -> str | None:
    explanation = SEED_EXPLANATIONS.get(slug)
    if explanation is None:
        return None
    output = _compact(output_text) or "empty output"
    sample_input = _compact(input_text)
    normalized = normalize_locale(locale)
    if uses_source_text(normalized):
        method = _first_sentence(explanation.en)
        return f"Example {index + 1} uses input {sample_input}. {method} Applying that logic produces {output}."
    method = _first_sentence(explanation.zh)
    return f"示例 {index + 1} 的输入是 {sample_input}。{method} 按这个逻辑处理后得到 {output}。"


def _first_sentence(text: str) -> str:
    for separator in ("。", ". "):
        if separator in text:
            sentence = text.split(separator, 1)[0].strip()
            return sentence + ("。" if separator == "。" else ".")
    return text.strip()


def _compact(text: str, limit: int = 140) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."
