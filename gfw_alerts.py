import requests
import time
from typing import List, Dict, Any

def post_gfw_alerts(
    geojson_polygon: Dict[str, Any],
    start_date: str,
    end_date: str,
    api_key: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> List[Dict[str, Any]]:
    """
    POSTs to GFW's gfw_integrated_alerts/latest/query endpoint with a GeoJSON polygon and date range.
    Returns a list of dicts with latitude, longitude, date, and confidence.
    Retries with exponential backoff on failure.
    """
    url = "https://production-api.globalforestwatch.org/v1/gfw_integrated_alerts/latest/query"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    payload = {
        "geometry": geojson_polygon,
        "startDate": start_date,
        "endDate": end_date
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            results = []
            for alert in data.get("data", []):
                results.append({
                    "latitude": alert.get("latitude"),
                    "longitude": alert.get("longitude"),
                    "date": alert.get("date"),
                    "confidence": alert.get("confidence")
                })
            return results
        except Exception as e:
            if attempt < max_retries - 1:
                sleep_time = backoff_factor ** attempt
                time.sleep(sleep_time)
            else:
                raise e
