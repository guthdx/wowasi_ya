# Risks and Assumptions

## Risk Register

### R1: API Dependency
**Description:** Wowasi_ya depends entirely on Claude API for document generation. If the API is unavailable, the tool doesn't work.

| Factor | Assessment |
|--------|------------|
| Likelihood | Low (Anthropic has good uptime) |
| Impact | High (complete loss of functionality) |
| Risk Score | Medium |

**Mitigation:**
- Implement graceful error handling with clear user messaging
- Cache successful generations locally
- Consider fallback to local model for basic functionality (post-MVP)
- Monitor Anthropic status page

---

### R2: API Pricing Changes
**Description:** Anthropic could increase API pricing significantly, making the tool expensive to operate.

| Factor | Assessment |
|--------|------------|
| Likelihood | Medium (market is competitive, but pricing fluctuates) |
| Impact | Medium (increases operating costs) |
| Risk Score | Medium |

**Mitigation:**
- Use cost optimization strategies (batching, caching, Haiku for drafts)
- Monitor monthly costs
- Build abstraction layer that could support alternative providers
- Set usage alerts/limits

---

### R3: Document Quality Issues
**Description:** AI-generated documents may contain errors, hallucinations, or inappropriate content.

| Factor | Assessment |
|--------|------------|
| Likelihood | Medium (LLMs do make mistakes) |
| Impact | Medium (bad docs lead to bad projects) |
| Risk Score | Medium |

**Mitigation:**
- User should review all generated documents before use
- Include disclaimer that docs are AI-assisted drafts
- Implement quality checks (cross-reference consistency)
- Provide easy editing/regeneration of individual docs

---

### R4: Privacy Layer Failure
**Description:** Sensitive data could be sent to external API despite privacy layer.

| Factor | Assessment |
|--------|------------|
| Likelihood | Low (if properly implemented) |
| Impact | High (data sovereignty violation) |
| Risk Score | Medium |

**Mitigation:**
- User review step before any API call
- Clear display of what will be sent
- Conservative sensitivity detection (flag more, not less)
- Audit log of all API interactions
- Regular review of what's being sent

---

### R5: Scope Creep
**Description:** Feature requests expand scope beyond MVP, delaying completion.

| Factor | Assessment |
|--------|------------|
| Likelihood | High (always tempting to add features) |
| Impact | Medium (delays, complexity) |
| Risk Score | Medium |

**Mitigation:**
- Clear MVP definition in Scope-and-Boundaries.md
- "Post-MVP" parking lot for ideas
- Strict prioritization
- Ship working MVP before adding features

---

### R6: Maintenance Burden
**Description:** Tool requires ongoing maintenance that exceeds available time.

| Factor | Assessment |
|--------|------------|
| Likelihood | Medium |
| Impact | Medium (tool becomes stale/broken) |
| Risk Score | Medium |

**Mitigation:**
- Choose stable, well-supported technologies
- Minimal dependencies
- Good logging for troubleshooting
- Documentation for future maintenance
- Containerization for reproducibility

---

### R7: Authentication Bypass
**Description:** Unauthorized users could access the tool.

| Factor | Assessment |
|--------|------------|
| Likelihood | Low (if auth implemented correctly) |
| Impact | Medium (unauthorized usage, data exposure) |
| Risk Score | Low |

**Mitigation:**
- Use proven authentication library (not custom)
- HTTPS required
- Network-level protection (VPN, firewall)
- Regular credential rotation

---

### R8: Data Loss
**Description:** Generated projects or configuration could be lost.

| Factor | Assessment |
|--------|------------|
| Likelihood | Low |
| Impact | High (lost work) |
| Risk Score | Medium |

**Mitigation:**
- Output to multiple destinations (filesystem + git)
- Regular backups of Proxmox VM
- Configuration stored in version-controlled files
- Git integration provides inherent backup

---

## Risk Matrix

```
           │ Low Impact │ Med Impact │ High Impact │
───────────┼────────────┼────────────┼─────────────┤
High Likl. │            │ R5         │             │
───────────┼────────────┼────────────┼─────────────┤
Med Likl.  │            │ R2,R3,R6   │             │
───────────┼────────────┼────────────┼─────────────┤
Low Likl.  │ R7         │ R8         │ R1,R4       │
───────────┴────────────┴────────────┴─────────────┘
```

**Priority Focus:** R4 (Privacy), R1 (API Dependency), R5 (Scope Creep)

---

## Critical Assumptions

### A1: Claude API Remains Suitable
**Assumption:** Claude Sonnet 4 continues to be the best option for this use case.
**If Wrong:** May need to switch providers or models, requiring code changes.
**Validation:** Periodic review of model landscape and quality.

### A2: Project Descriptions Are Sufficient
**Assumption:** Users can provide project descriptions detailed enough for meaningful analysis.
**If Wrong:** Generated documents will be generic/useless.
**Validation:** Test with real project descriptions early.

### A3: 15-Document Structure Is Appropriate
**Assumption:** The starter kit template meets actual project documentation needs.
**If Wrong:** May need to add/remove/modify document types.
**Validation:** Use generated docs on real projects, gather feedback.

### A4: Self-Hosting Is Feasible
**Assumption:** Proxmox infrastructure can support the application reliably.
**If Wrong:** May need alternative hosting.
**Validation:** Test deployment early in development.

### A5: Small Team Doesn't Need Complex Auth
**Assumption:** Basic username/password auth is sufficient.
**If Wrong:** May need SSO, MFA, or integration with existing auth.
**Validation:** Confirm with team members.

### A6: Privacy Layer Is Sufficient
**Assumption:** Pattern-based sensitivity detection + user review provides adequate protection.
**If Wrong:** May need more sophisticated NLP-based detection.
**Validation:** Test with intentionally sensitive content.

---

## Assumption Validation Plan

| Assumption | Validation Method | When |
|------------|------------------|------|
| A1 | Compare model outputs periodically | Ongoing |
| A2 | Test with 3+ real project descriptions | Phase 1 |
| A3 | Use docs on real project, note gaps | After MVP |
| A4 | Deploy test container to Proxmox | Phase 1 |
| A5 | Ask team about auth requirements | Before Phase 4 |
| A6 | Test with sample PHI/PII content | Phase 3 |
