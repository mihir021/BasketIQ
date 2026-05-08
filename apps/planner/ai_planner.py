"""AI-powered grocery planning using OpenAI and BasketIQ product search."""

from __future__ import annotations

import json
import logging
import re

from django.conf import settings

from apps.market import mongo_client

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None

logger = logging.getLogger(__name__)
_openai_client = None
_mongo_lookup_available = True

_FALLBACK_RECIPES = {
    "daal pakwaan": {
        "description": "A traditional Sindhi breakfast of crispy fried flatbreads served with spiced chana dal.",
        "prep_time": "20 mins",
        "cook_time": "45 mins",
        "ingredients": [
            {"name": "Chana Dal", "quantity": "500", "unit": "g", "category": "Pulses"},
            {"name": "Maida", "quantity": "400", "unit": "g", "category": "Flour"},
            {"name": "Onion", "quantity": "2", "unit": "pcs", "category": "Vegetables"},
            {"name": "Tomato", "quantity": "2", "unit": "pcs", "category": "Vegetables"},
            {"name": "Green Chilli", "quantity": "4", "unit": "pcs", "category": "Vegetables"},
            {"name": "Coriander", "quantity": "1", "unit": "bunch", "category": "Vegetables"},
            {"name": "Cumin", "quantity": "2", "unit": "tsp", "category": "Spices"},
            {"name": "Turmeric", "quantity": "1", "unit": "tsp", "category": "Spices"},
            {"name": "Salt", "quantity": "2", "unit": "tsp", "category": "Pantry"},
            {"name": "Oil", "quantity": "500", "unit": "ml", "category": "Oil"},
        ],
        "recipe_steps": [
            "Soak chana dal for 4 hours, then pressure cook until soft with turmeric and salt.",
            "Knead maida with salt, oil, and water into a smooth dough. Rest for 30 minutes.",
            "Heat oil in a kadai. Temper with cumin seeds, hing, and curry leaves.",
            "Add chopped onions and green chillies, saute until golden.",
            "Add tomatoes, turmeric, and red chilli powder. Cook until soft.",
            "Add boiled dal and mash lightly. Simmer for 10 minutes.",
            "Roll dough into thin circles and deep fry until golden and crispy.",
            "Garnish dal with fresh coriander and serve hot with crispy pakwaan.",
        ],
    },
}

_GENERIC_COOKING_STAPLES = [
    {"name": "Onion", "quantity": "2", "unit": "pcs", "category": "Vegetables"},
    {"name": "Tomato", "quantity": "3", "unit": "pcs", "category": "Vegetables"},
    {"name": "Ginger", "quantity": "1", "unit": "piece", "category": "Vegetables"},
    {"name": "Garlic", "quantity": "5", "unit": "cloves", "category": "Vegetables"},
    {"name": "Green Chilli", "quantity": "3", "unit": "pcs", "category": "Vegetables"},
    {"name": "Cumin", "quantity": "1", "unit": "tsp", "category": "Spices"},
    {"name": "Turmeric", "quantity": "1", "unit": "tsp", "category": "Spices"},
    {"name": "Red Chilli Powder", "quantity": "1", "unit": "tsp", "category": "Spices"},
    {"name": "Garam Masala", "quantity": "1", "unit": "tsp", "category": "Spices"},
    {"name": "Coriander", "quantity": "1", "unit": "bunch", "category": "Vegetables"},
    {"name": "Salt", "quantity": "2", "unit": "tsp", "category": "Pantry"},
    {"name": "Oil", "quantity": "3", "unit": "tbsp", "category": "Oil"},
]

