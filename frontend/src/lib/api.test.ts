import { describe, expect, test } from "vitest";

import { formatApiErrorDetail, formatApiErrorResponse } from "./api";

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
});
