import { describe, expect, it } from "vitest";
import type { ImportReadResult } from "../../lib/types";
import { draftRows, fileStatus } from "./importLogic";

const draft = {
  customer_name: "Yale", kind_attn: "Mr J", ref_no: "ETS/SS10/26-27", issue_status: "1.1", quote_date: "2026-05-23",
  intro: "", terms: [], printed_total: 100, computed_total: 100, warnings: [],
  items: [{ sl_no: 1, description: "Rack", qty: 1, unit_price: 100, join_above: false },
          { sl_no: 2, description: "Labview", qty: null, unit_price: null, join_above: true }],
};
const result = (over: Partial<ImportReadResult> = {}): ImportReadResult =>
  ({ filename: "q.pdf", draft, error: null, already_imported: false, customer_id: null, ...over });

describe("fileStatus", () => {
  it("is ready when everything was read", () => {
    expect(fileStatus(result())).toBe("ready");
  });

  it("needs a look when the reader raised warnings", () => {
    expect(fileStatus(result({ draft: { ...draft, warnings: ["No date found"] } }))).toBe("check");
  });

  it("marks quotations already in the system", () => {
    expect(fileStatus(result({ already_imported: true }))).toBe("duplicate");
  });

  it("marks unreadable files", () => {
    expect(fileStatus(result({ draft: null, error: "Upload a PDF…" }))).toBe("error");
  });
});

describe("draftRows", () => {
  it("turns read items into editable rows, keeping shared prices", () => {
    const rows = draftRows(draft.items);
    expect(rows.map((r) => [r.description, r.qty, r.unit_price, r.joinAbove])).toEqual([
      ["Rack", "1", "100", false], ["Labview", "", "", true]]);
  });
});
