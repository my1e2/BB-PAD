"""
Election Data Processing for Montgomery County, Alabama
Processes 2020 and 2024 precinct-level election results
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent # go up 3 folders to mark root folder (should work on any computer)

def load_2024_election_data():
    """
    Load and process 2024 general election data from RDH shapefile
    """
    
    shapefile_path = PROJECT_ROOT / "data/shapefiles/precincts/al_2024_gen_prec/al_2024_gen_all_prec/al_2024_gen_all_prec.shp"
    
    gdf = gpd.read_file(shapefile_path)
    montgomery_gdf = gdf[gdf['County'] == 'Montgomery'].copy()
    montgomery_gdf = montgomery_gdf[montgomery_gdf['COUNTYFP'] == '101']
    
    print(f"{len(montgomery_gdf)} precincts for Montgomery County (2024)")
    
    vote_columns = {
        'dem_pres': 'G24PREDHAR',
        'rep_pres': 'G24PRERTRU',
        'ind_pres_kennedy': 'G24PREIKEN',
        'ind_pres_oliver': 'G24PREIOLI',
        'ind_pres_stein': 'G24PREISTE',
        'writein_pres': 'G24PREOWRI'
    }
    
    for col_name, source_col in vote_columns.items():
        if source_col in montgomery_gdf.columns:
            montgomery_gdf[col_name] = pd.to_numeric(montgomery_gdf[source_col], errors='coerce').fillna(0)
    
    montgomery_gdf['total_pres_votes_2024'] = (
        montgomery_gdf['dem_pres'] + montgomery_gdf['rep_pres'] + 
        montgomery_gdf['ind_pres_kennedy'] + montgomery_gdf['ind_pres_oliver'] +
        montgomery_gdf['ind_pres_stein'] + montgomery_gdf['writein_pres']
    )
    
    montgomery_gdf['dem_share_2024'] = np.where(
        montgomery_gdf['total_pres_votes_2024'] > 0,
        montgomery_gdf['dem_pres'] / montgomery_gdf['total_pres_votes_2024'],
        0
    )
    
    # saving outputs
    
    output_path = PROJECT_ROOT / "data/elections/processed/montgomery_precinct_results_2024.csv" # csv (non-spatial use)
    montgomery_gdf.drop(columns=['geometry']).to_csv(output_path, index=False)
    
    geojson_path = PROJECT_ROOT / "data/elections/processed/montgomery_precincts_2024.geojson" # geojson (spatial use)
    montgomery_gdf.to_file(geojson_path, driver='GeoJSON')
    
    return montgomery_gdf

def load_2020_election_data():
    """
    Load and process 2020 general election data from UFL shapefile
    Montgomery County FIPS = '101'
    """
    shapefile_path = PROJECT_ROOT / "data/shapefiles/precincts/al_2020/al_2020.shp"
    
    gdf = gpd.read_file(shapefile_path)
    print(f"{len(gdf)} total precincts")
    
    # filtering by FIPS code (Montgomery = 101)
    
    montgomery_gdf = gdf[gdf['COUNTYFP20'] == '101'].copy()
    
    print(f"Filtered to {len(montgomery_gdf)} precincts for Montgomery County (2020)")
    
    # renaming for consistency with norms of 2024 data (newer)
    
    montgomery_gdf.rename(columns={
        'COUNTYFP20': 'COUNTYFP',
        'NAME20': 'Precinct'
    }, inplace=True)
    
    vote_columns_2020 = {
        'dem_pres': 'G20PREDBID',
        'rep_pres': 'G20PRERTRU',
        'lib_pres': 'G20PRELJOR',
        'writein_pres': 'G20PREOWRI'
    }
    
    for col_name, source_col in vote_columns_2020.items():
        if source_col in montgomery_gdf.columns:
            montgomery_gdf[col_name] = pd.to_numeric(montgomery_gdf[source_col], errors='coerce').fillna(0)
    
    montgomery_gdf['total_pres_votes_2020'] = (
        montgomery_gdf['dem_pres'] + montgomery_gdf['rep_pres'] + 
        montgomery_gdf['lib_pres'] + montgomery_gdf['writein_pres']
    )
    
    montgomery_gdf['dem_share_2020'] = np.where(
        montgomery_gdf['total_pres_votes_2020'] > 0,
        montgomery_gdf['dem_pres'] / montgomery_gdf['total_pres_votes_2020'],
        0
    )
    
    # saving outputs
    
    output_path = PROJECT_ROOT / "data/elections/processed/montgomery_precinct_results_2020.csv" # csv (non-spatial use)
    montgomery_gdf.drop(columns=['geometry']).to_csv(output_path, index=False)
    
    geojson_path = PROJECT_ROOT / "data/elections/processed/montgomery_precincts_2020.geojson" # geojson (spatial use)
    montgomery_gdf.to_file(geojson_path, driver='GeoJSON')
    
    return montgomery_gdf

def load_county_registration_data():
    """
    Load total registered voters from 2020 General Total Ballots Cast Report
    """
    csv_path = PROJECT_ROOT / "data/elections/raw/2020_General_Total_Ballots_Cast_Report.csv"
    
    df = pd.read_csv(csv_path)
    montgomery_row = df[df['County'] == 'Montgomery'].iloc[0]
    
    # converting string to int (removes commas if present for large numbers)
    
    registered_voters = int(str(montgomery_row['Registered Voters']).replace(',', ''))
    total_ballots = int(str(montgomery_row['Total Ballots Cast']).replace(',', ''))
    
    print(f"Montgomery County 2020 Registered Voters: {registered_voters:,}")
    print(f"Montgomery County 2020 Turnout: {(total_ballots/registered_voters)*100:.1f}%")
    
    return {
        'county': 'Montgomery',
        'registered_voters_2020': registered_voters,
        'total_ballots_2020': total_ballots,
        'turnout_rate_2020': total_ballots / registered_voters
    }

def merge_election_years():
    """
    Merge 2020 and 2024 election data using manual name mapping
    """
    gdf_2024 = load_2024_election_data()
    gdf_2020 = load_2020_election_data()
    
    print("\nMerging Election Years via Manual Mapping: ")
    
    # manual mapping to match 2024 to 2020 precinct names (found inconsistencies in client provided SPLC files)
    
    precinct_mapping = {
        # 100-series precincts
        
        '101 WILSON COMM & ATHLETIC CTR': 'AFED Conference Ctr',
        '102 VAUGHN PARK CH': 'Vaughn Park Church of Christ',
        '103 MUSEUM OF FINE ARTS': 'Museum of Fine Arts',
        '104 WHITFIELD METHODIST': 'Whitfield UMC',
        '105 ALDERSGATE METHODIST': 'Aldersgate UMC',
        '106 CITY OF REFUGE CH': 'City of Refuge Church',
        '107 TRENHOLM COMM COLLEGE': 'Trenholm St Comm College',
        
        # 200-series precincts
        
        '201 ST PAUL AME CH': 'St Paul AME Church',
        '202 BEULAH BAPT CH': 'Beulah Baptist',
        '203 HAYNEVILLE RD COMM CTR': 'Hayneville Rd Comm Ctr',
        '204 REBIRTH CHRISTIAN MINISTRI': None,  # No 2020 equivalent
        '205 SOUTHLAWN BAPT': 'Southlawn Baptist',
        '206 TWIN GATES COMM CTR': None,  # No 2020 equivalent
        '207 HUNTER STATION CC': 'Hunter Station Comm Ctr',
        '208 STONETANK ANTIOCH BAPT': None,  # No 2020 equivalent
        '209 1ST SOUTHERN BAPT': 'First Southern Baptist',
        '210 PINTLALA FIRE DEPT': 'Pintlala VFD',
        '211 RUFUS LEWIS LIBRARY': 'Rufus Lewis Library',
        '212 MACEDONIA BAPT CH': 'Macedonia Miracle Worship Ctr',
        
        # 300-series precincts
        
        '301 DALRAIDA CH CHRIST': 'Dalraida Church of Christ',
        '302 EASTERN HILLS BAPT': 'Eastern Hills Baptist',
        '303 EASTMONT BAPT CH': 'Eastmont Baptist',
        '304 OLD ELAM BAPT': None,  # No 2020 equivalent
        '305 FRAZER CHURCH': 'Frazer UMC',
        '306 EASTDALE BAPT CH': 'Eastdale Baptist',
        
        # 400-series precincts
        
        '401 ST_ JAMES BAPT CH': 'St James Baptist',
        '402 MCINTYRE CC': 'McIntyre Comm Ctr',
        '403 CLEVELAND AVE YMCA': 'Cleveland Ave YMCA',
        '404 ASU ACADOME': 'AL State University Acadome',
        '405 HOUSTON HILLS CC': 'Houston Hills Comm Ctr',
        '406 NEWTOWN COMM CTR': 'Newtown Comm Ctr',
        '407 HILTON L TRACY LARKIN CC': None,  # No 2020 equivalent (formerly King Hill?)
        '408 HIGHLAND GARDEN CC': 'Highland Gardens Comm Ctr',
        '409 BETTER COVENANT MINS': 'Covenant Ministries',
        '410 WEEPING WILLOW BAPT': None,  # No 2020 equivalent
        '411 UNION ACADEMY BAPT': 'Union Academy Baptist',
        '412 UNION CHAPEL AME': 'Union Chapel AME Church',
        '413 PASSION CH MONTGOMERY': 'Passion Church Montgomery',
        '414 NEW HOME BAPT CH': None,  # No 2020 equivalent
        
        # 500-series precincts
        
        '501 1ST CHRISTIAN CH': 'First Christian Church',
        '502 SNOWDOUN VFD': "Snowdoun Women's Club",
        '503 LAPINE BAPT CH': 'Lapine Baptist',
        '504 RAMER PUBLIC LIBRARY': 'Ramer Library',
        '505 ROLLING HILLS LAKE VFD': None,  # No 2020 equivalent
        '506 DAVIS CROSSRODS': 'Davis Crossroads Fire St',
        '507 DUBLIN SO MO VFD': 'Dublin Fire St',
        '508 PINE LEVEL SO MO VFD': 'Pine Level Fire St',
        '509 WOODLAND UN METHODIST': 'Woodland UMC',
        '510 ANTIOCH BAPT CH': None,  # No 2020 equivalent
        '511 AUM OUTREACH CTR': None,  # No 2020 equivalent (AUM campus)
        '512 ST JAMES METHODIST': 'St James UMC',
        
        # additional 2020 precincts not matched (may be consolidated or renamed)
        # 'Arrowhead Country Club' - appears to be gone in 2024
        # 'Catoma Elementary' - appears to be gone in 2024
        # 'Chisholm Comm Ctr' - appears to be gone in 2024
        # 'Georgia Washington Mid School' - appears to be gone in 2024
        # 'King Hill Comm Ctr' - may be now 'HILTON L TRACY LARKIN CC'
        # 'Lagoon Park Fire St' - appears to be gone in 2024
        # 'Leo Drum Theater/Huntingdon' - appears to be gone in 2024
        # 'Sheridan Heights Comm Ctr' - appears to be gone in 2024
    }
    
    # creating mapping dataframe to store these in
    
    mapping_df = pd.DataFrame([
        {'Precinct_2024': k, 'Precinct_2020': v}
        for k, v in precinct_mapping.items()
    ])
    
    # merging 2024 with mapping (left join - keeping all rows from 2020, pulling matches from 2024)
    
    gdf_2024_mapped = gdf_2024.merge(
        mapping_df,
        left_on='Precinct',
        right_on='Precinct_2024',
        how='left'
    )
    
    # preparing 2020 data for merge
    
    df_2020_subset = gdf_2020[['Precinct', 'total_pres_votes_2020', 'dem_share_2020', 
                                'dem_pres', 'rep_pres', 'lib_pres', 'writein_pres']].copy()
    df_2020_subset = df_2020_subset.rename(columns={ # consistency
        'dem_pres': 'dem_pres_2020',
        'rep_pres': 'rep_pres_2020',
        'lib_pres': 'lib_pres_2020',
        'writein_pres': 'writein_pres_2020'
    })
    
    # merging with 2020 data (left join - keeping all rows from 202)
    
    merged = gdf_2024_mapped.merge(
        df_2020_subset,
        left_on='Precinct_2020',
        right_on='Precinct',
        how='left',
        suffixes=('', '_drop')
    )
    
    # cleaning up duplicate columns
    
    if 'Precinct_drop' in merged.columns:
        merged = merged.drop(columns=['Precinct_drop'])
    
    # calculating turnout changes for matched precincts
    
    merged['turnout_change'] = merged['total_pres_votes_2024'] - merged['total_pres_votes_2020']
    merged['turnout_pct_change'] = np.where(
        merged['total_pres_votes_2020'].notna() & (merged['total_pres_votes_2020'] > 0),
        (merged['turnout_change'] / merged['total_pres_votes_2020']) * 100,
        np.nan
    )
    
    # checking for matched/unmatched precincts
    
    merged['has_2020_match'] = merged['Precinct_2020'].notna()
    
    # summary statistics
    
    total_2024 = len(merged)
    matched = merged['has_2020_match'].sum()
    unmatched = total_2024 - matched
    
    print(f"\nMerge Results:")
    print(f"  Total 2024 precincts: {total_2024}")
    print(f"  Matched to 2020 data: {matched}")
    print(f"  Unmatched (new precincts): {unmatched}")
    
    # unmatched precincts for documentation
    
    if unmatched > 0:
        print(f"\n  Unmatched 2024 precincts (no 2020 equivalent):")
        for p in merged[~merged['has_2020_match']]['Precinct'].tolist():
            print(f"    - {p}")
    
    # 2020 precincts that weren't matched (consolidated/removed)
    
    matched_2020_names = set(precinct_mapping.values())
    unmatched_2020 = set(gdf_2020['Precinct'].unique()) - matched_2020_names
    if unmatched_2020:
        print(f"\n  2020 precincts not present in 2024 (consolidated/removed):")
        for p in sorted(unmatched_2020):
            print(f"    - {p}")
    
    # dropping temporary columns for workflow
    
    merged = merged.drop(columns=['Precinct_2024', 'Precinct_2020', 'has_2020_match'])
    
    # saving outputs
    
    output_path = PROJECT_ROOT / "data/elections/processed/election_data_combined_2020_2024.csv"
    merged.drop(columns=['geometry']).to_csv(output_path, index=False)
    
    geojson_path = PROJECT_ROOT / "data/elections/processed/montgomery_precincts_combined_2020_2024.geojson"
    merged.to_file(geojson_path, driver='GeoJSON')
    
    print(f"\n  Outputs saved to:")
    print(f"    - {output_path}")
    print(f"    - {geojson_path}")
    
    return merged

if __name__ == "__main__": # execution
    
    print("2024 Election Data:")
    gdf_2024 = load_2024_election_data()
    
    print("\n2020 Election Data:")
    gdf_2020 = load_2020_election_data()
    
    print("\nCounty Registration Data:")
    reg_data = load_county_registration_data()
    
    print("\nMerged Election Years:")
    merged_data = merge_election_years()
    
    print(f"2024 precincts: {len(gdf_2024)}")
    print(f"2020 precincts: {len(gdf_2020)}")
    if merged_data is not None:
        print(f"Merged dataset: {len(merged_data)} rows")