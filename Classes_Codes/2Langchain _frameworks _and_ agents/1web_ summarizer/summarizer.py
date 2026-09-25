from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from scraper import fetch_website_contents   # reuse Class 1's scraper
load_dotenv()

prompt = ChatPromptTemplate.from_template(            # ①
    "Give a detailed brief of this website:\n\n{website}")

model = ChatGroq(
    model="openai/gpt-oss-120b", 
    temperature=0.7
)   # ②

# This parser strips all the junk away and extracts just the raw text string written by the AI.
parser = StrOutputParser()                              # ③

chain = prompt | model | parser                        # ④

def summarize(url):
    return chain.invoke({"website": fetch_website_contents(url)})   # ⑤

print(summarize("https://anthropic.com"))

# When you call summarize("https://anthropic.com"), five things happen sequentially:
# 1. fetch_website_contents(url) executes, triggering your scraper to download 
# and clean the raw text content of Anthropic's homepage.
# 2. The code passes that text into the chain via .invoke({"website": ...}).
# 3. The raw scraped text fills the {website} slot in your Prompt Template ①.
# 4. The completed prompt gets blasted to the Groq API ② to generate a response.
# 5. The Output Parser ③ grabs the final summary text and hands it back to you to print.