<div align="center">

# 🇯🇵 NihonAgent

### Autonomous AI Agent for Japanese Tech Job Market Intelligence

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-orange?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-purple?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br>

> *An end-to-end autonomous AI agent that researches Japanese tech companies in real-time and generates structured hiring intelligence briefs — visa sponsorship, tech stack, salary bands, and open positions — powered by LangGraph state machines, Model Context Protocol (MCP) tool servers, and local LLM inference via Ollama.*

<br>

[🚀 Quick Start](#-quick-start) · [🏗️ Architecture](#️-architecture) · [📡 API Reference](#-api-reference) · [🐳 Docker](#-docker-deployment) · [📖 Documentation](#-detailed-documentation)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#️-architecture)
- [Tech Stack](#-tech-stack)
- [How It Works](#-how-it-works-step-by-step)
- [Quick Start](#-quick-start)
- [Docker Deployment](#-docker-deployment)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Self-Correcting Agent Loop](#-self-correcting-agent-loop)
- [MCP Tool Server](#-mcp-tool-server)
- [Frontend Dashboard](#-frontend-dashboard)
- [Performance Optimization](#-performance-optimization)
- [Troubleshooting](#-troubleshooting)
- [Future Roadmap](#-future-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

**NihonAgent** is a fully autonomous, multi-step AI research agent purpose-built for the Japanese technology job market. Unlike traditional chatbots that rely on stale training data, NihonAgent connects to **live internet sources** through a decoupled **Model Context Protocol (MCP)** tool server, executes real-time searches via **Tavily AI Search API**, scrapes job listing pages, and synthesizes verified, structured intelligence briefs.

### The Problem It Solves

Searching for tech jobs in Japan as an international applicant involves checking dozens of fragmented sources — Japan Dev, TokyoDev, Daijob, LinkedIn, company career pages — each with different formats and languages. NihonAgent automates this entire workflow into a **single natural language query**.

### Example Queries

| Query | What the Agent Does |
|-------|-------------------|
| *"AI engineer jobs in Japan with visa sponsorship"* | Searches across multiple job boards, filters for visa-eligible roles, compiles salary & stack data |
| *"Sony Machine Learning engineer tech stack"* | Targets Sony's career pages, scrapes specific listings, extracts required technologies |
| *"Mercari backend developer salary range"* | Fetches compensation data from Japan Dev and Glassdoor snippets |
| *"Fast Retailing generative AI roles Tokyo"* | Finds Uniqlo parent company's AI division openings at Ariake HQ |

---

## ✨ Key Features

### 🧠 Autonomous Multi-Step Reasoning
- Built on **LangGraph** state machine with conditional routing
- Agent autonomously decides which tools to call, when to search, and when to compile results
- No hardcoded search pipelines — the LLM dynamically plans its research strategy

### 🔌 Model Context Protocol (MCP) Native
- Tools run as a **standalone FastMCP server** over SSE (Server-Sent Events)
- Decoupled architecture: swap Ollama for Claude, GPT-4, or any LLM without touching tools
- Three production tools: `search_company_jobs`, `general_web_search`, `fetch_job_page`

### 🔄 Self-Correcting Research Loop
- Evaluator node checks output completeness after each extraction
- If tech stack or salary data is missing, the agent automatically triggers refined sub-queries
- Recursion guard prevents infinite loops (max 2-5 configurable turns)

### 🌐 Real-Time Live Data
- Connected to **Tavily AI Search API** for live web results
- Web page scraper fetches raw content from career URLs
- No stale training data — every brief is generated from current job market information

### 🎨 Modern Interactive Dashboard
- Clean, minimalist **Vercel/Linear-inspired** UI (White + Black + Blue)
- Single natural language search bar with suggestion chips
- Live execution pipeline logs visible in the browser
- Responsive design for desktop and mobile

### 🐳 One-Click Docker Deployment
- Full system containerized with `docker-compose.yml`
- Two services: MCP Server + FastAPI Agent API
- Cross-platform: works on Windows, macOS, and Linux identically

### 🔒 Privacy-First Local AI
- All LLM inference runs **locally via Ollama** (no data sent to OpenAI/Anthropic)
- Your search queries and company research stay on your machine
- Only Tavily search API calls leave the network

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER (Browser / API Client)                     │
│                    "AI engineer jobs in Japan with visa"                 │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ HTTP POST /api/research
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FASTAPI WEB SERVER (Port 5000)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐                  │
│  │ /health     │  │ /api/diagnose│  │ /api/research │  ← Core Endpoint │
│  │ (GET)       │  │ (GET)        │  │ (POST)        │                  │
│  └─────────────┘  └──────────────┘  └───────┬───────┘                  │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  🎨 Embedded Frontend Dashboard (Tailwind CSS + Vanilla JS) │        │
│  └─────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ Calls run_research()
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH STATE MACHINE                              │
│                                                                         │
│   ┌──────────┐    Tool Call?    ┌──────────┐                            │
│   │  AGENT   │ ────── YES ────▶ │  TOOLS   │                            │
│   │  NODE    │                  │  NODE    │                            │
│   │ (Ollama) │ ◀──────────────── │ (MCP)    │                            │
│   └────┬─────┘   Tool Results   └────┬─────┘                            │
│        │ No more calls               │                                  │
│        ▼                             │                                  │
│   ┌──────────┐                       │                                  │
│   │EXTRACTOR │ ◀─────────────────────┘                                  │
│   │  NODE    │  (Pydantic JSON Parser)                                  │
│   └────┬─────┘                                                          │
│        ▼                                                                │
│   ┌──────────┐                                                          │
│   │EVALUATOR │ ── Complete? ──▶ END (Return Brief)                      │
│   │  NODE    │ ── Missing?  ──▶ Back to AGENT (Retry)                   │
│   └──────────┘                                                          │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ SSE Protocol (HTTP)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 MCP TOOL SERVER (FastMCP - Port 8000)                    │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │search_company_   │  │general_web_      │  │fetch_job_page    │       │
│  │jobs()            │  │search()          │  │()                │       │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │
│           │                     │                      │                │
│           ▼                     ▼                      ▼                │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │              TAVILY AI SEARCH API (Live Web)                │        │
│  └─────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ Local HTTP (11434)
┌─────────────────────────────────┴───────────────────────────────────────┐
│                    OLLAMA LOCAL LLM SERVER                              │
│              (Llama 3.2 / Qwen 2.5 / Mistral / Phi-3)                  │
│                    Auto-detects available models                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | LangGraph 1.2+ | State machine for multi-step agent reasoning |
| **LLM Inference** | Ollama (Llama 3.2) | Local, private AI model execution |
| **Tool Protocol** | FastMCP (MCP Standard) | Decoupled tool server over SSE |
| **Web Search** | Tavily AI Search API | Real-time internet search results |
| **Web Scraping** | HTTPX + BeautifulSoup | Job page content extraction |
| **Backend API** | FastAPI 0.141+ | REST API with async support |
| **Frontend** | Tailwind CSS + Vanilla JS | Embedded minimalist dashboard |
| **Data Validation** | Pydantic v2 | Strict JSON schema enforcement |
| **Containerization** | Docker + Docker Compose | One-click deployment |
| **Language** | Python 3.12 | Core runtime |

---

## 🔄 How It Works (Step-by-Step)

### Phase 1: User Input
```
User types: "AI engineer jobs in Japan with visa sponsorship"
```
The query is sent via `POST /api/research` to the FastAPI server.

### Phase 2: LangGraph Initialization
- The `AgentState` is initialized with the user's query, loop counter, and empty brief.
- The graph starts at the `agent_node`.

### Phase 3: Agent Reasoning (Ollama LLM)
- The LLM receives the query + system prompt + available MCP tools.
- It autonomously decides: *"I should call `general_web_search` with this query."*
- A `tool_call` is emitted in the response.

### Phase 4: Tool Execution (MCP Server)
- The `tool_node` receives the tool call and connects to the MCP server at `http://mcp-server:8000/sse`.
- The MCP server executes `general_web_search()` which calls the Tavily API.
- Live search results (titles, URLs, snippets) are returned as JSON.

### Phase 5: Second Agent Pass
- The LLM reads the search results.
- It may decide to call `fetch_job_page()` to scrape a specific career URL for detailed tech stack info.
- Or it may decide it has enough data and stop calling tools.

### Phase 6: Structured Extraction
- The `extractor_node` takes the full conversation history.
- It prompts the LLM to output a strict JSON object matching the `CompanyResearchBrief` Pydantic schema.
- Fields: `company_name`, `open_roles`, `tech_stack`, `salary_band`, `visa_sponsorship`, `recent_news`, `sources`.

### Phase 7: Evaluation & Self-Correction
- The `evaluator_node` checks if the brief has complete data.
- If critical fields are missing and loop count < max, it routes back to `agent_node` for a retry.
- Otherwise, it marks `is_complete = True` and the graph terminates.

### Phase 8: Response
- The structured `CompanyResearchBrief` is returned to FastAPI.
- The frontend renders a beautiful dark hero card with visa, salary, roles, tech stack chips, news, and source links.

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Installation |
|------------|---------|-------------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Ollama | Latest | [ollama.com](https://ollama.com/download) |
| Docker Desktop | Latest | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Tavily API Key | Free tier | [tavily.com](https://app.tavily.com/) |

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ameer-pasha/NihonAgent.git
cd NihonAgent
```

### Step 2: Environment Setup

Create a `.env` file in the project root:

```env
TAVILY_API_KEY=tvly-your-api-key-here
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://host.docker.internal:11434
MCP_SERVER_URL=http://mcp-server:8000/sse
```

### Step 3: Pull Ollama Model

```bash
ollama pull llama3.2:latest
```

> **Note:** You can also use `qwen2.5:7b`, `mistral`, or `phi3:mini`. The agent auto-detects available models.

### Step 4: Run with Docker (Recommended)

```bash
docker compose up --build -d
```

### Step 5: Open the Dashboard

Navigate to **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🐳 Docker Deployment

### Architecture

The Docker setup consists of **2 containers** on a shared bridge network:

| Container | Port | Purpose |
|-----------|------|---------|
| `nihon_mcp_server` | 8000 | FastMCP tool server (Tavily search, web scraping) |
| `nihon_agent_api` | 5000 | FastAPI web server + LangGraph agent + Frontend UI |

### Commands Reference

```bash
# Build and start all services
docker compose up --build -d

# View live logs
docker compose logs -f

# View logs for specific service
docker compose logs nihon-api --tail=50

# Check container status
docker compose ps

# Stop all services
docker compose down

# Rebuild after code changes
docker compose down && docker compose up --build -d
```

### Docker Compose Configuration

```yaml
services:
  mcp-server:
    build: .
    command: python mcp_server/server.py
    ports: ["8000:8000"]
    env_file: .env
    networks: [nihon-network]

  nihon-api:
    build: .
    command: uvicorn app:app --host 0.0.0.0 --port 5000
    ports: ["5000:5000"]
    env_file: .env
    depends_on: [mcp-server]
    extra_hosts: ["host.docker.internal:host-gateway"]
    networks: [nihon-network]

networks:
  nihon-network:
    driver: bridge
```

### Ollama Host Access (Windows)

Docker containers access the host machine's Ollama server via `host.docker.internal`. On Windows, ensure Ollama allows external connections:

```powershell
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
```

---

## 📡 API Reference

### Base URL
```
http://localhost:5000
```

### Interactive Swagger Docs
```
http://localhost:5000/docs
```

---

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "NihonAgent"
}
```

---

### `GET /api/diagnose`
Diagnoses connectivity to Ollama and MCP Server.

**Response:**
```json
{
  "ollama": {
    "status": "CONNECTED",
    "available_models": ["llama3.2:latest", "nomic-embed-text:latest"]
  },
  "mcp_server": {
    "status": "CONNECTED"
  },
  "tavily_key_configured": true
}
```

---

### `POST /api/research`
Triggers the autonomous research agent.

**Request Body:**
```json
{
  "query": "AI engineer jobs in Japan with visa sponsorship"
}
```

**Response (200 OK):**
```json
{
  "company_name": "Japan AI Tech Market",
  "open_roles": [
    "AI Engineer at Mercari",
    "ML Engineer at Sony",
    "Generative AI Developer at Fast Retailing"
  ],
  "tech_stack": ["Python", "PyTorch", "Hugging Face", "AWS", "Docker"],
  "salary_band": "¥6,000,000 - ¥15,000,000 / Year",
  "visa_sponsorship": "Available at select multinational companies for overseas applicants",
  "recent_news": "Increasing demand for LLM and generative AI talent in Tokyo.",
  "sources": [
    "https://japan-dev.com/jobs",
    "https://tokyodev.com/jobs"
  ]
}
```

**Error Response (500):**
```json
{
  "detail": "Agent Error: ResponseError: model not found"
}
```

---

## 📁 Project Structure

```
NihonAgent/
├── app.py                  # FastAPI server + Embedded HTML Dashboard
├── graph.py                # LangGraph state machine compilation + run_research()
├── nodes.py                # Agent, Tool, Extractor, Evaluator node functions
├── state.py                # AgentState TypedDict definition
├── schemas.py              # Pydantic CompanyResearchBrief model
├── requirements.txt        # Python dependencies (cross-platform)
├── Dockerfile              # Multi-stage Python 3.12 slim image
├── docker-compose.yml      # Two-service orchestration (MCP + API)
├── .dockerignore           # Excludes venv, __pycache__, .env from image
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── mcp_server/
│   └── server.py           # FastMCP tool server (Tavily + Web Scraper)
├── README.md               # This file
└── venv/                   # Local virtual environment (not in Docker)
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TAVILY_API_KEY` | *Required* | Your Tavily AI Search API key |
| `OLLAMA_MODEL` | `llama3.2:latest` | Ollama model name for inference |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama server URL |
| `MCP_SERVER_URL` | `http://mcp-server:8000/sse` | MCP tool server SSE endpoint |

### Model Auto-Detection

The agent automatically detects which models are installed in Ollama. If the configured `OLLAMA_MODEL` is not found, it falls back to the first available non-embedding model. This prevents `404 Not Found` errors when switching between machines.

---

## 🔄 Self-Correcting Agent Loop

NihonAgent implements a **self-correcting research loop** that validates output quality before returning results:

```
Agent → Tools → Agent → Extractor → Evaluator
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                    Data Complete?            Data Missing?
                          │                       │
                          ▼                       ▼
                        END                  Agent (Retry)
                                              (Max 2-5 loops)
```

### Loop Guard Configuration

In `graph.py`, the `should_continue_tools()` function enforces a maximum loop count:

```python
if loops >= 2:  # Configurable: 2 for speed, 5 for depth
    return "extractor"
```

- **2 loops**: Fast mode (~5-10 seconds). One search + one extraction.
- **5 loops**: Deep mode (~20-30 seconds). Multiple searches + page scraping + refinement.

---

## 🔌 MCP Tool Server

The MCP server runs as a **standalone process** on port 8000, exposing three tools over the Server-Sent Events (SSE) transport protocol.

### Available Tools

#### 1. `search_company_jobs(company_name, job_role)`
Searches for targeted company job listings in Japan.

```python
search_company_jobs(company_name="Sony", job_role="AI Engineer")
# Returns: JSON with titles, URLs, and snippets from Tavily
```

#### 2. `general_web_search(query)`
Performs a broad web search for news, blogs, or general information.

```python
general_web_search(query="Japan AI engineer visa sponsorship 2025")
# Returns: JSON with relevant web results
```

#### 3. `fetch_job_page(url)`
Scrapes raw text content from a specific job listing URL.

```python
fetch_job_page(url="https://japan-dev.com/jobs/12345")
# Returns: JSON with page content snippet (truncated to 1500 chars)
```

### Why MCP?

The **Model Context Protocol** is an open standard (by Anthropic) that decouples AI tools from the LLM. Benefits:

- **Framework Agnostic**: Works with LangChain, CrewAI, AutoGen, or raw API calls
- **Hot Swappable**: Change LLM providers without touching tool code
- **Scalable**: Add new tools without modifying the agent graph
- **Production Ready**: SSE transport supports streaming and reconnection

---

## 🎨 Frontend Dashboard

The embedded frontend is a **single-page application** served directly by FastAPI at `/`.

### Design Philosophy
- **Vercel/Linear-inspired** minimalist aesthetic
- **White + Black + Electric Blue** color palette
- **Inter** typeface for clean readability
- **Zero dependencies**: Pure Tailwind CSS + Vanilla JavaScript

### Features
| Feature | Description |
|---------|-------------|
| Natural Language Search | Single input field for free-form queries |
| Suggestion Chips | One-click popular search queries |
| Live Pipeline Logs | Real-time agent execution trace in the browser |
| System Diagnostics | Auto-checks Ollama + MCP connectivity on page load |
| Responsive Layout | Works on desktop, tablet, and mobile |
| Loading Animations | Smooth spinner + progress step indicators |
| Result Cards | Dark hero card + grid layout for roles, stack, news, sources |

---

## ⚡ Performance Optimization

### Latency Breakdown (Typical Query)

| Phase | Time | Optimization Applied |
|-------|------|---------------------|
| MCP SSE Connection | ~0.5s | Container network bridge |
| Tavily Search API | ~1.5s | `search_depth: basic`, `max_results: 3` |
| Ollama Tool Selection | ~2-3s | `temperature: 0.0`, concise system prompt |
| Ollama Extraction | ~2-3s | Truncated context (1000 chars per message) |
| JSON Parsing | ~0.5s | Pydantic with fallback |
| **Total** | **~7-10s** | |

### Optimization Techniques Used

1. **Context Truncation**: Tool outputs limited to 800-1500 characters to reduce Ollama token processing time
2. **Basic Search Depth**: Tavily `search_depth: basic` is 3x faster than `advanced`
3. **Strict Loop Guard**: Max 2 agent turns prevents redundant LLM calls
4. **Zero Temperature**: `temperature=0.0` for faster, more deterministic outputs
5. **Async HTTP**: All external calls use `httpx.AsyncClient` for non-blocking I/O

---

## 🔧 Troubleshooting

### Common Issues

#### ❌ `ERR_CONNECTION_REFUSED` on localhost:5000
**Cause**: Docker container crashed on startup.
**Fix**:
```bash
docker compose logs nihon-api --tail=20
```
Check for Python import errors or missing `run_research` function in `graph.py`.

#### ❌ `ImportError: cannot import name 'run_research' from 'graph'`
**Cause**: `graph.py` is missing the `run_research()` function.
**Fix**: Ensure `graph.py` contains the exported `async def run_research(query: str)` function.

#### ❌ `404 Not Found` model error
**Cause**: Configured Ollama model is not installed.
**Fix**:
```bash
ollama pull llama3.2:latest
```
Or update `.env` to match an installed model.

#### ❌ MCP Server not reachable from Docker
**Cause**: MCP server binding to `127.0.0.1` instead of `0.0.0.0`.
**Fix**: Ensure `mcp_server/server.py` has:
```python
mcp = FastMCP("NihonAgent-MCP", host="0.0.0.0", port=8000)
```

#### ❌ Ollama not reachable from Docker (Windows)
**Cause**: Ollama only listens on localhost by default.
**Fix**:
```powershell
$env:OLLAMA_HOST="0.0.0.0:11434"
ollama serve
```

#### ❌ `pywin32` error during Docker build
**Cause**: `requirements.txt` contains Windows-only packages.
**Fix**: Use a clean `requirements.txt` with only cross-platform packages.

---

## 🗺️ Future Roadmap

- [ ] **Multi-Company Comparison**: Side-by-side brief comparison for 2+ companies
- [ ] **Email Alerts**: Scheduled job market monitoring with email notifications
- [ ] **RAG Integration**: Vector store of historical job data for trend analysis
- [ ] **Resume Matching**: Upload resume and get match scores against found positions
- [ ] **Japanese Language Support**: Native Japanese query processing with JLPT level filtering
- [ ] **Cloud Deployment**: AWS ECS / Google Cloud Run deployment guide
- [ ] **React Frontend**: Separate SPA with WebSocket streaming for real-time agent logs
- [ ] **Multi-LLM Support**: OpenAI GPT-4, Anthropic Claude, Google Gemini backends

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m "feat: add amazing feature"`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Setup

```bash
git clone https://github.com/Ameer-pasha/NihonAgent.git
cd NihonAgent
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### Built with ❤️ for the global tech community seeking opportunities in Japan

**[⭐ Star this repository](https://github.com/Ameer-pasha/NihonAgent)** if you found it useful!

<br>

*Powered by LangGraph · FastMCP · Ollama · FastAPI · Docker*

</div>