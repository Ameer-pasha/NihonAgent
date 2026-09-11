An autonomous LangGraph agent that researches AI/ML engineering roles at companies in Japan and compiles structured briefs — visa sponsorship status, tech stack, salary bands, and recent company news — pulled live from job boards and web search. Built with tool-calling (Tavily search, scoped job-board queries, page fetching), a self-correcting research loop that retries on missing fields before giving up, and local LLM inference via Ollama.




## How to run (two terminals)

```powershell
# one-time
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # put your real TAVILY_API_KEY inside
ollama pull llama3.2

# Terminal 1 — MCP tool server (must be running BEFORE graph.py)
.\venv\Scripts\Activate.ps1
python mcp_server/server.py

# Terminal 2 — the agent
.\venv\Scripts\Activate.ps1
$env:HTTP_PROXY=''; $env:HTTPS_PROXY=''; $env:ALL_PROXY=''   # only if you have a broken proxy set
python -u graph.py "Fast Retailing" "AI Engineer"
```

`graph.py` prints `--- TOOLS USED (in order) ---` at the end. If it says `NONE`, the LLM never
called an MCP tool. Startup checks will tell you clearly if Ollama, the model, or the MCP server
is not reachable.
