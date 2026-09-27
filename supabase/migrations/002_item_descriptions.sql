-- Saved line-item descriptions for the quotation builder's description dropdown.
-- description_key is the lower-cased, whitespace-collapsed text, so "Oscilloscope" and
-- " oscilloscope " are the same item; the first-seen spelling is kept in description.

create table if not exists item_descriptions (
  id uuid primary key default gen_random_uuid(),
  description text not null,
  description_key text not null unique,
  last_used_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists item_descriptions_last_used_idx on item_descriptions(last_used_at desc);

alter table item_descriptions enable row level security;

-- Load descriptions already used in saved quotations.
insert into item_descriptions (description, description_key, last_used_at)
select distinct on (k) d, k, used
from (
  select trim(qi.description) as d,
         lower(regexp_replace(trim(qi.description), '\s+', ' ', 'g')) as k,
         q.updated_at as used
  from quote_items qi join quotes q on q.id = qi.quote_id
  where trim(qi.description) <> ''
  order by 2, q.updated_at desc
) s
order by k, used desc
on conflict (description_key) do nothing;
