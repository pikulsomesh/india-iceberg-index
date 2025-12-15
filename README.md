# India Iceberg Index

The **India Iceberg Index** is a comprehensive economic analysis and visualization project that quantifies the exposure of the Indian workforce to Generative AI.

While traditional metrics often focus on the "surface" of AI adoption (like the number of tech jobs), the Iceberg Index goes deeper. It measures the "submerged" exposure—the portion of occupational tasks across the *entire* economy that are technically compatible with AI automation, weighted by the wages of those jobs.

This repository serves as the deployment source for the [interactive Streamlit application](https://india-iceberg-index.streamlit.app/) (link placeholder) and hosts the technical documentation for the project.

## Research & Methodology

This work adapts the "Iceberg Index" methodology (originally developed by Felten et al.) to the Indian context. We answer:
*   *Which districts in India have the highest concentration of AI-exposed wages?*
*   *What percentage of employment is structurally exposed to Generative AI?*

We achieve this by combining:
1.  **AI Automability Scores**: Mapped to India's National Classification of Occupations (NCO 2015).
2.  **PLFS Data**: Utilizing the extensive 2023-24 Periodic Labor Force Survey to map occupational distribution at the district level.

### Technical Paper
For a deep dive into the methodology, data sources, and full economic analysis, please refer to the technical paper included in this repository:

📄 **[Read the Technical Paper (I3-Technical)] (I3-Technical.pdf)**

## Streamlit Application

The application code in this repository powers the interactive dashboard, allowing users to:
-   Explore AI exposure heatmaps across Indian districts.
-   Analyze the "Iceberg Index" vs. Census variables (literacy, urbanization, etc.).
-   Drill down into specific state-level data.

### Running Locally

1.  Start the app:
    ```bash
    pip install -r requirements.txt
    streamlit run app.py
    ```

## Author
**Somesh Mohapatra**
*PhD in AI (MIT) | MBA in Operations (MIT Sloan)*

*Disclaimer: This is a personal research project.*
