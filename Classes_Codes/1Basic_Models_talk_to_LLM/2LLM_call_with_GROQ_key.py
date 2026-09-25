# DEPENDENCY & LIBRARY IMPORTATION
import os   #need this to interact with our computer's system environment variables.
from openai import OpenAI  
from dotenv import load_dotenv  # helper function from a library called python-dotenv

# LOCAL CONFIGURATION & VARIABLE INJECTION
load_dotenv()   #Looks into the .env file you just hid with your .gitignore 
# and injects its keys into your system's environment memory


# GATEWAY CLIENT INSTANTIATION & REROUTING
# Rerouting the AI client to use the Groq API instead of OpenAI's API, and using the API key from our environment variables.
client = OpenAI(    # Spawns a communications portal
    api_key=os.getenv("GROQ_API_KEY"), #  Extracts the requested key out of that environment memory..
    base_url="https://api.groq.com/openai/v1", # Reroutes the communications portal to talk to Groq's API instead of OpenAI's API.
)

# API PAYLOAD TRANSACTION & TEXT GENERATION
#Creates a variable to capture and hold whatever text the AI sends back to your computer.
response = client.chat.completions.create(  # The standard function call to generate a response from a conversational text interface.
    model="openai/gpt-oss-120b",            # a free model on OpenAI
    n=1,                                    # number of responses to generate (its optional)
    messages=[
        {"role": "system", "content": "You are a popular travel guide."},
        {"role": "user",   "content": "Suggest one thing to do in Bangalore."},
        
    ],
)

# DATA EXTRACTION & TERMINAL DISPLAY
print(response.choices[0].message.content) 
# targets the first generated answer and  strips away metadata to isolate raw text and prints it