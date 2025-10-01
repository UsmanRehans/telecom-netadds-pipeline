import pandas as pd
import requests
import re
import sys
import os
import json

# Add src directory to path so we can import config
sys.path.append(os.path.dirname(__file__))
from config import HEADERS


def build_att_detailed_table_from_html(html_content):
    """Build a detailed table with current and prior-year values for AT&T Subscribers and Net Adds.

    Returns pandas DataFrame with columns:
      - segment: Postpaid | Prepaid | Total
      - subscribers_2025, subscribers_2024 (integers, thousands)
      - net_adds_2025, net_adds_2024 (integers, thousands)
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ')
    except Exception:
        text = html_content

    text = re.sub(r"\s+", " ", text)
    lower_text = text.lower()

    # Sections - AT&T uses "Subscribers" instead of "Connections"
    subscribers_start = lower_text.find('subscribers june 30')
    netadds_start = lower_text.find('net additions')
    churn_start = lower_text.find('churn')

    if subscribers_start != -1 and netadds_start != -1 and netadds_start > subscribers_start:
        subscribers_text = text[subscribers_start:netadds_start]
    else:
        subscribers_text = text

    if netadds_start != -1:
        if churn_start != -1 and churn_start > netadds_start:
            netadds_text = text[netadds_start:churn_start]
        else:
            netadds_text = text[netadds_start:netadds_start + 4000]
    else:
        netadds_text = text

    def find_subscribers_numbers(src_text, label_regex):
        # For subscribers: look for large numbers with commas (e.g., 89,928 87,999)
        pattern = rf"{label_regex}.*?(\d{{1,3}}(?:,\d{{3}})*).*?(\d{{1,3}}(?:,\d{{3}})*)"
        m = re.search(pattern, src_text, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return None, None
        def to_int(token):
            return int(token.replace(',', ''))
        val1, val2 = to_int(m.group(1)), to_int(m.group(2))
        return val1, val2

    def find_net_additions_numbers(src_text, label_regex):
        # For net additions: look for the Mobility Net Additions table
        # Try multiple patterns to catch different formats in quarterly vs annual reports
        patterns = [
            rf"{label_regex}.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",  # Standard format
            rf"{label_regex}.*?(\d{{1,3}}(?:,\d{{3}})*).*?(\d{{1,3}}(?:,\d{{3}})*)",  # With commas for annual
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, src_text, flags=re.IGNORECASE | re.DOTALL)
            if matches:
                # Filter for reasonable net additions numbers
                valid_matches = []
                for match in matches:
                    val1, val2 = match
                    try:
                        num1 = int(val1.replace(',', '').replace('(', '').replace(')', ''))
                        num2 = int(val2.replace(',', '').replace('(', '').replace(')', ''))
                        # Net additions should be reasonable numbers
                        if -10000 <= num1 <= 10000 and -10000 <= num2 <= 10000:
                            valid_matches.append(match)
                    except ValueError:
                        continue
                
                if valid_matches:
                    # Use the first valid match
                    val1, val2 = valid_matches[0]
                    break
        else:
            return None, None
        
        def to_int(token):
            t = token.replace(',', '')
            if t.startswith('(') and t.endswith(')'):
                return -int(t[1:-1])
            return int(t)
        
        val1, val2 = to_int(val1), to_int(val2)
        return val1, val2

    # Subscribers two-column capture
    postpaid_sub_2025, postpaid_sub_2024 = find_subscribers_numbers(subscribers_text, r"Postpaid")
    prepaid_sub_2025, prepaid_sub_2024 = find_subscribers_numbers(subscribers_text, r"Prepaid")
    
    # Calculate total subscribers
    total_sub_2025 = None
    total_sub_2024 = None
    if postpaid_sub_2025 is not None and prepaid_sub_2025 is not None:
        total_sub_2025 = postpaid_sub_2025 + prepaid_sub_2025
    if postpaid_sub_2024 is not None and prepaid_sub_2024 is not None:
        total_sub_2024 = postpaid_sub_2024 + prepaid_sub_2024

    # Net adds two-column capture from Mobility Net Additions table
    postpaid_adds_2025, postpaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Postpaid.*?[Pp]hone.*?[Nn]et [Aa]dditions")
    prepaid_adds_2025, prepaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Prepaid")
    
    # Total net additions - look for the summary line (skip the footnote number)
    total_adds_2025, total_adds_2024 = find_net_additions_numbers(netadds_text, r"[Mm]obility [Nn]et [Ss]ubscriber [Aa]dditions.*?\d+\s+(\d+|\(\d+\))\s+(\d+|\(\d+\))")

    rows = []
    
    # Postpaid row
    if postpaid_sub_2025 is not None or postpaid_adds_2025 is not None:
        rows.append({
            'segment': 'Postpaid',
            'subscribers_2025': postpaid_sub_2025,
            'subscribers_2024': postpaid_sub_2024,
            'net_adds_2025': postpaid_adds_2025,
            'net_adds_2024': postpaid_adds_2024
        })
    
    # Prepaid row
    if prepaid_sub_2025 is not None or prepaid_adds_2025 is not None:
        rows.append({
            'segment': 'Prepaid',
            'subscribers_2025': prepaid_sub_2025,
            'subscribers_2024': prepaid_sub_2024,
            'net_adds_2025': prepaid_adds_2025,
            'net_adds_2024': prepaid_adds_2024
        })
    
    # Total row
    if total_sub_2025 is not None or total_adds_2025 is not None:
        rows.append({
            'segment': 'Total',
            'subscribers_2025': total_sub_2025,
            'subscribers_2024': total_sub_2024,
            'net_adds_2025': total_adds_2025,
            'net_adds_2024': total_adds_2024
        })

    return pd.DataFrame(rows, columns=['segment', 'subscribers_2025', 'subscribers_2024', 'net_adds_2025', 'net_adds_2024'])


def build_att_detailed_table_from_url(filing_url):
    """Fetch AT&T filing HTML and return the detailed DataFrame."""
    response = requests.get(filing_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return build_att_detailed_table_from_html(response.text)


def test_att_scraper():
    """Test the AT&T scraper on the first AT&T filing."""
    print("🧪 Testing AT&T scraper...")
    
    df = pd.read_csv("data/filings.csv")
    att_filings = df[df['carrier_name'] == 'AT&T']
    
    if att_filings.empty:
        print("❌ No AT&T filings found")
        return False
    
    first_filing = att_filings.iloc[0]
    filing_url = first_filing['filing_url']
    quarter = first_filing['reportDate']
    
    print(f"📱 Testing: {quarter}")
    
    detailed_df = build_att_detailed_table_from_url(filing_url)
    
    if detailed_df is not None and not detailed_df.empty:
        print(f"\n📊 Results:")
        print(detailed_df.to_string(index=False))
        
        # Save results
        output_file = "data/att_test_results.csv"
        detailed_df.to_csv(output_file, index=False)
        print(f"\n💾 Saved to {output_file}")
        
        return True
    else:
        print("❌ No data extracted")
        return False


if __name__ == "__main__":
    success = test_att_scraper()
    if success:
        print("\n🎉 AT&T scraper test successful!")
    else:
        print("\n❌ AT&T scraper test failed!")
