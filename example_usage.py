"""
Example Usage of Forecast Data Extractor

This script demonstrates how to use the extracted forecast data for analysis.
"""

import pandas as pd
import json
from pathlib import Path
from extract_forecast_data import ForecastDataExtractor


def example_1_basic_extraction():
    """Example 1: Basic data extraction"""
    print("="*80)
    print("EXAMPLE 1: Basic Data Extraction")
    print("="*80)
    
    # Create extractor and run
    extractor = ForecastDataExtractor(
        file_path='data/Navi US Wireless Forecast Model_9.23.25.xlsx',
        sheet_name='Data'
    )
    
    output_files = extractor.run(export_json=True, export_csv=True)
    print(f"\nGenerated {len(output_files)} files")
    

def example_2_analyze_csv():
    """Example 2: Analyze data from CSV"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Analyzing CSV Data")
    print("="*80)
    
    # Find the most recent CSV file
    csv_files = list(Path('.').glob('forecast_data_extracted_*.csv'))
    if not csv_files:
        print("No CSV files found. Run example_1_basic_extraction() first.")
        return
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"\nReading: {latest_csv}")
    
    # Load data
    df = pd.read_csv(latest_csv)
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Analysis 1: Latest subscriber counts (with actual data, not forecasts)
    print("\n" + "-"*80)
    print("Latest Subscriber Counts (in thousands):")
    print("-"*80)
    
    # Get subscriber data and filter out null values
    subscriber_df = df[(df['metric'] == 'Subscribers') & (df['value'].notna())]
    
    # Get the latest date with actual data for each carrier
    latest_subscribers = subscriber_df.loc[
        subscriber_df.groupby('carrier')['date'].idxmax()
    ][['carrier', 'date', 'value']].sort_values('value', ascending=False)
    
    for _, row in latest_subscribers.iterrows():
        if pd.notna(row['date']):
            year = row['date'].year
            quarter = (row['date'].month - 1) // 3 + 1
            quarter_str = f"{year}-Q{quarter}"
        else:
            quarter_str = 'N/A'
        print(f"{row['carrier']:20s}: {row['value']:>10,.0f} (as of {quarter_str})")
    
    # Analysis 2: Total net additions by carrier (all time)
    print("\n" + "-"*80)
    print("Total Net Additions by Carrier (All Time):")
    print("-"*80)
    
    net_adds = df[df['metric'] == 'Net additions'].groupby('carrier')['value'].sum().sort_values(ascending=False)
    
    for carrier, total in net_adds.items():
        print(f"{carrier:20s}: {total:>10,.0f}")
    
    # Analysis 3: Average churn rate by carrier
    print("\n" + "-"*80)
    print("Average Churn Rate by Carrier:")
    print("-"*80)
    
    churn_data = df[df['metric'].isin(['Churn', 'Churn Rate'])]
    avg_churn = churn_data.groupby('carrier')['value'].mean().sort_values()
    
    for carrier, avg in avg_churn.items():
        if avg < 1:  # Percentage format
            print(f"{carrier:20s}: {avg*100:>6.2f}%")
        else:  # Already in percentage
            print(f"{carrier:20s}: {avg:>6.2f}%")
    
    # Analysis 4: Growth trends (YoY comparison)
    print("\n" + "-"*80)
    print("Year-over-Year Subscriber Growth (2023 vs 2024):")
    print("-"*80)
    
    subscriber_data = df[df['metric'] == 'Subscribers'].copy()
    subscriber_data['year'] = subscriber_data['date'].dt.year
    subscriber_data['quarter'] = subscriber_data['date'].dt.quarter
    
    # Get Q4 data for comparison
    q4_data = subscriber_data[subscriber_data['quarter'] == 4]
    
    for carrier in subscriber_data['carrier'].unique():
        carrier_q4 = q4_data[q4_data['carrier'] == carrier].sort_values('year')
        
        if len(carrier_q4) >= 2:
            # Get last two Q4 values
            values = carrier_q4['value'].tail(2).tolist()
            if len(values) == 2:
                growth = ((values[1] - values[0]) / values[0]) * 100
                print(f"{carrier:20s}: {growth:>6.2f}% ({values[0]:,.0f} -> {values[1]:,.0f})")


def example_3_json_analysis():
    """Example 3: Analyze data from JSON"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Analyzing JSON Data")
    print("="*80)
    
    # Find the most recent JSON file
    json_files = list(Path('.').glob('forecast_data_extracted_*.json'))
    if not json_files:
        print("No JSON files found. Run example_1_basic_extraction() first.")
        return
    
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"\nReading: {latest_json}")
    
    # Load data
    with open(latest_json, 'r') as f:
        data = json.load(f)
    
    print(f"\nExtraction Date: {data['extraction_date']}")
    print(f"Source File: {data['source_file']}")
    print(f"Total Quarters: {len(data['quarters'])}")
    print(f"Date Range: {data['quarters'][0]['quarter']} to {data['quarters'][-1]['quarter']}")
    
    # Show metrics available for each carrier
    print("\n" + "-"*80)
    print("Available Metrics by Carrier:")
    print("-"*80)
    
    for carrier, carrier_data in data['carriers'].items():
        metrics = list(carrier_data['metrics'].keys())
        if metrics:  # Only show carriers with metrics
            print(f"\n{carrier}:")
            for metric in metrics:
                data_count = len([v for v in carrier_data['metrics'][metric] if v['value'] is not None])
                print(f"  - {metric}: {data_count} quarters")


