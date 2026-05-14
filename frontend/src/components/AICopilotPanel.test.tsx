import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { AICopilotPanel } from "./AICopilotPanel";

test("renders AI copilot controls", () => {
  render(
    <AICopilotPanel
      submission={null}
      explain={null}
      review={null}
      hint={null}
      error={null}
      onExplain={vi.fn()}
      onReview={vi.fn()}
      onHint={vi.fn()}
      locale="en"
    />,
  );
  expect(screen.getByLabelText("AI Judge Copilot")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Hint 1" })).toBeEnabled();
});
