import {
  createContext, useCallback, useContext, useEffect, useId, useRef, useState,
  type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode,
  type SelectHTMLAttributes, type TextareaHTMLAttributes,
} from "react";
import type { QuoteStatus } from "../lib/types";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-navy text-white hover:bg-navy-deep disabled:bg-navy/50",
  secondary: "bg-white text-navy border border-line hover:border-navy/40 hover:bg-fixture-soft",
  ghost: "text-navy hover:bg-fixture-soft",
  danger: "bg-white text-danger border border-danger/30 hover:bg-danger-soft",
};

export function Button({ variant = "primary", busy, className = "", children, ...props }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; busy?: boolean }) {
  return (
    <button
      {...props}
      disabled={props.disabled || busy}
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 text-[15px]
        font-semibold transition-colors disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
    >
      {busy && <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {children}
    </button>
  );
}

const inputCls = `w-full rounded-md border border-line bg-white px-3 py-2 text-[15px] text-ink
  placeholder:text-muted/70 focus:border-navy focus:outline-none focus:ring-2 focus:ring-fixture`;

export function Field({ label, hint, children, className = "" }:
  { label: string; hint?: string; children: (id: string) => ReactNode; className?: string }) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-muted">{label}</label>
      {children(id)}
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export const Input = (props: InputHTMLAttributes<HTMLInputElement>) =>
  <input {...props} className={`${inputCls} ${props.className ?? ""}`} />;

export const Textarea = (props: TextareaHTMLAttributes<HTMLTextAreaElement>) =>
  <textarea {...props} className={`${inputCls} ${props.className ?? ""}`} />;

export const Select = (props: SelectHTMLAttributes<HTMLSelectElement>) =>
  <select {...props} className={`${inputCls} ${props.className ?? ""}`} />;

export function StatusBadge({ status }: { status: QuoteStatus }) {
  const cls = status === "sent" ? "bg-sent-soft text-sent" : "bg-draft-soft text-draft";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      <span className="size-1.5 rounded-full bg-current" />
      {status === "sent" ? "Sent" : "Draft"}
    </span>
  );
}

/** The quote ref styled as an engineering-drawing title block. */
export function RefBlock({ refNo, issue, size = "md" }: { refNo: string; issue?: string; size?: "sm" | "md" }) {
  const text = size === "sm" ? "text-sm" : "text-base";
  return (
    <span className={`inline-flex items-stretch overflow-hidden rounded-[3px] border border-navy/70 ${text}`}>
      <span className="bg-navy px-2 py-0.5 font-semibold tracking-wide text-white">{refNo}</span>
      {issue && <span className="bg-white px-1.5 py-0.5 font-medium text-navy">Rev {issue}</span>}
    </span>
  );
}

export function PageHeader({ title, actions, children }:
  { title: ReactNode; actions?: ReactNode; children?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-2xl font-bold leading-tight text-navy">{title}</h1>
        {children}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Panel({ title, children, className = "", actions }:
  { title?: string; children: ReactNode; className?: string; actions?: ReactNode }) {
  return (
    <section className={`rounded-lg border border-line bg-white ${className}`}>
      {title && (
        <header className="flex items-center justify-between gap-2 border-b border-line px-4 py-2.5">
          <h2 className="font-semibold text-navy">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white px-6 py-12 text-center">
      <p className="text-lg font-semibold text-navy">{title}</p>
      <p className="mx-auto mt-1 max-w-sm text-muted">{body}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-muted" role="status">
      <span className="size-5 animate-spin rounded-full border-2 border-navy border-t-transparent" />
      {label}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return <p role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{message}</p>;
}

export function Modal({ open, onClose, title, children, footer }:
  { open: boolean; onClose: () => void; title: string; children: ReactNode; footer?: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      onClose={onClose}
      className="m-auto w-[min(640px,calc(100vw-1.5rem))] rounded-lg border border-line p-0 text-ink
        shadow-xl backdrop:bg-navy-deep/40 max-sm:mb-0 max-sm:w-full max-sm:max-w-full max-sm:rounded-b-none"
    >
      <header className="flex items-center justify-between border-b border-line px-5 py-3">
        <h2 className="text-lg font-semibold text-navy">{title}</h2>
        <button onClick={onClose} aria-label="Close" className="rounded p-1 text-muted hover:bg-paper">✕</button>
      </header>
      <div className="max-h-[70vh] overflow-y-auto px-5 py-4">{children}</div>
      {footer && <footer className="flex justify-end gap-2 border-t border-line px-5 py-3">{footer}</footer>}
    </dialog>
  );
}

type Toast = { id: number; text: string; tone: "ok" | "error" };
const ToastContext = createContext<(text: string, tone?: Toast["tone"]) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((text: string, tone: Toast["tone"] = "ok") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, text, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), tone === "error" ? 7000 : 3500);
  }, []);
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-20 z-50 flex flex-col
        items-center gap-2 px-4 md:bottom-6 md:items-end">
        {toasts.map((t) => (
          <div key={t.id} className={`pointer-events-auto max-w-md rounded-md px-4 py-2.5 text-sm font-medium
            text-white shadow-lg ${t.tone === "error" ? "bg-danger" : "bg-navy-deep"}`}>
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
