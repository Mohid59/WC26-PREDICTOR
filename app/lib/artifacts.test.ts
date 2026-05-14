import { describe, it, expect } from "vitest";
import { pct, teamNameMap } from "./artifacts";

describe("pct", () => {
  it("formats fraction as one-decimal percent", () => {
    expect(pct(0.5)).toBe("50.0%");
    expect(pct(0)).toBe("0.0%");
    expect(pct(1)).toBe("100.0%");
  });
});

describe("teamNameMap", () => {
  it("builds a code->name map", () => {
    const m = teamNameMap([
      { code: "USA", name: "United States", confederation: "CONCACAF", pot: 1, is_host: true, elo_seed: 1800 },
      { code: "MEX", name: "Mexico", confederation: "CONCACAF", pot: 1, is_host: true, elo_seed: 1800 },
    ]);
    expect(m["USA"]).toBe("United States");
    expect(m["MEX"]).toBe("Mexico");
  });
  it("returns empty map for undefined input", () => {
    expect(teamNameMap(undefined)).toEqual({});
  });
});