def example_4_filtered_extraction():
    """Example 4: Extract and filter specific data"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Filtered Data Extraction")
    print("="*80)
    
    # Load the CSV
    csv_files = list(Path('.').glob('forecast_data_extracted_*.csv'))
    if not csv_files:
        print("No CSV files found. Run example_1_basic_extraction() first.")
        return
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    df = pd.read_csv(latest_csv)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter: Get only AT&T and Verizon data from 2022 onwards
    print("\nFiltering: AT&T and Verizon data from 2022 onwards")
    
    filtered_df = df[
        (df['carrier'].isin(['AT&T', 'Verizon'])) &
        (df['date'] >= '2022-01-01')
    ]
    
    # Export filtered data
    output_file = 'filtered_att_verizon_2022.csv'
    filtered_df.to_csv(output_file, index=False)
    print(f"\nFiltered data saved to: {output_file}")
    print(f"Total rows: {len(filtered_df)}")
    
    # Show sample
    print("\nSample of filtered data:")
    print(filtered_df.head(10).to_string())


def example_5_pivot_table():
    """Example 5: Create pivot table for analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Pivot Table Analysis")
    print("="*80)
    
    # Load the CSV
    csv_files = list(Path('.').glob('forecast_data_extracted_*.csv'))
    if not csv_files:
        print("No CSV files found. Run example_1_basic_extraction() first.")
        return
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    df = pd.read_csv(latest_csv)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    
    # Create pivot table: Net additions by carrier and year
    print("\nNet Additions by Carrier and Year:")
    
    net_adds_df = df[
        (df['metric'] == 'Net additions') & 
        (df['year'] >= 2020) & 
        (df['year'] <= 2024)
    ]
    
    pivot = pd.pivot_table(
        net_adds_df,
        values='value',
        index='carrier',
        columns='year',
        aggfunc='sum',
        fill_value=0
    )
    
    print("\n" + pivot.to_string())
    
    # Save pivot table
    output_file = 'net_additions_pivot.csv'
    pivot.to_csv(output_file)
    print(f"\nPivot table saved to: {output_file}")


def main():
    """Run all examples"""
    print("\n")
    print("*"*80)
    print("FORECAST DATA EXTRACTOR - USAGE EXAMPLES")
    print("*"*80)
    
    # Run extraction if files don't exist
    csv_files = list(Path('.').glob('forecast_data_extracted_*.csv'))
    if not csv_files:
        print("\nNo extracted data found. Running initial extraction...")
        example_1_basic_extraction()
    else:
        print("\nUsing existing extracted data files.")
    
    # Run all analysis examples
    example_2_analyze_csv()
    example_3_json_analysis()
    example_4_filtered_extraction()
    example_5_pivot_table()
    
    print("\n" + "*"*80)
    print("ALL EXAMPLES COMPLETED!")
    print("*"*80)
    print("\nYou now have several output files:")
    print("  - forecast_data_extracted_*.csv/json (original extracted data)")
    print("  - filtered_att_verizon_2022.csv (filtered subset)")
    print("  - net_additions_pivot.csv (pivot table)")
    print("\nYou can modify these examples for your specific analysis needs.")


if __name__ == "__main__":
    main()

