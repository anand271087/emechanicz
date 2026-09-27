import { describe, expect, it, vi } from "vitest";

vi.mock("../../lib/supabase", () => ({ supabase: {} }));
vi.stubEnv("VITE_API_BASE_URL", "http://api.test");
const { importSummary } = await import("./Items");

describe("importSummary", () => {
  it("lists only the kinds of skipped rows that happened", () => {
    expect(importSummary({ added: 42, already_in_list: 8, repeated_in_file: 0, blank_rows: 1 }))
      .toBe("Added 42 items. Skipped 8 items already in the list, 1 blank row.");
  });

  it("says nothing was skipped when everything was new", () => {
    expect(importSummary({ added: 1, already_in_list: 0, repeated_in_file: 0, blank_rows: 0 })).toBe("Added 1 item.");
  });

  it("reports zero added when the whole file was already in the list", () => {
    expect(importSummary({ added: 0, already_in_list: 3, repeated_in_file: 2, blank_rows: 0 }))
      .toBe("Added 0 items. Skipped 3 items already in the list, 2 repeats in the file.");
  });
});
