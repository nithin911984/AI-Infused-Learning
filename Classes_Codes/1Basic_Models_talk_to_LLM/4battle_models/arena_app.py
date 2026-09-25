# pip install openai gradio python-dotenv
import os
from groq import Groq
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

import os
from openai import OpenAI

openai_client = OpenAI()

groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def ask(client, model, prompt):
    r = client.chat.completions.create(
        model=model, 
        messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content

def battle(prompt):
    if not prompt.strip():
        return "Please enter a valid prompt.", "Please enter a valid prompt."
        
    msgs = [{"role": "user", "content": prompt}]

    try:
        # Model A — OpenAI Cloud Platform
        a = openai_client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=msgs,
            max_tokens=250
        )
        output_a = a.choices[0].message.content
    except Exception as e:
        output_a = f"OpenAI Error: {e}"

    try:
        # Model B — LPU Acceleration on Groq
        b = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b", 
            messages=msgs,
            max_tokens=250
        )
        output_b = b.choices[0].message.content
    except Exception as e:
        output_b = f"Groq Error: {e}"

    return output_a, output_b

def vote(label):
    return f"🗳️ Thanks! You voted: **{label}**"   # in real apps, save this to a file/DB

with gr.Blocks(title="LLM Arena") as demo:
    gr.Markdown("# 🥊 LLM Arena — one prompt, two models")
    prompt = gr.Textbox(label="Ask both models the same thing")
    go = gr.Button("⚔️ Battle!", variant="primary")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🤖 Model A")
            out_a = gr.Markdown()
            with gr.Row():
                up_a   = gr.Button("👍");  down_a = gr.Button("👎")
        with gr.Column():
            gr.Markdown("### 🤖 Model B")
            out_b = gr.Markdown()
            with gr.Row():
                up_b   = gr.Button("👍");  down_b = gr.Button("👎")

    verdict = gr.Markdown()

    go.click(battle, inputs=prompt, outputs=[out_a, out_b])
    up_a.click(lambda: vote("👍 Model A"), outputs=verdict)
    down_a.click(lambda: vote("👎 Model A"), outputs=verdict)
    up_b.click(lambda: vote("👍 Model B"), outputs=verdict)
    down_b.click(lambda: vote("👎 Model B"), outputs=verdict)

demo.launch(share=True)   # → local + public link 🎉