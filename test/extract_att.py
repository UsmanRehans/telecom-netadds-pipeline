#!/usr/bin/env python3
"""
AT&T quarterly summary extraction.
Processes all AT&T filings and generates quarterly summary data.
"""

import pandas as pd
import json
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from att_clean_scraper import build_att_detailed_table_from_url


def extract_att_quarterly_summary():
    """Process all AT&T filings and return quarterly summary."""
    print("🚀 Processing AT&T filings...")
    
    # Read the filings CSV
    df = pd.read_csv("data/filings.csv")
    att_filings = df[df['carrier_name'] == 'AT&T']
    
    if att_filings.empty:
        print("❌ No AT&T filings found")
        return None
    
    print(f"📱 Found {len(att_filings)} AT&T filings")
    
    all_results = []
    successful_count = 0
    
    for idx, filing in att_filings.iterrows():
        filing_url = filing['filing_url']
        quarter = filing['reportDate']
        form = filing['form']
        filing_date = filing['filingDate']
        report_time = filing['report_time']
        
        print(f"🔍 Processing {quarter} ({form}) - {report_time}")
        
        try:
            detailed_df = build_att_detailed_table_from_url(filing_url)
            
            if detailed_df is not None and not detailed_df.empty:
                detailed_df['quarter'] = quarter
                detailed_df['form'] = form
                detailed_df['filing_date'] = filing_date
                detailed_df['report_time'] = report_time
                detailed_df['filing_url'] = filing_url
                
                all_results.append(detailed_df)
                successful_count += 1
                print(f"   ✅ Success")
            else:
                print(f"   ❌ No data extracted")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Enforce integer-like output using pandas nullable Int64
        for col in ['subscribers_2025', 'subscribers_2024', 'net_adds_2025', 'net_adds_2024']:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').astype('Int64')
        
        # Build quarterly summary
        quarters = sorted(combined_df['quarter'].unique())
        summary_rows = []
        for q in quarters:
            q_df = combined_df[combined_df['quarter'] == q]
            post = q_df[q_df['segment'] == 'Postpaid'].iloc[0] if not q_df[q_df['segment'] == 'Postpaid'].empty else None
            pre = q_df[q_df['segment'] == 'Prepaid'].iloc[0] if not q_df[q_df['segment'] == 'Prepaid'].empty else None
            total = q_df[q_df['segment'] == 'Total'].iloc[0] if not q_df[q_df['segment'] == 'Total'].empty else None
            
            row = {
                'quarter': q,
                'postpaid_subscribers': int(post['subscribers_2025']) if post is not None and pd.notna(post['subscribers_2025']) else None,
                'postpaid_net_adds': int(post['net_adds_2025']) if post is not None and pd.notna(post['net_adds_2025']) else None,
                'prepaid_subscribers': int(pre['subscribers_2025']) if pre is not None and pd.notna(pre['subscribers_2025']) else None,
                'prepaid_net_adds': int(pre['net_adds_2025']) if pre is not None and pd.notna(pre['net_adds_2025']) else None,
                'total_subscribers': int(total['subscribers_2025']) if total is not None and pd.notna(total['subscribers_2025']) else None,
                'total_net_adds': int(total['net_adds_2025']) if total is not None and pd.notna(total['net_adds_2025']) else None,
            }
            
            summary_rows.append(row)
        
        print(f"✅ Successfully processed {successful_count} out of {len(att_filings)} AT&T filings")
        return summary_rows
    else:
        print("❌ No successful AT&T extractions")
        return None


def save_att_data(summary_data):
    """Save AT&T data to CSV and JSON files."""
    if summary_data is None:
        print("❌ No data to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as CSV
    df = pd.DataFrame(summary_data)
    csv_file = f"data/att_quarterly_summary_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"💾 AT&T quarterly summary saved to {csv_file}")
    
    # Save as JSON
    json_file = f"data/att_quarterly_summary_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"💾 AT&T quarterly summary saved to {json_file}")
    
    # Save latest versions
    df.to_csv("data/att_quarterly_summary.csv", index=False)
    with open("data/att_quarterly_summary.json", 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"💾 AT&T latest quarterly summary saved to data/att_quarterly_summary.csv")


if __name__ == "__main__":
    print("🚀 Starting AT&T quarterly summary extraction...")
    print("=" * 60)
    
    # Extract data
    att_data = extract_att_quarterly_summary()
    
    # Save data
    save_att_data(att_data)
    
    print("\n🎉 AT&T quarterly summary extraction complete!")
    if att_data:
        print(f"📊 AT&T: {len(att_data)} quarters processed")
