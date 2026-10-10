
import os
import json
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

from tools import search_recipes, check_grocery_price, calculate_protein


# 1. Define tools available to the AI agent

@tool
def find_recipes(meal_type: str = "", diet: str = "") -> str:
    """Search recipes by meal type such as Breakfast, Lunch, Dinner or Snack.
    Optionally filter by diet such as vegetarian or egg."""
    result = search_recipes(
        meal_type=meal_type or None,
        diet=diet or None
    )
    return json.dumps(result, ensure_ascii=False)


@tool
def get_grocery_price(ingredient: str) -> str:
    """Look up the sample dataset price of a grocery ingredient."""
    return json.dumps(
        check_grocery_price(ingredient),
        ensure_ascii=False
    )


@tool
def get_protein_total(meal_names: list[str]) -> str:
    """Calculate the total listed protein for a list of exact recipe names."""
    return json.dumps(
        calculate_protein(meal_names),
        ensure_ascii=False
    )


tools = [find_recipes, get_grocery_price, get_protein_total]
tool_map = {item.name: item for item in tools}


# 2. Connect to Groq

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    temperature=0
)

agent_llm = llm.bind_tools(tools)


# 3. Run the agent and execute the tools it selects

def run_agent(user_request):
    messages = [
        HumanMessage(content=(
            "You are BudgetBite AI, a budget-friendly meal planning assistant "
            "for students in India. Use the available tools when you need recipe, "
            "price, or protein data. Do not invent tool results. Prices and "
            "nutrition values are illustrative sample data. Clearly state when "
            "the available data is insufficient. Give practical, concise advice.\n\n"
            f"User request: {user_request}"
        ))
    ]

    print("\n--- Agent started ---")

    for step in range(5):
        response = agent_llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            print("\n--- Final Recommendation ---")
            print(response.content)
            return

        for call in response.tool_calls:
            name = call["name"]
            arguments = call["args"]

            print(f"\nTool selected: {name}")
            print(f"Arguments: {arguments}")

            try:
                result = tool_map[name].invoke(arguments)
            except Exception as error:
                result = f"Tool error: {error}"

            print(f"Tool result: {result}")

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call["id"]
                )
            )

    print("Agent stopped after reaching the step limit.")


# 4. Start the application

if __name__ == "__main__":
    request = input(
        "Describe your meal requirements "
        "(e.g. vegetarian breakfast under a student budget): "
    )
    run_agent(request)
