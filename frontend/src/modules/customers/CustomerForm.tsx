import { useState, type FormEvent } from "react";
import { Button, ErrorNote, Field, Input, Textarea } from "../../components/ui";
import { post, put } from "../../lib/api";
import type { Customer, CustomerIn } from "../../lib/types";

const EMPTY: CustomerIn = { company_name: "", contact_person: "", email: "", phone: "", address: "", gst_no: "" };

export default function CustomerForm({ customer, onSaved, onCancel }:
  { customer?: Customer; onSaved: (c: Customer) => void; onCancel: () => void }) {
  const [form, setForm] = useState<CustomerIn>(customer ? { ...EMPTY, ...customer } : EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: keyof CustomerIn) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    e.stopPropagation();
    setBusy(true);
    setError("");
    try {
      const body: CustomerIn = {
        company_name: form.company_name, contact_person: form.contact_person, email: form.email,
        phone: form.phone, address: form.address, gst_no: form.gst_no,
      };
      const saved = customer
        ? await put<Customer>(`/api/v1/customers/${customer.id}`, body)
        : await post<Customer>("/api/v1/customers", body);
      onSaved(saved);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
      <Field label="Company name" className="sm:col-span-2">
        {(id) => <Input id={id} required value={form.company_name} onChange={set("company_name")} autoFocus />}
      </Field>
      <Field label="Contact person (Kind Attn)">
        {(id) => <Input id={id} value={form.contact_person} onChange={set("contact_person")} placeholder="Mr. Reegan M" />}
      </Field>
      <Field label="Email">
        {(id) => <Input id={id} type="email" value={form.email} onChange={set("email")} />}
      </Field>
      <Field label="Phone">
        {(id) => <Input id={id} type="tel" value={form.phone} onChange={set("phone")} />}
      </Field>
      <Field label="GST no">
        {(id) => <Input id={id} value={form.gst_no} onChange={set("gst_no")} />}
      </Field>
      <Field label="Address" className="sm:col-span-2">
        {(id) => <Textarea id={id} rows={2} value={form.address} onChange={set("address")} />}
      </Field>
      {error && <div className="sm:col-span-2"><ErrorNote message={error} /></div>}
      <div className="flex justify-end gap-2 sm:col-span-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" busy={busy}>{customer ? "Save customer" : "Add customer"}</Button>
      </div>
    </form>
  );
}
