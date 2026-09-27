import { describe, expect, it } from "vitest";
import { niceMax } from "./MonthlyChart";

describe("niceMax", () => {
  it("keeps axis ticks at whole numbers of quotations", () => {
    for (const n of [0, 1, 3, 5, 7, 9, 12, 37, 140]) {
      const top = niceMax(n);
      expect(top).toBeGreaterThanOrEqual(n);
      expect(top % 2).toBe(0);
    }
  });

  it("stays close to the data", () => {
    expect(niceMax(5)).toBe(6);
    expect(niceMax(37)).toBe(40);
    expect(niceMax(2)).toBe(4);
  });
});
