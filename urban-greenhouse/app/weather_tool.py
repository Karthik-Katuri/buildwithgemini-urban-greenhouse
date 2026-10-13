# Copyright 2026 Google LLC
# Real-time climate and humidity lookup using Open-Meteo public API (no API key required)

from typing import Any
import requests

def get_ambient_plant_conditions(city: str) -> dict[str, Any]:
    """Fetches real-time temperature, humidity, and weather conditions for a city.

    Useful for determining if indoor/outdoor plants need extra misting, more frequent
    watering, or protection from dry air / extreme temperatures.

    Args:
        city: City name (e.g. 'San Francisco', 'Chicago', 'Austin', 'London').

    Returns:
        A dictionary with temperature (°F), relative humidity (%), precipitation, and plant care humidity guidance.
    """
    try:
        # Step 1: Geocode city name to lat/long
        geo_resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=5
        )
        geo_data = geo_resp.json()
        if not geo_data.get("results"):
            return {"error": f"Could not find coordinates for city '{city}'."}

        place = geo_data["results"][0]
        lat = place["latitude"]
        lon = place["longitude"]
        resolved_name = f"{place.get('name')}, {place.get('admin1', place.get('country', ''))}"

        # Step 2: Fetch current weather with temperature and relative humidity
        weather_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation",
                "temperature_unit": "fahrenheit"
            },
            timeout=5
        )
        weather_data = weather_resp.json()
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        precip = current.get("precipitation")

        # Botanical guidance based on humidity levels
        if humidity is not None:
            if humidity < 30:
                humidity_status = "Very Dry: High risk of leaf browning or crisping. Misting or humidifiers recommended for tropicals (Calathea, Ferns, Peace Lilies)."
            elif humidity < 50:
                humidity_status = "Moderate: Acceptable for most houseplants. Tropicals may benefit from grouping or a pebble tray."
            else:
                humidity_status = "High Humidity: Optimal for tropical plants and ferns. Ensure good airflow to prevent mold."
        else:
            humidity_status = "Unknown"

        return {
            "city": resolved_name,
            "temperature_f": temp,
            "relative_humidity_percent": humidity,
            "precipitation_mm": precip,
            "botanical_advice": humidity_status
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather conditions: {str(e)}"}
