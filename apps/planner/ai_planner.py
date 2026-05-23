"""AI-powered grocery planning using OpenAI and BasketIQ product search."""

from __future__ import annotations

import json
import logging
import math
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

_SERVING_LIMIT = 5000

_FOOD_SYNONYMS = {
    "aloo": "potato",
    "atta": "wheat flour",
    "besan": "besan",
    "bataka": "potato",
    "bhenda": "bhindi",
    "bhendi": "bhindi",
    "bhindi": "bhindi",
    "bhinda": "bhindi",
    "chawal": "rice",
    "chana": "chana dal",
    "chole": "kabuli chana",
    "dahi": "curd",
    "dal": "dal",
    "dhania": "coriander",
    "dudhi": "bottle gourd",
    "dudh": "milk",
    "dungli": "onion",
    "egg": "egg",
    "eggs": "egg",
    "gajar": "carrot",
    "ginger garlic": "ginger garlic",
    "gobi": "cauliflower",
    "gol": "jaggery",
    "kakdi": "cucumber",
    "karela": "bitter gourd",
    "jeera": "cumin",
    "kela": "banana",
    "kobi": "cabbage",
    "kothmir": "coriander",
    "limbu": "lemon",
    "mag": "moong dal",
    "maida": "all purpose flour",
    "makai": "corn",
    "marcha": "green chilli",
    "marchu": "red chilli powder",
    "matar": "peas",
    "methi": "fenugreek",
    "mirch": "green chilli",
    "palak": "spinach",
    "paneer": "paneer",
    "pyaaz": "onion",
    "ringan": "brinjal",
    "rice": "rice",
    "rotli": "roti",
    "sakar": "sugar",
    "shaak": "sabzi",
    "shak": "sabzi",
    "sing": "peanut",
    "tamatar": "tomato",
    "tameta": "tomato",
    "tuver": "toor dal",
    "turiya": "ridge gourd",
    "turia": "ridge gourd",
    "vatana": "peas",
    "valor": "hyacinth beans",
}

_FOOD_WORDS = {
    "ajwain", "apple", "atta", "banana", "basmati", "bataka", "besan", "bhatura", "bhenda",
    "bhendi", "bhinda", "biryani",
    "burger", "butter", "capsicum", "carrot", "chana", "cheese", "chicken", "chilli",
    "chole", "coriander", "cream", "cumin", "curd", "curry", "dal", "daal", "dosa",
    "egg", "flour", "food", "gajar", "garam", "garlic", "ghee", "ginger", "halva",
    "halwa", "halvo", "halwo", "idli", "jaggery",
    "khichdi", "lemon", "maida", "masala", "milk", "moong", "noodles", "oil", "onion",
    "pakoda", "pakwaan", "paneer", "pani", "pasta", "peas", "pizza", "poha", "potato",
    "puri", "rajma", "recipe", "rice", "roti", "sabzi", "shaak", "shak", "salt",
    "samosa", "semolina", "sooji", "soup", "spinach", "sugar", "tamatar", "tamarind", "tomato", "toor", "turmeric",
    "urad", "vada", "vegetable", "wheat",
    "yogurt",
    *_FOOD_SYNONYMS.keys(),
}

_DISH_ALIASES = {
    "samosa": "samosa",
    "samosas": "samosa",
    "biryani": "biryani",
    "veg biryani": "biryani",
    "vegetable biryani": "biryani",
    "paneer butter masala": "paneer butter masala",
    "butter paneer": "paneer butter masala",
    "bhenda nu shaak": "bhindi shaak",
    "bhenda nu shak": "bhindi shaak",
    "bhendi masala": "bhindi shaak",
    "bhendi nu shaak": "bhindi shaak",
    "bhendi nu shak": "bhindi shaak",
    "bhinda nu shaak": "bhindi shaak",
    "bhinda nu shak": "bhindi shaak",
    "bhindi masala": "bhindi shaak",
    "bhindi nu shaak": "bhindi shaak",
    "bhindi nu shak": "bhindi shaak",
    "carrot halwa": "gajar halwa",
    "gajar ka halwa": "gajar halwa",
    "gajar halva": "gajar halwa",
    "gajar halwa": "gajar halwa",
    "gajar halvo": "gajar halwa",
    "gajar halwo": "gajar halwa",
    "gajar no halva": "gajar halwa",
    "gajar no halwa": "gajar halwa",
    "gajar no halvo": "gajar halwa",
    "gajar no halwo": "gajar halwa",
    "dal tadka": "dal tadka",
    "daal tadka": "dal tadka",
    "dal vada": "dal vada",
    "daal vada": "dal vada",
    "dal wada": "dal vada",
    "daal wada": "dal vada",
    "dal vda": "dal vada",
    "daal vda": "dal vada",
    "dal": "dal tadka",
    "daal": "dal tadka",
    "chole": "chole",
    "chole bhature": "chole",
    "pasta": "pasta aglio e olio",
    "pasta aglio e olio": "pasta aglio e olio",
    "khichdi": "khichdi",
    "pani puri": "pani puri",
    "pani poori": "pani puri",
    "golgappa": "pani puri",
    "gol gappa": "pani puri",
    "puchka": "pani puri",
    "daal pakwaan": "daal pakwaan",
    "dal pakwan": "daal pakwaan",
    "aloo sabzi": "aloo sabzi",
    "potato sabzi": "aloo sabzi",
}

