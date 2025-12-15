import pandas as pd
import numpy as np
import os

ICEBERG_PATH = "data/district_iceberg_indices_filled.csv"
ICEBERG_PATH = "data/district_iceberg_indices_filled.csv"
GEOJSON_PATH = "data/india_districts_filled.geojson"
CENSUS_PATH = "data/india.csv"

def load_data():
    """
    Load pre-filled Iceberg Index data (with coordinates) and Census demographics.
    Returns:
        df: Merged DataFrame
        stats: Dictionary of summary statistics
    """
    # 1. Load Iceberg Data (Filled)
    if not os.path.exists(ICEBERG_PATH):
        raise FileNotFoundError(f"Iceberg Index file not found at {ICEBERG_PATH}")
    
    df = pd.read_csv(ICEBERG_PATH)
    
    # Map columns to expected names for UI
    # Filled CSV has: District, State, iceberg_index, Latitude, Longitude, Type
    df = df.rename(columns={
        'District': 'District_Name',
        'State': 'State_Name'
    })
    
    # 2. Load Census Data (Optional merge for extra metrics)
    # We kept logic to load census, but we don't need it for Lat/Long anymore as df has it.
    if os.path.exists(CENSUS_PATH):
        try:
            df_census = pd.read_csv(CENSUS_PATH)
            # Normalize names for merging
            df_census['District_Clean'] = df_census['District'].str.lower().str.strip()
            df['District_Clean'] = df['District_Name'].str.lower().str.strip()
            
            # Merge left (keep all filled districts)
            # Only bring in metrics, NOT lat/long
            merged = df.merge(
                df_census[['District_Clean', 'Population', 'literacy_rate', 'Workers', 'Agricultural_Workers', 'Households_with_Internet']], 
                on='District_Clean', 
                how='left'
            )
            df = merged
        except Exception as e:
            print(f"Warning: Census merge failed: {e}")
            # Continue with just iceberg data

    # 3. Calculate National Stats based on loaded data
    # Create valid total_employment for visualization sizing
    # If merged with census, we have 'Workers'. Use that if total_employment is missing.
    if 'total_employment' not in df.columns or df['total_employment'].sum() <= len(df): # Check if it's just the dummy 1s
        if 'Workers' in df.columns:
            df['total_employment'] = df['Workers']
        else:
            df['total_employment'] = 1000 # Default dummy
            
            
    # Scaling for display (Millions) is handled in UI usually, but let's keep raw here.
    df['total_employment'] = df['total_employment'].fillna(0)
    
    # Fix Scale Issue: Input seems to be in thousands (e.g. 142M for a district).
    # Census Workers is usually ~100k-1M per district.
    # We detect if mean is too high (> 10M) and scale down.
    if df['total_employment'].mean() > 10_000_000:
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

def load_geojson():
    """Lengths the GeoJSON file for the interactive map."""
    import json
    if not os.path.exists(GEOJSON_PATH):
        return None
    with open(GEOJSON_PATH, 'r') as f:
        geojson = json.load(f)
    return geojson
