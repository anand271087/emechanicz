import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, EmptyState, ErrorNote, Input, PageHeader, RefBlock, Spinner, StatusBadge, useToast } from "../../components/ui";
import { api, post } from "../../lib/api";
import { formatDate, formatINR } from "../../lib/inr";
import type { Quote, QuoteStatus, QuoteSummary } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";

const FILTERS: { value: "" | QuoteStatus; label: string }[] = [
  { value: "", label: "All" }, { value: "draft", label: "Drafts" }, { value: "sent", label: "Sent" },
];

export default function QuoteList() {
  const navigate = useNavigate();
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"" | QuoteStatus>("");

  useEffect(() => {
    const t = setTimeout(() => setQuery(search), 250);
    return () => clearTimeout(t);
  }, [search]);

  const { data, error, loading } = useLoad(
    () => api<QuoteSummary[]>(`/api/v1/quotes?search=${encodeURIComponent(query)}&status=${status}`),
    [query, status],
  );

  async function duplicate(id: string) {
    try {
      const copy = await post<Quote>(`/api/v1/quotes/${id}/duplicate`);
      toast(`Duplicated as ${copy.ref_no}`);
      navigate(`/quotes/${copy.id}/edit`);
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  return (
    <>
      <PageHeader title="Quotations"
        actions={<Button onClick={() => navigate("/quotes/new")}>New quotation</Button>} />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input type="search" placeholder="Search by ref no or customer" value={search}
          onChange={(e) => setSearch(e.target.value)} className="sm:max-w-sm" aria-label="Search quotations" />
        <div className="flex gap-1 rounded-md border border-line bg-white p-1" role="group" aria-label="Filter by status">
          {FILTERS.map((f) => (
            <button key={f.value} onClick={() => setStatus(f.value)} aria-pressed={status === f.value}
              className={`rounded px-3 py-1.5 text-sm font-medium ${status === f.value
                ? "bg-navy text-white" : "text-muted hover:text-navy"}`}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorNote message={error} />}
      {loading && !data ? <Spinner /> : data && data.length === 0 ? (
        query || status ? (
          <EmptyState title="No matching quotations" body="Try a different ref no or customer name, or clear the filter." />
        ) : (
          <EmptyState title="No quotations yet" body="Create your first quotation. It will appear here with its ref no and status."
            action={<Button onClick={() => navigate("/quotes/new")}>New quotation</Button>} />
        )
      ) : data && (
        <div className="overflow-hidden rounded-lg border border-line bg-white">
          <table className="hidden w-full text-left md:table">
            <thead className="border-b border-line bg-fixture-soft text-sm text-navy">
              <tr>
                <th className="px-4 py-2.5 font-semibold">Ref no</th>
                <th className="px-4 py-2.5 font-semibold">Customer</th>
                <th className="px-4 py-2.5 font-semibold">Date</th>
                <th className="px-4 py-2.5 text-right font-semibold">Total (INR)</th>
                <th className="px-4 py-2.5 font-semibold">Status</th>
                <th className="px-4 py-2.5"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.map((q) => (
                <tr key={q.id} className="hover:bg-paper">
                  <td className="px-4 py-3"><Link to={`/quotes/${q.id}`}><RefBlock refNo={q.ref_no} size="sm" /></Link></td>
                  <td className="px-4 py-3 font-medium">{q.customers?.company_name}</td>
                  <td className="px-4 py-3 text-muted">{formatDate(q.quote_date)}</td>
                  <td className="px-4 py-3 text-right font-semibold">{formatINR(q.subtotal)}</td>
                  <td className="px-4 py-3"><StatusBadge status={q.status} /></td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <Link to={`/quotes/${q.id}`} className="mr-4 font-medium text-navy hover:underline">Open</Link>
                    <button onClick={() => duplicate(q.id)} className="font-medium text-navy hover:underline">Duplicate</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <ul className="divide-y divide-line md:hidden">
            {data.map((q) => (
              <li key={q.id}>
                <Link to={`/quotes/${q.id}`} className="block px-4 py-3 active:bg-paper">
                  <div className="flex items-center justify-between gap-2">
                    <RefBlock refNo={q.ref_no} size="sm" />
                    <StatusBadge status={q.status} />
                  </div>
                  <p className="mt-2 font-semibold">{q.customers?.company_name}</p>
                  <div className="mt-0.5 flex justify-between text-sm text-muted">
                    <span>{formatDate(q.quote_date)}</span>
                    <span className="font-semibold text-ink">₹ {formatINR(q.subtotal)}</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
