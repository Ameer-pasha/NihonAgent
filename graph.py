from langgraph.graph import StateGraph, END

from state import AgentState
from nodes import agent_node, tool_node, should_continue


graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("agent")

graph.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "agent": "agent",   # loop back if fields still missing
    "end": END
})

graph.add_edge("tools", "agent")  # after tool runs, go back to agent to decide next step

app = graph.compile()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    result = app.invoke({
        "messages": [HumanMessage(content="Research Rakuten for AI/ML engineer roles — visa sponsorship, tech stack, and salary if available.")],
        "search_attempts": 0
    })

    for msg in result["messages"]:
        print(type(msg).__name__, ":", getattr(msg, "content", msg))