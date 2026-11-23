import { CumulativeLineChart, NetAddsBarChart } from "@/components/charts";
import { formatK } from "@/lib/format";
import { CARRIER_ORDER, loadDashboard, type Dashboard, type MetricRow } from "@/lib/data";

const METRIC_LABELS: Record<string, string> = {
  subs_total: "Total subscribers",
  subs_postpaid: "Postpaid subscribers",
  subs_postpaid_phone: "Postpaid phone subscribers",
  subs_prepaid: "Prepaid subscribers",
  accounts_postpaid: "Postpaid accounts",
  netadds_total: "Total net additions",
  netadds_postpaid: "Postpaid net additions",
  netadds_postpaid_phone: "Postpaid phone net additions",
  netadds_prepaid: "Prepaid net additions",
  netadds_accounts_postpaid: "Postpaid net account additions",
};

type Carrier = (typeof CARRIER_ORDER)[number];

function labelFor(dash: Dashboard, periodEnd: string) {
  return dash.rows.find((r) => r.period_end === periodEnd)?.label ?? periodEnd;
}

function seriesFor(dash: Dashboard, metric: string) {
  return dash.quarters.map((q) => {
    const point: Record<string, unknown> = { label: labelFor(dash, q) };
    for (const c of CARRIER_ORDER) {
      const row = dash.rows.find(
        (r) => r.period_end === q && r.carrier_id === c && r.metric === metric,
      );
      point[c] = row ? row.value : null;
      point[`${c}Basis`] = row?.basis;
    }
    return point as {
      label: string;
      att: number | null;
      verizon: number | null;
      tmobile: number | null;
    };
  });
}

function cumulativeSeries(dash: Dashboard) {
  const base = seriesFor(dash, "netadds_total");
  const running: Record<Carrier, number> = { att: 0, verizon: 0, tmobile: 0 };
  return base.map((p) => {
    const out: Record<string, unknown> = { label: p.label };
    for (const c of CARRIER_ORDER) {
      const v = p[c];
      if (v != null) running[c] += v;
      out[c] = running[c];
    }
    return out as { label: string; att: number; verizon: number; tmobile: number };
  });
}

function Card({
  title,
  note,
  children,
}: {
  title: string;
  note?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-borderline bg-surface-1 p-5">
      <h2 className="text-sm font-semibold text-ink">{title}</h2>
      {note ? <p className="mb-3 mt-0.5 text-xs text-ink-3">{note}</p> : <div className="mb-3" />}
      {children}
    </section>
  );
}

function KpiTile({
  carrier,
  cssVar,
  label,
  value,
  delta,
}: {
  carrier: string;
  cssVar: string;
  label: string;
  value: number | null;
  delta: number | null;
}) {
  return (
    <div className="rounded-xl border border-borderline bg-surface-1 p-5">
      <div className="flex items-center gap-2">
        <span className="h-2.5 w-2.5 rounded-sm" style={{ background: `var(${cssVar})` }} />
        <span className="text-sm font-medium text-ink-2">{carrier}</span>
      </div>
      <div className="mt-2 text-3xl font-semibold tabular-nums text-ink">
        {value == null ? "—" : formatK(value)}
      </div>
      <div className="mt-1 text-xs text-ink-3">
        {label}
        {delta != null && <span> &middot; {formatK(delta)} vs prior qtr</span>}
      </div>
    </div>
  );
}

function SetupNotice() {
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-borderline bg-surface-1 p-8 text-center">
      <h2 className="text-lg font-semibold">No data yet</h2>
      <p className="mt-2 text-sm text-ink-2">
        The database is not connected or hasn&apos;t been loaded. Provision the Supabase
        integration, then run{" "}
        <code className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-xs">
          python -m pipeline.run load --schema
        </code>{" "}
        from the repository root.
      </p>
    </div>
  );
}

