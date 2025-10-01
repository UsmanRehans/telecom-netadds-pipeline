import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.sec.gov/Archives/edgar/data/732712/000073271225000006/vz-20241231.htm'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
src_text = soup.get_text()

# Find the net additions section
netadds_match = re.search(r'Net Additions in Period.*?(?=Churn Rate|Account Statistics|$)', src_text, re.IGNORECASE | re.DOTALL)
netadds_text = netadds_match.group(0) if netadds_match else ''

print("Net Additions section:")
print(netadds_text[:2000])
print("\n" + "="*50 + "\n")

# Look for prepaid patterns
prepaid_patterns = [
    r"Wireless\s+retail\s+core\s+prepaid.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",
    r"Wireless\s+retail\s+prepaid.*?(\d+|\(\d+\)).*?(\d+|\(\d+\))",
]

for i, pattern in enumerate(prepaid_patterns):
    matches = re.findall(pattern, netadds_text, flags=re.IGNORECASE | re.DOTALL)
    print(f"Pattern {i+1} matches: {matches}")
