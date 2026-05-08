"""
fix_images.py — Replace ALL product image_url with stunning locally generated AI food photos.
Connects directly to MongoDB Atlas and updates every product.

Usage:
    python scripts/fix_images.py
"""
import re
from pymongo import MongoClient

URI = "mongodb+srv://manushyop_db_user:lvwPKZwuhQdIlcwB@cluster0.xptaihd.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(URI)
db = client["grocery_admin"]

_U = "/static/images/products/"

# Map: keyword list → local photo URL
KEYWORD_MAP = [
    (["milk", "full cream", "toned", "doodh", "curd", "yogurt", "dahi", "cream", "paneer", "cottage cheese"],         _U + "milk_bottle.png"),
    (["butter", "makhan", "ghee", "clarified butter"],  _U + "ghee_jar.png"),
    (["egg", "anda"],                                   _U + "farm_eggs.png"),
    (["apple", "seb", "shimla", "banana", "kela", "mango", "alphonso", "kesar", "aam", "lemon", "nimbu", "pomegranate", "anar"], _U + "fruits_basket.png"),
    (["tomato", "tamatar", "onion", "pyaaz", "potato", "aloo", "spinach", "palak", "carrot", "gajar", "capsicum", "bell pepper", "shimla mirch", "cauliflower", "gobi", "brinjal", "baingan", "eggplant", "peas", "matar", "ginger", "adrak", "garlic", "lehsun", "coriander", "dhania", "cilantro", "curry leaves", "green chilli", "hari mirch"], _U + "vegetables_basket.png"),
    (["turmeric", "haldi", "red chilli", "chilli powder", "lal mirch", "cumin", "jeera", "coriander powder", "mustard seeds", "garam masala", "black pepper", "hing", "fennel", "ajwain", "amchur", "masala", "spice"], _U + "spices_bowl.png"),
    (["rice", "basmati", "chawal"],                     _U + "rice_bowl.png"),
    (["flour", "atta", "wheat", "maida", "besan", "sooji", "semolina", "rava"], _U + "flour_bowl.png"),
    (["rajma", "kidney", "chickpea", "kabuli", "chole", "chana dal", "chana", "toor", "arhar", "masoor", "moong", "urad", "dal", "lentil"], _U + "pulses_bowl.png"),
    (["oil", "cooking oil", "mustard oil", "vegetable oil"], _U + "oil_bottle.png"),
    (["salt", "sugar", "baking", "jaggery", "gur", "tamarind", "imli", "honey", "shahad", "tea", "chai", "papad", "snack"], _U + "pantry_jars.png"),
    (["chicken", "meat"],                               _U + "pantry_jars.png"), # fallback
]

CATEGORY_FALLBACK = {
    "Dairy":      _U + "milk_bottle.png",
    "Fruits":     _U + "fruits_basket.png",
    "Vegetables": _U + "vegetables_basket.png",
    "Spices":     _U + "spices_bowl.png",
    "Grains":     _U + "rice_bowl.png",
    "Pulses":     _U + "pulses_bowl.png",
    "Flour":      _U + "flour_bowl.png",
    "Oil":        _U + "oil_bottle.png",
    "Pantry":     _U + "pantry_jars.png",
    "Beverages":  _U + "pantry_jars.png",
    "Meat":       _U + "pantry_jars.png",
}

def get_image_url(name, category):
    n = name.lower()
    for keywords, url in KEYWORD_MAP:
        if any(kw in n for kw in keywords):
            return url
    return CATEGORY_FALLBACK.get(category, _U + "pantry_jars.png")


products = list(db.products.find())
print(f"Updating images for {len(products)} products...")

for p in products:
    new_url = get_image_url(p["name"], p.get("category", ""))
    db.products.update_one(
        {"_id": p["_id"]},
        {"$set": {"image_url": new_url, "images": [new_url]}}
    )

print(f"\nDone! All {len(products)} products updated with local AI images.")
