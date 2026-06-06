import type { ProblemDetail, ProblemListItem } from "./schemas";
import { PROBLEM_ZH_EXTRA } from "./problemZh";
import { detailedZhProblemDescription } from "./problemStatementZh";

export const LOCALE_META = {
  zh: {
    htmlLang: "zh-CN",
    browserPrefixes: ["zh"],
    label: "中文",
    shortLabel: "中",
    switchLabel: "EN",
    sourceText: false,
    aiResponseLanguage: "Simplified Chinese",
  },
  en: {
    htmlLang: "en",
    browserPrefixes: ["en"],
    label: "English",
    shortLabel: "EN",
    switchLabel: "中",
    sourceText: true,
    aiResponseLanguage: "English",
  },
} as const;

export type Locale = keyof typeof LOCALE_META;

export const SUPPORTED_LOCALES = Object.keys(LOCALE_META) as Locale[];
export const DEFAULT_LOCALE = "zh" satisfies Locale;
export const LOCALE_STORAGE_KEY = "fastoj.locale";

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && Object.prototype.hasOwnProperty.call(LOCALE_META, value);
}

export function normalizeLocale(value: unknown): Locale | null {
  return isLocale(value) ? value : null;
}

export function htmlLangForLocale(locale: Locale): string {
  return LOCALE_META[locale].htmlLang;
}

export function nextLocale(locale: Locale): Locale {
  const index = SUPPORTED_LOCALES.indexOf(locale);
  return SUPPORTED_LOCALES[(index + 1) % SUPPORTED_LOCALES.length] ?? DEFAULT_LOCALE;
}

export function localeLabel(locale: Locale): string {
  return LOCALE_META[locale].label;
}

export function localeText(
  locale: Locale,
  values: Partial<Record<Locale, string>> & Pick<Record<Locale, string>, typeof DEFAULT_LOCALE>,
): string {
  return localeValue(locale, values);
}

export function localeValue<T>(
  locale: Locale,
  values: Partial<Record<Locale, T>> & Pick<Record<Locale, T>, typeof DEFAULT_LOCALE>,
): T {
  return values[locale] ?? values[DEFAULT_LOCALE];
}

type LocalizedText = Partial<Record<Locale, string>> & Pick<Record<Locale, string>, typeof DEFAULT_LOCALE>;
type LocalizedTuple = Partial<Record<Locale, [string, string]>> & Pick<Record<Locale, [string, string]>, typeof DEFAULT_LOCALE>;

function browserLocale(): Locale {
  if (typeof navigator === "undefined") return DEFAULT_LOCALE;
  const languages = [...(navigator.languages ?? []), navigator.language].filter((language): language is string => Boolean(language));
  for (const language of languages) {
    const normalized = language.toLowerCase();
    const match = SUPPORTED_LOCALES.find((locale) => (
      LOCALE_META[locale].browserPrefixes.some((prefix) => normalized.startsWith(prefix))
    ));
    if (match) return match;
  }
  return DEFAULT_LOCALE;
}

export function readStoredLocale(): Locale {
  if (typeof localStorage === "undefined") return browserLocale();
  try {
    return normalizeLocale(localStorage.getItem(LOCALE_STORAGE_KEY)) ?? browserLocale();
  } catch {
    return browserLocale();
  }
}

export function writeStoredLocale(locale: Locale) {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // Ignore storage failures so the UI language can still switch in-memory.
  }
}

