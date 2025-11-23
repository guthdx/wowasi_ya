# Context and Background

## How This Project Came About

This project emerged from repeated experience with the friction of starting new projects:

1. **The Pattern:** Every new project requires similar documentation - goals, scope, stakeholders, risks, workflows. This work is necessary but repetitive.

2. **The Starter Kit:** A standardized project folder structure and 15-document template was created to ensure consistency across projects.

3. **The Gap:** Even with templates, populating them requires significant effort - researching regulations, identifying stakeholders, estimating budgets, mapping workflows.

4. **The Opportunity:** AI capabilities (particularly Claude) now support high-quality research and document generation. The question became: can we automate the bootstrap process while maintaining quality and respecting data sovereignty?

5. **The Solution:** Wowasi_ya - an assistant that takes a project description and generates all 15 starter kit documents, using dynamic research agents tailored to each project's specific context.

---

## Related Efforts

### Project Starter Kit Template
- Location: `project_starter_template/project_starter_kit.md.rtf`
- Status: Complete
- Purpose: Defines the folder structure and document templates

### Claude Code Agent Strategy
- Location: `project_starter_template/claude_code_agent_strategy.md`
- Status: Complete (v1.1)
- Purpose: Defines how AI agents analyze projects and generate documents
- Key features:
  - Phase 0: Agent Discovery & Generation
  - Domain keyword mapping
  - Stakeholder-based agent triggers
  - Context-specific customization rules

### User Context File
- Location: `project_starter_template/user_context_g3dx.md.rtf`
- Status: Updated
- Purpose: Defines user preferences, constraints, and interaction style
- Key updates: Now prioritizes best solutions over familiar ones

---

## Known Constraints

### Technical Constraints
| Constraint | Impact | Mitigation |
|------------|--------|------------|
| No GPU hardware available | Cannot run large local LLMs | Use Claude API with privacy layer |
| Must self-host | Cannot use cloud-only solutions | Deploy on Proxmox VM/container |
| Multi-device access needed | Must be network-accessible | Web UI + VPN/Cloudflare tunnel |

### Data Handling Constraints
| Constraint | Impact | Mitigation |
|------------|--------|------------|
| Tribal data sovereignty | Sensitive data must be handled carefully | Privacy layer sanitizes before API calls |
| PHI/PII possible | Health/personal data may be in project descriptions | User reviews what goes to API |
| Audit requirements | Need to track what data leaves the network | Logging of API interactions |

### Resource Constraints
| Constraint | Impact | Mitigation |
|------------|--------|------------|
| Small team | Limited development/maintenance capacity | Pragmatic architecture, proven tools |
| Limited budget | Cannot afford expensive infrastructure | Leverage existing Proxmox setup |
| Time constraints | Need working solution, not perfect solution | MVP focus, iterate later |

---

## Relevant Policies and Considerations

### Data Sovereignty
- Project descriptions may contain tribal-specific information
- Some projects may involve federal trust responsibilities
- Data residency preferences favor local storage

### API Usage
- Claude API with Zero Data Retention (ZDR) available
- Commercial API terms: data not used for training
- 30-day retention (dropping to 7 days after Sept 2025)

### Security
- Authentication required for team access
- HTTPS for web interface
- API keys stored securely (not in code)
