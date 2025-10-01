# Quick Start Guide

## Overview

This toolset extracts telecom carrier data from Excel forecast models and provides powerful analysis capabilities.

## Files Created

1. **`extract_forecast_data.py`** - Main extraction script
2. **`example_usage.py`** - Demonstrates various analysis techniques
3. **`FORECAST_EXTRACTOR_README.md`** - Comprehensive documentation

## Quick Start

### Step 1: Extract Data

```bash
python extract_forecast_data.py
```

This generates:
- `forecast_data_extracted_[timestamp].json` - Hierarchical data structure
- `forecast_data_extracted_[timestamp].csv` - Flat table format

### Step 2: Analyze Data

```bash
python example_usage.py
```

This demonstrates:
- Latest subscriber counts by carrier
- Total net additions analysis
- Average churn rate calculations
- Filtered data exports
- Pivot table creation

## What Data is Extracted?

### Carriers
- AT&T
- Verizon
- T-Mobile
- USCellular
- Xfinity Mobile
- Spectrum Mobile

### Metrics (varies by carrier)
- Subscribers
- Net additions
- M&A / adjustments
- Gross additions
- Churn / Churn Rate
- Upgrade Rates
- Gross Losses

### Time Period
- 49 quarters total
- From Q1 2018 to Q1 2030
- ~30 quarters of actual data per carrier
- Remaining are forecast values

## Sample Results

From the extraction:

**Latest Subscriber Counts (Q2 2025):**
- Verizon: 93,207K
- T-Mobile: 80,338K
- AT&T: 73,408K

**Total Net Additions (All Time):**
- T-Mobile: 21,930K
- AT&T: 12,320K
- Verizon: 5,225K

**Average Churn Rates:**
- AT&T: 0.82%
- Verizon: 0.83%
- T-Mobile: 0.91%

## Customization

### Use with Different Files

```python
from extract_forecast_data import ForecastDataExtractor

extractor = ForecastDataExtractor(
    file_path='path/to/your/file.xlsx',
    sheet_name='Data'
)

extractor.run()
```

### Add New Carriers

Edit `extract_forecast_data.py`:

```python
CARRIERS = [
    'AT&T',
    'Verizon',
    # Add your carriers here
    'New Carrier Name'
]
```

### Add New Metrics

Edit `extract_forecast_data.py`:

```python
COMMON_METRICS = [
    'Subscribers',
    'Net additions',
    # Add your metrics here
    'New Metric Name'
]
```

## Output Files Generated

After running both scripts, you'll have:

1. **Original Extracts:**
   - `forecast_data_extracted_*.json`
   - `forecast_data_extracted_*.csv`

2. **Analysis Outputs:**
   - `filtered_att_verizon_2022.csv` - Filtered subset
   - `net_additions_pivot.csv` - Pivot table analysis

## Using the Data

### Python/Pandas

```python
import pandas as pd

# Load the CSV
df = pd.read_csv('forecast_data_extracted_[timestamp].csv')
df['date'] = pd.to_datetime(df['date'])

# Filter by carrier
att_data = df[df['carrier'] == 'AT&T']

# Filter by metric
subscribers = df[df['metric'] == 'Subscribers']

# Get specific carrier and metric
att_subscribers = df[
    (df['carrier'] == 'AT&T') & 
    (df['metric'] == 'Subscribers')
]
```

### Excel

Simply open the CSV files in Excel for manual analysis, charting, etc.

### JSON Processing

```python
import json

with open('forecast_data_extracted_[timestamp].json', 'r') as f:
    data = json.load(f)

# Access AT&T subscriber data
att_subscribers = data['carriers']['AT&T']['metrics']['Subscribers']
```

## Common Use Cases

1. **Trend Analysis**: Track subscriber growth over time
2. **Competitive Analysis**: Compare metrics across carriers
3. **Forecasting**: Use historical data to validate forecasts
4. **Reporting**: Generate automated reports
5. **Data Integration**: Feed into other systems/databases

## Troubleshooting

**Issue: No data extracted**
- Check that the Excel file is in the `data/` directory
- Verify the sheet name is "Data"
- Ensure the Excel file structure matches expected format

**Issue: Missing metrics**
- Some carriers may not have all metrics
- Add missing metric names to `COMMON_METRICS` list

**Issue: Unicode errors (Windows)**
- The scripts now use ASCII-safe characters
- If issues persist, redirect output to file: `python script.py > output.txt`

## Next Steps

1. Review the comprehensive documentation in `FORECAST_EXTRACTOR_README.md`
2. Explore the example analyses in `example_usage.py`
3. Customize for your specific needs
4. Integrate into your data pipeline

## Support

For questions or issues:
- Review the full README: `FORECAST_EXTRACTOR_README.md`
- Check the example code: `example_usage.py`
- Examine the source: `extract_forecast_data.py`

Happy analyzing! 📊


