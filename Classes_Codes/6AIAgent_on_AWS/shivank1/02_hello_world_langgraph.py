import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.agents import create_agent
from config import MODEL_ID


# Define a simple tool
@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome to the world of AI agents."


# Initialize the LLM via Bedrock
llm = init_chat_model(
    MODEL_ID,
    model_provider="bedrock_converse",
)

# Create a ReAct agent with the tool
agent = create_agent(model=llm, tools=[greet])

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Please greet Alice and Bob."}]}
)

# Print every step so you can see the loop
for message in response["messages"]:
    print(f"{message.type}: {message.content}")
