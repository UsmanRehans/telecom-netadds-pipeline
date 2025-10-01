from openai import OpenAI
import json
import re
from typing import Dict, List, Optional, Tuple
from config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, MAX_TOKENS, SEC_HEADERS

# Set up OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_telecom_data_with_ai(url_or_content: str, carrier_name: str, report_date: str) -> Dict:
    """
    Extract telecom data using OpenAI GPT-4o
    
    Args:
        url_or_content: Either a URL to fetch HTML from, or raw HTML content
        carrier_name: Name of the carrier (VZ, T, TMUS)
        report_date: Report date (YYYY-MM-DD)
    
    Returns:
        Dictionary with extracted data
    """
    
    # Check if it's a URL or HTML content
    if url_or_content.startswith('http'):
        # It's a URL, fetch the HTML content
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Use headers from config
            response = requests.get(url_or_content, headers=SEC_HEADERS)
            soup = BeautifulSoup(response.content, 'html.parser')
            html_text = soup.get_text()
            
            # Focus on the financial data sections to reduce noise
            # Look for carrier-specific table headers
            financial_sections = []
            
            # For Verizon, look for "Operating Revenues and Selected Operating Statistics" table
            if carrier_name.upper() == 'VZ':
                verizon_table_match = re.search(r'Operating Revenues and Selected Operating Statistics.*?(?=Table of Contents|$)', html_text, re.IGNORECASE | re.DOTALL)
                if verizon_table_match:
                    financial_sections.append("VERIZON FINANCIAL TABLE:\n" + verizon_table_match.group(0))
            
            # For AT&T, look for "Item 2. Management's Discussion and Analysis" section
            elif carrier_name.upper() in ['T', 'AT&T']:
                att_section_match = re.search(r'Item 2\. Management.*?Discussion and Analysis.*?(?=Item 3|Table of Contents|$)', html_text, re.IGNORECASE | re.DOTALL)
                if att_section_match:
                    section_content = att_section_match.group(0)
                    
                    # Extract specific AT&T tables
                    att_tables = []
                    
                    # Subscribers table
                    subscribers_match = re.search(r'Subscribers.*?(?=Net Additions|Churn|$)', section_content, re.IGNORECASE | re.DOTALL)
                    if subscribers_match:
                        att_tables.append("AT&T SUBSCRIBERS TABLE:\n" + subscribers_match.group(0))
                    
                    # Net Additions table
                    netadds_match = re.search(r'Net Additions.*?(?=Churn|$)', section_content, re.IGNORECASE | re.DOTALL)
                    if netadds_match:
                        att_tables.append("AT&T NET ADDITIONS TABLE:\n" + netadds_match.group(0))
                    
                    # Churn data
                    churn_match = re.search(r'Churn.*?(?=Account|$)', section_content, re.IGNORECASE | re.DOTALL)
                    if churn_match:
                        att_tables.append("AT&T CHURN DATA:\n" + churn_match.group(0))
                    
                    if att_tables:
                        financial_sections.extend(att_tables)
                    else:
                        financial_sections.append("AT&T FINANCIAL SECTION:\n" + section_content)
            
            # For T-Mobile, look for exhibit documents first (much smaller and focused)
            elif carrier_name.upper() in ['TMUS', 'T-MOBILE']:
                tmus_tables = []
                
                # First, try to find exhibit documents (ex991.htm) which are much smaller
                exhibit_match = re.search(r'ex991\.htm', html_text, re.IGNORECASE)
                if exhibit_match:
                    # If we find an exhibit reference, try to construct the exhibit URL
                    # This is a simplified approach - in practice, we'd need to parse the full URL structure
                    print("Found exhibit reference, but would need to fetch exhibit document separately")
                
                # Look for the specific data patterns in the current document
                # 1. Look for customers data (end of period numbers)
                customers_match = re.search(r'Total branded customers.*?end of period.*?\d+.*?Branded postpaid phone customers.*?\d+.*?Branded prepaid customers.*?\d+', html_text, re.IGNORECASE | re.DOTALL)
                if customers_match:
                    tmus_tables.append("T-MOBILE CUSTOMERS TABLE:\n" + customers_match.group(0))
                
                # 2. Look for "Net Additions" title
                netadds_match = re.search(r'Net Additions.*?(?=Churn|$)', html_text, re.IGNORECASE | re.DOTALL)
                if netadds_match:
                    tmus_tables.append("T-MOBILE NET ADDITIONS TABLE:\n" + netadds_match.group(0))
                
                # 3. Look for "Churn" title
                churn_match = re.search(r'Churn.*?(?=Table of Contents|$)', html_text, re.IGNORECASE | re.DOTALL)
                if churn_match:
                    tmus_tables.append("T-MOBILE CHURN TABLE:\n" + churn_match.group(0))
                
                
                if tmus_tables:
                    financial_sections.extend(tmus_tables)
                else:
                    # Fallback to management discussion
                    tmus_section_match = re.search(r'Management.*?Discussion.*?Analysis.*?(?=Item 3|Table of Contents|$)', html_text, re.IGNORECASE | re.DOTALL)
                    if tmus_section_match:
                        financial_sections.append("T-MOBILE FINANCIAL SECTION:\n" + tmus_section_match.group(0))
            
            # Fallback: try to find the data in other common patterns
            if not financial_sections:
                # Look for the specific data table with connections and net additions
                data_table_match = re.search(r'Connections.*?Wireless retail postpaid.*?Net Additions.*?Churn Rate.*?Account Statistics', html_text, re.IGNORECASE | re.DOTALL)
                if data_table_match:
                    financial_sections.append("FINANCIAL DATA TABLE:\n" + data_table_match.group(0))
                else:
                    # Try individual sections
                    connections_data = re.search(r'Connections.*?Wireless retail postpaid.*?\d+.*?\d+.*?Wireless retail prepaid.*?\d+.*?\d+.*?Total wireless retail.*?\d+.*?\d+', html_text, re.IGNORECASE | re.DOTALL)
                    if connections_data:
                        financial_sections.append("CONNECTIONS DATA:\n" + connections_data.group(0))
                    
                    netadds_data = re.search(r'Net Additions.*?Wireless retail postpaid.*?\d+.*?\d+.*?Wireless retail prepaid.*?\d+.*?\d+.*?Total wireless retail.*?\d+.*?\d+', html_text, re.IGNORECASE | re.DOTALL)
                    if netadds_data:
                        financial_sections.append("NET ADDITIONS DATA:\n" + netadds_data.group(0))
                    
                    churn_data = re.search(r'Churn Rate.*?Wireless retail.*?\d+\.\d+.*?Wireless retail postpaid.*?\d+\.\d+', html_text, re.IGNORECASE | re.DOTALL)
                    if churn_data:
                        financial_sections.append("CHURN RATE DATA:\n" + churn_data.group(0))
            
            # Use focused sections if found, otherwise use full text
            if financial_sections:
                html_content = "\n\n".join(financial_sections)
            else:
                html_content = html_text
        except Exception as e:
            return {
                'carrier_name': carrier_name,
                'report_date': report_date,
                'extraction_method': 'ai_failed',
                'error': f'Failed to fetch HTML from URL: {e}',
                'postpaid_connections_current': None,
                'postpaid_connections_previous': None,
                'prepaid_connections_current': None,
                'prepaid_connections_previous': None,
                'total_connections_current': None,
                'total_connections_previous': None,
                'postpaid_net_additions_current': None,
                'postpaid_net_additions_previous': None,
                'prepaid_net_additions_current': None,
                'prepaid_net_additions_previous': None,
                'total_net_additions_current': None,
                'total_net_additions_previous': None,
                'total_churn_rate_current': None,
                'total_churn_rate_previous': None,
                'postpaid_churn_rate_current': None,
                'postpaid_churn_rate_previous': None,
                'extraction_confidence': 'low',
                'notes': f'Failed to fetch HTML from URL: {e}'
            }
    else:
        # It's already HTML content
        html_content = url_or_content
    
    # Create a comprehensive prompt for the AI
    prompt = f"""
    You are a financial data extraction expert. Extract comprehensive telecom data from this {carrier_name} SEC filing HTML content.

    IMPORTANT: Look for these specific data points in the financial tables:

    CONNECTIONS/SUBSCRIBERS ('000):
    - Postpaid connections/subscribers (current year and previous year)
    - Prepaid connections/subscribers (current year and previous year) 
    - Total connections/subscribers (current year and previous year)
    - Look for labels like "Postpaid", "Prepaid", "Total Mobility Subscribers", "Wireless retail postpaid", "Wireless retail prepaid", "Total wireless retail", "Branded postpaid", "Branded prepaid", "Total branded customers"

    NET ADDITIONS IN PERIOD ('000):
    - Postpaid net additions (current year and previous year)
    - Prepaid net additions (current year and previous year)
    - Total net additions (current year and previous year)
    - Look for labels like "Postpaid", "Prepaid", "Mobility Net Subscriber Additions", "Wireless retail postpaid", "Wireless retail prepaid", "Total wireless retail", "Branded postpaid", "Branded prepaid", "Total branded customers"

    CHURN RATES (%):
    - Total churn rate (current year and previous year)
    - Postpaid churn rate (current year and previous year)
    - Look for labels like "Churn", "Postpaid Churn", "Wireless retail", "Wireless retail postpaid"

    CARRIER-SPECIFIC NOTES:
    - VERIZON: Look for "Operating Revenues and Selected Operating Statistics" table
    - AT&T: Look for "Item 2. Management's Discussion and Analysis" section with "Subscribers" and "Mobility Net Additions" tables
    - T-MOBILE: Look for "Customers" table (end of period), "Net Customer Additions" table, and "Churn" table

    EXTRACTION RULES:
    1. Extract numbers as integers (remove commas, handle parentheses for negative numbers)
    2. For percentages, extract as decimal numbers (e.g., 1.58% = 1.58)
    3. For AT&T: "Postpaid" = postpaid, "Prepaid" = prepaid, "Mobility Net Subscriber Additions" = total net additions
    4. For Verizon: "Wireless retail postpaid" = postpaid, "Wireless retail prepaid" = prepaid, "Total wireless retail" = total
    5. For T-MOBILE: Handle both formats - older reports (2020-2021) use "Branded postpaid phone customers" + "Branded postpaid other customers" = postpaid, newer reports (2022+) use "Postpaid phone customers" + "Postpaid other customers" = postpaid
    6. For T-MOBILE: "Branded prepaid customers" (older) or "Prepaid customers" (newer) = prepaid, "Total branded customers" (older) or "Total customers" (newer) = total
    7. For T-MOBILE net additions: "Total branded postpaid customers" (older) or "Total postpaid customers" (newer) = postpaid net additions, "Branded prepaid customers" (older) or "Prepaid customers" (newer) = prepaid net additions
    8. For T-MOBILE churn: Look for "Postpaid phone churn" or "Branded postpaid churn" patterns
    7. For annual reports (10-K), these are annual totals, not quarterly
    8. For quarterly reports (10-Q), these are quarterly numbers
    9. If data is not found, return null for that field
    10. Look for both quarterly and annual data sections

    Return ONLY a valid JSON object with this exact structure:
    {{
        "postpaid_connections_current": <integer or null>,
        "postpaid_connections_previous": <integer or null>,
        "prepaid_connections_current": <integer or null>,
        "prepaid_connections_previous": <integer or null>,
        "total_connections_current": <integer or null>,
        "total_connections_previous": <integer or null>,
        "postpaid_net_additions_current": <integer or null>,
        "postpaid_net_additions_previous": <integer or null>,
        "prepaid_net_additions_current": <integer or null>,
        "prepaid_net_additions_previous": <integer or null>,
        "total_net_additions_current": <integer or null>,
        "total_net_additions_previous": <integer or null>,
        "total_churn_rate_current": <decimal or null>,
        "total_churn_rate_previous": <decimal or null>,
        "postpaid_churn_rate_current": <decimal or null>,
        "postpaid_churn_rate_previous": <decimal or null>,
        "extraction_confidence": "high|medium|low",
        "notes": "Any relevant notes about the extraction"
    }}

    HTML Content:
    {html_content[:10000]}  # Increased limit for more comprehensive extraction
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a financial data extraction expert. Extract telecom subscriber data from SEC filings with high accuracy."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        # Extract the JSON response
        ai_response = response.choices[0].message.content.strip()
        
        # Clean up the response to extract JSON
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            extracted_data = json.loads(json_str)
            
            # Add metadata
            extracted_data['carrier_name'] = carrier_name
            extracted_data['report_date'] = report_date
            extracted_data['extraction_method'] = 'ai'
            
            return extracted_data
        else:
            raise ValueError("No valid JSON found in AI response")
            
    except Exception as e:
        print(f"AI extraction failed: {e}")
        return {
            'carrier_name': carrier_name,
            'report_date': report_date,
            'extraction_method': 'ai_failed',
            'error': str(e),
            'postpaid_connections_current': None,
            'postpaid_connections_previous': None,
            'prepaid_connections_current': None,
            'prepaid_connections_previous': None,
            'postpaid_net_additions_current': None,
            'postpaid_net_additions_previous': None,
            'prepaid_net_additions_current': None,
            'prepaid_net_additions_previous': None,
            'extraction_confidence': 'low',
            'notes': f'AI extraction failed: {e}'
        }

def convert_ai_data_to_dataframe(ai_data: Dict) -> Optional['pd.DataFrame']:
    """
    Convert AI extraction results to the same format as our existing scrapers
    """
    import pandas as pd
    
    if ai_data.get('extraction_method') == 'ai_failed':
        return None
    
    # Create rows for postpaid, prepaid, and total
    rows = []
    
    # Postpaid row
    postpaid_row = {
        'segment': 'Postpaid',
        'connections_2025': ai_data.get('postpaid_connections_current'),
        'connections_2024': ai_data.get('postpaid_connections_previous'),
        'net_adds_2025': ai_data.get('postpaid_net_additions_current'),
        'net_adds_2024': ai_data.get('postpaid_net_additions_previous'),
        'churn_rate_2025': ai_data.get('postpaid_churn_rate_current'),
        'churn_rate_2024': ai_data.get('postpaid_churn_rate_previous'),
        'extraction_method': ai_data.get('extraction_method', 'ai'),
        'confidence': ai_data.get('extraction_confidence', 'unknown')
    }
    rows.append(postpaid_row)
    
    # Prepaid row
    prepaid_row = {
        'segment': 'Prepaid',
        'connections_2025': ai_data.get('prepaid_connections_current'),
        'connections_2024': ai_data.get('prepaid_connections_previous'),
        'net_adds_2025': ai_data.get('prepaid_net_additions_current'),
        'net_adds_2024': ai_data.get('prepaid_net_additions_previous'),
        'churn_rate_2025': None,  # Prepaid typically doesn't report churn separately
        'churn_rate_2024': None,
        'extraction_method': ai_data.get('extraction_method', 'ai'),
        'confidence': ai_data.get('extraction_confidence', 'unknown')
    }
    rows.append(prepaid_row)
    
    # Total row
    total_row = {
        'segment': 'Total',
        'connections_2025': ai_data.get('total_connections_current'),
        'connections_2024': ai_data.get('total_connections_previous'),
        'net_adds_2025': ai_data.get('total_net_additions_current'),
        'net_adds_2024': ai_data.get('total_net_additions_previous'),
        'churn_rate_2025': ai_data.get('total_churn_rate_current'),
        'churn_rate_2024': ai_data.get('total_churn_rate_previous'),
        'extraction_method': ai_data.get('extraction_method', 'ai'),
        'confidence': ai_data.get('extraction_confidence', 'unknown')
    }
    rows.append(total_row)
    
    return pd.DataFrame(rows)

def test_ai_extraction(url: str, carrier_name: str = "VZ") -> None:
    """
    Test the AI extraction on a single URL
    """
    import requests
    from bs4 import BeautifulSoup
    
    print(f"🤖 Testing AI extraction for {carrier_name}...")
    
    try:
        # Fetch the HTML content
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        html_content = soup.get_text()
        
        # Extract data using AI
        ai_data = extract_telecom_data_with_ai(html_content, carrier_name, "2024-12-31")
        
        print("✅ AI Extraction Results:")
        print(json.dumps(ai_data, indent=2))
        
        # Convert to DataFrame format
        df = convert_ai_data_to_dataframe(ai_data)
        if df is not None:
            print("\n📊 DataFrame Format:")
            print(df.to_string())
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    # Test with Verizon 2024 annual report
    test_url = "https://www.sec.gov/Archives/edgar/data/732712/000073271225000006/vz-20241231.htm"
    test_ai_extraction(test_url, "VZ")
