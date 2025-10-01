#!/usr/bin/env python3
"""
T-Mobile quarterly summary extraction.
Processes all T-Mobile filings and generates quarterly summary data.
"""

import pandas as pd
import json
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))


def extract_tmobile_quarterly_summary():
    """Process all T-Mobile filings and return quarterly summary."""
    print("🚀 Processing T-Mobile filings...")
    
    # Read the filings CSV
    df = pd.read_csv("data/filings.csv")
    tmobile_filings = df[df['carrier_name'] == 'TMUS']
    
    if tmobile_filings.empty:
        print("❌ No T-Mobile filings found")
        return None
    
    print(f"📱 Found {len(tmobile_filings)} T-Mobile filings")
    print("⚠️ T-Mobile extraction not yet implemented")
    
    # TODO: Implement T-Mobile extraction logic
    # This will be similar to Verizon and AT&T but adapted for T-Mobile's filing format
    
    return None


def save_tmobile_data(summary_data):
    """Save T-Mobile data to CSV and JSON files."""
    if summary_data is None:
        print("❌ No data to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as CSV
    df = pd.DataFrame(summary_data)
    csv_file = f"data/tmobile_quarterly_summary_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"💾 T-Mobile quarterly summary saved to {csv_file}")
    
    # Save as JSON
    json_file = f"data/tmobile_quarterly_summary_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"💾 T-Mobile quarterly summary saved to {json_file}")
    
    # Save latest versions
    df.to_csv("data/tmobile_quarterly_summary.csv", index=False)
    with open("data/tmobile_quarterly_summary.json", 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"💾 T-Mobile latest quarterly summary saved to data/tmobile_quarterly_summary.csv")


if __name__ == "__main__":
    print("🚀 Starting T-Mobile quarterly summary extraction...")
    print("=" * 60)
    
    # Extract data
    tmobile_data = extract_tmobile_quarterly_summary()
    
    # Save data
    save_tmobile_data(tmobile_data)
    
    print("\n🎉 T-Mobile quarterly summary extraction complete!")
    if tmobile_data:
        print(f"📊 T-Mobile: {len(tmobile_data)} quarters processed")
