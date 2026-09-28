import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, EmptyState, ErrorNote, Field, Input, PageHeader, Panel, Select, Textarea, useToast } from "../../components/ui";
import { api, post, uploadFiles } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { formatINR } from "../../lib/inr";
import type { AppUser, ImportReadResult, Quote } from "../../lib/types";
import { draftRows, fileStatus, type FileStatus } from "./importLogic";
import ItemsEditor from "./ItemsEditor";
import { subtotal, toApiItems, validateRows, type Row } from "./itemsLogic";
import TermsEditor from "./TermsEditor";

const ACCEPT = ".pdf,.xlsx,.xls,.docx,.doc";

const STATUS: Record<FileStatus, { label: string; cls: string }> = {
  ready: { label: "Ready to save", cls: "bg-sent-soft text-sent" },
  check: { label: "Needs a look", cls: "bg-draft-soft text-draft" },
  duplicate: { label: "Already in the system", cls: "bg-paper text-muted" },
  error: { label: "Couldn't read", cls: "bg-danger-soft text-danger" },
  saved: { label: "Saved", cls: "bg-sent-soft text-sent" },
};

interface Entry {
  key: string;
  result: ImportReadResult;
  status: FileStatus;
  form: { customer_name: string; kind_attn: string; ref_no: string; quote_date: string; issue_status: string;
    intro: string; terms: string[] };
  rows: Row[];
  errors: string[];
  savedId?: string;
  open: boolean;
}

function toEntry(result: ImportReadResult, n: number): Entry {
  const d = result.draft;
  const status = fileStatus(result);
  return {
    key: `${n}-${result.filename}`, result, status,
    form: {
      customer_name: d?.customer_name ?? "", kind_attn: d?.kind_attn ?? "", ref_no: d?.ref_no ?? "",
      quote_date: d?.quote_date ?? "", issue_status: d?.issue_status || "1.1", intro: d?.intro ?? "", terms: d?.terms ?? [],
    },
    rows: d ? draftRows(d.items) : [],
    errors: [],
    open: status === "check",
  };
}

export default function ImportQuotes() {
  const { isAdmin } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const picker = useRef<HTMLInputElement>(null);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [reading, setReading] = useState(false);
  const [readError, setReadError] = useState("");
  const [owner, setOwner] = useState<{ user_id: string; name: string } | null>(null);
  const [ownerId, setOwnerId] = useState("");
  const [team, setTeam] = useState<AppUser[]>([]);
  const [savingAll, setSavingAll] = useState(false);

  useEffect(() => {
    api<{ user_id: string; name: string }>("/api/v1/quotes/import/owner").then((o) => { setOwner(o); setOwnerId(o.user_id); });
    if (isAdmin) api<AppUser[]>("/api/v1/users").then(setTeam).catch(() => setTeam([]));
  }, [isAdmin]);

  const update = (key: string, patch: Partial<Entry>) =>
    setEntries((list) => list.map((e) => (e.key === key ? { ...e, ...patch } : e)));

  async function pick(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (!files.length) return;
    setReading(true);
    setReadError("");
    try {
      const results = await uploadFiles<ImportReadResult[]>("/api/v1/quotes/import/read", files);
      setEntries((list) => [...list, ...results.map((r, i) => toEntry(r, list.length + i))]);
    } catch (err) {
      setReadError((err as Error).message);
    } finally {
      setReading(false);
    }
  }

  async function save(entry: Entry): Promise<boolean> {
    const f = entry.form;
    const problems = [
      ...(f.customer_name.trim() ? [] : ["Enter the customer name"]),
      ...(f.ref_no.trim() ? [] : ["Enter the ref no"]),
      ...(f.quote_date ? [] : ["Enter the quotation date"]),
      ...(entry.rows.length ? [] : ["Add at least one item"]),
      ...validateRows(entry.rows),
    ];
    if (problems.length) {
      update(entry.key, { errors: problems, open: true });
      return false;
    }
    try {
      const saved = await post<Quote>("/api/v1/quotes/import/save", {
        ...f, terms: f.terms.filter((t) => t.trim()), items: toApiItems(entry.rows),
        owner_id: isAdmin ? ownerId || null : null,
      });
      update(entry.key, { status: "saved", savedId: saved.id, errors: [], open: false });
      return true;
    } catch (err) {
      update(entry.key, { errors: [(err as Error).message], open: true });
      return false;
    }
  }

  async function saveAllReady() {
    setSavingAll(true);
    let done = 0;
    for (const e of entries.filter((x) => x.status === "ready")) {
      if (await save(e)) done++;
    }
    setSavingAll(false);
    toast(`Saved ${done} ${done === 1 ? "quotation" : "quotations"}`);
  }

  const ready = entries.filter((e) => e.status === "ready").length;
  const ownerName = team.find((u) => u.id === ownerId)?.name || team.find((u) => u.id === ownerId)?.email || owner?.name;

  return (
    <>
      <PageHeader title="Upload quotations"
        actions={<>
          <Button variant="secondary" onClick={() => navigate("/quotes")}>Back to quotations</Button>
          <Button busy={reading} onClick={() => picker.current?.click()}>Choose files</Button>
          <input ref={picker} type="file" multiple accept={ACCEPT} className="hidden" onChange={pick}
            aria-label="Quotation files to upload" />
        </>}>
        <p className="text-muted">Bring in existing quotations from PDF, Excel (.xlsx, .xls) or Word (.docx, .doc).
          Check what was read, fix anything highlighted, then save.</p>
      </PageHeader>

      <Panel className="mb-5">
        <div className="flex flex-wrap items-end gap-3">
          {isAdmin && team.length > 0 ? (
            <Field label="Saved as created by" className="w-64">
              {(id) => (
                <Select id={id} value={ownerId} onChange={(e) => setOwnerId(e.target.value)}>
                  {team.map((u) => <option key={u.id} value={u.id}>{u.name || u.email}</option>)}
                </Select>
              )}
            </Field>
          ) : (
            <p>Saved as created by <strong>{ownerName ?? "…"}</strong></p>
          )}
          <p className="text-sm text-muted">Each quotation counts on the dashboard on the date printed on it.</p>
          {ready > 0 && (
            <Button className="ml-auto" busy={savingAll} onClick={saveAllReady}>
              Save {ready} ready {ready === 1 ? "quotation" : "quotations"}
            </Button>
          )}
        </div>
      </Panel>

      {readError && <div className="mb-4"><ErrorNote message={readError} /></div>}
      {!entries.length ? (
        <EmptyState title="No files chosen yet"
          body="Choose one or more quotation files. Up to 20 at a time, 10 MB each."
          action={<Button busy={reading} onClick={() => picker.current?.click()}>Choose files</Button>} />
      ) : (
        <ul className="space-y-3">
          {entries.map((e) => <EntryCard key={e.key} entry={e} onChange={(p) => update(e.key, p)} onSave={() => save(e)} />)}
        </ul>
      )}
    </>
  );
}

