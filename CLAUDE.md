# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🚨 ACTIVE WORK IN PROGRESS - READ FIRST

**Last Updated:** December 30, 2025

**Current Project:** Web Portal & Next Steps Engine - Complete project tracking system

**Status:** Phase 4 Complete - Portal deployed at https://portal.iyeska.net

**📋 Key Documents:**
- `USERS_GUIDE.md` - Complete workflow guide for all tools
- `API_SECURITY.md` - Endpoint security documentation
- `WEB_PORTAL_PLAN.md` - Portal implementation details
- `PROMPT_ENHANCEMENT_STATUS.md` - Document quality improvements

**Recent Completions:**
- ✅ Phase 1: Outline Wiki integration (publish documents)
- ✅ Phase 2: Wowasi → Outline API (programmatic publishing)
- ✅ Phase 3: Next Steps Engine (actionable tasks for each document)
- ✅ Phase 4: Web Portal (React dashboard at portal.iyeska.net)

**Quick Summary:**
- Portal provides visual project tracking at https://portal.iyeska.net
- Next Steps Engine creates actionable tasks for each of 15 documents
- Read-only endpoints are public for portal access
- Write operations require HTTP Basic authentication

---

## Project Overview

**Wowasi_ya** (Lakota: "Assistant") is an AI-powered project documentation generator that creates 15 standardized project documents from a simple description. It uses a hybrid LLM architecture with Claude for research (web search required) and Llama 3.3 70B (local) for generation.

## Build & Development Commands

```bash
# Setup (Python 3.11+)
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest                                          # All tests
pytest tests/test_privacy.py                    # Single test file
pytest --cov=src/wowasi_ya --cov-report=term-missing  # With coverage

# Lint and format
ruff check src/ tests/                          # Lint
ruff format src/ tests/                         # Format
mypy src/                                       # Type checking

# Start API server
wowasi serve --reload                           # Development (port 8000)
uvicorn wowasi_ya.main:app --host 0.0.0.0 --port 8002  # Production (port 8002)

# CLI commands
wowasi generate "Project Name" "Description..."  # Generate docs
wowasi discover "Project Name" "Description"     # Discovery only (no API)
wowasi privacy-check "Text to scan..."           # PII/PHI check
wowasi audit --limit 20                          # View audit logs

# Docker
docker compose up -d                             # Start
docker compose logs -f                           # Logs
docker compose down                              # Stop
```

## Local Development with Traefik

```bash
# 1. Start Traefik (if not already running)
cd ~/terminal_projects/claude_code/traefik && docker compose up -d

# 2. Start Wowasi_ya
cd ~/terminal_projects/claude_code/wowasi_ya
docker compose up -d
```

**Access via Traefik (recommended):**
- API: http://wowasi.localhost
- API Docs: http://wowasi.localhost/docs
- Traefik Dashboard: http://traefik.localhost

**Direct port access (fallback):**
- API: http://localhost:8001
- Portal: http://localhost:3003

**Port Allocation** (per PORT_REGISTRY.md):
- API: 8001
- Portal: 3003

## Web Portal

The portal provides a visual dashboard for project tracking at https://portal.iyeska.net

**Tech Stack:**
- React 19 + TypeScript + Vite 7
- Tailwind CSS v4
- TanStack Query (React Query) for data fetching
- Nginx for static serving in Docker

**Local Development:**
```bash
cd portal
npm install
npm run dev  # Runs on http://localhost:5173
```

**Docker Deployment:**
```bash
# Build and run portal container
docker compose -f docker-compose.portal.yml up -d --build

# Access at http://localhost:3003
```

**Production URL:** https://portal.iyeska.net (via Cloudflare Tunnel)

**Portal Features:**
- Dashboard with project list and status overview
- Project view with documents organized by phase
- Progress tracking with visual indicators
- Next steps management (complete/skip actions)

**Related Files:**
- `portal/` - React application source
- `docker-compose.portal.yml` - Portal container config
- `portal/nginx.conf` - Nginx SPA configuration

## Architecture

### Hybrid LLM Strategy

**Research Phase (Claude API):**
- Location: `src/wowasi_ya/core/research.py`
- Provider: Claude Sonnet 4 with web search enabled
- Why: Web search capability required for current information
- Cost: ~$2-5 per project

**Generation Phase (Llama 3.3 70B):**
- Location: `src/wowasi_ya/core/generator.py`
- Provider: Llama 3.3 70B via Cloudflare Tunnel to M4 Mac
- Why: 60-70% cost reduction, data privacy
- Cost: $0 (local inference)
- Fallback: Automatically uses Claude when Mac unavailable

### LLM Client Abstraction

All LLM calls go through `src/wowasi_ya/core/llm_client.py`:

```python
class BaseLLMClient(Protocol):
    async def generate(prompt, max_tokens, temperature) -> str
    def supports_web_search() -> bool
    async def health_check() -> bool

# Implementations
ClaudeClient      # Anthropic API
LlamaCPPClient    # Local via Cloudflare Tunnel

# Factory functions
get_generation_client(settings)  # With automatic fallback logic
get_research_client(settings)    # Always Claude for web search
```

