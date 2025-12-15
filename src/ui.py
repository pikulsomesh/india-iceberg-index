import streamlit as st
import pandas as pd
from src.plots import plot_histogram, plot_scatter, create_choropleth

def render_dashboard(df, stats):
    """Render the main dashboard."""
    st.header("🇮🇳 India Iceberg Index")
    
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
    
    st.info(
        f"Based on the analysis, the **National Mean Iceberg Index is {stats['national_iceberg_index']:.1f}**. "
        "This metric represents the percentage of occupational tasks (weighted by wages) that are susceptible to AI automation across the Indian workforce."
    )
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



    # --- Explore Further ---
    st.markdown("### Explore Further")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.subheader("🗺️ Geographic Analysis")
        st.write("Explore the **Interactive Map** to see how AI exposure varies across India's districts. Hover over specific regions to see detailed Iceberg Indices.")

    with col_b:
        st.subheader("📊 Socio Economic Analysis")
        st.write("Understand the drivers of AI exposure. This section correlates the Iceberg Index with key indicators like **Urbanization**, **Literacy**, and **Internet Access**.")

    with col_c:
        st.subheader("📚 Methodology")
        st.write("Learn how the index was constructed. Adapts the **Felten et al. (2023)** methodology using Indian NCO codes, PLFS 2024 workforce data, and spatial backfilling techniques.")

def render_map(df, geojson):
    """Render the geographic analysis map."""
    st.header("🗺️ Geographic Exposure Map")
    
    # 1. Interactive Choropleth Map (Single Map)
    st.subheader("Interactive District-Level Map")
    st.markdown("Color represents **Iceberg Index**. Hover for details.")
    
    map_chart = create_choropleth(df, geojson)
    if map_chart:
        st.plotly_chart(map_chart, use_container_width=True)
    else:
        st.error("Could not load map data.")
    
    st.markdown("---")
    
    # 2. Census Correlations
    # Data Explorer (Moved from Dashboard)
    st.subheader("🔍 Data Explorer")
    tab1, tab2 = st.tabs(["Search by District", "State Aggregation"])
    
    with tab1:
        st.subheader("Search District")
        districts = sorted(df['District_Name'].unique())
        selected_dist = st.selectbox("Select District", districts)
        
        if selected_dist:
            row = df[df['District_Name'] == selected_dist].iloc[0]
            st.write(f"**District:** {selected_dist}")
            st.write(f"**State:** {row['State_Name']}")
            st.metric("Iceberg Index", f"{row['iceberg_index']:.2f}")
                
    with tab2:
        st.subheader("State-Level Aggregation")
        
        # Comprehensive Aggregation
        agg_cols = {
            'iceberg_index': ['mean', 'std', 'min', 'max'],
            'surface_index': ['mean', 'std', 'min', 'max'],
            'surprise_index': ['mean', 'std', 'min', 'max'],
            'District_Name': 'count'
        }
        
        state_agg = df.groupby('State_Name').agg(agg_cols).reset_index()
        
        # Flatten MultiIndex Columns
        state_agg.columns = [
            'State/UT',
            'Iceberg Mean', 'Iceberg SD', 'Iceberg Min', 'Iceberg Max',
            'Surface Mean', 'Surface SD', 'Surface Min', 'Surface Max',
            'Surprise Mean', 'Surprise SD', 'Surprise Min', 'Surprise Max',
            'Districts (n)'
        ]
        
        # Reorder columns to match Appendix style: State, n, Iceberg stats, Surface stats, Surprise stats
        cols_order = ['State/UT', 'Districts (n)', 
                      'Iceberg Mean', 'Iceberg SD', 'Iceberg Min', 'Iceberg Max',
                      'Surface Mean', 'Surface SD', 'Surface Min', 'Surface Max',
                      'Surprise Mean', 'Surprise SD', 'Surprise Min', 'Surprise Max']
        
        state_agg = state_agg[cols_order].sort_values('Iceberg Mean', ascending=False)
        
        # Styling
        st.dataframe(
            state_agg.style.format(precision=2, na_rep="---")
                     .background_gradient(cmap='viridis', subset=['Iceberg Mean', 'Surface Mean', 'Surprise Mean']),
            use_container_width=True,
            hide_index=True
        )

def render_analysis(df):
    """Render socio-economic analysis."""
    st.header("📊 Socio Economic Analysis")
    
    # --- Filter ---
    states = sorted(df['State_Name'].unique())
    selected_states = st.multiselect("Filter by State", states, placeholder="Select states to filter analysis (default: All)")
    
    if selected_states:
        plot_df = df[df['State_Name'].isin(selected_states)]
    else:
        plot_df = df
        
    st.markdown("---")
    
    # --- Layout: 1 Row, 3 Columns ---
    col1, col2, col3 = st.columns(3)
    
    # Common Hover Data
    hover_cols = ['District_Name', 'State_Name']
    
    with col1:
        st.subheader("Urbanization")
        # Explicit labels for nice Title Case
        labels_urban = {'urban_pct': 'Urban Percentage (%)', 'iceberg_index': 'Iceberg Index', 'total_employment': 'Employment Size'}
        st.plotly_chart(
            plot_scatter(plot_df, "urban_pct", "iceberg_index", "total_employment", "iceberg_index", 
                         hover_cols, labels=labels_urban), 
            use_container_width=True
        )
        st.markdown("**Trend:** Higher urbanization correlates with higher AI exposure.")

    with col2:
        st.subheader("Literacy")
        if 'literacy_rate' in plot_df.columns and plot_df['literacy_rate'].notna().sum() > 0:
            labels_lit = {'literacy_rate': 'Literacy Rate (%)', 'iceberg_index': 'Iceberg Index', 'total_employment': 'Employment Size'}
            st.plotly_chart(
                plot_scatter(plot_df, "literacy_rate", "iceberg_index", "total_employment", "iceberg_index",
                             hover_cols, labels=labels_lit), 
                use_container_width=True
            )
            st.markdown("**Trend:** Education levels show positive correlation with exposure.")
        else:
            st.info("Literacy data not available.")

    with col3:
        st.subheader("Internet Access")
        if 'Households_with_Internet' in plot_df.columns:
             labels_net = {'Households_with_Internet': 'Internet Households (%)', 'iceberg_index': 'Iceberg Index', 'total_employment': 'Employment Size'}
             st.plotly_chart(
                plot_scatter(plot_df, "Households_with_Internet", "iceberg_index", "total_employment", "iceberg_index",
                             hover_cols, labels=labels_net), 
                use_container_width=True
             )
             st.markdown("**Trend:** Digital access strongly tracks with automability.")
        else:
            st.info("Internet data not available.")

def render_documentation():
    """Render documentation from markdown file."""
    st.header("📚 Methodology")
    
    st.image("images/pipeline.png", caption="Iceberg Index Generation Pipeline", use_container_width=True)
    
    st.markdown("""
    ### Methodology Highlights
    The Iceberg Index methodology adapts the process developed by Felten et al. (2023) for the Indian context:
    
    1.  **AI Occupational Exposure (AIOE):** Generated using the mapping between Indian NCO codes and ONet codes.
    2.  **District Aggregation:** Applied district-level industry/workforce composition from PLFS 2024 to calculate the weighted average exposure.
    3.  **Spatial Analysis:** Backfilled missing geometries using nearest-neighbor interpolation to provide 100% map coverage.
    
    For full technical details, please refer to the [Technical Paper on GitHub](https://github.com/pikulsomesh/india-iceberg-index/blob/main/I3-Technical.pdf).
    """)
