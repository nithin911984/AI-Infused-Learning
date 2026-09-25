import os, sys, time
import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI(title="ScalerGPT")

# Fail LOUDLY and clearly if the key is missing - not with a cryptic traceback
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not API_KEY or API_KEY.startswith("sk-paste"):
    sys.exit("[ScalerGPT] OPENAI_API_KEY missing. Put a real key in .env")

llm = OpenAI(api_key=API_KEY)

# The thin client has no built-in embedder - we must supply one explicitly
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=API_KEY, model_name="text-embedding-3-small")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

def connect_to_chroma(retries=30, delay=2):
    # Chroma takes a few seconds to boot. depends_on only waits for its
    # container to START, not to be READY - so we knock politely and retry.
    for attempt in range(1, retries + 1):
        try:
            client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            client.heartbeat()
            print(f"[ScalerGPT] Connected to chroma at {CHROMA_HOST}:{CHROMA_PORT}", flush=True)
            return client
        except Exception as e:
            print(f"[ScalerGPT] Waiting for chroma ({attempt}/{retries}): {type(e).__name__}", flush=True)
            time.sleep(delay)
    sys.exit(f"[ScalerGPT] Could not reach chroma at {CHROMA_HOST}:{CHROMA_PORT}")

chroma = connect_to_chroma()
collection = chroma.get_or_create_collection(name="notes", embedding_function=openai_ef)

class Question(BaseModel):
    query: str

@app.get("/")
def health():
    return {"status": "ScalerGPT is live 📚", "docs_indexed": collection.count(),
            "chroma_host": CHROMA_HOST, "chroma_port": CHROMA_PORT}

@app.post("/ask")
def ask(q: Question):
    if collection.count() == 0:
        raise HTTPException(status_code=400,
            detail="No documents indexed. Run: docker compose exec app python ingest.py")
    # 1. RETRIEVE - find the 3 most relevant chunks
    hits = collection.query(query_texts=[q.query], n_results=3)
    documents = hits.get("documents") or [[]]
    context = "\n\n---\n\n".join(documents[0])
    # 2. AUGMENT - paste those chunks into the prompt
    system_prompt = ("You are ScalerGPT, a helpful teaching assistant. "
        "Answer using ONLY the context below. If it does not contain the answer, "
        f"say you don't know.\n\nCONTEXT:\n{context}")
    # 3. GENERATE - let the LLM write the final answer
    resp = llm.chat.completions.create(model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": q.query}])
    return {"question": q.query, "answer": resp.choices[0].message.content,
            "sources_used": len(documents[0])}