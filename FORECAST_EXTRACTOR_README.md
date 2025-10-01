# Forecast Data Extractor

A Python tool to extract and organize telecom carrier data from Excel forecast models.

## Overview

This script extracts carrier metrics (like Subscribers, Net additions, Churn, etc.) from the Navi US Wireless Forecast Model Excel file and organizes the data into structured JSON and CSV formats for easy analysis.

## Features

- **Automatic Sheet Detection**: Finds the "Data" sheet in any Excel file
- **Multi-Carrier Support**: Extracts data for all major carriers:
  - AT&T
  - Verizon
  - T-Mobile
  - USCellular
  - Xfinity Mobile
  - Spectrum Mobile

- **Comprehensive Metrics**: Captures all available metrics including:
  - Subscribers
  - Net additions
  - M&A / adjustments
  - Gross additions
  - Churn / Churn Rate
  - Upgrade Rates
  - Gross Losses

- **Multiple Output Formats**:
  - **JSON**: Hierarchical structure (carriers → metrics → quarters)
  - **CSV**: Flat format for easy import into databases or analysis tools

- **Smart Duplicate Handling**: Automatically consolidates data when the same carrier appears multiple times

## Installation

Ensure you have the required dependencies:

```bash
pip install pandas openpyxl
```

## Usage

### Basic Usage

Simply run the script:

```bash
python extract_forecast_data.py
```

This will:
1. Load the Excel file from `data/Navi US Wireless Forecast Model_9.23.25.xlsx`
2. Extract all carrier data from the "Data" sheet
3. Generate two output files:
   - `forecast_data_extracted_[timestamp].json`
   - `forecast_data_extracted_[timestamp].csv`

### Using as a Module

You can also import and use the `ForecastDataExtractor` class in your own scripts:

```python
from extract_forecast_data import ForecastDataExtractor

# Create extractor instance
extractor = ForecastDataExtractor(
    file_path='path/to/your/file.xlsx',
    sheet_name='Data'
)

# Run extraction
output_files = extractor.run(export_json=True, export_csv=True)

# Or access the data programmatically
extractor.load_data()
extractor.extract_quarters()
extractor.extract_carrier_data()

# Access extracted data
for carrier, data in extractor.carrier_data.items():
    print(f"Carrier: {carrier}")
    for metric, values in data['metrics'].items():
        print(f"  {metric}: {len(values)} quarters")
```

### Customization

You can customize the extractor to work with different files or sheets:

```python
# Use a different file
extractor = ForecastDataExtractor(
    file_path='data/another_forecast.xlsx',
    sheet_name='Data'
)

# Export to specific file names
extractor.run()
extractor.export_to_json('custom_output.json')
extractor.export_to_csv('custom_output.csv')
```

## Output Format

### CSV Format

The CSV output is a flat, normalized structure:

```csv
carrier,metric,quarter,date,value
AT&T,Subscribers,2018-03-31,2018-03-31T00:00:00,63043.0
AT&T,Subscribers,2018-06-30,2018-06-30T00:00:00,62930.0
...
```

Columns:
- `carrier`: Carrier name (AT&T, Verizon, etc.)
- `metric`: Metric name (Subscribers, Net additions, etc.)
- `quarter`: Quarter date
- `date`: ISO format date
- `value`: Numeric value

### JSON Format

The JSON output is hierarchical and structured:

```json
{
  "extraction_date": "2025-10-01T06:39:22.920146",
  "source_file": "data/Navi US Wireless Forecast Model_9.23.25.xlsx",
  "sheet_name": "Data",
  "quarters": [
    {
      "quarter": "Q1 2018",
      "date": "2018-03-31T00:00:00"
    },
    ...
  ],
  "carriers": {
    "AT&T": {
      "metrics": {
        "Subscribers": [
          {
            "quarter": "2018-03-31 00:00:00",
            "date": "2018-03-31T00:00:00",
            "value": 63043.0
          },
          ...
        ],
        "Net additions": [...],
        ...
      }
    },
    "Verizon": {...},
    ...
  }
}
```

## Data Extraction Details

### How It Works

