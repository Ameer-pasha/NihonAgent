from langchain_core.tools import tool
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))




@tool
def web_search(query: str) -> dict:
    """Use this to search the web for general company information,
    funding news, or recent updates. Do NOT use for job postings
    or visa/salary details — use job_board_search for that."""

    try:
        response = client.search(query, max_results=5)

        results = []

        for result in response["results"]:
            results.append({
                "title": result.get("title"),
                "url": result.get("url"),
                # Limit content to reduce unnecessary LLM input.
                "snippet": result.get("content", "")[:500]
            })

        return {
            "query": query,
            "results": results
        }

    except Exception as e:
        return {
            "query": query,
            "results": [],
            "error": str(e)
        }




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
        response = client.search(
            query,
            max_results=5,
            search_depth="advanced"
        )

        results = []

        for result in response["results"]:
            results.append({
                "title": result.get("title"),
                "url": result.get("url"),
                "snippet": result.get("content", "")[:500]
            })

        return {
            "query": query,
            "company_name": company_name,
            "results": results
        }

    except Exception as e:
        return {
            "query": query,
            "company_name": company_name,
            "results": [],
            "error": str(e)
        }

    


@tool
def fetch_page(url: str) -> dict:
    """Fetch and extract the main text content of a specific webpage.
    Use this AFTER web_search or job_board_search has given you a URL,
    when the snippet is too short to find details like exact salary,
    visa sponsorship terms, or full job requirements. Do NOT use this
    to search — only to read a page you already have the URL for."""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Fix character encoding
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise before extracting text
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        return {
            "url": url,
            "content": text[:3000],
            "error": None
        }

    except Exception as e:
        return {
            "url": url,
            "content": "",
            "error": str(e)
        }

        