_SYSTEM_PROMPT = """You are BasketIQ's expert culinary AI — a professional chef and grocery planning specialist.

═══════════════════════════════════════════════════
STEP 1 - INPUT VALIDATION (ALWAYS DO THIS FIRST)
═══════════════════════════════════════════════════

Before doing anything else, classify the user input into one of these:

A) VALID FOOD REQUEST - a dish name, meal, snack, or cuisine
   Examples: "samosa for 500 people", "pasta for 2", "biryani for a wedding of 200"

B) GARBAGE / SYMBOLS - purely symbols, random chars, no meaningful words
   Examples: "@#$%", "!!!", "123abc", "xyzqq", "&&&", "###"

C) OFF-TOPIC / NON-FOOD - about coding, sports, politics, math, or other domains
   Examples: "write a Python function", "who won the World Cup", "solve x+2=5", "explain blockchain"

D) AMBIGUOUS - could be food but unclear; interpret charitably as a dish

If category B or C, return EXACTLY this JSON and NOTHING else:
{"error": "I can only help with food and grocery planning. Please enter a dish name like \"Paneer Butter Masala for 4\" or \"Samosa for 500 people\"."}

For D, make a reasonable food interpretation and proceed.

═══════════════════════════════════════════════════
STEP 2 - QUANTITY SCALING (CRITICAL - USE REAL CULINARY MATH)
═══════════════════════════════════════════════════

You MUST scale ALL ingredient quantities accurately. Do NOT give token amounts for large crowds.

CALIBRATION REFERENCE:

SAMOSA (1 samosa = 1 serving):
  Potato (filling): 150g per samosa  -> 500 samosas = 75 kg
  Maida (dough):     40g per samosa  -> 500 samosas = 20 kg
  Oil (deep fry):   500ml per 50    -> 500 samosas = 5 L
  Onion:            1 per 20        -> 500 samosas = 25 pcs
  Green chilli:     2 pcs per 20   -> 500 samosas = 50 pcs
  Ginger:          10g per 20      -> 500 samosas = 250 g
  Cumin seeds:      5g per 20      -> 500 samosas = 125 g
  Coriander powder: 5g per 20      -> 500 samosas = 125 g
  Garam masala:     2g per 20      -> 500 samosas = 50 g
  Salt:             3g per 20      -> 500 samosas = 75 g

BIRYANI (per serving ~300g cooked):
  Basmati rice: 80g raw/serving
  Meat/Paneer: 150g/serving
  Onion: 50g/serving
  Oil/Ghee: 20ml/serving

DAL (per serving ~200ml):
  Dal: 50g/serving
  Tomato: 30g/serving

SCALING RULES:
1. Multiply base quantities by (servings / base_servings)
2. Spices scale at 70% of linear for batches > 50 servings
3. Use kg/L for quantities above 500g/ml
4. Never round quantities below actual need
5. For 100+ people, show time in hours not minutes

═══════════════════════════════════════════════════
STEP 3 - RESPONSE FORMAT
═══════════════════════════════════════════════════

Reply ONLY with valid JSON (no markdown fences, no text outside JSON):
{
  "dish": "<proper dish name>",
  "servings": <integer>,
  "description": "<one appetizing sentence>",
  "prep_time": "<realistic prep time>",
  "cook_time": "<realistic cook time>",
  "ingredients": [
    {
      "name": "<ingredient in English>",
      "quantity": "<numeric string only e.g. '75'>",
      "unit": "<kg / g / L / ml / pcs / tsp / tbsp / bunch / pack>",
      "category": "<Pulses / Spices / Dairy / Flour / Oil / Vegetables / Fruits / Pantry / Other>"
    }
  ],
  "recipe_steps": [
    "Step 1: ...",
    "Step 2: ..."
  ]
}

RULES:
- quantity must be a number string only ("75" not "75 kg" -- unit field is separate)
- All names in English
- At least 4 recipe_steps
- ingredients must never be empty
- Do NOT include any text outside the JSON object
"""


def _get_openai():
    if OpenAI is None or not settings.OPENAI_API_KEY:
        return None
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# Keywords that clearly indicate off-topic (non-food) input
_OFFTRACK_KEYWORDS = [
    "function", "algorithm", "coding", "python", "javascript", "code", "program",
    "blockchain", "crypto", "nft", "equation", "solve", "integral", "derivative",
    "politics", "election", "president", "war", "sport", "cricket", "football",
    "movie", "actor", "news", "history", "geography", "capital of",
]

