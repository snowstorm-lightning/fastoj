import json
import re
import textwrap
from dataclasses import dataclass

from backend.services.problem_modes import FUNCTION_SIGNATURES

FUNCTION_ENTRYPOINTS = {
    "two-sum": {
        "names": ["two_sum", "twoSum"],
        "reader": "nums = json.loads(lines[0])\ntarget = json.loads(lines[1])",
        "call": "func(nums, target)",
        "formatter": "json.dumps(result, separators=(',', ':'))",
        "js_reader": "const nums = JSON.parse(lines[0]);\nconst target = JSON.parse(lines[1]);",
        "js_call": "fn(nums, target)",
        "js_formatter": "JSON.stringify(result)",
        "cpp_reader": "auto nums = parseIntVector(lines[0]);\n    int target = stoi(lines[1]);",
        "cpp_call": "two_sum(nums, target)",
        "cpp_formatter": "formatIntVector(result)",
        "java_reader": "int[] nums = parseIntArray(lines.get(0));\n        int target = Integer.parseInt(lines.get(1).trim());",
        "java_call": "solver.twoSum(nums, target)",
        "java_formatter": "formatIntArray(result)",
        "go_reader": "nums := parseInts(lines[0])\n\ttarget, _ := strconv.Atoi(strings.TrimSpace(lines[1]))",
        "go_call": "twoSum(nums, target)",
        "go_formatter": "formatInts(result)",
        "c_reader": "IntVec nums = parse_int_vec(lines[0]);\n    int target = atoi(lines[1]);",
        "c_call": "two_sum(nums.data, nums.len, target, &result_len)",
        "c_formatter": "print_int_array(result, result_len)",
    },
    "add-two-numbers": {
        "names": ["add_two_numbers", "addTwoNumbers"],
        "reader": "l1 = json.loads(lines[0])\nl2 = json.loads(lines[1])",
        "call": "func(l1, l2)",
        "formatter": "json.dumps(result, separators=(',', ':'))",
        "js_reader": "const l1 = JSON.parse(lines[0]);\nconst l2 = JSON.parse(lines[1]);",
        "js_call": "fn(l1, l2)",
        "js_formatter": "JSON.stringify(result)",
        "cpp_reader": "auto l1 = parseIntVector(lines[0]);\n    auto l2 = parseIntVector(lines[1]);",
        "cpp_call": "add_two_numbers(l1, l2)",
        "cpp_formatter": "formatIntVector(result)",
        "java_reader": "int[] l1 = parseIntArray(lines.get(0));\n        int[] l2 = parseIntArray(lines.get(1));",
        "java_call": "solver.addTwoNumbers(l1, l2)",
        "java_formatter": "formatIntArray(result)",
        "go_reader": "l1 := parseInts(lines[0])\n\tl2 := parseInts(lines[1])",
        "go_call": "addTwoNumbers(l1, l2)",
        "go_formatter": "formatInts(result)",
        "c_reader": "IntVec l1 = parse_int_vec(lines[0]);\n    IntVec l2 = parse_int_vec(lines[1]);",
        "c_call": "add_two_numbers(l1.data, l1.len, l2.data, l2.len, &result_len)",
        "c_formatter": "print_int_array(result, result_len)",
    },
    "longest-substring-without-repeating": {
        "names": ["length_of_longest_substring", "lengthOfLongestSubstring"],
        "reader": "s = raw",
        "call": "func(s)",
        "formatter": "str(result)",
        "js_reader": "const s = raw;",
        "js_call": "fn(s)",
        "js_formatter": "String(result)",
        "cpp_reader": "string s = raw;",
        "cpp_call": "length_of_longest_substring(s)",
        "cpp_formatter": "to_string(result)",
        "java_reader": "String s = raw;",
        "java_call": "solver.lengthOfLongestSubstring(s)",
        "java_formatter": "String.valueOf(result)",
        "go_reader": "s := raw",
        "go_call": "lengthOfLongestSubstring(s)",
        "go_formatter": "strconv.Itoa(result)",
        "c_reader": "const char *s = raw;",
        "c_call": "length_of_longest_substring(s)",
        "c_formatter": "printf(\"%d\\n\", result)",
    },
    "valid-parentheses": {
        "names": ["is_valid_parentheses", "isValidParentheses"],
        "reader": "s = raw",
        "call": "func(s)",
        "formatter": "str(result).lower()",
        "js_reader": "const s = raw;",
        "js_call": "fn(s)",
        "js_formatter": "String(Boolean(result))",
        "cpp_reader": "string s = raw;",
        "cpp_call": "is_valid_parentheses(s)",
        "cpp_formatter": "result ? string(\"true\") : string(\"false\")",
        "java_reader": "String s = raw;",
        "java_call": "solver.isValidParentheses(s)",
        "java_formatter": "String.valueOf(result)",
        "go_reader": "s := raw",
        "go_call": "isValidParentheses(s)",
        "go_formatter": "strconv.FormatBool(result)",
        "c_reader": "const char *s = raw;",
        "c_call": "is_valid_parentheses(s)",
        "c_formatter": "printf(\"%s\\n\", result ? \"true\" : \"false\")",
    },
    "logistic-regression-sigmoid": {
        "names": ["predict_probability", "predictProbability"],
        "reader": "weights = json.loads(lines[0])\nbias = json.loads(lines[1])\nfeatures = json.loads(lines[2])",
        "call": "func(weights, bias, features)",
        "formatter": "format(float(result), '.4f')",
        "js_reader": "const weights = JSON.parse(lines[0]);\nconst bias = JSON.parse(lines[1]);\nconst features = JSON.parse(lines[2]);",
        "js_call": "fn(weights, bias, features)",
        "js_formatter": "Number(result).toFixed(4)",
        "cpp_reader": "auto weights = parseDoubleVector(lines[0]);\n    double bias = stod(lines[1]);\n    auto features = parseDoubleVector(lines[2]);",
        "cpp_call": "predict_probability(weights, bias, features)",
        "cpp_formatter": "formatDouble(result)",
        "java_reader": "double[] weights = parseDoubleArray(lines.get(0));\n        double bias = Double.parseDouble(lines.get(1).trim());\n        double[] features = parseDoubleArray(lines.get(2));",
        "java_call": "solver.predictProbability(weights, bias, features)",
        "java_formatter": "String.format(Locale.US, \"%.4f\", result)",
        "go_reader": "weights := parseFloats(lines[0])\n\tbias, _ := strconv.ParseFloat(strings.TrimSpace(lines[1]), 64)\n\tfeatures := parseFloats(lines[2])",
        "go_call": "predictProbability(weights, bias, features)",
        "go_formatter": "fmt.Sprintf(\"%.4f\", result)",
        "c_reader": "DoubleVec weights = parse_double_vec(lines[0]);\n    double bias = atof(lines[1]);\n    DoubleVec features = parse_double_vec(lines[2]);",
        "c_call": "predict_probability(weights.data, weights.len, bias, features.data, features.len)",
        "c_formatter": "printf(\"%.4f\\n\", result)",
    },
    "knn-majority-vote": {
        "names": ["predict_knn", "predictKnn"],
        "reader": "points = json.loads(lines[0])\nlabels = json.loads(lines[1])\nquery = json.loads(lines[2])\nk = int(lines[3])",
        "call": "func(points, labels, query, k)",
        "formatter": "str(result)",
        "js_reader": "const points = JSON.parse(lines[0]);\nconst labels = JSON.parse(lines[1]);\nconst query = JSON.parse(lines[2]);\nconst k = Number(lines[3]);",
        "js_call": "fn(points, labels, query, k)",
        "js_formatter": "String(result)",
        "cpp_reader": "auto points = parseDoubleMatrix(lines[0]);\n    auto labels = parseStringVector(lines[1]);\n    auto query = parseDoubleVector(lines[2]);\n    int k = stoi(lines[3]);",
        "cpp_call": "predict_knn(points, labels, query, k)",
        "cpp_formatter": "result",
        "java_reader": "double[][] points = parseDoubleMatrix(lines.get(0));\n        String[] labels = parseStringArray(lines.get(1));\n        double[] query = parseDoubleArray(lines.get(2));\n        int k = Integer.parseInt(lines.get(3).trim());",
        "java_call": "solver.predictKnn(points, labels, query, k)",
        "java_formatter": "result",
        "go_reader": "points := parseFloatMatrix(lines[0])\n\tlabels := parseStrings(lines[1])\n\tquery := parseFloats(lines[2])\n\tk, _ := strconv.Atoi(strings.TrimSpace(lines[3]))",
        "go_call": "predictKnn(points, labels, query, k)",
        "go_formatter": "result",
    },
    "kmeans-one-iteration": {
        "names": ["assign_clusters", "assignClusters"],
        "reader": "points = json.loads(lines[0])\ncentroids = json.loads(lines[1])",
        "call": "func(points, centroids)",
        "formatter": "json.dumps(result, separators=(',', ':'))",
        "js_reader": "const points = JSON.parse(lines[0]);\nconst centroids = JSON.parse(lines[1]);",
        "js_call": "fn(points, centroids)",
        "js_formatter": "JSON.stringify(result)",
        "cpp_reader": "auto points = parseDoubleMatrix(lines[0]);\n    auto centroids = parseDoubleMatrix(lines[1]);",
        "cpp_call": "assign_clusters(points, centroids)",
        "cpp_formatter": "formatIntVector(result)",
        "java_reader": "double[][] points = parseDoubleMatrix(lines.get(0));\n        double[][] centroids = parseDoubleMatrix(lines.get(1));",
        "java_call": "solver.assignClusters(points, centroids)",
        "java_formatter": "formatIntArray(result)",
        "go_reader": "points := parseFloatMatrix(lines[0])\n\tcentroids := parseFloatMatrix(lines[1])",
        "go_call": "assignClusters(points, centroids)",
        "go_formatter": "formatInts(result)",
    },
    "scaled-dot-product-attention": {
        "names": ["attention_row", "attentionRow"],
        "reader": "query = json.loads(lines[0])\nkeys = json.loads(lines[1])\nvalues = json.loads(lines[2])",
        "call": "func(query, keys, values)",
        "formatter": "json.dumps([round(float(x), 4) for x in result], separators=(',', ':'))",
        "js_reader": "const query = JSON.parse(lines[0]);\nconst keys = JSON.parse(lines[1]);\nconst values = JSON.parse(lines[2]);",
        "js_call": "fn(query, keys, values)",
        "js_formatter": "JSON.stringify(result.map((x) => Number(Number(x).toFixed(4))))",
        "cpp_reader": "auto query = parseDoubleVector(lines[0]);\n    auto keys = parseDoubleMatrix(lines[1]);\n    auto values = parseDoubleMatrix(lines[2]);",
        "cpp_call": "attention_row(query, keys, values)",
        "cpp_formatter": "formatDoubleVector(result)",
        "java_reader": "double[] query = parseDoubleArray(lines.get(0));\n        double[][] keys = parseDoubleMatrix(lines.get(1));\n        double[][] values = parseDoubleMatrix(lines.get(2));",
        "java_call": "solver.attentionRow(query, keys, values)",
        "java_formatter": "formatDoubleArray(result)",
        "go_reader": "query := parseFloats(lines[0])\n\tkeys := parseFloatMatrix(lines[1])\n\tvalues := parseFloatMatrix(lines[2])",
        "go_call": "attentionRow(query, keys, values)",
        "go_formatter": "formatFloats(result)",
    },
    "softmax-cross-entropy": {
        "names": ["cross_entropy_loss", "crossEntropyLoss"],
        "reader": "logits = json.loads(lines[0])\ntarget = int(lines[1])",
        "call": "func(logits, target)",
        "formatter": "format(float(result), '.4f')",
        "js_reader": "const logits = JSON.parse(lines[0]);\nconst target = Number(lines[1]);",
        "js_call": "fn(logits, target)",
        "js_formatter": "Number(result).toFixed(4)",
        "cpp_reader": "auto logits = parseDoubleVector(lines[0]);\n    int target = stoi(lines[1]);",
        "cpp_call": "cross_entropy_loss(logits, target)",
        "cpp_formatter": "formatDouble(result)",
        "java_reader": "double[] logits = parseDoubleArray(lines.get(0));\n        int target = Integer.parseInt(lines.get(1).trim());",
        "java_call": "solver.crossEntropyLoss(logits, target)",
        "java_formatter": "String.format(Locale.US, \"%.4f\", result)",
        "go_reader": "logits := parseFloats(lines[0])\n\ttarget, _ := strconv.Atoi(strings.TrimSpace(lines[1]))",
        "go_call": "crossEntropyLoss(logits, target)",
        "go_formatter": "fmt.Sprintf(\"%.4f\", result)",
    },
    "attention-mask-apply": {
        "names": ["masked_softmax", "maskedSoftmax"],
        "reader": "scores = json.loads(lines[0])\nmask = json.loads(lines[1])",
        "call": "func(scores, mask)",
        "formatter": "json.dumps([format(float(x), '.4f') for x in result], separators=(',', ':')).replace('\"', '')",
        "js_reader": "const scores = JSON.parse(lines[0]);\nconst mask = JSON.parse(lines[1]);",
        "js_call": "fn(scores, mask)",
        "js_formatter": "`[${result.map((x) => Number(x).toFixed(4)).join(',')}]`",
        "cpp_reader": "auto scores = parseDoubleVector(lines[0]);\n    auto mask = parseIntVector(lines[1]);",
        "cpp_call": "masked_softmax(scores, mask)",
        "cpp_formatter": "formatDoubleVectorFixed(result)",
        "java_reader": "double[] scores = parseDoubleArray(lines.get(0));\n        int[] mask = parseIntArray(lines.get(1));",
        "java_call": "solver.maskedSoftmax(scores, mask)",
        "java_formatter": "formatDoubleArrayFixed(result)",
        "go_reader": "scores := parseFloats(lines[0])\n\tmask := parseInts(lines[1])",
        "go_call": "maskedSoftmax(scores, mask)",
        "go_formatter": "formatFloatsFixed(result)",
    },
}

FUNCTION_ENTRYPOINTS["longest-substring-without-repeating-characters"] = FUNCTION_ENTRYPOINTS[
    "longest-substring-without-repeating"
]


@dataclass(frozen=True)
class SignatureParam:
    name: str
    annotation: str


@dataclass(frozen=True)
class ParsedSignature:
    function_name: str
    params: list[SignatureParam]
    return_type: str


@dataclass(frozen=True)
class NodeFunctionProfile:
    function_name: str
    kind: str


NODE_FUNCTION_PROFILES: dict[str, NodeFunctionProfile] = {
    "add-two-numbers": NodeFunctionProfile("addTwoNumbers", "two_lists_to_list"),
    "intersection-of-two-linked-lists": NodeFunctionProfile("getIntersectionNode", "intersection_node_value"),
    "reverse-linked-list": NodeFunctionProfile("reverseList", "list_to_list"),
    "palindrome-linked-list": NodeFunctionProfile("isPalindrome", "list_to_bool"),
    "linked-list-cycle": NodeFunctionProfile("hasCycle", "cycle_to_bool"),
    "linked-list-cycle-ii": NodeFunctionProfile("detectCycle", "cycle_to_index"),
    "merge-two-sorted-lists": NodeFunctionProfile("mergeTwoLists", "two_lists_to_list"),
    "remove-nth-node-from-end-of-list": NodeFunctionProfile("removeNthFromEnd", "list_int_to_list"),
    "swap-nodes-in-pairs": NodeFunctionProfile("swapPairs", "list_to_list"),
    "reverse-nodes-in-k-group": NodeFunctionProfile("reverseKGroup", "list_int_to_list"),
    "copy-list-with-random-pointer": NodeFunctionProfile("copyRandomList", "random_to_random"),
    "sort-list": NodeFunctionProfile("sortList", "list_to_list"),
    "merge-k-sorted-lists": NodeFunctionProfile("mergeKLists", "list_array_to_list"),
    "binary-tree-inorder-traversal": NodeFunctionProfile("inorderTraversal", "tree_to_vector"),
    "maximum-depth-of-binary-tree": NodeFunctionProfile("maxDepth", "tree_to_scalar"),
    "invert-binary-tree": NodeFunctionProfile("invertTree", "tree_to_tree"),
    "symmetric-tree": NodeFunctionProfile("isSymmetric", "tree_to_scalar"),
    "diameter-of-binary-tree": NodeFunctionProfile("diameterOfBinaryTree", "tree_to_scalar"),
    "binary-tree-level-order-traversal": NodeFunctionProfile("levelOrder", "tree_to_matrix"),
    "convert-sorted-array-to-binary-search-tree": NodeFunctionProfile("sortedArrayToBST", "array_to_tree"),
    "validate-binary-search-tree": NodeFunctionProfile("isValidBST", "tree_to_scalar"),
    "kth-smallest-element-in-a-bst": NodeFunctionProfile("kthSmallest", "tree_int_to_scalar"),
    "binary-tree-right-side-view": NodeFunctionProfile("rightSideView", "tree_to_vector"),
    "flatten-binary-tree-to-linked-list": NodeFunctionProfile("flatten", "flatten_tree"),
    "construct-binary-tree-from-preorder-and-inorder-traversal": NodeFunctionProfile("buildTree", "two_arrays_to_tree"),
    "path-sum-iii": NodeFunctionProfile("pathSum", "tree_int_to_scalar"),
    "lowest-common-ancestor-of-a-binary-tree": NodeFunctionProfile("lowestCommonAncestor", "tree_lca_to_value"),
    "binary-tree-maximum-path-sum": NodeFunctionProfile("maxPathSum", "tree_to_scalar"),
}


CPP_HELPERS = r"""
#include <bits/stdc++.h>
using namespace std;

vector<double> parseDoubleVector(const string& s) {
    vector<double> values;
    string token;
    for (char ch : s) {
        if (isdigit(ch) || ch == '-' || ch == '+' || ch == '.' || ch == 'e' || ch == 'E') token += ch;
        else if (!token.empty()) { values.push_back(stod(token)); token.clear(); }
    }
    if (!token.empty()) values.push_back(stod(token));
    return values;
}
vector<int> parseIntVector(const string& s) {
    vector<double> raw = parseDoubleVector(s);
    vector<int> values;
    for (double value : raw) values.push_back((int)value);
    return values;
}
vector<vector<double>> parseDoubleMatrix(const string& s) {
    vector<vector<double>> rows;
    int depth = 0;
    string current;
    for (char ch : s) {
        if (ch == '[') { depth++; if (depth == 2) current.clear(); }
        else if (ch == ']') {
            if (depth == 2) rows.push_back(parseDoubleVector(current));
            depth--;
        } else if (depth >= 2) current += ch;
    }
    if (rows.empty()) rows.push_back(parseDoubleVector(s));
    return rows;
}
vector<string> parseStringVector(const string& s) {
    vector<string> values;
    string current;
    bool inString = false;
    for (char ch : s) {
        if (ch == '"') {
            if (inString) values.push_back(current);
            current.clear();
            inString = !inString;
        } else if (inString) current += ch;
    }
    return values;
}
string formatDouble(double value) {
    ostringstream out; out << fixed << setprecision(4) << value; return out.str();
}
string formatIntVector(const vector<int>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; out << values[i]; }
    out << "]"; return out.str();
}
string formatDoubleVector(const vector<double>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; out << fixed << setprecision(4) << values[i]; }
    out << "]"; return out.str();
}
string formatDoubleVectorFixed(const vector<double>& values) { return formatDoubleVector(values); }
"""


