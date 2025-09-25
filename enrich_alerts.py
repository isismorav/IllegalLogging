import geopandas as gpd
import pandas as pd

# Load GeoJSON and CSV
alerts_gdf = gpd.read_file("alert_data.geojson")
scores_df = pd.read_csv("scored_alerts.csv")

# Merge by alert ID (replace 'id' with your actual ID column name)
merged = alerts_gdf.merge(scores_df, on="id", how="left")

# Add risk_score and color to properties
if 'properties' in merged.columns:
    for idx, row in merged.iterrows():
        props = merged.at[idx, 'properties']
        props['risk_score'] = row['risk_score']
        props['color'] = row['color']
        merged.at[idx, 'properties'] = props
else:
    # If no 'properties' column, add as new columns
    merged['risk_score'] = merged['risk_score']
    merged['color'] = merged['color']

# Save enriched GeoJSON
merged.to_file("enriched_alert_data.geojson", driver="GeoJSON")
