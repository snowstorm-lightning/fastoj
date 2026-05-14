import {
  aiExplainSchema,
  aiHintSchema,
  aiReviewSchema,
  problemDetailSchema,
  problemListItemSchema,
  submissionDetailSchema,
  type AIExplain,
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
    throw new ApiError(data.detail ?? data.error?.message ?? `HTTP ${response.status}`, response.status);
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
    if (!response.ok) throw new Error(data.detail ?? "Login failed");
    localStorage.setItem("fastoj.jwt", data.access_token);
    return data;
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
  async solutions(problemId: string, language?: string) {
    const params = new URLSearchParams();
    if (language) params.set("language", language);
    return request(`/api/v1/problems/${problemId}/solutions?${params}`, { method: "GET" }, (data: any) =>
      data.data ?? [],
    );
  },
  async explain(submissionId: string): Promise<AIExplain> {
    return request(`/api/v1/ai/submissions/${submissionId}/explain`, { method: "POST" }, (data) =>
      aiExplainSchema.parse(data),
    );
  },
  async review(submissionId: string): Promise<AIReview> {
    return request(`/api/v1/ai/submissions/${submissionId}/review`, { method: "POST" }, (data) =>
      aiReviewSchema.parse(data),
    );
  },
  async hint(problemId: string, level: 1 | 2 | 3, language: string | null, current_code: string | null): Promise<AIHint> {
    return request(`/api/v1/ai/problems/${problemId}/hint`, {
      method: "POST",
      body: JSON.stringify({ level, language, current_code }),
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