_ERROR_MSG = (
    "I can only help with food and grocery planning 🍽️. "
    "Please enter a dish name like 'Paneer Butter Masala for 4' or 'Samosa for 500 people'."
)


def _is_garbage(text: str) -> bool:
    """Return True if the input is purely symbols/garbage or off-topic."""
    stripped = text.strip()
    # Pure symbols / no alphabetical chars
    if not re.search(r"[a-zA-Z]", stripped):
        return True
    # Very short random strings (< 3 real letters)
    alpha_chars = re.findall(r"[a-zA-Z]", stripped)
    if len(alpha_chars) < 3:
        return True
    # Off-topic keyword detection
    lowered = stripped.lower()
    for kw in _OFFTRACK_KEYWORDS:
        if kw in lowered:
            return True
    return False


def _fallback_parse_dish_request(user_input: str) -> dict:
    query = user_input.strip()
    if _is_garbage(query):
        return {"error": _ERROR_MSG}

    lowered = query.lower()
    servings = 2
    servings_match = re.search(r"\bfor\s+(\d+)\b", lowered)
    if servings_match:
        servings = int(servings_match.group(1))
    dish = re.split(r"\bfor\s+\d+\b", query, maxsplit=1, flags=re.IGNORECASE)[0].strip(" ,.-") or query
    recipe = _FALLBACK_RECIPES.get(dish.lower())
    if recipe:
        # Scale ingredients from their base (designed for 2-4 servings) to requested servings
        base_servings = 4
        scale = servings / base_servings
        scaled_ings = []
        for ing in recipe["ingredients"]:
            try:
                qty = float(ing["quantity"]) * scale
                # Use sensible precision
                qty = round(qty, 1) if qty < 10 else round(qty)
                scaled_ings.append({**ing, "quantity": str(qty)})
            except (ValueError, TypeError):
                scaled_ings.append(ing)
        return {
            "dish": dish.title(),
            "servings": servings,
            "description": recipe.get("description", ""),
            "prep_time": recipe.get("prep_time", ""),
            "cook_time": recipe.get("cook_time", ""),
            "ingredients": scaled_ings,
            "recipe_steps": recipe.get("recipe_steps", []),
        }
    return {
        "dish": dish.title(),
        "servings": servings,
        "description": f"A custom meal plan for {dish.title()}.",
        "prep_time": "15 mins",
        "cook_time": "30 mins",
        "ingredients": list(_GENERIC_COOKING_STAPLES),
        "recipe_steps": [
            "Prepare all vegetables and pantry staples.",
            "Heat oil in a pan and build the base masala.",
            "Add your main ingredients and cook until done.",
            "Adjust seasoning, garnish, and serve hot.",
        ],
    }


def parse_dish_request(user_input: str) -> dict:
    client = _get_openai()
    if client is None:
        return _fallback_parse_dish_request(user_input)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        raw_obj = json.loads(raw)
        if "error" in raw_obj:
            return raw_obj
        return raw_obj
    except Exception as exc:
        logger.warning("Falling back to local planner response: %s", exc)
        return _fallback_parse_dish_request(user_input)


