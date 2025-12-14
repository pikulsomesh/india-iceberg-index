# India Iceberg Index - Streamlit App

This repository contains the Streamlit application for the **Indian Iceberg Index**, a tool designed to visualize the exposure of the Indian workforce to Artificial Intelligence.

## Project Context & Methodology

While traditional metrics often focus on the "surface" of AI adoption (like the number of tech jobs), the **Iceberg Index** goes deeper. It measures the "submerged" exposure—the portion of occupational tasks across the *entire* economy that are technically compatible with AI automation, weighted by the wages of those jobs.

This application provides a district-level view of this AI exposure by combining two critical datasets:

1.  **AI Automability Scores (The Iceberg Index)**: derived from **Felten et al. (2023)** and mapped to India's National Classification of Occupations (NCO 2015). This index quantifies how much of a job's core tasks can be performed by Language Modeling AI.
2.  **Periodic Labor Force Survey (PLFS) Data**: Using the 2023-24 panel data to understand the real-world distribution of these occupations across India's districts.

By merging these, we can answer: *Which districts in India have the highest concentration of AI-exposed wages?* and *What percentage of employment is structurally exposed to Generative AI?*

## Folder Structure
- `app.py`: Main application entry point.
- `src/`: Source code modules.
- `data/`: Aggregated index data and census reference files.
- `methodology.md`: Documentation of the index calculation.

## How to Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   streamlit run app.py
   ```

## Data Privacy
This repository contains only aggregated district-level indices (`data/district_iceberg_indices.csv`) and public Census data (`data/india.csv`). No raw PLFS microdata is included.

## Author
**Somesh Mohapatra**  
*PhD in AI (MIT) | MBA in Operations (MIT Sloan)*

This is a personal project developed to explore the economic impact of AI. 
**Disclaimer**: No external support or sponsorship was provided for this work.
