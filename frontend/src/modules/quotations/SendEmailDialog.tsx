import { useEffect, useState } from "react";
import { Button, ErrorNote, Field, Input, Modal, Spinner, Textarea, useToast } from "../../components/ui";
import { api, post } from "../../lib/api";
import type { EmailDraft, Quote } from "../../lib/types";

const splitAddresses = (s: string) => s.split(/[,;\s]+/).map((a) => a.trim()).filter(Boolean);

export default function SendEmailDialog({ quote, open, onClose, onSent }:
  { quote: Quote; open: boolean; onClose: () => void; onSent: () => void }) {
  const toast = useToast();
  const [to, setTo] = useState("");
  const [cc, setCc] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachDocx, setAttachDocx] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError("");
    api<EmailDraft>(`/api/v1/quotes/${quote.id}/email-draft`)
      .then((d) => { setTo(d.to.join(", ")); setCc(d.cc.join(", ")); setSubject(d.subject); setBody(d.body); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [open, quote.id]);

  async function send() {
    const recipients = splitAddresses(to);
    if (!recipients.length) {
      setError("Add at least one recipient email address.");
      return;
    }
    setSending(true);
    setError("");
    try {
      await post(`/api/v1/quotes/${quote.id}/send-email`, {
        to: recipients, cc: splitAddresses(cc), subject, body, attach_docx: attachDocx,
      });
      toast(`Quotation sent to ${recipients.join(", ")}`);
      onSent();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={`Email ${quote.ref_no}`}
      footer={<>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button onClick={send} busy={sending} disabled={loading}>Send quotation</Button>
      </>}>
      {loading ? <Spinner label="Preparing email…" /> : (
        <div className="space-y-3">
          <Field label="To" hint="Separate several addresses with commas.">
            {(id) => <Input id={id} type="text" inputMode="email" value={to} onChange={(e) => setTo(e.target.value)}
              placeholder="buyer@company.com" />}
          </Field>
          <Field label="Cc">
            {(id) => <Input id={id} type="text" inputMode="email" value={cc} onChange={(e) => setCc(e.target.value)} />}
          </Field>
          <Field label="Subject">
            {(id) => <Input id={id} value={subject} onChange={(e) => setSubject(e.target.value)} />}
          </Field>
          <Field label="Message">
            {(id) => <Textarea id={id} rows={8} value={body} onChange={(e) => setBody(e.target.value)} />}
          </Field>
          <p className="text-sm text-muted">The PDF is attached automatically.</p>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={attachDocx} onChange={(e) => setAttachDocx(e.target.checked)}
              className="size-4 accent-navy" />
            Also attach the Word file
          </label>
          {error && <ErrorNote message={error} />}
        </div>
      )}
    </Modal>
  );
}
