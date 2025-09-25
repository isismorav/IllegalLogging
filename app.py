import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import pandas as pd

def load_gdf(file_path):
    if file_path.endswith('.geojson'):
        return gpd.read_file(file_path)
    elif file_path.endswith('.csv'):
        return gpd.read_file(file_path)
    else:
        st.error('Unsupported file type')
        return None

def main():
    st.title("Illegal Logging Alert Viewer")
    import os
    data_dir = os.path.join(os.path.dirname(__file__), "data", "data", "data")
    alerts_path = os.path.join(data_dir, "gfw_alerts.csv")
    wdpa_path = os.path.join(data_dir, "wdpa.geojson")
    roads_path = os.path.join(data_dir, "roads.geojson")

    # Try to load files automatically
    files_exist = all([os.path.exists(alerts_path), os.path.exists(wdpa_path), os.path.exists(roads_path)])
    def load_alerts(path_or_file):
        if str(path_or_file).endswith('.csv'):
            df = pd.read_csv(path_or_file)
            if 'latitude' in df.columns and 'longitude' in df.columns:
                gdf = gpd.GeoDataFrame(
                    df,
                    geometry=gpd.points_from_xy(df.longitude, df.latitude),
                    crs="EPSG:4326"
                )
                return gdf
            else:
                st.error("CSV missing latitude/longitude columns.")
                return None
        else:
            return gpd.read_file(path_or_file)

    if files_exist:
        alerts_gdf = load_alerts(alerts_path)
        wdpa_gdf = gpd.read_file(wdpa_path)
        roads_gdf = gpd.read_file(roads_path)
        st.success("Loaded data automatically from data/data/data directory.")
    else:
        st.sidebar.header("Data Upload")
        alerts_file = st.sidebar.file_uploader("Upload Alerts GeoJSON/CSV", type=["geojson", "csv"], accept_multiple_files=False)
        scored_file = st.sidebar.file_uploader("Upload Scored Alerts CSV (optional)", type=["csv"], accept_multiple_files=False)
        wdpa_file = st.sidebar.file_uploader("Upload WDPA GeoJSON", type=["geojson"])
        roads_file = st.sidebar.file_uploader("Upload Roads GeoJSON", type=["geojson"])
        if alerts_file and wdpa_file and roads_file:
            # Handle alerts file upload: CSV or GeoJSON
            if alerts_file.name.endswith('.csv'):
                df = pd.read_csv(alerts_file)
                if 'latitude' in df.columns and 'longitude' in df.columns:
                    alerts_gdf = gpd.GeoDataFrame(
                        df,
                        geometry=gpd.points_from_xy(df.longitude, df.latitude),
                        crs="EPSG:4326"
                    )
                else:
                    st.error("CSV missing latitude/longitude columns.")
                    return
            else:
                alerts_gdf = gpd.read_file(alerts_file)
            # If scored alerts CSV is uploaded, match by ID and use color from CSV
            color_map = None
            if scored_file:
                scored_df = pd.read_csv(scored_file)
                if 'id' in alerts_gdf.columns and 'id' in scored_df.columns and 'color' in scored_df.columns:
                    color_map = dict(zip(scored_df['id'], scored_df['color']))
                    alerts_gdf['color'] = alerts_gdf['id'].map(color_map)
                else:
                    st.warning("ID or color column not found in both alerts and scored CSVs. No color mapping performed.")
            wdpa_gdf = gpd.read_file(wdpa_file)
            roads_gdf = gpd.read_file(roads_file)
        else:
            st.info("Upload all three files to view the map and export alerts.")
            return

    # Convert all Timestamp/datetime objects to string for mapping
    import numpy as np
    for col in alerts_gdf.columns:
        if col == 'geometry':
            continue
        try:
            if np.issubdtype(alerts_gdf[col].dtype, np.datetime64):
                alerts_gdf[col] = alerts_gdf[col].astype(str)
            else:
                alerts_gdf[col] = alerts_gdf[col].apply(lambda x: x.isoformat() if hasattr(x, 'isoformat') else x)
        except TypeError:
            pass

    import folium
    m = leafmap.Map(center=[alerts_gdf.geometry.y.mean(), alerts_gdf.geometry.x.mean()], zoom=7)
    # Add colored alert pins using folium.Marker and folium.Icon
    if 'color' in alerts_gdf.columns:
        for _, row in alerts_gdf.iterrows():
            color = row['color'] if row['color'] in ['red', 'orange', 'green'] else 'blue'
            popup = folium.Popup(f"ID: {row.get('id', '')}<br>Risk Score: {row.get('risk_score', '')}<br>Color: {color}", max_width=250)
            marker = folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=popup,
                icon=folium.Icon(color=color)
            )
            marker.add_to(m)
    else:
        m.add_gdf(alerts_gdf, layer_name="Alerts")
    m.add_gdf(wdpa_gdf, layer_name="WDPA Protected Areas")
    m.add_gdf(roads_gdf, layer_name="Roads")
    m.to_streamlit(height=600)

    # Add legend for color meanings
    st.markdown("""
    <b>Alert Risk Legend:</b><br>
    <span style='color:red;'>Red</span>: High risk<br>
    <span style='color:orange;'>Orange</span>: Medium risk<br>
    <span style='color:green;'>Green</span>: Low risk<br>
    """, unsafe_allow_html=True)

    st.subheader("Export Alerts as CSV")
    csv = alerts_gdf.drop(columns='geometry').to_csv(index=False)
    st.download_button("Download CSV", csv, "alerts.csv", "text/csv")

if __name__ == "__main__":
    main()
