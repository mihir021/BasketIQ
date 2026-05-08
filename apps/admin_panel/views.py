from functools import wraps
from django.shortcuts import render, redirect


# ── Auth helpers ───────────────────────────────────────────────────────────────

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("admin_token"):
            return redirect("/admin-panel/login/")
        return view_func(request, *args, **kwargs)
    return _wrapped


def _ctx(request, page):
    """Base context passed to every admin template."""
    return {
        "active_page": page,
        "admin_name": request.session.get("admin_name", "Admin"),
        "admin_role": request.session.get("admin_role", "admin"),
        "admin_token": request.session.get("admin_token", ""),
    }


# ── Auth views ─────────────────────────────────────────────────────────────────

def admin_login(request):
    if request.session.get("admin_token"):
        return redirect("/admin-panel/")
    error = None
    if request.method == "POST":
        from apps.admin_api.services import login_admin
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        payload = login_admin(email=email, password=password)
        if payload:
            request.session["admin_token"] = payload["token"]
            request.session["admin_name"] = payload["admin"]["name"]
            request.session["admin_role"] = payload["admin"].get("role", "admin")
            return redirect("/admin-panel/")
        error = "Invalid email or password. Please try again."
    return render(request, "admin_panel/login.html", {"error": error})


def admin_logout(request):
    request.session.flush()
    return redirect("/admin-panel/login/")


# ── Page views (all protected) ─────────────────────────────────────────────────

@admin_required
def overview(request):
    return render(request, "admin_panel/overview.html", _ctx(request, "overview"))


@admin_required
def users(request):
    return render(request, "admin_panel/users.html", _ctx(request, "users"))


@admin_required
def orders(request):
    return render(request, "admin_panel/orders.html", _ctx(request, "orders"))


@admin_required
def analytics(request):
    return render(request, "admin_panel/analytics.html", _ctx(request, "analytics"))


@admin_required
def products(request):
    return render(request, "admin_panel/products.html", _ctx(request, "products"))


@admin_required
def ai_insights(request):
    return render(request, "admin_panel/ai_insights.html", _ctx(request, "ai_insights"))
