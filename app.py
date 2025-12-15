import streamlit as st
from src.data import load_data, load_geojson
from src.ui import render_dashboard, render_map, render_analysis, render_documentation

st.set_page_config(
    page_title="India Iceberg Index",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.sidebar.title("🧊 India Iceberg Index")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Geographic Analysis", "Socio Economic Analysis", "Methodology"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**About**\n\n"
        "The Iceberg Index measures the share of occupational skills that "
        "AI can technically perform. \n\nBased on PLFS 2024 data and "
        "Felten et al. (2023) AIOE scores."
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Author**\n\n"
        "**Somesh Mohapatra**\n\n"
        "PhD in AI (MIT) | MBA (MIT Sloan)\n\n"
        "*Personal Project and Opinions.*"
    )

    # Load Data
    with st.spinner("Loading data..."):
        try:
            df, summary_stats = load_data()
            geojson = load_geojson()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if page == "Dashboard":
        render_dashboard(df, summary_stats)
    elif page == "Geographic Analysis":
        render_map(df, geojson)
    elif page == "Socio Economic Analysis":
        render_analysis(df)
    elif page == "Methodology":
        render_documentation()

if __name__ == "__main__":
    main()
