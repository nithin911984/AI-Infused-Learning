import gradio as gr
from agent import Agent              # the function you just wrote

def chat(message, history):          # ① Gradio fills these two in for you
    return Agent(message) # Agent("How much are the shoes?")

gr.ChatInterface(fn=chat, title="🛍️ Smart Shop Assistant").launch(share=True)  # ②