import { useState, type FormEvent, type ReactNode } from "react";
import { Button, ErrorNote, Field, Input, PageHeader, Panel, Select, Spinner, Textarea, useToast } from "../../components/ui";
import { api, post, put } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { supabase } from "../../lib/supabase";
import type { AppSettings, AppUser, CompanySettings, QuoteSeq } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";
import TermsEditor from "../quotations/TermsEditor";

export default function Settings() {
  const { isAdmin, email } = useAuth();
  const { data, error, reload } = useLoad(() => api<AppSettings>("/api/v1/settings"), []);

  return (
    <>
      <PageHeader title="Settings"><p className="text-muted">Signed in as {email}</p></PageHeader>
      <div className="space-y-5">
        <ChangePassword />
        {isAdmin && (error ? <ErrorNote message={error} /> : !data ? <Spinner /> : (
          <>
            <CompanyForm initial={data.company} onSaved={reload} />
            <NumberingForm initial={data.quote_seq} onSaved={reload} />
            <DefaultsForm intro={data.default_intro} terms={data.default_terms} onSaved={reload} />
            <Users />
          </>
        ))}
      </div>
    </>
  );
}

function useSave(label: string, onSaved: () => void) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const save = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
      toast(`${label} saved`);
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, save };
}

function FormPanel({ title, onSubmit, busy, error, children, submitLabel }:
  { title: string; onSubmit: () => void; busy: boolean; error: string; children: ReactNode; submitLabel: string }) {
  return (
    <Panel title={title}>
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); onSubmit(); }} className="space-y-3">
        {children}
        {error && <ErrorNote message={error} />}
        <div className="flex justify-end"><Button type="submit" busy={busy}>{submitLabel}</Button></div>
      </form>
    </Panel>
  );
}

function ChangePassword() {
  const toast = useToast();
  const [pw, setPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (pw.length < 8) return setError("Use at least 8 characters.");
    if (pw !== confirmPw) return setError("The two passwords don't match.");
    setBusy(true);
    setError("");
    const { error } = await supabase.auth.updateUser({ password: pw });
    setBusy(false);
    if (error) return setError(error.message);
    setPw("");
    setConfirmPw("");
    toast("Password changed");
  }

  return (
    <FormPanel title="Your password" onSubmit={submit} busy={busy} error={error} submitLabel="Change password">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="New password">
          {(id) => <Input id={id} type="password" autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} />}
        </Field>
        <Field label="Repeat new password">
          {(id) => <Input id={id} type="password" autoComplete="new-password" value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)} />}
        </Field>
      </div>
    </FormPanel>
  );
}

const COMPANY_FIELDS: { key: keyof CompanySettings; label: string; wide?: boolean }[] = [
  { key: "name", label: "Company name" },
  { key: "signatory_name", label: "Signature line (For …)" },
  { key: "footer_address", label: "Footer address", wide: true },
  { key: "phone", label: "Phone numbers" },
  { key: "emails", label: "Emails" },
  { key: "gst_no", label: "GST no" },
  { key: "closing_line", label: "Closing line", wide: true },
  { key: "system_generated_note", label: "Signature note", wide: true },
];

function CompanyForm({ initial, onSaved }: { initial: CompanySettings; onSaved: () => void }) {
  const [form, setForm] = useState(initial);
  const { busy, error, save } = useSave("Company details", onSaved);
  return (
    <FormPanel title="Company details on quotations" busy={busy} error={error} submitLabel="Save company details"
      onSubmit={() => save(() => put("/api/v1/settings/company", { value: form }))}>
      <div className="grid gap-3 sm:grid-cols-2">
        {COMPANY_FIELDS.map((f) => (
          <Field key={f.key} label={f.label} className={f.wide ? "sm:col-span-2" : ""}>
            {(id) => <Input id={id} value={form[f.key]} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />}
          </Field>
        ))}
      </div>
    </FormPanel>
  );
}

