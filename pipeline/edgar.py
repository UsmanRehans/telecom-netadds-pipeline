"""SEC EDGAR client: filing metadata and primary-document downloads.

Uses the official data.sec.gov submissions API for metadata and the EDGAR
archives for filing documents. Downloads are cached on disk so re-runs only
hit the network for new filings.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import CARRIERS, REQUEST_DELAY_SECONDS, SEC_HEADERS

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


@dataclass(frozen=True)
class Filing:
    carrier_id: str
    form: str            # "10-Q" | "10-K"
    filing_date: str     # YYYY-MM-DD
    period_end: str      # YYYY-MM-DD (reportDate)
    accession_no: str
    url: str             # primary document URL


def _get(url: str) -> requests.Response:
    time.sleep(REQUEST_DELAY_SECONDS)
    resp = requests.get(url, headers=SEC_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def list_filings(carrier_id: str, since: str, forms=("10-Q", "10-K")) -> list[Filing]:
    """Return 10-Q/10-K filings for a carrier with period_end >= `since`."""
    cik = CARRIERS[carrier_id]["cik"]
    data = _get(f"https://data.sec.gov/submissions/CIK{cik}.json").json()
    recent = data["filings"]["recent"]
    filings = []
    for i in range(len(recent["form"])):
        form = recent["form"][i]
        period_end = recent["reportDate"][i]
        if form not in forms or not period_end or period_end < since:
            continue
        accession = recent["accessionNumber"][i]
        doc = recent["primaryDocument"][i]
        url = (
            "https://www.sec.gov/Archives/edgar/data/"
            + cik.lstrip("0")
            + "/"
            + accession.replace("-", "")
            + "/"
            + doc
        )
        filings.append(
            Filing(
                carrier_id=carrier_id,
                form=form,
                filing_date=recent["filingDate"][i],
                period_end=period_end,
                accession_no=accession,
                url=url,
            )
        )
    return filings


def fetch_document(filing: Filing) -> str:
    """Download (or load from cache) the filing's primary HTML document."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{filing.accession_no}.htm"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="ignore")
    html = _get(filing.url).text
    cache_file.write_text(html, encoding="utf-8")
    return html


def dump_filings_index(filings: list[Filing], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([f.__dict__ for f in filings], indent=2))