export const UI = {
  zh: {
    navLibrary: "题库",
    navWorkbench: "刷题",
    navGraph: "图谱",
    navSettings: "设置",
    login: "登录",
    register: "注册",
    logout: "退出",
    loggedIn: "已登录",
    authMessage: "登录后可以提交、查看个人轨迹并使用 AI 解释。",
    authExpired: "登录已过期，请重新登录。",
    authSuccess: "认证成功，正在进入题库。",
    authFailure: "认证失败",
    authInvalidCredentials: "用户名或密码错误。",
    authAlreadyRegistered: "用户名或邮箱已被注册。",
    authInvalidFields: "请检查用户名、邮箱和密码格式。",
    authPanelTitle: "进入训练空间",
    accountCopy: "题库、代码草稿、提交记录和AI反馈会在同一个账号下持续保存。",
    username: "用户名",
    email: "邮箱",
    password: "密码",
    confirmPassword: "确认密码",
    passwordMismatch: "两次输入的密码不一致。",
    authDialogTitle: "认证失败",
    registerSuccessTitle: "注册成功",
    registerSuccessMessage: "账号已创建并登录，继续进入题库。",
    dialogConfirm: "确定",
    processing: "处理中...",
    loginContinue: "登录并继续",
    registerContinue: "注册并继续",
    library: "题库",
    filters: "筛选",
    keyword: "关键字",
    allDifficulty: "全部难度",
    tagsPlaceholder: "标签，如 Array 或 AI",
    resetFilters: "重置筛选",
    layout: "布局",
    layoutOptions: "题库布局",
    cardLayout: "卡片",
    listLayout: "列表",
    solved: "已通过",
    openProblem: "打开题目",
    tags: "标签",
    modes: "模式",
    noTags: "综合",
    currentProblems: "当前题目",
    functionMode: "函数模式",
    acmMode: "ACM 模式",
    aiAlgorithms: "AI 算法",
    averageAc: "平均 AC",
    recommendation: "推荐",
    start: "开始",
    graph: "图谱",
    libraryCopy: "支持核心函数模式和 ACM 标准输入输出模式。",
    previous: "上一页",
    next: "下一页",
    page: "第",
    backLibrary: "返回题库",
    workbench: "练习台",
    resetTemplate: "重置模板",
    codeCompletion: "代码补全",
    codeCompletionOn: "关闭代码补全提示",
    codeCompletionOff: "开启代码补全提示",
    runTitle: "运行公开样例",
    submitTitle: "提交完整评测",
    publicCases: "用例",
    solution: "题解",
    judge: "判题",
    trail: "记录",
    discussion: "讨论",
    loadingProblem: "加载题目中...",
    acceptance: "通过率",
    submissions: "累计提交",
    officialHint: "官方提示",
    noHint: "暂无官方提示。",
    loadingCases: "加载公开用例中...",
    noSolution: "当前语言暂无官方题解。",
    acmFrame: "ACM 模式：请自行处理标准输入和标准输出。",
    noFunctionFrame: "当前题目没有函数模式模板。",
    modeFunctionTitle: "点击切换到 ACM 模式。当前只需要补全题目给定函数。",
    modeAcmTitle: "点击切换到函数模式。当前需要自行处理标准输入输出。",
    modeAcmOnlyTitle: "当前题目不支持函数模式，只能使用 ACM 模式。",
    chooseProblem: "选择一道题开始",
    chooseProblemCopy: "题面、模板、代码区、图解和判题轨迹会按工作台布局展开。",
    input: "输入",
    output: "输出",
    explanation: "解释",
    collapseLeft: "收起题面",
    expandLeft: "展开题面",
    collapseRight: "收起 AI 辅助",
    expandRight: "展开 AI 辅助",
    pickLanguage: "选择提交语言",
    settingsTitle: "账号设置",
    settingsCopy: "管理账号资料、语言偏好和本地训练体验。",
    displayName: "显示名称",
    compactMode: "紧凑模式",
    saveSettings: "保存设置",
    discussionTitle: "题目讨论",
    discussionPlaceholder: "分享思路、卡点或复杂度讨论。不要粘贴隐藏用例。",
    postDiscussion: "发布讨论",
    noDiscussion: "暂无讨论。",
    discussionLocalNotice: "讨论会保存到服务器，其他用户也能看到。",
    discussionLoginRequired: "请先登录后发布讨论。",
  },
  en: {
    navLibrary: "Problems",
    navWorkbench: "Practice",
    navGraph: "Graph",
    navSettings: "Settings",
    login: "Log in",
    register: "Sign up",
    logout: "Log out",
    loggedIn: "Signed in",
    authMessage: "Sign in to submit, review your attempts, and use AI explanations.",
    authExpired: "Your session has expired. Please log in again.",
    authSuccess: "Authenticated. Opening the problem library.",
    authFailure: "Authentication failed",
    authInvalidCredentials: "Incorrect username or password.",
    authAlreadyRegistered: "Username or email already registered.",
    authInvalidFields: "Please check the username, email, and password fields.",
    authPanelTitle: "Enter the Training Space",
    accountCopy: "Problem sets, code drafts, submission history, and AI feedback stay saved under the same account.",
    username: "Username",
    email: "Email",
    password: "Password",
    confirmPassword: "Confirm password",
    passwordMismatch: "The two passwords do not match.",
    authDialogTitle: "Authentication failed",
    registerSuccessTitle: "Registration complete",
    registerSuccessMessage: "Your account has been created and signed in. Continue to the problem library.",
    dialogConfirm: "OK",
    processing: "Working...",
    loginContinue: "Log in and continue",
    registerContinue: "Sign up and continue",
    library: "Problems",
    filters: "Filters",
    keyword: "Keyword",
    allDifficulty: "All difficulties",
    tagsPlaceholder: "Tag, e.g. Array or AI",
    resetFilters: "Reset filters",
    layout: "Layout",
    layoutOptions: "Problem layout",
    cardLayout: "Cards",
    listLayout: "List",
    solved: "Solved",
    openProblem: "Open problem",
    tags: "Tags",
    modes: "Modes",
    noTags: "General",
    currentProblems: "Problems",
    functionMode: "Function mode",
    acmMode: "ACM mode",
    aiAlgorithms: "AI algorithms",
    averageAc: "Average AC",
    recommendation: "Recommended",
    start: "Start",
    graph: "Graph",
    libraryCopy: "Practice with core function mode or ACM stdin/stdout mode.",
    previous: "Previous",
    next: "Next",
    page: "Page",
    backLibrary: "Back to problems",
    workbench: "Workbench",
    resetTemplate: "Reset template",
    codeCompletion: "Autocomplete",
    codeCompletionOn: "Turn autocomplete off",
    codeCompletionOff: "Turn autocomplete on",
    runTitle: "Run public samples",
    submitTitle: "Submit full judging",
    publicCases: "Cases",
    solution: "Solution",
    judge: "Judge",
    trail: "Trail",
    discussion: "Discuss",
    loadingProblem: "Loading problem...",
    acceptance: "Acceptance",
    submissions: "Submissions",
    officialHint: "Official hint",
    noHint: "No official hint yet.",
    loadingCases: "Loading samples...",
    noSolution: "No official solution for this language yet.",
    acmFrame: "ACM mode: read stdin and print stdout yourself.",
    noFunctionFrame: "This problem has no function-mode template.",
    modeFunctionTitle: "Click to switch to ACM mode. You only complete the given function now.",
    modeAcmTitle: "Click to switch to function mode. You handle stdin/stdout now.",
    modeAcmOnlyTitle: "This problem only supports ACM mode.",
    chooseProblem: "Choose a problem",
    chooseProblemCopy: "The statement, template, editor, visual guide, and judge trail will open here.",
    input: "Input",
    output: "Output",
    explanation: "Explanation",
    collapseLeft: "Collapse statement",
    expandLeft: "Open statement",
    collapseRight: "Collapse result",
    expandRight: "Open result",
    pickLanguage: "Choose language",
    settingsTitle: "Account Settings",
    settingsCopy: "Manage your profile, language preference, and local training experience.",
    displayName: "Display name",
    compactMode: "Compact mode",
    saveSettings: "Save settings",
    discussionTitle: "Problem Discussion",
    discussionPlaceholder: "Share an idea, blocker, or complexity note. Do not paste hidden cases.",
    postDiscussion: "Post discussion",
    noDiscussion: "No discussion yet.",
    discussionLocalNotice: "Discussion is saved on the server and visible to other users.",
    discussionLoginRequired: "Sign in before posting discussion.",
  },
} as const;