**To add a new provider:** Implement `BaseLLMClient` in `llm_client.py`, update factory functions, set environment variable. Business logic in `research.py` and `generator.py` requires no changes.

### Core Pipeline

```
1. Agent Discovery (core/agent_discovery.py)
   - Local keyword matching → domain identification → agent generation

2. Privacy Layer (core/privacy.py)
   - Presidio PII/PHI detection → user approval gate

3. Research (core/research.py)
   - Claude API with web search → compile findings

4. Generation (core/generator.py)
   - Llama 3.3 70B (or Claude fallback) → 15 documents in 5 batches

5. Quality Check (core/quality.py)
   - Cross-reference validation → completeness scoring

6. Output (core/output.py)
   - Filesystem → Obsidian vault → Git commit → Google Drive sync
```

## Repository Structure

```
src/wowasi_ya/
├── main.py              # FastAPI app entry point
├── cli.py               # Typer CLI entry point
├── config.py            # Pydantic settings (env vars)
├── api/
│   ├── routes.py        # FastAPI endpoints
│   └── auth.py          # JWT authentication
├── core/                # Business logic (all async)
│   ├── agent_discovery.py    # Phase 0: Local keyword → agents
│   ├── privacy.py            # PII/PHI detection (Presidio)
│   ├── research.py           # Phase 1: Claude API research
│   ├── generator.py          # Phase 2: Document generation
│   ├── quality.py            # Phase 3: Quality validation
│   ├── output.py             # Phase 4: Write outputs
│   └── llm_client.py         # LLM abstraction layer
├── models/              # Pydantic models
│   ├── agent.py         # AgentDefinition, DomainMatch
│   ├── document.py      # Document, GeneratedProject
│   └── project.py       # ProjectInput, ProjectStatus
└── db/                  # Audit logging (SQLite)
```

## Network Architecture

```
M4 Mac (anywhere) → Cloudflare Tunnel (llama.iyeska.net)
                           ↕
Ubuntu Server (192.168.11.20) → Cloudflare Tunnel (wowasi.iyeska.net)
                           ↕
                      End Users
```

**Key benefit:** Mac can be anywhere with internet (home, coffee shop, hotel). No VPN required. Auto-fallback to Claude when Mac offline.

## Configuration

### Critical Environment Variables

```bash
# LLM Providers
GENERATION_PROVIDER=llamacpp          # "llamacpp" or "claude"
RESEARCH_PROVIDER=claude              # Fixed (web search required)
ANTHROPIC_API_KEY=sk-ant-...          # Required

# Llama CPP (M4 Mac via Cloudflare)
LLAMACPP_BASE_URL=https://llama.iyeska.net
LLAMACPP_MODEL=Llama-3.3-70B-Instruct-Q4_K_M
LLAMACPP_TIMEOUT=300
LLAMACPP_FALLBACK_TO_CLAUDE=true      # Auto-switch when Mac offline

# Claude API
CLAUDE_MODEL=claude-sonnet-4-20250514
ENABLE_WEB_SEARCH=true
MAX_CONCURRENT_RESEARCH_AGENTS=1      # Rate limit protection

# Output
OUTPUT_DIR=./output
OBSIDIAN_VAULT_PATH=/path/to/vault    # Optional
GIT_OUTPUT_PATH=/path/to/repo         # Optional
GDRIVE_REMOTE_PATH=gdrive:Wowasi      # Rclone remote
ENABLE_GDRIVE_SYNC=true               # Auto-sync after generation

# Privacy
STRICT_PRIVACY_MODE=true              # Require user approval
PRIVACY_CONFIDENCE_THRESHOLD=0.7      # PII/PHI detection threshold

# Server
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8002                             # Avoid conflicts (8001 in use)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check (shows LLM provider status) |
| `/api/v1/projects` | POST | Create project → start discovery |
| `/api/v1/projects` | GET | List all projects |
| `/api/v1/projects/{id}/discovery` | GET | Discovery + privacy scan results |
| `/api/v1/projects/{id}/approve` | POST | User approval → start generation |
| `/api/v1/projects/{id}/status` | GET | Check generation progress |
| `/api/v1/projects/{id}/result` | GET | Download generated documents |

**Docs:** `http://localhost:8002/docs` (or `https://wowasi.iyeska.net/docs`)

## Output Writers

`src/wowasi_ya/core/output.py` provides pluggable output destinations:

```python
FilesystemWriter      # Write to ./output/
ObsidianWriter        # Obsidian vault with frontmatter + wiki links
GitWriter             # Git repo with auto-commit
GoogleDriveWriter     # Rclone sync to Google Drive
```

**Automatic Google Drive sync:** When `ENABLE_GDRIVE_SYNC=true`, all projects automatically sync to `gdrive:Wowasi/` after generation. Uses rclone (must be configured separately).

## Critical Constraints

