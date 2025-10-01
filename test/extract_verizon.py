#!/usr/bin/env python3
"""
Verizon quarterly summary extraction.
Processes all Verizon filings and generates quarterly summary data.
"""

import pandas as pd
import json
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from verizon_clean_scraper import build_detailed_table_from_url


def extract_verizon_quarterly_summary():
    """Process all Verizon filings and return quarterly summary."""
    print("🚀 Processing Verizon filings...")
    
    # Read the filings CSV
    df = pd.read_csv("data/filings.csv")
    vz_filings = df[df['carrier_name'] == 'VZ']
    
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return None
    
    print(f"📱 Found {len(vz_filings)} Verizon filings")
    
    all_results = []
    successful_count = 0
    
    for idx, filing in vz_filings.iterrows():
        filing_url = filing['filing_url']
        quarter = filing['reportDate']
        form = filing['form']
        filing_date = filing['filingDate']
        report_time = filing['report_time']
        
        print(f"🔍 Processing {quarter} ({form}) - {report_time}")
        
        try:
            detailed_df = build_detailed_table_from_url(filing_url)
            
            if detailed_df is not None and not detailed_df.empty:
                detailed_df['quarter'] = quarter
                detailed_df['form'] = form
                detailed_df['filing_date'] = filing_date
                detailed_df['report_time'] = report_time
                detailed_df['filing_url'] = filing_url
                
                all_results.append(detailed_df)
                successful_count += 1
                
                # Show what we extracted
                postpaid_row = detailed_df[detailed_df['segment'] == 'Postpaid'].iloc[0]
                prepaid_row = detailed_df[detailed_df['segment'] == 'Prepaid'].iloc[0]
                print(f"   ✅ Success - Postpaid: {postpaid_row['connections_2025']:,}, Prepaid: {prepaid_row['connections_2025']:,}")
                if pd.notna(postpaid_row['net_adds_2025']):
                    print(f"      Net adds - Postpaid: {postpaid_row['net_adds_2025']}, Prepaid: {prepaid_row['net_adds_2025']}")
            else:
                print(f"   ❌ No data extracted")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Enforce integer-like output using pandas nullable Int64
        for col in ['connections_2025', 'connections_2024', 'net_adds_2025', 'net_adds_2024']:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').astype('Int64')
        
        # Build quarterly summary
        quarters = sorted(combined_df['quarter'].unique())
        summary_rows = []
        for q in quarters:
            q_df = combined_df[combined_df['quarter'] == q]
            
            # For Q4, we might have both 10-Q and 10-K data
            # Prioritize 10-Q for net additions, 10-K for year-end connections
            quarterly_data = q_df[q_df['form'] == '10-Q'] if not q_df[q_df['form'] == '10-Q'].empty else q_df
            annual_data = q_df[q_df['form'] == '10-K'] if not q_df[q_df['form'] == '10-K'].empty else None
            
            # Use quarterly data if available, otherwise use annual data
            source_data = quarterly_data if not quarterly_data.empty else q_df
            
            post = source_data[source_data['segment'] == 'Postpaid'].iloc[0] if not source_data[source_data['segment'] == 'Postpaid'].empty else None
            pre = source_data[source_data['segment'] == 'Prepaid'].iloc[0] if not source_data[source_data['segment'] == 'Prepaid'].empty else None
            
            # For net additions, prefer quarterly data
            net_adds_post = None
            net_adds_pre = None
            if not quarterly_data.empty:
                q_post = quarterly_data[quarterly_data['segment'] == 'Postpaid'].iloc[0] if not quarterly_data[quarterly_data['segment'] == 'Postpaid'].empty else None
                q_pre = quarterly_data[quarterly_data['segment'] == 'Prepaid'].iloc[0] if not quarterly_data[quarterly_data['segment'] == 'Prepaid'].empty else None
                if q_post is not None and pd.notna(q_post['net_adds_2025']):
                    net_adds_post = int(q_post['net_adds_2025'])
                if q_pre is not None and pd.notna(q_pre['net_adds_2025']):
                    net_adds_pre = int(q_pre['net_adds_2025'])
            
            row = {
                'quarter': q,
                'postpaid_connections': int(post['connections_2025']) if post is not None and pd.notna(post['connections_2025']) else None,
                'postpaid_net_adds': net_adds_post,
                'prepaid_connections': int(pre['connections_2025']) if pre is not None and pd.notna(pre['connections_2025']) else None,
                'prepaid_net_adds': net_adds_pre,
                'total_connections': None,
                'total_net_adds': None,
            }
            
            # Calculate totals when both components exist
            if (post is not None and pre is not None and 
                pd.notna(post['connections_2025']) and pd.notna(pre['connections_2025'])):
                row['total_connections'] = int(post['connections_2025']) + int(pre['connections_2025'])
            
            if net_adds_post is not None and net_adds_pre is not None:
                row['total_net_adds'] = net_adds_post + net_adds_pre
            
            summary_rows.append(row)
        
        print(f"✅ Successfully processed {successful_count} out of {len(vz_filings)} Verizon filings")
        return summary_rows
    else:
        print("❌ No successful Verizon extractions")
        return None


def save_verizon_data(summary_data):
    """Save Verizon data to CSV and JSON files."""
    if summary_data is None:
        print("❌ No data to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as CSV
    df = pd.DataFrame(summary_data)
    csv_file = f"data/verizon_quarterly_summary_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"💾 Verizon quarterly summary saved to {csv_file}")
    
    # Save as JSON
    json_file = f"data/verizon_quarterly_summary_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"💾 Verizon quarterly summary saved to {json_file}")
    
    # Save latest versions
    df.to_csv("data/verizon_quarterly_summary.csv", index=False)
    with open("data/verizon_quarterly_summary.json", 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"💾 Verizon latest quarterly summary saved to data/verizon_quarterly_summary.csv")


if __name__ == "__main__":
    print("🚀 Starting Verizon quarterly summary extraction...")
    print("=" * 60)
    
    # Extract data
    verizon_data = extract_verizon_quarterly_summary()
    
    # Save data
    save_verizon_data(verizon_data)
    
    print("\n🎉 Verizon quarterly summary extraction complete!")
    if verizon_data:
        print(f"📊 Verizon: {len(verizon_data)} quarters processed")