type UIMessages = Record<keyof (typeof UI)[typeof DEFAULT_LOCALE], string>;
const UI_BY_LOCALE: Partial<Record<Locale, UIMessages>> & Record<typeof DEFAULT_LOCALE, UIMessages> = UI;

export function getUI(locale: Locale): UIMessages {
  return UI_BY_LOCALE[locale] ?? UI_BY_LOCALE[DEFAULT_LOCALE];
}

const VERDICTS: Record<string, LocalizedTuple> = {
  idle: {
    zh: ["未运行", "还没有提交或运行代码。"],
    en: ["Idle", "No run or submission has been started."],
  },
  pending: {
    zh: ["等待中", "提交已创建，正在等待 worker 处理。"],
    en: ["Pending", "The submission has been queued for judging."],
  },
  judging: {
    zh: ["评测中", "代码正在沙箱中编译或运行。"],
    en: ["Judging", "The code is compiling or running in the sandbox."],
  },
  finished: {
    zh: ["已完成", "评测流程已结束，请查看具体结果。"],
    en: ["Finished", "Judging is complete. Check the concrete verdict."],
  },
  ac: {
    zh: ["通过", "Accepted：所有参与评测的用例均通过。"],
    en: ["AC", "Accepted: all judged cases passed."],
  },
  wa: {
    zh: ["答案错误", "Wrong Answer：程序正常结束，但输出与期望不一致。"],
    en: ["WA", "Wrong Answer: output differs from the expected answer."],
  },
  re: {
    zh: ["运行错误", "Runtime Error：程序运行时崩溃、异常退出，或返回了非零退出码。"],
    en: ["RE", "Runtime Error: the program crashed, raised an exception, or exited non-zero."],
  },
  ce: {
    zh: ["编译错误", "Compile Error：代码未能通过编译或运行前检查。"],
    en: ["CE", "Compile Error: the code failed to compile or prepare."],
  },
  tle: {
    zh: ["超时", "Time Limit Exceeded：程序超过题目时间限制。"],
    en: ["TLE", "Time Limit Exceeded: the program exceeded the time limit."],
  },
  mle: {
    zh: ["内存超限", "Memory Limit Exceeded：程序超过题目内存限制。"],
    en: ["MLE", "Memory Limit Exceeded: the program exceeded the memory limit."],
  },
  se: {
    zh: ["系统错误", "System Error：评测系统或沙箱执行路径出现问题。"],
    en: ["SE", "System Error: the judge or sandbox failed."],
  },
};

