from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode

from tool import web_search, job_board_search, fetch_page
from state import AgentState


llm = ChatOllama(
    model="llama3.2",
    temperature=0
)

tools = [
    web_search,
    job_board_search,
    fetch_page,
]

llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools)

MAX_SEARCH_ATTEMPTS = 5


def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])

    # increment attempt counter each time the agent takes a turn
    attempts = state.get("search_attempts", 0) + 1

    return {
        "messages": [response],
        "search_attempts": attempts
    }


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]

    # Case 1: LLM wants to call a tool -> go run it
    if last_message.tool_calls:
        return "tools"

    # Case 2: no tool call -> check if we actually have enough info
    required_fields = ["visa_sponsorship", "tech_stack", "salary_band"]
    missing = [f for f in required_fields if not state.get(f)]

    attempts = state.get("search_attempts", 0)

    if missing and attempts < MAX_SEARCH_ATTEMPTS:
        # not enough info yet, but LLM stopped calling tools —
        # nudge it to keep searching instead of ending prematurely
        return "agent"

    return "end"