def match_ingredients_to_products(ingredients: list) -> list:
    matched_items = []
    global _mongo_lookup_available

    for ingredient in ingredients:
        name = ingredient.get("name", "")
        quantity = ingredient.get("quantity", "")
        unit = ingredient.get("unit", "")
        category = ingredient.get("category", "Other")

        product = None
        if _mongo_lookup_available:
            try:
                product = mongo_client.search_product_by_name(name)
            except Exception as exc:
                _mongo_lookup_available = False
                logger.warning("Mongo lookup disabled for this run: %s", exc)

        if product:
            image = product.get("image_url", "")
            if not image and product.get("images"):
                image = product["images"][0]
            matched_items.append(
                {
                    "ingredient_name": name,
                    "needed_quantity": f"{quantity}{unit}",
                    "product_id": str(product["_id"]),
                    "product_name": product.get("name", name),
                    "product_price": product.get("price", product.get("base_price", 0)),
                    "product_unit": product.get("unit", unit),
                    "product_weight": product.get("weight", ""),
                    "product_image": image,
                    "product_category": product.get("category", category),
                    "discount": product.get("discount", 0),
                    "matched": True,
                }
            )
        else:
            matched_items.append(
                {
                    "ingredient_name": name,
                    "needed_quantity": f"{quantity}{unit}",
                    "product_id": None,
                    "product_name": name,
                    "product_price": 0,
                    "product_unit": unit,
                    "product_weight": "",
                    "product_image": "",
                    "product_category": category,
                    "discount": 0,
                    "matched": False,
                }
            )
    return matched_items


def generate_plan(user_query: str) -> dict:
    parsed = parse_dish_request(user_query)
    if "error" in parsed:
        return parsed

    ingredients = parsed.get("ingredients", [])
    if not ingredients:
        return {"error": "Could not identify ingredients for this dish."}

    matched_items = match_ingredients_to_products(ingredients)
    total_price = sum(
        item["product_price"] * (1 - item["discount"] / 100)
        for item in matched_items
        if item["matched"]
    )
    return {
        "dish": parsed.get("dish", "Unknown Dish"),
        "servings": parsed.get("servings", 1),
        "description": parsed.get("description", ""),
        "prep_time": parsed.get("prep_time", ""),
        "cook_time": parsed.get("cook_time", ""),
        "recipe_steps": parsed.get("recipe_steps", []),
        "items": matched_items,
        "total_price": round(total_price, 2),
        "matched_count": sum(1 for item in matched_items if item["matched"]),
        "total_count": len(matched_items),
    }


# ─────────────────────────────────────────────────────────────────────────────
# PANTRY → RECIPE  (new "What can I cook?" feature)
# ─────────────────────────────────────────────────────────────────────────────

_PANTRY_SYSTEM_PROMPT = """You are BasketIQ's Pantry Chef AI. The user will give you a list of ingredients they have at home.

STEP 1 - VALIDATE:
- If the list contains no real food items (only symbols, numbers, junk text, or clearly non-food items), return:
  {"error": "Please enter real ingredient names like 'potato, onion, tomato'."}
- If the list has at least 2 real food ingredients, proceed.

STEP 2 - SUGGEST DISHES:
Suggest exactly 3 dishes that can be made using PRIMARILY the given ingredients.
It is OK to assume the user has basic pantry staples (salt, oil, water) even if not listed.
Prefer realistic, everyday Indian or common dishes.

STEP 3 - RESPONSE FORMAT (reply ONLY with valid JSON, no markdown):
{
  "suggestions": [
    {
      "dish": "<dish name>",
      "description": "<two sentences: what it is + why it's great with these ingredients>",
      "match_score": <integer 60-100>,
      "missing_ingredients": ["<ingredient not in pantry but needed>"],
      "prep_time": "<e.g. 15 mins>",
      "cook_time": "<e.g. 25 mins>",
      "serves": "<e.g. 2-3 people>",
      "youtube_query": "<a short YouTube search query to find a recipe video, e.g. 'how to make dal tadka at home'>",
      "recipe_steps": [
        "Step 1: <detailed instruction with exact quantity, temperature, or timing — e.g. Heat 2 tbsp oil in a heavy-bottomed pan over medium-high heat (around 180C). Add 1 tsp cumin seeds and let them splutter for 30 seconds until aromatic.>",
        "Step 2: ...",
        "... at least 6 steps total, each with enough detail that a beginner can follow without guessing"
      ],
      "pro_tips": ["<one line expert tip>", "<another tip — e.g. resting time, substitutions, texture advice>"],
      "ingredients_used": ["<pantry item used>"]
    }
  ]
}

RULES:
- Exactly 3 suggestions, ordered by match_score descending
- missing_ingredients should only list items the user truly does NOT have
- recipe_steps: minimum 6 steps, each step must be at least 20 words with specific quantities and timings
- pro_tips: exactly 2 tips per dish
- youtube_query: keep it simple and searchable, e.g. 'aloo samosa recipe hindi' or 'easy dal tadka recipe'
- Do NOT wrap in markdown or add any text outside the JSON
"""

