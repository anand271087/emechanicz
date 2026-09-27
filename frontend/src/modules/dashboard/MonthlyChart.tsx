import { useEffect, useRef, useState } from "react";
import { formatINR } from "../../lib/inr";
import type { DashboardData } from "../../lib/types";

type Month = DashboardData["monthly"][number];

const H = 180;
const PAD = { top: 16, right: 8, bottom: 26, left: 32 };

/** Axis top that is a whole, even number, so the midpoint tick is a whole number of quotations too. */
export function niceMax(n: number): number {
  if (n <= 4) return 4;
  const step = 10 ** Math.floor(Math.log10(n)) / 2;
  const top = Math.ceil(n / step) * step;
  return top % 2 === 0 ? top : top + 1;
}

/** Quotations created per month of the financial year: one series, so one colour and no legend. */
export default function MonthlyChart({ months }: { months: Month[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const [asTable, setAsTable] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(280, e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, [asTable]);
  const max = niceMax(Math.max(...months.map((m) => m.quotations)));
  const slot = (width - PAD.left - PAD.right) / months.length;
  const plotH = H - PAD.top - PAD.bottom;
  const y = (v: number) => PAD.top + plotH - (v / max) * plotH;
  const ticks = [0, max / 2, max];
  const peak = months.reduce((best, m, i) => (m.quotations > months[best].quotations ? i : best), 0);

  return (
    <div>
      <div className="mb-2 flex justify-end">
        <button onClick={() => setAsTable(!asTable)} className="text-sm font-medium text-navy hover:underline">
          {asTable ? "View as chart" : "View as table"}
        </button>
      </div>
      {asTable ? (
        <table className="w-full text-left text-sm">
          <thead className="text-muted"><tr><th className="py-1 font-medium">Month</th>
            <th className="py-1 text-right font-medium">Quotations</th><th className="py-1 text-right font-medium">Value (INR)</th></tr></thead>
          <tbody className="divide-y divide-line">
            {months.map((m) => (
              <tr key={m.month}><td className="py-1.5">{m.label}</td><td className="py-1.5 text-right">{m.quotations}</td>
                <td className="py-1.5 text-right">{formatINR(m.value)}</td></tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div ref={box} className="relative">
          <svg width={width} height={H} viewBox={`0 0 ${width} ${H}`}
            role="img" aria-label={`Quotations per month: ${months.map((m) => `${m.label} ${m.quotations}`).join(", ")}`}>
            {ticks.map((t) => (
              <g key={t}>
                <line x1={PAD.left} x2={width - PAD.right} y1={y(t)} y2={y(t)} stroke="var(--color-line)" strokeWidth={1} />
                <text x={PAD.left - 6} y={y(t) + 4} textAnchor="end" fontSize={11} fill="var(--color-muted)">{t}</text>
              </g>
            ))}
            {months.map((m, i) => {
              const x = PAD.left + i * slot;
              const barW = Math.min(28, slot * 0.5);
              const bx = x + (slot - barW) / 2;
              const top = y(m.quotations);
              const h = PAD.top + plotH - top;
              return (
                <g key={m.month} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
                  onFocus={() => setHover(i)} onBlur={() => setHover(null)} tabIndex={0}
                  aria-label={`${m.label}: ${m.quotations} quotations, ₹${formatINR(m.value)}`}>
                  <rect x={x} y={PAD.top} width={slot} height={plotH} fill="transparent" />
                  {h > 0 && (
                    <path fill="var(--color-navy)" opacity={hover === null || hover === i ? 1 : 0.55}
                      d={`M${bx},${PAD.top + plotH} V${top + 4} q0,-4 4,-4 h${barW - 8} q4,0 4,4 V${PAD.top + plotH} Z`} />
                  )}
                  {i === peak && m.quotations > 0 && hover === null && (
                    <text x={bx + barW / 2} y={top - 6} textAnchor="middle" fontSize={11} fontWeight={600}
                      fill="var(--color-ink)">{m.quotations}</text>
                  )}
                  <text x={x + slot / 2} y={H - 8} textAnchor="middle" fontSize={11} fill="var(--color-muted)">{m.label}</text>
                </g>
              );
            })}
            <line x1={PAD.left} x2={width - PAD.right} y1={PAD.top + plotH} y2={PAD.top + plotH}
              stroke="var(--color-muted)" strokeWidth={1} />
          </svg>
          {hover !== null && (
            <div role="status" className="pointer-events-none absolute top-0 rounded-md border border-line bg-white px-3 py-2
              text-sm shadow-lg" style={{ left: `min(calc(${((PAD.left + hover * slot + slot / 2) / width) * 100}% - 60px), calc(100% - 140px))` }}>
              <p className="font-semibold">{months[hover].label}</p>
              <p>{months[hover].quotations} quotations</p>
              <p className="text-muted">₹ {formatINR(months[hover].value)}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
