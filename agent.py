import os
from langchain_groq import ChatGroq

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL"),
    temperature=0
)

response = llm.invoke(
    "Suggest three affordable protein-rich Indian meals."
)

print(response.content)