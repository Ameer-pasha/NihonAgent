from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Shared state that flows through every node of the graph."""

    # ---- Inputs ----
    company_name: str
    job_role: str

    # ---- Extracted brief (filled by extraction_node) ----
    visa_sponsorship: str          # 'yes' | 'no' | 'not mentioned'
    tech_stack: Sequence[str]      # NOTE: was missing before -> LangGraph dropped it -> always None
    salary_band: str
    recent_news: str
    open_roles: Sequence[str]
    sources: Sequence[str]         # URLs collected programmatically from tool outputs

    # ---- Conversation ----
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # ---- Control flow ----
    search_attempts: int           # how many times agent_node has run (loop guard)
    tools_used: Sequence[str]      # names of MCP tools already called
    low_confidence: bool           # True when job search results don't actually mention the company
    retry_done: bool               # True once a broad retry has been forced (so we don't loop forever)
