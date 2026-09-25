import os
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from scraper import fetch_website_contents

         # <-- this reads your .env file
load_dotenv()          

# Explicitly pull the key from system memory and pass it to the client
client =Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

system_prompt = """You analyze the contents of a website and
give a short, friendly summary. Ignore navigation menus.
Respond in markdown."""

def summarize(url):
    website = fetch_website_contents(url) # invokes fetch_website_contents function (from scraper.py)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role":"system", "content": system_prompt},
            {"role":"user",   "content": f"Summarize this website:\n\n{website}"},
        ],
    )
    return response.choices[0].message.content

