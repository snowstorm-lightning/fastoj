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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export type ProblemFilters = {
  keyword?: string;
  difficulty?: string;
  tags?: string;
  page?: number;
};

export type AIModelProfile = "default" | "deepseek" | "qwen-local";
export type ProblemAgentRequest = {
  topic: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string[];
  mode: "function" | "acm";
  target_language: string;
  locale: "zh" | "en";
  model_profile: AIModelProfile;
  constraints?: string | null;
};
export type AgentStep = {
  id: string;
  step_index: number;
  step_type: string;
  tool_name?: string | null;
  status: string;
  error_message?: string | null;
  output: Record<string, unknown>;
};
export type ProblemDraft = {
  id: string;
  title: string;
  slug: string;
  description: string;
  difficulty: string;
  tags: string[];
  mode: string;
  status: string;
  validation_summary?: Record<string, unknown>;
  validation_report?: Record<string, any>;
  testcases?: Array<Record<string, any>>;
  approved_problem_id?: string | null;
};
export type CurrentUser = {
  id: string;
  username: string;
  email: string;
  avatar_url?: string | null;
  role: string;
  is_active: boolean;
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeErrorText(value: string, fallback: string): string {
  const text = value.trim();
  if (!text) return fallback;
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
  async register(username: string, email: string, password: string) {
    return request("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
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
  async updateMe(payload: Record<string, unknown>): Promise<CurrentUser> {
    return request("/api/v1/auth/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, (data: any) => data);
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
  async adminUpsertSolution(problemId: string, payload: Record<string, unknown>) {
    return request(`/api/v1/admin/problems/${problemId}/solutions`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }, (data: any) => data);
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
    return request(`/api/v1/problems?${params}`, { method: "GET" }, (data: any) =>
      problemListItemSchema.array().parse(data.data ?? []),
    );
  },
  async problem(id: string): Promise<ProblemDetail> {
    return request(`/api/v1/problems/${id}`, { method: "GET" }, (data: any) =>
      problemDetailSchema.parse(data.data),
    );
  },
  async submit(problem_id: string, language: string, code: string, runOnly = false, judge_mode: JudgeMode = "acm") {
    return request(runOnly ? "/api/v1/submissions/run" : "/api/v1/submissions", {
      method: "POST",
      body: JSON.stringify({ problem_id, language, code, judge_mode }),
    }, (data) => submissionDetailSchema.partial({ testcase_results: true }).parse(data));
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
  async solutions(problemId: string, language?: string, locale = "en") {
    const params = new URLSearchParams();
    if (language) params.set("language", language);
    params.set("locale", locale);
    return request(`/api/v1/problems/${problemId}/solutions?${params}`, { method: "GET" }, (data: any) =>
      data.data ?? [],
    );
  },
  async explain(submissionId: string, model_profile: AIModelProfile = "default", locale = "en"): Promise<AIExplain> {
    return request(`/api/v1/ai/submissions/${submissionId}/explain`, {
      method: "POST",
      body: JSON.stringify({ model_profile, locale }),
    }, (data) =>
      aiExplainSchema.parse(data),
    );
  },
  async review(submissionId: string, model_profile: AIModelProfile = "default", locale = "en"): Promise<AIReview> {
    return request(`/api/v1/ai/submissions/${submissionId}/review`, {
      method: "POST",
      body: JSON.stringify({ model_profile, locale }),
    }, (data) =>
      aiReviewSchema.parse(data),
    );
  },
  async chat(submissionId: string, message: string, model_profile: AIModelProfile = "default", locale = "en"): Promise<AIChat> {
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
    model_profile: AIModelProfile = "default",
    locale = "en",
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
