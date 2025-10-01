#!/usr/bin/env python3
"""
Dashboard Launcher Script

This script checks for extracted data and launches the Streamlit dashboard.
"""

import subprocess
import sys
from pathlib import Path


def main():
    print("=" * 50)
    print("  Telecom Forecast Dashboard Launcher")
    print("=" * 50)
    print()
    
    # Check if data has been extracted
    csv_files = list(Path('.').glob('forecast_data_extracted_*.csv'))
    
    if not csv_files:
        print("⚠️  No extracted data found.")
        print("📊 Running data extraction first...")
        print()
        
        try:
            subprocess.run([sys.executable, 'extract_forecast_data.py'], check=True)
            print()
            print("✅ Data extraction complete!")
            print()
        except subprocess.CalledProcessError:
            print("❌ Error during data extraction.")
            print("Please run 'python extract_forecast_data.py' manually.")
            sys.exit(1)
    else:
        print(f"✅ Found extracted data: {csv_files[0].name}")
        print()
    
    # Launch dashboard
    print("🚀 Starting dashboard...")
    print()
    print("📊 The dashboard will open in your browser at:")
    print("   http://localhost:8501")
    print()
    print("⌨️  Press Ctrl+C to stop the dashboard.")
    print()
    print("-" * 50)
    print()
    
    try:
        subprocess.run(['streamlit', 'run', 'dashboard.py'])
    except KeyboardInterrupt:
        print()
        print("👋 Dashboard stopped.")
        sys.exit(0)
    except FileNotFoundError:
        print("❌ Streamlit is not installed.")
        print("Please run: pip install streamlit plotly")
        sys.exit(1)


if __name__ == "__main__":
    main()


