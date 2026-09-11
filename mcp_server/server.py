import os
import json
import httpx
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Explicitly bind to 0.0.0.0 for Docker container networking
mcp = FastMCP(
    name="NihonAgent-MCP",
    host="0.0.0.0",
    port=8000
)
mcp.settings.host = "0.0.0.0"
mcp.settings.port = 8000

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    if not TAVILY_API_KEY:
        return [{"error": "TAVILY_API_KEY is not set in environment."}]
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": max_results
    }
    
    try:
        with httpx.Client(trust_env=False, timeout=25.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "snippet": r.get("content")
                })
            return results
    except Exception as e:
        return [{"error": f"Tavily search failed: {str(e)}"}]


@mcp.tool()
def search_company_jobs(company_name: str, job_role: str = "Software Engineer") -> str:
    """Searches for job openings, salary, tech stack, and visa sponsorship for a specific company in Japan."""
    query = f"{company_name} {job_role} Japan Tokyo careers visa sponsorship tech stack"
    results = tavily_search(query, max_results=6)
    return json.dumps({"query": query, "company_name": company_name, "results": results}, indent=2)


@mcp.tool()
def general_web_search(query: str) -> str:
    """Searches recent news or engineering blogs for tech companies in Japan."""
    results = tavily_search(query, max_results=5)
    return json.dumps({"query": query, "results": results}, indent=2)


@mcp.tool()
def fetch_job_page(url: str) -> str:
    """Fetches text content from a specific careers URL."""
    try:
        with httpx.Client(trust_env=False, timeout=20.0, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            return json.dumps({"url": url, "content_snippet": resp.text[:4000]})
    except Exception as e:
        return json.dumps({"url": url, "error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="sse")