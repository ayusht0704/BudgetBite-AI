
from tools import search_recipes, check_budget


def generate_weekly_plan(
    budget=100,
    diet="vegetarian",
    protein_target=10,
    pantry=None
):
    pantry = pantry or []

    recipes = search_recipes(diet=diet)

    # Keep recipes that fit the budget and protein target
    candidates = []

    for recipe in recipes:
        if recipe["protein_g"] < protein_target:
            continue

        cost = check_budget(
            recipe["meal_name"],
            budget,
            pantry=pantry
        )

        if cost.get("budget_status") == "WITHIN_BUDGET":
            candidates.append({
                "name": recipe["meal_name"],
                "meal_type": recipe["meal_type"],
                "protein_g": recipe["protein_g"],
                "prep_time_min": recipe["prep_time_min"],
                "cost": cost["estimated_cost_inr"]
            })

    if not candidates:
        return {
            "plan": [],
            "shopping_list": {},
            "message": (
                "No meals match the current budget and protein "
                "target. Try adjusting your requirements."
            )
        }

    # Rotate available meals to create a seven-day sample plan
    meal_types = ["Breakfast", "Lunch", "Dinner"]
    plan = []
    shopping_list = {}

    for day in range(7):
        daily_meals = []

        for meal_type in meal_types:
            options = [
                item for item in candidates
                if item["meal_type"] == meal_type
            ]

            if not options:
                continue

            # Rotate through the available recipes
            chosen = options[day % len(options)]
            daily_meals.append(chosen)

            # Build a consolidated list from recipe ingredients.
            # Quantities are not calculated in this initial version.
            recipe_rows = [
                r for r in recipes
                if r["meal_name"] == chosen["name"]
            ]

            if recipe_rows:
                ingredients = recipe_rows[0]["ingredients"].split(",")

                for ingredient in ingredients:
                    ingredient = ingredient.strip()
                    shopping_list[ingredient] = (
                        shopping_list.get(ingredient, 0) + 1
                    )

        plan.append({
            "day": f"Day {day + 1}",
            "meals": daily_meals,
            "estimated_total": round(
                sum(item["cost"] for item in daily_meals), 2
            )
        })

    return {
        "plan": plan,
        "shopping_list": shopping_list,
        "message": "Weekly sample plan generated successfully."
    }


if __name__ == "__main__":
    result = generate_weekly_plan(
        budget=100,
        diet="vegetarian",
        protein_target=10
    )

    print("\n", result["message"])

    for day in result["plan"]:
        print(f"\n{day['day']} — Estimated total: ₹{day['estimated_total']}")
        for meal in day["meals"]:
            print(
                f"  {meal['meal_type']}: {meal['name']} "
                f"({meal['protein_g']} g listed protein)"
            )

    print("\nConsolidated ingredient list:")
    for ingredient, count in result["shopping_list"].items():
        print(f"  {ingredient}: used in {count} planned servings")
