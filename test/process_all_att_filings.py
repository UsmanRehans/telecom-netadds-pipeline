import pandas as pd
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from att_clean_scraper import build_att_detailed_table_from_url


def process_all_att_filings():
    """
    Process all AT&T filings from filings.csv and extract detailed tables.
    """
    print("🚀 Processing all AT&T filings from filings.csv...")
    
    # Read the filings CSV
    try:
        df = pd.read_csv("data/filings.csv")
        print(f"📊 Loaded {len(df)} total filings")
    except Exception as e:
        print(f"❌ Error reading filings.csv: {e}")
        return
    
    # Filter for AT&T filings
    att_filings = df[df['carrier_name'] == 'AT&T']
    if att_filings.empty:
        print("❌ No AT&T filings found")
        return
    
    print(f"📱 Found {len(att_filings)} AT&T filings")
    
    # Process each filing
    all_results = []
    successful_count = 0
    
    for idx, filing in att_filings.iterrows():
        filing_url = filing['filing_url']
        quarter = filing['reportDate']
        form = filing['form']
        filing_date = filing['filingDate']
        
        print(f"\n🔍 Processing {quarter} ({form}) - Filed: {filing_date}")
        print(f"   URL: {filing_url}")
        
        try:
            # Extract detailed table
            detailed_df = build_att_detailed_table_from_url(filing_url)
            
            if detailed_df is not None and not detailed_df.empty:
                # Add filing metadata to each row
                detailed_df['quarter'] = quarter
                detailed_df['form'] = form
                detailed_df['filing_date'] = filing_date
                detailed_df['filing_url'] = filing_url
                
                all_results.append(detailed_df)
                successful_count += 1
                
                print(f"   ✅ Successfully extracted data")
                # Show postpaid data if available
                postpaid_row = detailed_df[detailed_df['segment'] == 'Postpaid']
                if not postpaid_row.empty:
                    postpaid = postpaid_row.iloc[0]
                    print(f"   📊 Postpaid: {postpaid['subscribers_2025']:,} subscribers, {postpaid['net_adds_2025']} net adds")
                
                # Show prepaid data if available
                prepaid_row = detailed_df[detailed_df['segment'] == 'Prepaid']
                if not prepaid_row.empty:
                    prepaid = prepaid_row.iloc[0]
                    print(f"   📊 Prepaid: {prepaid['subscribers_2025']:,} subscribers, {prepaid['net_adds_2025']} net adds")
            else:
                print(f"   ❌ No data extracted")
                
        except Exception as e:
            print(f"   ❌ Error processing filing: {e}")
            continue
    
    # Combine all results
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        
        # Enforce integer-like output using pandas nullable Int64
        for col in ['subscribers_2025', 'subscribers_2024', 'net_adds_2025', 'net_adds_2024']:
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').astype('Int64')
        
        # Save combined results
        output_file = "data/att_all_filings_detailed.csv"
        combined_df.to_csv(output_file, index=False)
        
        print(f"\n🎉 Successfully processed {successful_count} out of {len(att_filings)} AT&T filings")
        print(f"💾 Combined results saved to {output_file}")
        
        # Build a clean quarterly summary
        quarters = sorted(combined_df['quarter'].unique())
        summary_rows = []
        for q in quarters:
            q_df = combined_df[combined_df['quarter'] == q]
            post = q_df[q_df['segment'] == 'Postpaid'].iloc[0] if not q_df[q_df['segment'] == 'Postpaid'].empty else None
            pre = q_df[q_df['segment'] == 'Prepaid'].iloc[0] if not q_df[q_df['segment'] == 'Prepaid'].empty else None
            total = q_df[q_df['segment'] == 'Total'].iloc[0] if not q_df[q_df['segment'] == 'Total'].empty else None
            
            row = {
                'quarter': q,
                'postpaid_subscribers': post['subscribers_2025'] if post is not None else pd.NA,
                'postpaid_net_adds': post['net_adds_2025'] if post is not None else pd.NA,
                'prepaid_subscribers': pre['subscribers_2025'] if pre is not None else pd.NA,
                'prepaid_net_adds': pre['net_adds_2025'] if pre is not None else pd.NA,
                'total_subscribers': total['subscribers_2025'] if total is not None else pd.NA,
                'total_net_adds': total['net_adds_2025'] if total is not None else pd.NA,
            }
            summary_rows.append(row)
        
        summary_df = pd.DataFrame(summary_rows)
        # Ensure Int64 for integers
        for col in ['postpaid_subscribers', 'postpaid_net_adds', 'prepaid_subscribers', 'prepaid_net_adds', 'total_subscribers', 'total_net_adds']:
            summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce').astype('Int64')
        
        # Save quarterly summary
        summary_file = "data/att_quarterly_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        
        print(f"\n📈 Summary by Quarter:")
        print(summary_df.to_string(index=False))
        print(f"\n💾 Quarterly summary saved to {summary_file}")
        
        return combined_df
    else:
        print("❌ No successful extractions")
        return None


if __name__ == "__main__":
    # Process all filings
    results = process_all_att_filings()
    
    if results is not None:
        print(f"\n🎉 All AT&T processing complete!")
        print(f"📁 Files created:")
        print(f"   - data/att_all_filings_detailed.csv (detailed data for all quarters)")
        print(f"   - data/att_quarterly_summary.csv (quarterly summary)")
    else:
        print(f"\n❌ AT&T processing failed")
        sys.exit(1)
