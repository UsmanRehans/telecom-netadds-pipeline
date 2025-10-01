"""
Excel AI Extractor for Telecom Data
Extracts and organizes telecom data from Excel files using AI
"""

import pandas as pd
import openpyxl
import os
import re
from typing import Dict, List, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, MAX_TOKENS
import json


class ExcelAIExtractor:
    def __init__(self, excel_file_path: str):
        """
        Initialize the Excel AI Extractor
        
        Args:
            excel_file_path: Path to the Excel file
        """
        self.excel_file_path = excel_file_path
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.workbook = None
        self.data_sheet = None
        
    def find_data_sheet(self) -> Optional[str]:
        """
        Find the sheet containing telecom data by looking for carrier names
        and metric keywords in sheet names and content
        
        Returns:
            Name of the data sheet or None if not found
        """
        try:
            self.workbook = openpyxl.load_workbook(self.excel_file_path, data_only=True)
            sheet_names = self.workbook.sheetnames
            
            print(f"📊 Found {len(sheet_names)} sheets: {sheet_names}")
            
            # Look for sheets that might contain data
            potential_sheets = []
            for sheet_name in sheet_names:
                sheet = self.workbook[sheet_name]
                
                # Check if sheet has substantial data (more than 50 rows)
                if sheet.max_row > 50:
                    potential_sheets.append(sheet_name)
                    
                # Look for carrier names in sheet names
                if any(carrier in sheet_name.lower() for carrier in ['data', 'wireless', 'telecom', 'carrier']):
                    potential_sheets.append(sheet_name)
            
            print(f"🔍 Potential data sheets: {potential_sheets}")
            
            # Analyze each potential sheet
            for sheet_name in potential_sheets:
                if self._analyze_sheet_content(sheet_name):
                    print(f"✅ Found data sheet: {sheet_name}")
                    return sheet_name
            
            # If no clear data sheet found, try the first substantial sheet
            if potential_sheets:
                print(f"⚠️ Using first substantial sheet: {potential_sheets[0]}")
                return potential_sheets[0]
                
            return None
            
        except Exception as e:
            print(f"❌ Error finding data sheet: {e}")
            return None
    
    def _analyze_sheet_content(self, sheet_name: str) -> bool:
        """
        Analyze sheet content to determine if it contains telecom data
        
        Args:
            sheet_name: Name of the sheet to analyze
            
        Returns:
            True if sheet contains telecom data, False otherwise
        """
        try:
            sheet = self.workbook[sheet_name]
            
            # Sample cells from A1 to A104 and B1 to B50
            sample_data = []
            for row in range(1, min(105, sheet.max_row + 1)):
                cell_a = sheet[f'A{row}'].value
                if cell_a and str(cell_a).strip():
                    sample_data.append(str(cell_a).strip())
            
            # Check for carrier names and metrics
            data_text = ' '.join(sample_data)
            
            # Look for telecom indicators
            telecom_indicators = [
                'att', 'verizon', 'tmobile', 'subscribers', 'net additions',
                'churn', 'gross additions', 'upgrade', 'm&a', 'adjustments'
            ]
            
            matches = sum(1 for indicator in telecom_indicators 
                         if indicator.lower() in data_text.lower())
            
            # If we find 3+ telecom indicators, likely a data sheet
            is_telecom_sheet = matches >= 3
            
            if is_telecom_sheet:
                print(f"📱 Sheet '{sheet_name}' contains telecom data ({matches} indicators found)")
            
            return is_telecom_sheet
            
        except Exception as e:
            print(f"❌ Error analyzing sheet {sheet_name}: {e}")
            return False
    
    def extract_data_with_ai(self, sheet_name: str) -> Dict[str, Any]:
        """
        Extract telecom data using AI analysis
        
        Args:
            sheet_name: Name of the sheet to extract data from
            
        Returns:
            Dictionary containing extracted telecom data
        """
        try:
            sheet = self.workbook[sheet_name]
            
            # Extract data from A1:A104 and B1:B104
            raw_data = []
            for row in range(1, min(105, sheet.max_row + 1)):
                cell_a = sheet[f'A{row}'].value
                cell_b = sheet[f'B{row}'].value
                
                if cell_a or cell_b:
                    raw_data.append({
                        'row': row,
                        'column_a': str(cell_a).strip() if cell_a else '',
                        'column_b': str(cell_b).strip() if cell_b else ''
                    })
            
            # Extract column headers (starting from column C)
            headers = []
            for col in range(3, min(20, sheet.max_column + 1)):  # C to S
                header_cell = sheet.cell(row=1, column=col).value
                if header_cell:
                    headers.append(str(header_cell).strip())
                else:
                    break
            
            print(f"📊 Found {len(headers)} data columns: {headers}")
            
            # Prepare data for AI analysis
            data_text = self._prepare_data_for_ai(raw_data, headers)
            
            # Use AI to extract and organize the data
            ai_response = self._call_ai_for_extraction(data_text)
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Error extracting data with AI: {e}")
            return {'error': str(e)}
    
    def _prepare_data_for_ai(self, raw_data: List[Dict], headers: List[str]) -> str:
        """
        Prepare raw Excel data for AI analysis
        
        Args:
            raw_data: Raw data from Excel
            headers: Column headers
            
        Returns:
            Formatted text for AI analysis
        """
        # Create a structured text representation
        data_text = f"""
EXCEL TELECOM DATA EXTRACTION

Column Headers: {', '.join(headers)}

Row Data (A1:A104 and B1:B104):
"""
        
        for item in raw_data:
            if item['column_a'] or item['column_b']:
                data_text += f"Row {item['row']}: A='{item['column_a']}' | B='{item['column_b']}'\n"
        
        return data_text
    
    def _call_ai_for_extraction(self, data_text: str) -> Dict[str, Any]:
        """
        Call AI to extract and organize telecom data
        
        Args:
            data_text: Formatted data text for analysis
            
        Returns:
            AI response with extracted data
        """
        try:
            prompt = f"""
You are analyzing Excel data for US wireless telecom carriers (AT&T and Verizon).

Based on the Excel data below, extract and organize the following metrics for each carrier:

REQUIRED METRICS:
- Subscribers (current/ending subscribers)
- Net additions (quarterly net subscriber additions)
- M&A / adjustments (merger & acquisition adjustments)
- Gross additions (new subscriber additions)
- Churn (customer churn rate)
- Upgrade Rates (device upgrade rates)

EXTRACTION RULES:
1. Look for AT&T and Verizon data sections
2. Find the 6 metrics listed above for each carrier
3. Extract quarterly data from Q1 2018 onwards
4. Handle different naming conventions (e.g., "Net Additions" vs "Net additions")
5. Convert percentages to decimal format (e.g., 1.5% → 0.015)
6. Handle missing data with null values
7. Organize data by carrier and metric

OUTPUT FORMAT (JSON):
{{
    "extraction_success": true/false,
    "carriers": {{
        "AT&T": {{
            "subscribers": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "net_additions": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "ma_adjustments": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "gross_additions": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "churn": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "upgrade_rates": {{"Q1_2018": value, "Q2_2018": value, ...}}
        }},
        "Verizon": {{
            "subscribers": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "net_additions": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "ma_adjustments": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "gross_additions": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "churn": {{"Q1_2018": value, "Q2_2018": value, ...}},
            "upgrade_rates": {{"Q1_2018": value, "Q2_2018": value, ...}}
        }}
    }},
    "confidence": "high/medium/low",
    "notes": "Any extraction notes or issues"
}}

EXCEL DATA TO ANALYZE:
{data_text}
"""

            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting and organizing financial data from Excel files. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content.strip()
            
            # Handle markdown code blocks
            if ai_content.startswith('```json'):
                ai_content = ai_content[7:]
            if ai_content.startswith('```'):
                ai_content = ai_content[3:]
            if ai_content.endswith('```'):
                ai_content = ai_content[:-3]
            
            ai_data = json.loads(ai_content)
            ai_data['extraction_method'] = 'ai_success'
            
            return ai_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return {
                'extraction_method': 'ai_failed',
                'error': f'JSON parsing error: {e}',
                'raw_response': ai_content
            }
        except Exception as e:
            print(f"❌ AI extraction error: {e}")
            return {
                'extraction_method': 'ai_failed',
                'error': str(e)
            }
    
    def save_to_csv(self, ai_data: Dict[str, Any], output_path: str = "data/excel_extracted_data.csv"):
        """
        Save extracted data to CSV format
        
        Args:
            ai_data: AI extracted data
            output_path: Path to save CSV file
        """
        try:
            if ai_data.get('extraction_method') != 'ai_success':
                print(f"❌ Cannot save data - extraction failed: {ai_data.get('error', 'Unknown error')}")
                return
            
            # Create DataFrame from AI data
            rows = []
            carriers = ai_data.get('carriers', {})
            
            for carrier_name, carrier_data in carriers.items():
                for metric_name, metric_data in carrier_data.items():
                    for period, value in metric_data.items():
                        rows.append({
                            'carrier': carrier_name,
                            'metric': metric_name,
                            'period': period,
                            'value': value
                        })
            
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(output_path, index=False)
                print(f"💾 Data saved to {output_path}")
                print(f"📊 Extracted {len(rows)} data points")
            else:
                print("❌ No data to save")
                
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
    
    def process_excel_file(self, output_path: str = "data/excel_extracted_data.csv") -> Dict[str, Any]:
        """
        Main method to process the Excel file
        
        Args:
            output_path: Path to save extracted data
            
        Returns:
            Extracted data dictionary
        """
        print(f"🚀 Starting Excel AI extraction for: {self.excel_file_path}")
        
        # Find data sheet
        data_sheet = self.find_data_sheet()
        if not data_sheet:
            print("❌ Could not find data sheet")
            return {'error': 'Data sheet not found'}
        
        # Extract data with AI
        ai_data = self.extract_data_with_ai(data_sheet)
        
        # Save to CSV
        self.save_to_csv(ai_data, output_path)
        
        return ai_data


def main():
    """Main function to run the Excel AI extractor"""
    
    # Look for Excel files in the current directory
    excel_files = []
    for file in os.listdir('.'):
        if file.endswith(('.xlsx', '.xls')) and 'wireless' in file.lower():
            excel_files.append(file)
    
    if not excel_files:
        print("❌ No Excel files found containing 'wireless' in the filename")
        print("📁 Available Excel files:")
        for file in os.listdir('.'):
            if file.endswith(('.xlsx', '.xls')):
                print(f"   - {file}")
        return
    
    # Use the first matching file
    excel_file = excel_files[0]
    print(f"📊 Processing Excel file: {excel_file}")
    
    # Create extractor and process
    extractor = ExcelAIExtractor(excel_file)
    result = extractor.process_excel_file()
    
    if result.get('extraction_method') == 'ai_success':
        print("✅ Excel extraction completed successfully!")
        print(f"📈 Confidence: {result.get('confidence', 'unknown')}")
    else:
        print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()

