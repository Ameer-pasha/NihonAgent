# state.py
from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from schemas import CompanyResearchBrief

class AgentState(TypedDict, total=False):
    """Unified state allowing free-form natural language query processing."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    brief: Optional[CompanyResearchBrief]
    query: Optional[str]         # Free-form user prompt
    loop_count: Optional[int]
    is_complete: Optional[bool]