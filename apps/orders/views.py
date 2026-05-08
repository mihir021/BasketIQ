import json
import random
from datetime import datetime

from bson import ObjectId
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.views import _get_user_from_token
from apps.market import mongo_client
from apps.market.dynamic_pricing import calculate_dynamic_price, compute_demand_score
from apps.market.views import _json_serialise, _get_session_data, _get_demand_scores_batch, _track_behavior


def cart_page(request):
    return render(request, "orders/cart.html")


def my_order_page(request):
    return render(request, "orders/my_order.html")


def _recalculate_cart_prices(items, request):
    """Look up current product data and recalculate dynamic prices for cart items."""
    products_col = mongo_client.get_products_collection()
    product_ids = []
    for item in items:
        pid = item.get("product_id")
        if pid:
            try:
                product_ids.append(ObjectId(pid))
            except Exception:
                pass

    products_map = {}
    if product_ids:
        for prod in products_col.find({"_id": {"$in": product_ids}}):
            products_map[str(prod["_id"])] = prod

    demand_scores = _get_demand_scores_batch(product_ids) if product_ids else {}
    session_data = _get_session_data(request)

    for item in items:
        pid = str(item.get("product_id", ""))
        product = products_map.get(pid)
        if product:
            dynamic = calculate_dynamic_price(
                base_price=product.get("price", 0),
                existing_discount_pct=product.get("discount", 0),
                category=product.get("category", "Other"),
                is_best_seller=product.get("is_best_seller", False),
                session_data=session_data,
                demand_score=demand_scores.get(pid, 0.0),
            )
            item["price"] = dynamic["final_price"]
            item["dynamic_price"] = dynamic["final_price"]
            item["original_price"] = product.get("price", 0)
            item["effective_discount"] = dynamic["effective_discount"]
            item["dynamic_adjustment"] = dynamic["dynamic_adjustment"]
    return items


@csrf_exempt
def api_cart(request):
    user = _get_user_from_token(request)
    user_id = str(user["_id"]) if user else "guest"
    items = list(mongo_client.get_cart_collection().find({"user_id": user_id}).sort("added_at", -1))

    # Recalculate dynamic prices so cart always shows current prices
    items = _recalculate_cart_prices(items, request)

    return JsonResponse(_json_serialise(items), safe=False)


@csrf_exempt
def api_cart_update(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    user = _get_user_from_token(request)
    user_id = str(user["_id"]) if user else "guest"
    data = json.loads(request.body)
    item_id = data.get("item_id")
    quantity = int(data.get("quantity", 1))
    cart = mongo_client.get_cart_collection()

    if quantity <= 0:
        cart.delete_one({"_id": ObjectId(item_id), "user_id": user_id})
    else:
        cart.update_one({"_id": ObjectId(item_id), "user_id": user_id}, {"$set": {"quantity": quantity}})

    items = list(cart.find({"user_id": user_id}))
    return JsonResponse({"success": True, "cart_count": len(items)})


@csrf_exempt
def api_cart_remove(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    user = _get_user_from_token(request)
    user_id = str(user["_id"]) if user else "guest"
    item_id = json.loads(request.body).get("item_id")
    cart = mongo_client.get_cart_collection()
    cart.delete_one({"_id": ObjectId(item_id), "user_id": user_id})
    items = list(cart.find({"user_id": user_id}))
    return JsonResponse({"success": True, "cart_count": len(items)})


@csrf_exempt
def api_cart_checkout(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    user = _get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Please login first."}, status=401)

    user_id = str(user["_id"])
    cart = mongo_client.get_cart_collection()
    items = list(cart.find({"user_id": user_id}))
    if not items:
        return JsonResponse({"error": "Your cart is empty."}, status=400)

    # ── Recalculate CURRENT dynamic prices from the products DB ──
    items = _recalculate_cart_prices(items, request)

    order_items = []
    total = 0
    for item in items:
        quantity = item.get("quantity", 1)
        price = item.get("price", 0)
        line_total = quantity * price
        total += line_total
        order_items.append(
            {
                "product_id": str(item.get("product_id", "")),
                "name": item.get("product_name", ""),
                "quantity": quantity,
                "price": price,
                "line_total": line_total,
                "image_url": item.get("image_url", ""),
            }
        )

    order_id = f"BK-{random.randint(10000, 99999)}"
    mongo_client.get_orders_collection().insert_one(
        {
            "user_id": user_id,
            "order_id": order_id,
            "items": order_items,
            "total_amount": round(total, 2),
            "status": "Confirmed",
            "date": datetime.utcnow(),
        }
    )

    # ── Track each purchased item in analytics so demand scores increase ──
    for item in items:
        try:
            pid = item.get("product_id", "")
            _track_behavior(
                ObjectId(pid) if isinstance(pid, str) else pid,
                item.get("product_name", ""),
                item.get("category", "Other"),
                "order",
            )
        except Exception:
            pass

    # ── Write to expenses collection so profile charts update ──────────
    expenses_col = mongo_client.get_db()["expenses"]
    # Group by category so the pie chart breaks down correctly
    category_totals: dict = {}
    for item in order_items:
        cat = item.get("name", "Groceries")  # use product name as expense title
        category_totals[cat] = category_totals.get(cat, 0) + item["line_total"]

    now = datetime.utcnow()
    expense_docs = [
        {
            "user_id": user_id,
            "title": title,
            "amount": round(amount, 2),
            "category": _expense_category(order_items, title),
            "order_id": order_id,
            "date": now,
        }
        for title, amount in category_totals.items()
    ]
    if expense_docs:
        expenses_col.insert_many(expense_docs)
    # ─────────────────────────────────────────────────────────────────────

    cart.delete_many({"user_id": user_id})
    return JsonResponse(
        {
            "success": True,
            "order_id": order_id,
            "total_amount": round(total, 2),
            "item_count": len(order_items),
        }
    )


def _expense_category(order_items: list, product_name: str) -> str:
    """Map a product name back to its grocery category for the expense breakdown."""
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
    name_lower = product_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return category
    return "Groceries"


@csrf_exempt
def api_orders(request):
    user = _get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    docs = list(mongo_client.get_orders_collection().find({"user_id": str(user["_id"])}).sort("date", -1).limit(50))
    return JsonResponse(_json_serialise(docs), safe=False)