function NumberingForm({ initial, onSaved }: { initial: QuoteSeq; onSaved: () => void }) {
  const [form, setForm] = useState(initial);
  const { busy, error, save } = useSave("Numbering", onSaved);
  return (
    <FormPanel title="Quotation numbering" busy={busy} error={error} submitLabel="Save numbering"
      onSubmit={() => save(() => put("/api/v1/settings/quote_seq", { value: form }))}>
      <p className="text-sm text-muted">
        Next suggested ref no: <strong className="text-navy">ETS/{form.prefix}{form.seq + 1}/{form.fy}</strong>.
        Numbering restarts at 1 each April.
      </p>
      <div className="grid grid-cols-3 gap-3">
        <Field label="Prefix">
          {(id) => <Input id={id} value={form.prefix} onChange={(e) => setForm({ ...form, prefix: e.target.value })} />}
        </Field>
        <Field label="Last number used">
          {(id) => <Input id={id} inputMode="numeric" value={form.seq}
            onChange={(e) => setForm({ ...form, seq: Number(e.target.value.replace(/\D/g, "")) || 0 })} />}
        </Field>
        <Field label="Financial year">
          {(id) => <Input id={id} value={form.fy} onChange={(e) => setForm({ ...form, fy: e.target.value })} />}
        </Field>
      </div>
    </FormPanel>
  );
}

function DefaultsForm({ intro, terms, onSaved }: { intro: string; terms: string[]; onSaved: () => void }) {
  const [introText, setIntroText] = useState(intro);
  const [termList, setTermList] = useState(terms);
  const { busy, error, save } = useSave("Defaults", onSaved);
  return (
    <FormPanel title="Defaults for new quotations" busy={busy} error={error} submitLabel="Save defaults"
      onSubmit={() => save(async () => {
        await put("/api/v1/settings/default_intro", { value: introText });
        await put("/api/v1/settings/default_terms", { value: termList.filter((t) => t.trim()) });
      })}>
      <Field label="Opening lines">
        {(id) => <Textarea id={id} rows={2} value={introText} onChange={(e) => setIntroText(e.target.value)} />}
      </Field>
      <p className="text-sm font-medium text-muted">Terms and conditions</p>
      <TermsEditor terms={termList} onChange={setTermList} onReset={() => setTermList(terms)} />
    </FormPanel>
  );
}

function Users() {
  const { data, error, reload } = useLoad(() => api<AppUser[]>("/api/v1/users"), []);
  const [form, setForm] = useState({ email: "", password: "", role: "user" });
  const { busy, error: saveError, save } = useSave("User", () => {
    setForm({ email: "", password: "", role: "user" });
    reload();
  });

  return (
    <Panel title="Team members">
      {error && <ErrorNote message={error} />}
      {!data ? <Spinner /> : (
        <ul className="mb-5 divide-y divide-line rounded-md border border-line">
          {data.map((u) => (
            <li key={u.id} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2.5">
              <span className="font-medium">{u.email}</span>
              <span className="text-sm text-muted">
                {u.role === "admin" ? "Admin" : "Sales"}
                {u.last_sign_in_at ? `, last signed in ${new Date(u.last_sign_in_at).toLocaleDateString("en-IN")}`
                  : ", hasn't signed in yet"}
              </span>
            </li>
          ))}
        </ul>
      )}
      <form className="grid gap-3 sm:grid-cols-[1fr_1fr_9rem_auto] sm:items-end"
        onSubmit={(e) => { e.preventDefault(); save(() => post("/api/v1/users", form)); }}>
        <Field label="Email">
          {(id) => <Input id={id} type="email" required value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />}
        </Field>
        <Field label="Starting password">
          {(id) => <Input id={id} type="text" required minLength={8} value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })} />}
        </Field>
        <Field label="Role">
          {(id) => (
            <Select id={id} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="user">Sales</option>
              <option value="admin">Admin</option>
            </Select>
          )}
        </Field>
        <Button type="submit" busy={busy}>Add member</Button>
      </form>
      {saveError && <div className="mt-3"><ErrorNote message={saveError} /></div>}
      <p className="mt-2 text-sm text-muted">Share the starting password with them; they can change it here after signing in.</p>
    </Panel>
  );
}
