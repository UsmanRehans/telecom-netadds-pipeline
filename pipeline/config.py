"""Pipeline configuration: carriers, extraction rules, and SEC request settings.

Extraction rules are era-aware: carriers change the wording of their operating
tables over time (e.g. T-Mobile switched from customer counts to account counts
in 2026), so each metric carries a list of candidate patterns plus a plausible
value range. A regex match only counts if the captured value falls inside the
range, which disambiguates identical row labels that appear in both the
balance table and the net-additions table of the same filing.
"""

import os

# ---------------------------------------------------------------------------
# SEC EDGAR request settings
# ---------------------------------------------------------------------------
# The SEC requires automated clients to declare a contact in the User-Agent.
# Set SEC_CONTACT to your own contact address before running at any volume:
# https://www.sec.gov/os/webmaster-faq#developers
SEC_CONTACT = os.getenv("SEC_CONTACT", "contact@example.com")
SEC_USER_AGENT = f"telecom-netadds-pipeline/2.0 ({SEC_CONTACT})"
SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}
# Be polite: EDGAR allows 10 req/s; we stay well under it.
REQUEST_DELAY_SECONDS = 0.4

# ---------------------------------------------------------------------------
# Carriers
# ---------------------------------------------------------------------------
CARRIERS = {
    "att": {
        "name": "AT&T",
        "cik": "0000732717",
        "brand_color": "#00A8E0",
    },
    "verizon": {
        "name": "Verizon",
        "cik": "0000732712",
        "brand_color": "#EE0000",
    },
    "tmobile": {
        "name": "T-Mobile",
        "cik": "0001283699",
        "brand_color": "#E20074",
    },
}

# Earliest period we attempt to extract. All three carriers' recent EDGAR
# submission lists cover this window, and the extraction rules below have been
# verified against both reporting eras inside it.
DEFAULT_SINCE = "2023-12-31"

# ---------------------------------------------------------------------------
# Metric catalog
# ---------------------------------------------------------------------------
# All values are reported in thousands. Ranges are deliberately generous
# sanity bounds, not forecasts; they exist to reject footnote markers,
# percent-change columns, and segment tables that reuse the same row labels.
METRICS = {
    "subs_total":          {"label": "Total subscribers",            "lo": 50_000, "hi": 250_000},
    "subs_postpaid":       {"label": "Postpaid subscribers",         "lo": 50_000, "hi": 180_000},
    "subs_postpaid_phone": {"label": "Postpaid phone subscribers",   "lo": 40_000, "hi": 130_000},
    "subs_prepaid":        {"label": "Prepaid subscribers",          "lo": 5_000,  "hi": 40_000},
    "accounts_postpaid":   {"label": "Postpaid accounts",            "lo": 15_000, "hi": 60_000},
    "netadds_total":           {"label": "Total net additions",          "lo": -4_000, "hi": 4_000},
    "netadds_postpaid":        {"label": "Postpaid net additions",       "lo": -4_000, "hi": 4_000},
    "netadds_postpaid_phone":  {"label": "Postpaid phone net additions", "lo": -3_000, "hi": 3_000},
    "netadds_prepaid":         {"label": "Prepaid net additions",        "lo": -3_000, "hi": 3_000},
    "netadds_accounts_postpaid": {"label": "Postpaid net account additions", "lo": -2_000, "hi": 2_000},
}

