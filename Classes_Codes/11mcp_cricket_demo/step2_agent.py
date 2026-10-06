"""
step2_agent.py — the LLM decides WHICH tool to call and WITH WHAT arguments.
Our code does the actual calling via MCP.

Uses Groq (free API key from https://console.groq.com/keys).
Groq speaks the same API format as OpenAI, so we use the `openai` package
and just point it at Groq's URL.

Usage:
  python step2_agent.py "What is the score in India vs West Indies?"
  python step2_agent.py --no-tools "What is the score in India vs West Indies?"
"""
import asyncio, json, os, re, sys
from pathlib import Path
from openai import OpenAI

# Load GROQ_API_KEY from a .env file sitting next to this script (keeps the key off your screen).
# If python-dotenv isn't installed (e.g. in Colab), we simply skip this and use the environment.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = os.getenv("DEMO_MODEL", "openai/gpt-oss-20b")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# Start cricket_server.py (found next to this script) with the same Python that runs this script
server = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("cricket_server.py"))])


def to_openai_format(mcp_tools):
    """MCP tool list -> the format OpenAI's API expects."""
    return [{
        "type": "function",
        "function": {"name": t.name, "description": t.description or "", "parameters": t.inputSchema},
    } for t in mcp_tools]


def call_llm(llm, kwargs, retries=2):
    """Call the model. Returns (message, None) or (None, error_text).

    Some models (like gpt-oss) were trained with their own built-in browser tool and
    sometimes try to call it even though we never offered it. Groq rejects that with
    'tool_use_failed'. We retry a couple of times, then explain what happened.
    """
    last = None
    for _ in range(retries + 1):
        try:
            return llm.chat.completions.create(**kwargs).choices[0].message, None
        except Exception as e:
            last = str(e)
            if "tool_use_failed" not in last:
                return None, f"API ERROR: {last}"
    m = re.search(r'"name":\s*"([^"]+)"', last or "")
    tool = m.group(1) if m else "a tool"
    return None, (f"MODEL TRIED TO CALL A TOOL WE NEVER GAVE IT ({tool}). "
                  "It knows it needs live data, but it has no way to get it. Try running again.")


async def run_agent(question: str, use_tools: bool = True, verbose: bool = True) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        sys.exit("GROQ_API_KEY is not set. Put it in a .env file next to this script "
                 "(GROQ_API_KEY=gsk_...). Free key: https://console.groq.com/keys")
    llm = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    trace = []      # every tool call the LLM asked for, kept for evals later
    if use_tools:
        system = ("You are a cricket assistant. Use ONLY the functions provided to get live data. "
                  "Do not use any browser or code tools. Be brief.")
    else:
        system = ("You are a cricket assistant. You have NO tools, NO browser and NO internet access. "
                  "Never try to call a tool. Answer only from your own knowledge, in 1-2 sentences.")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = to_openai_format((await session.list_tools()).tools) if use_tools else None

            for _ in range(5):  # safety limit on loop turns
                kwargs = {"model": MODEL, "messages": messages, "temperature": 0}
                if tools:
                    kwargs["tools"] = tools
                reply, error = call_llm(llm, kwargs)
                if error:
                    if verbose:
                        print(f"\n{error}")
                    return {"answer": f"({error})", "trace": trace}

                if not reply.tool_calls:  # LLM gave a final answer
                    if verbose:
                        print(f"\nFINAL ANSWER: {reply.content}")
                    return {"answer": reply.content, "trace": trace}

                # Record the LLM's "prescription" in the conversation (plain dict = works with any provider)
                messages.append({
                    "role": "assistant",
                    "content": reply.content or "",
                    "tool_calls": [{"id": c.id, "type": "function",
                                    "function": {"name": c.function.name, "arguments": c.function.arguments}}
                                   for c in reply.tool_calls],
                })
                for call in reply.tool_calls:
                    args = json.loads(call.function.arguments)
                    trace.append({"tool": call.function.name, "args": args})
                    if verbose:
                        print(f"\nLLM SAYS: please call {call.function.name} with {args}")
                    result = await session.call_tool(call.function.name, args)  # OUR code calls the tool
                    text = result.content[0].text if result.content else "(empty)"
                    if verbose:
                        print(f"TOOL RETURNED: {text}")
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": text})

    return {"answer": "(stopped: too many steps)", "trace": trace}


if __name__ == "__main__":
    args = sys.argv[1:]
    use_tools = "--no-tools" not in args
    question = " ".join(a for a in args if a != "--no-tools") or "What is the score in India vs West Indies?"
    print(f"QUESTION: {question}   (tools {'ON' if use_tools else 'OFF'})")
    asyncio.run(run_agent(question, use_tools))