1. **Load Excel File**: Reads the specified sheet without headers to preserve structure
2. **Extract Quarters**: Identifies quarter labels from row 2 (Q1 2018, Q2 2018, etc.)
3. **Identify Carriers**: Scans column B for known carrier names
4. **Extract Metrics**: For each carrier, identifies associated metrics and extracts values across all quarters
5. **Consolidate Duplicates**: When the same carrier appears multiple times, keeps the version with the most data
6. **Export**: Converts to JSON and CSV formats

### Data Structure in Excel

The script expects the following structure in the Excel sheet:

- **Row 1**: Dates (optional)
- **Row 2**: Quarter labels (Q1 2018, Q2 2018, etc.)
- **Column A**: Empty (row identifiers)
- **Column B**: Carrier names and metric names
- **Column C onwards**: Quarterly data values

Example structure:
```
Row 1:  [empty]  [empty]     2018-03-31    2018-06-30    ...
Row 2:  [empty]  [empty]     Q1 2018       Q2 2018       ...
Row 7:  [empty]  AT&T        [empty]       [empty]       ...
Row 8:  [empty]  Subscribers 63043         62930         ...
Row 9:  [empty]  Net adds    -53           49            ...
...
```

## Results Summary

For the Navi US Wireless Forecast Model (9.23.25), the script extracts:

- **6 major carriers**: AT&T, Verizon, T-Mobile, USCellular, Xfinity Mobile, Spectrum Mobile
- **49 quarters**: From Q1 2018 to Q1 2030
- **1,960 total data points** across all carriers and metrics

### Metrics by Carrier

- **AT&T**: 8 metrics (Subscribers, Net additions, M&A/adjustments, Gross additions, Churn, Upgrade Rates, Churn Rate, Gross Losses)
- **Verizon**: 7 metrics (Subscribers, Net additions, M&A/adjustments, Gross additions, Churn, Upgrade Rates, Gross Losses)
- **T-Mobile**: 7 metrics (Subscribers, Net additions, M&A/adjustments, Gross additions, Churn, Upgrade Rates, Gross Losses)
- **USCellular**: 6 metrics (Subscribers, Net additions, M&A/adjustments, Gross additions, Churn, Gross Losses)
- **Xfinity Mobile**: 6 metrics (Subscribers, Net additions, M&A/adjustments, Gross additions, Churn, Gross Losses)
- **Spectrum Mobile**: 6 metrics (Subscribers, Net additions, M&A/adjustments, Gross additions, Churn, Gross Losses)

## Troubleshooting

### File Not Found

If you get a "File not found" error, make sure:
1. The Excel file is in the correct location (`data/` directory)
2. The filename matches exactly (including spaces and special characters)
3. You're running the script from the project root directory

### No Data Extracted

If no data is extracted:
1. Check that the sheet name is correct (default is "Data")
2. Verify the Excel structure matches the expected format
3. Check that carrier names match the expected values in the `CARRIERS` list

### Incorrect Data

If the extracted data seems incorrect:
1. Open the Excel file and verify the structure
2. Check the console output for which rows are being processed
3. Verify that metrics are properly labeled in column B

## Extending the Script

### Adding New Carriers

To support additional carriers, add them to the `CARRIERS` list:

```python
CARRIERS = [
    'AT&T',
    'Verizon',
    'T-Mobile',
    # Add your new carrier here
    'New Carrier Name'
]
```

### Adding New Metrics

To support additional metrics, add them to the `COMMON_METRICS` list:

```python
COMMON_METRICS = [
    'Subscribers',
    'Net additions',
    # Add your new metric here
    'New Metric Name'
]
```

### Custom Processing

You can add custom processing logic in the `_extract_metrics_for_carrier` method or create new methods:

```python
def custom_analysis(self):
    """Perform custom analysis on extracted data."""
    for carrier, data in self.carrier_data.items():
        # Your custom logic here
        pass
```

## Use Cases

This tool is particularly useful for:

- **Financial Analysis**: Analyzing subscriber trends and net additions
- **Competitive Intelligence**: Comparing metrics across carriers
- **Data Science**: Preparing data for machine learning models
- **Reporting**: Generating automated reports from forecast data
- **Forecasting**: Using historical data for future predictions

## License

This script is provided as-is for internal use.

## Contact

For questions or issues, please contact the development team.


