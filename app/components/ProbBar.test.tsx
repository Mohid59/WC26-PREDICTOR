import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProbBar } from "./ProbBar";

describe("ProbBar", () => {
  it("renders three percentage labels that round-trip to ~100%", () => {
    render(<ProbBar pHome={0.5} pDraw={0.3} pAway={0.2} />);
    expect(screen.getByText("50.0%")).toBeInTheDocument();
    expect(screen.getByText(/30\.0%/)).toBeInTheDocument();
    expect(screen.getByText("20.0%")).toBeInTheDocument();
  });

  it("includes an accessible label summarising probabilities", () => {
    render(<ProbBar pHome={0.55} pDraw={0.2} pAway={0.25} homeLabel="USA" awayLabel="MEX" />);
    expect(screen.getByRole("img", { name: /USA 55\.0%/ })).toBeInTheDocument();
  });

  it("handles edge cases without crashing", () => {
    const { container } = render(<ProbBar pHome={1} pDraw={0} pAway={0} />);
    expect(container.querySelectorAll("div").length).toBeGreaterThan(0);
  });
});
