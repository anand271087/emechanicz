export interface Customer {
  id: string;
  company_name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  gst_no: string;
}

export type CustomerIn = Omit<Customer, "id">;

export interface QuoteItemIn {
  sl_no: number;
  description: string;
  qty: number | null;
  unit_price: number | null;
  group_id: number | null;
}

export interface QuoteItem extends QuoteItemIn {
  id: string;
  total: number | null;
}

export type QuoteStatus = "draft" | "sent";

export interface QuoteIn {
  ref_no: string;
  customer_id: string;
  kind_attn: string;
  quote_date: string;
  issue_status: string;
  intro: string;
  terms: string[];
  items: QuoteItemIn[];
}

export interface Quote extends Omit<QuoteIn, "items"> {
  id: string;
  status: QuoteStatus;
  subtotal: number;
  amount_in_words: string;
  created_at: string;
  updated_at: string;
  customers: Customer | null;
  quote_items: QuoteItem[];
}

export interface QuoteSummary extends Omit<Quote, "customers" | "quote_items"> {
  customers: { company_name: string } | null;
}

export interface CompanySettings {
  name: string;
  signatory_name: string;
  footer_address: string;
  phone: string;
  emails: string;
  gst_no: string;
  closing_line: string;
  system_generated_note: string;
}

export interface QuoteSeq {
  prefix: string;
  fy: string;
  seq: number;
}

export interface AppSettings {
  company: CompanySettings;
  quote_seq: QuoteSeq;
  default_terms: string[];
  default_intro: string;
}

export interface EmailDraft {
  to: string[];
  cc: string[];
  subject: string;
  body: string;
}

export interface AppUser {
  id: string;
  email: string;
  role: "admin" | "user";
  created_at: string | null;
  last_sign_in_at: string | null;
}
