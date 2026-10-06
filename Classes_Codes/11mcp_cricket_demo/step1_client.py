"""
step1_client.py — talk to the MCP server WITHOUT any LLM.
Shows the raw MCP plumbing: handshake -> list tools -> call a tool.
"""
import asyncio, json, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Start cricket_server.py (found next to this script) with the same Python that runs this script
server = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("cricket_server.py"))])

async def main():
    async with stdio_client(server) as (read, write):          # 1. start the server as a child process
        async with ClientSession(read, write) as session:
            await session.initialize()                          # 2. handshake
            print("STEP 1: Handshake done\n")

            tools = (await session.list_tools()).tools          # 3. tools/list
            print("STEP 2: Server says it has these tools:")
            for t in tools:
                print(f"\n  Tool name   : {t.name}")
                print(f"  Description : {t.description}")
                print(f"  Input schema: {json.dumps(t.inputSchema)}")

            print("\nSTEP 3: Calling get_live_score ourselves (no LLM!)")
            result = await session.call_tool("get_live_score", {"teams": "India vs West Indies"})  # 4. tools/call
            print(result.content[0].text)

asyncio.run(main())