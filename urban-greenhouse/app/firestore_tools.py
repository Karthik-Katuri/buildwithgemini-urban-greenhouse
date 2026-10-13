# Copyright 2026 Google LLC
# Firestore tools for Urban Greenhouse catalog

from typing import Any, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-93b5deb0ee1a"

_db: Optional[firestore.Client] = None

def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client with the hardcoded project ID."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def search_plants(query: str = "") -> list[dict[str, Any]]:
    """Searches the greenhouse plant catalog by name, species, difficulty, or light requirement.

    Args:
        query: Optional search keyword (e.g. 'monstera', 'low light', 'beginner', 'ficus'). If empty, returns all plants.

    Returns:
        A list of plant records matching the query.
    """
    db = get_firestore_client()
    plants_ref = db.collection("plants")
    docs = plants_ref.stream()

    results = []
    clean_query = query.strip().lower()

    for doc in docs:
        data = doc.to_dict()
        if not clean_query:
            results.append(data)
            continue

        searchable_text = f"{data.get('name', '')} {data.get('species', '')} {data.get('light', '')} {data.get('difficulty', '')} {data.get('description', '')}".lower()
        if clean_query in searchable_text:
            results.append(data)

    return results


def get_plant_details(plant_id: str) -> dict[str, Any]:
    """Retrieves full details for a specific plant by its identifier.

    Args:
        plant_id: The unique identifier of the plant (e.g., 'monstera-deliciosa', 'snake-plant').

    Returns:
        A dictionary containing the plant details or an error message if not found.
    """
    db = get_firestore_client()
    doc = db.collection("plants").document(plant_id.strip().lower()).get()
    if not doc.exists:
        return {"error": f"Plant with ID '{plant_id}' not found in the greenhouse catalog."}
    return doc.to_dict()


def add_plant(
    plant_id: str,
    name: str,
    species: str,
    light: str,
    watering: str,
    difficulty: str,
    price: float,
    description: str,
    care_tips: str
) -> dict[str, Any]:
    """Adds or updates a plant record in the greenhouse catalog.

    Args:
        plant_id: Unique slug/id for the plant (e.g., 'calathea-orbifolia').
        name: Common name of the plant.
        species: Botanical/scientific species name.
        light: Lighting requirements (e.g., 'Medium indirect light').
        watering: Watering instructions and frequency.
        difficulty: Care difficulty level ('Beginner', 'Easy', 'Moderate', 'Expert').
        price: Price in USD.
        description: A short overview of the plant.
        care_tips: Helpful maintenance and care advice.

    Returns:
        Status message confirming the record was saved.
    """
    db = get_firestore_client()
    doc_ref = db.collection("plants").document(plant_id.strip().lower())
    payload = {
        "id": plant_id.strip().lower(),
        "name": name,
        "species": species,
        "light": light,
        "watering": watering,
        "difficulty": difficulty,
        "price": float(price),
        "description": description,
        "care_tips": care_tips
    }
    doc_ref.set(payload)
    return {"status": "success", "message": f"Plant '{name}' ({plant_id}) successfully saved to Firestore.", "data": payload}


def log_watering_event(plant_id: str, notes: str = "") -> dict[str, Any]:
    """Logs a watering event for a specific plant with the current timestamp.

    Args:
        plant_id: The ID of the plant (e.g. 'monstera-deliciosa', 'snake-plant').
        notes: Optional brief notes (e.g., 'Added liquid fertilizer', 'Soil was dry').

    Returns:
        Confirmation details including the recorded timestamp.
    """
    import datetime
    db = get_firestore_client()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_entry = {
        "plant_id": plant_id.strip().lower(),
        "timestamp": now_iso,
        "notes": notes
    }
    db.collection("plants").document(plant_id.strip().lower()).collection("care_logs").add(log_entry)
    return {
        "status": "success",
        "message": f"Watering event logged for {plant_id} at {now_iso}.",
        "entry": log_entry
    }


def get_watering_history(plant_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Retrieves recent watering history for a plant.

    Args:
        plant_id: The ID of the plant (e.g. 'monstera-deliciosa').
        limit: Maximum number of recent watering logs to return (default 5).

    Returns:
        A list of recent watering records ordered from newest to oldest.
    """
    db = get_firestore_client()
    logs_ref = (
        db.collection("plants")
        .document(plant_id.strip().lower())
        .collection("care_logs")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    return [doc.to_dict() for doc in logs_ref.stream()]

