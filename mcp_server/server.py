import sys
import os

# Project root ko path me daalo, taaki 'mcp_server' package kahin se bhi chalao, mile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP
from mcp_server.tools.web_search_tool import web_search
from mcp_server.tools.company_search import job_board_search
from mcp_server.tools.fetch_page_tool import fetch_page
from mcp_server.tools.duckduckgo_tool import duckduckgo_search

mcp = FastMCP("japan-job-research", host="0.0.0.0", port=8000)

@mcp.tool()
def search_company_jobs(company_name: str, job_role: str) -> dict:
    """Search for AI/ML job postings for a specific company in Japan,
    including visa sponsorship and salary info when available."""
    return job_board_search.invoke({"company_name": company_name, "job_role": job_role})

@mcp.tool()
def general_web_search(query: str) -> dict:
    """Search the web (Tavily) for general company information or news."""
    return web_search.invoke({"query": query})

@mcp.tool()
def fetch_job_page(url: str) -> dict:
    """Fetch and extract text content from a specific job posting URL."""
    return fetch_page.invoke({"url": url})

@mcp.tool()
def duckduckgo_web_search(query: str) -> dict:
    """Alternative web search using DuckDuckGo. Use as a fallback when 
    the primary search (general_web_search) doesn't return enough info."""
    return duckduckgo_search.invoke({"query": query})

if __name__ == "__main__":
    mcp.run(transport="sse")