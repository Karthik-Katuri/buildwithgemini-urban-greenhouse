# Copyright 2026 Google LLC
# Google Maps Geocoding and Places API (New) REST Tools

import os
from typing import Any, Optional
import requests

def _get_api_key() -> str:
    """Retrieves the Google Maps API key from the environment."""
    key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not key or key == "PASTE_KEY_HERE":
        raise ValueError(
            "GOOGLE_MAPS_API_KEY is not set or still contains placeholder. "
            "Please set a valid Maps API key in your .env file."
        )
    return key


def geocode_address(address: str) -> dict[str, Any]:
    """Converts a street address or location name into geographic latitude and longitude coordinates.

    Args:
        address: The address, city, or location name to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A dictionary with formatted address, latitude, longitude, and place_id.
    """
    try:
        api_key = _get_api_key()
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": api_key}
        
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        status = data.get("status")
        if status != "OK" or not data.get("results"):
            error_msg = data.get("error_message", f"Status: {status}")
            return {"error": f"Geocoding failed for '{address}': {error_msg}"}
            
        result = data["results"][0]
        loc = result["geometry"]["location"]
        return {
            "formatted_address": result.get("formatted_address"),
            "latitude": loc.get("lat"),
            "longitude": loc.get("lng"),
            "place_id": result.get("place_id"),
        }
    except Exception as e:
        return {"error": str(e)}


def find_nearby_places(
    latitude: float,
    longitude: float,
    included_types: Optional[list[str]] = None,
    radius_meters: float = 5000.0,
    max_result_count: int = 5
) -> list[dict[str, Any]]:
    """Finds nearby places using the Google Places API (New) searchNearby endpoint.

    Args:
        latitude: Latitude coordinate of the search center.
        longitude: Longitude coordinate of the search center.
        included_types: Optional list of place types (e.g. ['florist'], ['park'], ['plant_nursery'], ['store']).
        radius_meters: Search radius in meters (max 50000, default 5000).
        max_result_count: Number of results to return (1 to 20, default 5).

    Returns:
        A list of nearby places containing name, formatted address, and coordinates.
    """
    try:
        api_key = _get_api_key()
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.id,places.primaryType"
        }
        
        body: dict[str, Any] = {
            "maxResultCount": max_result_count,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius_meters
                }
            }
        }
        
        if included_types:
            body["includedTypes"] = included_types

        resp = requests.post(url, headers=headers, json=body, timeout=10)
        data = resp.json()
        
        if "error" in data:
            return [{"error": data["error"].get("message", "Places API error")}]
            
        places = []
        for place in data.get("places", []):
            loc = place.get("location", {})
            name_obj = place.get("displayName", {})
            display_name = name_obj.get("text", "") if isinstance(name_obj, dict) else str(name_obj)
            places.append({
                "name": display_name,
                "address": place.get("formattedAddress", ""),
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude")
                },
                "place_id": place.get("id"),
                "primary_type": place.get("primaryType")
            })
            
        return places
    except Exception as e:
        return [{"error": str(e)}]
