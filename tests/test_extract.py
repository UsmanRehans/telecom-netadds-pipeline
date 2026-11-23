"""Extraction rule tests against real table fragments from SEC filings.

Each fragment is verbatim text (post HTML-stripping) from the named filing, so
these tests pin the behavior of the era-aware rules without shipping megabytes
of filing HTML.

Run: python3 -m pytest tests/ -q
"""

import re

import pytest

from pipeline.config import EXTRACTION_RULES, METRICS
from pipeline.extract import parse_number


def run_rules(carrier: str, form: str, text: str) -> dict[str, float]:
    """Mirror extract_filing's matching on a raw text fragment."""
    out: dict[str, float] = {}
    for rule in EXTRACTION_RULES[carrier]:
        if form not in rule["forms"]:
            continue
        window = text
        if "section" in rule:
            m = re.search(rule["section"], text)
            if not m:
                continue
            window = text[m.end() : m.end() + 6000]
        if "section_end" in rule:
            m = re.search(rule["section_end"], window)
            if m:
                window = window[: m.start() + 200]
        bounds = METRICS[rule["metric"]]
        lo, hi = rule.get("lo", bounds["lo"]), rule.get("hi", bounds["hi"])
        for pattern in rule["patterns"]:
            found = None
            for m in re.finditer(pattern, window):
                v = parse_number(m.group(1))
                if lo <= v <= hi:
                    found = v
                    break
            if found is not None:
                out.setdefault(rule["metric"], found)
                break
    return out


def test_parse_number():
    assert parse_number("1,234") == 1234
    assert parse_number("(21)") == -21
    assert parse_number("(1,347)") == -1347


# --- Verizon, 2024/2025 era (10-Q for Q2 2025, filed 2025-07) ---------------
VZ_2025 = (
    "Connections (‘000): (2) Wireless retail 115,189 114,236 953 0.8 "
    "Wireless retail postpaid 94,948 93,960 988 1.1 "
    "Wireless retail core prepaid (3) 19,017 18,702 315 1.7 "
    "Total broadband 10,425 9,530 895 9.4 "
    "Net Additions in Period (‘000): Total wireless retail 112 (552) 664 nm "
    "Wireless retail postpaid 90 72 18 25.0 "
    "Wireless retail postpaid phone (51) (109) 58 53.2 "
    "Wireless retail core prepaid (3) 50 (12) 62 nm"
)


def test_verizon_2025_era():
    got = run_rules("verizon", "10-Q", VZ_2025)
    assert got["subs_total"] == 115189
    assert got["subs_postpaid"] == 94948
    assert got["subs_prepaid"] == 19017  # footnote (3) skipped, not parsed as -3
    assert got["netadds_total"] == 112
    assert got["netadds_postpaid"] == 90
    assert got["netadds_postpaid_phone"] == -51
    assert got["netadds_prepaid"] == 50


# --- Verizon, 2026 era (10-Q for Q3 2026): balances only --------------------
VZ_2026 = (
    "Connections (‘000) (1) : Wireless retail 147,098 146,119 979 0.7 % "
    "Wireless retail postpaid 126,831 125,913 918 0.7 "
    "Wireless retail postpaid phone 94,517 93,246 1,271 1.4 "
    "Wireless retail core prepaid 19,337 19,062 275 1.4 "
    "Wireless retail core prepaid phone 18,603 18,506 97 0.5"
)


def test_verizon_2026_era():
    got = run_rules("verizon", "10-Q", VZ_2026)
    assert got["subs_total"] == 147098
    assert got["subs_postpaid"] == 126831
    assert got["subs_postpaid_phone"] == 94517
    assert got["subs_prepaid"] == 19337
    assert "netadds_total" not in got  # no net-adds table in 2026 filings


# --- AT&T, 2026 era (10-Q for Q3 2026) ---------------------------------------
ATT_2026 = (
    "Wireless September 30, (in 000s) 2026 2025 Percent Change "
    "Retail Wireless Subscribers 1 110,237 108,799 1.3 % "
    "Phone 91,736 90,755 1.1 Postpaid phone 75,283 73,801 2.0 "
    "Prepaid phone 16,453 16,954 (3.0) Other 18,501 18,044 2.5 % "
    "Retail Wireless Net Adds 1, 2 537 161 — % 1,244 744 67.2 % "
    "Phone 358 322 11.2 1,016 993 2.3 "
    "Postpaid phone 379 405 (6.4) 1,105 1,130 (2.2) "
    "Prepaid phone (21) (83) 74.7 (89) (137) 35.0 "
    "Postpaid phone churn 3 0.92 % 0.92 %"
)


