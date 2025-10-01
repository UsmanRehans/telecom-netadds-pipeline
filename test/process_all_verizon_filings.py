import pandas as pd
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from verizon_clean_scraper import build_detailed_table_from_url, build_summary_table_from_url


def process_all_verizon_filings():
    """
    Process all Verizon filings from filings.csv and extract detailed tables.
    """
    print("🚀 Processing all Verizon filings from filings.csv...")
    
    # Read the filings CSV
    try:
        df = pd.read_csv("data/filings.csv")
        print(f"📊 Loaded {len(df)} total filings")
    except Exception as e:
        print(f"❌ Error reading filings.csv: {e}")
        return
    
    # Filter for Verizon filings
    vz_filings = df[df['carrier_name'] == 'VZ']
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return
    
    print(f"📱 Found {len(vz_filings)} Verizon filings")
    
    # Process each filing
    all_results = []
    successful_count = 0
    
    for idx, filing in vz_filings.iterrows():
        filing_url = filing['filing_url']
        quarter = filing['reportDate']
        form = filing['form']
        filing_date = filing['filingDate']
        
        print(f"\n🔍 Processing {quarter} ({form}) - Filed: {filing_date}")
        print(f"   URL: {filing_url}")
        
        try:
            # Extract detailed table
            detailed_df = build_detailed_table_from_url(filing_url)
            
            if detailed_df is not None and not detailed_df.empty:
                # Add filing metadata to each row
                detailed_df['quarter'] = quarter
                detailed_df['form'] = form
                detailed_df['filing_date'] = filing_date
                detailed_df['filing_url'] = filing_url
                
                all_results.append(detailed_df)
                successful_count += 1
                
                print(f"   ✅ Successfully extracted data")
                print(f"   📊 Postpaid: {detailed_df.iloc[0]['connections_2025']:,} connections, {detailed_df.iloc[0]['net_adds_2025']} net adds")
                print(f"   📊 Prepaid: {detailed_df.iloc[1]['connections_2025']:,} connections, {detailed_df.iloc[1]['net_adds_2025']} net adds")
            else:
                print(f"   ❌ No data extracted")
                
        except Exception as e:
            print(f"   ❌ Error processing filing: {e}")
            continue
    
    # Combine all results
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        # Enforce integer-like output using pandas nullable Int64
        for col in ['connections_2025', 'connections_2024', 'net_adds_2025', 'net_adds_2024']:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').astype('Int64')
        
        # Save combined results
        output_file = "data/verizon_all_filings_detailed.csv"
        combined_df.to_csv(output_file, index=False)
        
        print(f"\n🎉 Successfully processed {successful_count} out of {len(vz_filings)} Verizon filings")
        print(f"💾 Combined results saved to {output_file}")
        
        # Display summary
        print(f"\n📈 Summary by Quarter:")
        # Build a clean quarterly summary computing totals only when both segments exist
        quarters = sorted(combined_df['quarter'].unique())
        summary_rows = []
        for q in quarters:
            q_df = combined_df[combined_df['quarter'] == q]
            post = q_df[q_df['segment'] == 'Postpaid'].iloc[0] if not q_df[q_df['segment'] == 'Postpaid'].empty else None
            pre = q_df[q_df['segment'] == 'Prepaid'].iloc[0] if not q_df[q_df['segment'] == 'Prepaid'].empty else None
            row = {
                'quarter': q,
                'postpaid_connections': post['connections_2025'] if post is not None else pd.NA,
                'postpaid_net_adds': post['net_adds_2025'] if post is not None else pd.NA,
                'prepaid_connections': pre['connections_2025'] if pre is not None else pd.NA,
                'prepaid_net_adds': pre['net_adds_2025'] if pre is not None else pd.NA,
                'total_connections': pd.NA,
                'total_net_adds': pd.NA,
            }
            if post is not None and pre is not None and pd.notna(post['connections_2025']) and pd.notna(pre['connections_2025']):
                row['total_connections'] = int(post['connections_2025']) + int(pre['connections_2025'])
            if post is not None and pre is not None and pd.notna(post['net_adds_2025']) and pd.notna(pre['net_adds_2025']):
                row['total_net_adds'] = int(post['net_adds_2025']) + int(pre['net_adds_2025'])
            summary_rows.append(row)
        summary_df = pd.DataFrame(summary_rows)
        # Ensure Int64 for integers
        for col in ['postpaid_connections', 'postpaid_net_adds', 'prepaid_connections', 'prepaid_net_adds', 'total_connections', 'total_net_adds']:
            summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').astype('Int64')
        
        # Save quarterly summary
        summary_file = "data/verizon_quarterly_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"\n📈 Summary by Quarter:")
        print(summary_df.to_string(index=False))
        
        return combined_df
    else:
        print("❌ No successful extractions")
        return None


def create_quarterly_summary():
    """
    Create a quarterly summary table showing trends over time.
    """
    print("\n📊 Creating quarterly summary...")
    
    try:
        df = pd.read_csv("data/verizon_all_filings_detailed.csv")
        
        # Create quarterly summary
        quarterly_summary = []
        
        for quarter in df['quarter'].unique():
            quarter_data = df[df['quarter'] == quarter]
            
            postpaid = quarter_data[quarter_data['segment'] == 'Postpaid'].iloc[0]
            prepaid = quarter_data[quarter_data['segment'] == 'Prepaid'].iloc[0]
            
            quarterly_summary.append({
                'quarter': quarter,
                'postpaid_connections': postpaid['connections_2025'],
                'postpaid_net_adds': postpaid['net_adds_2025'],
                'prepaid_connections': prepaid['connections_2025'],
                'prepaid_net_adds': prepaid['net_adds_2025'],
                'total_connections': postpaid['connections_2025'] + prepaid['connections_2025'],
                'total_net_adds': postpaid['net_adds_2025'] + prepaid['net_adds_2025']
            })
        
        summary_df = pd.DataFrame(quarterly_summary)
        summary_df = summary_df.sort_values('quarter')
        
        # Save quarterly summary
        summary_file = "data/verizon_quarterly_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        
        print(f"💾 Quarterly summary saved to {summary_file}")
        print(f"\n📈 Quarterly Trends:")
        print(summary_df.to_string(index=False))
        
        return summary_df
        
    except Exception as e:
        print(f"❌ Error creating quarterly summary: {e}")
        return None


if __name__ == "__main__":
    # Process all filings
    results = process_all_verizon_filings()
    
    if results is not None:
        # Create quarterly summary
        create_quarterly_summary()
        
        print(f"\n🎉 All processing complete!")
        print(f"📁 Files created:")
        print(f"   - data/verizon_all_filings_detailed.csv (detailed data for all quarters)")
        print(f"   - data/verizon_quarterly_summary.csv (quarterly summary)")
    else:
        print(f"\n❌ Processing failed")
        sys.exit(1)
