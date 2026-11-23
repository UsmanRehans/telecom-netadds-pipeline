# telecom-netadds-pipeline

Automated data pipeline that extracts quarterly subscriber metrics (net adds,
subscriber counts) for **AT&T, Verizon, and T-Mobile** from their SEC EDGAR
10-Q/10-K filings, normalizes them into a clean warehouse schema in
**Supabase Postgres**, and serves a live dashboard on **Vercel**.

```
SEC EDGAR (10-Q / 10-K)
      │  pipeline/edgar.py      filing metadata + cached documents
      ▼
Era-aware extraction          pipeline/extract.py + config.py
      │  regex rules per carrier & reporting era, range-validated
      ▼
Supabase Postgres             db/schema.sql
      │  carriers · filings · metrics  +  v_net_adds / v_quarterly views
      ▼
Next.js dashboard on Vercel   web/
```

## Why it's built this way

- **Era-aware extraction.** Carriers change what they report: T-Mobile switched
  from customer counts to postpaid *accounts* in 2026, Verizon dropped its
  in-period net-additions table the same year, and AT&T removed connected
  devices from its subscriber definition in 2024. Every metric has per-era
  patterns plus a plausible value range, so footnote markers, percent-change
  columns, and segment tables with identical row labels can't produce bogus
  values.
- **Reported first, derived as fallback.** Where a filing states quarterly net
  additions, that number is stored. Where it doesn't (Q4s, Verizon's 2026
  filings), the `v_net_adds` view derives them from quarter-over-quarter
  balance deltas, flags them `derived`, and skips definitional breaks instead
  of producing a fake ±30M quarter.
- **Idempotent loads.** Primary-keyed upserts mean re-running the pipeline
  refreshes rows instead of duplicating them; the weekly GitHub Action is a
  no-op when there are no new filings.
- **Provenance.** Every value carries the URL of the SEC filing it came from,
  and the dashboard links each number back to its source document.

## Pipeline

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Extract only (writes data/processed/metrics.csv — no database needed)
python -m pipeline.run extract

# Extract + load into Postgres (applies db/schema.sql first)
DATABASE_URL=postgres://... python -m pipeline.run load --schema
```

Options: `--since YYYY-MM-DD` (default 2023-12-31), `--carrier att|verizon|tmobile`.

Set `SEC_CONTACT=you@example.com` — the SEC requires automated clients to
declare a contact address in the User-Agent.

## Database

`db/schema.sql` creates three tables (`carriers`, `filings`, `metrics`) and two
views (`v_net_adds`, `v_quarterly`). Values are in thousands. RLS is enabled
with no policies so the tables aren't exposed through Supabase's public REST
API; the dashboard reads server-side over the Postgres connection string.

## Dashboard (`web/`)

Next.js (App Router) + Recharts, deployed on Vercel with hourly ISR. Series
colors are brand-adjacent but validated for colorblind separation, lightness,
and surface contrast in both light and dark mode.

```bash
cd web
npm install
npm run dev   # needs DATABASE_URL (or POSTGRES_URL) in web/.env.local
```

## Scheduled refresh

`.github/workflows/refresh.yml` runs the pipeline weekly (and on demand) using
two repository secrets: `DATABASE_URL` and `SEC_CONTACT`.

## Notes

- Metric definitions differ by carrier and change over time; subscriber totals
  are **not** directly comparable across carriers. The dashboard's methodology
  notes spell out the caveats.
- Figures are as stated in each quarter's own filing; carriers occasionally
  restate prior periods in later filings.
- Not affiliated with AT&T, Verizon, or T-Mobile. All data from public SEC
  filings.