def test_att_2026_era():
    got = run_rules("att", "10-Q", ATT_2026)
    assert got["subs_total"] == 110237  # footnote "1" not swallowed into the value
    assert got["subs_postpaid_phone"] == 75283
    assert got["subs_prepaid"] == 16453
    assert got["netadds_total"] == 537  # first numeric column = current quarter
    assert got["netadds_postpaid_phone"] == 379
    assert got["netadds_prepaid"] == -21


# --- AT&T, 2022-2025 era (10-Q for Q2 2024) ----------------------------------
ATT_2024 = (
    "Selected Subscribers and Connections June 30, (in 000s) 2024 2023 "
    "Mobility Subscribers 1 115,474 111,854 "
    "Mobility Net Additions (in 000s) 2024 2023 Change "
    "Postpaid Phone Net Additions 419 326 28.5 % 768 750 2.4 % "
    "Total Phone Net Additions 454 449 1.1 "
    "Postpaid 2 593 464 27.8 982 1,006 (2.4) "
    "Prepaid 82 167 (50.9) 83 207 (59.9) "
    "Reseller 322 432 (25.5) "
    "Mobility Net Subscriber Additions 1 997 1,063 (6.2) %"
)


def test_att_2024_era():
    got = run_rules("att", "10-Q", ATT_2024)
    assert got["subs_total"] == 115474
    assert got["netadds_postpaid_phone"] == 419
    assert got["netadds_postpaid"] == 593
    assert got["netadds_prepaid"] == 82
    assert got["netadds_total"] == 997


# --- AT&T 10-K: annual table; pre-2024 total (incl. connected devices) rejected
ATT_10K_2023 = (
    "Subscribers Percent Change (in 000s) 2023 2022 2021 "
    "Postpaid 87,104 84,700 81,534 2.8 % 3.9 % "
    "Postpaid phone 71,255 69,596 67,260 2.4 3.5 "
    "Prepaid 19,236 19,176 19,028 0.3 0.8 "
    "Reseller 7,468 6,043 6,113 23.6 (1.1) "
    "Connected devices 1 127,724 107,478 95,116 18.8 13.0 "
    "Total Mobility Subscribers 2 241,532 217,397 201,791 11.1 % 7.7 %"
)


def test_att_10k_rejects_connected_devices_total():
    got = run_rules("att", "10-K", ATT_10K_2023)
    assert got["subs_postpaid"] == 87104
    assert got["subs_postpaid_phone"] == 71255
    assert got["subs_prepaid"] == 19236
    assert "subs_total" not in got  # 241M includes connected devices: rejected


# --- T-Mobile, <=2025 era (10-Q for Q2 2024) ---------------------------------
TMUS_2024 = (
    "The following table sets forth the number of ending customers: "
    "As of June 30, Change (in thousands) 2024 2023 # % Customers, end of period "
    "Postpaid phone customers 77,245 74,132 3,113 4 % "
    "Postpaid other customers 23,365 20,954 2,411 12 % "
    "Total postpaid customers 100,610 95,086 5,524 6 % "
    "Prepaid customers (1) 25,283 21,516 3,767 18 % "
    "Total customers 125,893 116,602 9,291 8 % "
    "Net Customer Additions ... (in thousands) 2024 2023 # % Net customer additions "
    "Postpaid phone customers 777 760 17 2 % "
    "Postpaid other customers 561 801 (240) (30) % "
    "Total postpaid customers 1,338 1,561 (223) (14) % "
    "Prepaid customers 179 124 55 44 % "
    "Total net customer additions 1,517 1,685 (168) (10) %"
)


def test_tmobile_2024_era():
    got = run_rules("tmobile", "10-Q", TMUS_2024)
    assert got["subs_total"] == 125893
    assert got["subs_postpaid"] == 100610
    assert got["subs_postpaid_phone"] == 77245
    assert got["subs_prepaid"] == 25283
    assert got["netadds_total"] == 1517
    assert got["netadds_postpaid"] == 1338
    assert got["netadds_postpaid_phone"] == 777
    assert got["netadds_prepaid"] == 179


# --- T-Mobile, 2026 era (10-Q for Q3 2026): accounts only --------------------
TMUS_2026 = (
    "The following table sets forth the number of ending postpaid accounts: "
    "As of September 30, Change (in thousands) 2026 2025 # % "
    "Postpaid accounts (1) (2) (3) (4) (5) 34,974 33,979 995 3 % "
    "Postpaid Net Account Additions The following table sets forth the number of "
    "postpaid net account additions: Three Months Ended September 30, "
    "Postpaid net account additions 274 396 (122) (31) %"
)


def test_tmobile_2026_era():
    got = run_rules("tmobile", "10-Q", TMUS_2026)
    assert got["accounts_postpaid"] == 34974
    assert got["netadds_accounts_postpaid"] == 274
    assert "subs_total" not in got


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
