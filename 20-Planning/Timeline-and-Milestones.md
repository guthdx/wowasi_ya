# Timeline and Milestones

## Project Phases

### Phase 1: Foundation
**Focus:** Core architecture and basic functionality

#### Milestone 1.1: Technical Architecture Defined
**Requirements to mark complete:**
- [ ] Stack decision finalized (language, framework)
- [ ] Component architecture documented
- [ ] Data flow diagram complete
- [ ] Privacy layer design specified
- [ ] API integration approach defined

#### Milestone 1.2: Development Environment Ready
**Requirements to mark complete:**
- [ ] Project repository initialized
- [ ] Development dependencies installed
- [ ] Basic project structure in place
- [ ] Configuration management set up
- [ ] Claude API key configured (dev environment)

#### Milestone 1.3: Core Engine Working
**Requirements to mark complete:**
- [ ] Project description input accepted
- [ ] Domain analysis functional
- [ ] Basic document generation working (at least 1 doc)
- [ ] Output saved to filesystem

---

### Phase 2: Agent System
**Focus:** Dynamic agent generation and research

#### Milestone 2.1: Agent Discovery Implemented
**Requirements to mark complete:**
- [ ] Keyword extraction from project description
- [ ] Domain matching against keyword map
- [ ] Intersection detection working
- [ ] Stakeholder triggers functional
- [ ] Agent definitions generated dynamically

#### Milestone 2.2: Web Research Functional
**Requirements to mark complete:**
- [ ] Claude web search integration working
- [ ] Research results incorporated into documents
- [ ] Source citations included
- [ ] Research brief compiled

#### Milestone 2.3: All 15 Documents Generated
**Requirements to mark complete:**
- [ ] All starter kit documents generated
- [ ] Documents are coherent and interconnected
- [ ] Glossary terms consistent across docs
- [ ] Quality acceptable for real use

---

### Phase 3: Privacy Layer
**Focus:** Data handling and sanitization

#### Milestone 3.1: Sensitivity Detection
**Requirements to mark complete:**
- [ ] PHI/PII patterns identified
- [ ] Tribal-specific terms flagged
- [ ] Sensitivity scoring implemented
- [ ] User notification of flagged content

#### Milestone 3.2: Sanitization Options
**Requirements to mark complete:**
- [ ] User can review flagged content
- [ ] User can approve/modify before API call
- [ ] Sanitized prompts used for API
- [ ] Original context preserved locally

#### Milestone 3.3: Audit Trail
**Requirements to mark complete:**
- [ ] API calls logged
- [ ] What was sent recorded
- [ ] Timestamps captured
- [ ] Logs accessible for review

---

### Phase 4: User Interfaces
**Focus:** Web UI and CLI

#### Milestone 4.1: CLI Tool Working
**Requirements to mark complete:**
- [ ] Project description input via CLI
- [ ] Progress output to terminal
- [ ] Documents generated to specified path
- [ ] Basic error handling

#### Milestone 4.2: Web UI Functional
**Requirements to mark complete:**
- [ ] Project description input form
- [ ] Generation progress displayed
- [ ] Document preview/download
- [ ] Basic responsive design

#### Milestone 4.3: Authentication Added
**Requirements to mark complete:**
- [ ] Login required for access
- [ ] User accounts for team members
- [ ] Session management
- [ ] Secure password handling

---

### Phase 5: Output & Integration
**Focus:** Multiple output formats

#### Milestone 5.1: Filesystem Output Complete
**Requirements to mark complete:**
- [ ] Folder structure matches starter kit
- [ ] All files written correctly
- [ ] Path configurable

#### Milestone 5.2: Obsidian Integration
**Requirements to mark complete:**
- [ ] Output compatible with Obsidian vault
- [ ] Links between documents work
- [ ] Frontmatter/metadata if needed

#### Milestone 5.3: Git Integration
**Requirements to mark complete:**
- [ ] Git repo initialized for project
- [ ] Initial commit with all docs
- [ ] Remote push optional

---

### Phase 6: Deployment
**Focus:** Production-ready self-hosting

#### Milestone 6.1: Containerized
**Requirements to mark complete:**
- [ ] Dockerfile created
- [ ] Container builds successfully
- [ ] All dependencies included
- [ ] Configuration via environment variables

#### Milestone 6.2: Deployed to Proxmox
**Requirements to mark complete:**
- [ ] VM or LXC container running
- [ ] Application accessible on network
- [ ] Auto-start on reboot
- [ ] HTTPS configured

#### Milestone 6.3: MVP Complete
**Requirements to mark complete:**
- [ ] All Phase 1-6 milestones achieved
- [ ] Used successfully on real project
- [ ] Documentation complete
- [ ] Team can access and use

---

## Milestone Summary

| Phase | Milestones | Key Deliverable |
|-------|------------|-----------------|
| 1. Foundation | 1.1-1.3 | Core engine working |
| 2. Agent System | 2.1-2.3 | All 15 docs generated |
| 3. Privacy Layer | 3.1-3.3 | Audit trail working |
| 4. User Interfaces | 4.1-4.3 | Web + CLI with auth |
| 5. Output | 5.1-5.3 | Multiple export formats |
| 6. Deployment | 6.1-6.3 | MVP running on Proxmox |

---

## Dependencies Between Phases

```
Phase 1 (Foundation)
    │
    ├──► Phase 2 (Agent System)
    │         │
    │         └──► Phase 3 (Privacy Layer)
    │
    └──► Phase 4 (User Interfaces) ◄── can start after 1.3
              │
              └──► Phase 5 (Output)
                        │
                        └──► Phase 6 (Deployment)
```

Phases 2-3 and 4-5 can proceed in parallel after Phase 1 completes.
