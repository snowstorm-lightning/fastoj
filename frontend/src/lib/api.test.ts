import { describe, expect, test, vi } from "vitest";

import { api, ApiError, formatApiErrorDetail, formatApiErrorResponse } from "./api";

describe("API error formatting", () => {
  test("summarizes FastAPI validation details without stringifying raw objects", () => {
    const message = formatApiErrorResponse({
      detail: [
        { loc: ["body", "email"], msg: "value is not a valid email address", type: "value_error" },
        { loc: ["body", "password"], msg: "String should have at least 8 characters", type: "string_too_short" },
      ],
    });

    expect(message).toBe("Validation failed: body.email (value_error); body.password (string_too_short)");
    expect(message).not.toContain("[object Object]");
  });

  test("refuses to surface suspicious structured or raw sensitive error text", () => {
    const fallback = "Request failed";

    expect(formatApiErrorDetail({ testcases: [{ input: "hidden-input", output: "hidden-output" }] }, fallback)).toBe(fallback);
    expect(formatApiErrorDetail("provider returned hidden_testcases with input/output fields", fallback)).toBe(fallback);
  });

  test("surfaces safe provider setup errors without exposing raw payloads", () => {
    expect(formatApiErrorResponse({
      detail: "DeepSeek profile is not configured. Set AI_DEEPSEEK_API_KEY or AI_API_KEY in .env, then restart Docker services.",
    })).toBe("DeepSeek profile is not configured. Set AI_DEEPSEEK_API_KEY or AI_API_KEY in .env, then restart Docker services.");

    expect(formatApiErrorResponse({
      detail: "AI provider returned HTTP 401 for model deepseek-v4-flash.",
    })).toBe("AI provider returned HTTP 401 for model deepseek-v4-flash.");

    expect(formatApiErrorResponse({
      detail: "AI provider is unreachable. If you selected Qwen local, start the local OpenAI-compatible server first.",
    })).toBe("AI provider is unreachable. If you selected Qwen local, start the local OpenAI-compatible server first.");

    expect(formatApiErrorResponse({
      detail: "AI provider returned JSON without a problem draft object. Top-level keys: none",
    })).toBe("AI provider returned JSON without a problem draft object. Top-level keys: none");
  });

  test("preserves structured agent run ids on API errors", async () => {
    localStorage.removeItem("fastoj.jwt");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      detail: {
        message: "AI provider returned JSON without a problem draft object. Top-level keys: none",
        run_id: "run-1",
      },
    }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    }));

    await expect(api.adminCreateProblemImport({
      raw_material: "A long imported problem statement with samples and solution notes.",
      difficulty: "medium",
      tags: ["array"],
      mode: "both",
      target_language: "python",
      target_languages: ["python"],
      locale: "zh",
      model_profile: "default",
      import_notes: null,
    })).rejects.toMatchObject({
      name: "ApiError",
      message: "AI provider returned JSON without a problem draft object. Top-level keys: none",
      status: 400,
      run_id: "run-1",
    } satisfies Partial<ApiError>);

    fetchMock.mockRestore();
  });

  test("posts problem imports to the admin import endpoint", async () => {
    localStorage.removeItem("fastoj.jwt");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      draft_id: "draft-1",
      run_id: "run-1",
      status: "validated",
      validation_summary: { passed: true },
    }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));

    const result = await api.adminCreateProblemImport({
      raw_material: "A long imported problem statement with samples and solution notes.",
      source_url: "https://example.com/problem",
      difficulty: "medium",
      tags: ["array"],
      mode: "both",
      target_language: "python",
      target_languages: ["python", "cpp"],
      locale: "zh",
      model_profile: "default",
      import_notes: "Rewrite and adapt for function mode.",
    });

    expect(result.draft_id).toBe("draft-1");
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/admin/agent/problem-imports", expect.objectContaining({
      method: "POST",
    }));
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(JSON.parse(String(init.body))).toMatchObject({
      raw_material: "A long imported problem statement with samples and solution notes.",
      source_url: "https://example.com/problem",
      mode: "both",
      target_languages: ["python", "cpp"],
      import_notes: "Rewrite and adapt for function mode.",
    });

    fetchMock.mockRestore();
  });

  test("loads admin agent runs with filters", async () => {
    localStorage.removeItem("fastoj.jwt");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify([{
      id: "run-1",
      run_type: "problem_import",
      status: "failed",
      input: {},
      output: {},
      error_message: "AI provider returned JSON without a problem draft object. Top-level keys: none",
      model_profile: "default",
      locale: "zh",
      created_by: "admin-1",
      draft_id: null,
      created_at: "2026-06-07T00:00:00Z",
      finished_at: "2026-06-07T00:00:10Z",
      steps: [{
        id: "step-1",
        run_id: "run-1",
        step_index: 1,
        step_type: "validation",
        tool_name: "pydantic",
        input: { attempt: 1 },
        output: { passed: false },
        status: "failed",
        error_message: "Invalid draft",
        created_at: "2026-06-07T00:00:05Z",
      }],
    }]), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));

    const runs = await api.adminAgentRuns({ runType: "problem_import", status: "failed", pageSize: 20 });

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/admin/agent/runs?run_type=problem_import&status=failed&page_size=20");
    expect(runs[0]?.draft_id).toBeNull();
    expect(runs[0]?.steps[0]?.input).toMatchObject({ attempt: 1 });

    fetchMock.mockRestore();
  });

  test("posts admin agent follow-ups and retries through run-scoped endpoints", async () => {
    localStorage.removeItem("fastoj.jwt");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        run_id: "run-2",
        session_id: "session-1",
        draft_id: "draft-1",
        message: "queued",
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        data: {
          run_id: "run-3",
          session_id: "session-1",
          draft_id: "draft-1",
          message: "retry queued",
        },
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));

    const followUp = await api.adminAgentFollowUp("run-1", {
      message: "Make samples clearer",
      locale: "zh",
      model_profile: "default",
      draft_id: "draft-1",
    });
    const retry = await api.adminRetryAgentRun("run-1", {
      locale: "zh",
      model_profile: "default",
      draft_id: "draft-1",
      message: null,
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/admin/agent/runs/run-1/follow-ups");
    expect(JSON.parse(String((fetchMock.mock.calls[0]?.[1] as RequestInit).body))).toMatchObject({
      message: "Make samples clearer",
      draft_id: "draft-1",
    });
    expect(followUp.run_id).toBe("run-2");
    expect(followUp.session_id).toBe("session-1");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("/api/v1/admin/agent/runs/run-1/retry");
    expect(retry.run_id).toBe("run-3");
    expect(retry.session_id).toBe("session-1");

    fetchMock.mockRestore();
  });

  test("loads admin agent sessions with filters and details", async () => {
    localStorage.removeItem("fastoj.jwt");
    const session = {
      id: "session-1",
      title: "Two sum variants",
      run_type: "problem_authoring",
      status: "succeeded",
      mode: "both",
      source_kind: null,
      draft_count: 1,
      run_count: 2,
      latest_draft: null,
      latest_run: null,
      drafts: [],
      runs: [],
      messages: [{
        id: "message-1",
        role: "user",
        message: "Make a graph problem",
        run_id: "run-1",
        created_at: "2026-06-07T00:00:00Z",
      }],
      created_at: "2026-06-07T00:00:00Z",
      updated_at: "2026-06-07T00:02:00Z",
    };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify([session]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify(session), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));

    const sessions = await api.adminAgentSessions({ runType: "problem_authoring", status: "succeeded", page: 2, pageSize: 10 });
    const detail = await api.adminAgentSession("session-1");

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/admin/agent/sessions?run_type=problem_authoring&status=succeeded&page=2&page_size=10");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("/api/v1/admin/agent/sessions/session-1");
    expect(sessions[0]?.id).toBe("session-1");
    expect(detail.messages[0]?.message).toBe("Make a graph problem");

    fetchMock.mockRestore();
  });

  test("supports nested discussion replies, likes, unlikes, and deletion endpoints", async () => {
    localStorage.removeItem("fastoj.jwt");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        success: true,
        data: {
          id: "comment-2",
          problem_id: "problem-1",
          user_id: "user-1",
          author: "alice",
          body: "Nested reply",
          parent_id: "comment-1",
          like_count: 0,
          liked_by_me: false,
          reply_count: 0,
          can_delete: true,
          is_deleted: false,
          is_template: false,
          replies: [],
          created_at: "2026-06-07T00:00:00Z",
        },
      }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        success: true,
        data: { liked: true, like_count: 1 },
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        success: true,
        data: { liked: false, like_count: 0 },
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));

    const reply = await api.createDiscussion("problem-1", "Nested reply", "comment-1");
    const liked = await api.likeDiscussion("problem-1", "comment-2");
    const unliked = await api.unlikeDiscussion("problem-1", "comment-2");
    await api.deleteDiscussion("problem-1", "comment-2");

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/problems/problem-1/discussions");
    expect(JSON.parse(String((fetchMock.mock.calls[0]?.[1] as RequestInit).body))).toMatchObject({
      body: "Nested reply",
      parent_id: "comment-1",
    });
    expect(reply.parent_id).toBe("comment-1");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("/api/v1/problems/problem-1/discussions/comment-2/like");
    expect(liked).toEqual({ liked: true, like_count: 1 });
    expect(fetchMock.mock.calls[2]?.[1]).toMatchObject({ method: "DELETE" });
    expect(unliked).toEqual({ liked: false, like_count: 0 });
    expect(fetchMock.mock.calls[3]?.[0]).toBe("/api/v1/problems/problem-1/discussions/comment-2");

    fetchMock.mockRestore();
  });

  test("returns Python fallback solutions with their real language", async () => {
    localStorage.removeItem("fastoj.jwt");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      success: true,
      data: [{
        id: "solution-1",
        language: "python",
        code: "def two_sum(nums, target):\n    return []\n",
        explanation: "Python fallback explanation",
        time_complexity: "O(n)",
        space_complexity: "O(n)",
      }],
    }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));

    const result = await api.solutions("problem-1", "cpp", "zh");

    expect(result[0].language).toBe("python");
    expect(result[0].code).toContain("def two_sum");
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/problems/problem-1/solutions?language=cpp&locale=zh");

    fetchMock.mockRestore();
  });

  test("requests problem detail with locale and preserves sample explanations", async () => {
    localStorage.removeItem("fastoj.jwt");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      success: true,
      data: {
        id: "problem-1",
        title: "Two Sum",
        slug: "two-sum",
        description: "Find two indices.",
        difficulty: "easy",
        tags: ["Array"],
        time_limit: 1000,
        memory_limit: 256,
        hint: null,
        mode: "function",
        function_signature: "def two_sum(nums: list[int], target: int) -> list[int]",
        total_submissions: 0,
        accepted_submissions: 0,
        ac_rate: 0,
        sample_testcases: [{ input: "[2,7,11,15]\n9", output: "[0,1]", explanation: "中文示例解释" }],
        created_at: "2026-06-07T00:00:00Z",
      },
    }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));

    const result = await api.problem("problem-1", "zh");

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/problems/problem-1?locale=zh");
    expect(result.sample_testcases[0]?.explanation).toBe("中文示例解释");

    fetchMock.mockRestore();
  });
});
