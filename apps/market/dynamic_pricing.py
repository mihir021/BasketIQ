"""Behavioral analytics-driven dynamic pricing."""

import math
from datetime import datetime

MAX_MARKUP_PCT = 25
MAX_DISCOUNT_PCT = 10

_DEMAND_BANDS = [
    (100, float("inf"), 15.0, "Viral demand"),
    (50, 100, 10.0, "Hot product"),
    (20, 50, 6.0, "Rising demand"),
    (5, 20, 3.0, "Moderate demand"),
    (0, 5, -3.0, "Low demand deal"),
]

_TIME_ADJUSTMENTS = {
    range(0, 6): -2,
    range(6, 11): 0,
    range(11, 14): 1,
    range(14, 17): 0,
    range(17, 21): 2,
    range(21, 24): -1,
}

_TIME_SENSITIVE_CATEGORIES = {
    "Vegetables": 1.2,
    "Fruits": 1.0,
    "Dairy": 0.8,
    "default": 0.4,
}

# High engagement = higher perceived value → price increase (not discount)
_ENGAGEMENT_PREMIUMS = [
    (8, 4),
    (5, 2),
    (3, 1),
]

_BEST_SELLER_PREMIUM = 5
_NO_DISCOUNT_PREMIUM = 2


def compute_demand_score(view_count: int, cart_add_count: int, order_count: int) -> float:
    return (view_count * 0.1) + (cart_add_count * 1.0) + (order_count * 3.0)


def _get_demand_adjustment(demand_score: float) -> tuple[float, str | None]:
    for min_score, max_score, adjustment, label in _DEMAND_BANDS:
        if min_score <= demand_score < max_score:
            return adjustment, label
    return 0.0, None


def _get_time_adjustment(category: str) -> float:
    hour = datetime.now().hour
    base_adjustment = 0
    for hours, adjustment in _TIME_ADJUSTMENTS.items():
        if hour in hours:
            base_adjustment = adjustment
            break
    multiplier = _TIME_SENSITIVE_CATEGORIES.get(category, _TIME_SENSITIVE_CATEGORIES["default"])
    return base_adjustment * multiplier


def _get_engagement_adjustment(session_views: dict, category: str) -> float:
    """More browsing in a category signals higher interest → price premium."""
    view_count = session_views.get(category, 0)
    premium = 0
    for min_views, value in _ENGAGEMENT_PREMIUMS:
        if view_count >= min_views:
            premium = value
    return premium


def _get_popularity_adjustment(is_best_seller: bool, has_existing_discount: bool) -> float:
    if is_best_seller:
        return _BEST_SELLER_PREMIUM
    if not has_existing_discount:
        return _NO_DISCOUNT_PREMIUM
    return 0


def calculate_dynamic_price(
    base_price: float,
    existing_discount_pct: float,
    category: str,
    is_best_seller: bool,
    session_data: dict | None = None,
    demand_score: float = 0.0,
) -> dict:
    session_data = session_data or {}
    category_views = session_data.get("category_views", {})

    factors = []

    demand_adjustment, demand_label = _get_demand_adjustment(demand_score)
    if demand_adjustment and demand_label:
        factors.append((demand_label, demand_adjustment))

    time_adjustment = _get_time_adjustment(category)
    if time_adjustment:
        factors.append(("Peak demand" if time_adjustment > 0 else "Off-peak deal", time_adjustment))

    engagement_adjustment = _get_engagement_adjustment(category_views, category)
    if engagement_adjustment:
        factors.append(("High interest", engagement_adjustment))

    popularity_adjustment = _get_popularity_adjustment(is_best_seller, existing_discount_pct > 0)
    if popularity_adjustment:
        factors.append(("Popular item" if popularity_adjustment > 0 else "Special offer", popularity_adjustment))

    total_dynamic = max(-MAX_DISCOUNT_PCT, min(MAX_MARKUP_PCT, sum(value for _, value in factors)))
    static_price = base_price * (1 - existing_discount_pct / 100)
    final_price = max(1, round(static_price * (1 + total_dynamic / 100)))
    savings = round(base_price - final_price)
    effective_discount = round((1 - final_price / base_price) * 100, 1) if base_price > 0 else 0

    if demand_score >= 100:
        demand_tier = "viral"
    elif demand_score >= 50:
        demand_tier = "hot"
    elif demand_score >= 20:
        demand_tier = "rising"
    elif demand_score < 5:
        demand_tier = "deal"
    else:
        demand_tier = "normal"

    return {
        "original_price": base_price,
        "static_discount": existing_discount_pct,
        "dynamic_adjustment": round(total_dynamic, 1),
        "final_price": final_price,
        "effective_discount": effective_discount,
        "savings": max(0, savings),
        "factors": factors,
        "demand_score": round(demand_score, 1),
        "demand_tier": demand_tier,
    }
