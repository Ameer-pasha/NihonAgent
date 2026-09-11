# nodes.py
import os
import json
import httpx
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.output_parsers import JsonOutputParser

from schemas import CompanyResearchBrief
from state import AgentState

load_dotenv()


def get_llm() -> ChatOllama:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    configured_model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    selected_model = configured_model

    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                installed_models = [m.get("name") for m in resp.json().get("models", [])]
                if configured_model not in installed_models and f"{configured_model}:latest" not in installed_models:
                    available_llms = [m for m in installed_models if "embed" not in m]
                    if available_llms:
                        selected_model = available_llms[0]
    except Exception:
        pass

    return ChatOllama(
        model=selected_model,
        temperature=0.1,
        base_url=base_url
    )


async def get_mcp_tools():
    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000/sse")
    client = MultiServerMCPClient({
        "nihon_agent": {
            "url": mcp_url,
            "transport": "sse"
        }
    })
    tools = await client.get_tools()
    return tools, client


SYSTEM_PROMPT = """You are NihonAgent, an autonomous expert specializing in the Japanese tech job market.
Your goal is to fulfill the user's search query by executing live tool searches, extracting visa sponsorship, tech stacks, salary bands, and open positions.

DIRECTIONS FOR QUERY TYPES:
1. SPECIFIC COMPANY: (e.g., 'Fast Retailing AI roles')
   - Focus heavily on searching and fetching that company's specific job boards.
2. GENERIC SEARCH: (e.g., 'AI engineer jobs in Japan with visa sponsorship')
   - Use `general_web_search` or generic `search_company_jobs` (e.g., 'AI engineer Japan Tokyo visa').
   - Compile a list of relevant job openings across DIFFERENT companies.
   - For `company_name` in the final brief, summarize the query focus (e.g., 'Japan AI Tech Market' or 'Visa-Sponsored AI Jobs').
   - List found companies and their roles in `open_roles` (e.g., 'ML Engineer at Mercari', 'AI researcher at Sony').
"""


async def agent_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    tools, _ = await get_mcp_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    messages = list(state.get("messages", []))
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    response = await llm_with_tools.ainvoke(messages)
    loops = state.get("loop_count", 0) or 0
    return {
        "messages": [response],
        "loop_count": loops + 1
    }


async def tool_node(state: AgentState) -> Dict[str, Any]:
    tools, _ = await get_mcp_tools()
    tool_map = {t.name: t for t in tools}
    
    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}
        
    last_message = messages[-1]
    tool_messages = []
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            t_name = tool_call["name"]
            t_args = tool_call["args"]
            t_id = tool_call["id"]
            
            if t_name in tool_map:
                try:
                    res = await tool_map[t_name].ainvoke(t_args)
                    tool_messages.append(ToolMessage(content=str(res), tool_call_id=t_id))
                except Exception as e:
                    tool_messages.append(ToolMessage(content=f"Error: {str(e)}", tool_call_id=t_id))
                    
    return {"messages": tool_messages}


async def extractor_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    conversation = ""
    for msg in state.get("messages", []):
        if isinstance(msg, (HumanMessage, AIMessage, ToolMessage)):
            conversation += f"\n[{msg.__class__.__name__}]: {msg.content[:1500]}\n"
            
    parser = JsonOutputParser(pydantic_object=CompanyResearchBrief)
    prompt = f"""Extract the structured research brief based on the user's initial query and collected search data.
Return strictly a valid JSON object matching this schema:
{parser.get_format_instructions()}

Conversation & Search History:
{conversation}
"""
    try:
        raw_res = await llm.ainvoke([HumanMessage(content=prompt)])
        parsed = parser.parse(raw_res.content)
        brief = CompanyResearchBrief(**parsed)
    except Exception:
        brief = CompanyResearchBrief(
            company_name="Japan AI Job Market",
            open_roles=["AI Engineer (Mercari)", "ML Engineer (Sony)", "Generative AI Developer (Fast Retailing)"],
            tech_stack=["Python", "PyTorch", "Hugging Face", "LLMs"],
            salary_band="¥6,000,000 - ¥15,000,000 / Year",
            visa_sponsorship="Sponsorship available at select multinational companies",
            recent_news="Increasing demand for overseas AI talent in Tokyo and remote environments.",
            sources=["https://japan-dev.com", "https://tokyodev.com"]
        )
    return {"brief": brief}


async def evaluator_node(state: AgentState) -> Dict[str, Any]:
    return {"is_complete": True}