"""
Telecom Forecast Data Dashboard

Interactive dashboard for analyzing carrier forecast data with filters and visualizations.
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import json


# Page configuration
st.set_page_config(
    page_title="Telecom Forecast Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load the most recent extracted forecast data."""
    # Find the most recent CSV file
    csv_files = list(Path('.').glob('forecast_data_extracted_*.csv'))
    
    if not csv_files:
        st.error("No extracted data found. Please run extract_forecast_data.py first.")
        st.stop()
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    
    # Load data
    df = pd.read_csv(latest_csv)
    df['date'] = pd.to_datetime(df['date'])
    
    # Add quarter column for display
    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    df['year'] = df['date'].dt.year
    df['quarter_num'] = df['date'].dt.quarter
    
    return df, latest_csv.name


@st.cache_data
def get_metadata():
    """Get metadata from the JSON export."""
    json_files = list(Path('.').glob('forecast_data_extracted_*.json'))
    
    if json_files:
        latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
        with open(latest_json, 'r') as f:
            data = json.load(f)
        return data
    return None


def create_subscriber_trend(df_filtered):
    """Create subscriber trend line chart."""
    subscriber_data = df_filtered[df_filtered['metric'] == 'Subscribers'].copy()
    
    fig = px.line(
        subscriber_data,
        x='date',
        y='value',
        color='carrier',
        title='Subscriber Trends Over Time',
        labels={'value': 'Subscribers (thousands)', 'date': 'Date'},
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    
    return fig


def create_net_additions_chart(df_filtered):
    """Create net additions bar chart."""
    net_adds = df_filtered[df_filtered['metric'] == 'Net additions'].copy()
    
    fig = px.bar(
        net_adds,
        x='quarter',
        y='value',
        color='carrier',
        title='Net Additions by Quarter',
        labels={'value': 'Net Additions (thousands)', 'quarter': 'Quarter'},
        barmode='group'
    )
    
    fig.update_layout(
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    
    return fig


def create_churn_comparison(df_filtered):
    """Create churn rate comparison chart."""
    churn_data = df_filtered[df_filtered['metric'].isin(['Churn', 'Churn Rate'])].copy()
    
    # Calculate average churn per carrier
    avg_churn = churn_data.groupby('carrier')['value'].mean().sort_values()
    
    fig = px.bar(
        x=avg_churn.index,
        y=avg_churn.values,
        title='Average Churn Rate by Carrier',
        labels={'x': 'Carrier', 'y': 'Average Churn Rate (%)'},
        color=avg_churn.values,
        color_continuous_scale='RdYlGn_r'
    )
    
    fig.update_layout(
        showlegend=False,
        height=400
    )
    
    return fig


def create_market_share_pie(df_filtered, selected_date):
    """Create market share pie chart for a specific date."""
    # Get subscriber data for the selected date
    date_data = df_filtered[
        (df_filtered['metric'] == 'Subscribers') &
        (df_filtered['date'] == selected_date)
    ]
    
    if len(date_data) == 0:
        return None
    
    # Convert date for title formatting
    if hasattr(selected_date, 'to_pydatetime'):
        date_obj = selected_date.to_pydatetime()
    else:
        date_obj = pd.to_datetime(selected_date)
    
    year = date_obj.year
    quarter = (date_obj.month - 1) // 3 + 1
    
    fig = px.pie(
        date_data,
        values='value',
        names='carrier',
        title=f'Market Share - {year} Q{quarter}',
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig


def create_growth_heatmap(df_filtered):
    """Create growth rate heatmap."""
    net_adds = df_filtered[df_filtered['metric'] == 'Net additions'].copy()
    
    # Create pivot table
    pivot = net_adds.pivot_table(
        values='value',
        index='carrier',
        columns='year',
        aggfunc='sum',
        fill_value=0
    )
    
    fig = px.imshow(
        pivot,
        labels=dict(x="Year", y="Carrier", color="Net Additions"),
        title="Net Additions Heatmap (by Year)",
        aspect="auto",
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(height=400)
    
    return fig


def create_metrics_comparison(df_filtered, selected_carriers):
    """Create comparison table of key metrics."""
    metrics_list = ['Subscribers', 'Net additions', 'Churn', 'Churn Rate', 'Gross additions']
    
    comparison_data = []
    
    for carrier in selected_carriers:
        carrier_data = df_filtered[df_filtered['carrier'] == carrier]
        
        row = {'Carrier': carrier}
        
        for metric in metrics_list:
            metric_data = carrier_data[carrier_data['metric'] == metric]
            if len(metric_data) > 0:
                # Get latest value
                latest_val = metric_data.nlargest(1, 'date')['value'].values[0]
                row[metric] = latest_val
            else:
                row[metric] = None
        
        comparison_data.append(row)
    
    return pd.DataFrame(comparison_data)


def main():
    """Main dashboard application."""
    
    # Header
    st.markdown('<p class="main-header">📊 Telecom Forecast Data Dashboard</p>', unsafe_allow_html=True)
    
    # Load data
    df, data_file = load_data()
    metadata = get_metadata()
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filters")
    
    # Info about data source
    with st.sidebar.expander("📁 Data Source", expanded=False):
        st.write(f"**File:** {data_file}")
        if metadata:
            st.write(f"**Extracted:** {metadata['extraction_date'][:10]}")
            st.write(f"**Source:** {Path(metadata['source_file']).name}")
    
    # Carrier filter
    all_carriers = sorted(df['carrier'].unique())
    selected_carriers = st.sidebar.multiselect(
        "Select Carriers",
        options=all_carriers,
        default=all_carriers[:3]  # Default to first 3 carriers
    )
    
    if not selected_carriers:
        st.warning("Please select at least one carrier.")
        st.stop()
    
    # Metric filter
    all_metrics = sorted(df['metric'].unique())
    selected_metrics = st.sidebar.multiselect(
        "Select Metrics",
        options=all_metrics,
        default=['Subscribers', 'Net additions', 'Churn']
    )
    
    # Date range filter
    st.sidebar.subheader("📅 Date Range")
    
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    date_range = st.sidebar.slider(
        "Select Date Range",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
        format="YYYY-MM"
    )
    
    # Filter data based on selections
    df_filtered = df[
        (df['carrier'].isin(selected_carriers)) &
        (df['metric'].isin(selected_metrics)) &
        (df['date'] >= date_range[0]) &
        (df['date'] <= date_range[1])
    ]
    
    # Display filter summary
    st.sidebar.markdown("---")
    st.sidebar.metric("Carriers Selected", len(selected_carriers))
    st.sidebar.metric("Metrics Selected", len(selected_metrics))
    st.sidebar.metric("Data Points", len(df_filtered))
    
    # Main content area
    if len(df_filtered) == 0:
        st.warning("No data available for the selected filters.")
        st.stop()
    
    # Key Metrics Row
    st.header("📈 Key Metrics")
    
    cols = st.columns(4)
    
    # Latest subscriber count
    latest_subscribers = df_filtered[
        (df_filtered['metric'] == 'Subscribers') &
        (df_filtered['date'] == df_filtered['date'].max())
    ]['value'].sum()
    
    with cols[0]:
        st.metric(
            "Total Subscribers",
            f"{latest_subscribers:,.0f}K",
            help="Total subscribers across selected carriers"
        )
    
    # Total net additions
    total_net_adds = df_filtered[df_filtered['metric'] == 'Net additions']['value'].sum()
    with cols[1]:
        st.metric(
            "Total Net Additions",
            f"{total_net_adds:+,.0f}K",
            help="Sum of net additions in selected period"
        )
    
    # Average churn
    avg_churn = df_filtered[df_filtered['metric'].isin(['Churn', 'Churn Rate'])]['value'].mean()
    with cols[2]:
        if pd.notna(avg_churn):
            if avg_churn < 1:
                st.metric("Average Churn Rate", f"{avg_churn*100:.2f}%")
            else:
                st.metric("Average Churn Rate", f"{avg_churn:.2f}%")
        else:
            st.metric("Average Churn Rate", "N/A")
    
    # Date range display
    with cols[3]:
        st.metric(
            "Quarters Analyzed",
            len(df_filtered['quarter'].unique())
        )
    
    st.markdown("---")
    
    # Visualization tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trends", 
        "📊 Comparisons", 
        "🥧 Market Share", 
        "🔥 Heatmap",
        "📋 Data Table"
    ])
    
    with tab1:
        st.subheader("Subscriber Trends")
        
        if 'Subscribers' in selected_metrics:
            fig = create_subscriber_trend(df_filtered)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Please select 'Subscribers' metric to view trends.")
        
        st.subheader("Net Additions Over Time")
        
        if 'Net additions' in selected_metrics:
            fig = create_net_additions_chart(df_filtered)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Please select 'Net additions' metric to view this chart.")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Churn Rate Comparison")
            if any(m in selected_metrics for m in ['Churn', 'Churn Rate']):
                fig = create_churn_comparison(df_filtered)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("Please select 'Churn' or 'Churn Rate' metric.")
        
        with col2:
            st.subheader("Key Metrics Comparison")
            comparison_df = create_metrics_comparison(df_filtered, selected_carriers)
            st.dataframe(
                comparison_df.style.format({
                    'Subscribers': '{:,.0f}',
                    'Net additions': '{:+,.0f}',
                    'Churn': '{:.2%}',
                    'Churn Rate': '{:.2%}',
                    'Gross additions': '{:,.0f}'
                }, na_rep='N/A'),
                width='stretch',
                height=300
            )
    
    with tab3:
        st.subheader("Market Share Analysis")
        
        if 'Subscribers' in selected_metrics:
            # Date selector for market share
            available_dates = sorted(df_filtered[df_filtered['metric'] == 'Subscribers']['date'].unique())
            
            if len(available_dates) > 0:
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    selected_date_idx = st.slider(
                        "Select Quarter",
                        min_value=0,
                        max_value=len(available_dates) - 1,
                        value=len(available_dates) - 1,
                        format=""
                    )
                    
                    selected_date = available_dates[selected_date_idx]
                    # Convert numpy datetime64 to pandas Timestamp for strftime
                    if hasattr(selected_date, 'to_pydatetime'):
                        date_obj = selected_date.to_pydatetime()
                    else:
                        date_obj = pd.to_datetime(selected_date)
                    
                    year = date_obj.year
                    quarter = (date_obj.month - 1) // 3 + 1
                    st.write(f"**{year} Q{quarter}**")
                
                with col2:
                    fig = create_market_share_pie(df_filtered, selected_date)
                    if fig:
                        st.plotly_chart(fig, width='stretch')
            else:
                st.info("No subscriber data available for the selected filters.")
        else:
            st.info("Please select 'Subscribers' metric to view market share.")
    
    with tab4:
        st.subheader("Growth Heatmap")
        
        if 'Net additions' in selected_metrics:
            fig = create_growth_heatmap(df_filtered)
            st.plotly_chart(fig, width='stretch')
            
            st.info("💡 Darker green indicates higher net additions, red indicates losses.")
        else:
            st.info("Please select 'Net additions' metric to view the heatmap.")
    
    with tab5:
        st.subheader("Filtered Data Table")
        
        # Display options
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search", placeholder="Type to filter table...")
        
        with col2:
            show_rows = st.selectbox("Rows per page", [10, 25, 50, 100], index=1)
        
        # Filter by search term
        display_df = df_filtered.copy()
        
        if search_term:
            mask = display_df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[mask]
        
        # Format and display
        st.dataframe(
            display_df[['carrier', 'metric', 'quarter', 'value']].head(show_rows),
            width='stretch'
        )
        
        st.write(f"Showing {min(show_rows, len(display_df))} of {len(display_df)} rows")
        
        # Download button
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name=f"filtered_forecast_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Telecom Forecast Dashboard | Built with Streamlit & Plotly</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()