JS_HELPERS = r"""
const fs = require('fs');
const raw = fs.readFileSync(0, 'utf8').trim();
const lines = raw.length ? raw.split(/\r?\n/) : [''];
"""


GO_HELPERS = r"""
package main

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

func parseFloats(s string) []float64 {
	re := regexp.MustCompile(`[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?`)
	matches := re.FindAllString(s, -1)
	values := make([]float64, 0, len(matches))
	for _, item := range matches {
		value, _ := strconv.ParseFloat(item, 64)
		values = append(values, value)
	}
	return values
}
func parseInts(s string) []int {
	raw := parseFloats(s)
	values := make([]int, 0, len(raw))
	for _, item := range raw { values = append(values, int(item)) }
	return values
}
func parseFloatMatrix(s string) [][]float64 {
	rows := [][]float64{}
	depth := 0
	current := strings.Builder{}
	for _, ch := range s {
		if ch == '[' {
			depth++
			if depth == 2 { current.Reset() }
		} else if ch == ']' {
			if depth == 2 { rows = append(rows, parseFloats(current.String())) }
			depth--
		} else if depth >= 2 {
			current.WriteRune(ch)
		}
	}
	if len(rows) == 0 { rows = append(rows, parseFloats(s)) }
	return rows
}
func parseStrings(s string) []string {
	values := []string{}
	inString := false
	current := strings.Builder{}
	for _, ch := range s {
		if ch == '"' {
			if inString { values = append(values, current.String()) }
			current.Reset()
			inString = !inString
		} else if inString {
			current.WriteRune(ch)
		}
	}
	return values
}
func formatInts(values []int) string {
	parts := make([]string, len(values))
	for i, item := range values { parts[i] = strconv.Itoa(item) }
	return "[" + strings.Join(parts, ",") + "]"
}
func formatFloats(values []float64) string {
	parts := make([]string, len(values))
	for i, item := range values { parts[i] = fmt.Sprintf("%.4f", item) }
	return "[" + strings.Join(parts, ",") + "]"
}
func formatFloatsFixed(values []float64) string { return formatFloats(values) }
"""


JAVA_HELPERS = r"""
    static int[] parseIntArray(String s) {
        double[] raw = parseDoubleArray(s);
        int[] values = new int[raw.length];
        for (int i = 0; i < raw.length; i++) values[i] = (int) raw[i];
        return values;
    }
    static double[] parseDoubleArray(String s) {
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("[-+]?\\d*\\.?\\d+(?:[eE][-+]?\\d+)?").matcher(s);
        ArrayList<Double> list = new ArrayList<>();
        while (m.find()) list.add(Double.parseDouble(m.group()));
        double[] values = new double[list.size()];
        for (int i = 0; i < list.size(); i++) values[i] = list.get(i);
        return values;
    }
    static double[][] parseDoubleMatrix(String s) {
        ArrayList<double[]> rows = new ArrayList<>();
        int depth = 0;
        StringBuilder current = new StringBuilder();
        for (char ch : s.toCharArray()) {
            if (ch == '[') { depth++; if (depth == 2) current.setLength(0); }
            else if (ch == ']') { if (depth == 2) rows.add(parseDoubleArray(current.toString())); depth--; }
            else if (depth >= 2) current.append(ch);
        }
        return rows.toArray(new double[0][]);
    }
    static String[] parseStringArray(String s) {
        ArrayList<String> values = new ArrayList<>();
        boolean inString = false;
        StringBuilder current = new StringBuilder();
        for (char ch : s.toCharArray()) {
            if (ch == '"') { if (inString) values.add(current.toString()); current.setLength(0); inString = !inString; }
            else if (inString) current.append(ch);
        }
        return values.toArray(new String[0]);
    }
    static String formatIntArray(int[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(values[i]); }
        return out.append("]").toString();
    }
    static String formatDoubleArray(double[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(String.format(Locale.US, "%.4f", values[i])); }
        return out.append("]").toString();
    }
    static String formatDoubleArrayFixed(double[] values) { return formatDoubleArray(values); }
"""


C_HELPERS = r"""
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { int *data; int len; } IntVec;
typedef struct { double *data; int len; } DoubleVec;
typedef struct { char **data; int len; } StringVec;
typedef struct { int *data; int *is_null; int len; } NullableIntVec;
typedef struct { double *data; int *is_null; int len; } NullableDoubleVec;
typedef struct { int **data; int rows; int *cols; } IntMatrix;
typedef struct { double **data; int rows; int *cols; } DoubleMatrix;
typedef struct { char ***data; int rows; int *cols; } StringMatrix;
typedef struct { int **data; int **is_null; int rows; int *cols; } NullableIntMatrix;
typedef struct { double **data; int **is_null; int rows; int *cols; } NullableDoubleMatrix;

static char *fastoj_strdup_range(const char *start, int len) {
    char *out = malloc((size_t)len + 1);
    memcpy(out, start, (size_t)len);
    out[len] = '\0';
    return out;
}

char *parse_string_scalar(const char *s) {
    while (*s && isspace((unsigned char)*s)) s++;
    int len = (int)strlen(s);
    while (len > 0 && isspace((unsigned char)s[len - 1])) len--;
    if (len >= 2 && s[0] == '"' && s[len - 1] == '"') {
        char *out = malloc((size_t)len);
        int out_len = 0;
        for (int i = 1; i < len - 1; i++) {
            if (s[i] == '\\' && i + 1 < len - 1) {
                i++;
                out[out_len++] = s[i] == 'n' ? '\n' : s[i];
            } else {
                out[out_len++] = s[i];
            }
        }
        out[out_len] = '\0';
        return out;
    }
    return fastoj_strdup_range(s, len);
}

int parse_bool_scalar(const char *s) {
    while (*s && isspace((unsigned char)*s)) s++;
    if (strncmp(s, "true", 4) == 0 || strncmp(s, "True", 4) == 0) return 1;
    return atoi(s) != 0;
}

DoubleVec parse_double_vec(const char *s) {
    int cap = 16, len = 0;
    double *data = malloc(sizeof(double) * cap);
    const char *p = s;
    while (*p) {
        char *end = NULL;
        double value = strtod(p, &end);
        if (end != p) {
            if (len == cap) { cap *= 2; data = realloc(data, sizeof(double) * cap); }
            data[len++] = value;
            p = end;
        } else {
            p++;
        }
    }
    DoubleVec result = { data, len };
    return result;
}
IntVec parse_int_vec(const char *s) {
    DoubleVec raw = parse_double_vec(s);
    int *data = malloc(sizeof(int) * raw.len);
    for (int i = 0; i < raw.len; i++) data[i] = (int)raw.data[i];
    IntVec result = { data, raw.len };
    return result;
}
NullableIntVec parse_nullable_int_vec(const char *s) {
    int cap = 16, len = 0;
    int *data = malloc(sizeof(int) * cap);
    int *is_null = malloc(sizeof(int) * cap);
    const char *p = s;
    while (*p) {
        if (strncmp(p, "null", 4) == 0 || strncmp(p, "None", 4) == 0) {
            if (len == cap) { cap *= 2; data = realloc(data, sizeof(int) * cap); is_null = realloc(is_null, sizeof(int) * cap); }
            data[len] = 0;
            is_null[len++] = 1;
            p += 4;
            continue;
        }
        char *end = NULL;
        long value = strtol(p, &end, 10);
        if (end != p) {
            if (len == cap) { cap *= 2; data = realloc(data, sizeof(int) * cap); is_null = realloc(is_null, sizeof(int) * cap); }
            data[len] = (int)value;
            is_null[len++] = 0;
            p = end;
        } else {
            p++;
        }
    }
    NullableIntVec result = { data, is_null, len };
    return result;
}
NullableDoubleVec parse_nullable_double_vec(const char *s) {
    int cap = 16, len = 0;
    double *data = malloc(sizeof(double) * cap);
    int *is_null = malloc(sizeof(int) * cap);
    const char *p = s;
    while (*p) {
        if (strncmp(p, "null", 4) == 0 || strncmp(p, "None", 4) == 0) {
            if (len == cap) { cap *= 2; data = realloc(data, sizeof(double) * cap); is_null = realloc(is_null, sizeof(int) * cap); }
            data[len] = 0.0;
            is_null[len++] = 1;
            p += 4;
            continue;
        }
        char *end = NULL;
        double value = strtod(p, &end);
        if (end != p) {
            if (len == cap) { cap *= 2; data = realloc(data, sizeof(double) * cap); is_null = realloc(is_null, sizeof(int) * cap); }
            data[len] = value;
            is_null[len++] = 0;
            p = end;
        } else {
            p++;
        }
    }
    NullableDoubleVec result = { data, is_null, len };
    return result;
}
NullableIntVec parse_nullable_bool_vec(const char *s) {
    int cap = 16, len = 0;
    int *data = malloc(sizeof(int) * cap);
    int *is_null = malloc(sizeof(int) * cap);
    char token[16];
    int token_len = 0;
    for (int i = 0;; i++) {
        char ch = s[i];
        if (isalnum((unsigned char)ch)) {
            if (token_len < 15) token[token_len++] = ch;
            continue;
        }
        if (token_len) {
            token[token_len] = '\0';
            if (len == cap) { cap *= 2; data = realloc(data, sizeof(int) * cap); is_null = realloc(is_null, sizeof(int) * cap); }
            if (strcmp(token, "null") == 0 || strcmp(token, "None") == 0) {
                data[len] = 0;
                is_null[len++] = 1;
            } else {
                data[len] = parse_bool_scalar(token);
                is_null[len++] = 0;
            }
            token_len = 0;
        }
        if (!ch) break;
    }
    NullableIntVec result = { data, is_null, len };
    return result;
}
StringVec parse_string_vec(const char *s) {
    int cap = 16, len = 0, in_string = 0, escaped = 0, start = -1;
    char **data = malloc(sizeof(char*) * cap);
    for (int i = 0; s[i]; i++) {
        char ch = s[i];
        if (escaped) {
            escaped = 0;
        } else if (ch == '\\' && in_string) {
            escaped = 1;
        } else if (ch == '"') {
            if (in_string) {
                if (len == cap) { cap *= 2; data = realloc(data, sizeof(char*) * cap); }
                data[len++] = fastoj_strdup_range(s + start, i - start);
                start = -1;
            } else {
                start = i + 1;
            }
            in_string = !in_string;
        }
    }
    StringVec result = { data, len };
    return result;
}
char **split_rows(const char *s, int *row_count) {
    int cap = 8, len = 0, depth = 0, start = -1;
    char **rows = malloc(sizeof(char*) * cap);
    for (int i = 0; s[i]; i++) {
        if (s[i] == '[') {
            depth++;
            if (depth == 2) start = i + 1;
        } else if (s[i] == ']') {
            if (depth == 2 && start >= 0) {
                if (len == cap) { cap *= 2; rows = realloc(rows, sizeof(char*) * cap); }
                rows[len++] = fastoj_strdup_range(s + start, i - start);
                start = -1;
            }
            if (depth > 0) depth--;
        }
    }
    if (len == 0) {
        rows[len++] = fastoj_strdup_range(s, (int)strlen(s));
    }
    *row_count = len;
    return rows;
}
IntMatrix parse_int_matrix(const char *s) {
    int rows_len = 0;
    char **rows = split_rows(s, &rows_len);
    int **data = malloc(sizeof(int*) * rows_len);
    int *cols = malloc(sizeof(int) * rows_len);
    for (int i = 0; i < rows_len; i++) {
        IntVec row = parse_int_vec(rows[i]);
        data[i] = row.data;
        cols[i] = row.len;
    }
    IntMatrix result = { data, rows_len, cols };
    return result;
}
DoubleMatrix parse_double_matrix(const char *s) {
    int rows_len = 0;
    char **rows = split_rows(s, &rows_len);
    double **data = malloc(sizeof(double*) * rows_len);
    int *cols = malloc(sizeof(int) * rows_len);
    for (int i = 0; i < rows_len; i++) {
        DoubleVec row = parse_double_vec(rows[i]);
        data[i] = row.data;
        cols[i] = row.len;
    }
    DoubleMatrix result = { data, rows_len, cols };
    return result;
}
NullableIntMatrix parse_nullable_int_matrix(const char *s) {
    int rows_len = 0;
    char **rows = split_rows(s, &rows_len);
    int **data = malloc(sizeof(int*) * rows_len);
    int **is_null = malloc(sizeof(int*) * rows_len);
    int *cols = malloc(sizeof(int) * rows_len);
    for (int i = 0; i < rows_len; i++) {
        NullableIntVec row = parse_nullable_int_vec(rows[i]);
        data[i] = row.data;
        is_null[i] = row.is_null;
        cols[i] = row.len;
    }
    NullableIntMatrix result = { data, is_null, rows_len, cols };
    return result;
}
NullableDoubleMatrix parse_nullable_double_matrix(const char *s) {
    int rows_len = 0;
    char **rows = split_rows(s, &rows_len);
    double **data = malloc(sizeof(double*) * rows_len);
    int **is_null = malloc(sizeof(int*) * rows_len);
    int *cols = malloc(sizeof(int) * rows_len);
    for (int i = 0; i < rows_len; i++) {
        NullableDoubleVec row = parse_nullable_double_vec(rows[i]);
        data[i] = row.data;
        is_null[i] = row.is_null;
        cols[i] = row.len;
    }
    NullableDoubleMatrix result = { data, is_null, rows_len, cols };
    return result;
}
NullableIntMatrix parse_nullable_bool_matrix(const char *s) {
    int rows_len = 0;
    char **rows = split_rows(s, &rows_len);
    int **data = malloc(sizeof(int*) * rows_len);
    int **is_null = malloc(sizeof(int*) * rows_len);
    int *cols = malloc(sizeof(int) * rows_len);
    for (int i = 0; i < rows_len; i++) {
        NullableIntVec row = parse_nullable_bool_vec(rows[i]);
        data[i] = row.data;
        is_null[i] = row.is_null;
        cols[i] = row.len;
    }
    NullableIntMatrix result = { data, is_null, rows_len, cols };
    return result;
}
StringMatrix parse_string_matrix(const char *s) {
    int rows_len = 0;
    char **rows = split_rows(s, &rows_len);
    char ***data = malloc(sizeof(char**) * rows_len);
    int *cols = malloc(sizeof(int) * rows_len);
    for (int i = 0; i < rows_len; i++) {
        StringVec row = parse_string_vec(rows[i]);
        data[i] = row.data;
        cols[i] = row.len;
    }
    StringMatrix result = { data, rows_len, cols };
    return result;
}
void print_int_array(int *values, int len) {
    printf("[");
    for (int i = 0; i < len; i++) { if (i) printf(","); printf("%d", values[i]); }
    printf("]\n");
}
void print_double_array(double *values, int len) {
    printf("[");
    for (int i = 0; i < len; i++) { if (i) printf(","); printf("%.4f", values[i]); }
    printf("]\n");
}
void print_nullable_int_array(int *values, int *is_null, int len) {
    printf("[");
    for (int i = 0; i < len; i++) { if (i) printf(","); if (is_null && is_null[i]) printf("null"); else printf("%d", values[i]); }
    printf("]\n");
}
void print_nullable_double_array(double *values, int *is_null, int len) {
    printf("[");
    for (int i = 0; i < len; i++) { if (i) printf(","); if (is_null && is_null[i]) printf("null"); else printf("%.4f", values[i]); }
    printf("]\n");
}
void print_nullable_bool_array(int *values, int *is_null, int len) {
    printf("[");
    for (int i = 0; i < len; i++) { if (i) printf(","); if (is_null && is_null[i]) printf("null"); else printf("%s", values[i] ? "true" : "false"); }
    printf("]\n");
}
void print_string_array(char **values, int len) {
    printf("[");
    for (int i = 0; i < len; i++) { if (i) printf(","); printf("\"%s\"", values[i]); }
    printf("]\n");
}
void print_int_matrix(int **values, int rows, int *cols) {
    printf("[");
    for (int i = 0; i < rows; i++) {
        if (i) printf(",");
        printf("[");
        for (int j = 0; j < cols[i]; j++) { if (j) printf(","); printf("%d", values[i][j]); }
        printf("]");
    }
    printf("]\n");
}
void print_double_matrix(double **values, int rows, int *cols) {
    printf("[");
    for (int i = 0; i < rows; i++) {
        if (i) printf(",");
        printf("[");
        for (int j = 0; j < cols[i]; j++) { if (j) printf(","); printf("%.4f", values[i][j]); }
        printf("]");
    }
    printf("]\n");
}
void print_nullable_int_matrix(int **values, int **is_null, int rows, int *cols) {
    printf("[");
    for (int i = 0; i < rows; i++) {
        if (i) printf(",");
        printf("[");
        for (int j = 0; j < cols[i]; j++) { if (j) printf(","); if (is_null && is_null[i] && is_null[i][j]) printf("null"); else printf("%d", values[i][j]); }
        printf("]");
    }
    printf("]\n");
}
void print_nullable_double_matrix(double **values, int **is_null, int rows, int *cols) {
    printf("[");
    for (int i = 0; i < rows; i++) {
        if (i) printf(",");
        printf("[");
        for (int j = 0; j < cols[i]; j++) { if (j) printf(","); if (is_null && is_null[i] && is_null[i][j]) printf("null"); else printf("%.4f", values[i][j]); }
        printf("]");
    }
    printf("]\n");
}
void print_nullable_bool_matrix(int **values, int **is_null, int rows, int *cols) {
    printf("[");
    for (int i = 0; i < rows; i++) {
        if (i) printf(",");
        printf("[");
        for (int j = 0; j < cols[i]; j++) { if (j) printf(","); if (is_null && is_null[i] && is_null[i][j]) printf("null"); else printf("%s", values[i][j] ? "true" : "false"); }
        printf("]");
    }
    printf("]\n");
}
void print_string_matrix(char ***values, int rows, int *cols) {
    printf("[");
    for (int i = 0; i < rows; i++) {
        if (i) printf(",");
        printf("[");
        for (int j = 0; j < cols[i]; j++) { if (j) printf(","); printf("\"%s\"", values[i][j]); }
        printf("]");
    }
    printf("]\n");
}
"""


def _wrap_python(code: str, spec: dict) -> str:
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


def _wrap_js(code: str, spec: dict) -> str:
    names = ", ".join(
        f"(typeof {name} !== 'undefined' ? {name} : null)" for name in spec["names"]
    )
    return f"""{code.rstrip()}

{JS_HELPERS}
{spec["js_reader"]}
const fn = [{names}].find((candidate) => typeof candidate === 'function');
if (!fn) throw new Error('Expected function: {", ".join(spec["names"])}');
const result = {spec["js_call"]};
console.log({spec["js_formatter"]});
"""


def _strip_cpp_includes(code: str) -> str:
    return "\n".join(line for line in code.splitlines() if not line.lstrip().startswith("#include"))


def _wrap_cpp(code: str, spec: dict) -> str:
    return f"""{CPP_HELPERS}

{_strip_cpp_includes(code).rstrip()}

int main() {{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string raw((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>());
    vector<string> lines;
    string line;
    stringstream ss(raw);
    while (getline(ss, line)) lines.push_back(line);
    {spec["cpp_reader"]}
    auto result = {spec["cpp_call"]};
    cout << {spec["cpp_formatter"]} << "\\n";
    return 0;
}}
"""


