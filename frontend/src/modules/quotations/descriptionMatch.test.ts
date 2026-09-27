import { describe, expect, it } from "vitest";
import { matchParts, sameDescription } from "./descriptionMatch";

describe("matchParts", () => {
  it("splits out the first case-insensitive match", () => {
    expect(matchParts("32 Channel Relay card", "relay")).toEqual([
      { text: "32 Channel ", match: false },
      { text: "Relay", match: true },
      { text: " card", match: false },
    ]);
  });

  it("ignores extra spaces in the query", () => {
    expect(matchParts("Oscilloscope", "  osc ")).toEqual([
      { text: "Osc", match: true },
      { text: "illoscope", match: false },
    ]);
  });

  it("returns the whole text unmatched for an empty or missing query", () => {
    expect(matchParts("Rack", "")).toEqual([{ text: "Rack", match: false }]);
    expect(matchParts("Rack", "zzz")).toEqual([{ text: "Rack", match: false }]);
  });
});

describe("sameDescription", () => {
  it("compares case- and whitespace-insensitively", () => {
    expect(sameDescription(" Oscilloscope", "oscilloscope  ")).toBe(true);
    expect(sameDescription("DMM  6", "dmm 6")).toBe(true);
    expect(sameDescription("Rack", "Racks")).toBe(false);
  });
});
