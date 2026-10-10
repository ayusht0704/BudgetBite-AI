
import os
from langchain_groq import ChatGroq

from tools import check_budget, suggest_alternatives


def replan_meal(meal_name, budget, protein_target=10,
                diet="vegetarian", meal_type="Breakfast",
                pantry=None):

    # Check the original meal against the budget
    original = check_budget(meal_name, budget, pantry)

    print("\n--- Original Meal Check ---")
    print(original)

    # If the cost is incomplete, don't claim it passed or failed
    if original.get("budget_status") == "INCOMPLETE_PRICE_DATA":
        return "Cannot replan reliably because some ingredient prices are missing."

    # Find alternatives using Python tools
    alternatives = suggest_alternatives(
        budget=budget,
        pantry=pantry,
        diet=diet,
        meal_type=meal_type
    )

    alternatives = [
        item for item in alternatives
        if item["protein_g"] >= protein_target
    ]

    if original.get("budget_status") == "WITHIN_BUDGET":
        return (
            f"{meal_name} fits your budget. "
            f"Estimated cost: ₹{original['estimated_cost_inr']:.2f}."
        )

    if not alternatives:
        return (
            f"{meal_name} exceeds your budget of ₹{budget}. "
            "No alternative matching the budget and protein target "
            "was found in the current dataset."
        )

    # Ask Groq to explain the verified results
    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    llm = ChatGroq(
        model=model_name,
        temperature=0
    )

    prompt = f"""
You are BudgetBite AI, a meal-planning assistant for students.

The original meal is: {meal_name}
Estimated original cost: ₹{original['estimated_cost_inr']:.2f}
User's budget: ₹{budget}
Protein target per meal: {protein_target} g

Affordable alternatives returned by the Python tools:
{alternatives}

Explain briefly why the original meal exceeds the budget.
Recommend the best alternative from the supplied list.
Use only the costs and protein values in the supplied results.
Clearly label costs as estimates based on sample data.
Do not invent additional prices or nutrition values.
"""

    response = llm.invoke(prompt)

    print("\n--- Affordable Alternatives From Tools ---")
    print(alternatives)

    print("\n--- Groq Replanning Recommendation ---")
    return response.content


if __name__ == "__main__":
    answer = replan_meal(
        meal_name="Oats with Milk",
        budget=20,
        protein_target=10,
        diet="vegetarian",
        meal_type="Breakfast"
    )

    print("\n" + str(answer))