# ---------------------------------------------------------------------------
# Extraction rules
# ---------------------------------------------------------------------------
# Each rule:
#   metric   - slug from METRICS
#   section  - optional regex; search is restricted to the window after the
#              FIRST occurrence of this marker (and the window can be capped
#              by section_end). Used when the same row label appears in more
#              than one table.
#   patterns - regexes tried in order; group 1 captures the value. The first
#              match whose parsed value is inside the metric's range wins.
#   forms    - which filings the rule applies to. Balance metrics are valid in
#              both 10-Qs and 10-Ks (period-end values); in-period net adds
#              are only taken from 10-Qs, where the first numeric column is
#              the current quarter. Annual net adds in 10-Ks are skipped and
#              derived later from balance deltas instead.
#
# NUM matches an integer with thousands separators, optionally parenthesized
# (negative). Decimals (churn rates, ARPA) never match.
NUM = r"\(?\d{1,3}(?:,\d{3})*\)?"
# A value that must contain a thousands separator (used where single footnote
# digits sit between the label and the number).
BIGNUM = r"\d{1,3}(?:,\d{3})+"
# AT&T footnote markers between label and value: "1" or "1, 2".
ATT_FN = r"(?:\s*\d(?:\s*,\s*\d)?)?"
# Verizon footnote marker "(3)" between label and value; only treated as a
# footnote when another number follows it.
VZ_FN = r"(?:\(\d\)\s*(?=[\d(]))?"

