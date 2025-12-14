import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.data import load_data

try:
    print("Testing data loading...")
    df, stats = load_data()
    print("SUCCESS: Data loaded successfully.")
    print("DataFrame Shape:", df.shape)
    print("Summary Stats:", stats)
    
    # Check for NaN in critical columns for map
    missing_geo = df[['Latitude', 'Longitude']].isna().sum()
    print("\nMissing Geo Data:")
    print(missing_geo)
    
    if len(df) == missing_geo['Latitude']:
        print("WARNING: All latitude data is missing. Map will be empty.")
        # This might happen if merge failed entirely.
        print("Sample District Names (Iceberg):", df['District_Clean'].head().tolist())
        # We can't see Census names here easily without re-reading, but the merge logic in data.py handles reading.
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
