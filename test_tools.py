import asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test():
    mcp_client = MultiServerMCPClient({
        "japan-job-research": {
            "url": "http://localhost:8000/sse",
            "transport": "sse"
        }
    })
    tools = await mcp_client.get_tools()
    print("Tools loaded:", [t.name for t in tools])

    llm = ChatOllama(model="llama3.2", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    response = await llm_with_tools.ainvoke("Search for Fast Retailing AI engineer jobs in Japan")
    print("Tool calls:", response.tool_calls)
    print("Content:", response.content)

asyncio.run(test())