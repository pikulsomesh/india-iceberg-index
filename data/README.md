# Data Sources & Descriptions

This directory contains the core datasets used by the Indian Iceberg Index application.

## 1. `district_iceberg_indices.csv`
**Type**: Calculated Output  
**Description**: This file is the primary output of the Iceberg Index methodology. It contains the calculated AI exposure indices for each district.
- **Source**: It is *not* raw data. It is computed by combining the PLFS 2023-24 labor force microdata with the AI Automability scores.
- **Key Metrics**: `iceberg_index` (weighted AI exposure), `total_employment` (estimated workforce), `surprise_index`.

## 2. `india.csv`
**Type**: Census Data  
**Description**: Provides geographic coordinates (Latitude/Longitude) and demographic context (Population, Literacy Rate) for Indian districts.
- **Source**: Obtained from the [India Data Visualization Repository](https://github.com/Mayank-Chourasia77/India_data_visualization/tree/main/India_census_analysis).
- **Purpose**: Used for mapping district names to coordinates for the visualization layer.

## 3. `ai_automability/`
**Type**: Research Data  
**Description**: Contains the AI exposure scores for occupations.
- **Source**: Derived from **Felten et al. (2023)** ("How will Language Modelers like ChatGPT Affect Occupations and Industries?").
- **Content**: `nco_onet_automatability.csv` maps Indian NCO codes to these research-based AIOE scores.

## 4. `job_code_mapping/`
**Type**: Reference / Crosswalk  
**Description**: Documentation and logic for mapping Indian Job Codes (NCO 2015) to U.S. O*NET codes.
- **Source**: 
    - **BLS O*NET**: U.S. Bureau of Labor Statistics.
    - **NCO 2015**: Ministry of Labour and Employment, India.
- **Content**: Raw PDF reference manuals and the Python logic used to bridge the two classification systems.