function EntryCard({ entry, onChange, onSave }:
  { entry: Entry; onChange: (patch: Partial<Entry>) => void; onSave: () => Promise<boolean> }) {
  const [busy, setBusy] = useState(false);
  const { result, status, form, rows } = entry;
  const d = result.draft;
  const s = STATUS[status];
  const set = (k: keyof Entry["form"], v: string | string[]) => onChange({ form: { ...form, [k]: v } });
  const total = subtotal(rows);
  const mismatch = d?.printed_total != null && Math.abs(d.printed_total - total) > 1;
  const editable = status !== "saved" && status !== "error";

  return (
    <li className="rounded-lg border border-line bg-white">
      <div className="flex flex-wrap items-center gap-3 px-4 py-3">
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${s.cls}`}>{s.label}</span>
        <span className="min-w-0 flex-1">
          <span className="block truncate font-semibold">{form.ref_no || result.filename}</span>
          <span className="block truncate text-sm text-muted">
            {d ? `${form.customer_name || "No customer"}, ₹ ${formatINR(total)}` : result.error}
          </span>
        </span>
        <span className="flex gap-3 text-sm font-medium">
          {status === "saved" && entry.savedId && <Link to={`/quotes/${entry.savedId}`} className="text-navy hover:underline">Open</Link>}
          {editable && <button onClick={() => onChange({ open: !entry.open })} className="text-navy hover:underline">
            {entry.open ? "Hide details" : "Review"}</button>}
          {editable && status !== "duplicate" && (
            <Button className="min-h-8 px-3 text-sm" busy={busy} onClick={async () => { setBusy(true); await onSave(); setBusy(false); }}>
              Save
            </Button>
          )}
        </span>
      </div>

      {entry.open && editable && d && (
        <div className="space-y-4 border-t border-line px-4 py-4">
          <p className="text-sm text-muted">From <strong>{result.filename}</strong>.{" "}
            {result.customer_id ? "The customer is already in your list." : "A new customer will be added."}
            {status === "duplicate" && " A quotation with this ref no is already in the system, so it won't be saved again."}
          </p>
          {d.warnings.length > 0 && (
            <ul className="space-y-1 rounded-md bg-draft-soft px-3 py-2 text-sm text-draft">
              {d.warnings.map((w) => <li key={w}>{w}</li>)}
            </ul>
          )}
          <div className="grid gap-3 md:grid-cols-3">
            <Field label="Customer" className="md:col-span-2">
              {(id) => <Input id={id} value={form.customer_name} onChange={(e) => set("customer_name", e.target.value)} />}
            </Field>
            <Field label="Kind Attn">
              {(id) => <Input id={id} value={form.kind_attn} onChange={(e) => set("kind_attn", e.target.value)} />}
            </Field>
            <Field label="Ref no">
              {(id) => <Input id={id} value={form.ref_no} onChange={(e) => set("ref_no", e.target.value)} />}
            </Field>
            <Field label="Date">
              {(id) => <Input id={id} type="date" value={form.quote_date} onChange={(e) => set("quote_date", e.target.value)} />}
            </Field>
            <Field label="Issue status">
              {(id) => <Input id={id} value={form.issue_status} onChange={(e) => set("issue_status", e.target.value)} />}
            </Field>
            <Field label="Opening lines" className="md:col-span-3">
              {(id) => <Textarea id={id} rows={2} value={form.intro} onChange={(e) => set("intro", e.target.value)} />}
            </Field>
          </div>
          <section className="overflow-hidden rounded-md border border-line">
            <ItemsEditor rows={rows} onChange={(r) => onChange({ rows: r })} words="" />
          </section>
          {d.printed_total != null && (
            <p className={`text-sm ${mismatch ? "font-semibold text-danger" : "text-muted"}`}>
              Total printed on the file: ₹ {formatINR(d.printed_total)}
              {mismatch ? ". The items above add up to a different amount." : ", matches the items."}
            </p>
          )}
          <div>
            <p className="mb-2 text-sm font-medium text-muted">Terms and conditions</p>
            <TermsEditor terms={form.terms} onChange={(t) => set("terms", t)} onReset={() => set("terms", d.terms)} />
          </div>
          {entry.errors.length > 0 && (
            <div role="alert" className="space-y-1 rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">
              {entry.errors.map((m) => <p key={m}>{m}</p>)}
            </div>
          )}
        </div>
      )}
    </li>
  );
}
