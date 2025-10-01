"""
Excel Forecast Data Extractor

This script extracts carrier data from the Navi US Wireless Forecast Model Excel file.
It identifies carriers and their associated metrics, then organizes the data into a 
structured format for analysis.
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path


class ForecastDataExtractor:
    """
    Extracts and organizes telecom carrier data from Excel forecast models.
    """
    
    # Common metric patterns to identify
    COMMON_METRICS = [
        'Subscribers',
        'Net additions',
        'M&A / adjustments',
        'Gross additions',
        'Churn',
        'Upgrade Rates',
        'Churn Rate',
        'Gross Losses',
        'SOGA of Winnable',
        'Gross Adds',
        'Winnable'
    ]
    
    # Carrier names to look for
    CARRIERS = [
        'AT&T',
        'Verizon',
        'T-Mobile',
        'USCellular',
        'UScellular',
        'Xfinity Mobile',
        'Spectrum Mobile'
    ]
    
    def __init__(self, file_path, sheet_name='Data'):
        """
        Initialize the extractor with file path and sheet name.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to extract (default: 'Data')
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.df = None
        self.quarters = []
        self.carrier_data = {}
        
    def load_data(self):
        """Load the Excel file and data sheet."""
        print(f"Loading Excel file: {self.file_path}")
        print(f"Reading sheet: {self.sheet_name}")
        
        # Read without headers to get raw structure
        self.df = pd.read_excel(
            self.file_path, 
            sheet_name=self.sheet_name, 
            header=None
        )
        
        print(f"Loaded data with {len(self.df)} rows and {len(self.df.columns)} columns")
        
    def extract_quarters(self):
        """Extract quarter labels from the header row."""
        # Row 2 (index 1) contains quarter labels like "Q1 2018", "Q2 2018", etc.
        quarter_row = self.df.iloc[1, :]
        
        self.quarters = []
        for idx, val in enumerate(quarter_row):
            if pd.notna(val) and isinstance(val, str) and 'Q' in val:
                self.quarters.append({
                    'column_index': idx,
                    'quarter': val,
                    'date': self.df.iloc[0, idx] if pd.notna(self.df.iloc[0, idx]) else None
                })
            elif pd.notna(val) and isinstance(val, datetime):
                # Handle datetime objects
                quarter_label = self.df.iloc[1, idx] if pd.notna(self.df.iloc[1, idx]) else f"Q{idx-1}"
                self.quarters.append({
                    'column_index': idx,
                    'quarter': quarter_label,
                    'date': val
                })
        
        print(f"Found {len(self.quarters)} quarters of data")
        if self.quarters:
            print(f"Date range: {self.quarters[0]['quarter']} to {self.quarters[-1]['quarter']}")
    
    def is_carrier_name(self, value):
        """Check if a value is a carrier name."""
        if pd.isna(value):
            return False
        value_str = str(value).strip()
        return value_str in self.CARRIERS
    
    def is_metric_name(self, value):
        """Check if a value is a metric name."""
        if pd.isna(value):
            return False
        value_str = str(value).strip()
        return value_str in self.COMMON_METRICS
    
    def extract_carrier_data(self):
        """
        Extract data for each carrier by identifying carrier sections
        and their associated metrics.
        """
        print("\nExtracting carrier data...")
        
        current_carrier = None
        carrier_start_row = None
        
        # Iterate through column B (index 1) to find carriers and metrics
        for row_idx in range(len(self.df)):
            cell_value = self.df.iloc[row_idx, 1]  # Column B
            
            # Check if this is a carrier name
            if self.is_carrier_name(cell_value):
                # Save previous carrier data if exists
                if current_carrier and carrier_start_row is not None:
                    self._extract_metrics_for_carrier(
                        current_carrier, 
                        carrier_start_row, 
                        row_idx
                    )
                
                # Start new carrier or add to existing
                current_carrier = str(cell_value).strip()
                carrier_start_row = row_idx
                
                # Initialize carrier data if not exists
                if current_carrier not in self.carrier_data:
                    self.carrier_data[current_carrier] = {
                        'metrics': {},
                        'start_row': row_idx
                    }
                    print(f"Found carrier: {current_carrier} at row {row_idx}")
                else:
                    print(f"Found additional section for {current_carrier} at row {row_idx}")
        
        # Don't forget the last carrier
        if current_carrier and carrier_start_row is not None:
            self._extract_metrics_for_carrier(
                current_carrier, 
                carrier_start_row, 
                len(self.df)
            )
    
    def _extract_metrics_for_carrier(self, carrier, start_row, end_row):
        """
        Extract all metrics for a specific carrier between start_row and end_row.
        """
        print(f"  Extracting metrics for {carrier} (rows {start_row}-{end_row})")
        
        for row_idx in range(start_row + 1, end_row):
            metric_name = self.df.iloc[row_idx, 1]  # Column B
            
            if pd.isna(metric_name):
                continue
                
            metric_name_str = str(metric_name).strip()
            
            # Check if this is a metric or another carrier
            if self.is_carrier_name(metric_name):
                break
            
            # Extract values for this metric across all quarters
            metric_values = []
            for quarter_info in self.quarters:
                col_idx = quarter_info['column_index']
                value = self.df.iloc[row_idx, col_idx]
                
                # Convert to appropriate type
                if pd.notna(value):
                    try:
                        # Try to convert to float
                        value = float(value)
                    except (ValueError, TypeError):
                        # Keep as string if not numeric
                        value = str(value)
                else:
                    value = None
                
                metric_values.append({
                    'quarter': quarter_info['quarter'],
                    'date': quarter_info['date'],
                    'value': value
                })
            
            # Only add if we have some data
            if any(v['value'] is not None for v in metric_values):
                # If metric already exists, check if the new data has more values
                if metric_name_str in self.carrier_data[carrier]['metrics']:
                    existing_count = len([v for v in self.carrier_data[carrier]['metrics'][metric_name_str] if v['value'] is not None])
                    new_count = len([v for v in metric_values if v['value'] is not None])
                    
                    # Keep the version with more data
                    if new_count > existing_count:
                        self.carrier_data[carrier]['metrics'][metric_name_str] = metric_values
                        print(f"    - {metric_name_str}: {new_count} values (updated)")
                    else:
                        print(f"    - {metric_name_str}: keeping existing ({existing_count} values)")
                else:
                    self.carrier_data[carrier]['metrics'][metric_name_str] = metric_values
                    print(f"    - {metric_name_str}: {len([v for v in metric_values if v['value'] is not None])} values")
    
    def export_to_json(self, output_path=None):
        """
        Export the extracted data to JSON format.
        
        Args:
            output_path: Path for the output JSON file
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'forecast_data_extracted_{timestamp}.json'
        
        # Convert datetime objects to strings for JSON serialization
        export_data = {
            'extraction_date': datetime.now().isoformat(),
            'source_file': str(self.file_path),
            'sheet_name': self.sheet_name,
            'quarters': [
                {
                    'quarter': str(q['quarter']),
                    'date': q['date'].isoformat() if isinstance(q['date'], datetime) else (str(q['date']) if q['date'] is not None else None)
                }
                for q in self.quarters
            ],
            'carriers': {}
        }
        
        for carrier, data in self.carrier_data.items():
            export_data['carriers'][carrier] = {
                'metrics': {}
            }
            
            for metric, values in data['metrics'].items():
                export_data['carriers'][carrier]['metrics'][metric] = [
                    {
                        'quarter': str(v['quarter']) if v['quarter'] is not None else None,
                        'date': v['date'].isoformat() if isinstance(v['date'], datetime) else (str(v['date']) if v['date'] is not None else None),
                        'value': v['value']
                    }
                    for v in values
                ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData exported to: {output_path}")
        return output_path
    
    def export_to_csv(self, output_path=None):
        """
        Export the extracted data to CSV format (flattened).
        
        Args:
            output_path: Path for the output CSV file
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'forecast_data_extracted_{timestamp}.csv'
        
        # Flatten the data for CSV export
        rows = []
        for carrier, data in self.carrier_data.items():
            for metric, values in data['metrics'].items():
                for value_data in values:
                    rows.append({
                        'carrier': carrier,
                        'metric': metric,
                        'quarter': value_data['quarter'],
                        'date': value_data['date'].isoformat() if isinstance(value_data['date'], datetime) else str(value_data['date']),
                        'value': value_data['value']
                    })
        
        df_export = pd.DataFrame(rows)
        df_export.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"Data exported to: {output_path}")
        return output_path
    
    def get_carrier_summary(self):
        """Print a summary of extracted data."""
        print("\n" + "="*80)
        print("EXTRACTION SUMMARY")
        print("="*80)
        print(f"Source File: {self.file_path}")
        print(f"Sheet: {self.sheet_name}")
        print(f"Total Quarters: {len(self.quarters)}")
        print(f"Total Carriers: {len(self.carrier_data)}")
        print("\nCarriers and Metrics:")
        
        for carrier, data in self.carrier_data.items():
            print(f"\n{carrier}:")
            for metric in data['metrics'].keys():
                print(f"  - {metric}")
        
        print("\n" + "="*80)
    
    def run(self, export_json=True, export_csv=True):
        """
        Run the complete extraction pipeline.
        
        Args:
            export_json: Whether to export to JSON (default: True)
            export_csv: Whether to export to CSV (default: True)
        """
        self.load_data()
        self.extract_quarters()
        self.extract_carrier_data()
        self.get_carrier_summary()
        
        output_files = []
        
        if export_json:
            json_file = self.export_to_json()
            output_files.append(json_file)
        
        if export_csv:
            csv_file = self.export_to_csv()
            output_files.append(csv_file)
        
        return output_files


def main():
    """Main execution function."""
    # Path to the Excel file
    excel_file = 'data/Navi US Wireless Forecast Model_9.23.25.xlsx'
    
    # Check if file exists
    if not Path(excel_file).exists():
        print(f"Error: File not found: {excel_file}")
        print("\nPlease provide the correct path to your Excel file.")
        return
    
    # Create extractor instance
    extractor = ForecastDataExtractor(excel_file, sheet_name='Data')
    
    # Run extraction and export
    print("Starting data extraction...")
    print("="*80)
    
    output_files = extractor.run(export_json=True, export_csv=True)
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE!")
    print("="*80)
    print(f"Generated {len(output_files)} output files:")
    for file in output_files:
        print(f"  - {file}")
    print("\nYou can now use this data for further analysis.")


if __name__ == "__main__":
    main()

