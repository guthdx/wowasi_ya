# Scope and Boundaries

## In Scope

### Core Functionality
- Project description input (text-based)
- Domain analysis and keyword extraction
- Dynamic ad hoc agent generation based on project context
- Web research via Claude API with native search
- Generation of all 15 starter kit documents
- Privacy layer for data sanitization before API calls

### User Interfaces
- Web-based UI for browser access
- CLI tool for terminal/scripting use
- Basic authentication for small team access

### Output Destinations
- Local filesystem (folder structure matching starter kit)
- Obsidian-compatible markdown vault
- Git repository initialization

### Infrastructure
- Self-hosted deployment (Proxmox VM or Docker container)
- Configuration via environment variables or config file
- Basic logging and error handling

---

## Out of Scope

### For MVP
- Real-time collaboration / multi-user editing
- Integration with external project management tools (Jira, Asana, Monday)
- Mobile-native applications
- Offline mode (requires API connectivity)
- Custom document templates beyond the standard 15
- Automated project updates after initial generation

### Permanently Out of Scope
- Multi-tenant SaaS offering
- Public-facing deployment
- Processing of raw PHI/PII through external APIs (privacy layer prevents this)

---

## Key Assumptions

1. **API Availability:** Claude API will remain available and pricing will stay reasonable
2. **Network Access:** The host server has outbound internet access for API calls
3. **User Competence:** Users can provide meaningful project descriptions (garbage in = garbage out)
4. **Storage:** Sufficient local storage exists for generated projects
5. **Single Deployment:** One instance serves the small team (not distributed/replicated)

---

## Dependencies

| Dependency | Type | Risk Level | Notes |
|------------|------|------------|-------|
| Claude API | External Service | Medium | No self-hosted alternative; ZDR mitigates privacy risk |
| Anthropic Pricing | External | Low | Current pricing is reasonable; monitor for changes |
| Proxmox/Docker | Infrastructure | Low | Already in use; well-understood |
| Network Connectivity | Infrastructure | Low | Required for API calls |
| User Context File | Internal | None | Defines user preferences; already created |
| Agent Strategy Doc | Internal | None | Defines agent generation rules; already created |

---

## Constraints

### Technical
- Must run on existing Proxmox infrastructure (no new hardware for MVP)
- No GPU available for local LLM processing
- Must work behind VPN/Cloudflare tunnel for remote access

### Data Handling
- Tribal data sovereignty principles must be respected
- PHI/PII must not be sent to external APIs without sanitization
- Audit trail of API interactions required

### Resource
- Small team usage (not enterprise scale)
- Limited development time (pragmatic choices over perfect architecture)
