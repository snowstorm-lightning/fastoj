import { describe, expect, test, vi } from "vitest";

import { api, formatApiErrorDetail, formatApiErrorResponse } from "./api";

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
});
