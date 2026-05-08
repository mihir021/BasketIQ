#!/usr/bin/env python
"""
seed_products.py — Populate MongoDB with sample Indian grocery products.
Usage:
    cd DA-IICT
    python scripts/seed_products.py
"""

import os, sys, re
import django

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
sys.path.insert(0, BASE_DIR)
django.setup()

from apps.market.mongo_client import ensure_product_indexes, get_products_collection

_U = "/static/images/products/"

PRODUCTS = [
    # ── Pulses & Lentils ─────────────────────────────────────
    {"name": "Chana Dal",          "category": "Pulses",     "price": 72,  "discount": 5,  "unit": "kg",   "weight": "1kg",   "is_best_seller": True,  "image_url": _U+"pulses_bowl.png", "keywords": ["chana","dal","lentil","gram"]},
    {"name": "Toor Dal",           "category": "Pulses",     "price": 95,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": True,  "image_url": _U+"pulses_bowl.png", "keywords": ["toor","arhar","dal","lentil"]},
    {"name": "Moong Dal",          "category": "Pulses",     "price": 110, "discount": 8,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"pulses_bowl.png", "keywords": ["moong","dal","lentil","green gram"]},
    {"name": "Urad Dal",           "category": "Pulses",     "price": 120, "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"pulses_bowl.png", "keywords": ["urad","dal","black gram"]},
    {"name": "Masoor Dal",         "category": "Pulses",     "price": 85,  "discount": 10, "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"pulses_bowl.png", "keywords": ["masoor","dal","red lentil"]},
    {"name": "Rajma",              "category": "Pulses",     "price": 140, "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"pulses_bowl.png", "keywords": ["rajma","kidney beans"]},
    {"name": "Kabuli Chana",       "category": "Pulses",     "price": 130, "discount": 5,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"pulses_bowl.png", "keywords": ["kabuli","chana","chickpeas","chole"]},

    # ── Flour & Grains ───────────────────────────────────────
    {"name": "Wheat Flour (Atta)", "category": "Flour",      "price": 210, "discount": 5,  "unit": "kg",   "weight": "5kg",   "is_best_seller": True,  "image_url": _U+"flour_bowl.png", "keywords": ["atta","wheat","flour","chapati"]},
    {"name": "All Purpose Flour (Maida)", "category": "Flour","price": 45, "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"flour_bowl.png", "keywords": ["maida","all purpose flour","refined flour"]},
    {"name": "Besan (Gram Flour)", "category": "Flour",      "price": 65,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"flour_bowl.png", "keywords": ["besan","gram flour","chickpea flour"]},
    {"name": "Basmati Rice",       "category": "Grains",     "price": 320, "discount": 10, "unit": "kg",   "weight": "5kg",   "is_best_seller": True,  "image_url": _U+"rice_bowl.png", "keywords": ["rice","basmati","chawal"]},
    {"name": "Sooji (Semolina)",   "category": "Flour",      "price": 40,  "discount": 0,  "unit": "kg",   "weight": "500g",  "is_best_seller": False, "image_url": _U+"flour_bowl.png", "keywords": ["sooji","semolina","rava","suji"]},

    # ── Spices ───────────────────────────────────────────────
    {"name": "Turmeric Powder (Haldi)", "category": "Spices","price": 35, "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["turmeric","haldi"]},
    {"name": "Red Chilli Powder",  "category": "Spices",     "price": 45,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["red chilli","lal mirch","chili"]},
    {"name": "Cumin Seeds (Jeera)","category": "Spices",     "price": 55,  "discount": 5,  "unit": "pack", "weight": "100g",  "is_best_seller": True,  "image_url": _U+"spices_bowl.png", "keywords": ["cumin","jeera"]},
    {"name": "Coriander Powder (Dhania)", "category": "Spices","price": 30,"discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["coriander","dhania"]},
    {"name": "Garam Masala",       "category": "Spices",     "price": 60,  "discount": 0,  "unit": "pack", "weight": "50g",   "is_best_seller": True,  "image_url": _U+"spices_bowl.png", "keywords": ["garam masala","masala"]},
    {"name": "Mustard Seeds (Rai)","category": "Spices",     "price": 25,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["mustard","rai","sarson"]},
    {"name": "Salt",               "category": "Pantry",     "price": 22,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"pantry_jars.png", "keywords": ["salt","namak","tata salt"]},
    {"name": "Black Pepper",       "category": "Spices",     "price": 80,  "discount": 0,  "unit": "pack", "weight": "50g",   "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["black pepper","kali mirch"]},
    {"name": "Asafoetida (Hing)",  "category": "Spices",     "price": 90,  "discount": 10, "unit": "pack", "weight": "50g",   "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["hing","asafoetida"]},
    {"name": "Fennel Seeds (Saunf)","category": "Spices",    "price": 40,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["fennel","saunf"]},
    {"name": "Dry Mango Powder (Amchur)","category": "Spices","price": 35, "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["amchur","dry mango","amchoor"]},
    {"name": "Ajwain (Carom Seeds)","category": "Spices",    "price": 30,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["ajwain","carom"]},

    # ── Oil & Ghee ───────────────────────────────────────────
    {"name": "Vegetable Oil",      "category": "Oil",        "price": 150, "discount": 5,  "unit": "L",    "weight": "1L",    "is_best_seller": True,  "image_url": _U+"oil_bottle.png", "keywords": ["vegetable oil","refined oil","cooking oil"]},
    {"name": "Mustard Oil",        "category": "Oil",        "price": 170, "discount": 0,  "unit": "L",    "weight": "1L",    "is_best_seller": False, "image_url": _U+"oil_bottle.png", "keywords": ["mustard oil","sarson ka tel"]},
    {"name": "Desi Ghee",          "category": "Dairy",      "price": 550, "discount": 8,  "unit": "kg",   "weight": "500ml", "is_best_seller": True,  "image_url": _U+"ghee_jar.png", "keywords": ["ghee","desi ghee","clarified butter"]},

    # ── Dairy ────────────────────────────────────────────────
    {"name": "Full Cream Milk",    "category": "Dairy",      "price": 66,  "discount": 0,  "unit": "L",    "weight": "1L",    "is_best_seller": True,  "image_url": _U+"milk_bottle.png", "keywords": ["milk","full cream","doodh"]},
    {"name": "Curd (Yogurt)",      "category": "Dairy",      "price": 40,  "discount": 0,  "unit": "pack", "weight": "400g",  "is_best_seller": False, "image_url": _U+"milk_bottle.png", "keywords": ["curd","yogurt","dahi"]},
    {"name": "Paneer",             "category": "Dairy",      "price": 90,  "discount": 5,  "unit": "pack", "weight": "200g",  "is_best_seller": True,  "image_url": _U+"milk_bottle.png", "keywords": ["paneer","cottage cheese"]},
    {"name": "Butter",             "category": "Dairy",      "price": 55,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"ghee_jar.png", "keywords": ["butter","makhan"]},
    {"name": "Cream",              "category": "Dairy",      "price": 35,  "discount": 0,  "unit": "pack", "weight": "200ml", "is_best_seller": False, "image_url": _U+"milk_bottle.png", "keywords": ["cream","fresh cream","malai"]},

    # ── Vegetables ───────────────────────────────────────────
    {"name": "Onion",              "category": "Vegetables", "price": 30,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": True,  "image_url": _U+"vegetables_basket.png", "keywords": ["onion","pyaaz","pyaz"]},
    {"name": "Tomato",             "category": "Vegetables", "price": 40,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": True,  "image_url": _U+"vegetables_basket.png", "keywords": ["tomato","tamatar"]},
    {"name": "Potato",             "category": "Vegetables", "price": 25,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["potato","aloo"]},
    {"name": "Green Chilli",       "category": "Vegetables", "price": 15,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["green chilli","hari mirch"]},
    {"name": "Ginger",             "category": "Vegetables", "price": 20,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["ginger","adrak"]},
    {"name": "Garlic",             "category": "Vegetables", "price": 25,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["garlic","lehsun","lahsun"]},
    {"name": "Fresh Coriander Leaves","category":"Vegetables","price": 10, "discount": 0,  "unit": "bunch","weight": "1 bunch","is_best_seller":False,  "image_url": _U+"vegetables_basket.png", "keywords": ["coriander","dhania","cilantro","fresh coriander"]},
    {"name": "Curry Leaves",       "category": "Vegetables", "price": 8,   "discount": 0,  "unit": "bunch","weight": "1 bunch","is_best_seller":False,  "image_url": _U+"vegetables_basket.png", "keywords": ["curry leaves","kadi patta"]},
    {"name": "Lemon",              "category": "Fruits",     "price": 10,  "discount": 0,  "unit": "pcs",  "weight": "1 pc",  "is_best_seller": False, "image_url": _U+"fruits_basket.png", "keywords": ["lemon","nimbu"]},
    {"name": "Spinach",            "category": "Vegetables", "price": 20,  "discount": 0,  "unit": "bunch","weight": "1 bunch","is_best_seller":False,  "image_url": _U+"vegetables_basket.png", "keywords": ["spinach","palak","leafy"]},
    {"name": "Carrot",             "category": "Vegetables", "price": 30,  "discount": 0,  "unit": "kg",   "weight": "500g",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["carrot","gajar"]},
    {"name": "Capsicum",           "category": "Vegetables", "price": 45,  "discount": 0,  "unit": "kg",   "weight": "500g",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["capsicum","bell pepper","shimla mirch"]},
    {"name": "Cauliflower",        "category": "Vegetables", "price": 35,  "discount": 0,  "unit": "pcs",  "weight": "1 pc",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["cauliflower","gobi","phool gobi"]},
    {"name": "Brinjal (Baingan)",  "category": "Vegetables", "price": 25,  "discount": 0,  "unit": "kg",   "weight": "500g",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["brinjal","baingan","eggplant","aubergine"]},
    {"name": "Peas (Matar)",       "category": "Vegetables", "price": 50,  "discount": 0,  "unit": "kg",   "weight": "500g",  "is_best_seller": False, "image_url": _U+"vegetables_basket.png", "keywords": ["peas","matar","green peas"]},

    # ── Fruits ───────────────────────────────────────────────
    {"name": "Shimla Apple",       "category": "Fruits",     "price": 180, "discount": 10, "unit": "kg",   "weight": "1kg",   "is_best_seller": True,  "image_url": _U+"fruits_basket.png", "keywords": ["apple","seb"]},
    {"name": "Banana",             "category": "Fruits",     "price": 40,  "discount": 0,  "unit": "dozen","weight": "1 dozen","is_best_seller":False,  "image_url": _U+"fruits_basket.png", "keywords": ["banana","kela"]},
    {"name": "Mango (Alphonso)",   "category": "Fruits",     "price": 350, "discount": 5,  "unit": "kg",   "weight": "1kg",   "is_best_seller": True,  "image_url": _U+"fruits_basket.png", "keywords": ["mango","alphonso","keri","aam"]},
    {"name": "Pomegranate",        "category": "Fruits",     "price": 120, "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"fruits_basket.png", "keywords": ["pomegranate","anar"]},
    {"name": "Papaya",             "category": "Fruits",     "price": 60,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"fruits_basket.png", "keywords": ["papaya","papita"]},

    # ── Pantry Staples ───────────────────────────────────────
    {"name": "Sugar",              "category": "Pantry",     "price": 45,  "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": False, "image_url": _U+"pantry_jars.png", "keywords": ["sugar","cheeni","shakkar"]},
    {"name": "Jaggery (Gur)",      "category": "Pantry",     "price": 60,  "discount": 0,  "unit": "kg",   "weight": "500g",  "is_best_seller": False, "image_url": _U+"pantry_jars.png", "keywords": ["jaggery","gur","gud"]},
    {"name": "Tamarind (Imli)",    "category": "Pantry",     "price": 30,  "discount": 0,  "unit": "pack", "weight": "200g",  "is_best_seller": False, "image_url": _U+"pantry_jars.png", "keywords": ["tamarind","imli"]},
    {"name": "Baking Soda",        "category": "Pantry",     "price": 15,  "discount": 0,  "unit": "pack", "weight": "50g",   "is_best_seller": False, "image_url": _U+"pantry_jars.png", "keywords": ["baking soda","meetha soda"]},
    {"name": "Dry Red Chilli",     "category": "Spices",     "price": 50,  "discount": 0,  "unit": "pack", "weight": "100g",  "is_best_seller": False, "image_url": _U+"spices_bowl.png", "keywords": ["dry red chilli","sabut lal mirch"]},
    {"name": "Honey",              "category": "Pantry",     "price": 180, "discount": 5,  "unit": "pack", "weight": "250g",  "is_best_seller": True,  "image_url": _U+"pantry_jars.png", "keywords": ["honey","shahad"]},

    # ── Snacks & Beverages ───────────────────────────────────
    {"name": "Tea (Chai Patti)",   "category": "Beverages",  "price": 120, "discount": 10, "unit": "pack", "weight": "250g",  "is_best_seller": True,  "image_url": _U+"pantry_jars.png", "keywords": ["tea","chai","patti"]},
    {"name": "Papad",              "category": "Snacks",     "price": 40,  "discount": 0,  "unit": "pack", "weight": "200g",  "is_best_seller": False, "image_url": _U+"pantry_jars.png", "keywords": ["papad","papadum"]},

    # ── Eggs ─────────────────────────────────────────────────
    {"name": "Eggs",               "category": "Dairy",      "price": 80,  "discount": 0,  "unit": "dozen","weight": "12 pcs","is_best_seller": True,  "image_url": _U+"farm_eggs.png", "keywords": ["eggs","anda","egg"]},

    # ── Chicken & Meat ───────────────────────────────────────
    {"name": "Chicken (Whole)",    "category": "Meat",       "price": 220, "discount": 0,  "unit": "kg",   "weight": "1kg",   "is_best_seller": True,  "image_url": _U+"pantry_jars.png", "keywords": ["chicken","murgh","poultry"]},
    {"name": "Chicken Breast",     "category": "Meat",       "price": 280, "discount": 5,  "unit": "kg",   "weight": "500g",  "is_best_seller": False, "image_url": _U+"pantry_jars.png", "keywords": ["chicken breast","boneless chicken"]},
]


def make_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def seed():
    col = get_products_collection()
    col.delete_many({})
    print(f"Cleared existing products.")
    # Add unique slugs before inserting
    for p in PRODUCTS:
        p["slug"] = make_slug(p["name"])
    result = col.insert_many(PRODUCTS)
    print(f"Inserted {len(result.inserted_ids)} products into MongoDB.")
    ensure_product_indexes()
    print("Text search index ensured.")


if __name__ == "__main__":
    seed()
