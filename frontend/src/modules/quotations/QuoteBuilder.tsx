import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Button, ErrorNote, Field, Input, Modal, PageHeader, Panel, Select, Spinner, Textarea, useToast,
} from "../../components/ui";
import { api, ApiError, post, put } from "../../lib/api";
import type { AppSettings, Customer, Quote, QuoteIn } from "../../lib/types";
import CustomerForm from "../customers/CustomerForm";
import ItemsEditor from "./ItemsEditor";
import {
  financialYear, fromApiItems, newRow, subtotal, toApiItems, validateRows, type Row,
} from "./itemsLogic";
import TermsEditor from "./TermsEditor";

type Form = Omit<QuoteIn, "items">;

const today = () => new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });

export default function QuoteBuilder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [form, setForm] = useState<Form | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [loadError, setLoadError] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [suggestedRef, setSuggestedRef] = useState("");
  const [saving, setSaving] = useState(false);
  const [words, setWords] = useState("");
  const [addingCustomer, setAddingCustomer] = useState(false);
  const [refTouched, setRefTouched] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [s, cs] = await Promise.all([
          api<AppSettings>("/api/v1/settings"), api<Customer[]>("/api/v1/customers"),
        ]);
        setSettings(s);
        setCustomers(cs);
        if (id) {
          const q = await api<Quote>(`/api/v1/quotes/${id}`);
          setForm({ ref_no: q.ref_no, customer_id: q.customer_id, kind_attn: q.kind_attn,
            quote_date: q.quote_date, issue_status: q.issue_status, intro: q.intro, terms: q.terms });
          setRows(q.quote_items.length ? fromApiItems(q.quote_items) : [newRow()]);
        } else {
          const { ref_no } = await api<{ ref_no: string }>("/api/v1/quotes/next-ref");
          setForm({ ref_no, customer_id: "", kind_attn: "", quote_date: today(), issue_status: "1.1",
            intro: s.default_intro, terms: s.default_terms });
          setRows([newRow()]);
        }
      } catch (e) {
        setLoadError((e as Error).message);
      }
    })();
  }, [id]);

  const total = subtotal(rows);
  useEffect(() => {
    const t = setTimeout(() => {
      api<{ words: string }>(`/api/v1/quotes/amount-words?amount=${total}`)
        .then((r) => setWords(`INR ${r.words}`)).catch(() => setWords(""));
    }, 300);
    return () => clearTimeout(t);
  }, [total]);

  if (loadError) return <ErrorNote message={loadError} />;
  if (!form || !settings) return <Spinner />;

  const set = <K extends keyof Form>(k: K, v: Form[K]) => setForm({ ...form, [k]: v });

  async function changeDate(quote_date: string) {
    setForm({ ...form!, quote_date });
    const fyChanged = quote_date && !form!.ref_no.endsWith(`/${financialYear(quote_date)}`);
    if (id || refTouched || !fyChanged) return;
    try {
      const { ref_no } = await api<{ ref_no: string }>(`/api/v1/quotes/next-ref?date=${quote_date}`);
      setForm((f) => (f ? { ...f, ref_no } : f));
    } catch {
      /* keep the current ref; saving will report any conflict */
    }
  }

  function pickCustomer(cid: string, list = customers) {
    const prev = list.find((c) => c.id === form!.customer_id);
    const next = list.find((c) => c.id === cid);
    const keepAttn = form!.kind_attn && form!.kind_attn !== prev?.contact_person;
    setForm({ ...form!, customer_id: cid, kind_attn: keepAttn ? form!.kind_attn : next?.contact_person ?? "" });
  }

  async function save() {
    const problems = [
      ...(form!.customer_id ? [] : ["Choose a customer"]),
      ...(form!.ref_no.trim() ? [] : ["Enter a ref no"]),
      ...(rows.length ? [] : ["Add at least one item"]),
      ...validateRows(rows),
    ];
    setErrors(problems);
    setSuggestedRef("");
    if (problems.length) return;
    setSaving(true);
    try {
      const body: QuoteIn = { ...form!, terms: form!.terms.filter((t) => t.trim()), items: toApiItems(rows) };
      const saved = id
        ? await put<Quote>(`/api/v1/quotes/${id}`, body)
        : await post<Quote>("/api/v1/quotes", body);
      toast(`Saved ${saved.ref_no}`);
      navigate(`/quotes/${saved.id}`);
    } catch (e) {
      setErrors([(e as Error).message]);
      if (e instanceof ApiError && e.status === 409) {
        setSuggestedRef((e.detail as { suggested_ref?: string })?.suggested_ref ?? "");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader title={id ? `Edit ${form.ref_no}` : "New quotation"}
        actions={<>
          <Button variant="secondary" onClick={() => navigate(id ? `/quotes/${id}` : "/quotes")}>Cancel</Button>
          <Button onClick={save} busy={saving}>Save and preview</Button>
        </>} />

      <div className="space-y-5">
        <Panel title="Customer and reference">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <Field label="Customer">
                {(fid) => (
                  <div className="flex gap-2">
                    <Select id={fid} value={form.customer_id} onChange={(e) => pickCustomer(e.target.value)}>
                      <option value="">Choose a customer…</option>
                      {customers.map((c) => <option key={c.id} value={c.id}>{c.company_name}</option>)}
                    </Select>
                    <Button type="button" variant="secondary" onClick={() => setAddingCustomer(true)}
                      className="shrink-0">New</Button>
                  </div>
                )}
              </Field>
              <Field label="Kind Attn">
                {(fid) => <Input id={fid} value={form.kind_attn} onChange={(e) => set("kind_attn", e.target.value)}
                  placeholder="Mr. Reegan M" />}
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-3 self-start">
              <Field label="Ref no" className="col-span-2" hint="Suggested automatically. You can change it.">
                {(fid) => <Input id={fid} value={form.ref_no}
                  onChange={(e) => { setRefTouched(true); set("ref_no", e.target.value); }} />}
              </Field>
              <Field label="Date">
                {(fid) => <Input id={fid} type="date" value={form.quote_date}
                  onChange={(e) => changeDate(e.target.value)} />}
              </Field>
              <Field label="Issue status">
                {(fid) => <Input id={fid} value={form.issue_status}
                  onChange={(e) => set("issue_status", e.target.value)} />}
              </Field>
            </div>
            <Field label="Opening lines" className="md:col-span-2"
              hint="Printed above the item table. Leave empty to skip.">
              {(fid) => <Textarea id={fid} rows={2} value={form.intro} onChange={(e) => set("intro", e.target.value)} />}
            </Field>
          </div>
        </Panel>

        <section className="overflow-hidden rounded-lg border border-line bg-white">
          <header className="border-b border-line px-4 py-2.5">
            <h2 className="font-semibold text-navy">Items</h2>
            <p className="text-sm text-muted">Leave qty and price blank for a description-only row.</p>
          </header>
          <ItemsEditor rows={rows} onChange={setRows} words={words} />
        </section>

        <Panel title="Terms and conditions">
          <TermsEditor terms={form.terms} onChange={(t) => set("terms", t)}
            onReset={() => set("terms", settings.default_terms)} />
        </Panel>

        {errors.length > 0 && (
          <div role="alert" className="space-y-1 rounded-md bg-danger-soft px-4 py-3 text-sm text-danger">
            {errors.map((e) => <p key={e}>{e}</p>)}
            {suggestedRef && (
              <Button variant="secondary" className="mt-2"
                onClick={() => { set("ref_no", suggestedRef); setRefTouched(false); setErrors([]); setSuggestedRef(""); }}>
                Use {suggestedRef}
              </Button>
            )}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => navigate(id ? `/quotes/${id}` : "/quotes")}>Cancel</Button>
          <Button onClick={save} busy={saving}>Save and preview</Button>
        </div>
      </div>

      <Modal open={addingCustomer} onClose={() => setAddingCustomer(false)} title="Add customer">
        {addingCustomer && (
          <CustomerForm onCancel={() => setAddingCustomer(false)} onSaved={(c) => {
            const list = [...customers, c].sort((a, b) => a.company_name.localeCompare(b.company_name));
            setCustomers(list);
            pickCustomer(c.id, list);
            setAddingCustomer(false);
          }} />
        )}
      </Modal>
    </>
  );
}
