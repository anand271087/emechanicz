import type { ReactNode } from "react";

/** CRM modules shown in the navigation. Add a new module here and give it a route in App.tsx. */
export interface CrmModule {
  path: string;
  label: string;
  icon: ReactNode;
  adminOnly?: boolean;
}

const icon = (d: string) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
    strokeLinejoin="round" className="size-5" aria-hidden="true"><path d={d} /></svg>
);

export const MODULES: CrmModule[] = [
  { path: "/quotes", label: "Quotations",
    icon: icon("M7 3h7l5 5v13H7zM14 3v5h5M10 12h6M10 16h6") },
  { path: "/customers", label: "Customers",
    icon: icon("M4 21V7l8-4 8 4v14M9 21v-6h6v6M9 10h.01M15 10h.01") },
  { path: "/settings", label: "Settings",
    icon: icon("M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z") },
];
