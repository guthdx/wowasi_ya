# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wowasi_ya** (Lakota for "Assistant") is an AI-powered project documentation generator. It automatically generates 15 standardized project documentation templates from a simple project description using the Claude API with web search capabilities.

## Build & Development Commands

```bash
# Setup (Python 3.11+)
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Run single test file
pytest tests/test_privacy.py

# Run with coverage
pytest --cov=src/wowasi_ya --cov-report=term-missing

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/

# Start API server (development)
wowasi serve --reload

# Start API server (production)
uvicorn wowasi_ya.main:app --host 0.0.0.0 --port 8001

# Docker
docker compose up -d
docker compose logs -f
```

## CLI Commands

```bash
# Generate project documentation
wowasi generate "Project Name" "Detailed project description..."

# Run only discovery (no API calls)
wowasi discover "Project Name" "Description"

# Check text for PII/PHI
wowasi privacy-check "Text to scan for sensitive data"

# View audit logs
wowasi audit --limit 20
```

## Repository Structure

```
wowasi_ya/
├── src/wowasi_ya/        # Main application code
│   ├── main.py           # FastAPI app entry point
│   ├── cli.py            # Typer CLI entry point
│   ├── config.py         # Pydantic settings
│   ├── api/              # FastAPI routes and auth
│   ├── core/             # Business logic
│   │   ├── agent_discovery.py  # Phase 0: Local keyword matching
│   │   ├── privacy.py          # PII/PHI detection (Presidio)
│   │   ├── research.py         # Phase 1: Claude API research
│   │   ├── generator.py        # Phase 2: Document generation
│   │   ├── quality.py          # Phase 3: Cross-reference validation
│   │   └── output.py           # Write to filesystem/Obsidian/Git
│   ├── models/           # Pydantic models
│   └── db/               # Audit logging
├── tests/                # Pytest tests
├── docker/               # Dockerfile
├── 00-Overview/          # Planning docs: overview, brief, glossary
├── 10-Discovery/         # Planning docs: context, stakeholders
├── 20-Planning/          # Planning docs: goals, scope, budget, timeline
├── 30-Execution/         # Planning docs: workflow, SOPs, task backlog
└── 40-Comms/             # Planning docs: meeting notes, status
```

## Architecture

**Tech Stack:** Python 3.11, FastAPI, Typer CLI, Pydantic, Presidio (PII detection)

**LLM Providers:**
- **Research:** Claude API (web search required)
- **Generation:** Llama 3.3 70B (local M4 Mac via Cloudflare Tunnel)
- **Fallback:** Auto-switch to Claude when Mac offline

**Core Components:**
1. **Agent Discovery** (`core/agent_discovery.py`) - Local keyword parsing, domain matching, agent generation
2. **Privacy Layer** (`core/privacy.py`) - PHI/PII detection with user approval gate
3. **Research Engine** (`core/research.py`) - Claude API with web search
4. **Document Generator** (`core/generator.py`) - Llama 3.3 70B (via Cloudflare) or Claude (fallback)
5. **LLM Client Abstraction** (`core/llm_client.py`) - Provider-agnostic interface
6. **Quality Checker** (`core/quality.py`) - Cross-reference validation
7. **Output Manager** (`core/output.py`) - Filesystem, Obsidian, Git outputs

**Data Flow:**
```
User Input → Agent Discovery (local) → Privacy Check (local)
  → User Approval → Research (Claude API) → Generation (Llama/Claude)
  → Quality Check (local) → Output
```

**Network Topology:**
```
M4 Mac (anywhere) → Cloudflare Tunnel (llama.iyeska.net)
                           ↕
Ubuntu Server (192.168.11.20) → Cloudflare Tunnel (wowasi.iyeska.net)
                           ↕
                      End Users
```

