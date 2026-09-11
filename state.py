from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Represents the state of an agent."""
    company_name: Annotated[str, "The name of the company associated with the agent."]
    job_role: Annotated[str, "The job role being researched for this company."]
    size: Annotated[str, "The size of the company associated with the agent."]
    location: Annotated[str, "The location of the company associated with the agent."]
    visa_sponsorship: Annotated[str, "Indicates whether the company offers visa sponsorship: 'yes', 'no', or 'not mentioned'."]
    salary_band: Annotated[str, "The salary band for the position associated with the agent."]
    recent_news: Annotated[str, "Recent news or updates related to the company associated with the agent."]
    open_roles: Annotated[Sequence[str], "A list of open roles or job positions available at the company associated with the agent."]
    sources: Annotated[Sequence[str], "A list of sources or references for the information provided in the agent's state."]
    messages: Annotated[Sequence[BaseMessage], add_messages, "A list of messages exchanged between the agent and the user."]

    # Control-flow fields — retry/loop logic ke liye
    search_attempts: Annotated[int, "Number of search/agent loop iterations so far, used to prevent infinite loops."]
    low_confidence: Annotated[bool, "True if the last search result did not clearly match the target company name."]