# pip install gradio
import gradio as gr
from summarizer_agent import summarize

gr.Interface(
    fn=summarize,                                  # your function
    inputs=gr.Textbox(label="Website URL"),
    outputs=gr.Textbox(label="Summary",lines=20, interactive=False),
    title="AI Website Summarizer",
).launch(share=True,debug=True)   # share=True, a public link you can post!