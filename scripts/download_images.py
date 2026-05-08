import os, sys, time, re
import requests
from duckduckgo_search import DDGS
from PIL import Image
from io import BytesIO

# Load django environment
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
sys.path.insert(0, BASE_DIR)
import django
django.setup()

from apps.market.mongo_client import get_products_collection

PRODUCTS = list(get_products_collection().find())
IMG_DIR = os.path.join(BASE_DIR, "static", "images", "products")
os.makedirs(IMG_DIR, exist_ok=True)

def make_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def download_image(url, filepath):
    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        if r.status_code == 200:
            img = Image.open(BytesIO(r.content)).convert("RGB")
            # Resize and crop to square for consistent UI
            w, h = img.size
            if w != h:
                # crop to center square
                min_dim = min(w, h)
                left = (w - min_dim)/2
                top = (h - min_dim)/2
                right = (w + min_dim)/2
                bottom = (h + min_dim)/2
                img = img.crop((left, top, right, bottom))
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            img.save(filepath, "JPEG", quality=85)
            return True
    except Exception as e:
        pass
    return False

ddgs = DDGS()

print(f"Downloading unique images for {len(PRODUCTS)} products...")

for p in PRODUCTS:
    name = p['name']
    slug = make_slug(name)
    filename = f"{slug}.jpg"
    filepath = os.path.join(IMG_DIR, filename)
    url_path = f"/static/images/products/{filename}"
    
    # Check if we already downloaded a unique image
    if os.path.exists(filepath):
        get_products_collection().update_one({"_id": p["_id"]}, {"$set": {"image_url": url_path, "images": [url_path]}})
        continue

    print(f"Searching image for: {name} ...", end=" ")
    query = f"{name} grocery product high quality"
    
    success = False
    try:
        results = list(ddgs.images(query, max_results=5))
        for res in results:
            img_url = res.get('image')
            if img_url and download_image(img_url, filepath):
                success = True
                break
    except Exception as e:
        print(f"Error searching: {e}", end=" ")
        
    if success:
        get_products_collection().update_one({"_id": p["_id"]}, {"$set": {"image_url": url_path, "images": [url_path]}})
        print("Done")
    else:
        print("Failed")
        
    time.sleep(1) # rate limit

print("Finished downloading images!")
