"""Update MongoDB products to use product-specific local images.

The script prefers existing files under static/images/products and downloads
missing product images from Wikimedia thumbnails when needed.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_PRODUCT_DIR = BASE_DIR / "static" / "images" / "products"
STATIC_PRODUCT_URL = "/static/images/products/"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
sys.path.insert(0, str(BASE_DIR))

import django  # noqa: E402

django.setup()

from apps.market import mongo_client  # noqa: E402


EXISTING_EXACT_MAP = {
    "Chana Dal": "chana_dal_ai.png",
    "Toor Dal": "toor_dal_ai.png",
    "Moong Dal": "moong_dal_ai.png",
    "Urad Dal": "urad_dal_ai.png",
    "Masoor Dal": "masoor_dal_ai.png",
    "Rajma": "rajma_ai.png",
    "Kabuli Chana": "kabuli_chana_ai.png",
    "Eggs": "farm_eggs.png",
}

WIKIMEDIA_TITLE_MAP = {
    "Wheat Flour (Atta)": "Atta flour",
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
    "Asafoetida (Hing)": "Ferula assa-foetida",
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
    "Mango (Alphonso)": "Alphonso_mango",
    "Pomegranate": "Pomegranate",
    "Papaya": "Papaya",
    "Sugar": "Sugar",
    "Jaggery (Gur)": "Jaggery",
    "Tamarind (Imli)": "Tamarind",
    "Baking Soda": "Sodium_bicarbonate",
    "Dry Red Chilli": "Chili_pepper",
    "Honey": "Honey",
    "Tea (Chai Patti)": "Black_tea",
    "Papad": "Papadam",
    "Chicken (Whole)": "Chicken_as_food",
    "Chicken Breast": "Chicken_meat",
}

DIRECT_IMAGE_URL_MAP = {
    "Dry Red Chilli": (
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/"
        "Bhiwapur_Chilli_-_Red_Dried.jpg?width=800"
    ),
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def product_url(filename: str) -> str:
    return STATIC_PRODUCT_URL + filename


def existing_file_for(name: str) -> str | None:
    mapped = EXISTING_EXACT_MAP.get(name)
    if mapped and (STATIC_PRODUCT_DIR / mapped).exists():
        return mapped

    slug = slugify(name)
    for extension in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = STATIC_PRODUCT_DIR / f"{slug}{extension}"
        if candidate.exists():
            return candidate.name
    return None


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 BasketIQ image updater"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, target_stem: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 BasketIQ image updater",
            "Referer": "https://commons.wikimedia.org/",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type", "").split(";")[0]

    extension = mimetypes.guess_extension(content_type) or Path(urllib.parse.urlparse(url).path).suffix
    if extension == ".jpe":
        extension = ".jpg"
    if extension.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        extension = ".jpg"

    filename = f"{target_stem}{extension.lower()}"
    (STATIC_PRODUCT_DIR / filename).write_bytes(data)
    return filename


def download_wikimedia_image(name: str) -> str | None:
    direct_url = DIRECT_IMAGE_URL_MAP.get(name)
    if direct_url:
        return download_file(direct_url, slugify(name))

    title = WIKIMEDIA_TITLE_MAP.get(name, name)
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "titles": title,
            "prop": "pageimages",
            "format": "json",
            "pithumbsize": "800",
            "redirects": "1",
        }
    )
    data = fetch_json(f"https://en.wikipedia.org/w/api.php?{params}")
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        source = page.get("thumbnail", {}).get("source")
        if source:
            return download_file(source, slugify(name))
    return None


def main() -> int:
    STATIC_PRODUCT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"using_fallback={mongo_client.using_fallback()}")

    products = list(mongo_client.get_products_collection().find({}))
    print(f"products={len(products)}")

    updated = 0
    failed = []
    for product in products:
        name = product.get("name", "").strip()
        if not name:
            continue

        filename = existing_file_for(name)
        source = "local"
        if filename is None:
            try:
                filename = download_wikimedia_image(name)
                source = "downloaded"
            except Exception as exc:
                failed.append((name, str(exc)))
                continue

        if filename is None:
            failed.append((name, "no Wikimedia thumbnail found"))
            continue

        url = product_url(filename)
        mongo_client.get_products_collection().update_one(
            {"_id": product["_id"]},
            {"$set": {"image_url": url, "images": [url]}},
        )
        updated += 1
        print(f"{source:10} {name} -> {url}")

    if failed:
        print("\nFailed:")
        for name, reason in failed:
            print(f"- {name}: {reason}")

    print(f"\nupdated={updated} failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
