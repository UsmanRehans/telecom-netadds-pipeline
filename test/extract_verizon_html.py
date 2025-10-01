import pandas as pd
import requests
import sys
import os

# Add src directory to path so we can import config
sys.path.append(os.path.dirname(__file__))
from config import HEADERS


def extract_first_verizon_html():
    """
    Extract HTML from the first Verizon filing URL for analysis.
    """
    print("📊 Reading filings data...")
    
    # Read the filings CSV
    df = pd.read_csv("../data/filings.csv")
    
    if df.empty:
        print("❌ No filings found")
        return None
    
    # Find the first Verizon (VZ) filing
    vz_filings = df[df['carrier_name'] == 'VZ']
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return None
    
    first_vz_filing = vz_filings.iloc[0]
    
    carrier = first_vz_filing['carrier_name']
    quarter = first_vz_filing['reportDate']
    form = first_vz_filing['form']
    filing_url = first_vz_filing['filing_url']
    
    print(f"📱 First Verizon filing: {carrier} {form} for {quarter}")
    print(f"🔗 URL: {filing_url}")
    
    # Extract HTML content
    print(f"\n🌐 Fetching HTML content...")
    try:
        response = requests.get(filing_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        print(f"✅ Successfully fetched {len(html_content):,} characters of HTML")
        
        # Save HTML to file for analysis
        output_file = f"../data/verizon_first_filing.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"💾 HTML saved to {output_file}")
        
        return {
            'carrier': carrier,
            'quarter': quarter,
            'form': form,
            'url': filing_url,
            'html_content': html_content,
            'html_length': len(html_content),
            'output_file': output_file
        }
        
    except Exception as e:
        print(f"❌ Error fetching HTML: {e}")
        return None


if __name__ == "__main__":
    result = extract_first_verizon_html()
    if result:
        print(f"\n✅ Ready for analysis!")
        print(f"📁 HTML file: {result['output_file']}")
        print(f"📊 File size: {result['html_length']:,} characters")
        print(f"\n🔍 Now you can open the HTML file and find the wireless metrics data!")
    else:
        print("❌ Failed to extract HTML")
