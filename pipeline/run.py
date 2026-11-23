"""Pipeline CLI.

    python -m pipeline.run extract            # EDGAR -> data/processed/metrics.csv
    python -m pipeline.run load               # extract + upsert into Postgres
    python -m pipeline.run load --schema      # also (re)apply db/schema.sql first

Options:
    --since YYYY-MM-DD   earliest period_end to include (default 2023-12-31)
    --carrier att|verizon|tmobile  limit to one carrier (repeatable)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from dotenv import load_dotenv

from .config import CARRIERS, DEFAULT_SINCE
from .edgar import dump_filings_index, fetch_document, list_filings
from .extract import MetricRow, extract_filing

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"


def run_extract(since: str, carriers: list[str]) -> tuple[list, list[MetricRow]]:
    all_filings, all_rows = [], []
    for carrier_id in carriers:
        filings = list_filings(carrier_id, since=since)
        print(f"{CARRIERS[carrier_id]['name']}: {len(filings)} filings since {since}")
        for filing in filings:
            html = fetch_document(filing)
            rows = extract_filing(filing, html)
            print(f"  {filing.form} {filing.period_end}: {len(rows)} metrics")
            all_rows.extend(rows)
        all_filings.extend(filings)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    dump_filings_index(all_filings, PROCESSED / "filings.json")
    csv_path = PROCESSED / "metrics.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["carrier_id", "period_end", "metric", "value",
                         "basis", "source_form", "source_url", "accession_no"])
        for r in sorted(all_rows, key=lambda r: (r.carrier_id, r.period_end, r.metric)):
            writer.writerow([r.carrier_id, r.period_end, r.metric, r.value,
                             r.basis, r.source_form, r.source_url, r.accession_no])
    print(f"\nWrote {len(all_rows)} metric rows -> {csv_path}")
    return all_filings, all_rows


def run_load(filings, rows, apply_schema_first: bool) -> None:
    from . import load  # import here so extract-only runs don't need psycopg

    conn = load.get_conn()
    try:
        if apply_schema_first:
            schema_sql = (ROOT / "db" / "schema.sql").read_text()
            load.apply_schema(conn, schema_sql)
            print("Applied db/schema.sql")
        load.upsert_carriers(conn)
        load.upsert_filings(conn, filings)
        n = load.upsert_metrics(conn, rows)
        print(f"Upserted {n} metric rows into Postgres")
    finally:
        conn.close()


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument("command", choices=["extract", "load"])
    parser.add_argument("--since", default=DEFAULT_SINCE)
    parser.add_argument("--carrier", action="append", choices=list(CARRIERS),
                        help="limit to one or more carriers")
    parser.add_argument("--schema", action="store_true",
                        help="apply db/schema.sql before loading")
    args = parser.parse_args()

    carriers = args.carrier or list(CARRIERS)
    filings, rows = run_extract(args.since, carriers)
    if args.command == "load":
        run_load(filings, rows, apply_schema_first=args.schema)


if __name__ == "__main__":
    main()