_OFFLINE_RECIPE_DB = [
    {
        "dish": "Aloo Sabzi (Spiced Potatoes)",
        "description": "A comforting dry potato curry with warming spices — comes together in under 30 minutes.",
        "primary_ingredients": ["potato", "onion", "tomato"],
        "prep_time": "10 mins", "cook_time": "20 mins", "serves": "2-3 people",
        "youtube_query": "aloo sabzi recipe easy indian style",
        "recipe_steps": [
            "Step 1: Wash, peel and cube 3 medium potatoes. Chop 1 onion and 1 tomato.",
            "Step 2: Heat 2 tbsp oil in a pan. Add 1 tsp mustard and cumin seeds.",
            "Step 3: Add chopped onions and saute until translucent.",
            "Step 4: Add tomatoes, 1/2 tsp turmeric, 1 tsp coriander powder, 1/2 tsp chilli powder, and salt.",
            "Step 5: Cook until tomatoes are mushy, then add potatoes.",
            "Step 6: Cover and cook on low heat for 12-15 minutes until potatoes are soft.",
            "Step 7: Garnish with fresh coriander."
        ],
        "pro_tips": ["Parboil potatoes for faster cooking.", "Add amchur (dry mango powder) for tanginess."]
    },
    {
        "dish": "Masala Omelette",
        "description": "A fluffy, spice-packed omelette loaded with fresh vegetables.",
        "primary_ingredients": ["egg", "onion", "green chilli", "tomato"],
        "prep_time": "5 mins", "cook_time": "10 mins", "serves": "1-2 people",
        "youtube_query": "masala omelette recipe indian style",
        "recipe_steps": [
            "Step 1: Beat 3 eggs in a bowl with salt, pepper, and a pinch of turmeric.",
            "Step 2: Finely chop 1 onion, 1 small tomato, and 1-2 green chillies.",
            "Step 3: Add the chopped vegetables to the beaten eggs.",
            "Step 4: Heat a pan with 1 tbsp oil or butter over medium heat.",
            "Step 5: Pour the egg mixture and let it cook for 2 minutes until the bottom sets.",
            "Step 6: Fold in half and cook for another minute. Serve hot."
        ],
        "pro_tips": ["Beat the eggs well to incorporate air for a fluffier omelette.", "Cook on medium heat to avoid burning."]
    },
    {
        "dish": "Dal Tadka",
        "description": "Golden, smoky lentils tempered with ghee and whole spices.",
        "primary_ingredients": ["toor dal", "onion", "tomato", "garlic", "cumin"],
        "prep_time": "10 mins", "cook_time": "30 mins", "serves": "3-4 people",
        "youtube_query": "dal tadka recipe dhaba style",
        "recipe_steps": [
            "Step 1: Wash and soak 1 cup toor dal for 20 minutes.",
            "Step 2: Pressure cook dal with 3 cups water, turmeric, and salt for 3-4 whistles.",
            "Step 3: Heat 2 tbsp ghee in a pan. Add cumin seeds and let them splutter.",
            "Step 4: Add chopped garlic, green chillies, and onion. Sauté until golden.",
            "Step 5: Add chopped tomatoes, red chilli powder, and coriander powder. Cook until mushy.",
            "Step 6: Pour the cooked dal into the pan, mix well, and simmer for 5 minutes."
        ],
        "pro_tips": ["For authentic flavor, use a charcoal smoke (dhungar) method at the end.", "Don't skimp on the garlic in the tempering."]
    },
    {
        "dish": "Kanda Poha",
        "description": "Flattened rice cooked with onions, peanuts, and mild spices.",
        "primary_ingredients": ["poha", "onion", "peanut", "green chilli", "curry leaves"],
        "prep_time": "10 mins", "cook_time": "10 mins", "serves": "2 people",
        "youtube_query": "kanda poha recipe authentic maharashtrian",
        "recipe_steps": [
            "Step 1: Rinse 2 cups thick poha gently in a colander and drain completely. Leave aside to soften.",
            "Step 2: Heat 2 tbsp oil in a pan. Fry 1/4 cup peanuts until crunchy, remove and set aside.",
            "Step 3: In the same oil, add 1 tsp mustard seeds, green chillies, and curry leaves.",
            "Step 4: Add 1 finely chopped onion and sauté until pink.",
            "Step 5: Add 1/2 tsp turmeric powder and salt. Mix well.",
            "Step 6: Add the softened poha and mix gently. Cover and cook on low heat for 3-4 minutes.",
            "Step 7: Garnish with fried peanuts, coriander, and a squeeze of lemon."
        ],
        "pro_tips": ["Do not soak the poha in water, just rinse it.", "A pinch of sugar balances the flavors beautifully."]
    },
    {
        "dish": "Jeera Aloo",
        "description": "Simple and flavorful cumin-spiced potatoes.",
        "primary_ingredients": ["potato", "cumin", "green chilli"],
        "prep_time": "5 mins", "cook_time": "15 mins", "serves": "2 people",
        "youtube_query": "jeera aloo recipe quick",
        "recipe_steps": [
            "Step 1: Boil, peel, and dice 3 medium potatoes.",
            "Step 2: Heat 2 tbsp oil in a pan. Add a generous 1.5 tsp of cumin seeds and let them crackle.",
            "Step 3: Add slit green chillies and a pinch of hing (asafoetida).",
            "Step 4: Add the boiled potatoes, turmeric, red chilli powder, coriander powder, and salt.",
            "Step 5: Toss well to coat the potatoes in spices.",
            "Step 6: Cook on medium-low for 5-7 minutes, stirring occasionally until slightly crispy.",
            "Step 7: Garnish with fresh coriander."
        ],
        "pro_tips": ["Using boiled potatoes that have completely cooled down prevents them from turning mushy.", "Crushing a few cumin seeds before adding enhances the aroma."]
    },
    {
        "dish": "Paneer Bhurji",
        "description": "Scrambled Indian cottage cheese cooked with onions, tomatoes, and spices.",
        "primary_ingredients": ["paneer", "onion", "tomato", "green chilli"],
        "prep_time": "10 mins", "cook_time": "15 mins", "serves": "2-3 people",
        "youtube_query": "paneer bhurji recipe dhaba style",
        "recipe_steps": [
            "Step 1: Crumble 200g of paneer and set aside.",
            "Step 2: Heat 2 tbsp oil or butter in a pan. Add cumin seeds.",
            "Step 3: Add finely chopped onions and green chillies. Sauté until translucent.",
            "Step 4: Add ginger-garlic paste and cook for a minute.",
            "Step 5: Add chopped tomatoes, turmeric, chilli powder, coriander powder, and salt. Cook until tomatoes soften.",
            "Step 6: Add the crumbled paneer and mix well. Cook for 2-3 minutes.",
            "Step 7: Finish with garam masala and fresh coriander."
        ],
        "pro_tips": ["Use fresh, homemade paneer for the best texture.", "A splash of milk at the end keeps the bhurji moist."]
    },
    {
        "dish": "Bhindi Masala",
        "description": "Stir-fried okra with onions and tangy spices.",
        "primary_ingredients": ["bhindi", "onion", "tomato"],
        "prep_time": "10 mins", "cook_time": "20 mins", "serves": "2-3 people",
        "youtube_query": "bhindi masala dry recipe",
        "recipe_steps": [
            "Step 1: Wash and completely dry 250g bhindi (okra). Cut into 1-inch pieces.",
            "Step 2: Heat 2 tbsp oil in a pan. Fry the bhindi until lightly browned and not slimy. Remove and set aside.",
            "Step 3: In the same pan, add cumin seeds, chopped onions, and sauté until golden.",
            "Step 4: Add ginger-garlic paste, then chopped tomatoes and dry spices.",
            "Step 5: Cook until the oil separates from the masala.",
            "Step 6: Add the fried bhindi and salt. Mix gently.",
            "Step 7: Cover and cook on low heat for 5 minutes. Sprinkle amchur powder before serving."
        ],
        "pro_tips": ["Ensure the bhindi is completely dry before chopping to prevent sliminess.", "Adding a few drops of lemon juice while frying also reduces slime."]
    },
    {
        "dish": "Tomato Chutney",
        "description": "A tangy, spicy condiment made with tomatoes, onions, and garlic.",
        "primary_ingredients": ["tomato", "onion", "garlic", "dry red chilli", "mustard seeds"],
        "prep_time": "5 mins", "cook_time": "15 mins", "serves": "4-6 people",
        "youtube_query": "spicy tomato onion chutney for dosa",
        "recipe_steps": [
            "Step 1: Roughly chop 3 large tomatoes and 1 large onion. Peel 4-5 garlic cloves.",
            "Step 2: Heat 1 tbsp oil in a pan. Add 1 tsp chana dal, 1 tsp urad dal, and 3-4 dry red chillies. Roast until dals are golden.",
            "Step 3: Add garlic and onions. Sauté until onions are translucent.",
            "Step 4: Add tomatoes and salt. Cook until tomatoes are completely mushy.",
            "Step 5: Let the mixture cool, then blend it into a smooth paste.",
            "Step 6: For tempering: Heat 1 tsp oil, add mustard seeds and curry leaves. Let them splutter.",
            "Step 7: Pour tempering over the blended chutney."
        ],
        "pro_tips": ["Sautéing the tomatoes well removes the raw smell and extends shelf life.", "Adjust dry red chillies according to your spice preference."]
    },
    {
        "dish": "Onion Pakoda",
        "description": "Crispy, deep-fried onion fritters.",
        "primary_ingredients": ["onion", "besan", "green chilli", "carom seeds"],
        "prep_time": "10 mins", "cook_time": "15 mins", "serves": "3-4 people",
        "youtube_query": "crispy onion pakoda recipe",
        "recipe_steps": [
            "Step 1: Thinly slice 2 large onions. Mix them with salt and let them sit for 5 minutes to release moisture.",
            "Step 2: Add chopped green chillies, fresh coriander, 1/2 tsp carom seeds (ajwain), and a pinch of turmeric.",
            "Step 3: Add 1 cup besan (gram flour) gradually. Mix well. Add a splash of water if needed to form a thick batter.",
            "Step 4: Heat oil for deep frying in a kadai.",
            "Step 5: Drop small, irregular spoonfuls of the batter into the hot oil.",
            "Step 6: Fry on medium heat until golden and crispy.",
            "Step 7: Drain on paper towels and serve hot with chutney or tea."
        ],
        "pro_tips": ["Don't add too much water; the batter should just coat the onions.", "Adding 1 tbsp of rice flour makes the pakodas extra crispy."]
    },
    {
        "dish": "Khichdi",
        "description": "A wholesome, comforting one-pot meal of rice and lentils.",
        "primary_ingredients": ["rice", "moong dal", "ghee", "cumin"],
        "prep_time": "5 mins", "cook_time": "20 mins", "serves": "2 people",
        "youtube_query": "moong dal khichdi recipe pressure cooker",
        "recipe_steps": [
            "Step 1: Wash 1/2 cup rice and 1/2 cup yellow moong dal together. Soak for 15 minutes.",
            "Step 2: Heat 1 tbsp ghee in a pressure cooker. Add 1 tsp cumin seeds and a pinch of hing.",
            "Step 3: Drain the soaked rice and dal, and add them to the cooker.",
            "Step 4: Sauté for a minute. Add 1/4 tsp turmeric powder and salt to taste.",
            "Step 5: Add 3.5 to 4 cups of water (depending on desired consistency).",
            "Step 6: Close the lid and pressure cook for 3-4 whistles on medium heat.",
            "Step 7: Let the pressure release naturally. Top with more ghee before serving."
        ],
        "pro_tips": ["For a vegetable khichdi, add chopped peas, carrots, and potatoes before adding water.", "The ratio of water determines if it's runny or thick; adjust as you like."]
    }
]