See `ARCHITECTURE.md` for detailed provider strategy and migration paths.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/projects` | POST | Create project, start discovery |
| `/api/v1/projects` | GET | List all projects |
| `/api/v1/projects/{id}/discovery` | GET | Get discovery + privacy results |
| `/api/v1/projects/{id}/approve` | POST | Approve and start generation |
| `/api/v1/projects/{id}/status` | GET | Check generation status |
| `/api/v1/projects/{id}/result` | GET | Get generated documents |

## Configuration

### LLM Provider Settings

**Hybrid Mode (Default):**
```bash
# Generation: Llama 3.3 70B on M4 Mac
GENERATION_PROVIDER=llamacpp
LLAMACPP_BASE_URL=https://llama.iyeska.net
LLAMACPP_FALLBACK_TO_CLAUDE=true

# Research: Claude API (web search)
RESEARCH_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
ENABLE_WEB_SEARCH=true
```

**Full Claude Mode:**
```bash
# Use Claude for everything
GENERATION_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
```

**Key Environment Variables** (see `.env.example`):
- `ANTHROPIC_API_KEY` - Required (for research, optional fallback for generation)
- `GENERATION_PROVIDER` - "llamacpp" or "claude"
- `LLAMACPP_BASE_URL` - Cloudflare tunnel URL for Mac
- `LLAMACPP_FALLBACK_TO_CLAUDE` - Auto-switch when Mac offline
- `ENVIRONMENT` - development/production
- `STRICT_PRIVACY_MODE` - Require approval for all flagged content
- `CLAUDE_MODEL` - Model ID (default: claude-sonnet-4-20250514)
- `OUTPUT_DIR` - Where to write generated documents

### Cost Comparison
- **Full Claude:** $5-15 per project
- **Hybrid (Llama + Claude):** $2-5 per project (60-70% savings)
- **Breakdown:** Research uses Claude (~$2-5), Generation uses local Llama ($0)

## Deployment

**Port:** 8001 (avoids conflicts with n8n/5678, RECAP/8088, Stoic/3333)

**Production Location:** `/home/guthdx/projects/wowasi_ya` on IYESKA Ubuntu server (192.168.11.20)

**Quick Deploy:** Run `bash deploy.sh` on the server (handles venv, deps, PM2 config)

**URLs:**
- Wowasi API: https://wowasi.iyeska.net (via Cloudflare tunnel)
- Llama CPP: https://llama.iyeska.net (M4 Mac via Cloudflare tunnel)

### Mac Setup (Llama Server)

1. **Start Llama CPP Server:**
```bash
llama-server \
  --model ~/models/bartowski_Llama-3.3-70B-Instruct-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --n-gpu-layers 35  # Adjust for M4 GPU
```

2. **Start Cloudflare Tunnel:**
```bash
# Run tunnel (or set to auto-start on login)
cloudflared tunnel run <your-tunnel-name>

# Or install as service
cloudflared service install
```

3. **Verify Connection:**
```bash
# Test locally
curl http://localhost:8080/health

# Test via tunnel
curl https://llama.iyeska.net/health
```

### Network Requirements
- Mac must have internet connection (any network, anywhere)
- Cloudflare tunnel handles routing (no VPN needed)
- Works from home office, coffee shop, hotel, conference, etc.
- Auto-fallback to Claude if Mac offline/asleep

See `DEPLOYMENT.md` for:
- Docker setup
- Cloudflare tunnel configuration for iyeska.net
- PM2 and systemd options
- Troubleshooting network issues

See `ARCHITECTURE.md` for:
- Detailed provider architecture
- Migration paths for adding new LLM providers
- Cost analysis and performance characteristics

## Critical Constraints

- **Privacy-First:** All data passes through privacy layer before API calls
- **Hybrid LLM:** Research via Claude (web search), Generation via local Llama (cost/privacy)
- **Data Sovereignty:** Audit logging for all API interactions, local inference when possible
- **User Approval Gate:** Required before any external API calls
- **Location Independence:** Works from anywhere with internet (Mac + Ubuntu via Cloudflare)
