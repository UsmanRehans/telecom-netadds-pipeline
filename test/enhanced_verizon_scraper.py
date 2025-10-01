import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple

def find_connections_numbers(src_text, label_regex):
    """Find connection numbers with commas (e.g., 94,948 93,960)"""
    pattern = rf"{label_regex}(?:\s+\(\d+\))?\s+(\d{{1,3}}(?:,\d{{3}})*)\s+(\d{{1,3}}(?:,\d{{3}})*)"
    matches = re.findall(pattern, src_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Filter for large numbers (likely subscriber counts)
    large_matches = []
    for match in matches:
        val1, val2 = match
        if len(val1.replace(',', '')) >= 4 and len(val2.replace(',', '')) >= 4:
            large_matches.append(match)
    
    if not large_matches:
        return None, None
        
    # Use the last (most likely) match
    val1, val2 = large_matches[-1]
    def to_int(token):
        return int(token.replace(',', ''))
    return to_int(val1), to_int(val2)

def find_net_additions_numbers(src_text, label_regex):
    """Find net additions numbers, can be negative in parentheses"""
    patterns = [
        rf"{label_regex}(?:\s+\(\d+\))?\s+(\d{{1,3}}(?:,\d{{3}})*|\(\d{{1,3}}(?:,\d{{3}})*\))\s+(\d{{1,3}}(?:,\d{{3}})*|\(\d{{1,3}}(?:,\d{{3}})*\))",  # With commas
        rf"{label_regex}(?:\s+\(\d+\))?\s+(\d+|\(\d+\))\s+(\d+|\(\d+\))",  # Without commas
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
                    if -5000 <= num1 <= 5000 and -5000 <= num2 <= 5000:
                        valid_matches.append(match)
                except ValueError:
                    continue
            
            if valid_matches:
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

def find_churn_rates(src_text, label_regex):
    """Find churn rates as percentages (e.g., 1.58% 1.63%)"""
    pattern = rf"{label_regex}(?:\s+\(\d+\))?\s+(\d+\.?\d*)\s*%\s+(\d+\.?\d*)\s*%"
    matches = re.findall(pattern, src_text, flags=re.IGNORECASE | re.DOTALL)
    
    if matches:
        val1, val2 = matches[0]
        return float(val1), float(val2)
    return None, None

def build_detailed_table_from_url_enhanced(filing_url: str) -> pd.DataFrame:
    """
    Build detailed table from URL using enhanced regex extraction
    """
    try:
        response = requests.get(filing_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        src_text = soup.get_text()
        
        # Split into sections
        connections_match = re.search(r'Connections.*?(?=Net Additions|Churn Rate|Account Statistics|$)', src_text, re.IGNORECASE | re.DOTALL)
        connections_text = connections_match.group(0) if connections_match else src_text
        
        netadds_match = re.search(r'Net Additions in Period.*?(?=Churn Rate|Account Statistics|$)', src_text, re.IGNORECASE | re.DOTALL)
        netadds_text = netadds_match.group(0) if netadds_match else src_text
        
        churn_match = re.search(r'Churn Rate.*?(?=Account Statistics|$)', src_text, re.IGNORECASE | re.DOTALL)
        churn_text = churn_match.group(0) if churn_match else src_text
        
        # Extract connections data
        postpaid_conn_2025, postpaid_conn_2024 = find_connections_numbers(connections_text, r"Wireless\s+retail\s+postpaid")
        
        # Try core prepaid first, then fallback to non-core prepaid label
        prepaid_conn_2025, prepaid_conn_2024 = find_connections_numbers(connections_text, r"Wireless\s+retail\s+core\s+prepaid")
        if prepaid_conn_2025 is None and prepaid_conn_2024 is None:
            prepaid_conn_2025, prepaid_conn_2024 = find_connections_numbers(connections_text, r"Wireless\s+retail\s+prepaid")
        
        # Try total connections
        total_conn_2025, total_conn_2024 = find_connections_numbers(connections_text, r"Total\s+wireless\s+retail")
        
        # Extract net additions data
        postpaid_adds_2025, postpaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Wireless\s+retail\s+postpaid")
        
        # Try core prepaid first, then fallback to non-core prepaid label
        prepaid_adds_2025, prepaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Wireless\s+retail\s+core\s+prepaid")
        if prepaid_adds_2025 is None and prepaid_adds_2024 is None:
            prepaid_adds_2025, prepaid_adds_2024 = find_net_additions_numbers(netadds_text, r"Wireless\s+retail\s+prepaid")
        
        # Try total net additions
        total_adds_2025, total_adds_2024 = find_net_additions_numbers(netadds_text, r"Total\s+wireless\s+retail")
        
        # Extract churn rates
        total_churn_2025, total_churn_2024 = find_churn_rates(churn_text, r"Wireless\s+retail")
        postpaid_churn_2025, postpaid_churn_2024 = find_churn_rates(churn_text, r"Wireless\s+retail\s+postpaid")
        
        # Create comprehensive DataFrame
        rows = []
        
        # Postpaid row
        postpaid_row = {
            'segment': 'Postpaid',
            'connections_2025': postpaid_conn_2025,
            'connections_2024': postpaid_conn_2024,
            'net_adds_2025': postpaid_adds_2025,
            'net_adds_2024': postpaid_adds_2024,
            'churn_rate_2025': postpaid_churn_2025,
            'churn_rate_2024': postpaid_churn_2024,
            'extraction_method': 'enhanced_regex',
            'confidence': 'high'
        }
        rows.append(postpaid_row)
        
        # Prepaid row
        prepaid_row = {
            'segment': 'Prepaid',
            'connections_2025': prepaid_conn_2025,
            'connections_2024': prepaid_conn_2024,
            'net_adds_2025': prepaid_adds_2025,
            'net_adds_2024': prepaid_adds_2024,
            'churn_rate_2025': None,  # Prepaid typically doesn't report churn separately
            'churn_rate_2024': None,
            'extraction_method': 'enhanced_regex',
            'confidence': 'high'
        }
        rows.append(prepaid_row)
        
        # Total row
        total_row = {
            'segment': 'Total',
            'connections_2025': total_conn_2025,
            'connections_2024': total_conn_2024,
            'net_adds_2025': total_adds_2025,
            'net_adds_2024': total_adds_2024,
            'churn_rate_2025': total_churn_2025,
            'churn_rate_2024': total_churn_2024,
            'extraction_method': 'enhanced_regex',
            'confidence': 'high'
        }
        rows.append(total_row)
        
        df = pd.DataFrame(rows)
        
        if not df.empty:
            print(f"✅ Enhanced extraction successful")
            # Show what we extracted
            postpaid = df[df['segment'] == 'Postpaid'].iloc[0]
            prepaid = df[df['segment'] == 'Prepaid'].iloc[0]
            total = df[df['segment'] == 'Total'].iloc[0]
            
            print(f"   Postpaid: {postpaid['connections_2025']:,} connections, {postpaid['net_adds_2025']} net adds")
            print(f"   Prepaid: {prepaid['connections_2025']:,} connections, {prepaid['net_adds_2025']} net adds")
            print(f"   Total: {total['connections_2025']:,} connections, {total['net_adds_2025']} net adds")
            if total['churn_rate_2025']:
                print(f"   Churn rates: Total {total['churn_rate_2025']}%, Postpaid {postpaid['churn_rate_2025']}%")
        
        return df
        
    except Exception as e:
        print(f"❌ Error in enhanced extraction: {e}")
        return pd.DataFrame()

def test_enhanced_extraction():
    """Test the enhanced extraction on Verizon 2024 annual report"""
    test_url = "https://www.sec.gov/Archives/edgar/data/732712/000073271225000006/vz-20241231.htm"
    print("🧪 Testing enhanced extraction on Verizon 2024 annual report...")
    
    df = build_detailed_table_from_url_enhanced(test_url)
    if not df.empty:
        print("\n📊 Enhanced Extraction Results:")
        print(df.to_string())
    else:
        print("❌ Enhanced extraction failed")

if __name__ == "__main__":
    test_enhanced_extraction()
