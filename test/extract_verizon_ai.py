import pandas as pd
import requests
from bs4 import BeautifulSoup
from src.ai_extractor import extract_telecom_data_with_ai, convert_ai_data_to_dataframe
from typing import List, Dict

def build_detailed_table_from_url_ai(filing_url: str) -> pd.DataFrame:
    """
    Build detailed table from URL using AI extraction
    """
    try:
        # Fetch the HTML content
        response = requests.get(filing_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        html_content = soup.get_text()
        
        # Extract data using AI
        ai_data = extract_telecom_data_with_ai(html_content, "VZ", "2024-12-31")
        
        # Convert to DataFrame format
        df = convert_ai_data_to_dataframe(ai_data)
        
        if df is not None and not df.empty:
            print(f"✅ AI extraction successful - Confidence: {ai_data.get('extraction_confidence', 'unknown')}")
            if ai_data.get('notes'):
                print(f"📝 Notes: {ai_data['notes']}")
        else:
            print("❌ AI extraction failed")
            
        return df
        
    except Exception as e:
        print(f"❌ Error in AI extraction: {e}")
        return pd.DataFrame()

def extract_verizon_quarterly_summary_ai():
    """
    Extract Verizon quarterly summary using AI
    """
    print("🤖 Processing Verizon filings with AI...")
    
    try:
        df = pd.read_csv("data/filings.csv")
    except Exception as e:
        print(f"❌ Error reading filings.csv: {e}")
        return []

    vz_filings = df[df['carrier_name'] == 'VZ'].copy()
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return []

    # Sort filings by reportDate to process chronologically
    vz_filings['reportDate'] = pd.to_datetime(vz_filings['reportDate'])
    vz_filings = vz_filings.sort_values(by='reportDate').reset_index(drop=True)

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
            detailed_df = build_detailed_table_from_url_ai(filing_url)
            
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
                total_row = detailed_df[detailed_df['segment'] == 'Total'].iloc[0]
                
                print(f"   ✅ Success - Postpaid: {postpaid_row['connections_2025']:,}, Prepaid: {prepaid_row['connections_2025']:,}")
                if pd.notna(postpaid_row['net_adds_2025']):
                    print(f"      Net adds - Postpaid: {postpaid_row['net_adds_2025']}, Prepaid: {prepaid_row['net_adds_2025']}")
                if pd.notna(total_row['churn_rate_2025']):
                    print(f"      Churn rate - Total: {total_row['churn_rate_2025']}%, Postpaid: {postpaid_row['churn_rate_2025']}%")
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
            
            # Get the data for this quarter
            postpaid_data = q_df[q_df['segment'] == 'Postpaid'].iloc[0] if not q_df[q_df['segment'] == 'Postpaid'].empty else None
            prepaid_data = q_df[q_df['segment'] == 'Prepaid'].iloc[0] if not q_df[q_df['segment'] == 'Prepaid'].empty else None
            total_data = q_df[q_df['segment'] == 'Total'].iloc[0] if not q_df[q_df['segment'] == 'Total'].empty else None
            
            row = {
                'quarter': q,
                'postpaid_connections': int(postpaid_data['connections_2025']) if postpaid_data is not None and pd.notna(postpaid_data['connections_2025']) else None,
                'postpaid_net_adds': int(postpaid_data['net_adds_2025']) if postpaid_data is not None and pd.notna(postpaid_data['net_adds_2025']) else None,
                'postpaid_churn_rate': float(postpaid_data['churn_rate_2025']) if postpaid_data is not None and pd.notna(postpaid_data['churn_rate_2025']) else None,
                'prepaid_connections': int(prepaid_data['connections_2025']) if prepaid_data is not None and pd.notna(prepaid_data['connections_2025']) else None,
                'prepaid_net_adds': int(prepaid_data['net_adds_2025']) if prepaid_data is not None and pd.notna(prepaid_data['net_adds_2025']) else None,
                'total_connections': int(total_data['connections_2025']) if total_data is not None and pd.notna(total_data['connections_2025']) else None,
                'total_net_adds': int(total_data['net_adds_2025']) if total_data is not None and pd.notna(total_data['net_adds_2025']) else None,
                'total_churn_rate': float(total_data['churn_rate_2025']) if total_data is not None and pd.notna(total_data['churn_rate_2025']) else None,
                'extraction_method': 'ai',
                'confidence': postpaid_data['confidence'] if postpaid_data is not None else 'unknown'
            }
            
            summary_rows.append(row)
        
        print(f"✅ Successfully processed {successful_count} out of {len(vz_filings)} Verizon filings with AI")
        return summary_rows
    else:
        print("❌ No successful Verizon extractions")
        return []

if __name__ == "__main__":
    # Test with a single filing
    test_url = "https://www.sec.gov/Archives/edgar/data/732712/000073271225000006/vz-20241231.htm"
    print("🧪 Testing AI extraction on Verizon 2024 annual report...")
    df = build_detailed_table_from_url_ai(test_url)
    if not df.empty:
        print("\n📊 AI Extraction Results:")
        print(df.to_string())
    else:
        print("❌ AI extraction failed")
