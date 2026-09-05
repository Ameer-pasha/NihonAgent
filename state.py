from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages



class AgentState(TypedDict):
    """Represents the state of an agent."""
    company_name: Annotated[str, "The name of the company associated with the agent."]
    size: Annotated[str, "The size of the company associated with the agent."]
    location: Annotated[str, "The location of the company associated with the agent."]
    visa_sponsorship: Annotated[bool, "Indicates whether the company offers visa sponsorship."]
    tech_stack: Annotated[Sequence[str], "A list of technologies used by the company associated with the agent."]
    salary_band: Annotated[str, "The salary band for the position associated with the agent."]
    recent_news: Annotated[str, "Recent news or updates related to the company associated with the agent."]
    open_roles: Annotated[Sequence[str], "A list of open roles or job positions available at the company associated with the agent."]
    sources: Annotated[Sequence[str], "A list of sources or references for the information provided in the agent's state."]
    messages: Annotated[Sequence[BaseMessage], add_messages, "A list of messages exchanged between the agent and the user."]
    





