_RECIPE_FORMULAS = {
    "samosa": {
        "dish": "Samosa",
        "description": "Crisp pastry pockets filled with spiced potato, scaled for the exact batch size.",
        "prep_base": 35,
        "cook_base": 40,
        "ingredients": [
            ("Potato", 150, "g", "Vegetables", "main"),
            ("All Purpose Flour (Maida)", 40, "g", "Flour", "main"),
            ("Vegetable Oil", 10, "ml", "Oil", "main"),
            ("Onion", 0.05, "pcs", "Vegetables", "main"),
            ("Green Chilli", 0.1, "pcs", "Vegetables", "main"),
            ("Ginger", 0.5, "g", "Vegetables", "main"),
            ("Cumin Seeds (Jeera)", 0.25, "g", "Spices", "spice"),
            ("Coriander Powder (Dhania)", 0.25, "g", "Spices", "spice"),
            ("Garam Masala", 0.1, "g", "Spices", "spice"),
            ("Salt", 0.15, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Boil, peel, and roughly mash the potatoes while they are still warm.",
            "Step 2: Knead maida with salt, a little oil, and water into a firm dough; rest it for 30 minutes.",
            "Step 3: Temper cumin in oil, saute onion, green chilli, and ginger, then mix in potatoes and dry spices.",
            "Step 4: Roll dough portions, fill with potato masala, seal into triangles, and keep covered.",
            "Step 5: Fry on medium heat until crisp and golden, working in batches for large quantities.",
        ],
    },
    "biryani": {
        "dish": "Biryani",
        "description": "Layered rice with vegetables, paneer, spices, and aromatics, scaled for your guest count.",
        "prep_base": 35,
        "cook_base": 60,
        "ingredients": [
            ("Basmati Rice", 80, "g", "Grains", "main"),
            ("Paneer", 120, "g", "Dairy", "main"),
            ("Onion", 50, "g", "Vegetables", "main"),
            ("Tomato", 35, "g", "Vegetables", "main"),
            ("Curd (Yogurt)", 35, "g", "Dairy", "main"),
            ("Vegetable Oil", 12, "ml", "Oil", "main"),
            ("Garam Masala", 1.2, "g", "Spices", "spice"),
            ("Turmeric Powder (Haldi)", 0.4, "g", "Spices", "spice"),
            ("Red Chilli Powder", 0.8, "g", "Spices", "spice"),
            ("Salt", 3, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Wash and soak basmati rice for 30 minutes, then parboil until about 70 percent cooked.",
            "Step 2: Fry sliced onions until golden and reserve some for garnish.",
            "Step 3: Cook tomato, curd, paneer, and spices into a thick biryani masala.",
            "Step 4: Layer rice and masala in a heavy pot, seal, and cook on low heat until fragrant.",
            "Step 5: Rest before serving so the rice grains stay separate and the masala settles.",
        ],
    },
    "paneer butter masala": {
        "dish": "Paneer Butter Masala",
        "description": "A creamy tomato-cashew style paneer curry with balanced spice and richness.",
        "prep_base": 20,
        "cook_base": 35,
        "ingredients": [
            ("Paneer", 100, "g", "Dairy", "main"),
            ("Tomato", 90, "g", "Vegetables", "main"),
            ("Onion", 35, "g", "Vegetables", "main"),
            ("Butter", 12, "g", "Dairy", "main"),
            ("Cream", 18, "ml", "Dairy", "main"),
            ("Ginger", 2, "g", "Vegetables", "main"),
            ("Garlic", 2, "g", "Vegetables", "main"),
            ("Garam Masala", 0.8, "g", "Spices", "spice"),
            ("Red Chilli Powder", 0.6, "g", "Spices", "spice"),
            ("Salt", 2.5, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Saute onion, tomato, ginger, and garlic until soft, then blend into a smooth sauce.",
            "Step 2: Simmer the sauce with butter and spices until the oil starts to separate.",
            "Step 3: Add paneer cubes and cook gently so they stay soft.",
            "Step 4: Finish with cream and garam masala, adjusting salt before serving.",
        ],
    },
    "dal tadka": {
        "dish": "Dal Tadka",
        "description": "Comforting lentils finished with a hot aromatic tempering.",
        "prep_base": 15,
        "cook_base": 35,
        "ingredients": [
            ("Toor Dal", 50, "g", "Pulses", "main"),
            ("Tomato", 30, "g", "Vegetables", "main"),
            ("Onion", 25, "g", "Vegetables", "main"),
            ("Garlic", 2, "g", "Vegetables", "main"),
            ("Ghee", 8, "ml", "Dairy", "main"),
            ("Cumin Seeds (Jeera)", 0.8, "g", "Spices", "spice"),
            ("Turmeric Powder (Haldi)", 0.4, "g", "Spices", "spice"),
            ("Red Chilli Powder", 0.5, "g", "Spices", "spice"),
            ("Salt", 2.5, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Wash dal thoroughly and pressure cook with turmeric and enough water until soft.",
            "Step 2: Cook onion, tomato, and garlic until the masala turns glossy.",
            "Step 3: Add cooked dal, simmer, and adjust thickness with hot water.",
            "Step 4: Finish with a cumin and chilli tadka in hot ghee.",
        ],
    },
    "chole": {
        "dish": "Chole",
        "description": "Spiced chickpeas cooked in a rich onion-tomato masala.",
        "prep_base": 25,
        "cook_base": 60,
        "ingredients": [
            ("Kabuli Chana", 70, "g", "Pulses", "main"),
            ("Onion", 45, "g", "Vegetables", "main"),
            ("Tomato", 55, "g", "Vegetables", "main"),
            ("Ginger", 2, "g", "Vegetables", "main"),
            ("Garlic", 2, "g", "Vegetables", "main"),
            ("Vegetable Oil", 10, "ml", "Oil", "main"),
            ("Garam Masala", 1, "g", "Spices", "spice"),
            ("Cumin Seeds (Jeera)", 0.8, "g", "Spices", "spice"),
            ("Red Chilli Powder", 0.8, "g", "Spices", "spice"),
            ("Salt", 2.5, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Soak chickpeas overnight, then pressure cook until tender.",
            "Step 2: Build a deep onion-tomato masala with ginger, garlic, and spices.",
            "Step 3: Simmer chickpeas in the masala until thick and glossy.",
            "Step 4: Rest briefly before serving so the gravy absorbs into the chickpeas.",
        ],
    },
    "pasta aglio e olio": {
        "dish": "Pasta Aglio e Olio",
        "description": "Simple pasta tossed with garlic, chilli, and oil.",
        "prep_base": 10,
        "cook_base": 20,
        "ingredients": [
            ("Sooji (Semolina)", 90, "g", "Flour", "main"),
            ("Garlic", 5, "g", "Vegetables", "main"),
            ("Vegetable Oil", 12, "ml", "Oil", "main"),
            ("Red Chilli Powder", 0.4, "g", "Spices", "spice"),
            ("Fresh Coriander Leaves", 3, "g", "Vegetables", "main"),
            ("Salt", 2, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Boil pasta in salted water until just tender, reserving some cooking water.",
            "Step 2: Warm oil gently with sliced garlic and chilli so the garlic turns pale golden.",
            "Step 3: Toss pasta with the garlic oil and a splash of cooking water until glossy.",
            "Step 4: Finish with herbs and serve immediately.",
        ],
    },
    "khichdi": {
        "dish": "Khichdi",
        "description": "Soft rice and lentils cooked together for a wholesome one-pot meal.",
        "prep_base": 10,
        "cook_base": 25,
        "ingredients": [
            ("Basmati Rice", 40, "g", "Grains", "main"),
            ("Moong Dal", 40, "g", "Pulses", "main"),
            ("Ghee", 8, "ml", "Dairy", "main"),
            ("Cumin Seeds (Jeera)", 0.8, "g", "Spices", "spice"),
            ("Turmeric Powder (Haldi)", 0.4, "g", "Spices", "spice"),
            ("Salt", 2.2, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Wash rice and moong dal together until the water runs mostly clear.",
            "Step 2: Temper cumin in ghee, then add rice, dal, turmeric, salt, and water.",
            "Step 3: Pressure cook until soft and mash lightly for a comforting texture.",
            "Step 4: Serve hot with extra ghee, curd, or pickle.",
        ],
    },
    "aloo sabzi": {
        "dish": "Aloo Sabzi",
        "description": "A simple spiced potato curry for everyday meals.",
        "prep_base": 15,
        "cook_base": 25,
        "ingredients": [
            ("Potato", 180, "g", "Vegetables", "main"),
            ("Onion", 35, "g", "Vegetables", "main"),
            ("Tomato", 40, "g", "Vegetables", "main"),
            ("Vegetable Oil", 8, "ml", "Oil", "main"),
            ("Cumin Seeds (Jeera)", 0.8, "g", "Spices", "spice"),
            ("Turmeric Powder (Haldi)", 0.4, "g", "Spices", "spice"),
            ("Red Chilli Powder", 0.5, "g", "Spices", "spice"),
            ("Salt", 2.5, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Peel and cube potatoes into even pieces so they cook at the same speed.",
            "Step 2: Temper cumin, then saute onion and tomato with spices.",
            "Step 3: Add potatoes, cover, and cook until tender.",
            "Step 4: Finish uncovered for a thicker masala coating.",
        ],
    },
    "bhindi shaak": {
        "dish": "Bhinda Nu Shaak",
        "description": "A Gujarati-style dry okra sabzi with onion, tomato, and everyday masala.",
        "prep_base": 15,
        "cook_base": 25,
        "ingredients": [
            ("Bhindi", 120, "g", "Vegetables", "main"),
            ("Onion", 30, "g", "Vegetables", "main"),
            ("Tomato", 30, "g", "Vegetables", "main"),
            ("Vegetable Oil", 8, "ml", "Oil", "main"),
            ("Cumin Seeds (Jeera)", 0.6, "g", "Spices", "spice"),
            ("Turmeric Powder (Haldi)", 0.3, "g", "Spices", "spice"),
            ("Red Chilli Powder", 0.5, "g", "Spices", "spice"),
            ("Coriander Powder (Dhania)", 0.8, "g", "Spices", "spice"),
            ("Dry Mango Powder (Amchur)", 0.5, "g", "Spices", "spice"),
            ("Salt", 2.2, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Wash bhindi and dry it completely before chopping, because moisture can make the shaak sticky.",
            "Step 2: Trim and cut the bhindi into small pieces, then chop onion and tomato for the masala base.",
            "Step 3: Heat oil, crackle cumin seeds, and saute onion until it turns light golden and sweet.",
            "Step 4: Add bhindi with turmeric, chilli powder, coriander powder, and salt, then cook uncovered until nearly tender.",
            "Step 5: Add tomato and amchur near the end, toss gently, and finish dry so the bhinda nu shaak stays crisp.",
        ],
    },
    "gajar halwa": {
        "dish": "Gajar No Halvo",
        "description": "A rich Gujarati-style carrot halwa slow-cooked with milk, ghee, sugar, and nuts.",
        "prep_base": 20,
        "cook_base": 50,
        "ingredients": [
            ("Carrot", 180, "g", "Vegetables", "main"),
            ("Full Cream Milk", 180, "ml", "Dairy", "main"),
            ("Sugar", 35, "g", "Pantry", "main"),
            ("Ghee", 12, "ml", "Dairy", "main"),
            ("Cashew", 8, "g", "Pantry", "main"),
            ("Almond", 8, "g", "Pantry", "main"),
            ("Cardamom Powder", 0.4, "g", "Spices", "spice"),
        ],
        "steps": [
            "Step 1: Wash, peel, and grate the carrots finely so they cook evenly and release sweetness into the milk.",
            "Step 2: Heat ghee in a heavy pan, add grated carrot, and saute for 5 minutes until the raw smell reduces.",
            "Step 3: Pour in full cream milk and simmer on medium-low heat, stirring often until the milk reduces deeply.",
            "Step 4: Add sugar and continue cooking until the halvo turns glossy and starts leaving the sides of the pan.",
            "Step 5: Mix in cardamom powder and fried cashew-almond pieces, then serve warm or chilled as preferred.",
        ],
    },
    "dal vada": {
        "dish": "Dal Vada",
        "description": "Crispy lentil fritters made with soaked chana dal, herbs, and warm spices.",
        "prep_base": 30,
        "cook_base": 35,
        "ingredients": [
            ("Chana Dal", 80, "g", "Pulses", "main"),
            ("Onion", 25, "g", "Vegetables", "main"),
            ("Ginger", 2, "g", "Vegetables", "main"),
            ("Garlic", 2, "g", "Vegetables", "main"),
            ("Green Chilli", 0.5, "pcs", "Vegetables", "main"),
            ("Fresh Coriander Leaves", 5, "g", "Vegetables", "main"),
            ("Cumin Seeds (Jeera)", 0.8, "g", "Spices", "spice"),
            ("Red Chilli Powder", 0.5, "g", "Spices", "spice"),
            ("Salt", 2.5, "g", "Pantry", "spice"),
            ("Vegetable Oil", 25, "ml", "Oil", "main"),
        ],
        "steps": [
            "Step 1: Wash chana dal well and soak it for at least 3 hours so it grinds easily.",
            "Step 2: Drain the dal completely, then grind most of it coarsely with ginger, garlic, and green chilli.",
            "Step 3: Mix in chopped onion, coriander, cumin, chilli powder, and salt; keep the batter thick and textured.",
            "Step 4: Shape small flattened vadas with wet hands so they fry evenly and become crisp at the edges.",
            "Step 5: Fry on medium heat until deep golden, turning once or twice, then drain and serve hot.",
        ],
    },
    "pani puri": {
        "dish": "Pani Puri",
        "description": "Crisp puris filled with spiced potato, chickpeas, and tangy mint-tamarind water.",
        "prep_base": 35,
        "cook_base": 20,
        "ingredients": [
            ("Puri", 6, "pcs", "Pantry", "main"),
            ("Potato", 80, "g", "Vegetables", "main"),
            ("Kabuli Chana", 30, "g", "Pulses", "main"),
            ("Tamarind", 8, "g", "Pantry", "main"),
            ("Fresh Coriander Leaves", 8, "g", "Vegetables", "main"),
            ("Mint Leaves", 8, "g", "Vegetables", "main"),
            ("Green Chilli", 0.4, "pcs", "Vegetables", "main"),
            ("Cumin Seeds (Jeera)", 0.6, "g", "Spices", "spice"),
            ("Chaat Masala", 1, "g", "Spices", "spice"),
            ("Salt", 2, "g", "Pantry", "spice"),
        ],
        "steps": [
            "Step 1: Boil potatoes until tender, peel them, and mash with salt, cumin, and chaat masala.",
            "Step 2: Cook soaked kabuli chana until soft, then mix it into the potato filling for body.",
            "Step 3: Blend coriander, mint, green chilli, tamarind, cumin, salt, and chilled water into tangy pani.",
            "Step 4: Strain and chill the pani, adjusting salt and sourness so it tastes bright and punchy.",
            "Step 5: Crack each puri gently, fill with potato-chana mixture, dip in pani, and serve immediately.",
        ],
    },
}

_RECIPE_FORMULAS["daal pakwaan"] = {
    "dish": "Daal Pakwaan",
    "description": _FALLBACK_RECIPES["daal pakwaan"]["description"],
    "prep_base": 30,
    "cook_base": 50,
    "ingredients": [
        ("Chana Dal", 80, "g", "Pulses", "main"),
        ("All Purpose Flour (Maida)", 90, "g", "Flour", "main"),
        ("Onion", 25, "g", "Vegetables", "main"),
        ("Tomato", 25, "g", "Vegetables", "main"),
        ("Green Chilli", 0.5, "pcs", "Vegetables", "main"),
        ("Fresh Coriander Leaves", 5, "g", "Vegetables", "main"),
        ("Cumin Seeds (Jeera)", 0.8, "g", "Spices", "spice"),
        ("Turmeric Powder (Haldi)", 0.5, "g", "Spices", "spice"),
        ("Salt", 2.5, "g", "Pantry", "spice"),
        ("Vegetable Oil", 20, "ml", "Oil", "main"),
    ],
    "steps": _FALLBACK_RECIPES["daal pakwaan"]["recipe_steps"],
}

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
{"error": "plz enter valied input"}

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
- description must be one appetizing sentence and mention catalog matching plus auto-adding missing essentials for testing
- use common grocery names to maximize catalog matches (e.g., "potato" not "aloo")
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
    "math", "mathematics", "algebra", "calculus",
    "politics", "election", "president", "war", "sport", "cricket", "football",
    "movie", "actor", "news", "history", "geography", "capital of",
]

_ERROR_MSG = "plz enter valied input"
_LOCAL_FIRST_DISHES = {"bhindi shaak", "dal vada", "gajar halwa", "pani puri"}


def _normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _has_food_signal(text: str) -> bool:
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if words & _FOOD_WORDS:
        return True
    return any(alias in text.lower() for alias in _DISH_ALIASES)


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
        if kw in lowered and not _has_food_signal(lowered):
            return True
    if not _has_food_signal(lowered):
        return True
    return False


def _extract_servings(query: str) -> int:
    lowered = query.lower()
    patterns = [
        r"\bfor\s+(\d{1,5})\s*(?:people|peoples|persons|guests|servings|serves|pax|plates|samosas?)?\b",
        r"\bserves?\s+(\d{1,5})\b",
        r"\bservings?\s*[:=]?\s*(\d{1,5})\b",
        r"\b(?:party|wedding|event|bulk|batch|order)\s+(?:of|for)?\s*(\d{1,5})\b",
        r"\b(\d{1,5})\s*(?:people|peoples|persons|guests|servings|pax|plates|samosas?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return max(1, min(_SERVING_LIMIT, int(match.group(1))))
    return 2


def _extract_dish_key(query: str) -> str | None:
    lowered = _normalise_text(query)
    for alias in sorted(_DISH_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            return _DISH_ALIASES[alias]
    return None


def _clean_dish_name(query: str) -> str:
    cleaned = re.sub(
        r"\b(for|serves?|servings?|people|persons|guests|pax|plates|bulk|batch|order|party|wedding|event|of)\b",
        " ",
        query,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\d+", " ", cleaned)
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() if cleaned else "Custom Meal"


def _format_quantity(quantity: float, unit: str, group: str, servings: int) -> tuple[str, str]:
    if group == "spice" and servings > 50:
        quantity *= 0.7

    if unit == "g" and quantity >= 500:
        return f"{quantity / 1000:.2f}".rstrip("0").rstrip("."), "kg"
    if unit == "ml" and quantity >= 500:
        return f"{quantity / 1000:.2f}".rstrip("0").rstrip("."), "L"
    if unit == "pcs":
        return str(max(1, math.ceil(quantity))), "pcs"
    if unit in {"g", "ml"}:
        return str(max(1, math.ceil(quantity))), unit
    return f"{quantity:.1f}".rstrip("0").rstrip("."), unit


def _estimate_time(base_minutes: int, servings: int, kind: str) -> str:
    if servings <= 12:
        minutes = base_minutes
    elif servings <= 50:
        minutes = int(base_minutes * 1.5)
    elif servings <= 200:
        minutes = int(base_minutes * 2.4)
    else:
        minutes = int(base_minutes * 3.5)

    if servings >= 100 or minutes >= 90:
        hours = minutes / 60
        return f"{hours:.1f} hours".replace(".0", "")
    return f"{minutes} mins"


def _build_formula_recipe(dish_key: str, servings: int) -> dict:
    formula = _RECIPE_FORMULAS[dish_key]
    ingredients = []
    for name, per_serving, unit, category, group in formula["ingredients"]:
        quantity, out_unit = _format_quantity(per_serving * servings, unit, group, servings)
        ingredients.append(
            {
                "name": name,
                "quantity": quantity,
                "unit": out_unit,
                "category": category,
            }
        )
    return {
        "dish": formula["dish"],
        "servings": servings,
        "description": formula["description"],
        "prep_time": _estimate_time(formula["prep_base"], servings, "prep"),
        "cook_time": _estimate_time(formula["cook_base"], servings, "cook"),
        "ingredients": ingredients,
        "recipe_steps": formula["steps"],
    }


_REGIONAL_SUBJECT_DISPLAY = {
    "bitter gourd": "Karela",
    "bottle gourd": "Dudhi",
    "brinjal": "Ringan",
    "cabbage": "Kobi",
    "carrot": "Gajar",
    "corn": "Makai",
    "cucumber": "Kakdi",
    "fenugreek": "Methi",
    "hyacinth beans": "Valor",
    "moong dal": "Mag",
    "peas": "Vatana",
    "potato": "Bataka",
    "ridge gourd": "Turiya",
    "toor dal": "Tuver",
}

_INGREDIENT_DISPLAY = {
    "all purpose flour": "All Purpose Flour (Maida)",
    "bitter gourd": "Bitter Gourd",
    "bottle gourd": "Bottle Gourd",
    "green chilli": "Green Chilli",
    "hyacinth beans": "Hyacinth Beans",
    "moong dal": "Moong Dal",
    "red chilli powder": "Red Chilli Powder",
    "ridge gourd": "Ridge Gourd",
    "toor dal": "Toor Dal",
}

_INGREDIENT_CATEGORY = {
    "all purpose flour": "Flour",
    "almond": "Pantry",
    "bitter gourd": "Vegetables",
    "bottle gourd": "Vegetables",
    "brinjal": "Vegetables",
    "cabbage": "Vegetables",
    "carrot": "Vegetables",
    "cashew": "Pantry",
    "chana dal": "Pulses",
    "corn": "Vegetables",
    "cucumber": "Vegetables",
    "curd": "Dairy",
    "fenugreek": "Vegetables",
    "hyacinth beans": "Vegetables",
    "milk": "Dairy",
    "moong dal": "Pulses",
    "paneer": "Dairy",
    "peas": "Vegetables",
    "potato": "Vegetables",
    "ridge gourd": "Vegetables",
    "toor dal": "Pulses",
}

_REGIONAL_FILLER_WORDS = {
    "a", "an", "banavanu", "banavo", "banao", "banav", "cook", "dish", "for", "hu",
    "i", "ka", "ke", "ko", "make", "mara", "mate", "me", "need", "please", "pls",
    "prepare", "recipe", "the", "to", "want",
}


def _remove_serving_phrases(query: str) -> str:
    cleaned = _normalise_text(query)
    cleaned = re.sub(
        r"\bfor\s+\d{1,5}\s*(?:people|peoples|persons|guests|servings|serves|pax|plates)?\b",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"\bserves?\s+\d{1,5}\b", " ", cleaned)
    cleaned = re.sub(r"\bservings?\s*[:=]?\s*\d{1,5}\b", " ", cleaned)
    cleaned = re.sub(r"\b\d{1,5}\s*(?:people|peoples|persons|guests|servings|pax|plates)\b", " ", cleaned)
    cleaned = re.sub(r"\b\d+\b", " ", cleaned)
    cleaned = re.sub(r"[^a-z\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _canonical_food_subject(subject: str) -> str | None:
    cleaned = _normalise_text(subject)
    cleaned = re.sub(r"[^a-z\s]", " ", cleaned)
    words = [word for word in cleaned.split() if word not in _REGIONAL_FILLER_WORDS]
    cleaned = " ".join(words)
    if not cleaned:
        return None

    for source, target in sorted(_FOOD_SYNONYMS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(source)}\b", cleaned):
            return target
    if cleaned in _INGREDIENT_CATEGORY:
        return cleaned
    if cleaned in _FOOD_WORDS:
        return cleaned
    return None


def _regional_subject_name(canonical: str) -> str:
    return _REGIONAL_SUBJECT_DISPLAY.get(canonical, canonical.title())


def _ingredient_name(canonical: str) -> str:
    return _INGREDIENT_DISPLAY.get(canonical, canonical.title())


def _ingredient_category(canonical: str) -> str:
    return _INGREDIENT_CATEGORY.get(canonical, "Vegetables")


def _scale_recipe_rows(rows: list[tuple[str, float, str, str, str]], servings: int) -> list[dict]:
    ingredients = []
    for name, per_serving, unit, category, group in rows:
        quantity, out_unit = _format_quantity(per_serving * servings, unit, group, servings)
        ingredients.append(
            {
                "name": name,
                "quantity": quantity,
                "unit": out_unit,
                "category": category,
            }
        )
    return ingredients


def _build_gujarati_halwa_recipe(canonical: str, servings: int) -> dict:
    subject = _regional_subject_name(canonical)
    ingredient = _ingredient_name(canonical)
    category = _ingredient_category(canonical)
    main_quantity = 220 if canonical == "bottle gourd" else 180
    rows = [
        (ingredient, main_quantity, "g", category, "main"),
        ("Full Cream Milk", 180, "ml", "Dairy", "main"),
        ("Sugar", 35, "g", "Pantry", "main"),
        ("Ghee", 12, "ml", "Dairy", "main"),
        ("Cashew", 8, "g", "Pantry", "main"),
        ("Almond", 8, "g", "Pantry", "main"),
        ("Cardamom Powder", 0.4, "g", "Spices", "spice"),
    ]
    subject_lower = subject.lower()
    return {
        "dish": f"{subject} No Halvo",
        "servings": servings,
        "description": f"A Gujarati-style {subject_lower} halvo slow-cooked with milk, ghee, sugar, nuts, and cardamom.",
        "prep_time": _estimate_time(20, servings, "prep"),
        "cook_time": _estimate_time(50, servings, "cook"),
        "ingredients": _scale_recipe_rows(rows, servings),
        "recipe_steps": [
            f"Step 1: Wash, peel, and grate the {ingredient.lower()} finely so it cooks evenly and blends into the milk.",
            f"Step 2: Heat ghee in a heavy pan, add the grated {ingredient.lower()}, and saute until the raw smell reduces.",
            "Step 3: Pour in full cream milk and simmer on medium-low heat, stirring often until the milk reduces deeply.",
            "Step 4: Add sugar and continue cooking until the halvo turns glossy and starts leaving the sides of the pan.",
            "Step 5: Mix in cardamom powder and fried cashew-almond pieces, then serve warm or chilled as preferred.",
        ],
    }


def _build_gujarati_shaak_recipe(canonical: str, servings: int) -> dict:
    subject = _regional_subject_name(canonical)
    ingredient = _ingredient_name(canonical)
    category = _ingredient_category(canonical)
    rows = [
        (ingredient, 180, "g", category, "main"),
        ("Vegetable Oil", 8, "ml", "Oil", "main"),
        ("Mustard Seeds (Rai)", 0.6, "g", "Spices", "spice"),
        ("Cumin Seeds (Jeera)", 0.6, "g", "Spices", "spice"),
        ("Turmeric Powder (Haldi)", 0.3, "g", "Spices", "spice"),
        ("Red Chilli Powder", 0.5, "g", "Spices", "spice"),
        ("Coriander Powder (Dhania)", 0.8, "g", "Spices", "spice"),
        ("Salt", 2.2, "g", "Pantry", "spice"),
        ("Fresh Coriander Leaves", 3, "g", "Vegetables", "main"),
    ]
    return {
        "dish": f"{subject} Nu Shaak",
        "servings": servings,
        "description": f"A simple Gujarati-style {subject.lower()} shaak with rai, jeera, turmeric, chilli, and coriander.",
        "prep_time": _estimate_time(15, servings, "prep"),
        "cook_time": _estimate_time(25, servings, "cook"),
        "ingredients": _scale_recipe_rows(rows, servings),
        "recipe_steps": [
            f"Step 1: Wash and cut the {ingredient.lower()} into even pieces so every piece cooks at the same speed.",
            "Step 2: Heat oil in a kadai, then crackle mustard seeds and cumin seeds until aromatic.",
            f"Step 3: Add the {ingredient.lower()}, turmeric, chilli powder, coriander powder, and salt, then mix well.",
            "Step 4: Cover and cook on medium-low heat, stirring every few minutes so the shaak does not stick.",
            "Step 5: Finish with fresh coriander and keep the shaak mostly dry before serving with rotli or dal.",
        ],
    }


def _build_regional_pattern_recipe(query: str, servings: int) -> dict | None:
    cleaned = _remove_serving_phrases(query)
    if not cleaned:
        return None

    patterns = [
        r"(?P<subject>[a-z\s]+?)\s+(?:no|nu|ni|na)\s+(?P<kind>halvo|halwa|halva|halwo|shaak|shak|sabzi)\b",
        r"(?P<subject>[a-z\s]+?)\s+(?P<kind>halvo|halwa|halva|halwo|shaak|shak|sabzi)\b",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, cleaned))
        for match in reversed(matches):
            canonical = _canonical_food_subject(match.group("subject"))
            if not canonical:
                continue
            kind = match.group("kind")
            if kind.startswith("hal"):
                return _build_gujarati_halwa_recipe(canonical, servings)
            return _build_gujarati_shaak_recipe(canonical, servings)
    return None


def _fallback_parse_dish_request(user_input: str) -> dict:
    query = user_input.strip()
    if _is_garbage(query):
        return {"error": _ERROR_MSG}

    servings = _extract_servings(query)
    dish_key = _extract_dish_key(query)
    if dish_key:
        return _build_formula_recipe(dish_key, servings)
    regional_recipe = _build_regional_pattern_recipe(query, servings)
    if regional_recipe:
        return regional_recipe

    dish = _clean_dish_name(query)
    scale = max(servings, 1)
    ingredients = []
    for item in _GENERIC_COOKING_STAPLES:
        try:
            qty = float(item["quantity"]) * scale / 2
            quantity, unit = _format_quantity(qty, item["unit"], "spice" if item["category"] == "Spices" else "main", servings)
            ingredients.append({**item, "quantity": quantity, "unit": unit})
        except (ValueError, TypeError):
            ingredients.append(item)
    return {
        "dish": dish,
        "servings": servings,
        "description": f"A practical grocery plan for {dish}, scaled for {servings} serving{'s' if servings != 1 else ''}.",
        "prep_time": _estimate_time(20, servings, "prep"),
        "cook_time": _estimate_time(35, servings, "cook"),
        "ingredients": ingredients,
        "recipe_steps": [
            "Step 1: Prepare all vegetables and pantry staples before heating the pan.",
            "Step 2: Heat oil and build a balanced onion-tomato masala with ginger, garlic, and spices.",
            "Step 3: Add the main ingredients in batches, keeping the heat steady for even cooking.",
            "Step 4: Adjust salt, finish with fresh coriander, and serve hot.",
        ],
    }


def parse_dish_request(user_input: str) -> dict:
    if not _is_garbage(user_input):
        servings = _extract_servings(user_input)
        dish_key = _extract_dish_key(user_input)
        if dish_key in _LOCAL_FIRST_DISHES:
            return _build_formula_recipe(dish_key, servings)
        regional_recipe = _build_regional_pattern_recipe(user_input, servings)
        if regional_recipe:
            return regional_recipe

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


_AUTO_ADD_PRICE_BY_CATEGORY = {
    "vegetables": 40,
    "fruits": 60,
    "pulses": 120,
    "grains": 90,
    "flour": 80,
    "dairy": 90,
    "oil": 120,
    "spices": 60,
    "pantry": 50,
    "other": 50,
}

_AUTO_ADD_IMAGE_BY_CATEGORY = {
    "vegetables": "/static/images/products/vegetables_basket.png",
    "fruits": "/static/images/products/fruits_basket.png",
    "pulses": "/static/images/products/pulses_bowl.png",
    "grains": "/static/images/products/rice_bowl.png",
    "flour": "/static/images/products/flour_bowl.png",
    "dairy": "/static/images/products/milk_bottle.png",
    "oil": "/static/images/products/oil_bottle.png",
    "spices": "/static/images/products/spices_bowl.png",
}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = slug.strip("-")
    return slug or "item"


def _default_weight_for_unit(unit: str) -> str:
    unit = (unit or "").lower()
    if unit in {"g", "kg"}:
        return "1kg"
    if unit in {"ml", "l", "L"}:
        return "1L"
    if unit == "pcs":
        return "1pc"
    if unit in {"tsp", "tbsp"}:
        return "50g"
    if unit == "bunch":
        return "1 bunch"
    if unit == "pack":
        return "1 pack"
    return "1 unit"


def _auto_add_product(name: str, category: str, unit: str) -> dict | None:
    if not getattr(settings, "PLANNER_AUTO_ADD_PRODUCTS", True):
        return None
    if not name:
        return None

    category = category or "Other"
    category_key = category.strip().lower()
    base_price = _AUTO_ADD_PRICE_BY_CATEGORY.get(category_key, 50)
    image_url = _AUTO_ADD_IMAGE_BY_CATEGORY.get(category_key, "")

    payload = {
        "name": name.strip(),
        "category": category,
        "price": base_price,
        "discount": 0,
        "weight": _default_weight_for_unit(unit),
        "slug": _slugify(name),
        "image_url": image_url,
        "keywords": f"{name.strip()} {category}",
        "is_best_seller": False,
        "unit": unit,
    }

    try:
        collection = mongo_client.get_products_collection()
        result = collection.insert_one(payload)
        payload["_id"] = result.inserted_id
        return payload
    except Exception as exc:
        logger.warning("Auto-add product failed: %s", exc)
        return None


_PIECE_WEIGHT_GRAMS = {
    "garlic": 5,
    "green chilli": 5,
    "lemon": 50,
    "onion": 100,
    "potato": 150,
    "tomato": 100,
}

_BUNCH_WEIGHT_GRAMS = {
    "coriander": 100,
    "fresh coriander leaves": 100,
    "mint leaves": 100,
}


def _to_float(value) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _normalise_unit(unit: str) -> str:
    unit = (unit or "").strip().lower()
    aliases = {
        "grams": "g",
        "gram": "g",
        "kgs": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "litre": "l",
        "liter": "l",
        "litres": "l",
        "liters": "l",
        "pcs": "pc",
        "piece": "pc",
        "pieces": "pc",
        "clove": "clove",
        "cloves": "clove",
        "bunches": "bunch",
        "packs": "pack",
        "packet": "pack",
        "packets": "pack",
        "dozen": "dozen",
    }
    return aliases.get(unit, unit)


def _lookup_piece_weight(name: str) -> float | None:
    lowered = _normalise_text(name)
    for key, grams in _PIECE_WEIGHT_GRAMS.items():
        if key in lowered:
            return grams
    return None


def _lookup_bunch_weight(name: str) -> float | None:
    lowered = _normalise_text(name)
    for key, grams in _BUNCH_WEIGHT_GRAMS.items():
        if key in lowered:
            return grams
    return None


def _quantity_to_base(quantity, unit: str, name: str, category: str) -> tuple[str, float] | None:
    qty = _to_float(quantity)
    if qty is None or qty <= 0:
        return None

    unit = _normalise_unit(unit)
    category = (category or "").strip().lower()
    if unit == "kg":
        return "weight", qty * 1000
    if unit == "g":
        return "weight", qty
    if unit == "l":
        return "volume", qty * 1000
    if unit == "ml":
        return "volume", qty
    if unit == "tsp":
        return ("volume", qty * 5) if category == "oil" else ("weight", qty * 5)
    if unit == "tbsp":
        return ("volume", qty * 15) if category == "oil" else ("weight", qty * 15)
    if unit in {"pc", "clove"}:
        grams = 5 if unit == "clove" else _lookup_piece_weight(name)
        if grams:
            return "weight", qty * grams
        return "count", qty
    if unit == "bunch":
        grams = _lookup_bunch_weight(name)
        if grams:
            return "weight", qty * grams
        return "count", qty
    if unit == "dozen":
        return "count", qty * 12
    if unit == "pack":
        return "count", qty
    return "count", qty


def _package_to_base(weight: str, product_unit: str, name: str, category: str) -> tuple[str, float] | None:
    text = f"{weight or ''} {product_unit or ''}".strip().lower()
    if not text:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)", text)
    if not match:
        return None

    amount = _to_float(match.group(1))
    unit = _normalise_unit(match.group(2))
    if amount is None or amount <= 0:
        return None

    if unit == "kg":
        return "weight", amount * 1000
    if unit == "g":
        return "weight", amount
    if unit == "l":
        return "volume", amount * 1000
    if unit == "ml":
        return "volume", amount
    if unit == "dozen":
        return "count", amount * 12
    if unit in {"pc", "clove"}:
        grams = 5 if unit == "clove" else _lookup_piece_weight(name)
        if grams:
            return "weight", amount * grams
        return "count", amount
    if unit == "bunch":
        grams = _lookup_bunch_weight(name)
        if grams:
            return "weight", amount * grams
        return "count", amount
    if unit == "pack":
        return "count", amount
    return None


def _estimate_package_count(ingredient: dict, product: dict) -> int:
    needed = _quantity_to_base(
        ingredient.get("quantity", ""),
        ingredient.get("unit", ""),
        ingredient.get("name", ""),
        ingredient.get("category", "Other"),
    )
    package = _package_to_base(
        product.get("weight", ""),
        product.get("unit", ""),
        product.get("name", ingredient.get("name", "")),
        product.get("category", ingredient.get("category", "Other")),
    )
    if not needed or not package:
        return 1

    needed_dimension, needed_amount = needed
    package_dimension, package_amount = package
    if needed_dimension != package_dimension or package_amount <= 0:
        return 1
    return max(1, math.ceil(needed_amount / package_amount))


def match_ingredients_to_products(ingredients: list) -> list:
    matched_items = []
    global _mongo_lookup_available

    for ingredient in ingredients:
        name = ingredient.get("name", "")
        quantity = ingredient.get("quantity", "")
        unit = ingredient.get("unit", "")
        category = ingredient.get("category", "Other")

        product = None
        auto_added = False
        if _mongo_lookup_available:
            try:
                product = mongo_client.search_product_by_name(name)
            except Exception as exc:
                _mongo_lookup_available = False
                logger.warning("Mongo lookup disabled for this run: %s", exc)

        if not product:
            product = _auto_add_product(name, category, unit)
            auto_added = product is not None

        if product:
            image = product.get("image_url", "")
            if not image and product.get("images"):
                image = product["images"][0]
            product_price = product.get("price", product.get("base_price", 0)) or 0
            discount = product.get("discount", 0) or 0
            unit_price = round(product_price * (1 - discount / 100), 2)
            package_count = _estimate_package_count(ingredient, product)
            estimated_price = round(unit_price * package_count, 2)
            matched_items.append(
                {
                    "ingredient_name": name,
                    "needed_quantity": f"{quantity}{unit}",
                    "product_id": str(product["_id"]),
                    "product_name": product.get("name", name),
                    "product_price": product_price,
                    "unit_price": unit_price,
                    "package_count": package_count,
                    "estimated_price": estimated_price,
                    "product_unit": product.get("unit", unit),
                    "product_weight": product.get("weight", ""),
                    "product_image": image,
                    "product_category": product.get("category", category),
                    "discount": discount,
                    "matched": True,
                    "auto_added": auto_added,
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
                    "unit_price": 0,
                    "package_count": 0,
                    "estimated_price": 0,
                    "product_unit": unit,
                    "product_weight": "",
                    "product_image": "",
                    "product_category": category,
                    "discount": 0,
                    "matched": False,
                    "auto_added": False,
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
        item.get("estimated_price", 0)
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


_PANTRY_EXTRA_RECIPES = [
    {
        "dish": "Paneer Butter Masala",
        "description": "A creamy paneer curry built around tomato, onion, butter, and warm spices.",
        "primary_ingredients": ["paneer", "tomato", "onion", "butter", "cream"],
        "prep_time": "20 mins",
        "cook_time": "35 mins",
        "serves": "3-4 people",
        "youtube_query": "paneer butter masala recipe restaurant style",
        "recipe_steps": _RECIPE_FORMULAS["paneer butter masala"]["steps"],
        "pro_tips": ["Blend the gravy very smooth for a restaurant texture.", "Add paneer at the end so it stays soft."],
    },
    {
        "dish": "Chole",
        "description": "A hearty chickpea curry that works beautifully with onion, tomato, ginger, and garlic.",
        "primary_ingredients": ["kabuli chana", "onion", "tomato", "ginger", "garlic"],
        "prep_time": "25 mins",
        "cook_time": "1 hour",
        "serves": "4 people",
        "youtube_query": "punjabi chole recipe",
        "recipe_steps": _RECIPE_FORMULAS["chole"]["steps"],
        "pro_tips": ["Soak chickpeas overnight for even cooking.", "Simmer longer after adding masala for a deeper flavor."],
    },
    {
        "dish": "Vegetable Biryani",
        "description": "A fragrant rice dish that uses pantry vegetables, curd, and spices in layered dum style.",
        "primary_ingredients": ["rice", "onion", "tomato", "curd", "peas", "carrot"],
        "prep_time": "35 mins",
        "cook_time": "1 hour",
        "serves": "4-5 people",
        "youtube_query": "vegetable biryani recipe",
        "recipe_steps": _RECIPE_FORMULAS["biryani"]["steps"],
        "pro_tips": ["Parboil rice only to 70 percent so it finishes during dum.", "Rest biryani before opening the pot."],
    },
    {
        "dish": "Samosa",
        "description": "A crisp snack that turns potato, flour, chilli, and spices into a filling batch.",
        "primary_ingredients": ["potato", "all purpose flour", "green chilli", "cumin"],
        "prep_time": "35 mins",
        "cook_time": "40 mins",
        "serves": "8-10 pieces",
        "youtube_query": "samosa recipe at home",
        "recipe_steps": _RECIPE_FORMULAS["samosa"]["steps"],
        "pro_tips": ["Keep the dough firm for flaky shells.", "Fry on medium heat so the samosas become crisp all the way through."],
    },
]

_KNOWN_PANTRY_TERMS = sorted(
    {
        "all purpose flour", "basmati rice", "besan", "bhindi", "butter", "capsicum",
        "carrot", "chana dal", "coriander", "cream", "cumin", "curd", "curry leaves",
        "dry red chilli", "egg", "garam masala", "garlic", "ghee", "ginger",
        "green chilli", "kabuli chana", "maida", "moong dal", "onion", "paneer",
        "peas", "poha", "potato", "rice", "salt", "tomato", "toor dal",
        "turmeric", "wheat flour",
    },
    key=len,
    reverse=True,
)


def _canonical_ingredient(value: str) -> str:
    cleaned = _normalise_text(value)
    cleaned = re.sub(r"\b\d+(\.\d+)?\s*(kg|g|grams?|l|ml|pcs?|pieces?|cups?|tbsp|tsp|bunch|packets?)\b", " ", cleaned)
    cleaned = re.sub(r"[^a-z\s-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for source, target in sorted(_FOOD_SYNONYMS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(source)}\b", cleaned):
            return target
    return cleaned


def _split_pantry_items(items: list[str]) -> list[str]:
    result = []
    for item in items:
        for part in re.split(r"[,;\n]+", str(item)):
            cleaned = _canonical_ingredient(part)
            matched_terms = [term for term in _KNOWN_PANTRY_TERMS if re.search(rf"\b{re.escape(term)}\b", cleaned)]
            matched_terms.sort(key=lambda term: cleaned.find(term))
            if len(matched_terms) >= 2:
                for term in matched_terms:
                    if term not in result:
                        result.append(term)
            elif cleaned and cleaned not in result:
                result.append(cleaned)
    return result


def _is_food_ingredient(item: str) -> bool:
    if not item:
        return False
    words = set(re.findall(r"[a-z]+", item.lower()))
    if words & _FOOD_WORDS:
        return True
    return any(word in item for word in _FOOD_WORDS if len(word) >= 4)


def _ingredient_matches(required: str, pantry_item: str) -> bool:
    required = _canonical_ingredient(required)
    pantry_item = _canonical_ingredient(pantry_item)
    if not required or not pantry_item:
        return False
    if required == pantry_item:
        return True
    if required in pantry_item or pantry_item in required:
        return True
    required_words = set(required.split())
    pantry_words = set(pantry_item.split())
    return bool(required_words & pantry_words)


def _score_pantry_recipe(recipe: dict, pantry: list[str]) -> dict | None:
    primary = recipe.get("primary_ingredients", [])
    if not primary:
        return None

    used = []
    missing = []
    for ingredient in primary:
        if any(_ingredient_matches(ingredient, item) for item in pantry):
            used.append(ingredient.title())
        else:
            missing.append(ingredient.title())

    if not used:
        return None

    coverage = len(used) / len(primary)
    penalty = min(len(missing) * 4, 20)
    score = max(35, min(100, round(coverage * 92 + len(used) * 3 - penalty)))
    return {
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
        "ingredients_used": used,
        "_sort": (score, len(used), -len(missing)),
    }


def generate_from_pantry(available_ingredients: list[str]) -> dict:
    if not available_ingredients:
        return {"error": "Please provide at least one ingredient."}

    cleaned = _split_pantry_items(available_ingredients)
    cleaned = [item for item in cleaned if _is_food_ingredient(item)]
    if len(cleaned) < 2:
        return {"error": "Please add at least 2 real food ingredients, like potato, onion, or tomato."}

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

    # Fallback engine: score every recipe against the pantry instead of
    # returning the same static first three recipes.
    scored_recipes = []
    for recipe in [*_OFFLINE_RECIPE_DB, *_PANTRY_EXTRA_RECIPES]:
        scored = _score_pantry_recipe(recipe, cleaned)
        if scored:
            scored_recipes.append(scored)

    scored_recipes.sort(key=lambda recipe: recipe["_sort"], reverse=True)

    if not scored_recipes:
        return {"error": "I could not find a sensible dish from those ingredients. Try adding a staple like onion, tomato, rice, dal, paneer, or potato."}

    for recipe in scored_recipes:
        del recipe["_sort"]

    return {"suggestions": scored_recipes[:3], "pantry": [item.title() for item in cleaned]}
