
from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup

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
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return {"url": url, "content": text[:3000], "error": None}
    except Exception as e:
        return {"url": url, "content": "", "error": str(e)}