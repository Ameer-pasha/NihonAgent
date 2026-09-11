import os
import re
import sys
import json
import asyncio
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_mcp_adapters.client import MultiServerMCPClient

from state import AgentState

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")

MAX_SEARCH_ATTEMPTS = 6   # hard cap on agent-node iterations (loop guard)
MIN_TOOL_CALLS = 2        # don't let the LLM "answer" before at least this many tools ran

llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)


# ---------------------------------------------------------------------------
# Tool loading (from the MCP server) with friendly pre-flight errors
# ---------------------------------------------------------------------------
def _die(msg: str) -> None:
    print("\n" + "=" * 70, file=sys.stderr)
    print("STARTUP ERROR", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(msg, file=sys.stderr)
    print("=" * 70 + "\n", file=sys.stderr)
    sys.exit(1)


def _check_ollama() -> None:
    import httpx
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
    except Exception as e:  # noqa: BLE001
        _die(
            f"Ollama is not reachable at {OLLAMA_BASE_URL} ({e}).\n"
            f"Start it with:   ollama serve\n"
            f"and make sure the model exists:   ollama pull {OLLAMA_MODEL}"
        )
    names = [m.get("name", "") for m in r.json().get("models", [])]
    if not any(n == OLLAMA_MODEL or n.startswith(OLLAMA_MODEL + ":") for n in names):
        _die(
            f"Model '{OLLAMA_MODEL}' is not installed in Ollama (found: {names}).\n"
            f"Run:   ollama pull {OLLAMA_MODEL}"
        )


async def _load_tools():
    client = MultiServerMCPClient({
        "japan-job-research": {"url": MCP_SERVER_URL, "transport": "sse"}
    })
    try:
        return await asyncio.wait_for(client.get_tools(), timeout=15)
    except Exception as e:  # noqa: BLE001
        _die(
            f"Could not connect to the MCP server at {MCP_SERVER_URL} ({type(e).__name__}: {e}).\n"
            f"Start it FIRST in a separate terminal (with the venv activated):\n"
            f"    python mcp_server/server.py\n"
            f"then run graph.py again."
        )


if os.getenv("SKIP_OLLAMA_CHECK") != "1":
    _check_ollama()
tools = asyncio.run(_load_tools())
if not tools:
    _die("MCP server responded but exposed 0 tools. Check mcp_server/server.py.")
print(f"[nodes] MCP tools loaded: {[t.name for t in tools]}")

llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)


# ---------------------------------------------------------------------------
# System prompt — without this the model did ONE search and then "answered".
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are NihonAgent, a research agent that builds a hiring brief about ONE
specific company in Japan for ONE job role. You can only learn things by calling tools.
Never answer from memory.

Research plan — call the tools in this order, one at a time:
1. search_company_jobs(company_name, job_role) -> job postings, visa, salary.
2. general_web_search("<company> engineering tech stack") -> technologies used.
3. general_web_search("<company> news 2026") -> recent news / funding.
4. If a result URL clearly belongs to the target company's job posting, call
   fetch_job_page(url) to read the full posting.
5. If a search returned nothing useful, try duckduckgo_web_search with a rephrased query.

Rules:
- Every tool call must include the exact company name given by the user.
- Ignore results about OTHER companies. Do not present them as the target company's jobs.
- Only after the research plan is complete, reply with a short plain-text summary
  (visa sponsorship, tech stack, salary band, recent news, open roles) citing the URLs you used.
- If something was not found, say "not found" — do not guess.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
URL_RE = re.compile(r"https?://[^\s\"'<>\\\]\)]+")


def _tool_message_text(m: ToolMessage) -> str:
    """MCP tool results arrive as a list of content blocks; flatten to text."""
    c = m.content
    if isinstance(c, list):
        return "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in c
        )
    return str(c)


def _mentions_company(text: str, company: str) -> bool:
    if not company:
        return True
    tokens = [t for t in re.split(r"\W+", company.lower()) if len(t) > 2]
    text_l = text.lower()
    return all(t in text_l for t in tokens) if tokens else True


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def agent_node(state: AgentState):
    messages = list(state["messages"])
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    print("\n=== agent_node: calling LLM ===")
    for m in messages[-3:]:
        preview = (
            _tool_message_text(m) if isinstance(m, ToolMessage) else str(m.content)
        )
        print(f"  {type(m).__name__}: {preview[:200]!r}")

    response: AIMessage = llm_with_tools.invoke(messages)

    print("  -> tool_calls:", [tc["name"] for tc in (response.tool_calls or [])])
    if response.content:
        print("  -> content:", str(response.content)[:300])

    return {
        "messages": [response],
        "search_attempts": state.get("search_attempts", 0) + 1,
    }


