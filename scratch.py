import os
import sys
import re

filepath = r"e:\DA IICT V.01\DA-IICT\apps\planner\ai_planner.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find("_PANTRY_FALLBACK_SUGGESTIONS = [")
if idx == -1:
    print("Could not find _PANTRY_FALLBACK_SUGGESTIONS")
    sys.exit(1)

new_content = content[:idx] + """_OFFLINE_RECIPE_DB = [
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
                raw = re.sub(r"^```[a-z]*\\n?", "", raw)
                raw = re.sub(r"\\n?```$", "", raw)
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
"""

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Update complete!")
