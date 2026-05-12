import { expect, test } from "vitest";

import { measureTrainingText } from "./textLayout";

test("measures text with safe dimensions", () => {
  const result = measureTrainingText("Dynamic Programming progress summary", 180);
  expect(result.width).toBeGreaterThan(0);
  expect(result.height).toBeGreaterThan(0);
  expect(result.lineCount).toBeGreaterThan(0);
});
