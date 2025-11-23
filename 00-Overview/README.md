# Wowasi_ya

**Lakota:** *Wówašiya* (Wo-wa-shi-ya) - "Assistant"

A self-hosted project bootstrapping tool that generates comprehensive project documentation using AI-powered research and document generation.

## What This Project Does

Wowasi_ya takes a project idea and automatically:
1. Analyzes the description to identify domains, stakeholders, and compliance needs
2. Generates specialized research agents based on project context
3. Conducts web research for regulations, grants, best practices
4. Produces 15 standardized project documents ready for use

## Who This Is For

- Small teams working in tribal, rural, and sovereignty-focused contexts
- Organizations managing projects across infrastructure, health, agriculture, nonprofits, and finance
- Anyone who needs structured project documentation without starting from scratch

## Current Status

**Status:** Planning

## Key Files

| Location | Purpose |
|----------|---------|
| `00-Overview/Project-Brief.md` | Problem statement and solution overview |
| `20-Planning/Goals-and-Success-Criteria.md` | What success looks like |
| `20-Planning/Scope-and-Boundaries.md` | What's in and out of scope |
| `30-Execution/` | Workflows, SOPs, and task tracking |
| `src/` | Application source code |

## Technology Stack

- **Backend:** TBD (Python FastAPI or Node.js)
- **Frontend:** Web UI + CLI
- **AI Integration:** Claude Sonnet 4 API with strict data handling
- **Hosting:** Self-hosted (Proxmox VM/Container)
- **Storage:** Filesystem + Obsidian + Git outputs
