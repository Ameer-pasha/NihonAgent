import asyncio
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from state import AgentState
from nodes import agent_node, tool_node, extraction_node, should_continue


graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_node("extract", extraction_node)

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "agent": "agent",
        "extract": "extract"
    }
)

graph.add_edge("tools", "agent")
graph.add_edge("extract", END)

app = graph.compile()


async def main():
    result = await app.ainvoke({
        "messages": [
            HumanMessage(content="Search for Fast Retailing AI engineer jobs in Japan")
        ],
        "company_name": "Fast Retailing",
        "job_role": "AI Engineer",
        "search_attempts": 0
    })

    # DEBUG: poori conversation dikhao
    print("\n--- MESSAGE TRACE ---")
    for msg in result["messages"]:
        print(type(msg).__name__, ":", getattr(msg, "content", "")[:200])
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("   TOOL CALLS:", msg.tool_calls)

    print("\n--- FINAL BRIEF ---")
    print("Visa Sponsorship:", result.get("visa_sponsorship"))
    print("Tech Stack:", result.get("tech_stack"))
    print("Salary Band:", result.get("salary_band"))
    print("Recent News:", result.get("recent_news"))
    print("Open Roles:", result.get("open_roles"))
    print("Sources:", result.get("sources"))


if __name__ == "__main__":
    asyncio.run(main())





