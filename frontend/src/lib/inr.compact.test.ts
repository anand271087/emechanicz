import { describe, expect, it } from "vitest";
import { compactINR } from "./inr";

describe("compactINR", () => {
  it("uses lakh and crore for large amounts", () => {
    expect(compactINR(1714200)).toBe("₹17.14 L");
    expect(compactINR(100000)).toBe("₹1 L");
    expect(compactINR(23500000)).toBe("₹2.35 Cr");
  });

  it("uses thousands below a lakh", () => {
    expect(compactINR(60000)).toBe("₹60 K");
    expect(compactINR(15500)).toBe("₹15.5 K");
  });

  it("shows small amounts in full", () => {
    expect(compactINR(999)).toBe("₹999");
    expect(compactINR(0)).toBe("₹0");
  });
});
