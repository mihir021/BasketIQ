"""
MongoDB client with a safe in-memory fallback for local development.
"""

from __future__ import annotations

import copy
import re
import threading
from dataclasses import dataclass

from bson import ObjectId
from django.conf import settings
from pymongo import MongoClient, TEXT

_client = None
_fallback_db = None
_init_lock = threading.Lock()
_using_fallback = False


def _is_placeholder(uri: str) -> bool:
    if not uri:
        return True
    return any(token in uri for token in ("<username>", "<password>", "<cluster>"))


def _match(doc: dict, query: dict) -> bool:
    if not query:
        return True
    for key, value in query.items():
        if key == "$or":
            if not any(_match(doc, part) for part in value):
                return False
            continue
        actual = doc.get(key)
        if isinstance(value, dict):
            if "$gt" in value:
                if not (actual is not None and actual > value["$gt"]):
                    return False
            elif "$gte" in value:
                if not (actual is not None and actual >= value["$gte"]):
                    return False
            elif "$lte" in value:
                if not (actual is not None and actual <= value["$lte"]):
                    return False
            elif "$ne" in value:
                if actual == value["$ne"]:
                    return False
            elif "$in" in value:
                if actual not in value["$in"]:
                    return False
            elif "$text" in value:
                needle = str(value["$text"].get("$search", "")).lower()
                hay = " ".join(
                    [str(doc.get("name", "")), str(doc.get("category", "")), str(doc.get("keywords", ""))]
                ).lower()
                if needle not in hay:
                    return False
            else:
                if actual != value:
                    return False
        elif hasattr(value, "search"):
            if not value.search(str(actual or "")):
                return False
        else:
            if actual != value:
                return False
    return True


class InMemoryCursor:
    def __init__(self, docs: list[dict]):
        self._docs = docs

    def sort(self, key, direction=1):
        if isinstance(key, list):
            for field, sort_direction in reversed(key):
                reverse = sort_direction == -1
                self._docs.sort(key=lambda item: item.get(field), reverse=reverse)
            return self
        reverse = direction == -1
        self._docs.sort(key=lambda item: item.get(key), reverse=reverse)
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


@dataclass
class InsertResult:
    inserted_id: ObjectId


class InMemoryCollection:
    def __init__(self):
        self.docs: list[dict] = []

    def index_information(self):
        return {}

    def create_index(self, *args, **kwargs):
        return None

    def find(self, query=None, projection=None):
        query = query or {}
        rows = [copy.deepcopy(doc) for doc in self.docs if _match(doc, query)]
        if projection and projection.get("_id") == 0:
            for row in rows:
                row.pop("_id", None)
        return InMemoryCursor(rows)

    def find_one(self, query=None, projection=None):
        for row in self.find(query, projection):
            return row
        return None

    def insert_one(self, doc: dict):
        row = copy.deepcopy(doc)
        row.setdefault("_id", ObjectId())
        self.docs.append(row)
        return InsertResult(inserted_id=row["_id"])

    def update_one(self, query: dict, update: dict, upsert: bool = False):
        for index, doc in enumerate(self.docs):
            if _match(doc, query):
                row = self.docs[index]
                if "$set" in update:
                    row.update(update["$set"])
                if "$inc" in update:
                    for key, value in update["$inc"].items():
                        row[key] = row.get(key, 0) + value
                if "$setOnInsert" in update:
                    for key, value in update["$setOnInsert"].items():
                        row.setdefault(key, value)
                return
        if upsert:
            merged = dict(query)
            for key, value in update.get("$setOnInsert", {}).items():
                merged.setdefault(key, value)
            merged.update(update.get("$set", {}))
            for key, value in update.get("$inc", {}).items():
                merged[key] = merged.get(key, 0) + value
            self.insert_one(merged)

    def delete_one(self, query: dict):
        for index, doc in enumerate(self.docs):
            if _match(doc, query):
                self.docs.pop(index)
                return

    def delete_many(self, query: dict):
        self.docs = [doc for doc in self.docs if not _match(doc, query)]

    def count_documents(self, query: dict):
        return sum(1 for doc in self.docs if _match(doc, query))


