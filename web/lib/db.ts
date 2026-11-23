import postgres from "postgres";

// Lazy init so `next build` succeeds before the database env vars exist
// (e.g. the first deploy, before the Supabase integration is provisioned).
let _sql: ReturnType<typeof postgres> | null = null;

export function getSql() {
  const url =
    process.env.DATABASE_URL ??
    process.env.POSTGRES_URL ??
    process.env.SUPABASE_DB_URL;
  if (!url) return null;
  if (!_sql) {
    const local = /@(localhost|127\.0\.0\.1)[:/]/.test(url);
    _sql = postgres(url, {
      ssl: local ? false : "require",
      max: 4,
      idle_timeout: 20,
      prepare: false, // Supabase transaction pooler doesn't support prepared statements
    });
  }
  return _sql;
}
