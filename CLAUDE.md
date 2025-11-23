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

**Core Components:**
1. **Agent Discovery** (`core/agent_discovery.py`) - Local keyword parsing, domain matching, agent generation
2. **Privacy Layer** (`core/privacy.py`) - PHI/PII detection with user approval gate
3. **Research Engine** (`core/research.py`) - Claude API with web search
4. **Document Generator** (`core/generator.py`) - Creates 15 documents in 5 batches
5. **Quality Checker** (`core/quality.py`) - Cross-reference validation
6. **Output Manager** (`core/output.py`) - Filesystem, Obsidian, Git outputs

**Data Flow:**
```
User Input → Agent Discovery (local) → Privacy Check (local)
  → User Approval → Research (API) → Generation (API)
  → Quality Check (local) → Output
```

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

Environment variables (see `.env.example`):
- `ANTHROPIC_API_KEY` - Required
- `ENVIRONMENT` - development/production
- `STRICT_PRIVACY_MODE` - Require approval for all flagged content
- `CLAUDE_MODEL` - Model ID (default: claude-sonnet-4-20250514)
- `OUTPUT_DIR` - Where to write generated documents

## Deployment

**Port:** 8001 (avoids conflicts with n8n/5678, RECAP/8088, Stoic/3333)

**Production Location:** `/home/guthdx/projects/wowasi_ya` on IyeskaLLC Ubuntu server

**Quick Deploy:** Run `bash deploy.sh` on the server (handles venv, deps, PM2 config)

**URL:** https://wowasi.iyeska.net (via Cloudflare tunnel)

See `DEPLOYMENT.md` for:
- Docker setup
- Cloudflare tunnel configuration for iyeska.net
- PM2 and systemd options

## Critical Constraints

- **Privacy-First:** All data passes through privacy layer before API calls
- **Self-Hosted:** Runs on Proxmox VM or Docker
- **Data Sovereignty:** Audit logging for all API interactions
- **User Approval Gate:** Required before any external API calls
