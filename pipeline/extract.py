"""Extract subscriber metrics from filing HTML.

The filings are inline-XBRL HTML documents. We strip them to plain text and
run the era-aware rules from config.EXTRACTION_RULES. Every captured value is
range-checked, which is what disambiguates identical row labels appearing in
both balance and net-additions tables, and rejects footnote markers and
percent-change columns.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from .config import EXTRACTION_RULES, METRICS
from .edgar import Filing

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


@dataclass(frozen=True)
class MetricRow:
    carrier_id: str
    period_end: str      # YYYY-MM-DD
    metric: str          # slug from METRICS
    value: float         # thousands
    basis: str           # "reported"
    source_form: str
    source_url: str
    accession_no: str


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    # Drop the hidden inline-XBRL header so tag soup doesn't pollute the text.
    for tag in soup.find_all(["ix:header", "script", "style"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def parse_number(token: str) -> float:
    token = token.strip()
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()").replace(",", "")
    value = float(token)
    return -value if negative else value


def _section_slice(text: str, rule: dict) -> str:
    start = 0
    if "section" in rule:
        m = re.search(rule["section"], text)
        if not m:
            return ""
        start = m.end()
    window = text[start : start + 6000]
    if "section_end" in rule:
        m = re.search(rule["section_end"], window)
        if m:
            window = window[: m.start() + 200]
    return window


def extract_filing(filing: Filing, html: str) -> list[MetricRow]:
    text = html_to_text(html)
    rows: list[MetricRow] = []
    for rule in EXTRACTION_RULES[filing.carrier_id]:
        if filing.form not in rule["forms"]:
            continue
        window = _section_slice(text, rule) if ("section" in rule or "section_end" in rule) else text
        if not window:
            continue
        bounds = METRICS[rule["metric"]]
        lo = rule.get("lo", bounds["lo"])
        hi = rule.get("hi", bounds["hi"])
        value = None
        for pattern in rule["patterns"]:
            for m in re.finditer(pattern, window):
                candidate = parse_number(m.group(1))
                if lo <= candidate <= hi:
                    value = candidate
                    break
            if value is not None:
                break
        if value is None:
            continue
        rows.append(
            MetricRow(
                carrier_id=filing.carrier_id,
                period_end=filing.period_end,
                metric=rule["metric"],
                value=value,
                basis="reported",
                source_form=filing.form,
                source_url=filing.url,
                accession_no=filing.accession_no,
            )
        )
    return rows
