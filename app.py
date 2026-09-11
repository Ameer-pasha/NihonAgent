# app.py
import os
import traceback
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from graph import run_research
from schemas import CompanyResearchBrief

app = FastAPI(
    title="NihonAgent API",
    description="Autonomous Agent for Japanese Tech Job Market Research (LangGraph + MCP)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "NihonAgent"}


@app.get("/api/diagnose")
async def diagnose_services():
    diagnostics = {}
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                diagnostics["ollama"] = {"status": "CONNECTED", "available_models": models}
            else:
                diagnostics["ollama"] = {"status": "ERROR", "code": resp.status_code}
    except Exception as e:
        diagnostics["ollama"] = {"status": "FAILED", "error": str(e)}

    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000/sse")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            async with client.stream("GET", mcp_url) as resp:
                if resp.status_code in [200, 307, 308]:
                    diagnostics["mcp_server"] = {"status": "CONNECTED"}
                else:
                    diagnostics["mcp_server"] = {"status": "ERROR", "code": resp.status_code}
    except Exception as e:
        diagnostics["mcp_server"] = {"status": "FAILED", "error": str(e)}

    diagnostics["tavily_key_configured"] = bool(os.getenv("TAVILY_API_KEY"))
    return diagnostics


@app.post("/api/research", response_model=CompanyResearchBrief)
async def perform_research(req: ResearchRequest):
    if not req.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        print(f"🚀 Running natural query research for: '{req.query}'", flush=True)
        brief = await run_research(req.query)
        if not brief:
            raise HTTPException(status_code=500, detail="Agent returned empty research brief")
        return brief
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ CRITICAL AGENT ERROR: {error_msg}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NihonAgent — Japan AI Job Intelligence</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        fontFamily: { sans: ['Inter', 'sans-serif'] },
                        colors: {
                            brand: {
                                blue: '#2563eb',
                                blueDark: '#1d4ed8',
                                blueLight: '#dbeafe',
                                blueBg: '#eff6ff',
                            }
                        }
                    }
                }
            }
        </script>
        <style>
            * { -webkit-font-smoothing: antialiased; }
            body {
                font-family: 'Inter', sans-serif;
                background: #ffffff;
                background-image: 
                    radial-gradient(circle at 10% 0%, rgba(37, 99, 235, 0.04) 0%, transparent 40%),
                    radial-gradient(circle at 90% 100%, rgba(37, 99, 235, 0.02) 0%, transparent 40%);
            }
            .grid-bg {
                background-image: 
                    linear-gradient(rgba(0,0,0,0.015) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0,0,0,0.015) 1px, transparent 1px);
                background-size: 30px 30px;
            }
            .search-box {
                box-shadow: 0 16px 32px -12px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.05);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .search-box:focus-within {
                box-shadow: 0 20px 38px -10px rgba(37, 99, 235, 0.12), 0 0 0 2px #2563eb;
                transform: translateY(-1px);
            }
        </style>
    </head>
    <body class="text-black min-h-screen flex flex-col">
        
        <!-- HEADER -->
        <header class="border-b border-gray-100 bg-white/80 backdrop-blur-xl sticky top-0 z-50">
            <div class="max-w-6xl mx-auto w-full px-6 py-4 flex justify-between items-center">
                <div class="flex items-center gap-2.5">
                    <div class="w-9 h-9 bg-black rounded-lg flex items-center justify-center text-white"><i class="fa-solid fa-torii-gate"></i></div>
                    <div><h1 class="text-base font-bold tracking-tight">NihonAgent</h1><p class="text-[10px] text-gray-500 font-medium">Japan Tech Market Intelligence</p></div>
                </div>
                <div class="flex items-center gap-3">
                    <div id="status-badge" class="flex items-center gap-1.5 bg-gray-50 border border-gray-100 px-3.5 py-1.5 rounded-full text-[11px] font-semibold text-gray-600">
                        <span class="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse"></span>Checking status...
                    </div>
                </div>
            </div>
        </header>

        <!-- MAIN HERO & SEARCH -->
        <main class="flex-grow max-w-4xl w-full mx-auto px-6 py-12 flex flex-col justify-center">
            <div class="text-center mb-10">
                <h2 class="text-4xl md:text-5xl font-black tracking-tight mb-3">Ask NihonAgent anything.</h2>
                <p class="text-base text-gray-500 max-w-xl mx-auto font-medium">Search for companies, roles, stacks, or visa status in Japan using free-form natural language.</p>
            </div>

            <!-- SEARCH WRAPPER -->
            <div class="w-full bg-white rounded-2xl search-box p-4 flex flex-col gap-3 mb-6">
                <form id="research-form" class="flex items-center gap-3">
                    <div class="text-gray-400 pl-2"><i class="fa-solid fa-wand-magic-sparkles text-lg"></i></div>
                    <input type="text" id="user-query" placeholder="Ask e.g. AI engineer jobs in Japan with visa sponsorship..." 
                        class="w-full bg-transparent border-0 outline-none text-sm font-medium placeholder-gray-400 py-2 focus:ring-0" required>
                    <button type="submit" id="submit-btn" class="bg-black hover:bg-brand-blue text-white rounded-xl px-5 py-2.5 font-bold text-xs transition flex items-center gap-2 whitespace-nowrap">
                        <span id="btn-text">Launch Agent</span><i id="btn-icon" class="fa-solid fa-arrow-right"></i>
                    </button>
                </form>
            </div>

            <!-- CHIPS / SUGGESTIONS -->
            <div class="flex flex-wrap items-center justify-center gap-2 mb-12">
                <span class="text-xs font-semibold text-gray-400 mr-1">Suggestions:</span>
                <button onclick="applyQuery('AI engineer jobs in Japan with visa sponsorship')" class="text-xs font-medium py-1.5 px-3 rounded-full bg-gray-50 hover:bg-brand-blueBg hover:text-brand-blue border border-gray-100 transition">AI jobs with visa</button>
                <button onclick="applyQuery('Sony Machine Learning engineer tech stack')" class="text-xs font-medium py-1.5 px-3 rounded-full bg-gray-50 hover:bg-brand-blueBg hover:text-brand-blue border border-gray-100 transition">Sony ML Stack</button>
                <button onclick="applyQuery('Mercari AI Engineer jobs and salary bands')" class="text-xs font-medium py-1.5 px-3 rounded-full bg-gray-50 hover:bg-brand-blueBg hover:text-brand-blue border border-gray-100 transition">Mercari Salary</button>
                <button onclick="applyQuery('Rakuten Software Engineer requirements')" class="text-xs font-medium py-1.5 px-3 rounded-full bg-gray-50 hover:bg-brand-blueBg hover:text-brand-blue border border-gray-100 transition">Rakuten Roles</button>
            </div>

            <!-- RESULTS LAYER -->
            <div class="w-full flex flex-col gap-6">
                
                <!-- Loading indicator -->
                <div id="loading-state" class="hidden bg-white border border-gray-100 rounded-2xl p-10 flex-col items-center justify-center text-center shadow-sm">
                    <div class="w-10 h-10 border-4 border-gray-100 border-t-brand-blue rounded-full animate-spin mb-4"></div>
                    <h3 class="text-base font-bold">Researching Tokyo Tech Jobs...</h3>
                    <p class="text-xs text-gray-400 mt-1">Autonomous agent is utilizing FastMCP tools to analyze live job boards.</p>
                </div>

                <!-- Live logs stream inside UI -->
                <div id="logs-wrapper" class="hidden bg-gray-50 border border-gray-100 rounded-xl p-4 font-mono text-xs text-gray-600 flex flex-col gap-1.5 max-h-[160px] overflow-y-auto shadow-inner">
                    <p class="text-gray-400 font-bold uppercase tracking-wider text-[10px] mb-1">Execution Pipeline Logs</p>
                    <div id="logs"></div>
                </div>

                <!-- Structured result card -->
                <div id="results-container" class="hidden flex flex-col gap-5 w-full">
                    
                    <div class="bg-black text-white rounded-2xl p-6 shadow-md relative overflow-hidden">
                        <div class="absolute top-0 right-0 w-48 h-48 bg-brand-blue opacity-25 rounded-full blur-3xl"></div>
                        <div class="relative z-10">
                            <span class="inline-block bg-white/10 text-white/80 text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">Hiring Brief</span>
                            <h2 id="res-company-name" class="text-2xl font-black mt-2 mb-4">Tokyo Jobs Analysis</h2>
                            
                            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-3">
                                    <p class="text-[9px] text-white/50 uppercase font-bold">Visa Sponsorship</p>
                                    <p id="res-visa" class="text-xs font-bold mt-0.5 text-white">-</p>
                                </div>
                                <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-3">
                                    <p class="text-[9px] text-white/50 uppercase font-bold">Salary Band</p>
                                    <p id="res-salary" class="text-xs font-bold mt-0.5 text-emerald-400">-</p>
                                </div>
                                <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-3">
                                    <p class="text-[9px] text-white/50 uppercase font-bold">Matched Positions</p>
                                    <p id="res-role-count" class="text-xs font-bold mt-0.5 text-white">-</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Roles and Stack Grid -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
                            <h3 class="text-xs font-bold uppercase text-gray-400 tracking-wider mb-3 flex items-center gap-1.5"><i class="fa-solid fa-briefcase text-brand-blue"></i> Open Positions</h3>
                            <ul id="res-roles" class="flex flex-col gap-2 text-xs text-gray-700"></ul>
                        </div>
                        <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
                            <h3 class="text-xs font-bold uppercase text-gray-400 tracking-wider mb-3 flex items-center gap-1.5"><i class="fa-solid fa-code text-brand-blue"></i> Tech Stack</h3>
                            <div id="res-stack" class="flex flex-wrap gap-1.5"></div>
                        </div>
                    </div>

                    <!-- News -->
                    <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
                        <h3 class="text-xs font-bold uppercase text-gray-400 tracking-wider mb-2 flex items-center gap-1.5"><i class="fa-solid fa-newspaper text-brand-blue"></i> Market Updates & Initiatives</h3>
                        <p id="res-news" class="text-xs text-gray-600 leading-relaxed"></p>
                    </div>

                    <!-- Sources -->
                    <div class="bg-white border border-gray-100 rounded-2xl p-4 shadow-sm">
                        <h3 class="text-xs font-bold uppercase text-gray-400 tracking-wider mb-2">Sources</h3>
                        <div id="res-sources" class="flex flex-wrap gap-2"></div>
                    </div>

                </div>
            </div>
        </main>

        <!-- FOOTER -->
        <footer class="border-t border-gray-100 py-6 text-center text-xs text-gray-400 font-medium font-mono">
            Powered by LangGraph + FastMCP + Ollama | © 2026 NihonAgent
        </footer>

        <script>
            const form = document.getElementById('research-form');
            const placeholder = document.getElementById('results-placeholder');
            const loading = document.getElementById('loading-state');
            const container = document.getElementById('results-container');
            const logsWrapper = document.getElementById('logs-wrapper');
            const logsDiv = document.getElementById('logs');
            const submitBtn = document.getElementById('submit-btn');
            const btnText = document.getElementById('btn-text');
            const btnIcon = document.getElementById('btn-icon');
            const statusBadge = document.getElementById('status-badge');

            function addLog(msg, color = 'text-gray-600') {
                const time = new Date().toLocaleTimeString();
                logsDiv.innerHTML += `<p class="${color}"><span class="text-gray-400">${time}</span> ${msg}</p>`;
                logsDiv.scrollTop = logsDiv.scrollHeight;
            }

            function applyQuery(query) {
                document.getElementById('user-query').value = query;
                form.dispatchEvent(new Event('submit'));
            }

            async function checkStatus() {
                try {
                    const res = await fetch('/api/diagnose');
                    const data = await res.json();
                    if (data.ollama.status === 'CONNECTED' && data.mcp_server.status === 'CONNECTED') {
                        statusBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span><span class="text-emerald-700">All Systems Online</span>';
                        statusBadge.className = 'flex items-center gap-1.5 bg-emerald-50 border border-emerald-100 px-3.5 py-1.5 rounded-full text-[11px] font-semibold';
                    }
                } catch(e) {}
            }
            checkStatus();

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const query = document.getElementById('user-query').value;

                container.classList.add('hidden');
                loading.classList.remove('hidden');
                loading.classList.add('flex');
                logsWrapper.classList.remove('hidden');
                logsDiv.innerHTML = '';

                submitBtn.disabled = true;
                btnText.textContent = 'Searching...';
                btnIcon.className = 'fa-solid fa-spinner fa-spin';

                addLog(`🔍 Initializing natural language research for: "${query}"`, 'text-brand-blue font-bold');
                addLog('🤖 Orchestrator selecting optimal MCP research path...', 'text-gray-600');

                try {
                    const response = await fetch('/api/research', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query })
                    });

                    const data = await response.json();
                    if (!response.ok) throw new Error(data.detail || 'Server error');

                    addLog('✓ Data successfully compiled and structured!', 'text-emerald-600 font-bold');

                    document.getElementById('res-company-name').textContent = data.company_name;
                    document.getElementById('res-visa').textContent = data.visa_sponsorship || 'Unknown';
                    document.getElementById('res-salary').textContent = data.salary_band || 'N/A';
                    document.getElementById('res-role-count').textContent = (data.open_roles || []).length + ' Matched';
                    document.getElementById('res-news').textContent = data.recent_news || "No specific updates found.";

                    const rolesUl = document.getElementById('res-roles');
                    rolesUl.innerHTML = '';
                    (data.open_roles || []).forEach(r => {
                        rolesUl.innerHTML += `<li class="flex items-start gap-2.5 pb-2.5 border-b border-gray-50 last:border-0"><div class="w-1.5 h-1.5 rounded-full bg-brand-blue mt-1.5 shrink-0"></div><span>${r}</span></li>`;
                    });
                    if ((data.open_roles || []).length === 0) rolesUl.innerHTML = '<li class="text-gray-400 text-xs">No roles found</li>';

                    const stackDiv = document.getElementById('res-stack');
                    stackDiv.innerHTML = '';
                    (data.tech_stack || []).forEach(t => {
                        stackDiv.innerHTML += `<span class="bg-brand-blueBg text-brand-blue border border-brand-blueLight text-[10px] font-bold px-2.5 py-1 rounded-lg">${t}</span>`;
                    });
                    if ((data.tech_stack || []).length === 0) stackDiv.innerHTML = '<span class="text-gray-400 text-xs">No tech stack data</span>';

                    const sourcesDiv = document.getElementById('res-sources');
                    sourcesDiv.innerHTML = '';
                    (data.sources || []).forEach(s => {
                        const short = s.length > 45 ? s.substring(0, 45) + '...' : s;
                        sourcesDiv.innerHTML += `<a href="${s}" target="_blank" class="text-[11px] font-medium bg-gray-50 border border-gray-200 hover:border-brand-blue hover:bg-brand-blueBg hover:text-brand-blue text-gray-500 px-2.5 py-1 rounded-lg transition flex items-center gap-1.5"><i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i> ${short}</a>`;
                    });
                    if ((data.sources || []).length === 0) sourcesDiv.innerHTML = '<span class="text-gray-400 text-xs">No sources available</span>';

                    loading.classList.add('hidden');
                    loading.classList.remove('flex');
                    container.classList.remove('hidden');

                } catch(err) {
                    addLog(`✗ Error during agent execution: ${err.message}`, 'text-red-600 font-bold');
                    loading.classList.add('hidden');
                    loading.classList.remove('flex');
                } finally {
                    submitBtn.disabled = false;
                    btnText.textContent = 'Launch Agent';
                    btnIcon.className = 'fa-solid fa-arrow-right';
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)