import streamlit as st
import pandas as pd
from src.plots import plot_histogram, plot_scatter, create_map

def render_dashboard(df, stats):
    """Render the main dashboard."""
    st.header("🇮🇳 India Iceberg Index Dashboard")
    
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("National Avg Iceberg Index", f"{stats['national_iceberg_index']:.1f}", 
                help="Wage-weighted share of occupational skills extendable by AI")
    col2.metric("Workforce Covered", f"{stats['total_workforce_analyzed'] / 1e6:.1f} M",
                help="Total estimated workforce in analyzed districts")
    col3.metric("Surface Index", f"{stats['avg_surface_index']:.1f}",
                help="Visible exposure in Tech/IT sector")
    col4.metric("Surprise Index", f"{stats['avg_surprise_index']:.1f}",
                help="Difference between Iceberg and Surface indices (Hidden Exposure)")

    st.markdown("---")

    # Distribution
    st.subheader("Distribution of AI Exposure Breakdown")
    col_dist1, col_dist2 = st.columns(2)
    
    with col_dist1:
        st.plotly_chart(plot_histogram(df, "iceberg_index", "Iceberg Index Distribution", "#FF4B4B"), use_container_width=True)
        st.caption("Distribution of districts by their AI exposure score.")
        
    with col_dist2:
        top_districts = df.nlargest(10, 'iceberg_index')[['District_Name', 'State_Name', 'iceberg_index', 'total_employment']]
        st.write("Top 10 Districts by Exposure")
        st.dataframe(top_districts, hide_index=True)

    st.markdown("### % of Jobs to be Automated")
    st.info(
        f"Based on the analysis, the **National Mean Iceberg Index is {stats['national_iceberg_index']:.1f}**. "
        "This metric represents the percentage of occupational tasks (weighted by wages) that are susceptible to AI automation across the Indian workforce."
    )

def render_map(df):
    """Render the geographic analysis map."""
    st.header("🗺️ Geographic Exposure Map")
    
    st.markdown("Bubble size represents **Employment Magnitude**. Color represents **Iceberg Index** (Red = Higher Exposure).")
    
    map_chart = create_map(df)
    if map_chart:
        st.pydeck_chart(map_chart)
    else:
        st.warning("Geographic data (Lat/Long) not available for mapping.")

    # State Level Table
    st.subheader("State-Level Aggregates")
    state_df = df.groupby('State_Name').agg({
        'iceberg_index': 'mean',
        'total_employment': 'sum',
        'District_Name': 'count'
    }).rename(columns={'District_Name': 'District_Count'}).reset_index().sort_values('iceberg_index', ascending=False)
    
    st.dataframe(state_df, use_container_width=True)

def render_analysis(df):
    """Render deep dive analysis."""
    st.header("📊 Deep Dive Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_scatter(df, "urban_pct", "iceberg_index", "total_employment", "iceberg_index", 
                                     ['District_Name', 'State_Name']), use_container_width=True)
        st.markdown("**Urbanization vs AI Exposure**: More urbanized districts tend to have higher exposure due to concentration of white-collar service jobs.")

    with col2:
        if 'literacy_rate' in df.columns and df['literacy_rate'].notna().sum() > 0:
            st.plotly_chart(plot_scatter(df, "literacy_rate", "iceberg_index", "total_employment", "iceberg_index",
                                         ['District_Name', 'State_Name']), use_container_width=True)
            st.markdown("**Literacy vs AI Exposure**: Correlation between education levels and exposure.")
        else:
            st.info("Literacy data not available for correlation analysis.")

def render_documentation():
    """Render documentation from markdown file."""
    st.header("📚 Methodology & Documentation")
    
    try:
        with open("methodology.md", "r") as f:
            content = f.read()
            st.markdown(content)
    except FileNotFoundError:
        st.error("Documentation file not found.")
