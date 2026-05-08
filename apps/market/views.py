import re
from datetime import datetime

from bson import ObjectId
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from . import mongo_client
from .dynamic_pricing import calculate_dynamic_price, compute_demand_score


def home(request):
    return render(request, "pages/landing.html")


def index_page(request):
    return render(request, "market/index.html")


def contact_page(request):
    return render(request, "market/contact.html")


def product_page(request, product_id):
    return render(request, "market/product.html", {"product_id": product_id})


def _json_serialise(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [_json_serialise(item) for item in doc]
    if isinstance(doc, dict):
        serialised = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                serialised[key] = str(value)
            elif isinstance(value, datetime):
                serialised[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialised[key] = _json_serialise(value)
            else:
                serialised[key] = value
        return serialised
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


def _get_session_data(request):
    if not hasattr(request, "session"):
        return {"category_views": {}, "total_views": 0, "cart_count": 0}
    return {
        "category_views": request.session.get("dp_category_views", {}),
        "total_views": request.session.get("dp_total_views", 0),
        "cart_count": request.session.get("dp_cart_count", 0),
    }


def _track_product_view(request, category):
    if not hasattr(request, "session"):
        return
    views = request.session.get("dp_category_views", {})
    views[category] = views.get(category, 0) + 1
    request.session["dp_category_views"] = views
    request.session["dp_total_views"] = request.session.get("dp_total_views", 0) + 1
    request.session.modified = True


def _get_demand_scores_batch(product_ids: list) -> dict:
    analytics_col = mongo_client.get_analytics_collection()
    try:
        rows = list(analytics_col.find({"product_id": {"$in": product_ids}}))
        return {
            str(row["product_id"]): compute_demand_score(
                row.get("view_count", 0),
                row.get("cart_add_count", 0),
                row.get("order_count", 0),
            )
            for row in rows
        }
    except Exception:
        return {}


def _track_behavior(product_id, product_name, category, event: str):
    field_map = {
        "view": "view_count",
        "cart": "cart_add_count",
        "order": "order_count",
    }
    field = field_map.get(event)
    if not field:
        return
    try:
        analytics_col = mongo_client.get_analytics_collection()
        analytics_col.update_one(
            {"product_id": product_id},
            {
                "$inc": {field: 1},
                "$set": {
                    "product_name": product_name,
                    "category": category,
                    "last_updated": datetime.utcnow(),
                },
                "$setOnInsert": {"product_id": product_id},
            },
            upsert=True,
        )
    except Exception:
        pass


def _apply_dynamic_pricing(products, session_data):
    product_ids = [item.get("_id") for item in products if item.get("_id")]
    demand_scores = _get_demand_scores_batch(product_ids)

    for product in products:
        if "base_price" in product and "price" not in product:
            product["price"] = product.get("base_price", 0)
        if product.get("images") and not product.get("image_url"):
            product["image_url"] = product["images"][0]

        dynamic = calculate_dynamic_price(
            base_price=product.get("price", 0),
            existing_discount_pct=product.get("discount", 0),
            category=product.get("category", "Other"),
            is_best_seller=product.get("is_best_seller", False),
            session_data=session_data,
            demand_score=demand_scores.get(str(product.get("_id", "")), 0.0),
        )
        product["dynamic_price"] = dynamic["final_price"]
        product["effective_discount"] = dynamic["effective_discount"]
        product["savings"] = dynamic["savings"]
        product["dynamic_adjustment"] = dynamic["dynamic_adjustment"]
        product["pricing_factors"] = dynamic["factors"]
        product["demand_score"] = dynamic["demand_score"]
        product["demand_tier"] = dynamic["demand_tier"]
    return products


@csrf_exempt
def api_products(request):
    search = request.GET.get("search", "")
    category = request.GET.get("category", "All")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    min_discount = request.GET.get("min_discount")
    sort_by = request.GET.get("sort")

    query = {}
    if search:
        pattern = re.compile(re.escape(search), re.IGNORECASE)
        query["$or"] = [{"name": pattern}, {"keywords": pattern}, {"category": pattern}]
    if category and category != "All":
        query["category"] = re.compile(re.escape(category), re.IGNORECASE)
    if min_price or max_price:
        query["price"] = {}
        if min_price:
            query["price"]["$gte"] = int(min_price)
        if max_price:
            query["price"]["$lte"] = int(max_price)
    if min_discount:
        query["discount"] = {"$gte": int(min_discount)}

    sort_config = [("_id", -1)]
    if sort_by == "price_asc":
        sort_config = [("price", 1)]
    elif sort_by == "price_desc":
        sort_config = [("price", -1)]
    elif sort_by == "discount_desc":
        sort_config = [("discount", -1)]

    products = list(mongo_client.get_products_collection().find(query).sort(sort_config).limit(100))
    serialised = _json_serialise(products)
    return JsonResponse(_apply_dynamic_pricing(serialised, _get_session_data(request)), safe=False)


@csrf_exempt
def api_best_sellers(request):
    products = list(mongo_client.get_products_collection().find({"is_best_seller": True}).limit(8))
    serialised = _json_serialise(products)
    return JsonResponse(_apply_dynamic_pricing(serialised, _get_session_data(request)), safe=False)


@csrf_exempt
def api_offers(request):
    products = list(mongo_client.get_products_collection().find({"discount": {"$gt": 0}}).limit(8))
    serialised = _json_serialise(products)
    return JsonResponse(_apply_dynamic_pricing(serialised, _get_session_data(request)), safe=False)


@csrf_exempt
def api_product_detail(request, product_id):
    try:
        product = mongo_client.get_products_collection().find_one({"_id": ObjectId(product_id)})
        if not product:
            return JsonResponse({"error": "Product not found"}, status=404)

        serialised = _json_serialise(product)
        if "base_price" in serialised and "price" not in serialised:
            serialised["price"] = serialised.get("base_price", 0)
        if serialised.get("images") and not serialised.get("image_url"):
            serialised["image_url"] = serialised["images"][0]

        _track_behavior(product["_id"], product.get("name", ""), product.get("category", "Other"), "view")
        _track_product_view(request, product.get("category", "Other"))
        dynamic = calculate_dynamic_price(
            base_price=serialised.get("price", 0),
            existing_discount_pct=serialised.get("discount", 0),
            category=serialised.get("category", "Other"),
            is_best_seller=serialised.get("is_best_seller", False),
            session_data=_get_session_data(request),
            demand_score=_get_demand_scores_batch([product["_id"]]).get(str(product["_id"]), 0.0),
        )
        serialised["dynamic_price"] = dynamic["final_price"]
        serialised["effective_discount"] = dynamic["effective_discount"]
        serialised["savings"] = dynamic["savings"]
        serialised["dynamic_adjustment"] = dynamic["dynamic_adjustment"]
        serialised["pricing_factors"] = dynamic["factors"]
        serialised["demand_score"] = dynamic["demand_score"]
        serialised["demand_tier"] = dynamic["demand_tier"]
        return JsonResponse(serialised)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@csrf_exempt
def api_product_suggestions(request, product_id):
    try:
        col = mongo_client.get_products_collection()
        product = col.find_one({"_id": ObjectId(product_id)})
        if not product:
            return JsonResponse({"error": "Product not found"}, status=404)

        suggestions = list(
            col.find({"category": product.get("category", ""), "_id": {"$ne": ObjectId(product_id)}}).limit(8)
        )
        if len(suggestions) < 4:
            extra = list(col.find({"_id": {"$ne": ObjectId(product_id)}, "is_best_seller": True}).limit(8))
            existing_ids = {str(item["_id"]) for item in suggestions}
            for item in extra:
                if str(item["_id"]) not in existing_ids:
                    suggestions.append(item)
        serialised = _json_serialise(suggestions)
        return JsonResponse(_apply_dynamic_pricing(serialised, _get_session_data(request)), safe=False)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@csrf_exempt
def api_track_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    import json

    try:
        data = json.loads(request.body)
        action = data.get("action", "")
        product_id = data.get("product_id")
        product_name = data.get("product_name", "")
        category = data.get("category", "Other")

        if action == "view_product":
            _track_product_view(request, category)
            if product_id:
                try:
                    _track_behavior(ObjectId(product_id), product_name, category, "view")
                except Exception:
                    pass
        elif action in {"add_to_cart", "cart_update"}:
            request.session["dp_cart_count"] = data.get("cart_count", 0)
            request.session.modified = True
            if action == "add_to_cart" and product_id:
                try:
                    _track_behavior(ObjectId(product_id), product_name, category, "cart")
                except Exception:
                    pass
        elif action == "purchase" and product_id:
            try:
                _track_behavior(ObjectId(product_id), product_name, category, "order")
            except Exception:
                pass
        elif action == "reset":
            request.session["dp_category_views"] = {}
            request.session["dp_total_views"] = 0
            request.session["dp_cart_count"] = 0
            request.session.modified = True

        return JsonResponse({"status": "ok", "session": _get_session_data(request)})
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@csrf_exempt
def api_analytics_trending(request):
    analytics_col = mongo_client.get_analytics_collection()
    try:
        rows = list(analytics_col.find({}).sort([("view_count", -1)]).limit(20))
        result = []
        for row in rows:
            score = compute_demand_score(
                row.get("view_count", 0),
                row.get("cart_add_count", 0),
                row.get("order_count", 0),
            )
            result.append(
                {
                    "product_id": str(row.get("product_id", "")),
                    "product_name": row.get("product_name", ""),
                    "category": row.get("category", ""),
                    "view_count": row.get("view_count", 0),
                    "cart_add_count": row.get("cart_add_count", 0),
                    "order_count": row.get("order_count", 0),
                    "demand_score": round(score, 1),
                }
            )
        result.sort(key=lambda item: item["demand_score"], reverse=True)
        return JsonResponse(result, safe=False)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@csrf_exempt
def api_contact_message(request):
    """Save a user contact message to MongoDB."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    import json
    try:
        data = json.loads(request.body)
        name    = (data.get("name",    "") or "").strip()
        email   = (data.get("email",   "") or "").strip()
        subject = (data.get("subject", "") or "").strip()
        message = (data.get("message", "") or "").strip()
        category = (data.get("category", "General") or "General").strip()

        if not name or not email or not message:
            return JsonResponse({"error": "Name, email and message are required."}, status=400)

        doc = {
            "name": name,
            "email": email,
            "subject": subject or "No Subject",
            "message": message,
            "category": category,
            "status": "open",
            "created_at": datetime.utcnow(),
        }
        col = mongo_client.get_db()["contact_messages"]
        result = col.insert_one(doc)
        return JsonResponse({"success": True, "id": str(result.inserted_id)})
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