def _wrap_go(code: str, spec: dict) -> str:
    body = "\n".join(
        line for line in code.splitlines() if not line.startswith("package ") and not line.startswith("import ")
    )
    return f"""{GO_HELPERS}

{body.rstrip()}

func main() {{
	rawBytes, _ := io.ReadAll(os.Stdin)
	raw := strings.TrimSpace(string(rawBytes))
	lines := strings.Split(raw, "\\n")
	{spec["go_reader"]}
	result := {spec["go_call"]}
	fmt.Println({spec["go_formatter"]})
}}
""".replace(
        'import (\n\t"fmt"',
        'import (\n\t"fmt"\n\t"io"\n\t"os"',
    )


def _wrap_java(code: str, spec: dict) -> str:
    insertion = f"""

{JAVA_HELPERS}
    public static void main(String[] _fastojArgs) throws Exception {{
        Scanner scanner = new Scanner(System.in).useDelimiter("\\\\A");
        String raw = scanner.hasNext() ? scanner.next().trim() : "";
        List<String> lines = raw.isEmpty() ? Arrays.asList("") : Arrays.asList(raw.split("\\\\R"));
        Solution solver = new Solution();
        {spec["java_reader"]}
        var result = {spec["java_call"]};
        System.out.println({spec["java_formatter"]});
    }}
"""
    index = code.rfind("}")
    if index == -1:
        raise ValueError("Java function mode expects a class Solution")
    return "import java.util.*;\n" + code[:index].rstrip() + insertion + "\n}\n"


def _wrap_c(code: str, spec: dict) -> str:
    if "c_reader" not in spec:
        raise ValueError("C function mode is not available for this problem")
    if spec["c_formatter"].startswith("print_int_array"):
        result_block = f"int *result = {spec['c_call']};\n    {spec['c_formatter']};"
    elif "%.4f" in spec["c_formatter"]:
        result_block = f"double result = {spec['c_call']};\n    {spec['c_formatter']};"
    else:
        result_block = f"int result = {spec['c_call']};\n    {spec['c_formatter']};"
    return f"""{C_HELPERS}

{code.rstrip()}

int main(void) {{
    char raw[65536];
    size_t n = fread(raw, 1, sizeof(raw) - 1, stdin);
    raw[n] = '\\0';
    char *lines[8] = {{0}};
    int line_count = 0;
    char *cursor = strtok(raw, "\\r\\n");
    while (cursor && line_count < 8) {{
        lines[line_count++] = cursor;
        cursor = strtok(NULL, "\\r\\n");
    }}
    int result_len = 0;
    {spec["c_reader"]}
    {result_block}
    return 0;
}}
"""


def _function_name_from_signature(function_signature: str) -> str:
    match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", function_signature)
    if not match:
        raise ValueError("Function mode requires a Python def function signature")
    return match.group(1)


