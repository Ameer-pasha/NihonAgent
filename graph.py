import sys
import asyncio
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from state import AgentState
from nodes import (
    agent_node,
    tool_node,
    record_tools_node,
    nudge_node,
    extraction_node,
    should_continue,
    after_tools,
)

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_node("record_tools", record_tools_node)
graph.add_node("nudge", nudge_node)
graph.add_node("extract", extraction_node)

graph.set_entry_point("agent")

# agent -> (tool call?) tools | (answered too early?) nudge | extract
graph.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "nudge": "nudge", "extract": "extract"},
)

# tools -> record what ran -> (bad results?) nudge | back to agent
graph.add_edge("tools", "record_tools")
graph.add_conditional_edges(
    "record_tools",
    after_tools,
    {"nudge": "nudge", "agent": "agent"},
)

graph.add_edge("nudge", "agent")
graph.add_edge("extract", END)

app = graph.compile()


async def run(company_name: str, job_role: str) -> dict:
    return await app.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=f"Research {job_role} jobs at {company_name} in Japan. "
                            f"Company name: {company_name}. Job role: {job_role}."
                )
            ],
            "company_name": company_name,
            "job_role": job_role,
            "search_attempts": 0,
            "tools_used": [],
            "sources": [],
            "low_confidence": False,
            "retry_done": False,
        },
        config={"recursion_limit": 40},
    )


def print_brief(result: dict) -> None:
    print("\n--- TOOLS USED (in order) ---")
    print(result.get("tools_used") or "NONE  <-- the LLM never called an MCP tool")

    print("\n--- FINAL BRIEF ---")
    print("Company:          ", result.get("company_name"))
    print("Role:             ", result.get("job_role"))
    print("Visa Sponsorship: ", result.get("visa_sponsorship"))
    print("Tech Stack:       ", result.get("tech_stack"))
    print("Salary Band:      ", result.get("salary_band"))
    print("Recent News:      ", result.get("recent_news"))
    print("Open Roles:       ", result.get("open_roles"))
    print("Low confidence:   ", result.get("low_confidence"))
    print("Sources:")
    for u in result.get("sources") or []:
        print("  -", u)


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "Fast Retailing"
    role = sys.argv[2] if len(sys.argv) > 2 else "AI Engineer"
    print_brief(asyncio.run(run(company, role)))
