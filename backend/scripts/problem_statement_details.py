"""Problem-statement enrichment for bundled seed problems.

The seed catalog keeps compact one-line summaries next to testcase metadata.
This module expands those summaries with short semantic clarifications: what the
task means, how the modelled structure behaves, and how ties or ordering should
be understood. It intentionally avoids repeating function signatures, judge I/O
mechanics, or broad testing advice already covered elsewhere in the UI.
"""

_OLD_GENERATED_MARKERS = (
    "Function contract",
    "Parameter contract",
    "Return contract",
    "Judging and representation notes",
    "Edge cases to consider",
)


_DETAILS: dict[str, list[str]] = {
    "two-sum": [
        "Choose two different positions in the array whose values add to the target. The problem guarantees one valid pair, so the answer is the pair of zero-based indexes for that pair.",
    ],
    "add-two-numbers": [
        "Each array stores a non-negative integer from least significant digit to most significant digit. Add the two numbers the same way you would add by hand, carrying into the next position as needed.",
    ],
    "longest-substring-without-repeating-characters": [
        "A substring is one contiguous block of characters. The answer is the length of the longest block in which no character appears twice.",
    ],
    "valid-parentheses": [
        "A string is valid only when every opening bracket is closed by the same type of bracket and brackets close in the reverse order in which they were opened.",
    ],
    "alien-dictionary": [
        "Only the relative order implied by adjacent words is known. For each neighboring pair, the first different characters determine one precedence rule; later characters in that pair do not add more information.",
        "If a longer word appears before its exact prefix, the list cannot be sorted by any alphabet. A cycle in the precedence graph is also impossible, because it would require one letter to come before itself.",
    ],
    "two-car-parking-lot": [
        "The grid contains uppercase A and B for the two cars, lowercase a and b for their matching parking spots, # for walls, and . for empty pavement. Cars are distinguishable: A must finish on a, and B must finish on b.",
        "Each move chooses one car and moves it one orthogonal cell. A car cannot leave the grid, enter a wall, or move into the other car's current cell; the question is whether some sequence reaches the two final positions at the same time.",
    ],
    "maximum-subarray": [
        "The subarray must contain at least one element and must use consecutive positions. Negative numbers may appear, so the best answer can be a single element.",
    ],
    "group-anagrams": [
        "Two words belong in the same group when they contain exactly the same characters with the same counts. Within this platform, sort each group and then sort the groups by their first word so equivalent answers have one stable order.",
    ],
    "merge-intervals": [
        "Each interval includes both endpoints. If two intervals overlap or touch at an endpoint, they become one interval spanning the smallest start to the largest end.",
    ],
    "climbing-stairs": [
        "Count different step sequences, not just different totals. For example, taking 1 then 2 steps is different from taking 2 then 1 steps.",
    ],
    "container-with-most-water": [
        "Choosing two indices creates a container whose width is the distance between them and whose height is limited by the shorter line. Maximize that area.",
    ],
    "logistic-regression-sigmoid": [
        "Compute the linear score by multiplying each weight with the matching feature, summing those products, and adding the bias. Then apply the sigmoid function to convert that score into a probability.",
    ],
    "knn-majority-vote": [
        "Distance is Euclidean distance between feature vectors; using squared distance gives the same nearest-neighbor order. If distances tie, prefer the earlier training point; if labels tie in the vote, prefer the lexicographically smaller label.",
    ],
    "kmeans-one-iteration": [
        "This is only the assignment step of k-means. For each point, find the closest centroid and record that centroid's zero-based index; if two centroids are equally close, choose the smaller index.",
    ],
    "scaled-dot-product-attention": [
        "Score each key by its dot product with the query divided by the square root of the vector length. Softmax those scores and use the resulting weights to average the value vectors.",
    ],
    "softmax-cross-entropy": [
        "Interpret the logits as unnormalized class scores. The loss is the negative log probability assigned to the target class after softmax.",
    ],
    "attention-mask-apply": [
        "Only positions marked visible by the mask participate in the softmax. Masked positions contribute no probability and must remain zero in the final distribution.",
    ],
    "longest-consecutive-sequence": [
        "Consecutive means values differ by exactly one, regardless of their positions in the original array. Count the longest value run such as x, x + 1, x + 2, and so on.",
    ],
    "move-zeroes": [
        "All non-zero values keep their original relative order. The array length stays the same, with all zeroes occupying the remaining positions at the end.",
    ],
    "3sum": [
        "A valid triple uses three different indices and has values summing to zero. Return each distinct value triple once, sorted internally and in lexicographic order overall.",
    ],
    "trapping-rain-water": [
        "Water above a bar is limited by the taller boundary available on its left and on its right. Sum the trapped water over all positions.",
    ],
    "find-all-anagrams-in-a-string": [
        "Look only at substrings whose length equals p. A match has exactly the same character counts as p, and answers are the starting indices in increasing order.",
    ],
    "subarray-sum-equals-k": [
        "A subarray is a contiguous slice. Count every slice whose elements sum exactly to k, including overlapping slices.",
    ],
    "sliding-window-maximum": [
        "The first window covers the first k elements, then the window moves one position at a time. Report the maximum value seen in each window in left-to-right order.",
    ],
    "minimum-window-substring": [
        "The window must contain every character from t with the required multiplicity. If several windows have the minimum length, choose the one that starts earliest; if none exists, return the empty string.",
    ],
    "rotate-array": [
        "A right rotation moves each value k positions toward the end, wrapping values that pass the end back to the front. When k is larger than the array length, only the remainder matters.",
    ],
    "product-of-array-except-self": [
        "For each position, multiply all values except the one at that position. Do this without division, so arrays containing zero still have well-defined answers.",
    ],
    "first-missing-positive": [
        "The answer is the smallest positive integer starting from 1 that is absent from the array. Zero, negative numbers, and very large numbers do not directly fill that first-positive gap.",
    ],
    "set-matrix-zeroes": [
        "Rows and columns are chosen from the zeroes present in the original matrix. A zero written during the update should not cause extra rows or columns to be cleared.",
    ],
    "spiral-matrix": [
        "Start at the top-left corner and walk around the current outer border clockwise. After finishing a border, move inward and repeat until every cell has been visited once.",
    ],
    "rotate-image": [
        "Rotate the square matrix as an image: the top row becomes the right column, the right column becomes the bottom row, and so on.",
    ],
    "search-a-2d-matrix-ii": [
        "The row and column ordering lets you discard a row or column after each comparison. The question is only whether the target value appears at least once.",
    ],
    "intersection-of-two-linked-lists": [
        "In this array model, two lists intersect when they share the same suffix of values. Return the first value in that shared suffix, or null if no shared suffix exists.",
    ],
    "reverse-linked-list": [
        "The array lists node values from head to tail. Reversing the list means returning those values from tail to head.",
    ],
    "palindrome-linked-list": [
        "The list is a palindrome when reading the node values from head to tail gives the same sequence as reading them from tail to head.",
    ],
    "linked-list-cycle": [
        "The pos value tells where the tail points back into the list. A pos of -1 means the tail points nowhere and the list has no cycle.",
    ],
    "linked-list-cycle-ii": [
        "When a cycle exists, the entry is the first node reached again by following next pointers from the head. In this array model, that entry is exactly the pos index.",
    ],
    "merge-two-sorted-lists": [
        "Both input lists are already sorted in nondecreasing order. Preserve all values from both lists and produce one nondecreasing sequence.",
    ],
    "remove-nth-node-from-end-of-list": [
        "The node to remove is counted from the tail: n = 1 removes the last node, n = 2 removes the node before it, and so on.",
    ],
    "swap-nodes-in-pairs": [
        "Swap the first node with the second, the third with the fourth, and continue in pairs. If one node is left over at the end, it stays where it is.",
    ],
    "reverse-nodes-in-k-group": [
        "Reverse only complete blocks of k consecutive nodes. Any final block with fewer than k nodes remains in its original order.",
    ],
    "copy-list-with-random-pointer": [
        "Each node has both a next pointer and a random pointer. The returned list must describe a deep copy with the same values and random relationships, not references to the original nodes.",
    ],
    "sort-list": [
        "Sort the linked-list values into nondecreasing order while preserving every value from the original list.",
    ],
    "merge-k-sorted-lists": [
        "Each input list is sorted. Merge all values from all lists into one sorted sequence, including duplicates.",
    ],
    "lru-cache": [
        "An LRU cache evicts the least recently used key when it needs room for a new key. Both a successful get and a put make that key the most recently used.",
    ],
    "binary-tree-inorder-traversal": [
        "The tree is represented as a level-order array with null placeholders. Inorder traversal visits the left subtree, then the current node, then the right subtree.",
    ],
    "maximum-depth-of-binary-tree": [
        "Depth counts nodes on the longest path from the root down to a leaf. An empty tree has depth 0.",
    ],
    "invert-binary-tree": [
        "Invert the tree by swapping the left and right child of every node. The shape is mirrored around the root.",
    ],
    "symmetric-tree": [
        "A tree is symmetric when the left and right subtrees are mirror images: outside branches match outside branches and inside branches match inside branches.",
    ],
    "diameter-of-binary-tree": [
        "The diameter is the number of edges on the longest path between any two nodes. The path may or may not pass through the root.",
    ],
    "binary-tree-level-order-traversal": [
        "Visit nodes breadth-first from the root. Group values by depth, from top level to bottom level.",
    ],
    "convert-sorted-array-to-binary-search-tree": [
        "Build a height-balanced search tree from the sorted values. This seed uses the lower middle value as the root of each range so the answer is deterministic.",
    ],
    "validate-binary-search-tree": [
        "Every node must be strictly greater than all values in its left subtree and strictly less than all values in its right subtree. Equal values violate the BST rule.",
    ],
    "kth-smallest-element-in-a-bst": [
        "Because it is a binary search tree, visiting values in inorder order gives them sorted from smallest to largest. The kth smallest is one-based.",
    ],
    "binary-tree-right-side-view": [
        "Imagine looking at the tree from its right side. At each depth, the visible value is the rightmost node present at that level.",
    ],
    "flatten-binary-tree-to-linked-list": [
        "Flattening follows preorder traversal. After flattening, each node's right pointer leads to the next preorder node and left pointers are ignored.",
    ],
    "construct-binary-tree-from-preorder-and-inorder-traversal": [
        "Preorder tells you each subtree root before its children, while inorder splits a subtree into left and right sides. Values are distinct, so the reconstruction is unique.",
    ],
    "path-sum-iii": [
        "A valid path moves downward from parent to child, but it may start at any node and end at any descendant. Count all downward paths whose values sum to the target.",
    ],
    "lowest-common-ancestor-of-a-binary-tree": [
        "The lowest common ancestor is the deepest node that has both target nodes in its subtree, allowing a node to be an ancestor of itself.",
    ],
    "binary-tree-maximum-path-sum": [
        "A path can start and end at any nodes, must follow parent-child links, and cannot branch. It must contain at least one node.",
    ],
    "number-of-islands": [
        "An island is a maximal group of land cells connected horizontally or vertically. Diagonal contact does not connect islands.",
    ],
    "rotting-oranges": [
        "Rot spreads in simultaneous one-minute waves from every currently rotten orange to adjacent fresh oranges. If any fresh orange can never be reached, the answer is -1.",
    ],
    "course-schedule": [
        "Each prerequisite pair says one course must be completed before another. All courses can be completed exactly when these dependency rules contain no cycle.",
    ],
    "implement-trie-prefix-tree": [
        "A trie stores words by sharing common prefixes. Search succeeds only for a full inserted word, while startsWith succeeds for any inserted prefix path.",
    ],
    "permutations": [
        "Use every input number exactly once in each arrangement. Return all possible arrangements in lexicographic order.",
    ],
    "subsets": [
        "A subset may include or exclude each input number. Return the empty subset, every partial subset, and the full set in deterministic lexicographic order.",
    ],
    "letter-combinations-of-a-phone-number": [
        "Use the standard phone keypad mapping for digits 2 through 9. Build strings by choosing one mapped letter per digit, keeping keypad traversal order.",
    ],
    "combination-sum": [
        "A candidate can be chosen more than once. Each returned combination should be nondecreasing so the same multiset is not reported in multiple orders.",
    ],
    "generate-parentheses": [
        "A string is balanced when every prefix has at least as many opening brackets as closing brackets, and the final counts are equal.",
    ],
    "word-search": [
        "Letters must be connected horizontally or vertically in order. A board cell may be used at most once in the same word path.",
    ],
    "palindrome-partitioning": [
        "Cut the string into consecutive pieces. A partition is valid only when every piece reads the same forward and backward.",
    ],
    "n-queens": [
        "Queens attack along rows, columns, and both diagonals. A valid board places exactly one queen per row with no attacks.",
    ],
    "search-insert-position": [
        "If the target exists, use its current index. Otherwise, find the position where inserting it would keep the array sorted.",
    ],
    "search-a-2d-matrix": [
        "The matrix behaves like one sorted list read row by row: every row is sorted, and each row starts after the previous row ends.",
    ],
    "find-first-and-last-position-of-element-in-sorted-array": [
        "Find the leftmost and rightmost occurrence of the target. If the target is absent, both positions are -1.",
    ],
    "search-in-rotated-sorted-array": [
        "The array was originally sorted in ascending order, then rotated at one pivot. Values are distinct, and the answer is the target's index or -1.",
    ],
    "find-minimum-in-rotated-sorted-array": [
        "The input is an ascending array rotated at an unknown pivot. The minimum is the first value in the original sorted order.",
    ],
    "median-of-two-sorted-arrays": [
        "Consider the two arrays as one sorted sequence without physically needing to merge them. For even total length, the median is the average of the two middle values.",
    ],
    "min-stack": [
        "A MinStack behaves like a normal stack but can also report the current minimum value among all elements still in the stack.",
    ],
    "decode-string": [
        "A number before brackets repeats the entire bracketed substring. Nested encodings are decoded from the inside out.",
    ],
    "daily-temperatures": [
        "For each day, look to the right for the first day with a strictly warmer temperature. Report how many days away it is, or 0 if it never appears.",
    ],
    "largest-rectangle-in-histogram": [
        "A rectangle must cover consecutive bars, and its height is limited by the shortest bar in that span. Maximize width times height.",
    ],
    "kth-largest-element-in-an-array": [
        "Rank values as they would appear in descending sorted order, including duplicates as separate positions. The kth largest is one-based.",
    ],
    "top-k-frequent-elements": [
        "Count how often each value appears. Higher frequency comes first; when frequencies tie, smaller values come first.",
    ],
    "find-median-from-data-stream": [
        "Numbers are added over time. Each median query asks for the median of all numbers seen so far; for an even count, average the two middle values.",
    ],
    "best-time-to-buy-and-sell-stock": [
        "You may complete at most one transaction, and the buy day must come before the sell day. If no profitable transaction exists, the maximum profit is 0.",
    ],
    "jump-game": [
        "From each index you may move up to that many steps to the right. Decide whether some sequence of jumps can reach the last index.",
    ],
    "jump-game-ii": [
        "From each index you may move up to that many steps to the right. Find the fewest jumps needed to reach the last index.",
    ],
    "partition-labels": [
        "Each character may appear in only one final part. Cut as early as possible while still ensuring all future occurrences of characters in the current part are included.",
    ],
    "pascals-triangle": [
        "The first row is [1]. Every later row starts and ends with 1, and each interior value is the sum of the two values above it.",
    ],
    "house-robber": [
        "Choosing one house prevents choosing either adjacent house. Maximize the total money from a set of non-adjacent houses.",
    ],
    "perfect-squares": [
        "Use square numbers such as 1, 4, 9, and 16 as building blocks. Find the smallest count of such numbers whose sum is n.",
    ],
    "coin-change": [
        "Each coin denomination may be used repeatedly. Find the smallest number of coins that sums exactly to the amount, or -1 if no exact sum is possible.",
    ],
    "word-break": [
        "Split the string into consecutive dictionary words. Dictionary entries may be reused, and every character must belong to one chosen word.",
    ],
    "longest-increasing-subsequence": [
        "A subsequence keeps the original order but may skip elements. It is valid only when each chosen value is strictly larger than the previous chosen value.",
    ],
    "maximum-product-subarray": [
        "The subarray must be contiguous and non-empty. Negative values matter because multiplying by a negative can turn a small negative product into a large positive one later.",
    ],
    "partition-equal-subset-sum": [
        "Decide whether the values can be divided into two groups with the same total sum. Each array element must belong to exactly one of the two groups.",
    ],
    "longest-valid-parentheses": [
        "A valid parentheses substring is contiguous and fully balanced. Return the length of the longest such substring.",
    ],
    "unique-paths": [
        "Start in the top-left cell and finish in the bottom-right cell. Each move goes exactly one cell right or one cell down.",
    ],
    "minimum-path-sum": [
        "Start in the top-left cell and finish in the bottom-right cell. A path's cost is the sum of every cell visited, including the start and destination; choose the path with the smallest cost.",
    ],
    "longest-palindromic-substring": [
        "The answer must be contiguous. If more than one longest palindrome exists, choose the one with the earliest starting position.",
    ],
    "longest-common-subsequence": [
        "A subsequence keeps characters in order but may skip characters. Count the longest sequence that can be formed from both strings this way.",
    ],
    "edit-distance": [
        "You may insert one character, delete one character, or replace one character per operation. Find the fewest operations to turn the first word into the second.",
    ],
    "single-number": [
        "All repeated values appear exactly twice. The answer is the only value whose frequency is one.",
    ],
    "majority-element": [
        "The majority element appears strictly more than n / 2 times, so it is guaranteed to be the unique value with that property.",
    ],
    "sort-colors": [
        "Treat 0, 1, and 2 as three ordered color labels. Rearrange all values so every 0 comes first, then every 1, then every 2.",
    ],
    "next-permutation": [
        "Permutations are ordered lexicographically. Move to the next larger ordering using the same values; if none exists, wrap around to the smallest ordering.",
    ],
    "find-the-duplicate-number": [
        "There are n + 1 positions but only values 1 through n, so at least one value repeats. Return the repeated value.",
    ],
}


def _strip_old_generated_content(description: str) -> str:
    base = description.strip()
    marker_positions = [base.find(marker) for marker in _OLD_GENERATED_MARKERS if marker in base]
    if not marker_positions:
        return base
    return base[: min(marker_positions)].strip()


def enhanced_description(problem: dict) -> str:
    base = _strip_old_generated_content(str(problem.get("description", "")))
    details = _DETAILS.get(problem["slug"], [])
    if not details:
        return base
    return "\n\n".join([base, *details]).strip()


def enrich_problem_descriptions(items: list[dict]) -> None:
    """Expand problem descriptions in place using only public catalog metadata."""
    for item in items:
        item["problem"]["description"] = enhanced_description(item["problem"])
