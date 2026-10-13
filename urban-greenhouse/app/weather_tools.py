# Copyright 2026 Google LLC
# Weather and environmental climate tool for plant care using Open-Meteo public API

from typing import Any
import requests

def get_plant_climate_conditions(city: str) -> dict[str, Any]:
    """Fetches real-time temperature, humidity, and atmospheric conditions for a given city to guide indoor/outdoor plant care.

    Args:
        city: Name of the city (e.g. 'San Francisco', 'New York', 'Seattle', 'Miami').

    Returns:
        A dictionary containing real temperature (°F), relative humidity (%), precipitation, and ambient conditions.
    """
    try:
        # Step 1: Geocode city name to lat/long using Open-Meteo free geocoding
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city, "count": 1, "format": "json"}, timeout=5)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return {"error": f"City '{city}' not found."}

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        city_name = loc.get("name", city)
        region = loc.get("admin1", "")
        country = loc.get("country", "")

        # Step 2: Fetch current weather, temp, and relative humidity
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_resp = requests.get(
            weather_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
                "temperature_unit": "fahrenheit",
            },
            timeout=5,
        )
        weather_resp.raise_for_status()
        curr = weather_resp.json().get("current", {})

        temp_f = curr.get("temperature_2m")
        humidity = curr.get("relative_humidity_2m")
        precip = curr.get("precipitation")

        return {
            "city": f"{city_name}, {region}" if region else city_name,
            "country": country,
            "temperature_f": temp_f,
            "relative_humidity_percent": humidity,
            "precipitation_mm": precip,
            "air_quality_plant_note": (
                "High humidity: tropicals thrive." if humidity and humidity > 60
                else "Dry air: tropical plants and ferns may need extra humidity or misting." if humidity and humidity < 40
                else "Moderate humidity: ideal for most houseplants."
            )
        }
    except Exception as e:
        return {"error": f"Failed to fetch climate conditions: {str(e)}"}
