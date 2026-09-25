import { describe, expect, it } from "vitest";
import { formatINR, formatDate } from "./inr";

describe("formatINR", () => {
  it("uses Indian digit grouping with two decimals", () => {
    expect(formatINR(2138000)).toBe("21,38,000.00");
    expect(formatINR(137850)).toBe("1,37,850.00");
    expect(formatINR(12345678.5)).toBe("1,23,45,678.50");
    expect(formatINR(500)).toBe("500.00");
  });

  it("returns empty string for null", () => {
    expect(formatINR(null)).toBe("");
  });
});

describe("formatDate", () => {
  it("formats ISO dates as DD-MM-YYYY", () => {
    expect(formatDate("2026-05-23")).toBe("23-05-2026");
  });
});