1. **Privacy-First:** All data passes through `core/privacy.py` before external API calls. User approval required in `STRICT_PRIVACY_MODE=true`.

2. **Hybrid LLM:** Research requires Claude (web search). Generation prefers Llama (cost/privacy) but auto-falls back to Claude.

3. **Data Sovereignty:** Audit logging in SQLite (`wowasi_ya.db`) tracks all LLM interactions. Local inference preferred when Mac available.

4. **Location Independence:** Works from anywhere. Mac only needs internet connection. Cloudflare Tunnel handles routing.

## Deployment

**Port:** 8002 (avoids conflicts with n8n/5678, RECAP/8088, Stoic/3333, initial Wowasi/8001)

**Production location:** `/home/guthdx/projects/wowasi_ya` on IYESKA server (192.168.11.20)

**Quick deploy:**
```bash
bash deploy.sh  # Handles venv, deps, PM2 restart
```

**PM2 management:**
```bash
pm2 restart wowasi_ya
pm2 logs wowasi_ya
pm2 list
```

**Public URLs:**
- Wowasi API: https://wowasi.iyeska.net
- Llama CPP: https://llama.iyeska.net (M4 Mac)

## Mac Setup (Llama Server)

```bash
# 1. Start Llama CPP server on Mac
llama-server \
  --model ~/models/bartowski_Llama-3.3-70B-Instruct-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --n-gpu-layers 35

# 2. Start Cloudflare tunnel
cloudflared tunnel run <tunnel-name>

# 3. Verify
curl http://localhost:8080/health           # Local
curl https://llama.iyeska.net/health        # Via tunnel
```

**Keep Mac awake:** System Settings → Energy → Prevent sleep when display is off

## Troubleshooting

### Llama Unavailable (Using Claude Fallback)

**Check:**
```bash
curl https://wowasi.iyeska.net/api/v1/health
```

Look for `"llamacpp": {"available": false}` in response.

**Solutions:**
1. Verify Mac is on and connected to internet
2. Check Llama server: `ps aux | grep llama` on Mac
3. Check Cloudflare tunnel: `cloudflared tunnel list` on Mac
4. Test locally: `curl http://localhost:8080/health` on Mac
5. Test via tunnel: `curl https://llama.iyeska.net/health`

### High API Costs

**Check:**
```bash
wowasi audit --limit 50  # Review Claude API usage
```

If frequently using Claude fallback, ensure Mac availability.

### Privacy Check Blocking

If PII/PHI detected and blocking generation:
1. Review flags in discovery response
2. Either sanitize input or use `--skip-privacy` (CLI only, NOT recommended)
3. Adjust `PRIVACY_CONFIDENCE_THRESHOLD` if too many false positives

## Testing

```bash
# Unit tests
pytest tests/                                   # All tests
pytest tests/test_privacy.py                    # Privacy layer
pytest tests/test_llm_client.py                 # LLM abstraction

# Integration tests (require API key)
pytest tests/integration/ -v

# Coverage
pytest --cov=src/wowasi_ya --cov-report=html
open htmlcov/index.html
```

**Mock LLM clients in tests:** See `tests/conftest.py` for fixtures.

## Migration Paths

### To Add New LLM Provider

Example: Add Perplexity for research (has web search):

1. **Implement client** in `llm_client.py`:
```python
class PerplexityClient(BaseLLMClient):
    async def generate(self, prompt, max_tokens, temperature):
        # Call Perplexity API
        ...

    def supports_web_search(self) -> bool:
        return True
```

2. **Update factory** in `llm_client.py`:
```python
def get_research_client(settings):
    if settings.research_provider == "perplexity":
        return PerplexityClient(settings)
    return ClaudeClient(settings)
```

3. **Update config** in `config.py`:
```python
research_provider: Literal["claude", "perplexity"] = "claude"
```

4. **Set env var:**
```bash
RESEARCH_PROVIDER=perplexity
PERPLEXITY_API_KEY=...
```

**No changes needed** in `core/research.py` business logic.

## Common Gotchas

1. **Port conflicts:** Wowasi_ya uses 8002. Initial Wowasi uses 8001. Check with `sudo lsof -i :8002` before starting.

2. **Environment not loaded:** PM2 requires `--update-env` flag after `.env` changes: `pm2 restart wowasi_ya --update-env`

3. **Presidio models not downloaded:** First run downloads spaCy models. May take 2-3 minutes.

4. **Rclone not configured:** Google Drive sync requires rclone setup. Run `rclone config` to add "gdrive" remote.

5. **Mac sleep kills Llama:** Disable sleep in Mac Energy settings or accept Claude fallback.

## Performance Characteristics

**Llama 3.3 70B on M4 Mac:**
- Throughput: ~15-30 tokens/second
- Latency: 3-8 seconds per document
- Memory: ~40GB RAM

**Claude API:**
- Latency: 1-5 seconds per document
- Cost: $3-15 per million tokens

**Full project generation:**
- Time: 3-8 minutes (15 documents)
- Cost: $2-5 (hybrid) vs $5-15 (full Claude)