def generate_from_pantry(available_ingredients: list[str]) -> dict:
    if not available_ingredients:
        return {"error": "Please provide at least one ingredient."}

    cleaned = [i.strip() for i in available_ingredients if i.strip()]
    if len(cleaned) < 2:
        return {"error": "Please add at least 2 ingredients to get dish suggestions."}

    client = _get_openai()
    if client is not None:
        try:
            ingredient_text = ", ".join(cleaned)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": _PANTRY_SYSTEM_PROMPT},
                    {"role": "user", "content": f"I have these ingredients: {ingredient_text}"},
                ],
                temperature=0.5,
                max_tokens=2500,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-z]*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
                raw = raw.strip()
            parsed = json.loads(raw)
            if "error" in parsed:
                return parsed
            parsed["pantry"] = cleaned
            return parsed
        except Exception as exc:
            logger.warning("Pantry AI fallback triggered: %s", exc)

    # ── FALLBACK ENGINE (Smart Match) ────────────────────────────────────────────
    user_lower = [c.lower() for c in cleaned]
    scored_recipes = []

    for recipe in _OFFLINE_RECIPE_DB:
        primary = recipe["primary_ingredients"]
        used_primary = []
        for p in primary:
            if any(p in u or u in p for u in user_lower):
                used_primary.append(p)
                
        match_ratio = len(used_primary) / len(primary) if primary else 0
        score = match_ratio * 100
        
        if score > 0:
            score += len(used_primary) * 2
            
        score = min(100, int(score))
        
        missing = [p.title() for p in primary if p not in used_primary]
        used_display = [p.title() for p in used_primary]
        
        for u in cleaned:
            if u.title() not in used_display and len(used_display) < 5:
                used_display.append(u.title())

        if score > 0:
            scored_recipes.append({
                "dish": recipe["dish"],
                "description": recipe["description"],
                "match_score": score,
                "missing_ingredients": missing,
                "prep_time": recipe["prep_time"],
                "cook_time": recipe["cook_time"],
                "serves": recipe["serves"],
                "youtube_query": recipe["youtube_query"],
                "recipe_steps": recipe["recipe_steps"],
                "pro_tips": recipe["pro_tips"],
                "ingredients_used": used_display,
                "_raw_score": score 
            })

    scored_recipes.sort(key=lambda x: x["_raw_score"], reverse=True)
    
    if not scored_recipes:
        for i, recipe in enumerate(_OFFLINE_RECIPE_DB[:3]):
            scored_recipes.append({
                "dish": recipe["dish"],
                "description": recipe["description"],
                "match_score": 20 - i, 
                "missing_ingredients": [p.title() for p in recipe["primary_ingredients"]],
                "prep_time": recipe["prep_time"],
                "cook_time": recipe["cook_time"],
                "serves": recipe["serves"],
                "youtube_query": recipe["youtube_query"],
                "recipe_steps": recipe["recipe_steps"],
                "pro_tips": recipe["pro_tips"],
                "ingredients_used": cleaned[:3],
            })
    else:
        for sr in scored_recipes:
            del sr["_raw_score"]

    return {"suggestions": scored_recipes[:3], "pantry": cleaned}
