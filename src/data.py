import pandas as pd
import numpy as np
import os

ICEBERG_PATH = "data/district_iceberg_indices.csv"
CENSUS_PATH = "data/india.csv"

def load_data():
    """
    Load and merge Iceberg Index data with Census demographics.
    Returns:
        df: Merged DataFrame
        stats: Dictionary of summary statistics
    """
    # 1. Load Iceberg Data
    if not os.path.exists(ICEBERG_PATH):
        raise FileNotFoundError(f"Iceberg Index file not found at {ICEBERG_PATH}")
    
    df_iceberg = pd.read_csv(ICEBERG_PATH)
    
    # 2. Load Census Data
    if os.path.exists(CENSUS_PATH):
        df_census = pd.read_csv(CENSUS_PATH)
        # Normalize names for merging
        df_census['District_Clean'] = df_census['District'].str.lower().str.strip()
        df_census['State_Clean'] = df_census['State'].str.lower().str.strip()
        
        df_iceberg['District_Clean'] = df_iceberg['District_Name'].str.lower().str.strip()
        df_iceberg['State_Clean'] = df_iceberg['State_Name'].str.lower().str.strip()
        
        # Merge
        # Note: Merging on District name primarily within State checking might be tricky due to spelling differences.
        # We will try a left join on District first.
        df = df_iceberg.merge(
            df_census[['District_Clean', 'Latitude', 'Longitude', 'Population', 'literacy_rate', 'Workers', 'Agricultural_Workers']], 
            on='District_Clean', 
            how='left'
        )
    else:
        df = df_iceberg
        # Create placeholder cols if census missing
        for col in ['Latitude', 'Longitude', 'Population', 'literacy_rate']:
            df[col] = np.nan

    # 3. Calculate National Stats based on loaded data
    # Correcting scale: The input total_employment seems to be off by factor of 1000 (390B vs 390M expected)
    df['total_employment'] = df['total_employment'] / 1000
    total_employment = df['total_employment'].sum()
    
    # Weighted average of Iceberg Index
    national_iceberg = np.average(df['iceberg_index'], weights=df['total_employment'])
    
    # Percentage of jobs automated (Exposure Weight / Total Wage Weight is the index definition, 
    # but user asked for "% of jobs". The index calculates share of wage bill exposed.
    # To estimate "jobs", we can look at high exposure thresholds or use the weighted average index as a proxy for "task exposure").
    # The user prompt: "what % of jobs can be automated using AI based on the results".
    # The Iceberg Index itself is "wage-weighted share of occupational skills that AI can perform".
    # We will present the Mean Iceberg Index as the primary "Exposure %".
    
    stats = {
        "national_iceberg_index": national_iceberg,
        "total_workforce_analyzed": total_employment,
        "total_districts": len(df),
        "avg_surprise_index": np.average(df['surprise_index'].fillna(0), weights=df['total_employment']),
        "avg_surface_index": np.average(df['surface_index'].fillna(0), weights=df['total_employment']),
    }
    
    return df, stats
