# Project Brief: Wowasi_ya

## Problem Statement

Starting new projects requires significant upfront documentation work:
- Defining scope, goals, and success criteria
- Identifying stakeholders and their concerns
- Researching compliance requirements, funding sources, and best practices
- Creating workflows, SOPs, and task backlogs

This work is repetitive, time-consuming, and often done inconsistently. Teams either skip documentation (leading to problems later) or spend excessive time on boilerplate before real work begins.

## Proposed Solution

Wowasi_ya is an AI-powered assistant that generates comprehensive project documentation from a simple project description. It:

1. **Analyzes** the project description to identify:
   - Relevant domains (health, agriculture, finance, technology, etc.)
   - Stakeholders and their interests
   - Compliance and regulatory requirements
   - Infrastructure and data sovereignty considerations

2. **Generates specialized research agents** dynamically based on project context (e.g., a tribal telehealth project spawns healthcare-compliance and tribal-sovereignty researchers)

3. **Conducts web research** for:
   - Relevant regulations and compliance frameworks
   - Grant and funding opportunities
   - Best practices and similar projects
   - Risk factors and lessons learned

4. **Produces 15 standardized documents**:
   - README, Project Brief, Glossary
   - Context, Stakeholder Notes
   - Goals, Scope, Budget, Timeline, Risks
   - Workflows, SOPs, Task Backlog
   - Meeting and Status templates

## Who Benefits

- **Project managers** get a head start on documentation
- **Small teams** without dedicated PMO resources
- **Organizations in tribal/rural contexts** who need sovereignty-aware documentation
- **Grant writers** who need compliant project structures

## Why This Matters Now

- AI capabilities now support high-quality document generation
- Remote/distributed teams need standardized documentation
- Tribal data sovereignty requires careful handling that generic tools ignore
- The project starter kit template already exists - this tool operationalizes it

## Rough Scope

### In Scope
- Web-based interface accessible from multiple devices
- CLI tool for automation and scripting
- Integration with Claude Sonnet 4 API for research and generation
- Privacy layer that sanitizes data before API calls
- Output to filesystem, Obsidian vaults, and git repositories
- Basic authentication for small team access
- Self-hosted deployment on Proxmox

### Out of Scope (for v1)
- Multi-tenant SaaS deployment
- Integration with project management tools (Jira, Asana, etc.)
- Real-time collaboration features
- Mobile-native apps
