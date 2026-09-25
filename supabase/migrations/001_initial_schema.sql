-- eMechanicz CRM: initial schema (quotations module)
-- Apply in Supabase Dashboard > SQL Editor > New query > paste > Run.

create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  company_name text not null,
  contact_person text not null default '',
  email text not null default '',
  phone text not null default '',
  address text not null default '',
  gst_no text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists quotes (
  id uuid primary key default gen_random_uuid(),
  ref_no text not null unique,
  customer_id uuid not null references customers(id),
  kind_attn text not null default '',
  quote_date date not null default current_date,
  issue_status text not null default '1.1',
  intro text not null default '',
  status text not null default 'draft' check (status in ('draft', 'sent')),
  subtotal numeric(14,2) not null default 0,
  amount_in_words text not null default '',
  terms jsonb not null default '[]',
  created_by uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists quotes_customer_idx on quotes(customer_id);
create index if not exists quotes_created_idx on quotes(created_at desc);

create table if not exists quote_items (
  id uuid primary key default gen_random_uuid(),
  quote_id uuid not null references quotes(id) on delete cascade,
  sl_no int not null,
  description text not null,
  qty numeric(10,2),
  unit_price numeric(14,2),
  total numeric(14,2),
  group_id int
);

create index if not exists quote_items_quote_idx on quote_items(quote_id);

create table if not exists app_settings (
  key text primary key,
  value jsonb not null
);

-- RLS on with no policies: the anon key can only authenticate; all data
-- access goes through the backend using the service-role key.
alter table customers enable row level security;
alter table quotes enable row level security;
alter table quote_items enable row level security;
alter table app_settings enable row level security;

insert into app_settings (key, value) values
 ('company', '{
    "name": "Emechanicz Test Solutions Pvt Ltd",
    "signatory_name": "EMechanicZ Test Solution Pvt ltd",
    "footer_address": "1st Floor, 1st Cross Adj to SBI ATM, Kodanda Rama Reddy Lyt, Ramamurthy Nagar, Bengaluru – 560016,",
    "phone": "+91 9844561185, 9980592929",
    "emails": "Sales@emechanicz.com ; Service@emechanicz.com",
    "gst_no": "29AADCE7362F1ZI",
    "closing_line": "Thanking you and assuring you of our best services at all the times.",
    "system_generated_note": "This is System generated document hence signature not required."
  }'),
 ('quote_seq', '{"prefix": "P", "fy": "26-27", "seq": 301}'),
 ('default_intro', '"Dear Sir,\nFurther to your enquiry, please find the quote below"'),
 ('default_terms', '[
    "Delivery: 3-4 Weeks from the date of PO & Confirmation",
    "Payment Terms: Net 30 Days",
    "Carriage: Delivery to - At Customer site",
    "Mode of Payment: Through ECS Transfer/Cheque",
    "Order to be placed on:\nEmechanicz Test Solutions Pvt Ltd ,\nNo.190/3,Kalkere Village ,Horamavu Post,Bangalore 560016.",
    "GST @ 18% or actuals extra (GST No. : 29AADCE7362F1ZI)",
    "Validity of quotation: 30 Days from the date of proposal."
  ]')
on conflict (key) do nothing;
