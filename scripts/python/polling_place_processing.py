"""
Polling Place Data Processing
Validates and standardizes client-provided polling location shapefile
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import Point

PROJECT_ROOT = Path(__file__).parent.parent.parent

def load_client_polling_places():
    """
    loading the client-provided polling place shapefile
    """
    
    shapefile_path = PROJECT_ROOT / "data/polling/raw/Polling-Places-Alabama/Al_Polls_Flood_SLED.shp"
    
    # reading shapefile
    
    gdf = gpd.read_file(shapefile_path)
    
    print(f"Loaded {len(gdf)} polling places")
    print(f"CRS: {gdf.crs}")
    print(f"Columns: {list(gdf.columns)}")
    
    return gdf

def standardize_polling_place_fields(gdf):
    """
    standardizing column names and creating consistent identifiers
    """
    # original columns for debugging
    
    print("\nOriginal column names:")
    for col in gdf.columns:
        print(f"  - {col}")
    
    # keeping original columns and adding standardized versions
    
    gdf['polling_place_id'] = gdf.index.astype(str).str.zfill(4)
    gdf['longitude'] = gdf.geometry.x
    gdf['latitude'] = gdf.geometry.y
    
    return gdf

def create_polling_place_database(gdf):
    """
    Exporting to multiple formats for different use cases
    """
    
    # saving as CSV (non-spatial use)
    
    csv_path = PROJECT_ROOT / "data/polling/processed/polling_places_montgomery_clean.csv"
    df = gdf.drop(columns=['geometry']).copy()
    df.to_csv(csv_path, index=False)
    
    # saving as GeoJSON (spatial use)
    
    geojson_path = PROJECT_ROOT / "data/polling/processed/polling_places_montgomery.geojson"
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    print(f"\nExported to: {csv_path}")
    print(f"Exported to: {geojson_path}")

if __name__ == "__main__":
    # loading data
    
    polling_gdf = load_client_polling_places()
    
    # skipping boundary validation for now
    
    print("\nVerify using geographic boundaries if necessary (was client provided file)")
    validated_gdf = polling_gdf.copy()
    
    # standardizing fields
    
    standardized_gdf = standardize_polling_place_fields(validated_gdf)
    
    # exporting
    
    create_polling_place_database(standardized_gdf)
    
    # summary statistics
    
    print("\nPolling Place Summary:")
    print(f"Total polling places: {len(standardized_gdf)}")