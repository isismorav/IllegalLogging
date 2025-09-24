import geopandas as gpd
import pandas as pd

def tag_and_score_alerts(alerts_gdf: gpd.GeoDataFrame, wdpa_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Tags each alert if it falls inside a protected area and computes a risk score.
    Risk score: (in_protected * 2) + (near_road * 1) + (cluster_size >= 5)
    Assumes alerts_gdf has 'near_road' (bool) and 'cluster_size' (int) columns.
    Returns alerts_gdf with new columns: 'in_protected', 'risk_score'.
    """
    # Spatial join to tag alerts inside protected areas
    alerts_gdf = alerts_gdf.copy()
    alerts_gdf['in_protected'] = gpd.sjoin(alerts_gdf, wdpa_gdf, predicate='within', how='left').index_right.notnull().astype(int)
    # Compute risk score
    alerts_gdf['risk_score'] = (
        alerts_gdf['in_protected'] * 2 +
        alerts_gdf['near_road'].astype(int) * 1 +
        (alerts_gdf['cluster_size'] >= 5).astype(int)
    )
    return alerts_gdf
