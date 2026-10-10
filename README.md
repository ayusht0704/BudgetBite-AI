# BudgetBite AI 🍽️

**An Agentic AI-Based Budget-Friendly Meal Planning and Protein Optimization System for Students**

## Overview

BudgetBite AI is an agentic AI prototype that helps students plan affordable meals according to their budget, dietary preferences, protein targets, available ingredients, and ingredients to avoid.

The system combines an LLM-based agent with Python tools to estimate meal costs, search recipes, recommend alternatives, and generate sample weekly meal plans.

## Features

- Budget-based recipe recommendations
- Dietary preference and meal-type filtering
- Protein target checking
- Estimated ingredient and meal costs
- Pantry ingredient support
- Ingredient exclusion
- AI-assisted meal replanning
- Sample seven-day meal planner
- Shopping-list generation

## Technology Stack

- Python
- Streamlit
- LangChain
- Groq API
- Pandas
- CSV datasets

## Project Structure

```text
BudgetBites/
├── app.py
├── agent.py
├── tools.py
├── replanning_agent.py
├── weekly_planner.py
├── requirements.txt
├── README.md
└── data/
    ├── recipes.csv
    ├── nutrition.csv
    └── grocery_prices.csv
```

## Installation

1. Clone this repository.
2. Open the project folder in VS Code.
3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Set your Groq API key as an environment variable named `GROQ_API_KEY`.
5. Set the model variable to the model used by the project:

```text
GROQ_MODEL=openai/gpt-oss-20b
```

6. Start the application:

```bash
python -m streamlit run app.py
```

## Dataset

The project uses local CSV files for recipes, nutrition information, and estimated grocery prices. The current prototype uses illustrative sample data, which should not be treated as verified nutritional information or current market prices.

## Limitations

- Recipe options are limited by the available dataset.
- Cost and protein estimates depend on the quality of the input data.
- The weekly planner is a prototype and may not provide nutritionally complete meal plans.
- Ingredient exclusion is a basic filter, not an allergy-safety system.

## Future Improvements

- Integrate verified nutrition databases and current grocery prices.
- Expand the recipe dataset.
- Improve weekly budget optimization and ingredient quantity calculations.
- Add user profiles and persistent preferences.
- Improve agent tracing and automated testing.

## Security

Never commit API keys, passwords, or other secrets to the repository.