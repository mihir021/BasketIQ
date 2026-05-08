"""
seed_grocery.py — Seed 30 real grocery items into the MongoDB products collection.
Run: python seed_grocery.py
"""

import os
import sys
from datetime import datetime

import django

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.market.mongo_client import get_products_collection

GROCERY_ITEMS = [
    # ── Fruits ────────────────────────────────────────────────────────
    {
        "name": "Fresh Bananas",
        "category": "Fruits",
        "price": 40,
        "discount": 0,
        "weight": "1 dozen",
        "unit": "dozen",
        "image_url": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=400&fit=crop&q=80",
        "keywords": ["banana", "fruit", "fresh", "yellow"],
        "is_best_seller": True,
    },
    {
        "name": "Red Apples (Shimla)",
        "category": "Fruits",
        "price": 180,
        "discount": 10,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=400&fit=crop&q=80",
        "keywords": ["apple", "fruit", "shimla", "red"],
        "is_best_seller": True,
    },
    {
        "name": "Alphonso Mango",
        "category": "Fruits",
        "price": 350,
        "discount": 5,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1553279768-865429fa0078?w=400&h=400&fit=crop&q=80",
        "keywords": ["mango", "alphonso", "fruit", "seasonal"],
        "is_best_seller": True,
    },

    # ── Vegetables ────────────────────────────────────────────────────
    {
        "name": "Fresh Tomatoes",
        "category": "Vegetables",
        "price": 30,
        "discount": 0,
        "weight": "500 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1546470427-0d4db154ceb8?w=400&h=400&fit=crop&q=80",
        "keywords": ["tomato", "vegetable", "fresh", "red"],
        "is_best_seller": False,
    },
    {
        "name": "Onion",
        "category": "Vegetables",
        "price": 35,
        "discount": 0,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=400&h=400&fit=crop&q=80",
        "keywords": ["onion", "vegetable", "pyaaz"],
        "is_best_seller": True,
    },
    {
        "name": "Potato (Aloo)",
        "category": "Vegetables",
        "price": 25,
        "discount": 0,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82ber3?w=400&h=400&fit=crop&q=80",
        "keywords": ["potato", "aloo", "vegetable"],
        "is_best_seller": False,
    },
    {
        "name": "Fresh Spinach (Palak)",
        "category": "Vegetables",
        "price": 25,
        "discount": 10,
        "weight": "250 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=400&fit=crop&q=80",
        "keywords": ["spinach", "palak", "green", "leafy", "vegetable"],
        "is_best_seller": False,
    },

    # ── Dairy ─────────────────────────────────────────────────────────
    {
        "name": "Amul Toned Milk",
        "category": "Dairy",
        "price": 29,
        "discount": 0,
        "weight": "500 ml",
        "unit": "ml",
        "image_url": "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=400&fit=crop&q=80",
        "keywords": ["milk", "amul", "dairy", "toned"],
        "is_best_seller": True,
    },
    {
        "name": "Amul Butter (100g)",
        "category": "Dairy",
        "price": 56,
        "discount": 5,
        "weight": "100 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400&h=400&fit=crop&q=80",
        "keywords": ["butter", "amul", "dairy"],
        "is_best_seller": True,
    },
    {
        "name": "Fresh Paneer",
        "category": "Dairy",
        "price": 90,
        "discount": 0,
        "weight": "200 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=400&fit=crop&q=80",
        "keywords": ["paneer", "cheese", "dairy", "cottage"],
        "is_best_seller": False,
    },
    {
        "name": "Curd (Dahi)",
        "category": "Dairy",
        "price": 35,
        "discount": 0,
        "weight": "400 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=400&fit=crop&q=80",
        "keywords": ["curd", "dahi", "yogurt", "dairy"],
        "is_best_seller": False,
    },

    # ── Pulses ────────────────────────────────────────────────────────
    {
        "name": "Toor Dal",
        "category": "Pulses",
        "price": 140,
        "discount": 8,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=400&h=400&fit=crop&q=80",
        "keywords": ["toor", "dal", "lentil", "pulse", "arhar"],
        "is_best_seller": True,
    },
    {
        "name": "Chana Dal",
        "category": "Pulses",
        "price": 110,
        "discount": 5,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1613758947307-f3b8f5d80711?w=400&h=400&fit=crop&q=80",
        "keywords": ["chana", "dal", "gram", "pulse"],
        "is_best_seller": False,
    },
    {
        "name": "Rajma (Kidney Beans)",
        "category": "Pulses",
        "price": 160,
        "discount": 10,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1558160074-4d7d8bdf4256?w=400&h=400&fit=crop&q=80",
        "keywords": ["rajma", "kidney", "beans", "pulse"],
        "is_best_seller": False,
    },
    {
        "name": "Moong Dal",
        "category": "Pulses",
        "price": 130,
        "discount": 0,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1612257999756-196f14140586?w=400&h=400&fit=crop&q=80",
        "keywords": ["moong", "dal", "lentil", "green", "pulse"],
        "is_best_seller": False,
    },

    # ── Flour & Grains ────────────────────────────────────────────────
    {
        "name": "Aashirvaad Whole Wheat Atta",
        "category": "Flour",
        "price": 280,
        "discount": 12,
        "weight": "5 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=400&fit=crop&q=80",
        "keywords": ["atta", "wheat", "flour", "aashirvaad", "roti"],
        "is_best_seller": True,
    },
    {
        "name": "Basmati Rice",
        "category": "Grains",
        "price": 320,
        "discount": 10,
        "weight": "5 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&h=400&fit=crop&q=80",
        "keywords": ["rice", "basmati", "grain", "chawal"],
        "is_best_seller": True,
    },
    {
        "name": "Sooji (Semolina)",
        "category": "Flour",
        "price": 45,
        "discount": 0,
        "weight": "500 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=400&h=400&fit=crop&q=80",
        "keywords": ["sooji", "suji", "semolina", "rava", "flour"],
        "is_best_seller": False,
    },

    # ── Oil & Ghee ────────────────────────────────────────────────────
    {
        "name": "Fortune Sunflower Oil",
        "category": "Oil",
        "price": 180,
        "discount": 8,
        "weight": "1 L",
        "unit": "L",
        "image_url": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&h=400&fit=crop&q=80",
        "keywords": ["oil", "sunflower", "fortune", "cooking"],
        "is_best_seller": True,
    },
    {
        "name": "Amul Pure Ghee",
        "category": "Oil",
        "price": 560,
        "discount": 5,
        "weight": "1 L",
        "unit": "L",
        "image_url": "https://images.unsplash.com/photo-1631898039968-203f36c4c82c?w=400&h=400&fit=crop&q=80",
        "keywords": ["ghee", "amul", "pure", "desi"],
        "is_best_seller": True,
    },

    # ── Spices ────────────────────────────────────────────────────────
    {
        "name": "MDH Garam Masala",
        "category": "Spices",
        "price": 75,
        "discount": 0,
        "weight": "100 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=400&fit=crop&q=80",
        "keywords": ["garam", "masala", "mdh", "spice"],
        "is_best_seller": False,
    },
    {
        "name": "Turmeric Powder (Haldi)",
        "category": "Spices",
        "price": 50,
        "discount": 0,
        "weight": "200 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=400&h=400&fit=crop&q=80",
        "keywords": ["turmeric", "haldi", "spice", "yellow"],
        "is_best_seller": False,
    },
    {
        "name": "Red Chilli Powder",
        "category": "Spices",
        "price": 65,
        "discount": 5,
        "weight": "200 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=400&h=400&fit=crop&q=80",
        "keywords": ["chilli", "red", "powder", "spice", "lal mirch"],
        "is_best_seller": False,
    },

    # ── Pantry Staples ────────────────────────────────────────────────
    {
        "name": "Tata Salt",
        "category": "Pantry",
        "price": 25,
        "discount": 0,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1518110925495-5fe2c8444b08?w=400&h=400&fit=crop&q=80",
        "keywords": ["salt", "tata", "namak", "iodized"],
        "is_best_seller": False,
    },
    {
        "name": "Sugar",
        "category": "Pantry",
        "price": 45,
        "discount": 0,
        "weight": "1 kg",
        "unit": "kg",
        "image_url": "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400&h=400&fit=crop&q=80",
        "keywords": ["sugar", "cheeni", "sweet"],
        "is_best_seller": False,
    },
    {
        "name": "Maggi 2-Minute Noodles",
        "category": "Pantry",
        "price": 56,
        "discount": 15,
        "weight": "280 g (4-pack)",
        "unit": "pack",
        "image_url": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=400&h=400&fit=crop&q=80",
        "keywords": ["maggi", "noodles", "instant", "snack"],
        "is_best_seller": True,
    },
    {
        "name": "Kissan Tomato Ketchup",
        "category": "Pantry",
        "price": 105,
        "discount": 10,
        "weight": "500 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1472476443507-c7a5948772fc?w=400&h=400&fit=crop&q=80",
        "keywords": ["ketchup", "tomato", "kissan", "sauce"],
        "is_best_seller": False,
    },

    # ── Beverages ─────────────────────────────────────────────────────
    {
        "name": "Tata Tea Gold",
        "category": "Pantry",
        "price": 220,
        "discount": 8,
        "weight": "500 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400&h=400&fit=crop&q=80",
        "keywords": ["tea", "chai", "tata", "gold"],
        "is_best_seller": True,
    },
    {
        "name": "Nescafe Classic Coffee",
        "category": "Pantry",
        "price": 190,
        "discount": 5,
        "weight": "100 g",
        "unit": "g",
        "image_url": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=400&fit=crop&q=80",
        "keywords": ["coffee", "nescafe", "instant", "classic"],
        "is_best_seller": False,
    },

    # ── Eggs ──────────────────────────────────────────────────────────
    {
        "name": "Farm Fresh Eggs",
        "category": "Dairy",
        "price": 72,
        "discount": 0,
        "weight": "6 pcs",
        "unit": "pcs",
        "image_url": "https://images.unsplash.com/photo-1607537070338-adb1b2e43e37?w=400&h=400&fit=crop&q=80",
        "keywords": ["eggs", "farm", "fresh", "protein"],
        "is_best_seller": False,
    },
]


def seed():
    col = get_products_collection()

    # Remove old generic products (keep any that match our grocery items)
    deleted = col.delete_many({})
    print(f"🗑  Cleared {deleted.deleted_count} existing products")

    now = datetime.utcnow()
    docs = []
    for item in GROCERY_ITEMS:
        item["created_at"] = now
        item["updated_at"] = now
        docs.append(item)

    result = col.insert_many(docs)
    print(f"✅ Inserted {len(result.inserted_ids)} grocery items")
    print()

    # Verify by listing them
    print("=" * 60)
    print(f"{'#':<3} {'Name':<30} {'Category':<12} {'Price':>6} {'Wt':<12}")
    print("=" * 60)
    for i, doc in enumerate(col.find().sort("category", 1), 1):
        discount_label = f" (-{doc.get('discount')}%)" if doc.get("discount", 0) > 0 else ""
        best = " ⭐" if doc.get("is_best_seller") else ""
        print(f"{i:<3} {doc['name']:<30} {doc['category']:<12} ₹{doc['price']:>4}{discount_label:<8} {doc.get('weight', ''):<12}{best}")

    print("=" * 60)
    print(f"\n🛒 Total: {col.count_documents({})} products in database")


if __name__ == "__main__":
    seed()
