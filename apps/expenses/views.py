import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.views import _get_user_from_token
from apps.market import mongo_client
from apps.market.views import _json_serialise


@csrf_exempt
def api_expenses(request):
    user = _get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user_id = str(user["_id"])
    expenses = mongo_client.get_expenses_collection()

    if request.method == "GET":
        docs = list(expenses.find({"user_id": user_id}).sort("date", -1).limit(100))
        return JsonResponse(_json_serialise(docs), safe=False)

    if request.method == "POST":
        data = json.loads(request.body)
        doc = {
            "user_id": user_id,
            "title": data.get("title", ""),
            "amount": float(data.get("amount", 0)),
            "category": data.get("category", "Other"),
            "date": datetime.utcnow(),
        }
        result = expenses.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return JsonResponse(_json_serialise(doc))

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_expense_graph(request, graph_type):
    user = _get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    docs = list(mongo_client.get_expenses_collection().find({"user_id": str(user["_id"])}))
    if not docs:
        return JsonResponse({"error": "No data"}, status=404)

    if graph_type == "monthly":
        from datetime import timedelta

        # Build a 6-month rolling window ending this month
        now = datetime.utcnow()
        window = []
        for i in range(5, -1, -1):          # 5 months ago → current month
            m = now.month - i
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            window.append(f"{y}-{m:02d}")

        monthly = {k: 0 for k in window}    # pre-fill with 0
        for doc in docs:
            d = doc.get("date")
            if isinstance(d, datetime):
                month_key = d.strftime("%Y-%m")
            elif isinstance(d, str):
                month_key = d[:7]
            else:
                continue
            if month_key in monthly:
                monthly[month_key] = monthly[month_key] + doc.get("amount", 0)

        sorted_months = window                # already ordered oldest→newest
        # Format labels as "Apr 2026" style for readability
        def fmt_label(ym):
            try:
                return datetime.strptime(ym, "%Y-%m").strftime("%b %Y")
            except Exception:
                return ym

        return JsonResponse(
            {
                "data": [
                    {
                        "x": [fmt_label(m) for m in sorted_months],
                        "y": [round(monthly[m], 2) for m in sorted_months],
                        "type": "scatter",
                        "mode": "lines+markers",
                    }
                ],
                "layout": {"autosize": True},
            }
        )

    if graph_type == "category":
        categories = {}
        for doc in docs:
            label = doc.get("category") or "Other"
            categories[label] = categories.get(label, 0) + doc.get("amount", 0)
        items = sorted(categories.items(), key=lambda item: item[1], reverse=True)
        return JsonResponse(
            {
                "data": [
                    {
                        "labels": [item[0] for item in items],
                        "values": [item[1] for item in items],
                        "type": "pie",
                        "hole": 0.45,
                    }
                ],
                "layout": {"autosize": True},
            }
        )

    return JsonResponse({"error": "Unknown graph type"}, status=400)
