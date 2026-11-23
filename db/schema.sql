-- Telecom net-adds warehouse schema (Supabase Postgres)
-- Idempotent: safe to re-run.

create table if not exists carriers (
  id          text primary key,            -- 'att' | 'verizon' | 'tmobile'
  name        text not null,
  cik         text not null,
  brand_color text
);

create table if not exists filings (
  accession_no text primary key,
  carrier_id   text not null references carriers (id),
  form         text not null,              -- '10-Q' | '10-K'
  filing_date  date not null,
  period_end   date not null,
  url          text not null,
  fetched_at   timestamptz not null default now()
);

create table if not exists metrics (
  carrier_id   text not null references carriers (id),
  period_end   date not null,
  metric       text not null,              -- e.g. 'subs_postpaid_phone', 'netadds_total'
  value        numeric not null,           -- thousands
  basis        text not null default 'reported',   -- 'reported' | 'derived'
  source_form  text,
  source_url   text,
  accession_no text,
  extracted_at timestamptz not null default now(),
  primary key (carrier_id, period_end, metric)
);

create index if not exists metrics_metric_idx on metrics (metric, period_end);

-- The dashboard reads server-side over the Postgres connection string; the
-- tables are not meant to be exposed through Supabase's public REST API.
-- Enabling RLS with no policies blocks anon/authenticated API access.
alter table carriers enable row level security;
alter table filings  enable row level security;
alter table metrics  enable row level security;

-- ---------------------------------------------------------------------------
-- v_net_adds: quarterly net additions.
-- Carriers stopped reporting some in-period net-add tables over time (e.g.
-- Verizon's 2026 10-Qs report only ending balances), and 10-Ks only carry
-- annual figures. Where a reported quarterly number exists we use it;
-- otherwise we derive it as the quarter-over-quarter balance delta and flag
-- basis='derived'. Derived values can include base adjustments such as
-- acquisitions (e.g. T-Mobile + UScellular), so the basis flag is surfaced
-- in the dashboard.
-- ---------------------------------------------------------------------------
create or replace view v_net_adds as
with balances as (
  select
    carrier_id,
    period_end,
    case
      when metric = 'accounts_postpaid' then 'netadds_accounts_postpaid'
      else replace(metric, 'subs_', 'netadds_')
    end as metric,
    value,
    lag(value)      over w as prev_value,
    lag(period_end) over w as prev_period,
    source_url
  from metrics
  where metric like 'subs_%' or metric = 'accounts_postpaid'
  window w as (partition by carrier_id, metric order by period_end)
),
derived as (
  select carrier_id, period_end, metric,
         value - prev_value as value,
         'derived'::text as basis,
         source_url
  from balances
  where prev_value is not null
    and period_end - prev_period between 80 and 100   -- consecutive quarters only
    and abs(value - prev_value) <= 4000               -- skip definitional breaks
),
reported as (
  select carrier_id, period_end, metric, value, basis, source_url
  from metrics
  where metric like 'netadds_%'
)
select * from reported
union all
select d.* from derived d
where not exists (
  select 1 from reported r
  where r.carrier_id = d.carrier_id
    and r.period_end = d.period_end
    and r.metric     = d.metric
);

-- Convenience view for the dashboard: everything joined and labeled.
create or replace view v_quarterly as
select
  m.carrier_id,
  c.name  as carrier_name,
  c.brand_color,
  m.period_end,
  extract(year from m.period_end)::int as year,
  'Q' || extract(quarter from m.period_end)::int as quarter,
  m.metric,
  m.value,
  m.basis,
  m.source_url
from (
  select carrier_id, period_end, metric, value, basis, source_url from metrics
  where metric not like 'netadds_%'
  union all
  select carrier_id, period_end, metric, value, basis, source_url from v_net_adds
) m
join carriers c on c.id = m.carrier_id;
