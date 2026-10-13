# Copyright 2026 Google LLC
# Seed script for Urban Greenhouse plant catalog

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-93b5deb0ee1a"

PLANTS = [
    {
        "id": "monstera-deliciosa",
        "name": "Monstera Deliciosa",
        "species": "Monstera deliciosa",
        "light": "Bright indirect light",
        "watering": "Every 1-2 weeks, let soil dry halfway",
        "difficulty": "Easy",
        "price": 34.99,
        "description": "Iconic Swiss cheese plant with large, glossy, perforated heart-shaped leaves.",
        "care_tips": "Wipe leaves with a damp cloth to remove dust and maximize photosynthesis."
    },
    {
        "id": "fiddle-leaf-fig",
        "name": "Fiddle Leaf Fig",
        "species": "Ficus lyrata",
        "light": "Very bright, filtered sunlight",
        "watering": "Every 7-10 days when top 2 inches of soil are dry",
        "difficulty": "Moderate",
        "price": 49.99,
        "description": "Dramatic statement plant with large violin-shaped leaves and upright stature.",
        "care_tips": "Avoid drafty windows and keep in a stable spot away from sudden temperature shifts."
    },
    {
        "id": "snake-plant",
        "name": "Snake Plant (Sansevieria)",
        "species": "Dracaena trifasciata",
        "light": "Tolerates low light up to full sun",
        "watering": "Every 2-4 weeks, allow soil to dry completely",
        "difficulty": "Beginner",
        "price": 24.99,
        "description": "Indestructible architectural houseplant with stiff, upright sword-like green foliage.",
        "care_tips": "Better to underwater than overwater. Well-draining succulent soil is ideal."
    },
    {
        "id": "pothos-golden",
        "name": "Golden Pothos",
        "species": "Epipremnum aureum",
        "light": "Low to medium indirect light",
        "watering": "Every 1-2 weeks when top inch feels dry",
        "difficulty": "Beginner",
        "price": 18.99,
        "description": "Fast-growing trailing vine with heart-shaped leaves splashed in gold and yellow.",
        "care_tips": "Great for hanging baskets or trailing along bookshelves."
    },
    {
        "id": "peace-lily",
        "name": "Peace Lily",
        "species": "Spathiphyllum wallisii",
        "light": "Medium to low indirect light",
        "watering": "Weekly, keep soil evenly moist but not waterlogged",
        "difficulty": "Easy",
        "price": 28.50,
        "description": "Lush dark green foliage with striking white spoon-shaped blooms (spathes).",
        "care_tips": "Leaves will visibly droop when thirsty, bouncing back quickly after a deep watering."
    }
]

def seed():
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("plants")
    print(f"Seeding {len(PLANTS)} plants into Firestore collection 'plants' (Project: {PROJECT_ID})...")
    for plant in PLANTS:
        doc_id = plant["id"]
        collection.document(doc_id).set(plant)
        print(f"  ✓ Seeded: {plant['name']} ({doc_id})")
    print("Seeding complete! ✅")

if __name__ == "__main__":
    seed()
