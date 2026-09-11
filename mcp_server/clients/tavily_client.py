import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_api_key = os.getenv("TAVILY_API_KEY")
if not _api_key or _api_key == "your_tavily_api_key_here":
    raise RuntimeError(
        "TAVILY_API_KEY is missing. Copy .env.example to .env and put your real key in it "
        "(https://app.tavily.com)."
    )

client = TavilyClient(api_key=_api_key)
