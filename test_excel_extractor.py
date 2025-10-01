"""
Test script for Excel AI Extractor
"""

import os
import sys
sys.path.append('src')

from src.excel_ai_extractor import ExcelAIExtractor


def test_excel_extraction():
    """Test the Excel extraction functionality"""
    
    print("🧪 Testing Excel AI Extractor")
    
    # Look for Excel files
    excel_files = []
    for file in os.listdir('.'):
        if file.endswith(('.xlsx', '.xls')):
            excel_files.append(file)
    
    if not excel_files:
        print("❌ No Excel files found in current directory")
        print("📁 Please place your Excel file in the current directory")
        return
    
    print(f"📊 Found Excel files: {excel_files}")
    
    # Test with the first Excel file
    excel_file = excel_files[0]
    print(f"🔍 Testing with: {excel_file}")
    
    try:
        # Create extractor
        extractor = ExcelAIExtractor(excel_file)
        
        # Process the file
        result = extractor.process_excel_file()
        
        if result.get('extraction_method') == 'ai_success':
            print("✅ Extraction successful!")
            print(f"📈 Confidence: {result.get('confidence', 'unknown')}")
            
            # Show sample data
            carriers = result.get('carriers', {})
            for carrier_name, carrier_data in carriers.items():
                print(f"\n📱 {carrier_name} Data:")
                for metric_name, metric_data in carrier_data.items():
                    sample_periods = list(metric_data.keys())[:3]  # Show first 3 periods
                    print(f"   {metric_name}: {sample_periods}")
        else:
            print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_excel_extraction()