def _camel_case(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _preferred_callable_name(code: str, snake_name: str) -> str:
    camel_name = _camel_case(snake_name)
    if camel_name != snake_name and re.search(rf"\b{re.escape(snake_name)}\s*\(", code):
        return snake_name
    return camel_name


def _split_signature_parameters(params: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(params):
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(params[start:index])
            start = index + 1
    parts.append(params[start:])
    return parts


def _parameter_specs_from_signature(function_signature: str) -> list[tuple[str, str]]:
    function_name = _function_name_from_signature(function_signature)
    match = re.search(rf"def\s+{re.escape(function_name)}\s*\((?P<params>.*?)\)", function_signature, re.DOTALL)
    if not match:
        raise ValueError("Function mode requires a parseable Python function signature")
    specs: list[tuple[str, str]] = []
    for item in _split_signature_parameters(match.group("params")):
        cleaned = item.strip()
        if not cleaned or cleaned.startswith("*"):
            continue
        left = cleaned.split("=", 1)[0].strip()
        name, _, annotation = left.partition(":")
        name = name.strip()
        if name and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            specs.append((name, annotation.strip()))
    return specs


def _parse_function_signature(function_signature: str) -> ParsedSignature:
    function_name = _function_name_from_signature(function_signature)
    match = re.search(rf"def\s+{re.escape(function_name)}\s*\((?P<params>.*?)\)\s*(?:->\s*(?P<returns>.*?))?\s*:?\s*$", function_signature, re.DOTALL)
    if not match:
        raise ValueError("Function mode requires a parseable Python function signature")
    params: list[SignatureParam] = []
    for item in _split_signature_parameters(match.group("params")):
        cleaned = item.strip()
        if not cleaned or cleaned.startswith("*"):
            continue
        left = cleaned.split("=", 1)[0].strip()
        name, _, annotation = left.partition(":")
        name = name.strip()
        if name in {"self", "cls"}:
            continue
        if name and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            params.append(SignatureParam(name=name, annotation=annotation.strip() or "Any"))
    return ParsedSignature(function_name=function_name, params=params, return_type=(match.group("returns") or "None").strip())


def _compact_annotation(annotation: str) -> str:
    return re.sub(r"\s+", " ", annotation.strip())


def _split_top_level(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


def _annotation_without_none(annotation: str) -> tuple[str, bool]:
    parts = [part.strip() for part in _split_top_level(_compact_annotation(annotation), "|") if part.strip()]
    concrete = [part for part in parts if part.lower() not in {"none", "null"}]
    return (concrete[0] if concrete else "None", len(concrete) != len(parts))


def _list_inner(annotation: str) -> str | None:
    concrete, _ = _annotation_without_none(_compact_annotation(annotation))
    match = re.match(r"^(?:list|List|Sequence|tuple|Tuple)\[(.*)\]$", concrete)
    return match.group(1).strip() if match else None


def _is_none_type(annotation: str) -> bool:
    return _compact_annotation(annotation).lower() in {"none", "null", "void"}


def _contains_float(annotation: str) -> bool:
    concrete, _ = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        return _contains_float(inner)
    return concrete.lower() == "float"


def _contains_nullable(annotation: str) -> bool:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    return nullable or bool(inner and _contains_nullable(inner))


DYNAMIC_CPP_HELPERS = r"""
#include <bits/stdc++.h>
using namespace std;

string trimCopy(const string& value) {
    size_t start = value.find_first_not_of(" \t\r\n");
    if (start == string::npos) return "";
    size_t end = value.find_last_not_of(" \t\r\n");
    return value.substr(start, end - start + 1);
}

string parseStringScalar(const string& s) {
    string value = trimCopy(s);
    if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
        string out;
        for (size_t i = 1; i + 1 < value.size(); ++i) {
            if (value[i] == '\\' && i + 1 < value.size() - 1) {
                ++i;
                if (value[i] == 'n') out += '\n';
                else out += value[i];
            } else {
                out += value[i];
            }
        }
        return out;
    }
    return value;
}

bool parseBool(const string& s) {
    string value = trimCopy(s);
    transform(value.begin(), value.end(), value.begin(), ::tolower);
    return value == "true" || value == "1";
}

vector<double> parseDoubleVector(const string& s) {
    vector<double> values;
    string token;
    for (char ch : s) {
        if (isdigit(ch) || ch == '-' || ch == '+' || ch == '.' || ch == 'e' || ch == 'E') token += ch;
        else if (!token.empty()) { values.push_back(stod(token)); token.clear(); }
    }
    if (!token.empty()) values.push_back(stod(token));
    return values;
}

vector<int> parseIntVector(const string& s) {
    vector<double> raw = parseDoubleVector(s);
    vector<int> values;
    for (double value : raw) values.push_back((int)value);
    return values;
}

vector<optional<int>> parseOptionalIntVector(const string& s) {
    vector<optional<int>> values;
    string token;
    auto flush = [&]() {
        if (token.empty()) return;
        string value = token;
        transform(value.begin(), value.end(), value.begin(), ::tolower);
        if (value == "null" || value == "none") values.push_back(nullopt);
        else values.push_back(stoi(token));
        token.clear();
    };
    for (char ch : s) {
        if (isalnum((unsigned char)ch) || ch == '-' || ch == '+') token += ch;
        else flush();
    }
    flush();
    return values;
}

vector<optional<double>> parseOptionalDoubleVector(const string& s) {
    vector<optional<double>> values;
    string token;
    auto flush = [&]() {
        if (token.empty()) return;
        string value = token;
        transform(value.begin(), value.end(), value.begin(), ::tolower);
        if (value == "null" || value == "none") values.push_back(nullopt);
        else values.push_back(stod(token));
        token.clear();
    };
    for (char ch : s) {
        if (isalnum((unsigned char)ch) || ch == '-' || ch == '+' || ch == '.' || ch == 'e' || ch == 'E') token += ch;
        else flush();
    }
    flush();
    return values;
}

vector<bool> parseBoolVector(const string& s) {
    vector<bool> values;
    string token;
    auto flush = [&]() {
        if (token.empty()) return;
        values.push_back(parseBool(token));
        token.clear();
    };
    for (char ch : s) {
        if (isalnum((unsigned char)ch)) token += ch;
        else flush();
    }
    flush();
    return values;
}

vector<optional<bool>> parseOptionalBoolVector(const string& s) {
    vector<optional<bool>> values;
    string token;
    auto flush = [&]() {
        if (token.empty()) return;
        string value = token;
        transform(value.begin(), value.end(), value.begin(), ::tolower);
        if (value == "null" || value == "none") values.push_back(nullopt);
        else values.push_back(parseBool(value));
        token.clear();
    };
    for (char ch : s) {
        if (isalnum((unsigned char)ch)) token += ch;
        else flush();
    }
    flush();
    return values;
}

vector<string> parseStringVector(const string& s) {
    vector<string> values;
    string current;
    bool inString = false;
    bool escaped = false;
    for (char ch : s) {
        if (escaped) {
            current += ch == 'n' ? '\n' : ch;
            escaped = false;
        } else if (ch == '\\' && inString) {
            escaped = true;
        } else if (ch == '"') {
            if (inString) values.push_back(current);
            current.clear();
            inString = !inString;
        } else if (inString) {
            current += ch;
        }
    }
    return values;
}

vector<string> splitRows(const string& s) {
    vector<string> rows;
    int depth = 0;
    string current;
    for (char ch : s) {
        if (ch == '[') {
            depth++;
            if (depth == 2) current.clear();
        } else if (ch == ']') {
            if (depth == 2) rows.push_back(current);
            depth--;
        } else if (depth >= 2) {
            current += ch;
        }
    }
    if (rows.empty()) rows.push_back(s);
    return rows;
}

vector<vector<double>> parseDoubleMatrix(const string& s) {
    vector<vector<double>> matrix;
    for (const string& row : splitRows(s)) matrix.push_back(parseDoubleVector(row));
    return matrix;
}

vector<vector<int>> parseIntMatrix(const string& s) {
    vector<vector<int>> matrix;
    for (const string& row : splitRows(s)) matrix.push_back(parseIntVector(row));
    return matrix;
}

vector<vector<optional<int>>> parseOptionalIntMatrix(const string& s) {
    vector<vector<optional<int>>> matrix;
    for (const string& row : splitRows(s)) matrix.push_back(parseOptionalIntVector(row));
    return matrix;
}

vector<vector<optional<double>>> parseOptionalDoubleMatrix(const string& s) {
    vector<vector<optional<double>>> matrix;
    for (const string& row : splitRows(s)) matrix.push_back(parseOptionalDoubleVector(row));
    return matrix;
}

vector<vector<bool>> parseBoolMatrix(const string& s) {
    vector<vector<bool>> matrix;
    for (const string& row : splitRows(s)) matrix.push_back(parseBoolVector(row));
    return matrix;
}

vector<vector<optional<bool>>> parseOptionalBoolMatrix(const string& s) {
    vector<vector<optional<bool>>> matrix;
    for (const string& row : splitRows(s)) matrix.push_back(parseOptionalBoolVector(row));
    return matrix;
}

vector<vector<string>> parseStringMatrix(const string& s) {
    vector<vector<string>> matrix;
    for (const string& row : splitRows(s)) matrix.push_back(parseStringVector(row));
    return matrix;
}

string formatDouble(double value) {
    ostringstream out; out << fixed << setprecision(4) << value; return out.str();
}

string formatStringValue(const string& value) {
    string out = "\"";
    for (char ch : value) {
        if (ch == '"' || ch == '\\') out += '\\';
        out += ch;
    }
    out += "\"";
    return out;
}

string formatIntVector(const vector<int>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; out << values[i]; }
    out << "]"; return out.str();
}

string formatOptionalIntVector(const vector<optional<int>>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; if (values[i]) out << *values[i]; else out << "null"; }
    out << "]"; return out.str();
}

string formatDoubleVector(const vector<double>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; out << fixed << setprecision(4) << values[i]; }
    out << "]"; return out.str();
}

string formatOptionalDoubleVector(const vector<optional<double>>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; if (values[i]) out << formatDouble(*values[i]); else out << "null"; }
    out << "]"; return out.str();
}

string formatBoolVector(const vector<bool>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; out << (values[i] ? "true" : "false"); }
    out << "]"; return out.str();
}

string formatOptionalBoolVector(const vector<optional<bool>>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; if (values[i]) out << (*values[i] ? "true" : "false"); else out << "null"; }
    out << "]"; return out.str();
}

string formatStringVector(const vector<string>& values) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; out << formatStringValue(values[i]); }
    out << "]"; return out.str();
}

template <typename RowFormatter, typename Matrix>
string formatMatrix(const Matrix& values, RowFormatter formatter) {
    ostringstream out; out << "[";
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ","; out << formatter(values[i]); }
    out << "]"; return out.str();
}
"""


DYNAMIC_JAVA_HELPERS = r"""
    static String trim(String value) { return value == null ? "" : value.trim(); }

    static String parseStringScalar(String s) {
        String value = trim(s);
        if (value.length() >= 2 && value.startsWith("\"") && value.endsWith("\"")) {
            return value.substring(1, value.length() - 1).replace("\\\"", "\"").replace("\\\\", "\\");
        }
        return value;
    }

    static int[] parseIntArray(String s) {
        double[] raw = parseDoubleArray(s);
        int[] values = new int[raw.length];
        for (int i = 0; i < raw.length; i++) values[i] = (int) raw[i];
        return values;
    }

    static Integer[] parseIntegerArray(String s) {
        ArrayList<Integer> values = new ArrayList<>();
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("null|None|[-+]?\\d+").matcher(s);
        while (m.find()) {
            String token = m.group();
            values.add(token.equals("null") || token.equals("None") ? null : Integer.parseInt(token));
        }
        return values.toArray(new Integer[0]);
    }

    static Boolean[] parseBooleanObjectArray(String s) {
        ArrayList<Boolean> values = new ArrayList<>();
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("null|None|true|false|True|False|0|1").matcher(s);
        while (m.find()) {
            String token = m.group();
            values.add(token.equals("null") || token.equals("None") ? null : token.equalsIgnoreCase("true") || token.equals("1"));
        }
        return values.toArray(new Boolean[0]);
    }

    static boolean[] parseBooleanArray(String s) {
        Boolean[] raw = parseBooleanObjectArray(s);
        boolean[] values = new boolean[raw.length];
        for (int i = 0; i < raw.length; i++) values[i] = Boolean.TRUE.equals(raw[i]);
        return values;
    }

    static double[] parseDoubleArray(String s) {
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("[-+]?\\d*\\.?\\d+(?:[eE][-+]?\\d+)?").matcher(s);
        ArrayList<Double> list = new ArrayList<>();
        while (m.find()) list.add(Double.parseDouble(m.group()));
        double[] values = new double[list.size()];
        for (int i = 0; i < list.size(); i++) values[i] = list.get(i);
        return values;
    }

    static Double[] parseDoubleObjectArray(String s) {
        ArrayList<Double> values = new ArrayList<>();
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("null|None|[-+]?\\d*\\.?\\d+(?:[eE][-+]?\\d+)?").matcher(s);
        while (m.find()) {
            String token = m.group();
            values.add(token.equals("null") || token.equals("None") ? null : Double.parseDouble(token));
        }
        return values.toArray(new Double[0]);
    }

    static String[] parseStringArray(String s) {
        ArrayList<String> values = new ArrayList<>();
        boolean inString = false;
        boolean escaped = false;
        StringBuilder current = new StringBuilder();
        for (char ch : s.toCharArray()) {
            if (escaped) { current.append(ch == 'n' ? '\n' : ch); escaped = false; }
            else if (ch == '\\' && inString) escaped = true;
            else if (ch == '"') { if (inString) values.add(current.toString()); current.setLength(0); inString = !inString; }
            else if (inString) current.append(ch);
        }
        return values.toArray(new String[0]);
    }

    static ArrayList<String> splitRows(String s) {
        ArrayList<String> rows = new ArrayList<>();
        int depth = 0;
        StringBuilder current = new StringBuilder();
        for (char ch : s.toCharArray()) {
            if (ch == '[') { depth++; if (depth == 2) current.setLength(0); }
            else if (ch == ']') { if (depth == 2) rows.add(current.toString()); depth--; }
            else if (depth >= 2) current.append(ch);
        }
        if (rows.isEmpty()) rows.add(s);
        return rows;
    }

    static int[][] parseIntMatrix(String s) {
        ArrayList<int[]> rows = new ArrayList<>();
        for (String row : splitRows(s)) rows.add(parseIntArray(row));
        return rows.toArray(new int[0][]);
    }

    static Integer[][] parseIntegerMatrix(String s) {
        ArrayList<Integer[]> rows = new ArrayList<>();
        for (String row : splitRows(s)) rows.add(parseIntegerArray(row));
        return rows.toArray(new Integer[0][]);
    }

    static Boolean[][] parseBooleanObjectMatrix(String s) {
        ArrayList<Boolean[]> rows = new ArrayList<>();
        for (String row : splitRows(s)) rows.add(parseBooleanObjectArray(row));
        return rows.toArray(new Boolean[0][]);
    }

    static boolean[][] parseBooleanMatrix(String s) {
        ArrayList<boolean[]> rows = new ArrayList<>();
        for (String row : splitRows(s)) rows.add(parseBooleanArray(row));
        return rows.toArray(new boolean[0][]);
    }

    static double[][] parseDoubleMatrix(String s) {
        ArrayList<double[]> rows = new ArrayList<>();
        for (String row : splitRows(s)) rows.add(parseDoubleArray(row));
        return rows.toArray(new double[0][]);
    }

    static Double[][] parseDoubleObjectMatrix(String s) {
        ArrayList<Double[]> rows = new ArrayList<>();
        for (String row : splitRows(s)) rows.add(parseDoubleObjectArray(row));
        return rows.toArray(new Double[0][]);
    }

    static String[][] parseStringMatrix(String s) {
        ArrayList<String[]> rows = new ArrayList<>();
        for (String row : splitRows(s)) rows.add(parseStringArray(row));
        return rows.toArray(new String[0][]);
    }

    static String quote(String value) { return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""; }

    static String formatDouble(double value) { return String.format(Locale.US, "%.4f", value); }
    static String formatIntArray(int[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(values[i]); }
        return out.append("]").toString();
    }
    static String formatIntegerArray(Integer[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(values[i] == null ? "null" : values[i]); }
        return out.append("]").toString();
    }
    static String formatBooleanArray(boolean[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(values[i] ? "true" : "false"); }
        return out.append("]").toString();
    }
    static String formatBooleanObjectArray(Boolean[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(values[i] == null ? "null" : values[i]); }
        return out.append("]").toString();
    }
    static String formatDoubleArray(double[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatDouble(values[i])); }
        return out.append("]").toString();
    }
    static String formatDoubleObjectArray(Double[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(values[i] == null ? "null" : formatDouble(values[i])); }
        return out.append("]").toString();
    }
    static String formatStringArray(String[] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(quote(values[i])); }
        return out.append("]").toString();
    }
    static String formatIntMatrix(int[][] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatIntArray(values[i])); }
        return out.append("]").toString();
    }
    static String formatIntegerMatrix(Integer[][] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatIntegerArray(values[i])); }
        return out.append("]").toString();
    }
    static String formatBooleanMatrix(boolean[][] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatBooleanArray(values[i])); }
        return out.append("]").toString();
    }
    static String formatBooleanObjectMatrix(Boolean[][] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatBooleanObjectArray(values[i])); }
        return out.append("]").toString();
    }
    static String formatDoubleMatrix(double[][] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatDoubleArray(values[i])); }
        return out.append("]").toString();
    }
    static String formatDoubleObjectMatrix(Double[][] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatDoubleObjectArray(values[i])); }
        return out.append("]").toString();
    }
    static String formatStringMatrix(String[][] values) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < values.length; i++) { if (i > 0) out.append(","); out.append(formatStringArray(values[i])); }
        return out.append("]").toString();
    }
"""


DYNAMIC_GO_HELPERS = r"""
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"strings"
)

func fastojArg(raw string, lines []string, index int, total int) string {
	if total == 1 {
		return raw
	}
	if index < len(lines) {
		return strings.TrimSpace(lines[index])
	}
	return ""
}

func fastojString(raw string) string {
	value := strings.TrimSpace(raw)
	if strings.HasPrefix(value, "\"") {
		var parsed string
		if json.Unmarshal([]byte(value), &parsed) == nil {
			return parsed
		}
	}
	return raw
}

func fastojJSON(value interface{}) string {
	data, _ := json.Marshal(value)
	return string(data)
}

func fastojFloat(value float64) string {
	return fmt.Sprintf("%.4f", value)
}

func fastojRound(value float64) float64 {
	return math.Round(value*10000) / 10000
}

func fastojFloatSlice(values []float64) string {
	parts := make([]string, len(values))
	for i, value := range values {
		parts[i] = fastojFloat(value)
	}
	return "[" + strings.Join(parts, ",") + "]"
}

func fastojFloatMatrix(values [][]float64) string {
	parts := make([]string, len(values))
	for i, value := range values {
		parts[i] = fastojFloatSlice(value)
	}
	return "[" + strings.Join(parts, ",") + "]"
}
"""


def _wrap_dynamic_python(code: str, function_signature: str) -> str:
    function_name = _function_name_from_signature(function_signature)
    parameter_specs = repr(_parameter_specs_from_signature(function_signature))
    return_annotation = repr(_parse_function_signature(function_signature).return_type)
    return f"""{code.rstrip()}

if __name__ == "__main__":
    import json
    import sys

    def _fastoj_load_value(raw_value, annotation):
        if annotation == "str":
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, str):
                    return parsed
            except json.JSONDecodeError:
                pass
            return raw_value
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value

    def _fastoj_load_args(raw, parameter_specs):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        names = [name for name, _ in parameter_specs if name not in ("self", "cls")]
        annotations = [annotation for name, annotation in parameter_specs if name not in ("self", "cls")]
        if not lines and not (len(names) == 1 and annotations and annotations[0] == "str"):
            return []
        if len(lines) > 1:
            args = [
                _fastoj_load_value(line, annotations[index] if index < len(annotations) else "")
                for index, line in enumerate(lines)
            ]
            if names and len(args) != len(names):
                raise ValueError("Function-mode testcase input argument count does not match function_signature.")
            return args
        if not lines and len(names) == 1:
            return [raw]
        value = _fastoj_load_value(lines[0], annotations[0] if annotations else "")
        if isinstance(value, dict) and names:
            if all(name in value for name in names):
                return [value[name] for name in names]
            args_value = value.get("args")
            if isinstance(args_value, list):
                if len(args_value) != len(names):
                    raise ValueError("Function-mode testcase input argument count does not match function_signature.")
                return args_value
            return [value]
        if isinstance(value, list) and len(names) > 1 and len(value) == len(names):
            return value
        args = value if isinstance(value, list) and not names else [value]
        if names and len(args) != len(names):
            raise ValueError("Function-mode testcase input argument count does not match function_signature.")
        return args

    def _fastoj_annotation_without_none(annotation):
        annotation = annotation.strip()
        parts = []
        start = 0
        depth = 0
        for index, char in enumerate(annotation):
            if char in "([{{":
                depth += 1
            elif char in ")]}}" and depth:
                depth -= 1
            elif char == "|" and depth == 0:
                parts.append(annotation[start:index].strip())
                start = index + 1
        parts.append(annotation[start:].strip())
        concrete = [part for part in parts if part.lower() not in ("none", "null")]
        return concrete[0] if concrete else "None"

    def _fastoj_list_inner(annotation):
        annotation = _fastoj_annotation_without_none(annotation.strip())
        for prefix in ("list[", "List[", "Sequence[", "tuple[", "Tuple["):
            if annotation.startswith(prefix) and annotation.endswith("]"):
                return annotation[len(prefix):-1].strip()
        return None

    def _fastoj_format_result(value, annotation, nested=False):
        concrete = _fastoj_annotation_without_none(annotation)
        inner = _fastoj_list_inner(concrete)
        if value is None:
            return "null"
        if inner:
            if not isinstance(value, (list, tuple)):
                return json.dumps(value, separators=(",", ":"))
            return "[" + ",".join(_fastoj_format_result(item, inner, True) for item in value) + "]"
        key = concrete.lower()
        if key == "float":
            return format(float(value), ".4f")
        if key == "bool":
            return str(bool(value)).lower()
        if key == "str":
            return json.dumps(str(value), separators=(",", ":")) if nested else str(value)
        if key in ("none", "null", "void"):
            return "null"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (list, tuple, dict)):
            return json.dumps(value, separators=(",", ":"))
        return str(value)

    raw = sys.stdin.read().strip()
    args = _fastoj_load_args(raw, {parameter_specs})
    func = globals().get("{function_name}")
    if not callable(func) and "Solution" in globals():
        candidate = getattr(Solution(), "{function_name}", None)
        if callable(candidate):
            func = candidate
    if not callable(func):
        raise NameError("Expected function {function_name}")
    result = func(*args)
    print(_fastoj_format_result(result, {return_annotation}))
"""


def _cpp_type(annotation: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        return f"vector<{_cpp_type(inner)}>"
    key = concrete.lower()
    if key == "int":
        result = "int"
    elif key == "float":
        result = "double"
    elif key == "bool":
        result = "bool"
    elif key == "str":
        result = "string"
    elif _is_none_type(key):
        result = "void"
    else:
        result = "int"
    return f"optional<{result}>" if nullable and result != "void" else result


def _cpp_parser(annotation: str, source: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        nested = _list_inner(inner)
        if nested:
            nested_concrete, nested_nullable = _annotation_without_none(nested)
            if nested_nullable:
                if nested_concrete.lower() == "float":
                    return f"parseOptionalDoubleMatrix({source})"
                if nested_concrete.lower() == "bool":
                    return f"parseOptionalBoolMatrix({source})"
                return f"parseOptionalIntMatrix({source})"
            if nested_concrete.lower() == "float":
                return f"parseDoubleMatrix({source})"
            if nested_concrete.lower() == "str":
                return f"parseStringMatrix({source})"
            if nested_concrete.lower() == "bool":
                return f"parseBoolMatrix({source})"
            return f"parseIntMatrix({source})"
        inner_concrete, inner_nullable = _annotation_without_none(inner)
        if inner_nullable:
            if inner_concrete.lower() == "float":
                return f"parseOptionalDoubleVector({source})"
            if inner_concrete.lower() == "bool":
                return f"parseOptionalBoolVector({source})"
            return f"parseOptionalIntVector({source})"
        if inner_concrete.lower() == "float":
            return f"parseDoubleVector({source})"
        if inner_concrete.lower() == "str":
            return f"parseStringVector({source})"
        if inner_concrete.lower() == "bool":
            return f"parseBoolVector({source})"
        return f"parseIntVector({source})"
    key = concrete.lower()
    if nullable:
        if key == "float":
            return f"(trimCopy({source}) == \"null\" ? optional<double>{{}} : optional<double>{{stod(trimCopy({source}))}})"
        if key == "bool":
            return f"(trimCopy({source}) == \"null\" ? optional<bool>{{}} : optional<bool>{{parseBool({source})}})"
        if key == "str":
            return f"(trimCopy({source}) == \"null\" ? optional<string>{{}} : optional<string>{{parseStringScalar({source})}})"
        return f"(trimCopy({source}) == \"null\" ? optional<int>{{}} : optional<int>{{stoi(trimCopy({source}))}})"
    if key == "float":
        return f"stod(trimCopy({source}))"
    if key == "bool":
        return f"parseBool({source})"
    if key == "str":
        return f"parseStringScalar({source})"
    if key == "int":
        return f"stoi(trimCopy({source}))"
    return f"stoi(trimCopy({source}))"


def _cpp_formatter(annotation: str, value: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        nested = _list_inner(inner)
        if nested:
            nested_concrete, nested_nullable = _annotation_without_none(nested)
            if nested_nullable:
                if nested_concrete.lower() == "float":
                    return f"formatMatrix({value}, formatOptionalDoubleVector)"
                if nested_concrete.lower() == "bool":
                    return f"formatMatrix({value}, formatOptionalBoolVector)"
                return f"formatMatrix({value}, formatOptionalIntVector)"
            if nested_concrete.lower() == "float":
                return f"formatMatrix({value}, formatDoubleVector)"
            if nested_concrete.lower() == "str":
                return f"formatMatrix({value}, formatStringVector)"
            if nested_concrete.lower() == "bool":
                return f"formatMatrix({value}, formatBoolVector)"
            return f"formatMatrix({value}, formatIntVector)"
        inner_concrete, inner_nullable = _annotation_without_none(inner)
        if inner_nullable:
            if inner_concrete.lower() == "float":
                return f"formatOptionalDoubleVector({value})"
            if inner_concrete.lower() == "bool":
                return f"formatOptionalBoolVector({value})"
            return f"formatOptionalIntVector({value})"
        if inner_concrete.lower() == "float":
            return f"formatDoubleVector({value})"
        if inner_concrete.lower() == "str":
            return f"formatStringVector({value})"
        if inner_concrete.lower() == "bool":
            return f"formatBoolVector({value})"
        return f"formatIntVector({value})"
    key = concrete.lower()
    if nullable:
        if key == "float":
            return f"({value} ? formatDouble(*{value}) : string(\"null\"))"
        if key == "bool":
            return f"({value} ? (*{value} ? string(\"true\") : string(\"false\")) : string(\"null\"))"
        if key == "str":
            return f"({value} ? *{value} : string(\"null\"))"
        return f"({value} ? to_string(*{value}) : string(\"null\"))"
    if key == "float":
        return f"formatDouble({value})"
    if key == "bool":
        return f"({value} ? string(\"true\") : string(\"false\"))"
    if key == "str":
        return value
    if _is_none_type(key):
        return "string(\"\")"
    return f"to_string({value})"


def _wrap_dynamic_cpp(code: str, function_signature: str) -> str:
    parsed = _parse_function_signature(function_signature)
    readers = []
    total = len(parsed.params)
    for index, param in enumerate(parsed.params):
        source = "raw" if total == 1 else f"lines[{index}]"
        readers.append(f"    {_cpp_type(param.annotation)} {param.name} = {_cpp_parser(param.annotation, source)};")
    call_args = ", ".join(param.name for param in parsed.params)
    return_type = _cpp_type(parsed.return_type)
    result_block = (
        f"    {parsed.function_name}({call_args});\n"
        if return_type == "void"
        else f"    auto result = {parsed.function_name}({call_args});\n    cout << {_cpp_formatter(parsed.return_type, 'result')} << \"\\n\";\n"
    )
    return f"""{DYNAMIC_CPP_HELPERS}

{_strip_cpp_includes(code).rstrip()}

int main() {{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string raw((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>());
    raw = trimCopy(raw);
    vector<string> lines;
    string line;
    stringstream ss(raw);
    while (getline(ss, line)) if (!trimCopy(line).empty()) lines.push_back(trimCopy(line));
{chr(10).join(readers)}
{result_block}    return 0;
}}
"""


def _js_format_expression(return_type: str, value: str) -> str:
    if _contains_float(return_type):
        return f"fastojFormatFloatish({value}, {str(_list_inner(return_type) is None).lower()})"
    return f"fastojFormat({value})"


def _wrap_dynamic_js(code: str, function_signature: str, *, typescript: bool = False) -> str:
    parsed = _parse_function_signature(function_signature)
    specs = json.dumps([(param.name, param.annotation) for param in parsed.params])
    snake = parsed.function_name
    camel = _camel_case(snake)
    prefix = "// @ts-nocheck\n" if typescript else ""
    return f"""{prefix}{code.rstrip()}

const fs = require('fs');
const raw = fs.readFileSync(0, 'utf8').trim();

function fastojLoadValue(rawValue, annotation) {{
  if (annotation === 'str') {{
    try {{
      const parsed = JSON.parse(rawValue);
      if (typeof parsed === 'string') return parsed;
    }} catch {{}}
    return rawValue;
  }}
  try {{ return JSON.parse(rawValue); }} catch {{ return rawValue; }}
}}

function fastojLoadArgs(rawInput, parameterSpecs) {{
  const lines = rawInput.split(/\\r?\\n/).map((line) => line.trim()).filter(Boolean);
  const names = parameterSpecs.map(([name]) => name);
  const annotations = parameterSpecs.map(([, annotation]) => annotation);
  if (lines.length > 1) return lines.map((line, index) => fastojLoadValue(line, annotations[index] || ''));
  if (!lines.length) return names.length === 1 && annotations[0] === 'str' ? [rawInput] : [];
  const value = fastojLoadValue(lines[0], annotations[0] || '');
  if (value && typeof value === 'object' && !Array.isArray(value) && names.length) {{
    if (names.every((name) => Object.prototype.hasOwnProperty.call(value, name))) return names.map((name) => value[name]);
    if (Array.isArray(value.args)) return value.args;
    return [value];
  }}
  if (Array.isArray(value) && names.length > 1 && value.length === names.length) return value;
  return names.length === 1 ? [value] : [];
}}

function fastojRoundFloatish(value) {{
  if (Array.isArray(value)) return value.map(fastojRoundFloatish);
  if (typeof value === 'number') return Number(value.toFixed(4));
  return value;
}}

function fastojFormat(value) {{
  if (value === undefined || value === null) return 'null';
  if (typeof value === 'boolean') return String(value);
  if (Array.isArray(value) || typeof value === 'object') return JSON.stringify(value);
  return String(value);
}}

function fastojFormatFloatish(value, scalar) {{
  if (value === undefined || value === null) return 'null';
  if (scalar) return Number(value).toFixed(4);
  return JSON.stringify(fastojRoundFloatish(value));
}}

const args = fastojLoadArgs(raw, {specs});
const candidates = [
  typeof {snake} !== 'undefined' ? {snake} : null,
  typeof {camel} !== 'undefined' ? {camel} : null,
];
const fn = candidates.find((candidate) => typeof candidate === 'function');
if (!fn) throw new Error('Expected function: {snake} or {camel}');
const result = fn(...args);
console.log({_js_format_expression(parsed.return_type, 'result')});
"""


def _java_type(annotation: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        return f"{_java_type(inner)}[]"
    key = concrete.lower()
    if key == "int":
        return "Integer" if nullable else "int"
    if key == "float":
        return "Double" if nullable else "double"
    if key == "bool":
        return "Boolean" if nullable else "boolean"
    if key == "str":
        return "String"
    if _is_none_type(key):
        return "void"
    return "Object"


def _java_parser(annotation: str, source: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        nested = _list_inner(inner)
        if nested:
            nested_concrete, nested_nullable = _annotation_without_none(nested)
            if nested_nullable:
                if nested_concrete.lower() == "float":
                    return f"parseDoubleObjectMatrix({source})"
                if nested_concrete.lower() == "bool":
                    return f"parseBooleanObjectMatrix({source})"
                return f"parseIntegerMatrix({source})"
            if nested_concrete.lower() == "float":
                return f"parseDoubleMatrix({source})"
            if nested_concrete.lower() == "str":
                return f"parseStringMatrix({source})"
            if nested_concrete.lower() == "bool":
                return f"parseBooleanMatrix({source})"
            return f"parseIntMatrix({source})"
        inner_concrete, inner_nullable = _annotation_without_none(inner)
        if inner_nullable:
            if inner_concrete.lower() == "float":
                return f"parseDoubleObjectArray({source})"
            if inner_concrete.lower() == "bool":
                return f"parseBooleanObjectArray({source})"
            return f"parseIntegerArray({source})"
        if inner_concrete.lower() == "float":
            return f"parseDoubleArray({source})"
        if inner_concrete.lower() == "str":
            return f"parseStringArray({source})"
        if inner_concrete.lower() == "bool":
            return f"parseBooleanArray({source})"
        return f"parseIntArray({source})"
    key = concrete.lower()
    if nullable:
        if key == "float":
            return f"(trim({source}).equals(\"null\") ? null : Double.parseDouble(trim({source})))"
        if key == "bool":
            return f"(trim({source}).equals(\"null\") ? null : Boolean.parseBoolean(trim({source})))"
        return f"(trim({source}).equals(\"null\") ? null : Integer.parseInt(trim({source})))"
    if key == "float":
        return f"Double.parseDouble(trim({source}))"
    if key == "bool":
        return f"Boolean.parseBoolean(trim({source}))"
    if key == "str":
        return f"parseStringScalar({source})"
    if key == "int":
        return f"Integer.parseInt(trim({source}))"
    return source


def _java_formatter(annotation: str, value: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        nested = _list_inner(inner)
        if nested:
            nested_concrete, nested_nullable = _annotation_without_none(nested)
            if nested_nullable:
                if nested_concrete.lower() == "float":
                    return f"formatDoubleObjectMatrix({value})"
                if nested_concrete.lower() == "bool":
                    return f"formatBooleanObjectMatrix({value})"
                return f"formatIntegerMatrix({value})"
            if nested_concrete.lower() == "float":
                return f"formatDoubleMatrix({value})"
            if nested_concrete.lower() == "str":
                return f"formatStringMatrix({value})"
            if nested_concrete.lower() == "bool":
                return f"formatBooleanMatrix({value})"
            return f"formatIntMatrix({value})"
        inner_concrete, inner_nullable = _annotation_without_none(inner)
        if inner_nullable:
            if inner_concrete.lower() == "float":
                return f"formatDoubleObjectArray({value})"
            if inner_concrete.lower() == "bool":
                return f"formatBooleanObjectArray({value})"
            return f"formatIntegerArray({value})"
        if inner_concrete.lower() == "float":
            return f"formatDoubleArray({value})"
        if inner_concrete.lower() == "str":
            return f"formatStringArray({value})"
        if inner_concrete.lower() == "bool":
            return f"formatBooleanArray({value})"
        return f"formatIntArray({value})"
    key = concrete.lower()
    if key == "float":
        return f"formatDouble({value})"
    if nullable and key == "int":
        return f"String.valueOf({value})"
    return f"String.valueOf({value})"


def _wrap_dynamic_java(code: str, function_signature: str) -> str:
    parsed = _parse_function_signature(function_signature)
    method_name = _preferred_callable_name(code, parsed.function_name)
    total = len(parsed.params)
    readers = []
    for index, param in enumerate(parsed.params):
        source = "raw" if total == 1 else f"lines.get({index})"
        readers.append(f"        {_java_type(param.annotation)} {param.name} = {_java_parser(param.annotation, source)};")
    call_args = ", ".join(param.name for param in parsed.params)
    return_type = _java_type(parsed.return_type)
    result_block = (
        f"        solver.{method_name}({call_args});\n"
        if return_type == "void"
        else f"        var result = solver.{method_name}({call_args});\n        System.out.println({_java_formatter(parsed.return_type, 'result')});\n"
    )
    insertion = f"""

{DYNAMIC_JAVA_HELPERS}
    public static void main(String[] _fastojArgs) throws Exception {{
        Scanner scanner = new Scanner(System.in).useDelimiter("\\\\A");
        String raw = scanner.hasNext() ? scanner.next().trim() : "";
        List<String> lines = raw.isEmpty() ? Arrays.asList("") : Arrays.asList(raw.split("\\\\R"));
        Solution solver = new Solution();
{chr(10).join(readers)}
{result_block}    }}
"""
    index = code.rfind("}")
    if index == -1:
        raise ValueError("Java function mode expects a class Solution")
    return "import java.util.*;\n" + code[:index].rstrip() + insertion + "\n}\n"


def _go_type(annotation: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        return f"[]{_go_type(inner)}"
    key = concrete.lower()
    if key == "int":
        result = "int"
    elif key == "float":
        result = "float64"
    elif key == "bool":
        result = "bool"
    elif key == "str":
        result = "string"
    elif _is_none_type(key):
        result = ""
    else:
        result = "interface{}"
    return f"*{result}" if nullable and result and not result.startswith("[]") else result


def _strip_go_package_and_imports(code: str) -> str:
    lines = code.splitlines()
    body: list[str] = []
    skipping_import_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("package "):
            continue
        if skipping_import_block:
            if stripped == ")":
                skipping_import_block = False
            continue
        if stripped.startswith("import ("):
            skipping_import_block = True
            continue
        if stripped.startswith("import "):
            continue
        body.append(line)
    return "\n".join(body).strip()


def _go_reader(param: SignatureParam, index: int, total: int) -> str:
    source = f"fastojArg(raw, lines, {index}, {total})"
    go_type = _go_type(param.annotation)
    if go_type == "string":
        return f"\t{param.name} := fastojString({source})"
    return f"\tvar {param.name} {go_type}\n\t_ = json.Unmarshal([]byte({source}), &{param.name})"


def _go_formatter(annotation: str, value: str) -> str:
    concrete, nullable = _annotation_without_none(annotation)
    inner = _list_inner(concrete)
    if inner:
        nested = _list_inner(inner)
        if _contains_nullable(inner):
            return f"fastojJSON({value})"
        if nested and _annotation_without_none(nested)[0].lower() == "float":
            return f"fastojFloatMatrix({value})"
        if not nested and _annotation_without_none(inner)[0].lower() == "float":
            return f"fastojFloatSlice({value})"
        return f"fastojJSON({value})"
    key = concrete.lower()
    if nullable:
        return f"fastojJSON({value})"
    if key == "float":
        return f"fastojFloat({value})"
    if key == "str":
        return value
    return f"fmt.Sprint({value})"


def _wrap_dynamic_go(code: str, function_signature: str) -> str:
    parsed = _parse_function_signature(function_signature)
    function_name = _preferred_callable_name(code, parsed.function_name)
    total = len(parsed.params)
    readers = [_go_reader(param, index, total) for index, param in enumerate(parsed.params)]
    call_args = ", ".join(param.name for param in parsed.params)
    return_type = _go_type(parsed.return_type)
    result_block = (
        f"\t{function_name}({call_args})\n"
        if not return_type
        else f"\tresult := {function_name}({call_args})\n\tfmt.Println({_go_formatter(parsed.return_type, 'result')})\n"
    )
    return f"""{DYNAMIC_GO_HELPERS}

{_strip_go_package_and_imports(code)}

func main() {{
	rawBytes, _ := os.ReadFile("/dev/stdin")
	raw := strings.TrimSpace(string(rawBytes))
	lines := []string{{}}
	if raw != "" {{
		lines = strings.Split(raw, "\\n")
	}}
	_ = lines
{chr(10).join(readers)}
{result_block}}}
"""


def _c_type(annotation: str) -> str:
    concrete, _ = _annotation_without_none(annotation)
    key = concrete.lower()
    if key == "float":
        return "double"
    if key == "str":
        return "char*"
    if key == "bool":
        return "int"
    if _is_none_type(key):
        return "void"
    return "int"


def _c_base_kind(annotation: str) -> str:
    concrete, _ = _annotation_without_none(annotation)
    key = concrete.lower()
    if key == "float":
        return "float"
    if key == "str":
        return "str"
    if key == "bool":
        return "bool"
    if _is_none_type(key):
        return "void"
    return "int"


def _c_list_inner(annotation: str) -> str | None:
    inner = _list_inner(annotation)
    if inner:
        return inner
    concrete, _ = _annotation_without_none(annotation)
    return "int" if concrete.lower() == "list" else None


def _c_vector_struct(base_type: str, nullable: bool = False) -> str:
    if nullable:
        return "NullableDoubleVec" if base_type == "double" else "NullableIntVec"
    if base_type == "double":
        return "DoubleVec"
    if base_type == "char*":
        return "StringVec"
    return "IntVec"


def _c_matrix_struct(base_type: str, nullable: bool = False) -> str:
    if nullable:
        return "NullableDoubleMatrix" if base_type == "double" else "NullableIntMatrix"
    if base_type == "double":
        return "DoubleMatrix"
    if base_type == "char*":
        return "StringMatrix"
    return "IntMatrix"


def _c_vector_parser(base_type: str, base_kind: str = "int", nullable: bool = False) -> str:
    if nullable:
        if base_type == "double":
            return "parse_nullable_double_vec"
        if base_kind == "bool":
            return "parse_nullable_bool_vec"
        return "parse_nullable_int_vec"
    if base_type == "double":
        return "parse_double_vec"
    if base_type == "char*":
        return "parse_string_vec"
    return "parse_int_vec"


def _c_matrix_parser(base_type: str, base_kind: str = "int", nullable: bool = False) -> str:
    if nullable:
        if base_type == "double":
            return "parse_nullable_double_matrix"
        if base_kind == "bool":
            return "parse_nullable_bool_matrix"
        return "parse_nullable_int_matrix"
    if base_type == "double":
        return "parse_double_matrix"
    if base_type == "char*":
        return "parse_string_matrix"
    return "parse_int_matrix"


def _c_array_printer(base_type: str, base_kind: str = "int", nullable: bool = False) -> str:
    if nullable:
        if base_type == "double":
            return "print_nullable_double_array"
        if base_kind == "bool":
            return "print_nullable_bool_array"
        return "print_nullable_int_array"
    if base_type == "double":
        return "print_double_array"
    if base_type == "char*":
        return "print_string_array"
    return "print_int_array"


def _c_matrix_printer(base_type: str, base_kind: str = "int", nullable: bool = False) -> str:
    if nullable:
        if base_type == "double":
            return "print_nullable_double_matrix"
        if base_kind == "bool":
            return "print_nullable_bool_matrix"
        return "print_nullable_int_matrix"
    if base_type == "double":
        return "print_double_matrix"
    if base_type == "char*":
        return "print_string_matrix"
    return "print_int_matrix"


def _c_pointer_type(base_type: str, dimensions: int) -> str:
    return f"{base_type}{'*' * dimensions}"


def _wrap_dynamic_c(code: str, function_signature: str) -> str:
    parsed = _parse_function_signature(function_signature)
    params: list[str] = []
    readers: list[str] = []
    call_args: list[str] = []
    total = len(parsed.params)
    for index, param in enumerate(parsed.params):
        source = "raw" if total == 1 else f"lines[{index}]"
        inner = _c_list_inner(param.annotation)
        nested = _c_list_inner(inner) if inner else None
        if inner and nested:
            c_type = _c_type(nested)
            base_kind = _c_base_kind(nested)
            _, nullable = _annotation_without_none(nested)
            matrix_type = _c_matrix_struct(c_type, nullable)
            parser = _c_matrix_parser(c_type, base_kind, nullable)
            readers.append(f"    {matrix_type} {param.name} = {parser}({source});")
            if nullable:
                params.extend([f"{_c_pointer_type(c_type, 2)} {param.name}", f"int** {param.name}_is_null", f"int {param.name}_rows", f"int* {param.name}_cols"])
                call_args.extend([f"{param.name}.data", f"{param.name}.is_null", f"{param.name}.rows", f"{param.name}.cols"])
            else:
                params.extend([f"{_c_pointer_type(c_type, 2)} {param.name}", f"int {param.name}_rows", f"int* {param.name}_cols"])
                call_args.extend([f"{param.name}.data", f"{param.name}.rows", f"{param.name}.cols"])
        elif inner:
            c_type = _c_type(inner)
            base_kind = _c_base_kind(inner)
            _, nullable = _annotation_without_none(inner)
            vec_type = _c_vector_struct(c_type, nullable)
            parser = _c_vector_parser(c_type, base_kind, nullable)
            readers.append(f"    {vec_type} {param.name} = {parser}({source});")
            if nullable:
                params.extend([f"{_c_pointer_type(c_type, 1)} {param.name}", f"int* {param.name}_is_null", f"int {param.name}_len"])
                call_args.extend([f"{param.name}.data", f"{param.name}.is_null", f"{param.name}.len"])
            else:
                params.extend([f"{_c_pointer_type(c_type, 1)} {param.name}", f"int {param.name}_len"])
                call_args.extend([f"{param.name}.data", f"{param.name}.len"])
        else:
            c_type = _c_type(param.annotation)
            _, nullable = _annotation_without_none(param.annotation)
            params.append(f"{c_type} {param.name}")
            if nullable:
                params.append(f"int {param.name}_is_null")
            if c_type == "double":
                readers.append(f"    double {param.name} = atof({source});")
            elif c_type == "char*":
                readers.append(f"    char* {param.name} = parse_string_scalar({source});")
            elif _annotation_without_none(param.annotation)[0].lower() == "bool":
                readers.append(f"    int {param.name} = parse_bool_scalar({source});")
            else:
                readers.append(f"    int {param.name} = atoi({source});")
            call_args.append(param.name)
            if nullable:
                readers.append(f"    int {param.name}_is_null = strncmp({source}, \"null\", 4) == 0 || strncmp({source}, \"None\", 4) == 0;")
                call_args.append(f"{param.name}_is_null")
    return_inner = _c_list_inner(parsed.return_type)
    return_nested = _c_list_inner(return_inner) if return_inner else None
    if return_inner and return_nested:
        return_type = _c_type(return_nested)
        base_kind = _c_base_kind(return_nested)
        _, nullable = _annotation_without_none(return_nested)
        function_return = _c_pointer_type(return_type, 2)
        call_args.append("&result_len")
        call_args.append("&result_cols")
        if nullable:
            call_args.append("&result_nulls")
        result_setup = (
            "    int result_len = 0;\n"
            "    int *result_cols = NULL;\n"
        )
        if nullable:
            result_setup += "    int **result_nulls = NULL;\n"
        result_block = result_setup + (
            f"    {function_return} result = {parsed.function_name}({', '.join(call_args)});\n"
            f"    {_c_matrix_printer(return_type, base_kind, nullable)}(result, {'result_nulls, ' if nullable else ''}result_len, result_cols);\n"
        )
    elif return_inner:
        return_type = _c_type(return_inner)
        base_kind = _c_base_kind(return_inner)
        _, nullable = _annotation_without_none(return_inner)
        function_return = _c_pointer_type(return_type, 1)
        call_args.append("&result_len")
        if nullable:
            call_args.append("&result_nulls")
        result_setup = "    int result_len = 0;\n"
        if nullable:
            result_setup += "    int *result_nulls = NULL;\n"
        result_block = result_setup + (
            f"    {function_return} result = {parsed.function_name}({', '.join(call_args)});\n"
            f"    {_c_array_printer(return_type, base_kind, nullable)}(result, {'result_nulls, ' if nullable else ''}result_len);\n"
        )
    else:
        return_type = _c_type(parsed.return_type)
        _, nullable = _annotation_without_none(parsed.return_type)
        if nullable:
            call_args.append("&result_is_null")
        if return_type == "void":
            result_block = f"    {parsed.function_name}({', '.join(call_args)});\n"
        elif return_type == "double":
            prefix = "    int result_is_null = 0;\n" if nullable else ""
            printer = "    if (result_is_null) printf(\"null\\n\"); else printf(\"%.4f\\n\", result);\n" if nullable else "    printf(\"%.4f\\n\", result);\n"
            result_block = f"{prefix}    double result = {parsed.function_name}({', '.join(call_args)});\n{printer}"
        elif return_type == "char*":
            prefix = "    int result_is_null = 0;\n" if nullable else ""
            printer = "    if (result_is_null) printf(\"null\\n\"); else printf(\"%s\\n\", result);\n" if nullable else "    printf(\"%s\\n\", result);\n"
            result_block = f"{prefix}    const char* result = {parsed.function_name}({', '.join(call_args)});\n{printer}"
        elif _annotation_without_none(parsed.return_type)[0].lower() == "bool":
            prefix = "    int result_is_null = 0;\n" if nullable else ""
            printer = "    if (result_is_null) printf(\"null\\n\"); else printf(\"%s\\n\", result ? \"true\" : \"false\");\n" if nullable else "    printf(\"%s\\n\", result ? \"true\" : \"false\");\n"
            result_block = f"{prefix}    int result = {parsed.function_name}({', '.join(call_args)});\n{printer}"
        else:
            prefix = "    int result_is_null = 0;\n" if nullable else ""
            printer = "    if (result_is_null) printf(\"null\\n\"); else printf(\"%d\\n\", result);\n" if nullable else "    printf(\"%d\\n\", result);\n"
            result_block = f"{prefix}    int result = {parsed.function_name}({', '.join(call_args)});\n{printer}"
    return f"""{C_HELPERS}

{code.rstrip()}

int main(void) {{
    char raw[65536];
    size_t n = fread(raw, 1, sizeof(raw) - 1, stdin);
    raw[n] = '\\0';
    char *lines[32] = {{0}};
    int line_count = 0;
    char *cursor = strtok(raw, "\\r\\n");
    while (cursor && line_count < 32) {{
        lines[line_count++] = cursor;
        cursor = strtok(NULL, "\\r\\n");
    }}
{chr(10).join(readers)}
{result_block}    return 0;
}}
"""


PYTHON_NODE_HELPERS = r"""
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Node:
    def __init__(self, x=0, next=None, random=None):
        self.val = x
        self.next = next
        self.random = random


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
"""


def _strip_python_future_annotations(code: str) -> str:
    return "\n".join(
        line
        for line in code.splitlines()
        if line.strip() != "from __future__ import annotations"
    ).strip()


def _wrap_node_python(code: str, profile: NodeFunctionProfile) -> str:
    function_name = profile.function_name
    kind = profile.kind
    user_code = _strip_python_future_annotations(code)
    return f"""{PYTHON_NODE_HELPERS}

{user_code}

if __name__ == "__main__":
    import json
    import sys
    from collections import deque

    def _fastoj_json(line):
        return json.loads(line) if line else None

    def _fastoj_lines(raw):
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def _fastoj_build_list(values):
        dummy = ListNode()
        tail = dummy
        nodes = []
        for value in values:
            node = ListNode(value)
            nodes.append(node)
            tail.next = node
            tail = node
        return dummy.next, nodes

    def _fastoj_list_values(head):
        values = []
        seen = set()
        while head is not None and id(head) not in seen:
            seen.add(id(head))
            values.append(head.val)
            head = head.next
        return values

    def _fastoj_build_cycle(values, pos):
        head, nodes = _fastoj_build_list(values)
        if nodes and 0 <= pos < len(nodes):
            nodes[-1].next = nodes[pos]
        return head, nodes

    def _fastoj_node_index(nodes, target):
        for index, node in enumerate(nodes):
            if node is target:
                return index
        return -1

    def _fastoj_build_intersection(left_values, right_values):
        index = 1
        while index <= len(left_values) and index <= len(right_values) and left_values[-index] == right_values[-index]:
            index += 1
        shared_count = index - 1
        if shared_count >= 4:
            shared_count -= 1
        shared_values = left_values[len(left_values) - shared_count:] if shared_count else []
        shared_head, _ = _fastoj_build_list(shared_values)

        def attach(prefix):
            prefix_head, prefix_nodes = _fastoj_build_list(prefix)
            if prefix_nodes:
                prefix_nodes[-1].next = shared_head
                return prefix_head
            return shared_head

        return attach(left_values[: len(left_values) - len(shared_values)]), attach(right_values[: len(right_values) - len(shared_values)])

    def _fastoj_build_random(values):
        nodes = [Node(item[0]) for item in values]
        for index, item in enumerate(values):
            if index + 1 < len(nodes):
                nodes[index].next = nodes[index + 1]
            random_index = item[1] if len(item) > 1 else None
            if random_index is not None:
                nodes[index].random = nodes[random_index]
        return nodes[0] if nodes else None

    def _fastoj_random_values(head):
        nodes = []
        index_by_id = {{}}
        current = head
        while current is not None and id(current) not in index_by_id:
            index_by_id[id(current)] = len(nodes)
            nodes.append(current)
            current = current.next
        return [[node.val, index_by_id.get(id(node.random)) if node.random is not None else None] for node in nodes]

    def _fastoj_build_tree(values):
        if not values or values[0] is None:
            return None
        root = TreeNode(values[0])
        queue = deque([root])
        cursor = 1
        while queue and cursor < len(values):
            node = queue.popleft()
            if cursor < len(values):
                value = values[cursor]
                cursor += 1
                if value is not None:
                    node.left = TreeNode(value)
                    queue.append(node.left)
            if cursor < len(values):
                value = values[cursor]
                cursor += 1
                if value is not None:
                    node.right = TreeNode(value)
                    queue.append(node.right)
        return root

    def _fastoj_tree_values(root):
        if root is None:
            return []
        values = []
        queue = deque([root])
        while queue:
            node = queue.popleft()
            if node is None:
                values.append(None)
                continue
            values.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        while values and values[-1] is None:
            values.pop()
        return values

    def _fastoj_find_tree_node(root, value):
        if root is None:
            return None
        queue = deque([root])
        while queue:
            node = queue.popleft()
            if node.val == value:
                return node
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)
        return None

    def _fastoj_right_chain_values(root):
        values = []
        seen = set()
        while root is not None and id(root) not in seen:
            seen.add(id(root))
            values.append(root.val)
            root = root.right
        return values

    def _fastoj_format(value):
        if isinstance(value, bool):
            return str(value).lower()
        if value is None:
            return "null"
        if isinstance(value, (list, tuple, dict)):
            return json.dumps(value, separators=(",", ":"))
        return str(value)

    raw = sys.stdin.read().strip()
    lines = _fastoj_lines(raw)
    kind = {kind!r}
    func = globals().get({function_name!r})
    if not callable(func) and "Solution" in globals():
        candidate = getattr(Solution(), {function_name!r}, None)
        if callable(candidate):
            func = candidate
    if not callable(func):
        raise NameError("Expected function {function_name}")

    if kind == "list_to_list":
        head, _nodes = _fastoj_build_list(_fastoj_json(lines[0]))
        print(json.dumps(_fastoj_list_values(func(head)), separators=(",", ":")))
    elif kind == "two_lists_to_list":
        left, _ = _fastoj_build_list(_fastoj_json(lines[0]))
        right, _ = _fastoj_build_list(_fastoj_json(lines[1]))
        print(json.dumps(_fastoj_list_values(func(left, right)), separators=(",", ":")))
    elif kind == "list_int_to_list":
        head, _ = _fastoj_build_list(_fastoj_json(lines[0]))
        print(json.dumps(_fastoj_list_values(func(head, int(lines[1]))), separators=(",", ":")))
    elif kind == "list_array_to_list":
        heads = [_fastoj_build_list(values)[0] for values in _fastoj_json(lines[0])]
        print(json.dumps(_fastoj_list_values(func(heads)), separators=(",", ":")))
    elif kind == "list_to_bool":
        head, _ = _fastoj_build_list(_fastoj_json(lines[0]))
        print(str(bool(func(head))).lower())
    elif kind == "cycle_to_bool":
        head, _nodes = _fastoj_build_cycle(_fastoj_json(lines[0]), int(lines[1]))
        print(str(bool(func(head))).lower())
    elif kind == "cycle_to_index":
        head, nodes = _fastoj_build_cycle(_fastoj_json(lines[0]), int(lines[1]))
        print(_fastoj_node_index(nodes, func(head)))
    elif kind == "intersection_node_value":
        head_a, head_b = _fastoj_build_intersection(_fastoj_json(lines[0]), _fastoj_json(lines[1]))
        result = func(head_a, head_b)
        print("null" if result is None else result.val)
    elif kind == "random_to_random":
        head = _fastoj_build_random(_fastoj_json(lines[0]))
        print(json.dumps(_fastoj_random_values(func(head)), separators=(",", ":")))
    elif kind in ("tree_to_vector", "tree_to_matrix"):
        root = _fastoj_build_tree(_fastoj_json(lines[0]))
        print(_fastoj_format(func(root)))
    elif kind == "tree_to_scalar":
        root = _fastoj_build_tree(_fastoj_json(lines[0]))
        print(_fastoj_format(func(root)))
    elif kind == "tree_to_tree":
        root = _fastoj_build_tree(_fastoj_json(lines[0]))
        print(json.dumps(_fastoj_tree_values(func(root)), separators=(",", ":")))
    elif kind == "array_to_tree":
        print(json.dumps(_fastoj_tree_values(func(_fastoj_json(lines[0]))), separators=(",", ":")))
    elif kind == "two_arrays_to_tree":
        print(json.dumps(_fastoj_tree_values(func(_fastoj_json(lines[0]), _fastoj_json(lines[1]))), separators=(",", ":")))
    elif kind == "tree_int_to_scalar":
        root = _fastoj_build_tree(_fastoj_json(lines[0]))
        print(_fastoj_format(func(root, int(lines[1]))))
    elif kind == "flatten_tree":
        root = _fastoj_build_tree(_fastoj_json(lines[0]))
        result = func(root)
        print(json.dumps(_fastoj_right_chain_values(root if result is None else result), separators=(",", ":")))
    elif kind == "tree_lca_to_value":
        root = _fastoj_build_tree(_fastoj_json(lines[0]))
        result = func(root, _fastoj_find_tree_node(root, int(lines[1])), _fastoj_find_tree_node(root, int(lines[2])))
        print("null" if result is None else result.val)
    else:
        raise ValueError(f"Unsupported node function profile: {{kind}}")
"""


NODE_CPP_HELPERS = r"""
struct ListNode {
    int val;
    ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode *next) : val(x), next(next) {}
};

class Node {
public:
    int val;
    Node* next;
    Node* random;
    Node(int _val) : val(_val), next(nullptr), random(nullptr) {}
};

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};

pair<ListNode*, vector<ListNode*>> buildList(const vector<int>& values) {
    ListNode dummy;
    ListNode* tail = &dummy;
    vector<ListNode*> nodes;
    for (int value : values) {
        auto* node = new ListNode(value);
        nodes.push_back(node);
        tail->next = node;
        tail = node;
    }
    return {dummy.next, nodes};
}

vector<int> listValues(ListNode* head) {
    vector<int> values;
    unordered_set<ListNode*> seen;
    while (head && !seen.count(head)) {
        seen.insert(head);
        values.push_back(head->val);
        head = head->next;
    }
    return values;
}

pair<ListNode*, vector<ListNode*>> buildCycleList(const vector<int>& values, int pos) {
    auto built = buildList(values);
    if (!built.second.empty() && pos >= 0 && pos < (int)built.second.size()) built.second.back()->next = built.second[pos];
    return built;
}

int nodeIndex(const vector<ListNode*>& nodes, ListNode* target) {
    for (int i = 0; i < (int)nodes.size(); ++i) if (nodes[i] == target) return i;
    return -1;
}

pair<ListNode*, ListNode*> buildIntersectionLists(const vector<int>& leftValues, const vector<int>& rightValues) {
    int suffix = 0;
    while (suffix < (int)leftValues.size() && suffix < (int)rightValues.size()
        && leftValues[leftValues.size() - suffix - 1] == rightValues[rightValues.size() - suffix - 1]) suffix++;
    if (suffix >= 4) suffix--;
    vector<int> sharedValues(leftValues.end() - suffix, leftValues.end());
    auto shared = buildList(sharedValues).first;
    auto attach = [&](const vector<int>& values) {
        auto built = buildList(values);
        if (!built.second.empty()) {
            built.second.back()->next = shared;
            return built.first;
        }
        return shared;
    };
    return {attach(vector<int>(leftValues.begin(), leftValues.end() - suffix)), attach(vector<int>(rightValues.begin(), rightValues.end() - suffix))};
}

Node* buildRandomList(const vector<vector<optional<int>>>& values) {
    vector<Node*> nodes;
    for (const auto& item : values) nodes.push_back(new Node(item.empty() || !item[0] ? 0 : *item[0]));
    for (int i = 0; i < (int)nodes.size(); ++i) {
        if (i + 1 < (int)nodes.size()) nodes[i]->next = nodes[i + 1];
        if (values[i].size() > 1 && values[i][1]) nodes[i]->random = nodes[*values[i][1]];
    }
    return nodes.empty() ? nullptr : nodes[0];
}

vector<vector<optional<int>>> randomValues(Node* head) {
    vector<Node*> nodes;
    unordered_map<Node*, int> index;
    for (Node* current = head; current && !index.count(current); current = current->next) {
        index[current] = (int)nodes.size();
        nodes.push_back(current);
    }
    vector<vector<optional<int>>> result;
    for (Node* node : nodes) {
        result.push_back({node->val, node->random ? optional<int>(index[node->random]) : nullopt});
    }
    return result;
}

TreeNode* buildTree(const vector<optional<int>>& values) {
    if (values.empty() || !values[0]) return nullptr;
    auto* root = new TreeNode(*values[0]);
    queue<TreeNode*> nodes;
    nodes.push(root);
    size_t cursor = 1;
    while (!nodes.empty() && cursor < values.size()) {
        TreeNode* node = nodes.front();
        nodes.pop();
        if (cursor < values.size() && values[cursor]) {
            node->left = new TreeNode(*values[cursor]);
            nodes.push(node->left);
        }
        cursor++;
        if (cursor < values.size() && values[cursor]) {
            node->right = new TreeNode(*values[cursor]);
            nodes.push(node->right);
        }
        cursor++;
    }
    return root;
}

vector<optional<int>> treeValues(TreeNode* root) {
    if (!root) return {};
    vector<optional<int>> values;
    queue<TreeNode*> nodes;
    nodes.push(root);
    while (!nodes.empty()) {
        TreeNode* node = nodes.front();
        nodes.pop();
        if (!node) {
            values.push_back(nullopt);
            continue;
        }
        values.push_back(node->val);
        nodes.push(node->left);
        nodes.push(node->right);
    }
    while (!values.empty() && !values.back()) values.pop_back();
    return values;
}

TreeNode* findTreeNode(TreeNode* root, int value) {
    if (!root) return nullptr;
    queue<TreeNode*> nodes;
    nodes.push(root);
    while (!nodes.empty()) {
        TreeNode* node = nodes.front();
        nodes.pop();
        if (node->val == value) return node;
        if (node->left) nodes.push(node->left);
        if (node->right) nodes.push(node->right);
    }
    return nullptr;
}

vector<int> rightChainValues(TreeNode* root) {
    vector<int> values;
    unordered_set<TreeNode*> seen;
    while (root && !seen.count(root)) {
        seen.insert(root);
        values.push_back(root->val);
        root = root->right;
    }
    return values;
}
"""


def _wrap_node_cpp(code: str, profile: NodeFunctionProfile) -> str:
    name = profile.function_name
    kind = profile.kind
    kind_literal = json.dumps(kind)
    return f"""{DYNAMIC_CPP_HELPERS}
{NODE_CPP_HELPERS}

{code.rstrip()}

int main() {{
    string raw((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>());
    raw = trimCopy(raw);
    vector<string> lines;
    string line;
    stringstream ss(raw);
    while (getline(ss, line)) if (!trimCopy(line).empty()) lines.push_back(trimCopy(line));
    Solution solver;
    string kind = {kind_literal};
    if (kind == "list_to_list") {{
        auto built = buildList(parseIntVector(lines[0]));
        cout << formatIntVector(listValues(solver.{name}(built.first))) << "\\n";
    }} else if (kind == "two_lists_to_list") {{
        auto left = buildList(parseIntVector(lines[0]));
        auto right = buildList(parseIntVector(lines[1]));
        cout << formatIntVector(listValues(solver.{name}(left.first, right.first))) << "\\n";
    }} else if (kind == "list_int_to_list") {{
        auto built = buildList(parseIntVector(lines[0]));
        cout << formatIntVector(listValues(solver.{name}(built.first, stoi(lines[1])))) << "\\n";
    }} else if (kind == "list_array_to_list") {{
        vector<ListNode*> lists;
        for (const auto& values : parseIntMatrix(lines[0])) lists.push_back(buildList(values).first);
        cout << formatIntVector(listValues(solver.{name}(lists))) << "\\n";
    }} else if (kind == "list_to_bool") {{
        auto built = buildList(parseIntVector(lines[0]));
        cout << (solver.{name}(built.first) ? "true" : "false") << "\\n";
    }} else if (kind == "cycle_to_bool") {{
        auto built = buildCycleList(parseIntVector(lines[0]), stoi(lines[1]));
        cout << (solver.{name}(built.first) ? "true" : "false") << "\\n";
    }} else if (kind == "cycle_to_index") {{
        auto built = buildCycleList(parseIntVector(lines[0]), stoi(lines[1]));
        cout << nodeIndex(built.second, solver.{name}(built.first)) << "\\n";
    }} else if (kind == "intersection_node_value") {{
        auto built = buildIntersectionLists(parseIntVector(lines[0]), parseIntVector(lines[1]));
        auto* result = solver.{name}(built.first, built.second);
        cout << (result ? to_string(result->val) : string("null")) << "\\n";
    }} else if (kind == "random_to_random") {{
        cout << formatMatrix(randomValues(solver.{name}(buildRandomList(parseOptionalIntMatrix(lines[0])))), formatOptionalIntVector) << "\\n";
    }} else if (kind == "tree_to_vector") {{
        cout << formatIntVector(solver.{name}(buildTree(parseOptionalIntVector(lines[0])))) << "\\n";
    }} else if (kind == "tree_to_matrix") {{
        cout << formatMatrix(solver.{name}(buildTree(parseOptionalIntVector(lines[0]))), formatIntVector) << "\\n";
    }} else if (kind == "tree_to_scalar") {{
        auto result = solver.{name}(buildTree(parseOptionalIntVector(lines[0])));
        if constexpr (is_same_v<decltype(result), bool>) cout << (result ? "true" : "false") << "\\n";
        else cout << result << "\\n";
    }} else if (kind == "tree_to_tree") {{
        cout << formatOptionalIntVector(treeValues(solver.{name}(buildTree(parseOptionalIntVector(lines[0]))))) << "\\n";
    }} else if (kind == "array_to_tree") {{
        cout << formatOptionalIntVector(treeValues(solver.{name}(parseIntVector(lines[0])))) << "\\n";
    }} else if (kind == "two_arrays_to_tree") {{
        cout << formatOptionalIntVector(treeValues(solver.{name}(parseIntVector(lines[0]), parseIntVector(lines[1])))) << "\\n";
    }} else if (kind == "tree_int_to_scalar") {{
        cout << solver.{name}(buildTree(parseOptionalIntVector(lines[0])), stoi(lines[1])) << "\\n";
    }} else if (kind == "flatten_tree") {{
        auto* root = buildTree(parseOptionalIntVector(lines[0]));
        solver.{name}(root);
        cout << formatIntVector(rightChainValues(root)) << "\\n";
    }} else if (kind == "tree_lca_to_value") {{
        auto* root = buildTree(parseOptionalIntVector(lines[0]));
        auto* result = solver.{name}(root, findTreeNode(root, stoi(lines[1])), findTreeNode(root, stoi(lines[2])));
        cout << (result ? to_string(result->val) : string("null")) << "\\n";
    }}
    return 0;
}}
"""


NODE_JS_HELPERS = r"""
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

class Node {
  constructor(val = 0, next = null, random = null) {
    this.val = val;
    this.next = next;
    this.random = random;
  }
}

class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function buildList(values) {
  const dummy = new ListNode();
  let tail = dummy;
  const nodes = [];
  for (const value of values) {
    const node = new ListNode(value);
    nodes.push(node);
    tail.next = node;
    tail = node;
  }
  return [dummy.next, nodes];
}

function listValues(head) {
  const values = [];
  const seen = new Set();
  while (head && !seen.has(head)) {
    seen.add(head);
    values.push(head.val);
    head = head.next;
  }
  return values;
}

function buildCycleList(values, pos) {
  const built = buildList(values);
  const nodes = built[1];
  if (nodes.length && pos >= 0 && pos < nodes.length) nodes[nodes.length - 1].next = nodes[pos];
  return built;
}

function nodeIndex(nodes, target) {
  return nodes.findIndex((node) => node === target);
}

function buildIntersectionLists(leftValues, rightValues) {
  let suffix = 0;
  while (
    suffix < leftValues.length &&
    suffix < rightValues.length &&
    leftValues[leftValues.length - suffix - 1] === rightValues[rightValues.length - suffix - 1]
  ) suffix += 1;
  if (suffix >= 4) suffix -= 1;
  const sharedValues = suffix ? leftValues.slice(leftValues.length - suffix) : [];
  const [shared] = buildList(sharedValues);
  const attach = (values) => {
    const [head, nodes] = buildList(values);
    if (nodes.length) {
      nodes[nodes.length - 1].next = shared;
      return head;
    }
    return shared;
  };
  return [attach(leftValues.slice(0, leftValues.length - suffix)), attach(rightValues.slice(0, rightValues.length - suffix))];
}

function buildRandomList(values) {
  const nodes = values.map(([value]) => new Node(value));
  values.forEach((item, index) => {
    if (index + 1 < nodes.length) nodes[index].next = nodes[index + 1];
    if (item[1] !== null && item[1] !== undefined) nodes[index].random = nodes[item[1]];
  });
  return nodes[0] || null;
}

function randomValues(head) {
  const nodes = [];
  const index = new Map();
  for (let current = head; current && !index.has(current); current = current.next) {
    index.set(current, nodes.length);
    nodes.push(current);
  }
  return nodes.map((node) => [node.val, node.random ? index.get(node.random) : null]);
}

function buildTree(values) {
  if (!values.length || values[0] === null || values[0] === undefined) return null;
  const root = new TreeNode(values[0]);
  const queue = [root];
  let cursor = 1;
  while (queue.length && cursor < values.length) {
    const node = queue.shift();
    if (cursor < values.length && values[cursor] !== null && values[cursor] !== undefined) {
      node.left = new TreeNode(values[cursor]);
      queue.push(node.left);
    }
    cursor += 1;
    if (cursor < values.length && values[cursor] !== null && values[cursor] !== undefined) {
      node.right = new TreeNode(values[cursor]);
      queue.push(node.right);
    }
    cursor += 1;
  }
  return root;
}

function treeValues(root) {
  if (!root) return [];
  const values = [];
  const queue = [root];
  while (queue.length) {
    const node = queue.shift();
    if (!node) {
      values.push(null);
      continue;
    }
    values.push(node.val);
    queue.push(node.left);
    queue.push(node.right);
  }
  while (values.length && values[values.length - 1] === null) values.pop();
  return values;
}

function findTreeNode(root, value) {
  const queue = root ? [root] : [];
  while (queue.length) {
    const node = queue.shift();
    if (node.val === value) return node;
    if (node.left) queue.push(node.left);
    if (node.right) queue.push(node.right);
  }
  return null;
}

function rightChainValues(root) {
  const values = [];
  const seen = new Set();
  while (root && !seen.has(root)) {
    seen.add(root);
    values.push(root.val);
    root = root.right;
  }
  return values;
}

function format(value) {
  if (typeof value === 'boolean') return String(value);
  if (value === null || value === undefined) return 'null';
  if (Array.isArray(value) || typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
"""


def _wrap_node_js(code: str, profile: NodeFunctionProfile, *, typescript: bool = False) -> str:
    name = profile.function_name
    kind = profile.kind
    prefix = "// @ts-nocheck\n" if typescript else ""
    return f"""{prefix}{NODE_JS_HELPERS}

{code.rstrip()}

const fs = require('fs');
const raw = fs.readFileSync(0, 'utf8').trim();
const lines = raw.split(/\\r?\\n/).map((line) => line.trim()).filter(Boolean);
const solver = typeof Solution !== 'undefined' ? new Solution() : null;
const fn = solver && typeof solver.{name} === 'function' ? solver.{name}.bind(solver) : globalThis.{name};
if (typeof fn !== 'function') throw new Error('Expected function: {name}');
const kind = {kind!r};

if (kind === 'list_to_list') {{
  const [head] = buildList(JSON.parse(lines[0]));
  console.log(JSON.stringify(listValues(fn(head))));
}} else if (kind === 'two_lists_to_list') {{
  const [left] = buildList(JSON.parse(lines[0]));
  const [right] = buildList(JSON.parse(lines[1]));
  console.log(JSON.stringify(listValues(fn(left, right))));
}} else if (kind === 'list_int_to_list') {{
  const [head] = buildList(JSON.parse(lines[0]));
  console.log(JSON.stringify(listValues(fn(head, Number(lines[1])))));
}} else if (kind === 'list_array_to_list') {{
  const lists = JSON.parse(lines[0]).map((values) => buildList(values)[0]);
  console.log(JSON.stringify(listValues(fn(lists))));
}} else if (kind === 'list_to_bool') {{
  const [head] = buildList(JSON.parse(lines[0]));
  console.log(String(Boolean(fn(head))));
}} else if (kind === 'cycle_to_bool') {{
  const [head] = buildCycleList(JSON.parse(lines[0]), Number(lines[1]));
  console.log(String(Boolean(fn(head))));
}} else if (kind === 'cycle_to_index') {{
  const [head, nodes] = buildCycleList(JSON.parse(lines[0]), Number(lines[1]));
  console.log(String(nodeIndex(nodes, fn(head))));
}} else if (kind === 'intersection_node_value') {{
  const [headA, headB] = buildIntersectionLists(JSON.parse(lines[0]), JSON.parse(lines[1]));
  const result = fn(headA, headB);
  console.log(result ? String(result.val) : 'null');
}} else if (kind === 'random_to_random') {{
  console.log(JSON.stringify(randomValues(fn(buildRandomList(JSON.parse(lines[0]))))));
}} else if (kind === 'tree_to_vector' || kind === 'tree_to_matrix') {{
  console.log(format(fn(buildTree(JSON.parse(lines[0])))));
}} else if (kind === 'tree_to_scalar') {{
  console.log(format(fn(buildTree(JSON.parse(lines[0])))));
}} else if (kind === 'tree_to_tree') {{
  console.log(JSON.stringify(treeValues(fn(buildTree(JSON.parse(lines[0]))))));
}} else if (kind === 'array_to_tree') {{
  console.log(JSON.stringify(treeValues(fn(JSON.parse(lines[0])))));
}} else if (kind === 'two_arrays_to_tree') {{
  console.log(JSON.stringify(treeValues(fn(JSON.parse(lines[0]), JSON.parse(lines[1])))));
}} else if (kind === 'tree_int_to_scalar') {{
  console.log(format(fn(buildTree(JSON.parse(lines[0])), Number(lines[1]))));
}} else if (kind === 'flatten_tree') {{
  const root = buildTree(JSON.parse(lines[0]));
  const result = fn(root);
  console.log(JSON.stringify(rightChainValues(result || root)));
}} else if (kind === 'tree_lca_to_value') {{
  const root = buildTree(JSON.parse(lines[0]));
  const result = fn(root, findTreeNode(root, Number(lines[1])), findTreeNode(root, Number(lines[2])));
  console.log(result ? String(result.val) : 'null');
}}
"""


JAVA_NODE_CLASSES = r"""
class ListNode {
    int val;
    ListNode next;
    ListNode() {}
    ListNode(int val) { this.val = val; }
    ListNode(int val, ListNode next) { this.val = val; this.next = next; }
}

class Node {
    int val;
    Node next;
    Node random;
    Node(int val) { this.val = val; }
}

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;
    TreeNode() {}
    TreeNode(int val) { this.val = val; }
    TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; }
}
"""


JAVA_NODE_HELPERS = r"""
    static class BuiltList {
        ListNode head;
        ArrayList<ListNode> nodes;
        BuiltList(ListNode head, ArrayList<ListNode> nodes) { this.head = head; this.nodes = nodes; }
    }

    static BuiltList buildList(int[] values) {
        ListNode dummy = new ListNode();
        ListNode tail = dummy;
        ArrayList<ListNode> nodes = new ArrayList<>();
        for (int value : values) {
            ListNode node = new ListNode(value);
            nodes.add(node);
            tail.next = node;
            tail = node;
        }
        return new BuiltList(dummy.next, nodes);
    }

    static int[] listValues(ListNode head) {
        ArrayList<Integer> values = new ArrayList<>();
        HashSet<ListNode> seen = new HashSet<>();
        while (head != null && !seen.contains(head)) {
            seen.add(head);
            values.add(head.val);
            head = head.next;
        }
        int[] result = new int[values.size()];
        for (int i = 0; i < values.size(); i++) result[i] = values.get(i);
        return result;
    }

    static BuiltList buildCycleList(int[] values, int pos) {
        BuiltList built = buildList(values);
        if (!built.nodes.isEmpty() && pos >= 0 && pos < built.nodes.size()) built.nodes.get(built.nodes.size() - 1).next = built.nodes.get(pos);
        return built;
    }

    static int nodeIndex(ArrayList<ListNode> nodes, ListNode target) {
        for (int i = 0; i < nodes.size(); i++) if (nodes.get(i) == target) return i;
        return -1;
    }

    static ListNode[] buildIntersectionLists(int[] leftValues, int[] rightValues) {
        int suffix = 0;
        while (suffix < leftValues.length && suffix < rightValues.length
            && leftValues[leftValues.length - suffix - 1] == rightValues[rightValues.length - suffix - 1]) suffix++;
        if (suffix >= 4) suffix--;
        int[] sharedValues = java.util.Arrays.copyOfRange(leftValues, leftValues.length - suffix, leftValues.length);
        ListNode shared = buildList(sharedValues).head;
        return new ListNode[] {
            attachShared(java.util.Arrays.copyOfRange(leftValues, 0, leftValues.length - suffix), shared),
            attachShared(java.util.Arrays.copyOfRange(rightValues, 0, rightValues.length - suffix), shared)
        };
    }

    static ListNode attachShared(int[] values, ListNode shared) {
        BuiltList built = buildList(values);
        if (!built.nodes.isEmpty()) {
            built.nodes.get(built.nodes.size() - 1).next = shared;
            return built.head;
        }
        return shared;
    }

    static Node buildRandomList(Integer[][] values) {
        Node[] nodes = new Node[values.length];
        for (int i = 0; i < values.length; i++) nodes[i] = new Node(values[i][0] == null ? 0 : values[i][0]);
        for (int i = 0; i < values.length; i++) {
            if (i + 1 < values.length) nodes[i].next = nodes[i + 1];
            if (values[i].length > 1 && values[i][1] != null) nodes[i].random = nodes[values[i][1]];
        }
        return nodes.length == 0 ? null : nodes[0];
    }

    static Integer[][] randomValues(Node head) {
        ArrayList<Node> nodes = new ArrayList<>();
        IdentityHashMap<Node, Integer> index = new IdentityHashMap<>();
        for (Node current = head; current != null && !index.containsKey(current); current = current.next) {
            index.put(current, nodes.size());
            nodes.add(current);
        }
        Integer[][] result = new Integer[nodes.size()][2];
        for (int i = 0; i < nodes.size(); i++) {
            Node node = nodes.get(i);
            result[i][0] = node.val;
            result[i][1] = node.random == null ? null : index.get(node.random);
        }
        return result;
    }

    static TreeNode buildTree(Integer[] values) {
        if (values.length == 0 || values[0] == null) return null;
        TreeNode root = new TreeNode(values[0]);
        LinkedList<TreeNode> queue = new LinkedList<>();
        queue.add(root);
        int cursor = 1;
        while (!queue.isEmpty() && cursor < values.length) {
            TreeNode node = queue.remove();
            if (cursor < values.length && values[cursor] != null) {
                node.left = new TreeNode(values[cursor]);
                queue.add(node.left);
            }
            cursor++;
            if (cursor < values.length && values[cursor] != null) {
                node.right = new TreeNode(values[cursor]);
                queue.add(node.right);
            }
            cursor++;
        }
        return root;
    }

    static Integer[] treeValues(TreeNode root) {
        if (root == null) return new Integer[0];
        ArrayList<Integer> values = new ArrayList<>();
        LinkedList<TreeNode> queue = new LinkedList<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.remove();
            if (node == null) {
                values.add(null);
                continue;
            }
            values.add(node.val);
            queue.add(node.left);
            queue.add(node.right);
        }
        while (!values.isEmpty() && values.get(values.size() - 1) == null) values.remove(values.size() - 1);
        return values.toArray(new Integer[0]);
    }

    static TreeNode findTreeNode(TreeNode root, int value) {
        ArrayDeque<TreeNode> queue = new ArrayDeque<>();
        if (root != null) queue.add(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.remove();
            if (node.val == value) return node;
            if (node.left != null) queue.add(node.left);
            if (node.right != null) queue.add(node.right);
        }
        return null;
    }

    static int[] rightChainValues(TreeNode root) {
        ArrayList<Integer> values = new ArrayList<>();
        HashSet<TreeNode> seen = new HashSet<>();
        while (root != null && !seen.contains(root)) {
            seen.add(root);
            values.add(root.val);
            root = root.right;
        }
        int[] result = new int[values.size()];
        for (int i = 0; i < values.size(); i++) result[i] = values.get(i);
        return result;
    }
"""


def _wrap_node_java(code: str, profile: NodeFunctionProfile) -> str:
    name = profile.function_name
    kind = profile.kind
    kind_literal = json.dumps(kind)
    return f"""import java.io.*;
import java.util.*;

{JAVA_NODE_CLASSES}

{code.rstrip()}

class Main {{
{DYNAMIC_JAVA_HELPERS}
{JAVA_NODE_HELPERS}

    public static void main(String[] args) throws Exception {{
        Scanner scanner = new Scanner(System.in).useDelimiter("\\\\A");
        String raw = scanner.hasNext() ? scanner.next().trim() : "";
        ArrayList<String> lines = new ArrayList<>();
        for (String line : raw.split("\\\\R")) if (!trim(line).isEmpty()) lines.add(trim(line));
        Solution solver = new Solution();
        String kind = {kind_literal};
        if (kind.equals("list_to_list")) {{
            BuiltList built = buildList(parseIntArray(lines.get(0)));
            System.out.println(formatIntArray(listValues(solver.{name}(built.head))));
        }} else if (kind.equals("two_lists_to_list")) {{
            BuiltList left = buildList(parseIntArray(lines.get(0)));
            BuiltList right = buildList(parseIntArray(lines.get(1)));
            System.out.println(formatIntArray(listValues(solver.{name}(left.head, right.head))));
        }} else if (kind.equals("list_int_to_list")) {{
            BuiltList built = buildList(parseIntArray(lines.get(0)));
            System.out.println(formatIntArray(listValues(solver.{name}(built.head, Integer.parseInt(lines.get(1)))));
        }} else if (kind.equals("list_array_to_list")) {{
            int[][] rawLists = parseIntMatrix(lines.get(0));
            ListNode[] lists = new ListNode[rawLists.length];
            for (int i = 0; i < rawLists.length; i++) lists[i] = buildList(rawLists[i]).head;
            System.out.println(formatIntArray(listValues(solver.{name}(lists))));
        }} else if (kind.equals("list_to_bool")) {{
            BuiltList built = buildList(parseIntArray(lines.get(0)));
            System.out.println(String.valueOf(solver.{name}(built.head)));
        }} else if (kind.equals("cycle_to_bool")) {{
            BuiltList built = buildCycleList(parseIntArray(lines.get(0)), Integer.parseInt(lines.get(1)));
            System.out.println(String.valueOf(solver.{name}(built.head)));
        }} else if (kind.equals("cycle_to_index")) {{
            BuiltList built = buildCycleList(parseIntArray(lines.get(0)), Integer.parseInt(lines.get(1)));
            System.out.println(nodeIndex(built.nodes, solver.{name}(built.head)));
        }} else if (kind.equals("intersection_node_value")) {{
            ListNode[] heads = buildIntersectionLists(parseIntArray(lines.get(0)), parseIntArray(lines.get(1)));
            ListNode result = solver.{name}(heads[0], heads[1]);
            System.out.println(result == null ? "null" : String.valueOf(result.val));
        }} else if (kind.equals("random_to_random")) {{
            System.out.println(formatIntegerMatrix(randomValues(solver.{name}(buildRandomList(parseIntegerMatrix(lines.get(0)))))));
        }} else if (kind.equals("tree_to_vector")) {{
            System.out.println(formatIntArray(solver.{name}(buildTree(parseIntegerArray(lines.get(0))))));
        }} else if (kind.equals("tree_to_matrix")) {{
            System.out.println(formatIntMatrix(solver.{name}(buildTree(parseIntegerArray(lines.get(0))))));
        }} else if (kind.equals("tree_to_scalar")) {{
            System.out.println(String.valueOf(solver.{name}(buildTree(parseIntegerArray(lines.get(0))))));
        }} else if (kind.equals("tree_to_tree")) {{
            System.out.println(formatIntegerArray(treeValues(solver.{name}(buildTree(parseIntegerArray(lines.get(0)))))));
        }} else if (kind.equals("array_to_tree")) {{
            System.out.println(formatIntegerArray(treeValues(solver.{name}(parseIntArray(lines.get(0))))));
        }} else if (kind.equals("two_arrays_to_tree")) {{
            System.out.println(formatIntegerArray(treeValues(solver.{name}(parseIntArray(lines.get(0)), parseIntArray(lines.get(1))))));
        }} else if (kind.equals("tree_int_to_scalar")) {{
            System.out.println(String.valueOf(solver.{name}(buildTree(parseIntegerArray(lines.get(0))), Integer.parseInt(lines.get(1)))));
        }} else if (kind.equals("flatten_tree")) {{
            TreeNode root = buildTree(parseIntegerArray(lines.get(0)));
            solver.{name}(root);
            System.out.println(formatIntArray(rightChainValues(root)));
        }} else if (kind.equals("tree_lca_to_value")) {{
            TreeNode root = buildTree(parseIntegerArray(lines.get(0)));
            TreeNode result = solver.{name}(root, findTreeNode(root, Integer.parseInt(lines.get(1))), findTreeNode(root, Integer.parseInt(lines.get(2))));
            System.out.println(result == null ? "null" : String.valueOf(result.val));
        }}
    }}
}}
"""


GO_NODE_HELPERS = r"""
type ListNode struct {
	Val  int
	Next *ListNode
}

type Node struct {
	Val    int
	Next   *Node
	Random *Node
}

type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

func buildList(values []int) (*ListNode, []*ListNode) {
	dummy := &ListNode{}
	tail := dummy
	nodes := []*ListNode{}
	for _, value := range values {
		node := &ListNode{Val: value}
		nodes = append(nodes, node)
		tail.Next = node
		tail = node
	}
	return dummy.Next, nodes
}

func listValues(head *ListNode) []int {
	values := []int{}
	seen := map[*ListNode]bool{}
	for head != nil && !seen[head] {
		seen[head] = true
		values = append(values, head.Val)
		head = head.Next
	}
	return values
}

func buildCycleList(values []int, pos int) (*ListNode, []*ListNode) {
	head, nodes := buildList(values)
	if len(nodes) > 0 && pos >= 0 && pos < len(nodes) {
		nodes[len(nodes)-1].Next = nodes[pos]
	}
	return head, nodes
}

func nodeIndex(nodes []*ListNode, target *ListNode) int {
	for index, node := range nodes {
		if node == target {
			return index
		}
	}
	return -1
}

func buildIntersectionLists(leftValues []int, rightValues []int) (*ListNode, *ListNode) {
	suffix := 0
	for suffix < len(leftValues) && suffix < len(rightValues) && leftValues[len(leftValues)-suffix-1] == rightValues[len(rightValues)-suffix-1] {
		suffix++
	}
	if suffix >= 4 {
		suffix--
	}
	shared, _ := buildList(leftValues[len(leftValues)-suffix:])
	attach := func(values []int) *ListNode {
		head, nodes := buildList(values)
		if len(nodes) > 0 {
			nodes[len(nodes)-1].Next = shared
			return head
		}
		return shared
	}
	return attach(leftValues[:len(leftValues)-suffix]), attach(rightValues[:len(rightValues)-suffix])
}

func buildRandomList(values [][]*int) *Node {
	nodes := make([]*Node, len(values))
	for index, item := range values {
		value := 0
		if len(item) > 0 && item[0] != nil {
			value = *item[0]
		}
		nodes[index] = &Node{Val: value}
	}
	for index, item := range values {
		if index+1 < len(nodes) {
			nodes[index].Next = nodes[index+1]
		}
		if len(item) > 1 && item[1] != nil {
			nodes[index].Random = nodes[*item[1]]
		}
	}
	if len(nodes) == 0 {
		return nil
	}
	return nodes[0]
}

func randomValues(head *Node) [][]*int {
	nodes := []*Node{}
	index := map[*Node]int{}
	for current := head; current != nil; current = current.Next {
		if _, exists := index[current]; exists {
			break
		}
		index[current] = len(nodes)
		nodes = append(nodes, current)
	}
	result := make([][]*int, len(nodes))
	for i, node := range nodes {
		value := node.Val
		row := []*int{&value, nil}
		if node.Random != nil {
			randomIndex := index[node.Random]
			row[1] = &randomIndex
		}
		result[i] = row
	}
	return result
}

func buildTree(values []*int) *TreeNode {
	if len(values) == 0 || values[0] == nil {
		return nil
	}
	root := &TreeNode{Val: *values[0]}
	queue := []*TreeNode{root}
	cursor := 1
	for len(queue) > 0 && cursor < len(values) {
		node := queue[0]
		queue = queue[1:]
		if cursor < len(values) && values[cursor] != nil {
			node.Left = &TreeNode{Val: *values[cursor]}
			queue = append(queue, node.Left)
		}
		cursor++
		if cursor < len(values) && values[cursor] != nil {
			node.Right = &TreeNode{Val: *values[cursor]}
			queue = append(queue, node.Right)
		}
		cursor++
	}
	return root
}

func treeValues(root *TreeNode) []*int {
	if root == nil {
		return []*int{}
	}
	values := []*int{}
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		if node == nil {
			values = append(values, nil)
			continue
		}
		value := node.Val
		values = append(values, &value)
		queue = append(queue, node.Left, node.Right)
	}
	for len(values) > 0 && values[len(values)-1] == nil {
		values = values[:len(values)-1]
	}
	return values
}

func findTreeNode(root *TreeNode, value int) *TreeNode {
	queue := []*TreeNode{}
	if root != nil {
		queue = append(queue, root)
	}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		if node.Val == value {
			return node
		}
		if node.Left != nil {
			queue = append(queue, node.Left)
		}
		if node.Right != nil {
			queue = append(queue, node.Right)
		}
	}
	return nil
}

func rightChainValues(root *TreeNode) []int {
	values := []int{}
	seen := map[*TreeNode]bool{}
	for root != nil && !seen[root] {
		seen[root] = true
		values = append(values, root.Val)
		root = root.Right
	}
	return values
}
"""


def _wrap_node_go(code: str, profile: NodeFunctionProfile) -> str:
    name = _preferred_callable_name(code, profile.function_name)
    kind = profile.kind
    kind_literal = json.dumps(kind)
    return f"""{DYNAMIC_GO_HELPERS}

{GO_NODE_HELPERS}

{_strip_go_package_and_imports(code)}

func main() {{
	rawBytes, _ := os.ReadFile("/dev/stdin")
	raw := strings.TrimSpace(string(rawBytes))
	lines := strings.Split(raw, "\\n")
	for i := range lines {{
		lines[i] = strings.TrimSpace(lines[i])
	}}
	kind := {kind_literal}
	if kind == "list_to_list" {{
		var values []int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		head, _ := buildList(values)
		fmt.Println(fastojJSON(listValues({name}(head))))
	}} else if kind == "two_lists_to_list" {{
		var leftValues []int
		var rightValues []int
		_ = json.Unmarshal([]byte(lines[0]), &leftValues)
		_ = json.Unmarshal([]byte(lines[1]), &rightValues)
		left, _ := buildList(leftValues)
		right, _ := buildList(rightValues)
		fmt.Println(fastojJSON(listValues({name}(left, right))))
	}} else if kind == "list_int_to_list" {{
		var values []int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		head, _ := buildList(values)
		n, _ := strconv.Atoi(lines[1])
		fmt.Println(fastojJSON(listValues({name}(head, n))))
	}} else if kind == "list_array_to_list" {{
		var rawLists [][]int
		_ = json.Unmarshal([]byte(lines[0]), &rawLists)
		lists := make([]*ListNode, len(rawLists))
		for i, values := range rawLists {{
			lists[i], _ = buildList(values)
		}}
		fmt.Println(fastojJSON(listValues({name}(lists))))
	}} else if kind == "list_to_bool" {{
		var values []int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		head, _ := buildList(values)
		fmt.Println(strconv.FormatBool({name}(head)))
	}} else if kind == "cycle_to_bool" {{
		var values []int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		pos, _ := strconv.Atoi(lines[1])
		head, _ := buildCycleList(values, pos)
		fmt.Println(strconv.FormatBool({name}(head)))
	}} else if kind == "cycle_to_index" {{
		var values []int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		pos, _ := strconv.Atoi(lines[1])
		head, nodes := buildCycleList(values, pos)
		fmt.Println(nodeIndex(nodes, {name}(head)))
	}} else if kind == "intersection_node_value" {{
		var leftValues []int
		var rightValues []int
		_ = json.Unmarshal([]byte(lines[0]), &leftValues)
		_ = json.Unmarshal([]byte(lines[1]), &rightValues)
		left, right := buildIntersectionLists(leftValues, rightValues)
		result := {name}(left, right)
		if result == nil {{ fmt.Println("null") }} else {{ fmt.Println(result.Val) }}
	}} else if kind == "random_to_random" {{
		var values [][]*int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		fmt.Println(fastojJSON(randomValues({name}(buildRandomList(values)))))
	}} else if kind == "tree_to_vector" || kind == "tree_to_matrix" {{
		var values []*int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		fmt.Println(fastojJSON({name}(buildTree(values))))
	}} else if kind == "tree_to_scalar" {{
		var values []*int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		fmt.Println(fmt.Sprint({name}(buildTree(values))))
	}} else if kind == "tree_to_tree" {{
		var values []*int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		fmt.Println(fastojJSON(treeValues({name}(buildTree(values)))))
	}} else if kind == "array_to_tree" {{
		var values []int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		fmt.Println(fastojJSON(treeValues({name}(values))))
	}} else if kind == "two_arrays_to_tree" {{
		var preorder []int
		var inorder []int
		_ = json.Unmarshal([]byte(lines[0]), &preorder)
		_ = json.Unmarshal([]byte(lines[1]), &inorder)
		fmt.Println(fastojJSON(treeValues({name}(preorder, inorder))))
	}} else if kind == "tree_int_to_scalar" {{
		var values []*int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		number, _ := strconv.Atoi(lines[1])
		fmt.Println(fmt.Sprint({name}(buildTree(values), number)))
	}} else if kind == "flatten_tree" {{
		var values []*int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		root := buildTree(values)
		{name}(root)
		fmt.Println(fastojJSON(rightChainValues(root)))
	}} else if kind == "tree_lca_to_value" {{
		var values []*int
		_ = json.Unmarshal([]byte(lines[0]), &values)
		root := buildTree(values)
		p, _ := strconv.Atoi(lines[1])
		q, _ := strconv.Atoi(lines[2])
		result := {name}(root, findTreeNode(root, p), findTreeNode(root, q))
		if result == nil {{ fmt.Println("null") }} else {{ fmt.Println(result.Val) }}
	}}
}}
"""


C_NODE_HELPERS = r"""
struct ListNode { int val; struct ListNode *next; };
struct Node { int val; struct Node *next; struct Node *random; };
struct TreeNode { int val; struct TreeNode *left; struct TreeNode *right; };

typedef struct { struct ListNode *head; struct ListNode **nodes; int len; } BuiltList;

BuiltList build_list(IntVec values) {
    struct ListNode dummy = {0, NULL};
    struct ListNode *tail = &dummy;
    struct ListNode **nodes = malloc(sizeof(struct ListNode*) * (values.len > 0 ? values.len : 1));
    for (int i = 0; i < values.len; i++) {
        struct ListNode *node = malloc(sizeof(struct ListNode));
        node->val = values.data[i];
        node->next = NULL;
        nodes[i] = node;
        tail->next = node;
        tail = node;
    }
    BuiltList result = { dummy.next, nodes, values.len };
    return result;
}

IntVec list_values(struct ListNode *head) {
    int capacity = 16;
    int len = 0;
    int *data = malloc(sizeof(int) * capacity);
    struct ListNode **seen = malloc(sizeof(struct ListNode*) * capacity);
    while (head) {
        int duplicate = 0;
        for (int i = 0; i < len; i++) if (seen[i] == head) duplicate = 1;
        if (duplicate) break;
        if (len == capacity) {
            capacity *= 2;
            data = realloc(data, sizeof(int) * capacity);
            seen = realloc(seen, sizeof(struct ListNode*) * capacity);
        }
        seen[len] = head;
        data[len++] = head->val;
        head = head->next;
    }
    IntVec result = { data, len };
    return result;
}

BuiltList build_cycle_list(IntVec values, int pos) {
    BuiltList built = build_list(values);
    if (built.len > 0 && pos >= 0 && pos < built.len) built.nodes[built.len - 1]->next = built.nodes[pos];
    return built;
}

int node_index(BuiltList built, struct ListNode *target) {
    for (int i = 0; i < built.len; i++) if (built.nodes[i] == target) return i;
    return -1;
}

struct ListNode *attach_shared(IntVec values, int len, struct ListNode *shared) {
    IntVec prefix = { values.data, len };
    BuiltList built = build_list(prefix);
    if (built.len > 0) {
        built.nodes[built.len - 1]->next = shared;
        return built.head;
    }
    return shared;
}

void build_intersection_lists(IntVec left, IntVec right, struct ListNode **head_a, struct ListNode **head_b) {
    int suffix = 0;
    while (suffix < left.len && suffix < right.len && left.data[left.len - suffix - 1] == right.data[right.len - suffix - 1]) suffix++;
    if (suffix >= 4) suffix--;
    IntVec shared_values = { left.data + left.len - suffix, suffix };
    struct ListNode *shared = build_list(shared_values).head;
    *head_a = attach_shared(left, left.len - suffix, shared);
    *head_b = attach_shared(right, right.len - suffix, shared);
}

struct Node *build_random_list(NullableIntMatrix values) {
    struct Node **nodes = malloc(sizeof(struct Node*) * (values.rows > 0 ? values.rows : 1));
    for (int i = 0; i < values.rows; i++) {
        nodes[i] = malloc(sizeof(struct Node));
        nodes[i]->val = values.is_null[i][0] ? 0 : values.data[i][0];
        nodes[i]->next = NULL;
        nodes[i]->random = NULL;
    }
    for (int i = 0; i < values.rows; i++) {
        if (i + 1 < values.rows) nodes[i]->next = nodes[i + 1];
        if (values.cols[i] > 1 && !values.is_null[i][1]) nodes[i]->random = nodes[values.data[i][1]];
    }
    return values.rows ? nodes[0] : NULL;
}

NullableIntMatrix random_values(struct Node *head) {
    int capacity = 16;
    int rows = 0;
    struct Node **nodes = malloc(sizeof(struct Node*) * capacity);
    for (struct Node *cur = head; cur; cur = cur->next) {
        int duplicate = 0;
        for (int i = 0; i < rows; i++) if (nodes[i] == cur) duplicate = 1;
        if (duplicate) break;
        if (rows == capacity) {
            capacity *= 2;
            nodes = realloc(nodes, sizeof(struct Node*) * capacity);
        }
        nodes[rows++] = cur;
    }
    int **data = malloc(sizeof(int*) * (rows > 0 ? rows : 1));
    int **is_null = malloc(sizeof(int*) * (rows > 0 ? rows : 1));
    int *cols = malloc(sizeof(int) * (rows > 0 ? rows : 1));
    for (int i = 0; i < rows; i++) {
        data[i] = malloc(sizeof(int) * 2);
        is_null[i] = calloc(2, sizeof(int));
        cols[i] = 2;
        data[i][0] = nodes[i]->val;
        is_null[i][0] = 0;
        data[i][1] = 0;
        is_null[i][1] = 1;
        if (nodes[i]->random) {
            for (int j = 0; j < rows; j++) if (nodes[j] == nodes[i]->random) {
                data[i][1] = j;
                is_null[i][1] = 0;
            }
        }
    }
    NullableIntMatrix result = { data, is_null, rows, cols };
    return result;
}

struct TreeNode *build_tree(NullableIntVec values) {
    if (values.len == 0 || values.is_null[0]) return NULL;
    struct TreeNode *root = malloc(sizeof(struct TreeNode));
    root->val = values.data[0];
    root->left = NULL;
    root->right = NULL;
    struct TreeNode **queue = malloc(sizeof(struct TreeNode*) * values.len);
    int head = 0, tail = 0, cursor = 1;
    queue[tail++] = root;
    while (head < tail && cursor < values.len) {
        struct TreeNode *node = queue[head++];
        if (cursor < values.len && !values.is_null[cursor]) {
            node->left = malloc(sizeof(struct TreeNode));
            node->left->val = values.data[cursor];
            node->left->left = NULL;
            node->left->right = NULL;
            queue[tail++] = node->left;
        }
        cursor++;
        if (cursor < values.len && !values.is_null[cursor]) {
            node->right = malloc(sizeof(struct TreeNode));
            node->right->val = values.data[cursor];
            node->right->left = NULL;
            node->right->right = NULL;
            queue[tail++] = node->right;
        }
        cursor++;
    }
    return root;
}

NullableIntVec tree_values(struct TreeNode *root) {
    if (!root) {
        NullableIntVec empty = { NULL, NULL, 0 };
        return empty;
    }
    int capacity = 32;
    int len = 0;
    int *data = malloc(sizeof(int) * capacity);
    int *is_null = malloc(sizeof(int) * capacity);
    struct TreeNode **queue = malloc(sizeof(struct TreeNode*) * capacity);
    int head = 0, tail = 0;
    queue[tail++] = root;
    while (head < tail) {
        struct TreeNode *node = queue[head++];
        if (len == capacity || tail + 2 >= capacity) {
            capacity *= 2;
            data = realloc(data, sizeof(int) * capacity);
            is_null = realloc(is_null, sizeof(int) * capacity);
            queue = realloc(queue, sizeof(struct TreeNode*) * capacity);
        }
        if (!node) {
            data[len] = 0;
            is_null[len++] = 1;
            continue;
        }
        data[len] = node->val;
        is_null[len++] = 0;
        queue[tail++] = node->left;
        queue[tail++] = node->right;
    }
    while (len > 0 && is_null[len - 1]) len--;
    NullableIntVec result = { data, is_null, len };
    return result;
}

struct TreeNode *find_tree_node(struct TreeNode *root, int value) {
    if (!root) return NULL;
    struct TreeNode **queue = malloc(sizeof(struct TreeNode*) * 4096);
    int head = 0, tail = 0;
    queue[tail++] = root;
    while (head < tail) {
        struct TreeNode *node = queue[head++];
        if (node->val == value) return node;
        if (node->left) queue[tail++] = node->left;
        if (node->right) queue[tail++] = node->right;
    }
    return NULL;
}

IntVec right_chain_values(struct TreeNode *root) {
    int capacity = 16;
    int len = 0;
    int *data = malloc(sizeof(int) * capacity);
    struct TreeNode **seen = malloc(sizeof(struct TreeNode*) * capacity);
    while (root) {
        int duplicate = 0;
        for (int i = 0; i < len; i++) if (seen[i] == root) duplicate = 1;
        if (duplicate) break;
        if (len == capacity) {
            capacity *= 2;
            data = realloc(data, sizeof(int) * capacity);
            seen = realloc(seen, sizeof(struct TreeNode*) * capacity);
        }
        seen[len] = root;
        data[len++] = root->val;
        root = root->right;
    }
    IntVec result = { data, len };
    return result;
}
"""


def _wrap_node_c(code: str, profile: NodeFunctionProfile) -> str:
    name = profile.function_name
    kind = profile.kind
    kind_literal = json.dumps(kind)
    return f"""{C_HELPERS}

{C_NODE_HELPERS}

{code.rstrip()}

int main(void) {{
    char raw[65536];
    size_t n = fread(raw, 1, sizeof(raw) - 1, stdin);
    raw[n] = '\\0';
    char *lines[32] = {{0}};
    int line_count = 0;
    char *cursor = strtok(raw, "\\r\\n");
    while (cursor && line_count < 32) {{
        lines[line_count++] = cursor;
        cursor = strtok(NULL, "\\r\\n");
    }}
    const char *kind = {kind_literal};
    if (strcmp(kind, "list_to_list") == 0) {{
        BuiltList built = build_list(parse_int_vec(lines[0]));
        IntVec values = list_values({name}(built.head));
        print_int_array(values.data, values.len);
    }} else if (strcmp(kind, "two_lists_to_list") == 0) {{
        BuiltList left = build_list(parse_int_vec(lines[0]));
        BuiltList right = build_list(parse_int_vec(lines[1]));
        IntVec values = list_values({name}(left.head, right.head));
        print_int_array(values.data, values.len);
    }} else if (strcmp(kind, "list_int_to_list") == 0) {{
        BuiltList built = build_list(parse_int_vec(lines[0]));
        IntVec values = list_values({name}(built.head, atoi(lines[1])));
        print_int_array(values.data, values.len);
    }} else if (strcmp(kind, "list_array_to_list") == 0) {{
        IntMatrix matrix = parse_int_matrix(lines[0]);
        struct ListNode **lists = malloc(sizeof(struct ListNode*) * (matrix.rows > 0 ? matrix.rows : 1));
        for (int i = 0; i < matrix.rows; i++) {{
            IntVec row = {{ matrix.data[i], matrix.cols[i] }};
            lists[i] = build_list(row).head;
        }}
        IntVec values = list_values({name}(lists, matrix.rows));
        print_int_array(values.data, values.len);
    }} else if (strcmp(kind, "list_to_bool") == 0) {{
        BuiltList built = build_list(parse_int_vec(lines[0]));
        printf("%s\\n", {name}(built.head) ? "true" : "false");
    }} else if (strcmp(kind, "cycle_to_bool") == 0) {{
        BuiltList built = build_cycle_list(parse_int_vec(lines[0]), atoi(lines[1]));
        printf("%s\\n", {name}(built.head) ? "true" : "false");
    }} else if (strcmp(kind, "cycle_to_index") == 0) {{
        BuiltList built = build_cycle_list(parse_int_vec(lines[0]), atoi(lines[1]));
        printf("%d\\n", node_index(built, {name}(built.head)));
    }} else if (strcmp(kind, "intersection_node_value") == 0) {{
        struct ListNode *head_a = NULL;
        struct ListNode *head_b = NULL;
        build_intersection_lists(parse_int_vec(lines[0]), parse_int_vec(lines[1]), &head_a, &head_b);
        struct ListNode *result = {name}(head_a, head_b);
        if (result) printf("%d\\n", result->val); else printf("null\\n");
    }} else if (strcmp(kind, "random_to_random") == 0) {{
        NullableIntMatrix values = random_values({name}(build_random_list(parse_nullable_int_matrix(lines[0]))));
        print_nullable_int_matrix(values.data, values.is_null, values.rows, values.cols);
    }} else if (strcmp(kind, "tree_to_vector") == 0) {{
        int result_len = 0;
        int *result = {name}(build_tree(parse_nullable_int_vec(lines[0])), &result_len);
        print_int_array(result, result_len);
    }} else if (strcmp(kind, "tree_to_matrix") == 0) {{
        int result_len = 0;
        int *result_cols = NULL;
        int **result = {name}(build_tree(parse_nullable_int_vec(lines[0])), &result_len, &result_cols);
        print_int_matrix(result, result_len, result_cols);
    }} else if (strcmp(kind, "tree_to_scalar") == 0) {{
        int result = {name}(build_tree(parse_nullable_int_vec(lines[0])));
        if (strcmp("{name}", "isSymmetric") == 0 || strcmp("{name}", "isValidBST") == 0) printf("%s\\n", result ? "true" : "false");
        else printf("%d\\n", result);
    }} else if (strcmp(kind, "tree_to_tree") == 0) {{
        NullableIntVec values = tree_values({name}(build_tree(parse_nullable_int_vec(lines[0]))));
        print_nullable_int_array(values.data, values.is_null, values.len);
    }} else if (strcmp(kind, "array_to_tree") == 0) {{
        IntVec nums = parse_int_vec(lines[0]);
        NullableIntVec values = tree_values({name}(nums.data, nums.len));
        print_nullable_int_array(values.data, values.is_null, values.len);
    }} else if (strcmp(kind, "two_arrays_to_tree") == 0) {{
        IntVec preorder = parse_int_vec(lines[0]);
        IntVec inorder = parse_int_vec(lines[1]);
        NullableIntVec values = tree_values({name}(preorder.data, preorder.len, inorder.data, inorder.len));
        print_nullable_int_array(values.data, values.is_null, values.len);
    }} else if (strcmp(kind, "tree_int_to_scalar") == 0) {{
        printf("%d\\n", {name}(build_tree(parse_nullable_int_vec(lines[0])), atoi(lines[1])));
    }} else if (strcmp(kind, "flatten_tree") == 0) {{
        struct TreeNode *root = build_tree(parse_nullable_int_vec(lines[0]));
        {name}(root);
        IntVec values = right_chain_values(root);
        print_int_array(values.data, values.len);
    }} else if (strcmp(kind, "tree_lca_to_value") == 0) {{
        struct TreeNode *root = build_tree(parse_nullable_int_vec(lines[0]));
        struct TreeNode *result = {name}(root, find_tree_node(root, atoi(lines[1])), find_tree_node(root, atoi(lines[2])));
        if (result) printf("%d\\n", result->val); else printf("null\\n");
    }}
    return 0;
}}
"""


def wrap_function_submission(
    code: str,
    language: str,
    problem_slug: str,
    function_signature: str | None = None,
) -> str:
    """Wrap a user function body in a stdin/stdout harness for judge execution."""
    node_profile = NODE_FUNCTION_PROFILES.get(problem_slug)
    if node_profile:
        if language == "python":
            return _wrap_node_python(code, node_profile)
        if language == "cpp":
            return _wrap_node_cpp(code, node_profile)
        if language in {"javascript", "typescript"}:
            return _wrap_node_js(code, node_profile, typescript=language == "typescript")
        if language == "java":
            return _wrap_node_java(code, node_profile)
        if language == "golang":
            return _wrap_node_go(code, node_profile)
        if language == "c":
            return _wrap_node_c(code, node_profile)

    signature = function_signature or FUNCTION_SIGNATURES.get(problem_slug)
    if signature:
        if language == "python":
            return _wrap_dynamic_python(code, signature)
        if language in {"javascript", "typescript"}:
            return _wrap_dynamic_js(code, signature, typescript=language == "typescript")
        if language == "cpp":
            return _wrap_dynamic_cpp(code, signature)
        if language == "golang":
            return _wrap_dynamic_go(code, signature)
        if language == "java":
            return _wrap_dynamic_java(code, signature)
        if language == "c":
            return _wrap_dynamic_c(code, signature)

    spec = FUNCTION_ENTRYPOINTS.get(problem_slug)
    if not spec:
        raise ValueError("Function mode is not available for this problem")

    if language == "python":
        return _wrap_python(code, spec)
    if language in {"javascript", "typescript"}:
        return _wrap_js(code, spec)
    if language == "cpp":
        return _wrap_cpp(code, spec)
    if language == "golang":
        return _wrap_go(code, spec)
    if language == "java":
        return _wrap_java(code, spec)
    if language == "c":
        return _wrap_c(code, spec)

    raise ValueError(f"Function mode is not available for language '{language}'")
