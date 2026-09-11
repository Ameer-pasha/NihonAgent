# graph.py
import sys
import asyncio
from typing import Literal
from langgraph.graph import StateGraph, START, END

from state import AgentState
from nodes import agent_node, tool_node, extractor_node, evaluator_node
from langchain_core.messages import HumanMessage
from schemas import CompanyResearchBrief


def should_continue_tools(state: AgentState) -> Literal["tools", "extractor"]:
    loops = state.get("loop_count", 0) or 0
    if loops >= 5:
        return "extractor"
        
    messages = state.get("messages", [])
    if not messages:
        return "extractor"
        
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
    return "extractor"


def should_continue_eval(state: AgentState) -> Literal["agent", "__end__"]:
    if state.get("is_complete", True):
        return "__end__"
    return "agent"


# Build State Graph
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.add_node("extractor", extractor_node)
builder.add_node("evaluator", evaluator_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    should_continue_tools,
    {
        "tools": "tools",
        "extractor": "extractor"
    }
)
builder.add_edge("tools", "agent")
builder.add_edge("extractor", "evaluator")
builder.add_conditional_edges(
    "evaluator",
    should_continue_eval,
    {
        "agent": "agent",
        "__end__": END
    }
)

graph = builder.compile()


async def run_research(query: str) -> CompanyResearchBrief:
    """Executes the agent for any free-form natural language query."""
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "brief": None,
        "query": query,
        "loop_count": 0,
        "is_complete": False
    }
    
    final_state = await graph.ainvoke(initial_state)
    return final_state.get("brief", CompanyResearchBrief())