import json
import os
import secrets
from datetime import datetime

from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from apps.market import mongo_client

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def login_page(request):
    return render(request, "pages/login.html")


def signup_page(request):
    return render(request, "pages/register.html")


def profile_page(request):
    return render(request, "accounts/profile.html")


def _get_user_from_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    return mongo_client.get_users_collection().find_one({"token": token})


@csrf_exempt
def api_signup(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    location = data.get("location", "Not provided")

    if not name or not email or not password:
        return JsonResponse({"error": "Name, email and password are required."}, status=400)

    users = mongo_client.get_users_collection()
    if users.find_one({"email": email}):
        return JsonResponse({"error": "Email already registered."}, status=400)

    token = secrets.token_hex(32)
    result = users.insert_one(
        {
            "name": name,
            "email": email,
            "password": make_password(password),
            "location": location,
            "profile_image": "",
            "token": token,
            "created_at": datetime.utcnow(),
        }
    )

    return JsonResponse(
        {
            "user_id": str(result.inserted_id),
            "token": token,
            "name": name,
            "email": email,
            "message": "Account created successfully! Welcome to BasketIQ!",
        }
    )


@csrf_exempt
def api_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    users = mongo_client.get_users_collection()
    user = users.find_one({"email": email})

    if not user or not check_password(password, user.get("password", "")):
        return JsonResponse({"error": "Invalid email or password."}, status=401)

    token = secrets.token_hex(32)
    users.update_one({"_id": user["_id"]}, {"$set": {"token": token}})

    return JsonResponse(
        {
            "token": token,
            "name": user.get("name", ""),
            "email": user.get("email", ""),
        }
    )


@csrf_exempt
def api_profile(request):
    user = _get_user_from_token(request)
    if not user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "GET":
        expenses = mongo_client.get_expenses_collection()
        total = sum(
            expense.get("amount", 0)
            for expense in expenses.find({"user_id": str(user["_id"])})
        )
        return JsonResponse(
            {
                "name": user.get("name", ""),
                "email": user.get("email", ""),
                "location": user.get("location", "Not provided"),
                "profile_image": user.get("profile_image", ""),
                "total_expenses": total,
            }
        )

    if request.method == "PUT":
        data = json.loads(request.body)
        update_fields = {
            key: data[key]
            for key in ("name", "email", "location", "profile_image")
            if key in data
        }
        users = mongo_client.get_users_collection()
        users.update_one({"_id": user["_id"]}, {"$set": update_fields})
        updated = users.find_one({"_id": user["_id"]})
        return JsonResponse(
            {
                "name": updated.get("name", ""),
                "email": updated.get("email", ""),
                "location": updated.get("location", ""),
                "profile_image": updated.get("profile_image", ""),
            }
        )

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_google_auth(request):
    """Verify a Google ID token and return a session token.

    Flow:
      1. Frontend gets credential (ID token) from Google GSI popup.
      2. Sends it here as JSON {"credential": "<id_token>"}.
      3. We verify it with google-auth library.
      4. Upsert user in MongoDB (create if new, update token if existing).
      5. Return token + name + email — same shape as api_login.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
    except ImportError:
        return JsonResponse(
            {"error": "google-auth not installed. Run: pip install google-auth"},
            status=500,
        )

    try:
        data = json.loads(request.body)
        credential = data.get("credential", "").strip()
        if not credential:
            return JsonResponse({"error": "No credential provided."}, status=400)

        # Verify with Google
        id_info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )

        email = id_info.get("email", "").lower()
        name  = id_info.get("name", email.split("@")[0])
        picture = id_info.get("picture", "")

        if not email:
            return JsonResponse({"error": "Could not retrieve email from Google."}, status=400)

        users = mongo_client.get_users_collection()
        user  = users.find_one({"email": email})
        token = secrets.token_hex(32)

        if user:
            # Existing user — refresh token
            users.update_one(
                {"_id": user["_id"]},
                {"$set": {"token": token, "profile_image": picture or user.get("profile_image", "")}},
            )
        else:
            # New user — create account (no password needed for OAuth users)
            users.insert_one(
                {
                    "name": name,
                    "email": email,
                    "password": "",          # no password for OAuth accounts
                    "location": "Not provided",
                    "profile_image": picture,
                    "token": token,
                    "auth_provider": "google",
                    "created_at": datetime.utcnow(),
                }
            )

        return JsonResponse({"token": token, "name": name, "email": email})

    except ValueError as exc:
        # Token verification failed
        return JsonResponse({"error": f"Invalid Google token: {exc}"}, status=401)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)

