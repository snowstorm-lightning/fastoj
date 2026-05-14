import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { TrainingGraph } from "./TrainingGraph";

test("renders training graph nodes", () => {
  render(
    <TrainingGraph
      problems={[
        {
          id: "p1",
          title: "Two Sum",
          slug: "two-sum",
          difficulty: "EASY",
          tags: ["Array", "Hash Table"],
          total_submissions: 10,
          accepted_submissions: 5,
          ac_rate: 0.5,
          is_public: true,
          created_at: "2026-05-12T00:00:00",
        },
      ]}
      locale="en"
      onTag={vi.fn()}
    />,
  );
  expect(screen.getByTestId("training-graph")).toBeInTheDocument();
  expect(screen.getByText("Array")).toBeInTheDocument();
});
