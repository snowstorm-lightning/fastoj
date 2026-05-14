import textwrap

FUNCTION_ENTRYPOINTS = {
    "two-sum": {
        "names": ["two_sum", "twoSum"],
        "reader": "nums = json.loads(lines[0])\ntarget = json.loads(lines[1])",
        "call": "func(nums, target)",
        "formatter": "json.dumps(result, separators=(',', ':'))",
    },
    "add-two-numbers": {
        "names": ["add_two_numbers", "addTwoNumbers"],
        "reader": "l1 = json.loads(lines[0])\nl2 = json.loads(lines[1])",
        "call": "func(l1, l2)",
        "formatter": "json.dumps(result, separators=(',', ':'))",
    },
    "longest-substring-without-repeating": {
        "names": ["length_of_longest_substring", "lengthOfLongestSubstring"],
        "reader": "s = raw",
        "call": "func(s)",
        "formatter": "str(result)",
    },
    "logistic-regression-sigmoid": {
        "names": ["predict_probability", "predictProbability"],
        "reader": "weights = json.loads(lines[0])\nbias = json.loads(lines[1])\nfeatures = json.loads(lines[2])",
        "call": "func(weights, bias, features)",
        "formatter": "format(float(result), '.4f')",
    },
    "knn-majority-vote": {
        "names": ["predict_knn", "predictKnn"],
        "reader": "points = json.loads(lines[0])\nlabels = json.loads(lines[1])\nquery = json.loads(lines[2])\nk = int(lines[3])",
        "call": "func(points, labels, query, k)",
        "formatter": "str(result)",
    },
    "kmeans-one-iteration": {
        "names": ["assign_clusters", "assignClusters"],
        "reader": "points = json.loads(lines[0])\ncentroids = json.loads(lines[1])",
        "call": "func(points, centroids)",
        "formatter": "json.dumps(result, separators=(',', ':'))",
    },
    "scaled-dot-product-attention": {
        "names": ["attention_row", "attentionRow"],
        "reader": "query = json.loads(lines[0])\nkeys = json.loads(lines[1])\nvalues = json.loads(lines[2])",
        "call": "func(query, keys, values)",
        "formatter": "json.dumps([round(float(x), 4) for x in result], separators=(',', ':'))",
    },
    "softmax-cross-entropy": {
        "names": ["cross_entropy_loss", "crossEntropyLoss"],
        "reader": "logits = json.loads(lines[0])\ntarget = int(lines[1])",
        "call": "func(logits, target)",
        "formatter": "format(float(result), '.4f')",
    },
    "attention-mask-apply": {
        "names": ["masked_softmax", "maskedSoftmax"],
        "reader": "scores = json.loads(lines[0])\nmask = json.loads(lines[1])",
        "call": "func(scores, mask)",
        "formatter": "json.dumps([format(float(x), '.4f') for x in result], separators=(',', ':')).replace('\"', '')",
    },
}


def wrap_function_submission(code: str, language: str, problem_slug: str) -> str:
    """Wrap a user function body in a stdin/stdout harness for judge execution."""
    if language != "python":
        raise ValueError("Function mode currently supports Python submissions only")

    spec = FUNCTION_ENTRYPOINTS.get(problem_slug)
    if not spec:
        raise ValueError("Function mode is not available for this problem")

    names = ", ".join(repr(name) for name in spec["names"])
    reader = textwrap.indent(spec["reader"], "    ")
    harness = f"""

if __name__ == "__main__":
    import json
    import sys

    raw = sys.stdin.read().strip()
    lines = raw.splitlines()

{reader}
    func = None
    for name in [{names}]:
        candidate = globals().get(name)
        if callable(candidate):
            func = candidate
            break
    if func is None and "Solution" in globals():
        solution = Solution()
        for name in [{names}]:
            candidate = getattr(solution, name, None)
            if callable(candidate):
                func = candidate
                break
    if func is None:
        raise NameError("Expected one of these functions: {', '.join(spec['names'])}")
    result = {spec["call"]}
    print({spec["formatter"]})
"""
    return code.rstrip() + "\n" + harness
