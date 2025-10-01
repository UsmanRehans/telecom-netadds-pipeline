import sys
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

# Add src directory to path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import HEADERS


def extract_verizon_wireless_metrics(filing_url: str):
    """
    Extract wireless metrics from Verizon SEC filing HTML.
    
    Args:
        filing_url: URL to the Verizon SEC filing
        
    Returns:
        Dictionary with extracted wireless metrics
    """
    print(f"🔍 Extracting Verizon wireless metrics from: {filing_url}")
    
    try:
        # Fetch the HTML content
        response = requests.get(filing_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the table with "Operating Revenues and Selected Operating Statistics"
        target_table = None
        tables = soup.find_all('table')
        
        for table in tables:
            table_text = table.get_text()
            if "Operating Revenues and Selected Operating Statistics" in table_text:
                target_table = table
                break
        
        if not target_table:
            print("❌ Could not find the Operating Statistics table")
            return None
        
        print("✅ Found Operating Statistics table")
        
        # Extract data from the table
        metrics = extract_metrics_from_table(target_table)
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error extracting metrics: {e}")
        return None


def extract_metrics_from_table(table):
    """
    Extract wireless metrics from the Operating Statistics table.
    """
    metrics = {
        'connections': {},
        'net_additions': {},
        'extraction_method': 'verizon_table_parser'
    }
    
    # Get the table text for pattern matching
    table_text = table.get_text()
    
    # Extract Connections data (in thousands)
    connections_patterns = {
        'wireless_retail_total': r'Wireless retail\s+(\d{1,3}(?:,\d{3})*)',
        'wireless_retail_postpaid': r'Wireless retail postpaid\s+(\d{1,3}(?:,\d{3})*)',
        'wireless_retail_prepaid': r'Wireless retail core prepaid.*?(\d{1,3}(?:,\d{3})*)'
    }
    
    for metric_name, pattern in connections_patterns.items():
        match = re.search(pattern, table_text)
        if match:
            value = int(match.group(1).replace(',', ''))
            metrics['connections'][metric_name] = value
            print(f"   ✅ {metric_name}: {value:,}")
    
    # Extract Net Additions data (in thousands)
    net_additions_patterns = {
        'total_wireless_retail': r'Total wireless retail\s+(\d+|\(\d+\))',
        'wireless_retail_postpaid': r'Wireless retail postpaid\s+(\d+|\(\d+\))',
        'wireless_retail_postpaid_phone': r'Wireless retail postpaid phone\s+(\d+|\(\d+\))',
        'wireless_retail_prepaid': r'Wireless retail core prepaid.*?(\d+|\(\d+\))'
    }
    
    for metric_name, pattern in net_additions_patterns.items():
        match = re.search(pattern, table_text)
        if match:
            value_str = match.group(1)
            # Handle negative numbers in parentheses
            if value_str.startswith('(') and value_str.endswith(')'):
                value = -int(value_str[1:-1])
            else:
                value = int(value_str)
            
            metrics['net_additions'][metric_name] = value
            print(f"   ✅ {metric_name}: {value:,}")
    
    return metrics


def test_verizon_scraper():
    """
    Test the Verizon scraper on the first Verizon filing.
    """
    print("🧪 Testing Verizon scraper...")
    
    # Read the filings CSV to get the first Verizon filing
    df = pd.read_csv("../data/filings.csv")
    
    # Find the first Verizon (VZ) filing
    vz_filings = df[df['carrier_name'] == 'VZ']
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return
    
    first_vz_filing = vz_filings.iloc[0]
    filing_url = first_vz_filing['filing_url']
    quarter = first_vz_filing['reportDate']
    
    print(f"📱 Testing on Verizon filing for {quarter}")
    print(f"🔗 URL: {filing_url}")
    
    # Extract metrics
    metrics = extract_verizon_wireless_metrics(filing_url)
    
    if metrics:
        print(f"\n📊 Extracted Metrics:")
        print(f"   Connections: {metrics['connections']}")
        print(f"   Net Additions: {metrics['net_additions']}")
        
        # Expected values from your data:
        expected_connections = {
            'wireless_retail_total': 115189,
            'wireless_retail_postpaid': 94948,
            'wireless_retail_prepaid': 19017
        }
        
        expected_net_additions = {
            'total_wireless_retail': 112,
            'wireless_retail_postpaid': 90,
            'wireless_retail_postpaid_phone': -51,
            'wireless_retail_prepaid': 50
        }
        
        # Validate results
        print(f"\n✅ Validation:")
        for key, expected in expected_connections.items():
            if key in metrics['connections']:
                actual = metrics['connections'][key]
                if actual == expected:
                    print(f"   ✅ {key}: {actual} (matches expected)")
                else:
                    print(f"   ❌ {key}: {actual} (expected {expected})")
            else:
                print(f"   ❌ {key}: Not found")
        
        for key, expected in expected_net_additions.items():
            if key in metrics['net_additions']:
                actual = metrics['net_additions'][key]
                if actual == expected:
                    print(f"   ✅ {key}: {actual} (matches expected)")
                else:
                    print(f"   ❌ {key}: {actual} (expected {expected})")
            else:
                print(f"   ❌ {key}: Not found")
        
        # Save results
        import json
        with open("../data/verizon_test_results.json", 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n💾 Results saved to ../data/verizon_test_results.json")
        
        return True
    else:
        print("❌ No metrics extracted")
        return False


if __name__ == "__main__":
    success = test_verizon_scraper()
    if success:
        print("\n🎉 Verizon scraper test completed successfully!")
    else:
        print("\n❌ Verizon scraper test failed!")
        sys.exit(1)