export default async function Page() {
  const dash = await loadDashboard();

  if (!dash || dash.rows.length === 0) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-16">
        <Header updated={null} />
        <div className="mt-12">
          <SetupNotice />
        </div>
      </main>
    );
  }

  const phoneNetAdds = seriesFor(dash, "netadds_postpaid_phone");
  const accountNetAdds = seriesFor(dash, "netadds_accounts_postpaid");
  const cumulative = cumulativeSeries(dash);
  const latest = dash.latestQuarter!;
  const latestLabel = labelFor(dash, latest);

  const kpi = (carrier: Carrier, metric: string) => {
    const pts = seriesFor(dash, metric);
    const value = pts.at(-1)?.[carrier] ?? null;
    const prev = pts.at(-2)?.[carrier] ?? null;
    return { value, delta: value != null && prev != null ? value - prev : null };
  };
  const attKpi = kpi("att", "netadds_postpaid_phone");
  const vzKpi = kpi("verizon", "netadds_postpaid_phone");
  const tmusKpi = kpi("tmobile", "netadds_accounts_postpaid");

  const latestRows = dash.rows
    .filter((r) => r.period_end === latest)
    .sort(
      (a, b) =>
        CARRIER_ORDER.indexOf(a.carrier_id as Carrier) -
          CARRIER_ORDER.indexOf(b.carrier_id as Carrier) ||
        a.metric.localeCompare(b.metric),
    );

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-10">
      <Header updated={latestLabel} />

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <KpiTile
          carrier="AT&T"
          cssVar="--series-att"
          label={`Postpaid phone net adds, ${latestLabel}`}
          {...attKpi}
        />
        <KpiTile
          carrier="Verizon"
          cssVar="--series-verizon"
          label={`Postpaid phone net adds, ${latestLabel}`}
          {...vzKpi}
        />
        <KpiTile
          carrier="T-Mobile"
          cssVar="--series-tmobile"
          label={`Postpaid net account adds, ${latestLabel}`}
          {...tmusKpi}
        />
      </div>

      <div className="mt-6 grid gap-6">
        <Card
          title="Postpaid phone net additions by quarter"
          note="Thousands. The industry's headline competitive metric. T-Mobile stopped reporting phone-level figures in its 2026 10-Qs (gaps shown); Verizon's 2026 figures are derived from balance deltas and flagged in the tooltip."
        >
          <NetAddsBarChart data={phoneNetAdds} />
        </Card>

        <Card
          title="Cumulative total net additions"
          note={`Thousands, cumulative since ${labelFor(dash, dash.quarters[0])}. Reported quarterly figures where available, balance-delta estimates elsewhere; quarters with definitional breaks are excluded rather than guessed.`}
        >
          <CumulativeLineChart data={cumulative} />
        </Card>

        <Card
          title="T-Mobile postpaid net account additions"
          note="Thousands. T-Mobile's primary KPI since 2026; shown separately because it counts accounts, not lines."
        >
          <NetAddsBarChart data={accountNetAdds} series={["tmobile"]} />
        </Card>

        <Card
          title={`Latest quarter detail (${latestLabel})`}
          note="Every reported value links to the SEC filing it was extracted from."
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-borderline text-left text-xs text-ink-3">
                  <th className="py-2 pr-4 font-medium">Carrier</th>
                  <th className="py-2 pr-4 font-medium">Metric</th>
                  <th className="py-2 pr-4 text-right font-medium">Value (000s)</th>
                  <th className="py-2 pr-4 font-medium">Basis</th>
                  <th className="py-2 font-medium">Source</th>
                </tr>
              </thead>
              <tbody>
                {latestRows.map((r: MetricRow) => (
                  <tr key={`${r.carrier_id}-${r.metric}`} className="border-b border-borderline/60">
                    <td className="py-2 pr-4 text-ink-2">{r.carrier_name}</td>
                    <td className="py-2 pr-4">{METRIC_LABELS[r.metric] ?? r.metric}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">
                      {r.value.toLocaleString("en-US")}
                    </td>
                    <td className="py-2 pr-4 text-xs text-ink-3">{r.basis}</td>
                    <td className="py-2 text-xs">
                      {r.source_url ? (
                        <a
                          className="text-ink-2 underline decoration-dotted underline-offset-2 hover:text-ink"
                          href={r.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          SEC filing
                        </a>
                      ) : (
                        <span className="text-ink-3">&mdash;</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <footer className="mt-10 border-t border-borderline pt-6 text-xs leading-relaxed text-ink-3">
        <p>
          <strong className="text-ink-2">Methodology.</strong> Quarterly 10-Q and annual 10-K
          filings are pulled from SEC EDGAR, subscriber tables are parsed with era-aware rules
          (carriers change their reported KPIs over time), every value is range-validated, and
          results are loaded into Supabase Postgres. Where a carrier reports in-period net
          additions, that figure is used; otherwise net adds are derived from quarter-over-quarter
          balance changes and flagged. Derived values can include acquisitions and base
          adjustments. Figures are as stated in each quarter&apos;s own filing (carriers
          occasionally restate prior periods). Definitions differ by carrier &mdash; subscriber
          totals are not directly comparable across carriers.
        </p>
        <p className="mt-2">
          Source code:{" "}
          <a
            className="underline decoration-dotted underline-offset-2"
            href="https://github.com/UsmanRehans/telecom-netadds-pipeline"
          >
            github.com/UsmanRehans/telecom-netadds-pipeline
          </a>
          . Not affiliated with AT&amp;T, Verizon, or T-Mobile. Data from public SEC filings.
        </p>
      </footer>
    </main>
  );
}

function Header({ updated }: { updated: string | null }) {
  return (
    <header>
      <p className="text-xs font-medium uppercase tracking-widest text-ink-3">
        US Wireless &middot; SEC EDGAR pipeline
      </p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight">Telecom Net Adds Dashboard</h1>
      <p className="mt-1 text-sm text-ink-2">
        Quarterly subscriber metrics for AT&amp;T, Verizon, and T-Mobile, extracted from
        10-Q/10-K filings{updated ? ` · through ${updated}` : ""}.
      </p>
    </header>
  );
}
