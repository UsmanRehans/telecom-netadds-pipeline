import pandas as pd
from src.ingest_filings import get_filings
from src.config import CARRIERS

def test_ingest():
    cik = CARRIERS["T"]
    df = get_filings(cik)
    assert not df.empty, "Ingest returned an empty DataFrame"
    assert "filing_url" in df.columns, "Missing filing_url column"
