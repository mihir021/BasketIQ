"""Seed a production-like product catalogue into MongoDB."""

import os
import sys
from datetime import datetime

import django

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from apps.market.mongo_client import get_products_collection


PRODUCTS = [
    {
        "name": "Full Cream Milk",
        "category": "Dairy",
        "price": 66,
        "discount": 0,
        "unit": "L",
        "weight": "1L",
        "image_url": "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=600&q=80",
        "keywords": ["milk", "dairy", "full cream"],
        "is_best_seller": True,
    },
    {
        "name": "Fresh Tomatoes",
        "category": "Vegetables",
        "price": 40,
        "discount": 0,
        "unit": "kg",
        "weight": "1kg",
        "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=600&q=80",
        "keywords": ["tomato", "vegetable", "fresh"],
        "is_best_seller": True,
    },
    {
        "name": "Toor Dal",
        "category": "Pulses",
        "price": 95,
        "discount": 5,
        "unit": "kg",
        "weight": "1kg",
        "image_url": "https://images.unsplash.com/photo-1550998816-724bc2f00a58?w=600&q=80",
        "keywords": ["toor", "dal", "lentils"],
        "is_best_seller": True,
    },
]


def main():
    products = get_products_collection()
    products.delete_many({})
    now = datetime.utcnow()
    for item in PRODUCTS:
        products.insert_one({**item, "seeded_at": now})
    print(f"Seeded {len(PRODUCTS)} products into the production catalogue.")


if __name__ == "__main__":
    main()
