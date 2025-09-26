import streamlit as st
import json
import leafmap.foliumap as leafmap
import pandas as pd

def load_gdf(file_path):
    if file_path.endswith('.geojson'):
        with open(file_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        return geojson_data
    elif file_path.endswith('.csv'):
        return pd.read_csv(file_path)
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
                return df
            else:
                st.error("CSV missing latitude/longitude columns.")
                return None
        else:
            geojson_data = json.load(path_or_file) if hasattr(path_or_file, 'read') else json.load(open(path_or_file, 'r', encoding='utf-8'))
            return geojson_data

    if files_exist:
        alerts_df = load_alerts(alerts_path)
        with open(wdpa_path, 'r', encoding='utf-8') as f:
            wdpa_geojson = json.load(f)
        with open(roads_path, 'r', encoding='utf-8') as f:
            roads_geojson = json.load(f)
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
                alerts_df = pd.read_csv(alerts_file)
                if 'latitude' not in alerts_df.columns or 'longitude' not in alerts_df.columns:
                    st.error("CSV missing latitude/longitude columns.")
                    return
            else:
                alerts_df = json.load(alerts_file)
            # If scored alerts CSV is uploaded, match by ID and use color from CSV
            color_map = None
            if scored_file and alerts_file.name.endswith('.csv'):
                scored_df = pd.read_csv(scored_file)
                if 'id' in alerts_df.columns and 'id' in scored_df.columns and 'color' in scored_df.columns:
                    color_map = dict(zip(scored_df['id'], scored_df['color']))
                    alerts_df['color'] = alerts_df['id'].map(color_map)
                else:
                    st.warning("ID or color column not found in both alerts and scored CSVs. No color mapping performed.")
            wdpa_geojson = json.load(wdpa_file)
            roads_geojson = json.load(roads_file)
        else:
            st.info("Upload all three files to view the map and export alerts.")
            return

    # Convert all Timestamp/datetime objects to string for mapping
    import numpy as np
    if 'alerts_df' in locals():
        for col in alerts_df.columns:
            try:
                if np.issubdtype(alerts_df[col].dtype, np.datetime64):
                    alerts_df[col] = alerts_df[col].astype(str)
                else:
                    alerts_df[col] = alerts_df[col].apply(lambda x: x.isoformat() if hasattr(x, 'isoformat') else x)
            except TypeError:
                pass

    import folium
    # Map center: use mean lat/lon from alerts_df if CSV, else use first feature from geojson
    if 'alerts_df' in locals():
        center_lat = alerts_df['latitude'].mean()
        center_lon = alerts_df['longitude'].mean()
    else:
        coords = alerts_df['features'][0]['geometry']['coordinates']
        center_lon, center_lat = coords if len(coords) == 2 else coords[0]
    m = leafmap.Map(center=[center_lat, center_lon], zoom=7)
    # Add colored alert pins using folium.Marker and folium.Icon
    if 'alerts_df' in locals() and 'color' in alerts_df.columns:
        for _, row in alerts_df.iterrows():
            color = row['color'] if row['color'] in ['red', 'orange', 'green'] else 'blue'
            popup = folium.Popup(f"ID: {row.get('id', '')}<br>Risk Score: {row.get('risk_score', '')}<br>Color: {color}", max_width=250)
            marker = folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup,
                icon=folium.Icon(color=color)
            )
            marker.add_to(m)
    elif 'alerts_df' in locals():
        for _, row in alerts_df.iterrows():
            marker = folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(f"ID: {row.get('id', '')}", max_width=250)
            )
            marker.add_to(m)
    else:
        m.add_geojson(alerts_df, layer_name="Alerts")
    m.add_geojson(wdpa_geojson, layer_name="WDPA Protected Areas")
    m.add_geojson(roads_geojson, layer_name="Roads")
    m.to_streamlit(height=600)

    # Add legend for color meanings
    st.markdown("""
    <b>Alert Risk Legend:</b><br>
    <span style='color:red;'>Red</span>: High risk<br>
    <span style='color:orange;'>Orange</span>: Medium risk<br>
    <span style='color:green;'>Green</span>: Low risk<br>
    """, unsafe_allow_html=True)

    st.subheader("Export Alerts as CSV")
    if 'alerts_df' in locals():
        csv = alerts_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "alerts.csv", "text/csv")

if __name__ == "__main__":
    main()