export function verdictInfo(code: string | null | undefined, locale: Locale) {
  const key = (code ?? "idle").toLowerCase();
  const fallback: [string, string] = [
    code ?? "idle",
    localeText(locale, { zh: "未知评测结果。", en: "Unknown verdict." }),
  ];
  const [label, description] = VERDICTS[key] ? localeValue(locale, VERDICTS[key]) : fallback;
  return { label, description, code: key };
}

const DIFFICULTY_LABELS: Record<string, LocalizedText> = {
  easy: { zh: "简单", en: "Easy" },
  medium: { zh: "中等", en: "Medium" },
  hard: { zh: "困难", en: "Hard" },
};

const TAG_LABELS: Record<string, string> = {
  AI: "AI",
  Array: "数组",
  Backtracking: "回溯",
  "Binary Search": "二分查找",
  "Binary Search Tree": "二叉搜索树",
  "Binary Tree": "二叉树",
  "Bit Manipulation": "位运算",
  "Breadth-First Search": "广度优先搜索",
  "Bucket Sort": "桶排序",
  Combinatorics: "组合数学",
  Counting: "计数",
  "Data Stream": "数据流",
  "Deep Learning": "深度学习",
  "Depth-First Search": "深度优先搜索",
  Design: "设计",
  "Divide and Conquer": "分治",
  "Dynamic Programming": "动态规划",
  Function: "函数",
  Graph: "图",
  Greedy: "贪心",
  "Hash Table": "哈希表",
  Heap: "堆",
  "Hot 100": "热门 100",
  Interview: "面试",
  KMeans: "KMeans",
  KNN: "KNN",
  Knapsack: "背包",
  "Linked List": "链表",
  "Logistic Regression": "逻辑回归",
  Math: "数学",
  Matrix: "矩阵",
  "Merge Sort": "归并排序",
  MHA: "多头注意力",
  ML: "机器学习",
  "Monotonic Queue": "单调队列",
  "Monotonic Stack": "单调栈",
  "Prefix Product": "前缀积",
  "Prefix Sum": "前缀和",
  Queue: "队列",
  Recursion: "递归",
  Simulation: "模拟",
  "Sliding Window": "滑动窗口",
  Softmax: "Softmax",
  Sorting: "排序",
  Stack: "栈",
  String: "字符串",
  "Topological Sort": "拓扑排序",
  Tree: "树",
  Trie: "字典树",
  "Two Heaps": "双堆",
  "Two Pointers": "双指针",
};

