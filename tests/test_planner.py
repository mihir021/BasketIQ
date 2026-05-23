from django.urls import reverse

from apps.planner import ai_planner


def test_bulk_samosa_fallback_scales_real_quantities(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("samosa for 500 people")
    quantities = {item["name"]: (item["quantity"], item["unit"]) for item in result["ingredients"]}

    assert result["dish"] == "Samosa"
    assert result["servings"] == 500
    assert quantities["Potato"] == ("75", "kg")
    assert quantities["All Purpose Flour (Maida)"] == ("20", "kg")
    assert quantities["Vegetable Oil"] == ("5", "L")
    assert quantities["Onion"] == ("25", "pcs")


def test_planner_rejects_non_food(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("write a python function")

    assert "error" in result


def test_pantry_splits_pasted_ingredients_and_ranks(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.generate_from_pantry(["potato onion tomato"])

    assert result["suggestions"][0]["dish"] == "Aloo Sabzi (Spiced Potatoes)"
    assert result["suggestions"][0]["match_score"] == 100
    assert result["pantry"] == ["Potato", "Onion", "Tomato"]


def test_pantry_rejects_non_food(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.generate_from_pantry(["laptop", "phone"])

    assert "error" in result


def test_planner_api_responds_for_bulk_request(client, settings):
    settings.OPENAI_API_KEY = ""

    response = client.post(
        reverse("planner:api_planner_generate"),
        data={"query": "paneer butter masala for 20"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["servings"] == 20
