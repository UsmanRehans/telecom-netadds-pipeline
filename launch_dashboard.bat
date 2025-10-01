@echo off
echo ========================================
echo  Telecom Forecast Dashboard Launcher
echo ========================================
echo.

REM Check if data has been extracted
if not exist "forecast_data_extracted_*.csv" (
    echo No extracted data found.
    echo Running data extraction first...
    echo.
    python extract_forecast_data.py
    echo.
    echo Data extraction complete!
    echo.
)

echo Starting dashboard...
echo.
echo The dashboard will open in your browser at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard.
echo.

streamlit run dashboard.py

pause


