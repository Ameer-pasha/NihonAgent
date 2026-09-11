import asyncio
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from pydantic import BaseModel, Field
from typing import List

from langchain_mcp_adapters.client import MultiServerMCPClient

from state import AgentState


llm = ChatOllama(
    model="llama3.2",
    temperature=0
)

# MCP client — batata hai kaha se tools milenge
mcp_client = MultiServerMCPClient({
    "japan-job-research": {
        "url": "http://localhost:8000/sse",
        "transport": "sse"
    }
})


async def get_tools():
    """MCP server se available tools fetch karta hai."""
    return await mcp_client.get_tools()


# Tools ko synchronously load karo (module load hote hi ek baar)
tools = asyncio.run(get_tools())

llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)

MAX_SEARCH_ATTEMPTS = 5


def agent_node(state: AgentState):
    print("\n=== DEBUG: Messages going into LLM ===")
    for m in state["messages"]:
        print(type(m).__name__, ":", getattr(m, "content", m))

    response = llm_with_tools.invoke(state["messages"])

    print("\n=== DEBUG: Raw response ===")
    print("Content:", response.content)
    print("Tool calls:", response.tool_calls)
    print("===\n")

    attempts = state.get("search_attempts", 0) + 1

    return {
        "messages": [response],
        "search_attempts": attempts
    }


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]

    # Case 1: LLM tool call chahta hai -> tools chalao
    if last_message.tool_calls:
        attempts = state.get("search_attempts", 0)
        if attempts >= MAX_SEARCH_ATTEMPTS:
            # bahut zyada tool calls ho gaye, force extract karo
            return "extract"
        return "tools"

    # Case 2: LLM ne tool call nahi kiya -> matlab usne apna jawab de diya
    # ab extraction karo, jo bhi info mila hai usi se
    return "extract"


# ---- EXTRACTION NODE (same as before, no change needed) ----

class CompanyBrief(BaseModel):
    """Structured brief extracted from search results."""
    visa_sponsorship: str = Field(description="Whether the company sponsors visas: 'yes', 'no', or 'not mentioned' if unclear from the sources")
    tech_stack: List[str] = Field(description="List of technologies mentioned, empty list if none found")
    salary_band: str = Field(description="Salary range if found, otherwise 'not disclosed'")
    recent_news: str = Field(description="Any recent news or funding info found, otherwise 'not found'")
    open_roles: List[str] = Field(description="Job titles/roles mentioned, empty list if none found")
    sources: List[str] = Field(description="The actual URLs (starting with http) used as evidence — not company names")

extractor_llm = llm.with_structured_output(CompanyBrief)



def extraction_node(state: AgentState):
    # Tool results + agent ke apne text jawab, dono le lo
    relevant_messages = [
        m for m in state["messages"] 
        if isinstance(m, ToolMessage) or (hasattr(m, "content") and m.content)
    ]

    if not relevant_messages:
        return {
            "visa_sponsorship": "not mentioned",
            "tech_stack": [],
            "salary_band": "not disclosed",
            "recent_news": "not found",
            "open_roles": [],
            "sources": []
        }

    combined_text = "\n\n".join(str(m.content) for m in relevant_messages)

    prompt = (
        f"Company: {state.get('company_name')}\n"
        f"Role: {state.get('job_role')}\n\n"
        f"Below is a conversation containing search results and an assistant's summary. "
        f"Extract visa sponsorship status, tech stack, salary band, recent news, and open roles. "
        f"If information is not found, say so clearly rather than guessing.\n\n"
        f"{combined_text}"
    )

    brief = extractor_llm.invoke(prompt)

    return {
        "visa_sponsorship": brief.visa_sponsorship,
        "tech_stack": brief.tech_stack,
        "salary_band": brief.salary_band,
        "recent_news": brief.recent_news,
        "open_roles": brief.open_roles,
        "sources": brief.sources
    }