const TAG_CANONICAL_BY_ZH = new Map(Object.entries(TAG_LABELS).map(([tag, label]) => [label, tag]));
const TAG_CANONICAL_BY_LOWER = new Map(Object.keys(TAG_LABELS).map((tag) => [tag.toLowerCase(), tag]));

export function localizeDifficulty(difficulty: string | null | undefined, locale: Locale): string {
  if (!difficulty) return "";
  const label = DIFFICULTY_LABELS[difficulty.toLowerCase()];
  return label ? localeText(locale, label) : difficulty;
}

export function localizeTag(tag: string, locale: Locale): string {
  if (LOCALE_META[locale].sourceText) return tag;
  return TAG_LABELS[tag] ?? tag;
}

export function localizeTags(tags: string[] | null | undefined, locale: Locale): string[] {
  return (tags ?? []).map((tag) => localizeTag(tag, locale));
}

export function canonicalTagQuery(value: string, locale: Locale): string {
  const parts = value.split(/[,，]/).map((tag) => tag.trim()).filter(Boolean);
  if (LOCALE_META[locale].sourceText) {
    return parts.map((tag) => TAG_CANONICAL_BY_LOWER.get(tag.toLowerCase()) ?? tag).join(", ");
  }
  return value
    .split(/[,，]/)
    .map((tag) => {
      const trimmed = tag.trim();
      return TAG_CANONICAL_BY_ZH.get(trimmed) ?? TAG_CANONICAL_BY_LOWER.get(trimmed.toLowerCase()) ?? trimmed;
    })
    .filter(Boolean)
    .join(", ");
}

