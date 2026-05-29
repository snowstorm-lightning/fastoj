import {
  aiExplainSchema,
  aiChatSchema,
  aiHintSchema,
  aiReviewSchema,
  problemDetailSchema,
  problemListItemSchema,
  submissionDetailSchema,
  type AIExplain,
  type AIChat,
  type AIHint,
  type AIReview,
  type ProblemDetail,
  type ProblemListItem,
  type SubmissionDetail,
} from "./schemas";
import type { JudgeMode } from "./problemModes";
import type { Locale } from "./i18n";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export type ProblemFilters = {
  keyword?: string;
  difficulty?: string;
  tags?: string;
  page?: number;
  page_size?: number;
};

export type AIModelProfile = "default" | "deepseek" | "qwen-local";
export type AIProfile = {
  value: AIModelProfile;
  label_zh: string;
  label_en: string;
  detail_zh: string;
  detail_en: string;
  configured: boolean;
  available: boolean;
  reason?: string | null;
  checked_at?: string | null;
};
export type ProblemAgentRequest = {
  topic: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string[];
  mode: "function" | "acm" | "both";
  target_language: string;
  target_languages?: string[];
  locale: Locale;
  model_profile: AIModelProfile;
  constraints?: string | null;
};
export type AgentStep = {
  id: string;
  run_id?: string;
  step_index: number;
  step_type: string;
  tool_name?: string | null;
  status: string;
  error_message?: string | null;
  output: Record<string, unknown>;
};
export type AgentRun = {
  id: string;
  run_type: string;
  status: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error_message?: string | null;
  model_profile: string;
  locale: string;
  created_by: string;
  draft_id?: string | null;
  created_at: string;
  finished_at?: string | null;
  steps: AgentStep[];
};
export type ProblemDraft = {
  id: string;
  title: string;
  slug: string;
  description: string;
  difficulty: string;
  tags: string[];
  mode: string;
  target_languages?: string[];
  status: string;
  input_format?: string | null;
  output_format?: string | null;
  function_signature?: string | null;
  time_limit?: number;
  memory_limit?: number;
  hint?: string | null;
  official_solution_language?: string;
  official_solution_code?: string;
  official_solution_explanation?: string;
  official_solutions?: Array<{ language: string; code: string; explanation: string }>;
  time_complexity?: string | null;
  space_complexity?: string | null;
  validation_summary?: Record<string, unknown>;
  validation_report?: Record<string, any>;
  testcases?: Array<Record<string, any>>;
  steps?: AgentStep[];
  runs?: AgentRun[];
  approved_problem_id?: string | null;
};
export type ProblemDraftUpdatePayload = {
  title?: string;
  slug?: string;
  description?: string;
  difficulty?: string;
  tags?: string[];
  mode?: string;
  target_languages?: string[];
  input_format?: string | null;
  output_format?: string | null;
  function_signature?: string | null;
  time_limit?: number;
  memory_limit?: number;
  hint?: string | null;
  official_solution_language?: string;
  official_solution_code?: string;
  official_solution_explanation?: string;
  official_solutions?: Array<{ language: string; code: string; explanation: string }>;
  time_complexity?: string | null;
  space_complexity?: string | null;
  testcases?: Array<Record<string, unknown>>;
};
export type ProblemDraftSolutionGeneratePayload = {
  language: string;
  locale: Locale;
  model_profile: AIModelProfile;
  draft?: ProblemDraftUpdatePayload;
};
export type AdminProblemSolutionGeneratePayload = {
  language: string;
  locale: Locale;
  model_profile: AIModelProfile;
  problem?: Record<string, unknown>;
  solutions?: AdminSolutionPayload[];
};
export type AdminTestCase = {
  id: string;
  problem_id: string;
  input: string;
  output: string;
  is_hidden: boolean;
  is_sample: boolean;
  score: number;
  order: number;
  created_at?: string | null;
};
export type AdminTestCasePayload = {
  input: string;
  output: string;
  is_hidden: boolean;
  is_sample: boolean;
  score: number;
  order?: number | null;
};
export type AdminSolution = {
  id: string;
  problem_id: string;
  language: string;
  code: string;
  explanation: string;
  time_complexity?: string | null;
  space_complexity?: string | null;
  is_official?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};
