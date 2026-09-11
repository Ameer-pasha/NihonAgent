from langchain_core.tools import tool

try:                      # package was renamed: duckduckgo_search -> ddgs
    from ddgs import DDGS
except ImportError:       # pragma: no cover
    from duckduckgo_search import DDGS


@tool
def duckduckgo_search(query: str) -> dict:
    """Search the web using DuckDuckGo. Useful as a fallback or
    supplementary source when Tavily results are insufficient."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("href"),
                    "snippet": (r.get("body") or "")[:500],
                })
        return {"query": query, "results": results}
    except Exception as e:  # noqa: BLE001
        return {"query": query, "results": [], "error": str(e)}


if __name__ == "__main__":
    print(duckduckgo_search.invoke({"query": "Rakuten AI engineer hiring 2026"}))
