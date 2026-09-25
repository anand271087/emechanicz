import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, ErrorNote, RefBlock, Spinner, StatusBadge, useToast } from "../../components/ui";
import { api, apiFetch, del, downloadFile, post } from "../../lib/api";
import { formatDate, formatINR } from "../../lib/inr";
import type { Quote } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";
import DocumentFrame from "./DocumentFrame";
import SendEmailDialog from "./SendEmailDialog";

export default function QuotePreview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [emailing, setEmailing] = useState(false);
  const [busy, setBusy] = useState<"" | "pdf" | "docx" | "dup">("");

  const { data, error, loading, reload } = useLoad(async () => {
    const [quote, html] = await Promise.all([
      api<Quote>(`/api/v1/quotes/${id}`),
      apiFetch(`/api/v1/quotes/${id}/html`).then((r) => r.text()),
    ]);
    return { quote, html };
  }, [id]);

  if (error) return <ErrorNote message={error} />;
  if (loading && !data) return <Spinner />;
  if (!data) return null;
  const { quote, html } = data;

  async function download(kind: "pdf" | "docx") {
    setBusy(kind);
    try {
      await downloadFile(`/api/v1/quotes/${id}/${kind}`);
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy("");
    }
  }

  async function duplicate() {
    setBusy("dup");
    try {
      const copy = await post<Quote>(`/api/v1/quotes/${id}/duplicate`);
      toast(`Duplicated as ${copy.ref_no}`);
      navigate(`/quotes/${copy.id}/edit`);
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy("");
    }
  }

  async function remove() {
    if (!confirm(`Delete quotation ${quote.ref_no}? This can't be undone.`)) return;
    try {
      await del(`/api/v1/quotes/${id}`);
      toast(`Deleted ${quote.ref_no}`);
      navigate("/quotes");
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  return (
    <div className="lg:grid lg:grid-cols-[1fr_17rem] lg:gap-6">
      <div className="mb-4 lg:order-2 lg:mb-0">
        <div className="space-y-4 lg:sticky lg:top-8">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <RefBlock refNo={quote.ref_no} issue={quote.issue_status} />
              <StatusBadge status={quote.status} />
            </div>
            <p className="mt-2 text-lg font-semibold text-navy">{quote.customers?.company_name}</p>
            <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 text-sm">
              <dt className="text-muted">Date</dt><dd>{formatDate(quote.quote_date)}</dd>
              <dt className="text-muted">Total</dt><dd className="font-semibold">₹ {formatINR(quote.subtotal)}</dd>
            </dl>
          </div>
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-1">
            <Button onClick={() => setEmailing(true)} className="col-span-2 lg:col-span-1">Email to customer</Button>
            <Button variant="secondary" busy={busy === "pdf"} onClick={() => download("pdf")}>Download PDF</Button>
            <Button variant="secondary" busy={busy === "docx"} onClick={() => download("docx")}>Download Word</Button>
            <Button variant="secondary" onClick={() => navigate(`/quotes/${id}/edit`)}>Edit</Button>
            <Button variant="secondary" busy={busy === "dup"} onClick={duplicate}>Duplicate</Button>
          </div>
          <button onClick={remove} className="text-sm font-medium text-danger hover:underline">Delete quotation</button>
        </div>
      </div>

      <div className="lg:order-1"><DocumentFrame html={html} /></div>

      <SendEmailDialog quote={quote} open={emailing} onClose={() => setEmailing(false)} onSent={reload} />
    </div>
  );
}
