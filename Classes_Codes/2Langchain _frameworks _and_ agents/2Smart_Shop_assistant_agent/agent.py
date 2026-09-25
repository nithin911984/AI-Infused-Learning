import json
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(    # Spawns a communications portal
    api_key=os.getenv("GROQ_API_KEY"), #  looks up the line labeled GROQ_API_KEY inside your hidden .env file.
    base_url="https://api.groq.com/openai/v1", # Reroutes the communications portal to talk to Groq's API instead of OpenAI's API.
    # uses OpenAI's code structure but redirects the base_url directly to Groq's servers
)

# DATABASE LOAD
PRICES = {"shoes": 799, "hat": 399, "bag": 1420, "shorts": 1299, "pants": 1699}

# TOOL CALL
def get_price(item):
    print(f"🔧 tool called: get_price({item})")     # so you SEE it happen
    return f"₹{PRICES.get(item.lower(), 'unknown')}"

# TOOL SCHEMA
tools = [{
    "type": "function",                                      # ①
    "function": {
        "name": "get_price",                                 # ②
        "description": "Get the price of a shop item the user asks about.",  # ③
        "parameters": {                                       # ④
            "type": "object",
            "properties": {"item": {"type": "string", "description": "the item name"}},
            "required": ["item"],
        },
    },
}]

# LOOP
def Agent(user_message):
    messages = [{"role": "user", "content": user_message}] # messages = [{"role": "user", "content": "How much are the shoes?"}]

    response = client.chat.completions.create(          # ① send message + tools menu
        model="openai/gpt-oss-120b", messages=messages, tools=tools)
    msg = response.choices[0].message
    
    if msg.tool_calls:                                  # ② did it ask for a tool?
        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)  # ③ read its request, run it
            result = get_price(args["item"])
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        response = client.chat.completions.create(      # ④ send it all back → nice answer
            model="openai/gpt-oss-120b", messages=messages)
        msg = response.choices[0].message

    return msg.content

print(Agent("How much are the shoes? Give response only if available in the PRICES"))      # → tool fires → "₹799"
print(Agent("Hi! What can you help with?"))   # → no tool → just chats




# A User Types a Message (The Real-Time Conversation Loop)
# When a human opens the webpage and types: "How much are the shoes?", the code triggers step-by-step:
# Step A: Entering the Gateway
#   Gradio intercepts the text and automatically passes it into the chat(message, history) function.
#   This immediately forwards the message to your core AI brain by executing Agent("How much are the shoes?").
# Step B: Structuring and First Call to Groq (①)
#   Inside Agent(), the user's string is converted into standard AI conversational format: messages = [{"role": "user", "content": "How much are the shoes?"}].
#   client.chat.completions.create(...) executes. This blasts your messages array and your tools definition menu over the internet to Groq.
# Step C: The Model Demands a Tool (② & ③)
#   Groq processes the prompt, realizes it doesn't know your inventory prices, and responds with a tool call intent.
#   The line if msg.tool_calls: evaluates to True.
#   The Record: messages.append(msg) logs the model's tool intent into your conversation history.
#   The Parse: json.loads(call.function.arguments) strips down the AI's complex request object into a clean Python dictionary: {"item": "shoes"}.
#   The Execution: get_price("shoes") runs locally on your machine. You see 🔧 tool called: get_price(shoes) print out in your server terminal. It looks up the price in your dictionary and returns "₹799".
#   The Update: This value is appended to the message logs as a "role": "tool" entry so the AI knows the function successfully resolved.
# Step D: Final Formulation and Reply (④)
#   Your script triggers a second network call to Groq using client.chat.completions.create(). 
#   This time, you pass the fully updated messages array which now contains the user question, the tool request, and the tool's answer (₹799).
#   Groq receives the complete context, formulates a natural sentence (like "The shoes cost ₹799"), and hands it back.
#   msg = response.choices[0].message extracts this clean reply, and return msg.content sends it backward through your Python blocks straight into the Gradio UI text box for the user to read.