const PROBLEM_ZH: Record<string, { title: string; description?: string; hint?: string }> = {
  ...PROBLEM_ZH_EXTRA,
  "two-sum": {
    title: "两数之和",
    description: "给定整数数组 nums 和目标值 target，返回两个数的下标，使它们相加等于 target。",
    hint: "用哈希表记录已经扫描过的值。",
  },
  "add-two-numbers": {
    title: "两数相加",
    description: "两个逆序数字数组表示两个非负整数，返回它们相加后的逆序数字数组。",
    hint: "同时遍历两个数组，并维护进位。",
  },
  "longest-substring-without-repeating": {
    title: "无重复字符的最长子串",
    description: "给定字符串 s，找出不含重复字符的最长子串长度。",
    hint: "维护滑动窗口和字符最近出现位置。",
  },
  "valid-parentheses": {
    title: "有效的括号",
    description: "判断括号字符串是否按正确顺序闭合。",
    hint: "用栈保存左括号，遇到右括号时检查栈顶是否匹配。",
  },
  "maximum-subarray": {
    title: "最大子数组和",
    description: "返回非空连续子数组的最大和。",
    hint: "维护以当前位置结尾的最大子数组和，同时更新全局最大值。",
  },
  "group-anagrams": {
    title: "字母异位词分组",
    description: "将互为字母异位词的字符串分到同一组。",
    hint: "把排序后的字符串或字符计数作为分组键。",
  },
  "merge-intervals": {
    title: "合并区间",
    description: "合并所有重叠区间，并按左端点输出。",
    hint: "先按左端点排序，再和当前结果的最后一个区间比较是否重叠。",
  },
  "climbing-stairs": {
    title: "爬楼梯",
    description: "每次爬 1 或 2 阶，计算到达楼顶的不同方法数。",
    hint: "状态转移与斐波那契相同，ways[n] = ways[n-1] + ways[n-2]。",
  },
  "container-with-most-water": {
    title: "盛最多水的容器",
    description: "选择两条竖线，使它们与 x 轴围成的容器能装最多水。",
    hint: "双指针从两端向内收缩，每次移动较短的那条边。",
  },
  "logistic-regression-sigmoid": {
    title: "逻辑回归 Sigmoid",
    description: "实现 p=sigmoid(w dot x + b) 的预测概率。",
    hint: "先求线性得分，再用 sigmoid 映射到 0 到 1。",
  },
  "knn-majority-vote": {
    title: "KNN 多数投票",
    description: "按欧氏距离选出 k 个最近训练样本，并用多数投票预测标签。",
    hint: "先计算距离并排序，再对前 k 个标签计数。",
  },
  "kmeans-one-iteration": {
    title: "KMeans 一轮分配",
    description: "给定固定中心点，将每个样本分配到最近的簇。",
    hint: "对每个样本遍历所有中心，选择距离最小的中心编号。",
  },
  "scaled-dot-product-attention": {
    title: "缩放点积注意力",
    description: "手写单个 query 的 scaled dot-product attention 输出。",
    hint: "点积后除以 sqrt(d)，做 softmax，再加权求和 value。",
  },
  "softmax-cross-entropy": {
    title: "Softmax 交叉熵",
    description: "给定 logits 和目标类别，计算数值稳定的 softmax cross-entropy loss。",
    hint: "先减去最大 logit 保持数值稳定，再取目标类别概率的负对数。",
  },
  "attention-mask-apply": {
    title: "注意力 Mask 应用",
    description: "对注意力分数应用 mask，被屏蔽位置的概率必须为 0。",
    hint: "只对可见位置做 softmax，被 mask 的位置直接输出 0。",
  },
};

PROBLEM_ZH["longest-substring-without-repeating-characters"] =
  PROBLEM_ZH["longest-substring-without-repeating"];

export function localizedProblem<T extends ProblemDetail | ProblemListItem | undefined>(
  problem: T,
  locale: Locale,
) {
  if (!problem || LOCALE_META[locale].sourceText) return problem;
  const zh = PROBLEM_ZH[problem.slug];
  if (!zh) return problem;
  const result = { ...problem, title: zh.title } as NonNullable<T>;
  if ("description" in result && zh.description) {
    (result as ProblemDetail).description = detailedZhProblemDescription(result, zh.description);
  }
  if ("hint" in result && zh.hint) {
    (result as ProblemDetail).hint = zh.hint;
  }
  return result as T;
}

function normalizeProblemSearch(value: string): string {
  return value.trim().toLocaleLowerCase();
}

export function localizedProblemSearchText(problem: ProblemDetail | ProblemListItem, locale: Locale): string {
  const displayProblem = localizedProblem(problem, locale) ?? problem;
  const parts = [
    problem.title,
    problem.slug,
    ...problem.tags,
    localizeDifficulty(problem.difficulty, locale),
    ...localizeTags(problem.tags, locale),
    displayProblem.title,
    "description" in displayProblem ? displayProblem.description : "",
    "hint" in displayProblem ? displayProblem.hint ?? "" : "",
  ];
  return normalizeProblemSearch(parts.filter(Boolean).join(" "));
}

export function matchesLocalizedProblem(problem: ProblemDetail | ProblemListItem, locale: Locale, keyword: string): boolean {
  const query = normalizeProblemSearch(keyword);
  if (!query) return true;
  return localizedProblemSearchText(problem, locale).includes(query);
}
