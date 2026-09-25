import json
import os
import sys

import httpx
import redis
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI(title="DeskBuddy Agent")

# Fail LOUDLY and clearly if the key is missing - not with a cryptic traceback
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not API_KEY or API_KEY.startswith("sk-paste"):
    sys.exit(
        "\n [DeskBuddy] OPENAI_API_KEY missing.\n"
        " Fix : cp.env.example .env, put your real key in it, then\n"
        "  docker compose up -d --force-recreate\n"
    )
llm = OpenAI(api_key = API_KEY)

r = redis.Redis(
                host=os.getenv("REDIS_HOST", "redis"), 
                port=6379, 
                decode_responses=True
            )

TOOLS_URL = os.getenv("TOOLS_URL", "http://tools:7000")

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "evaluate a math expression, e.g. '23*47'",
            "parameters": {
                "type": "object",
                "properties": {"expression":{"type" : "string"}},
                "required": ["expression"],
                          },
                    },
    },
    {
            "type": "function",
            "function": {
                "name": "get_datetime",
                "description": "get the current date and time",
                "parameters": {
                    "type": "object", "properties": {}},
            },
    },
    
]

def call_tool(name: str, args: dict) -> dict:
    """Actually execute a tool by calling the tools microservice over HTTP."""
    try:
        if name == "calculator":
            return httpx.post(f"{TOOLS_URL}/calculator", json=args, timeout=10).json()
        if name == "get_datetime":
            return httpx.get(f"{TOOLS_URL}/datetime", timeout=10).json()
        return {"error": f"unknown tool: {name}"}
    except Exception as e:
        return {"error": f"tool call failed: {e}"}

    

class Chat(BaseModel):
    session_id:str
    message: str



@app.get("/")
def health():
    return{
        "status" : "DeskBuddy Agent is live",
        "tools_url" : TOOLS_URL,
        "redis_host" : os.getenv("REDIS_HOST","redis")
    }


def chat(req: Chat):
    key = f"history:{req.session_id}"
    history = [json.loads(m) for m in r.lrange(key, 0, -1)]   # load memory
    history.append({"role": "user", "content": req.message})
    msge = None
    for _ in range(5):                                  # the agent loop
        resp = llm.chat.completions.create(
                                            model="gpt-4o-mini", 
                                            messages=history, 
                                            tools=TOOL_DEFS)
        msg = resp.choices[0].message

        if not msg.tool_calls:                            # no tool needed?
            break                                         # then we're done

        history.append(msg.model_dump(exclude_none=True))
        for tc in msg.tool_calls:                        # run each requested tool
            result = call_tool(tc.function.name, json.loads(tc.function.arguments))
            history.append(
                            {"role": "tool", 
                            "tool_call_id": tc.id,
                            "content": json.dumps(result)
                            }
                        )

    # save memory back to redis, return final answer
    history.append({"role":"assistant","content":msg.content})
    r.delete(key)
    for m in history:
        r.rpush(key, json.dumps(m))

    return {"answer" : msg.content}