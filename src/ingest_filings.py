import requests
import pandas as pd
from config import HEADERS, CARRIERS


def get_filings(cik, forms=["10-Q", "10-K"]):
    """Fetch filings metadata for a given CIK"""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()

    filings = data["filings"]["recent"]
    df = pd.DataFrame(filings)
    df = df[df["form"].isin(forms)]

    # Fix filing URL (must include edgar/data/{CIK}/)
    df["filing_url"] = (
        "https://www.sec.gov/Archives/edgar/data/"
        + cik.lstrip("0")  # remove left zeros from CIK for correct path
        + "/"
        + df["accessionNumber"].str.replace("-", "", regex=False)
        + "/"
        + df["primaryDocument"]
    )
    return df


if __name__ == "__main__":
    all_filings = []

    for carrier_name, cik in CARRIERS.items():
        print(f"Fetching filings for {carrier_name}...")
        df = get_filings(cik)
        df["carrier_name"] = carrier_name
        all_filings.append(df)

    result = pd.concat(all_filings, ignore_index=True)

    # Add report_time column based on form
    result['report_time'] = result['form'].map({'10-Q': 'Quarterly', '10-K': 'Annual'})

    # Save cleaned metadata
    result.to_csv("data/filings.csv", index=False)
    print("✅ Filings metadata saved to data/filings.csv")
    print("📊 Report time mapping:")
    print("   10-Q → Quarterly")
    print("   10-K → Annual")
    print(f"📈 Total filings: {len(result)}")
    print(f"📊 Quarterly filings: {len(result[result['report_time'] == 'Quarterly'])}")
    print(f"📊 Annual filings: {len(result[result['report_time'] == 'Annual'])}")
