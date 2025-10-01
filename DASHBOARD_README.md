# 📊 Telecom Forecast Dashboard

An interactive, local web dashboard for analyzing telecom carrier forecast data with powerful filtering and visualization capabilities.

## Features

### 🎛️ Interactive Filters
- **Carrier Selection**: Multi-select filter to choose which carriers to analyze
- **Metric Selection**: Choose which metrics to display (Subscribers, Net Additions, Churn, etc.)
- **Date Range Slider**: Easily filter data by time period

### 📈 Visualizations

1. **Trends Tab**
   - Subscriber trends over time (line chart)
   - Net additions by quarter (bar chart)

2. **Comparisons Tab**
   - Churn rate comparison across carriers
   - Key metrics comparison table

3. **Market Share Tab**
   - Interactive pie chart showing market share
   - Quarter-by-quarter slider to see changes over time

4. **Heatmap Tab**
   - Growth heatmap showing net additions by carrier and year
   - Color-coded for easy pattern recognition

5. **Data Table Tab**
   - Searchable, filterable data table
   - Export filtered data to CSV

### 📊 Key Metrics Dashboard
- Total Subscribers (across selected carriers)
- Total Net Additions
- Average Churn Rate
- Number of Quarters Analyzed

## Installation

### Prerequisites

Ensure you have Python 3.9+ installed.

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install streamlit plotly pandas
```

## Usage

### Step 1: Extract Data

First, make sure you have extracted data from your Excel file:

```bash
python extract_forecast_data.py
```

This creates the necessary CSV and JSON files that the dashboard reads.

### Step 2: Launch Dashboard

Run the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

The dashboard will automatically open in your default web browser at `http://localhost:8501`.

### Step 3: Interact with the Dashboard

1. **Use the sidebar** to select:
   - Carriers you want to analyze
   - Metrics to display
   - Date range using the slider

2. **Explore the tabs**:
   - Click through different tabs to see various visualizations
   - Hover over charts for detailed information

