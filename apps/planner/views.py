import json
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from apps.market import mongo_client
from apps.market.views import _json_serialise

from .ai_planner import generate_plan, generate_from_pantry


def planner_page(request):
    return render(request, "planner/planner.html")


def pantry_page(request):
    return render(request, "planner/pantry.html")


@csrf_exempt
def api_planner_generate(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    query = data.get("query", "").strip()
    if not query:
        return JsonResponse({"error": "Please describe what you want to cook."}, status=400)

    result = generate_plan(query)
    if "error" in result:
        return JsonResponse(result, status=200)
    return JsonResponse(_json_serialise(result))


@csrf_exempt
def api_planner_add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    items = data.get("items", [])
    token = data.get("token", "")
    if not items:
        return JsonResponse({"error": "No items provided."}, status=400)

    user_id = "guest"
    if token:
        user = mongo_client.get_users_collection().find_one({"token": token})
        if user:
            user_id = str(user["_id"])

    cart = mongo_client.get_cart_collection()
    for item in items:
        existing = cart.find_one({"user_id": user_id, "product_id": item.get("product_id")})
        if existing:
            cart.update_one({"_id": existing["_id"]}, {"$inc": {"quantity": item.get("quantity", 1)}})
        else:
            cart.insert_one(
                {
                    "user_id": user_id,
                    "product_id": item.get("product_id"),
                    "product_name": item.get("product_name", ""),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0),
                    "image_url": item.get("image_url", ""),
                    "added_at": datetime.utcnow(),
                }
            )
    return JsonResponse({"success": True, "cart_count": cart.count_documents({"user_id": user_id})})


@csrf_exempt
def api_pantry_suggest(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    ingredients = data.get("ingredients", [])
    if not isinstance(ingredients, list):
        return JsonResponse({"error": "ingredients must be a list."}, status=400)
    result = generate_from_pantry(ingredients)
    return JsonResponse(_json_serialise(result))


def api_ingredient_search(request):
    """GET /api/pantry/search/?q=potato — returns matching products for autocomplete."""
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'results': []})
    products = mongo_client.search_products(q, limit=8)
    results = []
    for p in products:
        image = p.get('image_url', '')
        if not image and p.get('images'):
            image = p['images'][0]
        results.append({
            'name': p.get('name', ''),
            'category': p.get('category', ''),
            'price': p.get('price', 0),
            'weight': p.get('weight', ''),
            'image': image,
        })
    return JsonResponse({'results': results})
