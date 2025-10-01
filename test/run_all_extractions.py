#!/usr/bin/env python3
"""
Main runner script for all carrier extractions.
Runs Verizon, AT&T, and T-Mobile extractions and combines results.
"""

import pandas as pd
import json
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from extract_verizon import extract_verizon_quarterly_summary, save_verizon_data
from extract_att import extract_att_quarterly_summary, save_att_data
from extract_tmobile import extract_tmobile_quarterly_summary, save_tmobile_data


def run_all_extractions():
    """Run all carrier extractions and combine results."""
    print("🚀 Starting all carrier extractions...")
    print("=" * 80)
    
    # Run Verizon extraction
    print("\n📱 VERIZON EXTRACTION")
    print("-" * 40)
    verizon_data = extract_verizon_quarterly_summary()
    save_verizon_data(verizon_data)
    
    print("\n📱 AT&T EXTRACTION")
    print("-" * 40)
    att_data = extract_att_quarterly_summary()
    save_att_data(att_data)
    
    print("\n📱 T-MOBILE EXTRACTION")
    print("-" * 40)
    tmobile_data = extract_tmobile_quarterly_summary()
    save_tmobile_data(tmobile_data)
    
    print("\n" + "=" * 80)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 80)
    
    if verizon_data:
        print(f"✅ Verizon: {len(verizon_data)} quarters processed")
    else:
        print("❌ Verizon: No data extracted")
    
    if att_data:
        print(f"✅ AT&T: {len(att_data)} quarters processed")
    else:
        print("❌ AT&T: No data extracted")
    
    if tmobile_data:
        print(f"✅ T-Mobile: {len(tmobile_data)} quarters processed")
    else:
        print("⚠️ T-Mobile: Not yet implemented")
    
    # Combine all data into a single summary
    combine_all_data(verizon_data, att_data, tmobile_data)
    
    print("\n🎉 All extractions complete!")


def combine_all_data(verizon_data, att_data, tmobile_data):
    """Combine all carrier data into a single summary."""
    print("\n📊 COMBINING ALL CARRIER DATA")
    print("-" * 40)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_data = []
    
    # Add Verizon data
    if verizon_data:
        for row in verizon_data:
            combined_row = {
                'carrier': 'Verizon',
                'quarter': row['quarter'],
                'postpaid_connections': row.get('postpaid_connections'),
                'postpaid_net_adds': row.get('postpaid_net_adds'),
                'prepaid_connections': row.get('prepaid_connections'),
                'prepaid_net_adds': row.get('prepaid_net_adds'),
                'total_connections': row.get('total_connections'),
                'total_net_adds': row.get('total_net_adds'),
            }
            combined_data.append(combined_row)
    
    # Add AT&T data
    if att_data:
        for row in att_data:
            combined_row = {
                'carrier': 'AT&T',
                'quarter': row['quarter'],
                'postpaid_connections': row.get('postpaid_subscribers'),  # AT&T uses 'subscribers'
                'postpaid_net_adds': row.get('postpaid_net_adds'),
                'prepaid_connections': row.get('prepaid_subscribers'),  # AT&T uses 'subscribers'
                'prepaid_net_adds': row.get('prepaid_net_adds'),
                'total_connections': row.get('total_subscribers'),  # AT&T uses 'subscribers'
                'total_net_adds': row.get('total_net_adds'),
            }
            combined_data.append(combined_row)
    
    # Add T-Mobile data (when implemented)
    if tmobile_data:
        for row in tmobile_data:
            combined_row = {
                'carrier': 'T-Mobile',
                'quarter': row['quarter'],
                'postpaid_connections': row.get('postpaid_connections'),
                'postpaid_net_adds': row.get('postpaid_net_adds'),
                'prepaid_connections': row.get('prepaid_connections'),
                'prepaid_net_adds': row.get('prepaid_net_adds'),
                'total_connections': row.get('total_connections'),
                'total_net_adds': row.get('total_net_adds'),
            }
            combined_data.append(combined_row)
    
    if combined_data:
        # Save combined data
        df = pd.DataFrame(combined_data)
        
        # Save timestamped version
        csv_file = f"data/all_carriers_combined_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"💾 Combined data saved to {csv_file}")
        
        # Save latest version
        df.to_csv("data/all_carriers_combined.csv", index=False)
        print(f"💾 Latest combined data saved to data/all_carriers_combined.csv")
        
        # Save as JSON
        json_file = f"data/all_carriers_combined_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(combined_data, f, indent=2)
        print(f"💾 Combined data saved to {json_file}")
        
        # Save latest JSON
        with open("data/all_carriers_combined.json", 'w') as f:
            json.dump(combined_data, f, indent=2)
        print(f"💾 Latest combined data saved to data/all_carriers_combined.json")
        
        print(f"\n📈 Total records: {len(combined_data)}")
        print(f"📊 Carriers: {df['carrier'].unique()}")
        print(f"📅 Quarters: {sorted(df['quarter'].unique())}")
    else:
        print("❌ No data to combine")


if __name__ == "__main__":
    run_all_extractions()
