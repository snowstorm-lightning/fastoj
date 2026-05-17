import re
import textwrap

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
void print_int_array(int *values, int len) {
    printf("[");
    for (int i = 0; i < len; i++) { if (i) printf(","); printf("%d", values[i]); }
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
    public static void main(String[] args) throws Exception {{
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


def _parameter_names_from_signature(function_signature: str) -> list[str]:
    function_name = _function_name_from_signature(function_signature)
    match = re.search(rf"def\s+{re.escape(function_name)}\s*\((?P<params>.*?)\)", function_signature, re.DOTALL)
    if not match:
        raise ValueError("Function mode requires a parseable Python function signature")
    names: list[str] = []
    for item in _split_signature_parameters(match.group("params")):
        cleaned = item.strip()
        if not cleaned or cleaned.startswith("*"):
            continue
        name = cleaned.split(":", 1)[0].split("=", 1)[0].strip()
        if name and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            names.append(name)
    return names


def _wrap_dynamic_python(code: str, function_signature: str) -> str:
    function_name = _function_name_from_signature(function_signature)
    parameter_names = ", ".join(repr(name) for name in _parameter_names_from_signature(function_signature))
    return f"""{code.rstrip()}

if __name__ == "__main__":
    import json
    import sys

    def _fastoj_load_args(raw, parameter_names):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            return []
        if len(lines) > 1:
            args = [json.loads(line) for line in lines]
            names = [name for name in parameter_names if name not in ("self", "cls")]
            if names and len(args) != len(names):
                raise ValueError("Function-mode testcase input argument count does not match function_signature.")
            return args
        value = json.loads(lines[0])
        names = [name for name in parameter_names if name not in ("self", "cls")]
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

    raw = sys.stdin.read().strip()
    args = _fastoj_load_args(raw, [{parameter_names}])
    func = globals().get("{function_name}")
    if not callable(func) and "Solution" in globals():
        candidate = getattr(Solution(), "{function_name}", None)
        if callable(candidate):
            func = candidate
    if not callable(func):
        raise NameError("Expected function {function_name}")
    result = func(*args)
    if isinstance(result, bool):
        print(str(result).lower())
    elif isinstance(result, (list, dict)):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)
"""


def wrap_function_submission(
    code: str,
    language: str,
    problem_slug: str,
    function_signature: str | None = None,
) -> str:
    """Wrap a user function body in a stdin/stdout harness for judge execution."""
    spec = FUNCTION_ENTRYPOINTS.get(problem_slug)
    if not spec:
        if language == "python" and function_signature:
            return _wrap_dynamic_python(code, function_signature)
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
