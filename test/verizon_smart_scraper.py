import pandas as pd
import requests
import re
import sys
import os
from bs4 import BeautifulSoup

# Add src directory to path so we can import config
sys.path.append(os.path.dirname(__file__))
from config import HEADERS


def extract_verizon_wireless_metrics(filing_url: str):
    """
    Extract wireless metrics from Verizon SEC filing HTML using smart pattern matching.
    
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
        
        html_content = response.text
        print(f"✅ Successfully fetched {len(html_content):,} characters of HTML")
        
        # Extract metrics using pattern matching
        metrics = extract_metrics_from_html(html_content)
        
        return metrics
        
    except Exception as e:
        print(f"❌ Error extracting metrics: {e}")
        return None


def extract_metrics_from_html(html_content: str):
    """
    Extract wireless metrics from HTML content using regex patterns.
    """
    metrics = {
        'connections': {},
        'net_additions': {},
        'extraction_method': 'verizon_smart_parser'
    }
    
    # Define patterns for connections (in thousands)
    connections_patterns = {
        'wireless_retail_total': r'Wireless retail\s+(\d{1,3}(?:,\d{3})*)',
        'wireless_retail_postpaid': r'Wireless retail postpaid\s+(\d{1,3}(?:,\d{3})*)',
        'wireless_retail_prepaid': r'Wireless retail core prepaid.*?(\d{1,3}(?:,\d{3})*)'
    }
    
    # Extract connections data
    for metric_name, pattern in connections_patterns.items():
        match = re.search(pattern, html_content)
        if match:
            value = int(match.group(1).replace(',', ''))
            metrics['connections'][metric_name] = value
            print(f"   ✅ {metric_name}: {value:,}")
        else:
            print(f"   ❌ {metric_name}: Not found")
    
    # Define patterns for net additions (in thousands)
    net_additions_patterns = {
        'total_wireless_retail': r'Total wireless retail\s+(\d+|\(\d+\))',
        'wireless_retail_postpaid': r'Wireless retail postpaid\s+(\d+|\(\d+\))',
        'wireless_retail_postpaid_phone': r'Wireless retail postpaid phone\s+(\d+|\(\d+\))',
        'wireless_retail_prepaid': r'Wireless retail core prepaid.*?(\d+|\(\d+\))'
    }
    
    # Extract net additions data
    for metric_name, pattern in net_additions_patterns.items():
        match = re.search(pattern, html_content)
        if match:
            value_str = match.group(1)
            # Handle negative numbers in parentheses
            if value_str.startswith('(') and value_str.endswith(')'):
                value = -int(value_str[1:-1])
            else:
                value = int(value_str)
            
            metrics['net_additions'][metric_name] = value
            print(f"   ✅ {metric_name}: {value:,}")
            else:
            print(f"   ❌ {metric_name}: Not found")
    
    return metrics


def test_verizon_scraper():
    """
    Test the Verizon scraper on the first Verizon filing.
    """
    print("🧪 Testing Verizon smart scraper...")
    
    # Read the filings CSV to get the first Verizon filing
    df = pd.read_csv("../data/filings.csv")
    
    # Find the first Verizon (VZ) filing
    vz_filings = df[df['carrier_name'] == 'VZ']
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return False
    
    first_vz_filing = vz_filings.iloc[0]
    filing_url = first_vz_filing['filing_url']
    quarter = first_vz_filing['reportDate']
    
    print(f"📱 Testing on Verizon filing for {quarter}")
    
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
        all_correct = True
        
        for key, expected in expected_connections.items():
            if key in metrics['connections']:
                actual = metrics['connections'][key]
                if actual == expected:
                    print(f"   ✅ {key}: {actual} (matches expected)")
                else:
                    print(f"   ❌ {key}: {actual} (expected {expected})")
                    all_correct = False
            else:
                print(f"   ❌ {key}: Not found")
                all_correct = False
        
        for key, expected in expected_net_additions.items():
            if key in metrics['net_additions']:
                actual = metrics['net_additions'][key]
                if actual == expected:
                    print(f"   ✅ {key}: {actual} (matches expected)")
                else:
                    print(f"   ❌ {key}: {actual} (expected {expected})")
                    all_correct = False
            else:
                print(f"   ❌ {key}: Not found")
                all_correct = False
        
        # Save results
        import json
        with open("../data/verizon_smart_scraper_results.json", 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n💾 Results saved to ../data/verizon_smart_scraper_results.json")
        
        return all_correct
    else:
        print("❌ No metrics extracted")
        return False


def extract_all_verizon_metrics():
    """
    Extract wireless metrics from all Verizon filings.
    """
    print("📱 Extracting metrics from all Verizon filings...")
    
    # Read the filings CSV
    df = pd.read_csv("../data/filings.csv")
    
    # Find all Verizon filings
    vz_filings = df[df['carrier_name'] == 'VZ']
    if vz_filings.empty:
        print("❌ No Verizon filings found")
        return
    
    print(f"📊 Found {len(vz_filings)} Verizon filings")
    
    all_results = []
    
    for idx, filing in vz_filings.iterrows():
        filing_url = filing['filing_url']
        quarter = filing['reportDate']
        form = filing['form']
        
        print(f"\n🔍 Processing {quarter} ({form})")
        
        # Extract metrics
        metrics = extract_verizon_wireless_metrics(filing_url)
        
        if metrics:
            # Add filing metadata
            result = {
                'quarter': quarter,
                'form': form,
                'filing_url': filing_url,
                **metrics
            }
            all_results.append(result)
            print(f"   ✅ Successfully extracted metrics")
        else:
            print(f"   ❌ Failed to extract metrics")
    
    # Save all results
    if all_results:
        results_df = pd.DataFrame(all_results)
        results_df.to_csv("../data/verizon_all_metrics.csv", index=False)
        print(f"\n💾 All Verizon metrics saved to ../data/verizon_all_metrics.csv")
        print(f"📊 Successfully processed {len(all_results)} out of {len(vz_filings)} filings")
    
    return all_results


if __name__ == "__main__":
    # Test on single filing first
    success = test_verizon_scraper()
    
    if success:
        print("\n🎉 Verizon scraper test completed successfully!")
        print("\n🚀 Now extracting from all Verizon filings...")
        extract_all_verizon_metrics()
    else:
        print("\n❌ Verizon scraper test failed!")
        sys.exit(1)