from langchain_core.tools import tool
from mcp_server.clients.tavily_client import client


@tool
def job_board_search(company_name: str, job_role: str) -> dict:
    """Search for job postings, visa sponsorship information, and salary
    details for a specific company and job role, with a focus on Japan.
    Use this only when the company name is known. Do NOT use this for
    general company news or funding information — use web_search instead."""

    # Two-pass search: first a precise query, then a broader one if the
    # first pass returned nothing that actually mentions the company.
    queries = [
        f'"{company_name}" "{job_role}" Japan careers visa sponsorship salary',
        f'{company_name} {job_role} job Tokyo',
    ]
    company_l = company_name.lower()

    last_error = None
    for query in queries:
        try:
            response = client.search(query, max_results=8, search_depth="advanced")
        except Exception as e:  # noqa: BLE001
            last_error = str(e)
            continue
        results = [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": (r.get("content") or "")[:600],
                "mentions_company": company_l in (
                    f"{r.get('title','')} {r.get('url','')} {r.get('content','')}".lower()
                ),
            }
            for r in response.get("results", [])
        ]
        # Put results that actually mention the company first
        results.sort(key=lambda r: not r["mentions_company"])
        if any(r["mentions_company"] for r in results):
            return {"query": query, "company_name": company_name, "results": results[:5]}
        fallback = results

    return {
        "query": queries[-1],
        "company_name": company_name,
        "results": fallback[:5] if last_error is None else [],
        "warning": f"No result explicitly mentioned '{company_name}'." if last_error is None else None,
        "error": last_error,
    }
