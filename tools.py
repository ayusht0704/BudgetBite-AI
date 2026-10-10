
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

recipes = pd.read_csv(DATA_DIR / "recipes.csv")
prices = pd.read_csv(DATA_DIR / "grocery_prices.csv")

# Estimated quantities for one serving
PORTIONS = {
    "Moong Dal Chilla": {
        "moong_dal_dry": (0.08, "kg"),
        "onion": (0.03, "kg"),
        "oil": (0.01, "liter")
    },
    "Oats with Milk": {
        "oats": (0.05, "kg"),
        "milk": (0.25, "liter")
    },
    "Boiled Eggs and Roti": {
        "eggs": (2, "piece"),
        "wheat_flour": (0.06, "kg")
    },
    "Chana Masala with Rice": {
        "chickpeas_dry": (0.08, "kg"),
        "rice_dry": (0.06, "kg"),
        "onion": (0.03, "kg"),
        "tomato": (0.05, "kg")
    },
    "Moong Dal with Chapati": {
        "moong_dal_dry": (0.07, "kg"),
        "wheat_flour": (0.06, "kg")
    },
    "Paneer Bhurji with Roti": {
        "paneer": (0.08, "kg"),
        "wheat_flour": (0.06, "kg"),
        "onion": (0.03, "kg"),
        "tomato": (0.05, "kg")
    },
    "Soy Chunk Curry with Rice": {
        "soy_chunks_dry": (0.05, "kg"),
        "rice_dry": (0.06, "kg"),
        "tomato": (0.05, "kg")
    },
    "Boiled Chickpeas": {
        "chickpeas_dry": (0.06, "kg")
    }
}


def search_recipes(meal_type=None, diet=None):
    result = recipes.copy()

    if meal_type:
        result = result[
            result["meal_type"].str.lower() == meal_type.lower()
        ]

    if diet:
        result = result[
            result["diet"].str.lower() == diet.lower()
        ]

    return result[
        ["meal_name", "meal_type", "diet",
         "protein_g", "prep_time_min", "ingredients"]
    ].to_dict(orient="records")


def estimate_meal_cost(meal_name, pantry=None):
    pantry = {
        item.strip().lower()
        for item in (pantry or [])
    }

    if meal_name not in PORTIONS:
        return {"error": "No portion estimate available."}

    ingredient_costs = {}
    missing_prices = []

    for ingredient, (quantity, unit) in PORTIONS[meal_name].items():
        if ingredient.lower() in pantry:
            ingredient_costs[ingredient] = 0.0
            continue

        match = prices[
            prices["ingredient"].str.lower() == ingredient.lower()
        ]

        if match.empty or match.iloc[0]["unit"] != unit:
            missing_prices.append(ingredient)
        else:
            price = float(match.iloc[0]["price_inr"])
            ingredient_costs[ingredient] = round(price * quantity, 2)

    return {
        "meal": meal_name,
        "estimated_cost_inr": round(sum(ingredient_costs.values()), 2),
        "ingredient_costs": ingredient_costs,
        "missing_prices": missing_prices,
        "estimate_only": True
    }


def check_budget(meal_name, budget, pantry=None):
    result = estimate_meal_cost(meal_name, pantry)

    if "error" in result:
        return result

    if result["missing_prices"]:
        result["budget_status"] = "INCOMPLETE_PRICE_DATA"
    elif result["estimated_cost_inr"] <= budget:
        result["budget_status"] = "WITHIN_BUDGET"
    else:
        result["budget_status"] = "OVER_BUDGET"

    result["budget_inr"] = float(budget)
    return result


def suggest_alternatives(
    budget, pantry=None, diet=None, meal_type=None
):
    candidates = recipes.copy()

    if diet:
        candidates = candidates[
            candidates["diet"].str.lower() == diet.lower()
        ]

    if meal_type:
        candidates = candidates[
            candidates["meal_type"].str.lower() == meal_type.lower()
        ]

    suggestions = []

    for _, recipe in candidates.iterrows():
        result = check_budget(
            recipe["meal_name"], budget, pantry
        )

        if result.get("budget_status") == "WITHIN_BUDGET":
            suggestions.append({
                "meal_name": recipe["meal_name"],
                "estimated_cost_inr": result["estimated_cost_inr"],
                "protein_g": float(recipe["protein_g"]),
                "prep_time_min": int(recipe["prep_time_min"])
            })

    return sorted(
        suggestions,
        key=lambda item: (
            item["estimated_cost_inr"], -item["protein_g"]
        )
    )
