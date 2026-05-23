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


def test_planner_understands_dal_vada_typo(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("dal vda for 4")
    ingredient_names = {item["name"] for item in result["ingredients"]}

    assert result["dish"] == "Dal Vada"
    assert result["servings"] == 4
    assert "Chana Dal" in ingredient_names
    assert "Toor Dal" not in ingredient_names


def test_planner_understands_pani_puri(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("pani puri for 5")
    ingredient_names = {item["name"] for item in result["ingredients"]}

    assert result["dish"] == "Pani Puri"
    assert result["servings"] == 5
    assert "Puri" in ingredient_names
    assert "Tamarind" in ingredient_names


def test_planner_understands_gujarati_bhinda_nu_shak(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("bhinda nu shak for 3")
    ingredient_names = {item["name"] for item in result["ingredients"]}

    assert result["dish"] == "Bhinda Nu Shaak"
    assert result["servings"] == 3
    assert "Bhindi" in ingredient_names
    assert "Dry Mango Powder (Amchur)" in ingredient_names


def test_planner_understands_gujarati_gajar_no_halvo(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("gajar no halvo for 4")
    ingredient_names = {item["name"] for item in result["ingredients"]}

    assert result["dish"] == "Gajar No Halvo"
    assert result["servings"] == 4
    assert "Carrot" in ingredient_names
    assert "Full Cream Milk" in ingredient_names


def test_planner_uses_gujarati_halvo_pattern_for_dudhi(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("dudhi no halvo")
    ingredient_names = {item["name"] for item in result["ingredients"]}

    assert result["dish"] == "Dudhi No Halvo"
    assert "Bottle Gourd" in ingredient_names
    assert "Full Cream Milk" in ingredient_names
    assert "Onion" not in ingredient_names
    assert "Tomato" not in ingredient_names


def test_planner_uses_gujarati_shaak_pattern_for_bataka(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.parse_dish_request("bataka nu shaak for 4")
    ingredient_names = {item["name"] for item in result["ingredients"]}

    assert result["dish"] == "Bataka Nu Shaak"
    assert result["servings"] == 4
    assert "Potato" in ingredient_names
    assert "Mustard Seeds (Rai)" in ingredient_names


def test_planner_price_scales_by_required_packages(settings):
    settings.OPENAI_API_KEY = ""

    result = ai_planner.generate_plan("daal pakwaan for 400")
    chana = next(item for item in result["items"] if item["ingredient_name"] == "Chana Dal")

    assert chana["needed_quantity"] == "32kg"
    assert chana["package_count"] == 32
    assert chana["estimated_price"] == chana["unit_price"] * chana["package_count"]
    assert result["total_price"] > 1000


def test_planner_estimates_count_items_against_weight_packs():
    ingredient = {
        "name": "Green Chilli",
        "quantity": "200",
        "unit": "pcs",
        "category": "Vegetables",
    }
    product = {
        "name": "Green Chilli",
        "weight": "100g",
        "unit": "pack",
        "category": "Vegetables",
    }

    assert ai_planner._estimate_package_count(ingredient, product) == 10


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