def record_tools_node(state: AgentState):
    """Runs right after the ToolNode: tracks which tools ran, collects URLs,
    and flags low-confidence job results (results that never mention the company)."""
    company = state.get("company_name", "")
    used = list(state.get("tools_used", []))
    sources = list(state.get("sources", []))
    low_conf = state.get("low_confidence", False)

    # Walk back over the most recent consecutive ToolMessages
    for m in reversed(state["messages"]):
        if not isinstance(m, ToolMessage):
            break
        used.append(m.name or "unknown")
        text = _tool_message_text(m)
        for u in URL_RE.findall(text):
            if u not in sources:
                sources.append(u)
        if m.name == "search_company_jobs":
            try:
                data = json.loads(text)
                results = data.get("results", [])
            except Exception:  # noqa: BLE001
                results = []
            matching = [
                r for r in results
                if _mentions_company(f"{r.get('title','')} {r.get('url','')} {r.get('snippet','')}", company)
            ]
            low_conf = len(matching) == 0
            print(f"[record_tools] search_company_jobs: {len(results)} results, "
                  f"{len(matching)} mention '{company}' -> low_confidence={low_conf}")

    return {"tools_used": used, "sources": sources, "low_confidence": low_conf}


def nudge_node(state: AgentState):
    """Self-correction: the LLM tried to stop too early or the job search missed
    the company. Push it back into research with an explicit instruction."""
    company = state.get("company_name", "")
    role = state.get("job_role", "")
    used = set(state.get("tools_used", []))

    if state.get("low_confidence") and not state.get("retry_done"):
        text = (
            f"The job-board results did not mention {company} at all. "
            f'Call general_web_search with the query "{company} {role} careers Japan" '
            f'and then duckduckgo_web_search with "{company} recruit engineer". '
            f"Do not summarise yet."
        )
    else:
        missing = []
        if "search_company_jobs" not in used:
            missing.append(f'search_company_jobs(company_name="{company}", job_role="{role}")')
        if "general_web_search" not in used:
            missing.append(f'general_web_search(query="{company} tech stack news")')
        text = (
            "You have not finished the research plan. Call the next tool now: "
            + (missing[0] if missing else f'general_web_search(query="{company} {role}")')
            + ". Do not summarise yet."
        )
    print(f"[nudge] {text}")
    return {"messages": [HumanMessage(content=text)], "retry_done": True}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    attempts = state.get("search_attempts", 0)
    used = state.get("tools_used", [])

    if attempts >= MAX_SEARCH_ATTEMPTS:
        return "extract"

    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"

    # LLM produced a final answer. Is the research actually done?
    if len(used) < MIN_TOOL_CALLS and not state.get("retry_done"):
        return "nudge"
    if state.get("low_confidence") and not state.get("retry_done"):
        return "nudge"
    return "extract"


def after_tools(state: AgentState) -> str:
    """After tools ran: retry once if job search clearly missed the company."""
    if state.get("low_confidence") and not state.get("retry_done"):
        return "nudge"
    return "agent"


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
class CompanyBrief(BaseModel):
    """Structured brief extracted from search results."""
    visa_sponsorship: str = Field(description="'yes', 'no', or 'not mentioned'")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies explicitly named in the sources")
    salary_band: str = Field(default="not disclosed", description="Salary range if found, else 'not disclosed'")
    recent_news: str = Field(default="not found", description="Recent news / funding if found, else 'not found'")
    open_roles: List[str] = Field(default_factory=list, description="Job titles at the TARGET company only")


extractor_llm = llm.with_structured_output(CompanyBrief)

EMPTY_BRIEF = {
    "visa_sponsorship": "not mentioned",
    "tech_stack": [],
    "salary_band": "not disclosed",
    "recent_news": "not found",
    "open_roles": [],
}


def extraction_node(state: AgentState):
    company = state.get("company_name", "")
    role = state.get("job_role", "")

    chunks = []
    for m in state["messages"]:
        if isinstance(m, ToolMessage):
            chunks.append(f"[TOOL {m.name}]\n{_tool_message_text(m)[:4000]}")
        elif isinstance(m, AIMessage) and m.content and not m.tool_calls:
            chunks.append(f"[ASSISTANT SUMMARY]\n{m.content}")

    sources = list(state.get("sources", []))
    if not chunks:
        return {**EMPTY_BRIEF, "sources": sources}

    prompt = (
        f"Target company: {company}\nTarget role: {role}\n\n"
        f"Below are raw tool outputs and an assistant summary. Extract a brief ONLY about "
        f"{company}. Results about other companies must be ignored. If a field is not "
        f"explicitly supported by the text, use 'not mentioned' / 'not disclosed' / "
        f"'not found' / empty list. Never invent values.\n\n"
        + "\n\n".join(chunks)
    )

    try:
        brief = extractor_llm.invoke(prompt)
        data = brief.model_dump()
    except Exception as e:  # noqa: BLE001
        print(f"[extraction] structured output failed ({e}); returning empty brief")
        data = dict(EMPTY_BRIEF)

    if state.get("low_confidence") and data.get("open_roles"):
        # Job board never mentioned the company: don't attribute other companies' roles to it.
        data["open_roles"] = [r for r in data["open_roles"] if _mentions_company(r, company)]

    return {**data, "sources": sources}