3. **Export data**:
   - Go to the "Data Table" tab
   - Click "Download Filtered Data (CSV)" to export your selection

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│                  Telecom Forecast Dashboard                  │
├──────────────┬──────────────────────────────────────────────┤
│              │  Key Metrics Row                             │
│   Sidebar    │  [Total Subscribers] [Net Adds] [Churn] [Q's]│
│   Filters    ├──────────────────────────────────────────────┤
│              │                                              │
│  • Carriers  │  Visualization Tabs:                         │
│  • Metrics   │  [Trends] [Comparisons] [Market Share]       │
│  • Date      │  [Heatmap] [Data Table]                      │
│    Range     │                                              │
│              │  [Interactive Charts and Tables]             │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

## Available Visualizations

### Subscriber Trends
- **Type**: Line chart
- **Shows**: Subscriber count over time for each carrier
- **Features**: Hover for exact values, zoom, pan

### Net Additions
- **Type**: Grouped bar chart
- **Shows**: Quarterly net additions by carrier
- **Features**: Compare performance across carriers

### Churn Rate Comparison
- **Type**: Bar chart
- **Shows**: Average churn rate per carrier
- **Features**: Color-coded by performance

### Market Share
- **Type**: Pie/Donut chart
- **Shows**: Subscriber market share at specific quarters
- **Features**: Interactive quarter slider

### Growth Heatmap
- **Type**: Heatmap
- **Shows**: Net additions intensity by carrier and year
- **Features**: Color gradient (green = growth, red = decline)

### Data Table
- **Type**: Interactive table
- **Shows**: Filtered raw data
- **Features**: Search, download CSV

## Tips & Tricks

### 1. Quick Comparisons
Select only 2-3 carriers for cleaner, easier-to-read charts.

### 2. Focus on Specific Periods
Use the date slider to zoom into specific time periods (e.g., post-pandemic growth).

### 3. Metric Combinations
Try different metric combinations:
- Subscribers + Net additions = Growth story
- Churn + Gross additions = Retention insights

### 4. Export Your Analysis
After filtering, export the data from the Data Table tab to create custom Excel reports.

### 5. Full Screen Charts
Click the expand icon on any chart to view in full screen.

## Keyboard Shortcuts

When focused on the dashboard:

- `R` - Rerun the app (reload data)
- `C` - Clear cache
- `Esc` - Close modals/dialogs

## Customization

### Change Default Selections

Edit `dashboard.py` line ~112:

```python
selected_carriers = st.sidebar.multiselect(
    "Select Carriers",
    options=all_carriers,
    default=['AT&T', 'Verizon', 'T-Mobile']  # Change these
)
```

### Add Custom Visualizations

Add your own chart functions following this pattern:

```python
def create_my_custom_chart(df_filtered):
    """Create your custom visualization."""
    # Your chart code here
    fig = px.bar(...)  # or px.line(), px.scatter(), etc.
    return fig
```

Then add it to a tab in the `main()` function.

### Modify Color Schemes

Change color schemes in chart functions:

```python
fig = px.line(
    ...,
    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']  # Custom colors
)
```

## Troubleshooting

### Dashboard Won't Start

**Error**: "No extracted data found"
- **Solution**: Run `python extract_forecast_data.py` first

**Error**: "Module not found"
- **Solution**: Install dependencies: `pip install -r requirements.txt`

### Charts Not Displaying

**Issue**: Empty charts
- **Solution**: Check that you've selected the required metrics for that chart
- Check the date range includes data

### Performance Issues

**Issue**: Dashboard is slow
- **Solution**: 
  - Reduce date range
  - Select fewer carriers
  - Clear browser cache
  - Restart the dashboard

### Port Already in Use

**Error**: "Port 8501 is already in use"
- **Solution**: 
  ```bash
  streamlit run dashboard.py --server.port 8502
  ```

## Advanced Features

### Running on a Custom Port

```bash
streamlit run dashboard.py --server.port 8080
```

### Disable Auto-Open Browser

```bash
streamlit run dashboard.py --server.headless true
```

### Share on Local Network

```bash
streamlit run dashboard.py --server.address 0.0.0.0
```

Then access from other devices using your computer's IP address: `http://192.168.1.X:8501`

## File Structure

```
telecom-netadds-pipeline/
├── dashboard.py                          # Dashboard application
├── extract_forecast_data.py              # Data extraction script
├── forecast_data_extracted_*.csv         # Extracted data (CSV)
├── forecast_data_extracted_*.json        # Extracted data (JSON)
├── requirements.txt                      # Dependencies
└── DASHBOARD_README.md                   # This file
```

## Data Refresh

To update the dashboard with new data:

1. Update your Excel file
2. Run the extraction script:
   ```bash
   python extract_forecast_data.py
   ```
3. The dashboard will automatically use the newest extracted file
4. If the dashboard is running, click the "Rerun" button or press `R`

## Performance Notes

- **First Load**: May take 2-3 seconds to load data
- **Filter Changes**: Instant (data is cached)
- **Chart Rendering**: Very fast with Plotly
- **Data Size**: Handles 10,000+ rows easily

## Browser Compatibility

Recommended browsers:
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ⚠️ Internet Explorer (not supported)

## Privacy & Security

- **100% Local**: All data stays on your computer
- **No Internet Required**: After installation, runs completely offline
- **No Data Transmission**: Nothing is sent to external servers

## Upcoming Features

Potential enhancements (feel free to implement):

- [ ] Year-over-year comparison charts
- [ ] Forecast vs Actual comparison
- [ ] Export charts as images
- [ ] Custom metric calculations
- [ ] Quarterly report generator
- [ ] Email alerts for thresholds

## Support

For issues or questions:

1. Check this README
2. Review `FORECAST_EXTRACTOR_README.md`
3. Examine the code comments in `dashboard.py`

## Credits

Built with:
- **Streamlit**: Web dashboard framework
- **Plotly**: Interactive charts
- **Pandas**: Data manipulation

## License

Internal use only.

---

**Happy Analyzing! 📊**


