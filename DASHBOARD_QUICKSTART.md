# 🚀 Dashboard Quick Start Guide

## What You Just Got

A complete interactive dashboard for analyzing your telecom forecast data with:
- ✅ Carrier filters (select which carriers to view)
- ✅ Date range slider (filter by time period)  
- ✅ Interactive charts (subscribers, net additions, churn, market share)
- ✅ Data export capabilities
- ✅ 100% local - runs on your PC, no internet needed

## Launch the Dashboard (3 Easy Steps)

### Option A: Using the Launcher (Easiest)

**Windows:**
```bash
launch_dashboard.bat
```

**Mac/Linux or Alternative:**
```bash
python launch_dashboard.py
```

### Option B: Manual Launch

**Step 1:** Extract the data (if you haven't already)
```bash
python extract_forecast_data.py
```

**Step 2:** Start the dashboard
```bash
streamlit run dashboard.py
```

**Step 3:** Open your browser
The dashboard will automatically open at `http://localhost:8501`

## What You'll See

### Sidebar (Left)
```
🎛️ Filters
├── Select Carriers (multi-select)
├── Select Metrics (multi-select)
└── Date Range Slider (drag to adjust)
```

### Main Dashboard
```
📊 Dashboard Tabs
├── 📈 Trends
│   ├── Subscriber trends over time
│   └── Net additions by quarter
│
├── 📊 Comparisons
│   ├── Churn rate comparison
│   └── Key metrics table
│
├── 🥧 Market Share
│   └── Interactive pie chart with quarter slider
│
├── 🔥 Heatmap
│   └── Growth heatmap (by carrier & year)
│
└── 📋 Data Table
    ├── Searchable data
    └── Download filtered CSV
```

## Interactive Features

### 1. Filter by Carrier
- Click the "Select Carriers" dropdown
- Choose one or more carriers
- Charts update instantly

### 2. Adjust Date Range
- Use the slider at the bottom of the sidebar
- Drag the handles to select your date range
- All visualizations update automatically

### 3. Select Metrics
- Choose which metrics to analyze
- Different tabs require different metrics
- Tooltips will guide you

### 4. Explore Charts
- **Hover**: See exact values
- **Zoom**: Click and drag on charts
- **Pan**: Hold shift and drag
- **Reset**: Double-click chart
- **Fullscreen**: Click expand icon

### 5. Export Data
- Go to "Data Table" tab
- Use filters as needed
- Click "Download Filtered Data (CSV)"

## Sample Use Cases

### Case 1: Compare AT&T vs Verizon Growth

1. Select only "AT&T" and "Verizon" in carrier filter
2. Select "Subscribers" and "Net additions" metrics
3. Go to "Trends" tab
4. Adjust date range to 2020-2024
5. Observe growth patterns

### Case 2: Analyze Recent Churn Trends

1. Select all carriers
2. Select "Churn" or "Churn Rate" metric
3. Adjust date range to last 2 years
4. Go to "Comparisons" tab
5. See which carrier has best retention

### Case 3: Market Share Evolution

1. Select all carriers
2. Select "Subscribers" metric
3. Go to "Market Share" tab
4. Use the quarter slider to see changes over time

### Case 4: Export Q1 2024 Data

1. Use date slider to select Q1 2024
2. Select desired carriers and metrics
3. Go to "Data Table" tab
4. Click "Download Filtered Data (CSV)"

## Dashboard Controls

### Sidebar Filters

| Control | Purpose | Example |
|---------|---------|---------|
| Carrier Multi-Select | Choose which carriers to analyze | AT&T, Verizon |
| Metric Multi-Select | Choose what to measure | Subscribers, Churn |
| Date Range Slider | Select time period | 2020-2024 |

### Chart Interactions

| Action | How | Result |
|--------|-----|--------|
| Hover | Move mouse over data point | See exact value |
| Zoom | Click and drag area | Zoom into selection |
| Pan | Shift + drag | Move around chart |
| Reset | Double-click | Reset to original view |
| Download | Click camera icon | Save as PNG |

## Tips for Best Experience

### 1. Start Simple
- Begin with 2-3 carriers
- Select a few key metrics
- Explore one tab at a time

### 2. Use Chrome/Edge
- Best performance
- All features supported
- Fastest rendering

### 3. Refresh Data
- After updating Excel file
- Run `python extract_forecast_data.py`
- Click "Rerun" in dashboard (or press R)

### 4. Full Screen Mode
- Click expand icon on any chart
- Better for presentations
- Press ESC to exit

## Common Questions

**Q: How do I stop the dashboard?**
A: Press `Ctrl+C` in the terminal/command prompt

**Q: Can I access this from another device?**
A: Yes! Run: `streamlit run dashboard.py --server.address 0.0.0.0`
   Then access via your PC's IP address from other devices on your network

**Q: The dashboard looks blank?**
A: Make sure you've selected at least one carrier and appropriate metrics for the tab you're viewing

**Q: How do I update the data?**
A: 
1. Update your Excel file
2. Run `python extract_forecast_data.py`
3. Refresh the dashboard (press R or click Rerun)

**Q: Can I change the default selections?**
A: Yes! Edit the `default` parameter in `dashboard.py` around line 112

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `R` | Rerun app (reload data) |
| `C` | Clear cache |
| `?` | Show keyboard shortcuts |
| `Esc` | Close dialogs |

## Troubleshooting

### "No extracted data found"
**Solution:** Run `python extract_forecast_data.py` first

### "Module not found: streamlit"
**Solution:** Install dependencies: `pip install streamlit plotly`

### Charts show "Please select X metric"
**Solution:** Check the sidebar and ensure you've selected the required metrics

### Port 8501 already in use
**Solution:** 
```bash
streamlit run dashboard.py --server.port 8502
```

### Dashboard is slow
**Solution:** 
- Select fewer carriers
- Reduce date range
- Close and restart

## Files Created

```
📁 Your Project
├── 📊 dashboard.py              # Main dashboard app
├── 🚀 launch_dashboard.py       # Python launcher
├── 🚀 launch_dashboard.bat      # Windows launcher
├── 📖 DASHBOARD_README.md       # Full documentation
├── 📖 DASHBOARD_QUICKSTART.md   # This file
├── 📄 extract_forecast_data.py  # Data extractor
└── 📊 forecast_data_*.csv       # Extracted data
```

## Next Steps

1. **Explore the Dashboard**
   - Try different filter combinations
   - Explore all tabs
   - Export some data

2. **Read Full Docs**
   - See `DASHBOARD_README.md` for advanced features
   - See `FORECAST_EXTRACTOR_README.md` for data extraction details

3. **Customize**
   - Add your own charts
   - Modify color schemes
   - Add custom metrics

4. **Share**
   - Present insights to your team
   - Export charts as images
   - Download filtered data for reports

## Visual Guide

### Example: Filtering to AT&T Q1-Q4 2023

```
Sidebar                          Main Area
┌──────────────┐                ┌────────────────────────┐
│ 🎛️ Filters  │                │ 📈 Subscriber Trends   │
├──────────────┤                │                        │
│ Carriers:    │                │  [Line Chart]          │
│ ☑ AT&T       │  ────────────▶ │   Shows AT&T           │
│ ☐ Verizon    │                │   data only from       │
│ ☐ T-Mobile   │                │   2023                 │
│              │                │                        │
│ Date Range:  │                └────────────────────────┘
│ ▸────────◂   │                
│ 2023  2023   │                
└──────────────┘                
```

## Get Help

Need assistance?

1. Check the info tooltips (ℹ️) in the dashboard
2. Review `DASHBOARD_README.md` for detailed docs
3. Look at the code comments in `dashboard.py`

---

**Ready to explore your data! 🎉**

Press the launch button and start analyzing!


