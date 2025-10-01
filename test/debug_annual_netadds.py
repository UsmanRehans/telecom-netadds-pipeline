import requests
import re
from bs4 import BeautifulSoup
from config import HEADERS

# Test both Verizon and AT&T annual reports
urls = [
    "https://www.sec.gov/Archives/edgar/data/732712/000073271225000006/vz-20241231.htm",  # Verizon 2024 annual
    "https://www.sec.gov/Archives/edgar/data/732717/000073271725000013/t-20241231.htm"   # AT&T 2024 annual
]

for i, url in enumerate(urls):
    carrier = "Verizon" if i == 0 else "AT&T"
    print(f"\n{'='*60}")
    print(f"CHECKING {carrier} 2024 ANNUAL REPORT FOR NET ADDITIONS")
    print(f"{'='*60}")
    
    response = requests.get(url, headers=HEADERS)
    html_content = response.text
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ')
    text = re.sub(r"\s+", " ", text)
    
    # Find net additions section
    netadds_start = text.lower().find('net additions')
    churn_start = text.lower().find('churn')
    
    if netadds_start != -1:
        if churn_start != -1 and churn_start > netadds_start:
            netadds_text = text[netadds_start:churn_start]
        else:
            netadds_text = text[netadds_start:netadds_start + 4000]
    else:
        netadds_text = text
    
    print(f"NET ADDITIONS SECTION (first 1500 chars):")
    print(netadds_text[:1500])
    print("\n" + "-"*40)
    
    # Look for specific patterns
    if carrier == "Verizon":
        patterns = [
            r"Wireless retail postpaid.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",
            r"Wireless retail prepaid.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",
            r"Total wireless retail.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))"
        ]
    else:  # AT&T
        patterns = [
            r"Postpaid.*?Phone.*?Net Additions.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",
            r"Prepaid.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",
            r"Mobility Net Subscriber Additions.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))"
        ]
    
    for j, pattern in enumerate(patterns):
        matches = re.findall(pattern, netadds_text, flags=re.IGNORECASE | re.DOTALL)
        print(f"Pattern {j+1}: {pattern}")
        print(f"Matches: {matches}")
        print()