export type AdminSolutionPayload = {
  language: string;
  code: string;
  explanation: string;
  time_complexity?: string | null;
  space_complexity?: string | null;
};
export type CurrentUser = {
  id: string;
  username: string;
  email: string;
  avatar_url?: string | null;
  locale: Locale;
  role: string;
  is_active: boolean;
};
export type UpdateMePayload = {
  username?: string;
  email?: string;
  avatar_url?: string | null;
  locale?: Locale;
  current_password?: string;
  new_password?: string;
};
export type AdminOverviewFilters = {
  userQuery?: string;
  userRole?: string;
  userStatus?: string;
  userPage?: number;
  userPageSize?: number;
  problemQuery?: string;
  problemDifficulty?: string;
  problemVisibility?: string;
  problemPage?: number;
  problemPageSize?: number;
};
export type ProblemDraftFilters = {
  query?: string;
  status?: string;
  page?: number;
  pageSize?: number;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

const SENSITIVE_ERROR_TEXT = /\b(hidden|testcases?|expected|actual|input|output|official_solution_code|current_code|code|token|password|secret|provider|prompt)\b/i;
const SAFE_BACKEND_ERROR_TEXT = [
  /^DeepSeek profile is not configured\./,
  /^AI provider returned HTTP \d{3} for model [A-Za-z0-9._:-]+\.$/,
  /^AI provider returned HTTP \d{3}\.$/,
  /^AI provider did not return a JSON object for the problem draft\.$/,
  /^AI provider returned JSON without a problem draft object\. Top-level keys: [A-Za-z0-9_, -]+\.$/,
  /^AI problem draft JSON is missing required fields: [A-Za-z0-9_., -]+\.?$/,
  /^AI problem draft JSON does not match the required schema: [A-Za-z0-9_()., -]+$/,
  /^AI provider did not return a JSON object for the official solution\.$/,
  /^AI provider returned JSON without an official solution object\. Top-level keys: [A-Za-z0-9_, -]+\.$/,
  /^AI official solution JSON does not match the required schema: [A-Za-z0-9_()., -]+$/,
  /^AI provider is unreachable at https?:\/\/[A-Za-z0-9.:/_-]+\/?[A-Za-z0-9./_-]*\./,
  /^AI provider is unreachable\./,
  /^AI provider is unavailable\./,
  /^AI provider returned an invalid chat-completions response\.$/,
  /^AI provider is disabled\./,
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeErrorText(value: string, fallback: string): string {
  const text = value.trim();
  if (!text) return fallback;
  if (SAFE_BACKEND_ERROR_TEXT.some((pattern) => pattern.test(text))) {
    return text.length > 240 ? `${text.slice(0, 237)}...` : text;
  }
  if (SENSITIVE_ERROR_TEXT.test(text)) return fallback;
  return text.length > 240 ? `${text.slice(0, 237)}...` : text;
}

function validationPath(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((part) => String(part)).filter(Boolean).join(".");
  }
  return typeof value === "string" && value.trim() ? value.trim() : "request";
}

function validationSummary(item: unknown): string | null {
  if (!isRecord(item)) return null;
  const path = validationPath(item.loc);
  const type = typeof item.type === "string" && item.type.trim() ? item.type.trim() : "invalid";
  return `${path} (${type})`;
}

export function formatApiErrorDetail(detail: unknown, fallback = "Request failed"): string {
  if (typeof detail === "string") return safeErrorText(detail, fallback);
  if (Array.isArray(detail)) {
    const items = detail.map(validationSummary).filter((item): item is string => Boolean(item));
    if (items.length) {
      const preview = items.slice(0, 4).join("; ");
      return `Validation failed: ${preview}${items.length > 4 ? "; ..." : ""}`;
    }
    return fallback;
  }
  if (isRecord(detail)) {
    if (typeof detail.message === "string") return safeErrorText(detail.message, fallback);
    if (typeof detail.detail === "string") return safeErrorText(detail.detail, fallback);
  }
  return fallback;
}

export function formatApiErrorResponse(data: unknown, fallback = "Request failed"): string {
  if (!isRecord(data)) return fallback;
  const detail = formatApiErrorDetail(data.detail, "");
  if (detail) return detail;
  if (isRecord(data.error)) {
    const message = formatApiErrorDetail(data.error.message, "");
    if (message) return message;
  }
  return fallback;
}

function token() {
  return localStorage.getItem("fastoj.jwt") ?? "";
}

async function request<T>(path: string, options: RequestInit, parse: (data: unknown) => T): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
      ...options.headers,
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(formatApiErrorResponse(data, `HTTP ${response.status}`), response.status);
  }
  return parse(data);
}

