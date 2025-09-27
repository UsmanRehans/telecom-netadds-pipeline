import requests
import pandas as pd
from src.config import HEADERS, CARRIERS

def get_filings(cik, forms=["10-Q", "10-K"]):
    """Fetch filings metadata for a given CIK"""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    r = requests.get(url, headers=HEADERS)
    data = r.json()

    filings = data["filings"]["recent"]
    df = pd.DataFrame(filings)
    df = df[df["form"].isin(forms)]
    df["filing_url"] = (
        "https://www.sec.gov/Archives/"
        + df["accessionNumber"].str.replace("-", "")
        + "/"
        + df["primaryDocument"]
    )
    return df

if __name__ == "__main__":
    all_filings = []

    for ticker, cik in CARRIERS.items():
        print(f"Fetching filings for {ticker}...")
        df = get_filings(cik)
        df["carrier"] = ticker
        all_filings.append(df)

    result = pd.concat(all_filings)
    result.to_csv("data/carrier_filings.csv", index=False)

    print("✅ Saved filings to data/carrier_filings.csv")
