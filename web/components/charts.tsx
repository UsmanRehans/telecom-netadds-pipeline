"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type SeriesPoint = {
  label: string;
  att?: number | null;
  verizon?: number | null;
  tmobile?: number | null;
  attBasis?: string;
  verizonBasis?: string;
  tmobileBasis?: string;
};

const SERIES = [
  { key: "att", name: "AT&T", cssVar: "--series-att" },
  { key: "verizon", name: "Verizon", cssVar: "--series-verizon" },
  { key: "tmobile", name: "T-Mobile", cssVar: "--series-tmobile" },
] as const;

export function formatK(v: number): string {
  const sign = v < 0 ? "−" : "+";
  const abs = Math.abs(v);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2).replace(/\.?0+$/, "")}M`;
  return `${sign}${Math.round(abs)}K`;
}

function axisK(v: number): string {
  if (v === 0) return "0";
  const abs = Math.abs(v);
  const s = abs >= 1000 ? `${abs / 1000}M` : `${abs}K`;
  return v < 0 ? `−${s}` : s;
}

function VizTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ dataKey?: string | number; name?: string; value?: number | string; color?: string; payload?: SeriesPoint }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "8px 12px",
        fontSize: 12,
        color: "var(--text-primary)",
        boxShadow: "0 4px 12px rgba(0,0,0,0.12)",
      }}
    >
      <div style={{ color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      {payload.map((p) => {
        if (p.value == null) return null;
        const basis = row?.[`${String(p.dataKey)}Basis` as keyof SeriesPoint];
        return (
          <div key={String(p.dataKey)} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: p.color, display: "inline-block" }} />
            <span style={{ color: "var(--text-secondary)" }}>{p.name}</span>
            <span style={{ marginLeft: "auto", fontVariantNumeric: "tabular-nums" }}>
              {formatK(Number(p.value))}
              {basis === "derived" ? " · derived" : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}

const commonAxisProps = {
  tick: { fill: "var(--text-muted)", fontSize: 11 },
  axisLine: { stroke: "var(--border)" },
  tickLine: false as const,
};

export function NetAddsBarChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barGap={2}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey="label" {...commonAxisProps} interval="preserveStartEnd" />
        <YAxis {...commonAxisProps} tickFormatter={axisK} width={48} />
        <Tooltip content={<VizTooltip />} cursor={{ fill: "var(--surface-2)", opacity: 0.6 }} />
        <Legend
          wrapperStyle={{ fontSize: 12, color: "var(--text-secondary)" }}
          iconType="circle"
          iconSize={8}
        />
        {SERIES.map((s) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.name}
            fill={`var(${s.cssVar})`}
            radius={[4, 4, 0, 0]}
            maxBarSize={18}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CumulativeLineChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 8, right: 56, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey="label" {...commonAxisProps} interval="preserveStartEnd" />
        <YAxis {...commonAxisProps} tickFormatter={axisK} width={48} />
        <Tooltip content={<VizTooltip />} cursor={{ stroke: "var(--border)" }} />
        <Legend
          wrapperStyle={{ fontSize: 12, color: "var(--text-secondary)" }}
          iconType="circle"
          iconSize={8}
        />
        {SERIES.map((s) => (
          <Line
            key={s.key}
            dataKey={s.key}
            name={s.name}
            stroke={`var(${s.cssVar})`}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: "var(--surface-1)", strokeWidth: 2 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
