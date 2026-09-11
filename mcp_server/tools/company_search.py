from langchain_core.tools import tool
from mcp_server.clients.tavily_client import client

@tool
def job_board_search(company_name: str, job_role: str) -> dict:
    """Search for job postings, visa sponsorship information, and salary
    details for a specific company and job role, with a focus on Japan.
    Use this only when the company name is known. Do NOT use this for
    general company news or funding information — use web_search instead."""

    query = (
        f'"{company_name}" "{job_role}" '
        f'Japan Tokyo visa sponsorship salary '
        f'site:tokyodev.com OR '
        f'site:wantedly.com OR '
        f'site:linkedin.com/jobs'
    )

    try:
        response = client.search(query, max_results=5, search_depth="advanced")
        results = [
            {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content", "")[:500]}
            for r in response["results"]
        ]
        return {"query": query, "company_name": company_name, "results": results}
    except Exception as e:
        return {"query": query, "company_name": company_name, "results": [], "error": str(e)}