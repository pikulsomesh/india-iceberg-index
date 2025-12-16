# India Iceberg Index

The **India Iceberg Index** is a comprehensive economic analysis and visualization project that quantifies the exposure of the Indian workforce to Generative AI.

While traditional metrics often focus on the "surface" of AI adoption (like the number of tech jobs), the Iceberg Index goes deeper. It measures the "submerged" exposure—the portion of occupational tasks across the *entire* economy that are technically compatible with AI automation, weighted by the wages of those jobs.

This repository serves as the deployment source for the [interactive Streamlit application](https://india-iceberg-index.streamlit.app/) (link placeholder) and hosts the technical documentation for the project.

## Research & Methodology
This work adapts the "Iceberg Index" methodology (originally developed by [Chopra et al.](https://arxiv.org/pdf/2510.25137)) to the Indian context. We answer questions like:
*   *Which districts in India have the highest concentration of AI-exposed wages?*
*   *What percentage of employment is structurally exposed to Generative AI?*

We achieve this by combining:
1.  **AI Automability Scores**: Mapped to India's National Classification of Occupations (NCO 2015).
2.  **PLFS Data**: Utilizing the extensive 2023-24 Periodic Labor Force Survey to map occupational distribution at the district level.

### Technical Paper
For a deep dive into the methodology, data sources, and full economic analysis, please refer to the technical paper included in this repository:

📄 **Read the [Technical Paper](https://github.com/pikulsomesh/india-iceberg-index/blob/main/I3-Technical.pdf)**

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
**Somesh Mohapatra, PhD, MBA**

Somesh Mohapatra is an independent researcher specializing in artificial intelligence and its implications in different sectors. Recently, he has been focused on measuring AI-driven occupational risks such as the Indian Iceberg Index for automation exposure across districts and sectors. He holds a PhD in Artificial Intelligence and an MBA, both from the Massachusetts Institute of Technology, and is a Gold Medalist from the Indian Institute of Technology Roorkee. His professional experience spans industry and research, including leadership roles in AI, analytics, and digital transformation at Caterpillar Inc., and prior research work at Google, Amgen Inc, alongside co-founding an AI startup serving manufacturing clients in India and the United States.

*Disclaimer: This is a personal research project.*
