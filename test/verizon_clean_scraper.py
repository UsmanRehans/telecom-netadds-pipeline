import pandas as pd
import requests
import re
import sys
import os
import json

# Add src directory to path so we can import config
sys.path.append(os.path.dirname(__file__))
from config import HEADERS


def extract_verizon_metrics(filing_url):
    """Extract wireless metrics from Verizon SEC filing."""
    print(f"🔍 Processing: {filing_url}")
    
    try:
        response = requests.get(filing_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        html_content = response.text
        
        metrics = {
            'connections': {},
            'net_additions': {},
            'extraction_method': 'verizon_clean_parser'
        }
        
        # Extract connections (in thousands)
        connections = {
            'wireless_retail_total': r'Wireless retail\s+(\d{1,3}(?:,\d{3})*)',
            'wireless_retail_postpaid': r'Wireless retail postpaid\s+(\d{1,3}(?:,\d{3})*)',
            'wireless_retail_prepaid': r'Wireless retail core prepaid.*?(\d{1,3}(?:,\d{3})*)'
        }
        
        for name, pattern in connections.items():
            match = re.search(pattern, html_content)
            if match:
                value = int(match.group(1).replace(',', ''))
                metrics['connections'][name] = value
                print(f"   ✅ {name}: {value:,}")
            else:
                print(f"   ❌ {name}: Not found")
        
        # Extract net additions (in thousands)
        net_additions = {
            'total_wireless_retail': r'Total wireless retail\s+(\d+|\(\d+\))',
            'wireless_retail_postpaid': r'Wireless retail postpaid\s+(\d+|\(\d+\))',
            'wireless_retail_postpaid_phone': r'Wireless retail postpaid phone\s+(\d+|\(\d+\))',
            'wireless_retail_prepaid': r'Wireless retail core prepaid.*?(\d+|\(\d+\))'
        }
        
        for name, pattern in net_additions.items():
            match = re.search(pattern, html_content)
            if match:
                value_str = match.group(1)
                if value_str.startswith('(') and value_str.endswith(')'):
                    value = -int(value_str[1:-1])
                else:
                    value = int(value_str)
                
                metrics['net_additions'][name] = value
                print(f"   ✅ {name}: {value:,}")
            else:
                print(f"   ❌ {name}: Not found")
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def build_detailed_table_from_html(html_content):
    """Build a detailed table with current and prior-year values for Connections and Net Adds.

    Returns pandas DataFrame with columns:
      - segment: Postpaid | Prepaid
      - connections_2025, connections_2024 (integers, thousands)
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

    # Sections
    conn_start = lower_text.find('connections')
    netadds_start = lower_text.find('net additions in period')
    churn_start = lower_text.find('churn rate')

    if conn_start != -1 and netadds_start != -1 and netadds_start > conn_start:
        connections_text = text[conn_start:netadds_start]
    else:
        connections_text = text

    if netadds_start != -1:
        if churn_start != -1 and churn_start > netadds_start:
            netadds_text = text[netadds_start:churn_start]
        else:
            netadds_text = text[netadds_start:netadds_start + 4000]
    else:
        netadds_text = text

    def find_connections_numbers(src_text, label_regex):
        # For connections: look for large numbers with commas (e.g., 94,948 93,960)
        # Use more specific pattern to avoid picking up small numbers
        pattern = rf"{label_regex}(?:\s+\(\d+\))?\s+(\d{{1,3}}(?:,\d{{3}})*)\s+(\d{{1,3}}(?:,\d{{3}})*)"
        matches = re.findall(pattern, src_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Filter for large numbers (likely subscriber counts)
        large_matches = []
        for match in matches:
            val1, val2 = match
            if len(val1.replace(',', '')) >= 4 and len(val2.replace(',', '')) >= 4:  # At least 4 digits
                large_matches.append(match)
        
        if not large_matches:
            return None, None
            
        # Use the last (most likely) match
        val1, val2 = large_matches[-1]
        def to_int(token):
            return int(token.replace(',', ''))
        return to_int(val1), to_int(val2)

    def find_net_additions_numbers(src_text, label_regex):
        # For net additions: look for numbers, can be negative in parentheses
        # Annual reports have larger numbers (annual totals), quarterly have smaller numbers
        # Handle numbers with commas like 1,345
        patterns = [
            rf"{label_regex}(?:\s+\(\d+\))?\s+(\d{{1,3}}(?:,\d{{3}})*|\(\d{{1,3}}(?:,\d{{3}})*\))\s+(\d{{1,3}}(?:,\d{{3}})*|\(\d{{1,3}}(?:,\d{{3}})*\))",  # With commas
            rf"{label_regex}(?:\s+\(\d+\))?\s+(\d+|\(\d+\))\s+(\d+|\(\d+\))",  # Without commas
            rf"{label_regex}.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",  # More flexible format
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
                        # Net additions should be reasonable numbers (annual can be larger)
                        if -5000 <= num1 <= 5000 and -5000 <= num2 <= 5000:
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
            try:
                return int(t)
            except ValueError:
                return None
        
        val1, val2 = to_int(val1), to_int(val2)
        # Return None if either value couldn't be parsed
        if val1 is None or val2 is None:
            return None, None
        return val1, val2

    # Connections two-column capture
    postpaid_conn_2025, postpaid_conn_2024 = find_connections_numbers(connections_text, r"Wireless\s+retail\s+postpaid")
    # Try core prepaid first, then fallback to non-core prepaid label
    prepaid_conn_2025, prepaid_conn_2024 = find_connections_numbers(connections_text, r"Wireless\s+retail\s+core\s+prepaid")
    if prepaid_conn_2025 is None and prepaid_conn_2024 is None:
        prepaid_conn_2025, prepaid_conn_2024 = find_connections_numbers(connections_text, r"Wireless\s+retail\s+prepaid")

    # Net adds two-column capture
    postpaid_adds_2025, postpaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Wireless\s+retail\s+postpaid")
    # Try core prepaid first, then fallback to non-core prepaid label
    prepaid_adds_2025, prepaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Wireless\s+retail\s+core\s+prepaid")
    if prepaid_adds_2025 is None and prepaid_adds_2024 is None:
        prepaid_adds_2025, prepaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Wireless\s+retail\s+prepaid")

    rows = []
    rows.append({
        'segment': 'Postpaid',
        'connections_2025': postpaid_conn_2025,
        'connections_2024': postpaid_conn_2024,
        'net_adds_2025': postpaid_adds_2025,
        'net_adds_2024': postpaid_adds_2024
    })
    rows.append({
        'segment': 'Prepaid',
        'connections_2025': prepaid_conn_2025,
        'connections_2024': prepaid_conn_2024,
        'net_adds_2025': prepaid_adds_2025,
        'net_adds_2024': prepaid_adds_2024
    })

    return pd.DataFrame(rows, columns=['segment', 'connections_2025', 'connections_2024', 'net_adds_2025', 'net_adds_2024'])


def build_detailed_table_from_url(filing_url):
    """Fetch filing HTML and return the detailed DataFrame."""
    response = requests.get(filing_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return build_detailed_table_from_html(response.text)


def test_verizon_scraper():
    """Test the scraper on the first Verizon filing."""
    print("🧪 Testing Verizon scraper...")
    
    df = pd.read_csv("../data/filings.csv")
    vz_filings = df[df['carrier_name'] == 'VZ']
    
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return False
    
    first_filing = vz_filings.iloc[0]
    filing_url = first_filing['filing_url']
    quarter = first_filing['reportDate']
    
    print(f"📱 Testing: {quarter}")
    
    metrics = extract_verizon_metrics(filing_url)
    
    if metrics:
        print(f"\n📊 Results:")
        print(f"   Connections: {metrics['connections']}")
        print(f"   Net Additions: {metrics['net_additions']}")
        
        # Save results
        with open("../data/verizon_test_results.json", 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n💾 Saved to ../data/verizon_test_results.json")
        
        return True
    else:
        print("❌ No metrics extracted")
        return False


if __name__ == "__main__":
    success = test_verizon_scraper()
    if success:
        print("\n🎉 Test successful!")
    else:
        print("\n❌ Test failed!")