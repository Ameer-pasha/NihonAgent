from langchain_core.tools import tool
from mcp_server.clients.tavily_client import client

@tool
def web_search(query: str) -> dict:
    """Use this to search the web for general company information,
    funding news, or recent updates."""
    try:
        response = client.search(query, max_results=5)
        results = [
            {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content", "")[:500]}
            for r in response["results"]
        ]
        return {"query": query, "results": results}
    except Exception as e:
        return {"query": query, "results": [], "error": str(e)}