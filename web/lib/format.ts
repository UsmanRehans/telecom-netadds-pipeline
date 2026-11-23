export function formatK(v: number): string {
  const sign = v < 0 ? "−" : "+";
  const abs = Math.abs(v);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2).replace(/\.?0+$/, "")}M`;
  return `${sign}${Math.round(abs)}K`;
}