class InMemoryDB:
    def __init__(self):
        self._cols: dict[str, InMemoryCollection] = {}
        self._seed()

    def __getitem__(self, name: str):
        if name not in self._cols:
            self._cols[name] = InMemoryCollection()
        return self._cols[name]

    def _seed(self):
        _U = "/static/images/products/"
        products = self["products"]
        for product in [
            {"name": "Amul Full Cream Milk", "category": "Dairy",      "price": 68,  "discount": 6,  "weight": "1L",    "slug": "amul-full-cream-milk", "image_url": _U + "milk_bottle.png", "keywords": "milk dairy amul",       "is_best_seller": True},
            {"name": "Fresh Banana",          "category": "Fruits",     "price": 50,  "discount": 10, "weight": "1 Dozen","slug": "fresh-banana",          "image_url": _U + "fruits_basket.png", "keywords": "banana fruit",          "is_best_seller": True},
            {"name": "Toor Dal",              "category": "Pulses",     "price": 145, "discount": 0,  "weight": "1kg",   "slug": "toor-dal",              "image_url": _U + "pulses_bowl.png", "keywords": "dal pulses toor",      "is_best_seller": False},
            {"name": "Wheat Flour (Atta)",    "category": "Flour",      "price": 280, "discount": 8,  "weight": "5kg",   "slug": "wheat-flour-atta",      "image_url": _U + "flour_bowl.png", "keywords": "flour atta wheat",     "is_best_seller": True},
            {"name": "Tomato",                "category": "Vegetables", "price": 40,  "discount": 0,  "weight": "1kg",   "slug": "tomato",                "image_url": _U + "vegetables_basket.png", "keywords": "tomato vegetable",      "is_best_seller": False},
            {"name": "Onion",                 "category": "Vegetables", "price": 30,  "discount": 0,  "weight": "1kg",   "slug": "onion",                 "image_url": _U + "vegetables_basket.png", "keywords": "onion pyaaz vegetable", "is_best_seller": True},
            {"name": "Potato",                "category": "Vegetables", "price": 25,  "discount": 0,  "weight": "1kg",   "slug": "potato",                "image_url": _U + "vegetables_basket.png", "keywords": "potato aloo vegetable", "is_best_seller": False},
            {"name": "Basmati Rice",          "category": "Grains",     "price": 320, "discount": 10, "weight": "5kg",   "slug": "basmati-rice",          "image_url": _U + "rice_bowl.png", "keywords": "rice basmati chawal",  "is_best_seller": True},
            {"name": "Paneer",                "category": "Dairy",      "price": 90,  "discount": 5,  "weight": "200g",  "slug": "paneer",                "image_url": _U + "milk_bottle.png", "keywords": "paneer cottage cheese", "is_best_seller": True},
            {"name": "Garam Masala",          "category": "Spices",     "price": 60,  "discount": 0,  "weight": "50g",   "slug": "garam-masala",          "image_url": _U + "spices_bowl.png", "keywords": "garam masala spice",   "is_best_seller": True},
        ]:
            products.insert_one(product)


def _get_client():
    global _client, _fallback_db, _using_fallback
    with _init_lock:
        if _client is not None:
            return _client
        uri = getattr(settings, "MONGODB_URI", "") or ""
        if _is_placeholder(uri):
            _using_fallback = True
            _fallback_db = InMemoryDB()
            return None
        try:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
            )
            client.admin.command("ping")
            _client = client
            _using_fallback = False
            return _client
        except Exception:
            _using_fallback = True
            _fallback_db = InMemoryDB()
            return None


def get_db():
    client = _get_client()
    if client is None:
        return _fallback_db
    return client[settings.MONGODB_DB_NAME]


def using_fallback() -> bool:
    _get_client()
    return _using_fallback


def get_products_collection():
    return get_db()["products"]


def get_cart_collection():
    return get_db()["cart"]


def get_users_collection():
    return get_db()["users"]


def get_orders_collection():
    return get_db()["orders"]


def get_expenses_collection():
    return get_db()["expenses"]


def get_analytics_collection():
    return get_db()["product_analytics"]


def ensure_product_indexes():
    col = get_products_collection()
    existing = col.index_information()
    if "text_search" not in existing:
        try:
            col.create_index(
                [("name", TEXT), ("keywords", TEXT), ("category", TEXT)],
                name="text_search",
            )
        except Exception:
            pass


def search_products(query_text: str, limit: int = 20) -> list:
    col = get_products_collection()
    try:
        results = list(
            col.find({"$text": {"$search": query_text}}, {"score": {"$meta": "textScore"}})
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )
        if results:
            return results
    except Exception:
        pass

    pattern = re.compile(re.escape(query_text), re.IGNORECASE)
    return list(
        col.find({"$or": [{"name": pattern}, {"keywords": pattern}, {"category": pattern}]}).limit(limit)
    )


def search_product_by_name(name: str):
    col = get_products_collection()
    pattern = re.compile(f"^{re.escape(name)}$", re.IGNORECASE)
    product = col.find_one({"name": pattern})
    if product:
        return product
    pattern = re.compile(re.escape(name), re.IGNORECASE)
    return col.find_one({"$or": [{"name": pattern}, {"keywords": pattern}]})
