import { Fragment, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { EmptyState, ErrorNote, PageHeader, Panel, RefBlock, Spinner } from "../../components/ui";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { compactINR, formatDate, formatINR } from "../../lib/inr";
import type { DashboardData, DashboardPeriod, DashboardQuote } from "../../lib/types";
import { useLoad } from "../../lib/useLoad";
import MonthlyChart from "./MonthlyChart";

const PERIODS: { value: DashboardPeriod; label: string }[] = [
  { value: "today", label: "Today" }, { value: "30d", label: "Last 30 days" },
  { value: "quarter", label: "This quarter" }, { value: "year", label: "This year" },
];

const istDate = (iso: string) => formatDate(new Date(iso).toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" }));

export default function Dashboard() {
  const { isAdmin } = useAuth();
  const [period, setPeriod] = useState<DashboardPeriod>("30d");
  const [open, setOpen] = useState<string | null>(null);
  const { data, error, loading } = useLoad(() => api<DashboardData>(`/api/v1/dashboard?period=${period}`), [period]);

  if (!isAdmin) return <Navigate to="/quotes" replace />;

  return (
    <>
      <PageHeader title="Dashboard">{data && <p className="text-muted">{data.label}</p>}</PageHeader>

      <div className="mb-5 flex flex-wrap gap-1 rounded-md border border-line bg-white p-1 sm:inline-flex" role="group"
        aria-label="Period">
        {PERIODS.map((p) => (
          <button key={p.value} onClick={() => { setPeriod(p.value); setOpen(null); }} aria-pressed={period === p.value}
            className={`flex-1 rounded px-3 py-1.5 text-sm font-medium sm:flex-none ${period === p.value
              ? "bg-navy text-white" : "text-muted hover:text-navy"}`}>
            {p.label}
          </button>
        ))}
      </div>

      {error && <ErrorNote message={error} />}
      {loading && !data ? <Spinner /> : data && (
        <div className={`space-y-5 transition-opacity ${loading ? "opacity-60" : ""}`}>
          <div className="grid gap-3 sm:grid-cols-3">
            <Stat label="Quotations created" value={String(data.totals.quotations)} />
            <Stat label="Value quoted" value={compactINR(data.totals.value)} detail={`₹ ${formatINR(data.totals.value)}`} />
            <Stat label="Average quotation" value={compactINR(data.totals.average)} detail={`₹ ${formatINR(data.totals.average)}`} />
          </div>

          {data.totals.quotations === 0 ? (
            <EmptyState title="No quotations in this period" body="Pick a longer period, or create a quotation to see it here." />
          ) : (
            <>
              <Panel title="Quotations by team member">
                <div className="-mx-4 -my-4 overflow-x-auto">
                  <table className="w-full min-w-[480px] text-left">
                    <thead className="border-b border-line bg-fixture-soft text-sm text-navy">
                      <tr>
                        <th className="px-4 py-2.5 font-semibold">Team member</th>
                        <th className="px-4 py-2.5 text-right font-semibold">Quotations</th>
                        <th className="px-4 py-2.5 text-right font-semibold">Value (INR)</th>
                        <th className="px-4 py-2.5"><span className="sr-only">Show quotations</span></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {data.by_person.map((p) => {
                        const expanded = open === p.user_id;
                        return (
                          <Fragment key={p.user_id}>
                            <tr className="hover:bg-paper">
                              <td className="px-4 py-3 font-semibold">{p.name}</td>
                              <td className="px-4 py-3 text-right font-semibold">{p.quotations}</td>
                              <td className="px-4 py-3 text-right">{formatINR(p.value)}</td>
                              <td className="px-4 py-3 text-right">
                                <button onClick={() => setOpen(expanded ? null : p.user_id)} aria-expanded={expanded}
                                  className="text-sm font-medium text-navy hover:underline">
                                  {expanded ? "Hide quotations" : "Show quotations"}
                                </button>
                              </td>
                            </tr>
                            {expanded && (
                              <tr className="bg-paper">
                                <td colSpan={4} className="px-4 py-3"><QuoteRows quotes={p.quotes} /></td>
                              </tr>
                            )}
                          </Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Panel>

              <div className="grid gap-5 lg:grid-cols-2">
                <Panel title="Top customers">
                  <ol className="divide-y divide-line">
                    {data.top_customers.map((c) => (
                      <li key={c.name} className="flex items-baseline justify-between gap-3 py-2">
                        <span className="min-w-0">
                          <span className="block truncate font-medium">{c.name}</span>
                          <span className="text-sm text-muted">{c.quotations} {c.quotations === 1 ? "quotation" : "quotations"}</span>
                        </span>
                        <span className="shrink-0 font-semibold">₹ {formatINR(c.value)}</span>
                      </li>
                    ))}
                  </ol>
                </Panel>
                <Panel title="Latest quotations">
                  <QuoteRows quotes={data.recent} showCreator />
                </Panel>
              </div>

              {data.monthly.length > 0 && (
                <Panel title="Quotations per month">
                  <MonthlyChart months={data.monthly} />
                </Panel>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
}

function Stat({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-lg border border-line bg-white px-4 py-3">
      <p className="text-sm text-muted">{label}</p>
      <p className="text-3xl font-bold text-navy">{value}</p>
      {detail && <p className="text-sm text-muted">{detail}</p>}
    </div>
  );
}

function QuoteRows({ quotes, showCreator }: { quotes: DashboardQuote[]; showCreator?: boolean }) {
  return (
    <ul className="divide-y divide-line">
      {quotes.map((q) => (
        <li key={q.id}>
          <Link to={`/quotes/${q.id}`} className="block py-2 hover:bg-white/60">
            <span className="flex min-w-0 items-center gap-2">
              <RefBlock refNo={q.ref_no} size="sm" />
              <span className="truncate">{q.customer}</span>
            </span>
            <span className="mt-1 flex items-baseline justify-between gap-3 text-sm">
              <span className="text-muted">{showCreator ? `${q.created_by_name}, ` : ""}{istDate(q.created_at)}</span>
              <span className="font-semibold">₹ {formatINR(q.value)}</span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
