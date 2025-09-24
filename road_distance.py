import requests
import geopandas as gpd
from shapely.geometry import LineString, shape
import pandas as pd
from pyproj import CRS

def get_highways_gdf(bbox):
    """
    Downloads highway ways from Overpass API within bbox.
    bbox: (min_lon, min_lat, max_lon, max_lat)
    Returns GeoDataFrame of highways.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      way["highway"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
    );
    out geom;
    """
    response = requests.post(overpass_url, data={'data': query})
    response.raise_for_status()
    data = response.json()
    lines = []
    for element in data['elements']:
        if element['type'] == 'way' and 'geometry' in element:
            coords = [(pt['lon'], pt['lat']) for pt in element['geometry']]
            lines.append(LineString(coords))
    gdf = gpd.GeoDataFrame(geometry=lines, crs="EPSG:4326")
    return gdf

def compute_min_road_distance(alerts_gdf, roads_gdf):
    """
    Computes min distance (meters) from each alert to nearest road.
    Returns alerts_gdf with new column 'min_road_dist_m'.
    """
    # Project to metric CRS for accurate distance
    metric_crs = CRS.from_epsg(3857)
    alerts_proj = alerts_gdf.to_crs(metric_crs)
    roads_proj = roads_gdf.to_crs(metric_crs)
    alerts_proj['min_road_dist_m'] = alerts_proj.geometry.apply(
        lambda pt: roads_proj.distance(pt).min()
    )
    # Add back to original alerts_gdf
    alerts_gdf['min_road_dist_m'] = alerts_proj['min_road_dist_m']
    return alerts_gdf
