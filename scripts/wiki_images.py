import os, sys, re, time
import requests
from PIL import Image
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
sys.path.insert(0, BASE_DIR)
import django
django.setup()

from apps.market.mongo_client import get_products_collection

WIKI_MAP = {
    "Wheat Flour (Atta)": "Wheat_flour",
    "All Purpose Flour (Maida)": "Maida_flour",
    "Besan (Gram Flour)": "Gram_flour",
    "Basmati Rice": "Basmati",
    "Sooji (Semolina)": "Semolina",
    "Turmeric Powder (Haldi)": "Turmeric",
    "Red Chilli Powder": "Chili_powder",
    "Cumin Seeds (Jeera)": "Cumin",
    "Coriander Powder (Dhania)": "Coriander",
    "Garam Masala": "Garam_masala",
    "Mustard Seeds (Rai)": "Mustard_seed",
    "Salt": "Salt",
    "Black Pepper": "Black_pepper",
    "Asafoetida (Hing)": "Asafoetida",
    "Fennel Seeds (Saunf)": "Fennel",
    "Dry Mango Powder (Amchur)": "Amchoor",
    "Ajwain (Carom Seeds)": "Ajwain",
    "Vegetable Oil": "Vegetable_oil",
    "Mustard Oil": "Mustard_oil",
    "Desi Ghee": "Ghee",
    "Full Cream Milk": "Milk",
    "Curd (Yogurt)": "Curd",
    "Paneer": "Paneer",
    "Butter": "Butter",
    "Cream": "Cream",
    "Onion": "Onion",
    "Tomato": "Tomato",
    "Potato": "Potato",
    "Green Chilli": "Chili_pepper",
    "Ginger": "Ginger",
    "Garlic": "Garlic",
    "Fresh Coriander Leaves": "Coriander",
    "Curry Leaves": "Curry_tree",
    "Lemon": "Lemon",
    "Spinach": "Spinach",
    "Carrot": "Carrot",
    "Capsicum": "Bell_pepper",
    "Cauliflower": "Cauliflower",
    "Brinjal (Baingan)": "Eggplant",
    "Peas (Matar)": "Pea",
    "Shimla Apple": "Apple",
    "Banana": "Banana",
    "Mango (Alphonso)": "Alphonso_(mango)",
    "Pomegranate": "Pomegranate",
    "Papaya": "Papaya",
    "Sugar": "Sugar",
    "Jaggery (Gur)": "Jaggery",
    "Tamarind (Imli)": "Tamarind",
    "Baking Soda": "Sodium_bicarbonate",
    "Dry Red Chilli": "Dry_chili",
    "Honey": "Honey",
    "Tea (Chai Patti)": "Black_tea",
    "Papad": "Papadam",
    "Eggs": "Egg_(food)",
    "Chicken (Whole)": "Roast_chicken",
    "Chicken Breast": "Chicken_meat"
}

AI_MAP = {
    "Chana Dal": "chana_dal_ai.png",
    "Toor Dal": "toor_dal_ai.png",
    "Moong Dal": "moong_dal_ai.png",
    "Urad Dal": "urad_dal_ai.png",
    "Masoor Dal": "masoor_dal_ai.png",
    "Rajma": "rajma_ai.png",
    "Kabuli Chana": "kabuli_chana_ai.png"
}

def make_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

IMG_DIR = os.path.join(BASE_DIR, "static", "images", "products")
col = get_products_collection()

for p in list(col.find()):
    name = p["name"]
    slug = make_slug(name)
    
    if name in AI_MAP:
        url_path = f"/static/images/products/{AI_MAP[name]}"
        col.update_one({"_id": p["_id"]}, {"$set": {"image_url": url_path, "images": [url_path]}})
        print(f"Updated {name} with AI image.")
        continue

    wiki_title = WIKI_MAP.get(name)
    if not wiki_title:
        print(f"No mapping for {name}")
        continue
        
    filepath = os.path.join(IMG_DIR, f"{slug}.jpg")
    url_path = f"/static/images/products/{slug}.jpg"
    
    if not os.path.exists(filepath):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={wiki_title}&prop=pageimages&format=json&pithumbsize=600"
        try:
            r = requests.get(api_url, headers=headers, timeout=5).json()
            pages = r.get("query", {}).get("pages", {})
            img_src = None
            for pid in pages:
                if "thumbnail" in pages[pid]:
                    img_src = pages[pid]["thumbnail"]["source"]
            
            if img_src:
                img_resp = requests.get(img_src, headers=headers, timeout=5)
                if img_resp.status_code == 200:
                    img = Image.open(BytesIO(img_resp.content)).convert("RGB")
                    w, h = img.size
                    if w != h:
                        min_dim = min(w, h)
                        left = (w - min_dim)/2
                        top = (h - min_dim)/2
                        right = (w + min_dim)/2
                        bottom = (h + min_dim)/2
                        img = img.crop((left, top, right, bottom))
                    img = img.resize((400, 400), Image.Resampling.LANCZOS)
                    img.save(filepath, "JPEG", quality=85)
                    print(f"Downloaded Wikipedia image for {name}")
                    col.update_one({"_id": p["_id"]}, {"$set": {"image_url": url_path, "images": [url_path]}})
                else:
                    print(f"Failed to download image from {img_src}")
            else:
                print(f"No thumbnail found for {name} ({wiki_title})")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
    else:
        # File exists, just update DB
        col.update_one({"_id": p["_id"]}, {"$set": {"image_url": url_path, "images": [url_path]}})

print("Database and images updated.")