export const api = {
  async register(username: string, email: string, password: string, locale: Locale) {
    return request("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password, locale }),
    }, (data) => data);
  },
  async login(username: string, password: string) {
    const body = new URLSearchParams({ username, password });
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(formatApiErrorResponse(data, "Login failed"));
    localStorage.setItem("fastoj.jwt", data.access_token);
    return data;
  },
  async me(): Promise<CurrentUser> {
    return request("/api/v1/auth/me", { method: "GET" }, (data: any) => data);
  },
  async updateMe(payload: UpdateMePayload): Promise<CurrentUser> {
    return request("/api/v1/auth/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, (data: any) => data);
  },
  async aiProfiles(): Promise<AIProfile[]> {
    return request("/api/v1/ai/profiles", { method: "GET" }, (data: any) => data ?? []);
  },
  async adminOverview(filters: AdminOverviewFilters = {}) {
    const params = new URLSearchParams();
    if (filters.userQuery) params.set("user_query", filters.userQuery);
    if (filters.userRole) params.set("user_role", filters.userRole);
    if (filters.userStatus) params.set("user_status", filters.userStatus);
    if (filters.userPage) params.set("user_page", String(filters.userPage));
    if (filters.userPageSize) params.set("user_page_size", String(filters.userPageSize));
    if (filters.problemQuery) params.set("problem_query", filters.problemQuery);
    if (filters.problemDifficulty) params.set("problem_difficulty", filters.problemDifficulty);
    if (filters.problemVisibility) params.set("problem_visibility", filters.problemVisibility);
    if (filters.problemPage) params.set("problem_page", String(filters.problemPage));
    if (filters.problemPageSize) params.set("problem_page_size", String(filters.problemPageSize));
    return request(`/api/v1/admin/overview?${params}`, { method: "GET" }, (data: any) => data.data);
  },
  async adminUpdateUser(userId: string, payload: Record<string, unknown>) {
    return request(`/api/v1/admin/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, (data: any) => data);
  },
  async adminUpdateProblem(problemId: string, payload: Record<string, unknown>) {
    return request(`/api/v1/admin/problems/${problemId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, (data: any) => data);
  },
  async adminDeleteProblem(problemId: string) {
    return request(`/api/v1/admin/problems/${problemId}`, { method: "DELETE" }, (data: any) => data);
  },
  async adminProblemSolutions(problemId: string): Promise<AdminSolution[]> {
    return request(`/api/v1/admin/problems/${problemId}/solutions`, { method: "GET" }, (data: any) => data.data ?? []);
  },
  async adminUpsertSolution(problemId: string, payload: AdminSolutionPayload): Promise<AdminSolution> {
    return request(`/api/v1/admin/problems/${problemId}/solutions`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }, (data: any) => data.data);
  },
  async adminGenerateProblemSolution(problemId: string, payload: AdminProblemSolutionGeneratePayload) {
    return request(`/api/v1/admin/problems/${problemId}/solutions/generate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, (data: any) => data as { language: string; code: string; explanation: string });
  },
  async adminDeleteSolution(problemId: string, language: string) {
    return request(`/api/v1/admin/problems/${problemId}/solutions/${encodeURIComponent(language)}`, {
      method: "DELETE",
    }, (data: any) => data);
  },
  async adminRevalidateProblem(problemId: string): Promise<Record<string, any>> {
    return request(`/api/v1/admin/problems/${problemId}/revalidate`, {
      method: "POST",
    }, (data: any) => data.data ?? {});
  },
  async adminProblemTestcases(problemId: string): Promise<AdminTestCase[]> {
    return request(`/api/v1/admin/problems/${problemId}/testcases`, { method: "GET" }, (data: any) => data.data ?? []);
  },
  async adminCreateTestcase(problemId: string, payload: AdminTestCasePayload): Promise<AdminTestCase> {
    return request(`/api/v1/admin/problems/${problemId}/testcases`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, (data: any) => data.data);
  },
  async adminUpdateTestcase(testcaseId: string, payload: Partial<AdminTestCasePayload>): Promise<AdminTestCase> {
    return request(`/api/v1/admin/testcases/${testcaseId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, (data: any) => data.data);
  },
  async adminDeleteTestcase(testcaseId: string) {
    return request(`/api/v1/admin/testcases/${testcaseId}`, { method: "DELETE" }, (data: any) => data);
  },
  async adminCreateProblemDraft(payload: ProblemAgentRequest) {
    return request("/api/v1/admin/agent/problem-drafts", {
      method: "POST",
      body: JSON.stringify(payload),
    }, (data: any) => data);
  },
  async adminProblemDrafts(filters: ProblemDraftFilters = {}): Promise<ProblemDraft[]> {
    const params = new URLSearchParams();
    if (filters.query) params.set("query", filters.query);
    if (filters.status) params.set("status", filters.status);
    if (filters.page) params.set("page", String(filters.page));
    if (filters.pageSize) params.set("page_size", String(filters.pageSize));
    return request(`/api/v1/admin/problem-drafts?${params}`, { method: "GET" }, (data: any) => data ?? []);
  },
  async adminProblemDraft(draftId: string): Promise<ProblemDraft> {
    return request(`/api/v1/admin/problem-drafts/${draftId}`, { method: "GET" }, (data: any) => data);
  },
  async adminUpdateProblemDraft(draftId: string, payload: ProblemDraftUpdatePayload): Promise<ProblemDraft> {
    return request(`/api/v1/admin/problem-drafts/${draftId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, (data: any) => data);
  },
  async adminRevalidateProblemDraft(draftId: string): Promise<ProblemDraft> {
    return request(`/api/v1/admin/problem-drafts/${draftId}/revalidate`, {
      method: "POST",
    }, (data: any) => data);
  },
  async adminGenerateProblemDraftSolution(draftId: string, payload: ProblemDraftSolutionGeneratePayload) {
    return request(`/api/v1/admin/problem-drafts/${draftId}/solutions/generate`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, (data: any) => data as { language: string; code: string; explanation: string });
  },
  async adminAgentRun(runId: string) {
    return request(`/api/v1/admin/agent/runs/${runId}`, { method: "GET" }, (data: any) => data);
  },
  async adminApproveProblemDraft(draftId: string): Promise<ProblemDraft> {
    return request(`/api/v1/admin/problem-drafts/${draftId}/approve`, { method: "POST" }, (data: any) => data);
  },
  async adminRejectProblemDraft(draftId: string): Promise<ProblemDraft> {
    return request(`/api/v1/admin/problem-drafts/${draftId}/reject`, { method: "POST" }, (data: any) => data);
  },
  async problems(filters: ProblemFilters): Promise<ProblemListItem[]> {
    const params = new URLSearchParams();
    if (filters.keyword) params.set("keyword", filters.keyword);
    if (filters.difficulty) params.set("difficulty", filters.difficulty);
    if (filters.tags) params.set("tags", filters.tags);
    params.set("page", String(filters.page ?? 1));
    if (filters.page_size) params.set("page_size", String(filters.page_size));
    return request(`/api/v1/problems?${params}`, { method: "GET" }, (data: any) =>
      problemListItemSchema.array().parse(data.data ?? []),
    );
  },
  async problem(id: string): Promise<ProblemDetail> {
    return request(`/api/v1/problems/${id}`, { method: "GET" }, (data: any) =>
      problemDetailSchema.parse(data.data),
    );
  },
  async submit(
    problem_id: string,
    language: string,
    code: string,
    runOnly = false,
    judge_mode: JudgeMode = "acm",
    run_testcases?: Array<{ input: string }>,
  ) {
    return request(runOnly ? "/api/v1/submissions/run" : "/api/v1/submissions", {
      method: "POST",
      body: JSON.stringify({
        problem_id,
        language,
        code,
        judge_mode,
        ...(runOnly && run_testcases?.length ? { run_testcases } : {}),
      }),
    }, (data) => {
      const parsed = submissionDetailSchema.partial({ testcase_results: true }).parse(data);
      return { ...parsed, testcase_results: parsed.testcase_results ?? [] };
    });
  },
  async submission(id: string): Promise<SubmissionDetail> {
    return request(`/api/v1/submissions/${id}`, { method: "GET" }, (data) =>
      submissionDetailSchema.parse(data),
    );
  },
  async submissions(problemId?: string) {
    const params = new URLSearchParams();
    if (problemId) params.set("problem_id", problemId);
    return request(`/api/v1/submissions?${params}`, { method: "GET" }, (data: any) => data.data ?? []);
  },
  async solutions(problemId: string, language: string | undefined, locale: Locale) {
    const params = new URLSearchParams();
    if (language) params.set("language", language);
    params.set("locale", locale);
    return request(`/api/v1/problems/${problemId}/solutions?${params}`, { method: "GET" }, (data: any) =>
      data.data ?? [],
    );
  },
  async explain(submissionId: string, model_profile: AIModelProfile, locale: Locale): Promise<AIExplain> {
    return request(`/api/v1/ai/submissions/${submissionId}/explain`, {
      method: "POST",
      body: JSON.stringify({ model_profile, locale }),
    }, (data) =>
      aiExplainSchema.parse(data),
    );
  },
  async review(submissionId: string, model_profile: AIModelProfile, locale: Locale): Promise<AIReview> {
    return request(`/api/v1/ai/submissions/${submissionId}/review`, {
      method: "POST",
      body: JSON.stringify({ model_profile, locale }),
    }, (data) =>
      aiReviewSchema.parse(data),
    );
  },
  async chat(submissionId: string, message: string, model_profile: AIModelProfile, locale: Locale): Promise<AIChat> {
    return request(`/api/v1/ai/submissions/${submissionId}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, model_profile, locale }),
    }, (data) => aiChatSchema.parse(data));
  },
  async hint(
    problemId: string,
    level: 1 | 2 | 3,
    language: string | null,
    current_code: string | null,
    model_profile: AIModelProfile,
    locale: Locale,
  ): Promise<AIHint> {
    return request(`/api/v1/ai/problems/${problemId}/hint`, {
      method: "POST",
      body: JSON.stringify({ level, language, current_code, model_profile, locale }),
    }, (data) => aiHintSchema.parse(data));
  },
};

export function makeJudgeSocket(submissionId: string): WebSocket | null {
  const jwt = token();
  if (!jwt) return null;
  const base = API_BASE || window.location.origin;
  const url = new URL(base);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/ws/judge/${submissionId}`;
  url.searchParams.set("token", jwt);
  return new WebSocket(url);
}
