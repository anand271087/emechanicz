import type { ImportItem, ImportReadResult } from "../../lib/types";
import { newRow, type Row } from "./itemsLogic";

export type FileStatus = "ready" | "check" | "duplicate" | "error" | "saved";

export function fileStatus(r: ImportReadResult): FileStatus {
  if (!r.draft) return "error";
  if (r.already_imported) return "duplicate";
  return r.draft.warnings.length ? "check" : "ready";
}

export const draftRows = (items: ImportItem[]): Row[] =>
  items.map((i) => newRow({
    description: i.description,
    qty: i.qty === null ? "" : String(i.qty),
    unit_price: i.unit_price === null ? "" : String(i.unit_price),
    joinAbove: i.join_above,
  }));