EXTRACTION_RULES = {
    "verizon": [
        # --- ending balances (Connections table; consolidated table comes first) ---
        # 2023-2025 era: "Total wireless retail 114,236"; the 2025+ filings use
        # a bare "Wireless retail 115,189" row at the top of the table.
        {"metric": "subs_total", "section": r"Connections \(.{0,4}000\)",
         "patterns": [rf"Total wireless retail\s+({NUM})",
                      rf"Wireless retail\s+({NUM})"],
         "forms": ("10-Q", "10-K")},
        {"metric": "subs_postpaid", "section": r"Connections \(.{0,4}000\)",
         "patterns": [rf"Wireless retail postpaid\s+(?!phone)({NUM})"],
         "forms": ("10-Q", "10-K")},
        {"metric": "subs_postpaid_phone", "section": r"Connections \(.{0,4}000\)",
         "patterns": [rf"Wireless retail postpaid phone\s+({NUM})"],
         "forms": ("10-Q", "10-K")},
        {"metric": "subs_prepaid", "section": r"Connections \(.{0,4}000\)",
         "patterns": [rf"Wireless retail (?:core )?prepaid\s*{VZ_FN}(?![Pp]hone)({NUM})"],
         "forms": ("10-Q", "10-K")},
        # --- reported quarterly net additions (2023-2025 era; absent in 2026 filings) ---
        {"metric": "netadds_total", "section": r"Net Additions in Period",
         "patterns": [rf"Total wireless retail\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_postpaid", "section": r"Net Additions in Period",
         "patterns": [rf"Wireless retail postpaid\s+(?!phone)({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_postpaid_phone", "section": r"Net Additions in Period",
         "patterns": [rf"Wireless retail postpaid phone\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_prepaid", "section": r"Net Additions in Period",
         "patterns": [rf"Wireless retail (?:core )?prepaid\s*{VZ_FN}(?![Pp]hone)({NUM})"],
         "forms": ("10-Q",)},
    ],
    "att": [
        # --- ending balances, 10-Qs ---
        # 2026 era: "Retail Wireless Subscribers 1 110,237 ..." (footnote
        # markers like "1" or "1, 2" may sit between label and value).
        # 2022-2025 era: "Mobility Subscribers 1 115,474 ..." — capped at
        # 160M so the pre-2024 definition that counted connected devices
        # ("Total Mobility Subscribers 241,532") is rejected rather than mixed
        # into the series.
        {"metric": "subs_total", "hi": 160_000,
         "patterns": [rf"Retail Wireless Subscribers{ATT_FN}\s+({BIGNUM})",
                      rf"Mobility Subscribers{ATT_FN}\s+({BIGNUM})"],
         "forms": ("10-Q",)},
        {"metric": "subs_postpaid_phone", "section": r"Retail Wireless Subscribers",
         "section_end": r"Net Adds",
         "patterns": [rf"Postpaid phone\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "subs_prepaid", "section": r"Retail Wireless Subscribers",
         "section_end": r"Net Adds",
         "patterns": [rf"Prepaid phone\s+({NUM})"],
         "forms": ("10-Q",)},
        # --- ending balances, 10-Ks ("Subscribers Percent Change" table,
        # first numeric column = current year end) ---
        {"metric": "subs_total", "section": r"Subscribers Percent Change", "hi": 160_000,
         "patterns": [rf"Total Mobility Subscribers{ATT_FN}\s+({BIGNUM})"],
         "forms": ("10-K",)},
        {"metric": "subs_postpaid", "section": r"Subscribers Percent Change",
         "patterns": [rf"Postpaid\s+(?![Pp]hone)({NUM})"],
         "forms": ("10-K",)},
        {"metric": "subs_postpaid_phone", "section": r"Subscribers Percent Change",
         "patterns": [rf"Postpaid phone\s+({NUM})"],
         "forms": ("10-K",)},
        {"metric": "subs_prepaid", "section": r"Subscribers Percent Change",
         "patterns": [rf"Prepaid\s+({NUM})"],
         "forms": ("10-K",)},
        # --- reported quarterly net additions ---
        # 2026 era rows live under "Retail Wireless Net Adds"; earlier era rows
        # are uniquely labeled ("Postpaid Phone Net Additions 419 ...").
        {"metric": "netadds_total",
         "patterns": [rf"Retail Wireless Net Adds{ATT_FN}\s+({NUM})",
                      rf"Mobility Net Subscriber Additions{ATT_FN}\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_postpaid",
         "section": r"(?:Retail Wireless Net Adds|Net Additions)",
         "patterns": [rf"Postpaid{ATT_FN}\s+(?![Pp]hone)({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_postpaid_phone",
         "section": r"(?:Retail Wireless Net Adds|Net Additions)",
         "patterns": [rf"Postpaid [Pp]hone(?: Net Additions)?\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_prepaid",
         "section": r"(?:Retail Wireless Net Adds|Net Additions)",
         "patterns": [rf"Prepaid(?: [Pp]hone)?\s+({NUM})"],
         "forms": ("10-Q",)},
    ],
    "tmobile": [
        # --- ending balances ---
        # <=2025 era: customer counts; 2026 era: postpaid accounts only.
        {"metric": "subs_total", "section": r"ending customers",
         "patterns": [rf"Total customers\s+({NUM})"],
         "forms": ("10-Q", "10-K")},
        {"metric": "subs_postpaid", "section": r"ending customers",
         "patterns": [rf"Total postpaid customers\s+({NUM})"],
         "forms": ("10-Q", "10-K")},
        {"metric": "subs_postpaid_phone", "section": r"ending customers",
         "patterns": [rf"Postpaid phone customers\s*(?:\(\d\)\s*)*({NUM})"],
         "forms": ("10-Q", "10-K")},
        {"metric": "subs_prepaid", "section": r"ending customers",
         "patterns": [rf"Prepaid customers\s*(?:\(\d\)\s*)*({NUM})"],
         "forms": ("10-Q", "10-K")},
        {"metric": "accounts_postpaid", "section": r"ending postpaid accounts",
         "patterns": [rf"Postpaid accounts\s*(?:\(\d\)\s*)*({NUM})"],
         "forms": ("10-Q", "10-K")},
        # --- reported quarterly net additions ---
        {"metric": "netadds_total", "section": r"Net Customer Additions",
         "patterns": [rf"Total net customer additions\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_postpaid", "section": r"Net Customer Additions",
         "patterns": [rf"Total postpaid customers\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_postpaid_phone", "section": r"Net Customer Additions",
         "patterns": [rf"Postpaid phone customers\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_prepaid", "section": r"Net Customer Additions",
         "patterns": [rf"Prepaid customers\s+({NUM})"],
         "forms": ("10-Q",)},
        {"metric": "netadds_accounts_postpaid",
         "patterns": [rf"Postpaid net account additions\s+({NUM})"],
         "forms": ("10-Q",)},
    ],
}
