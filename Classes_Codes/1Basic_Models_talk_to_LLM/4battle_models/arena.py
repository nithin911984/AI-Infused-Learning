import os
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client   = OpenAI(api_key=os.getenv("GROQ_API_KEY"),
                       base_url="https://api.groq.com/openai/v1")

def battle(prompt):
    if not prompt.strip():
        return "Please enter a valid prompt.", "Please enter a valid prompt."
        
    msgs = [{"role": "user", "content": prompt}]

    try:
        # Model A — OpenAI Cloud Platform
        a = openai_client.chat.completions.create(
            model="openai/gpt-oss-20b", 
            messages=msgs
        )
        output_a = a.choices[0].message.content
    except Exception as e:
        output_a = f"OpenAI Error: {e}"

    try:
        # Model B — LPU Acceleration on Groq
        b = groq_client.chat.completions.create(
            model="qwen/qwen3.6-27b", 
            messages=msgs
        )
        output_b = b.choices[0].message.content
    except Exception as e:
        output_b = f"Groq Error: {e}"

    return output_a, output_b
# …now we wrap this in Gradio with two columns + thumbs up/down 👇