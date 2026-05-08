"""
Backfill expenses from existing orders that were placed before the fix.
Run once: python scripts/backfill_expenses.py
"""
import os, sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
sys.path.insert(0, BASE_DIR)
import django
django.setup()

from apps.market.mongo_client import get_db, get_orders_collection

db = get_db()
orders_col = get_orders_collection()
expenses_col = db["expenses"]

CATEGORY_KEYWORDS = {
    "Vegetables": ["tomato", "potato", "onion", "chilli", "ginger", "garlic",
                   "spinach", "carrot", "capsicum", "cauliflower", "brinjal",
                   "peas", "coriander", "curry"],
    "Fruits":     ["apple", "banana", "mango", "pomegranate", "papaya"],
    "Dairy":      ["milk", "curd", "paneer", "butter", "cream", "ghee"],
    "Pulses":     ["dal", "chana", "rajma", "moong", "urad", "masoor", "kabuli"],
    "Grains":     ["rice", "sooji", "semolina", "basmati"],
    "Flour":      ["flour", "atta", "maida", "besan"],
    "Spices":     ["turmeric", "chilli", "cumin", "coriander", "garam", "pepper",
                   "mustard", "ajwain", "saunf", "amchur", "hing", "salt"],
    "Oil":        ["oil", "ghee"],
    "Pantry":     ["sugar", "jaggery", "tamarind", "honey", "baking", "tea", "papad"],
    "Protein":    ["egg", "chicken"],
}

def get_category(name):
    nl = name.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in nl for kw in keywords):
            return cat
    return "Groceries"

# Find orders that have no corresponding expense entry
all_orders = list(orders_col.find({}))
print(f"Found {len(all_orders)} total orders.")

backfilled = 0
for order in all_orders:
    order_id = order.get("order_id", str(order["_id"]))
    user_id  = order.get("user_id", "")

    # Skip if expenses already exist for this order
    existing = expenses_col.count_documents({"order_id": order_id})
    if existing > 0:
        print(f"  Order {order_id}: already has {existing} expense entries, skipping.")
        continue

    items = order.get("items", [])
    order_date = order.get("date", datetime.utcnow())

    expense_docs = []
    for item in items:
        name = item.get("name", "Grocery Item")
        line_total = item.get("line_total", item.get("price", 0) * item.get("quantity", 1))
        expense_docs.append({
            "user_id": user_id,
            "title": name,
            "amount": round(float(line_total), 2),
            "category": get_category(name),
            "order_id": order_id,
            "date": order_date,
        })

    if expense_docs:
        expenses_col.insert_many(expense_docs)
        backfilled += len(expense_docs)
        print(f"  Order {order_id}: inserted {len(expense_docs)} expense entries (total Rs.{order.get('total_amount', '?')})")

print(f"\nDone! Backfilled {backfilled} expense entries from {len(all_orders)} orders.")
