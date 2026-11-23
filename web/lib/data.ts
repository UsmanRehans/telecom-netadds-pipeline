import { cacheLife } from "next/cache";

import { getSql } from "./db";

export type MetricRow = {
  carrier_id: string;
  carrier_name: string;
  period_end: string; // YYYY-MM-DD
  label: string; // "2026 Q3"
  metric: string;
  value: number;
  basis: "reported" | "derived";
  source_url: string | null;
};

export type Dashboard = {
  rows: MetricRow[];
  carriers: { id: string; name: string }[];
  quarters: string[]; // ordered period_end values
  latestQuarter: string | null;
  updatedAt: string;
};

export const CARRIER_ORDER = ["att", "verizon", "tmobile"] as const;

export async function loadDashboard(): Promise<Dashboard | null> {
  "use cache";
  cacheLife("hours");
  const sql = getSql();
  if (!sql) return null;
  try {
    const raw = await sql<
      {
        carrier_id: string;
        carrier_name: string;
        period_end: string;
        year: number;
        quarter: string;
        metric: string;
        value: string;
        basis: "reported" | "derived";
        source_url: string | null;
      }[]
    >`
      select carrier_id, carrier_name,
             to_char(period_end, 'YYYY-MM-DD') as period_end,
             year, quarter, metric, value, basis, source_url
      from v_quarterly
      order by period_end, carrier_id, metric
    `;
    const rows: MetricRow[] = raw.map((r) => ({
      carrier_id: r.carrier_id,
      carrier_name: r.carrier_name,
      period_end: r.period_end,
      label: `${r.year} ${r.quarter}`,
      metric: r.metric,
      value: Number(r.value),
      basis: r.basis,
      source_url: r.source_url,
    }));
    const quarters = [...new Set(rows.map((r) => r.period_end))].sort();
    const carriers = CARRIER_ORDER.map((id) => ({
      id,
      name: rows.find((r) => r.carrier_id === id)?.carrier_name ?? id,
    }));
    return {
      rows,
      carriers,
      quarters,
      latestQuarter: quarters.at(-1) ?? null,
      updatedAt: new Date().toISOString(),
    };
  } catch (err) {
    console.error("dashboard query failed:", err);
    return null;
  }
}
