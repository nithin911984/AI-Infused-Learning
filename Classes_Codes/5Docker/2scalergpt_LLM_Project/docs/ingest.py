import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env first
load_dotenv()

import chromadb
from chromadb.utils import embedding_functions

# 1. Validate the API Key
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not API_KEY or API_KEY.startswith("sk-paste"):
    sys.exit("[Ingest] OPENAI_API_KEY missing. Put a real key in .env")

# 2. Setup the exact same embedding model as ScalerGPT
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY, model_name="text-embedding-3-small"
)

# 3. Connection details for the Chroma container/server
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

def connect_to_chroma(retries=30, delay=2):
    for attempt in range(1, retries + 1):
        try:
            client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            client.heartbeat()
            print(f"[Ingest] Connected to chroma at {CHROMA_HOST}:{CHROMA_PORT}", flush=True)
            return client
        except Exception as e:
            print(f"[Ingest] Waiting for chroma ({attempt}/{retries}): {type(e).__name__}", flush=True)
            time.sleep(delay)
    sys.exit(f"[Ingest] Could not reach chroma at {CHROMA_HOST}:{CHROMA_PORT}")

def main():
    # Connect to the running Chroma instance
    chroma = connect_to_chroma()
    
    # Get or create the 'notes' collection
    collection = chroma.get_or_create_collection(name="notes", embedding_function=openai_ef)

    # 4. Define the sample texts/documents you want to index
    # (In a real app, you could read these from text or markdown files)
    documents_to_embed = [
        "ScalerGPT is an artificial intelligence teaching assistant engineered to help students learn software development.",
        "To install project dependencies, developers must create a requirements.txt file and run 'pip install -r requirements.txt'.",
        "Environment configurations should be kept safe in a hidden .env file and never committed directly to public Git repositories.",
        "ChromaDB is a developer-focused vector database used for semantic document retrieval inside LLM pipelines."
    ]
    
    # Generate unique IDs for each chunk
    ids = [f"id_{i}" for i in range(len(documents_to_embed))]

    print(f"[Ingest] Preparing to upload {len(documents_to_embed)} documents into Chroma...")

    try:
        # 5. Push data to vector database
        collection.add(
            documents=documents_to_embed,
            ids=ids
        )
        print(f"[Ingest] Success! Total documents now indexed: {collection.count()}", flush=True)
    except Exception as e:
        print(f"[Ingest] Failed to add documents to database: {e}", flush=True)

if __name__ == "__main__":
    main()
