"""Load normalized metrics into Postgres (Supabase).

Connects with DATABASE_URL (Supabase's pooled Postgres connection string works
as-is) and upserts, so the pipeline is idempotent: re-running a quarter
overwrites the same rows instead of duplicating them.
"""

from __future__ import annotations

import os

import psycopg

from .config import CARRIERS
from .edgar import Filing
from .extract import MetricRow


def get_conn() -> psycopg.Connection:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set. Copy the Supabase Postgres connection "
            "string into .env or the environment before loading."
        )
    return psycopg.connect(url)


def apply_schema(conn: psycopg.Connection, schema_sql: str) -> None:
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


def upsert_carriers(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        for carrier_id, info in CARRIERS.items():
            cur.execute(
                """
                insert into carriers (id, name, cik, brand_color)
                values (%s, %s, %s, %s)
                on conflict (id) do update
                  set name = excluded.name,
                      cik = excluded.cik,
                      brand_color = excluded.brand_color
                """,
                (carrier_id, info["name"], info["cik"], info["brand_color"]),
            )
    conn.commit()


def upsert_filings(conn: psycopg.Connection, filings: list[Filing]) -> None:
    with conn.cursor() as cur:
        for f in filings:
            cur.execute(
                """
                insert into filings (accession_no, carrier_id, form, filing_date, period_end, url)
                values (%s, %s, %s, %s, %s, %s)
                on conflict (accession_no) do update
                  set period_end = excluded.period_end,
                      url = excluded.url
                """,
                (f.accession_no, f.carrier_id, f.form, f.filing_date, f.period_end, f.url),
            )
    conn.commit()


def upsert_metrics(conn: psycopg.Connection, rows: list[MetricRow]) -> int:
    with conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                insert into metrics
                  (carrier_id, period_end, metric, value, basis,
                   source_form, source_url, accession_no, extracted_at)
                values (%s, %s, %s, %s, %s, %s, %s, %s, now())
                on conflict (carrier_id, period_end, metric) do update
                  set value = excluded.value,
                      basis = excluded.basis,
                      source_form = excluded.source_form,
                      source_url = excluded.source_url,
                      accession_no = excluded.accession_no,
                      extracted_at = now()
                """,
                (r.carrier_id, r.period_end, r.metric, r.value, r.basis,
                 r.source_form, r.source_url, r.accession_no),
            )
    conn.commit()
    return len(rows)
