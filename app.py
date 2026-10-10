import streamlit as st

from tools import search_recipes, check_budget
from replanning_agent import replan_meal
from weekly_planner import generate_weekly_plan


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="BudgetBite AI",
    page_icon="🍽️",
    layout="wide"
)


# ==================================================
# CUSTOM CSS
# ==================================================

st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}

.block-container {
    max-width: 100%;
    padding: 1.5rem 2.1rem;
}

h1, h2, h3, p, label {
    color: white;
}

.main-title {
    font-size: 32px;
    font-weight: 650;
    margin-bottom: 18px;
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {
    background-color: #262831;
    border: none;
    border-radius: 8px;
    min-height: 40px;
}

div[data-baseweb="input"] input,
div[data-baseweb="select"] div {
    color: white;
}

div[data-testid="stNumberInput"] button {
    background-color: #262831;
    color: white;
    border: none;
}

div.stButton > button {
    width: 100%;
    background-color: #ff484f;
    color: white;
    border: none;
    border-radius: 8px;
    height: 40px;
    font-weight: 600;
}

div.stButton > button:hover {
    background-color: #ed343c;
    color: white;
    border: none;
}

.disclaimer {
    color: #92949c;
    font-size: 13px;
    margin-top: 5px;
    margin-bottom: 18px;
}

hr {
    border-color: #34363e;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def parse_ingredients(text):
    """Convert comma-separated ingredients into a list."""
    return [
        item.strip().lower()
        for item in (text or "").split(",")
        if item.strip()
    ]


def contains_avoided_ingredient(recipe, avoided):
    """Exclude recipes containing ingredients the user wants to avoid."""
    ingredients = parse_ingredients(
        str(recipe.get("ingredients", ""))
    )

    return any(
        avoid_item in ingredient
        for avoid_item in avoided
        for ingredient in ingredients
    )


def get_recipes(diet, meal_type):
    """Retrieve recipes using the existing recipe-search tool."""
    selected_diet = None if diet == "Any" else diet
    selected_type = None if meal_type == "Any" else meal_type

    return search_recipes(
        diet=selected_diet,
        meal_type=selected_type
    )


def get_affordable_options(
    budget,
    diet,
    meal_type,
    protein_target,
    pantry,
    avoided
):
    """
    Search for affordable alternatives.

    Exact matches are preferred. If none exist, progressively relax
    the protein target and meal-type restriction. Dietary restrictions,
    avoided ingredients and the budget are still enforced.
    """

    selected_diet = None if diet == "Any" else diet
    selected_type = None if meal_type == "Any" else meal_type

    # Stage 1: requested diet, meal type and protein target.
    # Stage 2: requested diet and meal type, lower protein target.
    # Stage 3: requested diet and any meal type.
    # Stage 4: any diet and any meal type.
    search_stages = [
        (selected_diet, selected_type, protein_target),
        (selected_diet, selected_type, 0),
        (selected_diet, None, 0),
        (None, None, 0),
    ]

    seen = set()

    for stage_diet, stage_type, minimum_protein in search_stages:
        try:
            recipes = search_recipes(
                diet=stage_diet,
                meal_type=stage_type
            )
        except Exception:
            continue

        options = []

        for recipe in recipes:
            name = recipe["meal_name"]

            if name in seen:
                continue

            seen.add(name)

            if contains_avoided_ingredient(recipe, avoided):
                continue

            protein = float(recipe.get("protein_g", 0))

            if protein < minimum_protein:
                continue

            cost_info = check_budget(name, budget, pantry)

            if cost_info.get("budget_status") != "WITHIN_BUDGET":
                continue

            options.append({
                "meal_name": name,
                "meal_type": recipe.get("meal_type", "Unknown"),
                "protein_g": protein,
                "prep_time_min": int(
                    recipe.get("prep_time_min", 0)
                ),
                "ingredients": recipe.get("ingredients", ""),
                "estimated_cost_inr": float(
                    cost_info["estimated_cost_inr"]
                ),
                "meets_protein": protein >= protein_target,
                "meets_diet": (
                    stage_diet is None
                    or str(recipe.get("diet", "")).lower()
                    == stage_diet.lower()
                ),
                "matches_meal_type": (
                    stage_type is None
                    or str(recipe.get("meal_type", "")).lower()
                    == stage_type.lower()
                ),
            })

        if options:
            # Prioritize protein target, then cost and protein amount.
            options.sort(
                key=lambda item: (
                    not item["meets_protein"],
                    item["estimated_cost_inr"],
                    -item["protein_g"]
                )
            )

            return options, stage_diet, stage_type

    return [], selected_diet, selected_type


# ==================================================
# PAGE HEADING
# ==================================================

st.markdown(
    '<div class="main-title">Tell us your requirements</div>',
    unsafe_allow_html=True
)


# ==================================================
# REQUIREMENTS FORM
# ==================================================

left_col, right_col = st.columns(2, gap="medium")

with left_col:
    budget = st.number_input(
        "Budget per serving (₹)",
        min_value=1,
        max_value=10000,
        value=200,
        step=10
    )

    diet = st.selectbox(
        "Dietary preference",
        ["vegetarian", "egg", "Any"]
    )

    protein_target = st.number_input(
        "Protein target per meal (g)",
        min_value=1,
        max_value=200,
        value=55,
        step=5
    )

with right_col:
    meal_type = st.selectbox(
        "Meal type",
        ["Lunch", "Breakfast", "Dinner", "Snack", "Any"]
    )

    pantry_text = st.text_input(
        "Ingredients already available",
        placeholder="e.g. oats, milk, onion"
    )

    avoid_text = st.text_input(
        "Ingredients to avoid",
        placeholder="e.g. eggs"
    )

st.markdown(
    '<div class="disclaimer">'
    'Costs use illustrative portion sizes and sample grocery prices. '
    'This prototype is not a medical or allergy-safety system.'
    '</div>',
    unsafe_allow_html=True
)


# ==================================================
# FIND MY MEALS
# ==================================================

if st.button("Find My Meals", key="find_meals"):

    pantry = parse_ingredients(pantry_text)
    avoided = parse_ingredients(avoid_text)

    st.session_state["requirements"] = {
        "budget": float(budget),
        "diet": diet,
        "meal_type": meal_type,
        "protein_target": float(protein_target),
        "pantry": pantry,
        "avoided": avoided,
    }

    try:
        recipes = get_recipes(diet, meal_type)

        exact_matches = []

        # First search for meals satisfying all requirements.
        for recipe in recipes:

            if contains_avoided_ingredient(recipe, avoided):
                continue

            protein = float(recipe.get("protein_g", 0))

            if protein < protein_target:
                continue

            cost_info = check_budget(
                recipe["meal_name"],
                budget,
                pantry
            )

            if cost_info.get("budget_status") == "WITHIN_BUDGET":
                exact_matches.append({
                    "meal_name": recipe["meal_name"],
                    "meal_type": recipe["meal_type"],
                    "protein_g": protein,
                    "prep_time_min": int(
                        recipe.get("prep_time_min", 0)
                    ),
                    "ingredients": recipe.get("ingredients", ""),
                    "estimated_cost_inr": float(
                        cost_info["estimated_cost_inr"]
                    ),
                    "meets_protein": True,
                    "meets_diet": True,
                    "matches_meal_type": True,
                })

        st.session_state["exact_matches"] = exact_matches

        if exact_matches:
            st.session_state["recommendations"] = exact_matches
            st.session_state["fallback_used"] = False
            st.session_state["fallback_stage"] = None

        else:
            # Automatically replan if no exact match exists.
            with st.spinner(
                "No exact match found. BudgetBite is replanning..."
            ):
                options, used_diet, used_type = get_affordable_options(
                    budget=budget,
                    diet=diet,
                    meal_type=meal_type,
                    protein_target=protein_target,
                    pantry=pantry,
                    avoided=avoided
                )

            st.session_state["recommendations"] = options
            st.session_state["fallback_used"] = bool(options)
            st.session_state["fallback_stage"] = {
                "diet": used_diet,
                "meal_type": used_type,
            }

        st.session_state["ai_explanation"] = None

    except Exception as error:
        st.error(f"Meal planning failed: {error}")

# ==================================================
# RECOMMENDATIONS AND AUTOMATIC REPLANNING
# ==================================================

if "recommendations" in st.session_state:

    recommendations = st.session_state["recommendations"]
    requirements = st.session_state["requirements"]

    st.divider()
    st.header("Your Meal Recommendations")

    if recommendations:

        if st.session_state.get("fallback_used"):
            st.warning(
                "No exact match was found. These are alternative meals "
                "selected using your budget and available recipe data."
            )
        else:
            st.success("Meals matching your requirements were found.")

        for meal in recommendations[:10]:

            with st.container(border=True):

                st.subheader(meal["meal_name"])

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Estimated cost",
                    f"₹{meal['estimated_cost_inr']:.2f}"
                )

                col2.metric(
                    "Protein",
                    f"{meal['protein_g']:.1f} g"
                )

                col3.metric(
                    "Preparation",
                    f"{meal['prep_time_min']} min"
                )

                st.write(f"Meal type: {meal['meal_type']}")
                st.write(f"Ingredients: {meal['ingredients']}")

                if not meal["meets_protein"]:
                    st.warning("This meal is below your protein target.")

    else:
        st.warning(
            "No affordable alternatives were found in the current dataset. "
            "You can still use AI Meal Replanning below."
        )


# ==================================================
# AI MEAL REPLANNING - ALWAYS VISIBLE
# ==================================================

st.divider()
st.header("🤖 AI Meal Replanning")

st.write(
    "Choose a meal. The AI agent checks your budget and protein target "
    "and suggests an alternative when needed."
)

requirements = st.session_state.get(
    "requirements",
    {
        "budget": float(budget),
        "diet": diet,
        "meal_type": meal_type,
        "protein_target": float(protein_target),
        "pantry": parse_ingredients(pantry_text),
        "avoided": parse_ingredients(avoid_text),
    }
)

try:
    all_recipes = search_recipes(
        diet=None if requirements["diet"] == "Any"
        else requirements["diet"],
        meal_type=None if requirements["meal_type"] == "Any"
        else requirements["meal_type"]
    )

    if not all_recipes:
        all_recipes = search_recipes(
            diet=None,
            meal_type=None
        )

    if all_recipes:

        meal_names = [r["meal_name"] for r in all_recipes]

        selected_meal = st.selectbox(
            "Select a meal to replan",
            meal_names,
            key="ai_replan_meal"
        )

        if st.button("Replan My Meal", key="ai_replan_button"):

            selected_recipe = next(
                r for r in all_recipes
                if r["meal_name"] == selected_meal
            )

            if contains_avoided_ingredient(
                selected_recipe,
                requirements["avoided"]
            ):
                st.warning(
                    "This meal contains an ingredient you asked to avoid. "
                    "Choose a different meal."
                )

            else:
                cost_info = check_budget(
                    selected_meal,
                    requirements["budget"],
                    requirements["pantry"]
                )

                protein = float(selected_recipe.get("protein_g", 0))
                target = requirements["protein_target"]

                if cost_info.get("budget_status") == "INCOMPLETE_PRICE_DATA":
                    st.warning(
                        "Ingredient price data is incomplete for this meal."
                    )

                elif (
                    cost_info.get("budget_status") == "WITHIN_BUDGET"
                    and protein >= target
                ):
                    st.success(
                        f"{selected_meal} meets your requirements. "
                        f"Estimated cost: "
                        f"₹{cost_info['estimated_cost_inr']:.2f}; "
                        f"protein: {protein:.1f} g."
                    )

                else:
                    with st.spinner(
                        "AI agent is checking alternatives..."
                    ):
                        try:
                            explanation = replan_meal(
                                meal_name=selected_meal,
                                budget=requirements["budget"],
                                protein_target=target,
                                diet=(
                                    requirements["diet"]
                                    if requirements["diet"] != "Any"
                                    else "vegetarian"
                                ),
                                meal_type=(
                                    requirements["meal_type"]
                                    if requirements["meal_type"] != "Any"
                                    else selected_recipe.get(
                                        "meal_type", "Breakfast"
                                    )
                                ),
                                pantry=requirements["pantry"]
                            )

                            st.session_state["ai_replanning_result"] = (
                                explanation
                            )

                        except Exception as error:
                            st.session_state["ai_replanning_result"] = (
                                f"AI replanning error: {error}"
                            )

        if st.session_state.get("ai_replanning_result"):
            st.subheader("AI Agent Recommendation")
            st.info(st.session_state["ai_replanning_result"])

    else:
        st.warning(
            "No recipes are available. Check your data/recipes.csv file."
        )

except Exception as error:
    st.error(f"Unable to load AI replanning: {error}")


# ==================================================
# WEEKLY MEAL PLANNER
# ==================================================

st.divider()
st.header("Weekly Meal Planner")

st.write(
    "Generate a seven-day sample meal plan using your current requirements."
)

if st.button("Generate Weekly Plan", key="weekly_plan_button"):

    try:
        weekly_result = generate_weekly_plan(
            budget=float(requirements["budget"]),
            diet=(
                None if requirements["diet"] == "Any"
                else requirements["diet"]
            ),
            protein_target=float(requirements["protein_target"]),
            pantry=requirements["pantry"]
        )

        st.session_state["weekly_plan_result"] = weekly_result

    except Exception as error:
        st.error(f"Weekly planner error: {error}")


if "weekly_plan_result" in st.session_state:

    weekly_result = st.session_state["weekly_plan_result"]

    st.info(
        weekly_result.get("message", "Weekly plan generated.")
    )

    for day in weekly_result.get("plan", []):

        with st.expander(day["day"], expanded=True):

            for meal in day.get("meals", []):

                st.write(
                    f"**{meal['meal_type']} — {meal['name']}**"
                )

                st.write(
                    f"Cost: ₹{meal['cost']:.2f} | "
                    f"Protein: {meal['protein_g']} g"
                )

            st.write(
                f"**Estimated daily total: "
                f"₹{day['estimated_total']:.2f}**"
            )

    st.subheader("Shopping List")

    for ingredient, count in weekly_result.get(
        "shopping_list", {}
    ).items():

        st.write(
            f"- {ingredient.replace('_', ' ').title()}: "
            f"{count} recipe occurrence(s)"
        )

    st.caption(
        "Costs and nutrition are estimates from the sample dataset. "
        "Shopping-list counts are recipe occurrences, not measured quantities."
    )
