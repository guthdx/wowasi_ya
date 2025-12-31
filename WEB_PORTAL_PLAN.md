# Wowasi Ya Web Portal: Implementation Plan

> **Status:** Planning (Updated with Outline Pivot)
> **Created:** 2025-12-30
> **Last Updated:** 2025-12-30
> **Purpose:** Extend wowasi_ya from a document generator into a living project workspace

---

## Vision

Transform wowasi_ya from a document generation tool into a **living project workspace** where clients can view, iterate on, and take action on their foundational documents over time.

**Key Value Proposition:** "We don't just give you documents, we help you use them."

---

## Strategic Pivot: Outline + Thin Portal

### Original Plan (Build Everything)
- Full React frontend from scratch
- Custom document storage and versioning
- Custom collaboration features
- 6-12 months estimated effort

### New Plan (Outline + Portal Layer)
- **Outline Wiki** handles 80% of functionality (docs, versions, collaboration, sharing)
- **Thin Portal** adds the 20% differentiator (Next Steps tracking)
- **Wowasi_ya** pushes generated docs directly to Outline via API
- 4-6 weeks estimated effort

### Why This Pivot?

| Concern | Build Everything | Outline + Portal |
|---------|------------------|------------------|
| Time to MVP | 3-4 months | 2-3 weeks |
| Document versioning | Build from scratch | Built-in |
| Collaboration | Build from scratch | Built-in |
| Public sharing | Build from scratch | Built-in |
| Custom domain | Implement | Built-in |
| Maintenance burden | High | Low (Outline updates) |
| Data sovereignty | Yes | Yes (self-hosted) |
| Cost | $0 (time cost) | $0 (self-hosted) |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Browser                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
┌──────────────────────────────────┐  ┌───────────────────────────────────────┐
│         Outline Wiki             │  │           Portal (React)              │
│         docs.iyeska.net          │  │         portal.iyeska.net             │
│  ┌────────────────────────────┐  │  │  ┌─────────────────────────────────┐  │
│  │ Documents (Markdown)       │  │  │  │ Next Steps Dashboard            │  │
│  │ Version History            │  │  │  │ Progress Tracking               │  │
│  │ Collections (Projects)     │  │  │  │ Action Checklists               │  │
│  │ Public Sharing             │  │  │  │ Owner Assignments               │  │
│  │ Guest Access               │  │  │  │ Embedded Outline Viewer         │  │
│  │ Search                     │  │  │  └─────────────────────────────────┘  │
│  │ Collaboration              │  │  └───────────────────────────────────────┘
│  └────────────────────────────┘  │                    │
└──────────────────────────────────┘                    │
            ▲                                           │
            │ Outline API                               │
            │                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Wowasi_ya (FastAPI)                               │
│                           wowasi.iyeska.net                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Document        │  │ Outline         │  │ Next Steps                  │  │
│  │ Generation      │  │ Integration     │  │ Engine                      │  │
│  │ (existing)      │  │ (new)           │  │ (new)                       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PostgreSQL                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │ Outline DB       │  │ Wowasi DB        │  │ Next Steps DB              │ │
│  │ (5437)           │  │ (SQLite/existing)│  │ (same as Wowasi or new)    │ │
│  └──────────────────┘  └──────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Document Management | Outline Wiki (self-hosted) | Docs, versions, sharing, collaboration |
| Portal Frontend | React + Vite | Next Steps UI only |
| Backend | FastAPI (existing wowasi_ya) | API, generation, Outline integration |
| Database | PostgreSQL (Outline) + SQLite (Wowasi) | Storage |
| Storage | MinIO (S3-compatible) | Outline file uploads |
| Auth | Google OAuth or Zitadel OIDC | Single sign-on |

---

## Port Allocations (per PORT_REGISTRY.md)

| Service | Port | Traefik URL |
|---------|------|-------------|
| outline | 3010 | http://docs.localhost |
| outline-postgres | 5437 | - |
| outline-minio API | 9002 | - |
| outline-minio console | 9003 | http://minio-outline.localhost |
| portal | 3003 | http://portal.localhost |
| wowasi_ya | 8001 | http://wowasi.localhost |

---

## What Outline Provides (Built-in)

No code required for these features:

- **Document viewing** with beautiful markdown rendering
- **Document editing** with real-time collaboration
- **Version history** with diff view and restore
- **Collections** to group the 15 documents per project
- **Public sharing** via link (no login required)
- **Guest access** with view/comment permissions
- **Full-text search** across all documents
- **API access** for programmatic document creation
- **Custom branding** (logo, colors)
- **Custom domain** (docs.iyeska.net)
- **Export** to PDF, Markdown, HTML

---

## What We Build (The Portal Layer)

The differentiator that Outline doesn't provide:

### 1. Next Steps Engine (Backend - FastAPI)

```python
# New endpoints in wowasi_ya
POST /api/v1/projects/{id}/publish-to-outline  # Push docs to Outline
GET  /api/v1/projects/{id}/next-steps          # Get steps for project
PATCH /api/v1/projects/{id}/next-steps/{step}  # Update step status
POST /api/v1/projects/{id}/next-steps/{step}/complete
GET  /api/v1/projects/{id}/progress            # Overall progress metrics
```

### 2. Next Steps Database Schema

```sql
-- Extends existing wowasi_ya SQLite or new PostgreSQL

-- Next step templates (predefined per document type)
CREATE TABLE next_step_templates (
    id INTEGER PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL,  -- project_brief, risks, etc.
    step_order INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    action_type VARCHAR(50) NOT NULL,    -- guidance | checklist | form
    action_config JSON,                   -- type-specific config
    is_required BOOLEAN DEFAULT FALSE
);

-- Project-specific next steps (instances)
CREATE TABLE project_next_steps (
    id INTEGER PRIMARY KEY,
    project_id VARCHAR(36) REFERENCES projects(id),
    template_id INTEGER REFERENCES next_step_templates(id),
    document_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'not_started',  -- not_started | in_progress | completed | skipped
    completed_at TIMESTAMP,
    completed_by VARCHAR(255),  -- email or name
    notes TEXT,
    output_data JSON  -- form responses, checklist items, etc.
);

-- Link wowasi projects to Outline collections
CREATE TABLE outline_mappings (
    id INTEGER PRIMARY KEY,
    project_id VARCHAR(36) REFERENCES projects(id),
    outline_collection_id VARCHAR(36) NOT NULL,
    outline_document_ids JSON,  -- {document_type: outline_doc_id}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Portal Frontend (React - Minimal)

```
portal/
├── src/
│   ├── components/
│   │   ├── NextStepsPanel.tsx      # Main next steps UI
│   │   ├── StepCard.tsx            # Individual step display
│   │   ├── StepChecklist.tsx       # Interactive checkboxes
│   │   ├── StepForm.tsx            # Assign owner, set date
│   │   ├── ProgressBar.tsx         # Visual progress
│   │   └── OutlineEmbed.tsx        # Iframe Outline doc viewer
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx           # List all projects
│   │   ├── Project.tsx             # Single project view
│   │   └── Document.tsx            # Doc (embedded) + next steps
│   │
│   └── hooks/
│       ├── useProject.ts
│       ├── useNextSteps.ts
│       └── useOutline.ts
│
├── Dockerfile
└── package.json
```

**Key insight:** The Portal doesn't render documents—it embeds Outline in an iframe and adds the Next Steps panel alongside.

---

## The Next Steps Framework

This is what makes us different. Each document type has predefined actions.

### Next Steps by Document Type

| Document | Next Steps |
|----------|------------|
| **Project Brief** | Share with stakeholders for feedback, Identify gaps/questions, Schedule kickoff meeting |
| **README** | Verify all links work, Share with new team members, Set reminder to update quarterly |
| **Glossary** | Review with domain experts, Add organization-specific terms |
| **Context & Background** | Validate assumptions with stakeholders, Flag outdated information |
| **Stakeholder Notes** | Assign communication owners, Schedule introductory meetings |
| **Goals & Success Criteria** | Assign metric owners, Set up tracking dashboard, Define baseline measurements |
| **Scope & Boundaries** | Get formal sign-off, Set up change request process |
| **Timeline & Milestones** | Import to project management tool, Assign milestone owners |
| **Initial Budget** | Review with finance, Identify funding sources, Flag items needing quotes |
| **Risks & Assumptions** | Assign risk owners, Schedule risk review meetings, Prioritize mitigation |
| **Process Workflow** | Walk through with team, Identify automation opportunities |
| **SOPs** | Assign procedure owners, Schedule training sessions, Test procedures |
| **Task Backlog** | Import to task management tool, Assign initial tasks, Schedule sprint planning |
| **Status Updates** | Set reporting cadence, Identify report recipients |
| **Meeting Notes** | Schedule recurring meetings, Assign note-taker rotation |

### Action Types

1. **Guidance** - Read-only instructions (no interaction needed)
2. **Checklist** - Interactive checkboxes that track completion
3. **Form** - Input fields (assign owner, set date, add notes)

---

## Implementation Phases

### Phase 1: Outline Deployment (Week 1)

**Goal:** Get Outline running and accessible

- [x] Deploy Outline stack via docker-compose.outline.yml
- [x] Configure authentication (Zitadel OIDC - Google OAuth doesn't support personal Gmail)
- [x] Set up Cloudflare tunnel for docs.iyeska.net
- [x] Create first collection manually to verify everything works
- [x] Generate Outline API key for wowasi_ya integration

**Deliverable:** Outline accessible at https://docs.iyeska.net ✅

**Completed:** 2025-12-30 - API key: `ol...qj2s`, Test collection: "Test Project"

---

### Phase 2: Wowasi → Outline Integration (Week 2)

**Goal:** Generated documents automatically publish to Outline

- [x] Install `outline-wiki-api` Python package
- [x] Create Outline integration service in wowasi_ya (`src/wowasi_ya/core/outline.py`)
- [x] Add `/publish-to-outline` endpoint
- [x] Implement collection creation (one per project)
- [x] Implement document creation (15 docs per collection)
- [ ] Store Outline IDs in wowasi_ya database (deferred to Phase 3)
- [x] Test end-to-end: generate → publish → view in Outline

**Deliverable:** Running `wowasi generate` creates an Outline collection with all 15 docs ✅

**Completed:** 2025-12-30 - API endpoint working, tested with mock project

---

### Phase 3: Next Steps Engine (Weeks 3-4)

**Goal:** Backend support for tracking next steps

- [ ] Create next_step_templates table with data for all 15 doc types
- [ ] Create project_next_steps table
- [ ] Build API endpoints for CRUD on next steps
- [ ] Add progress calculation logic
- [ ] Write tests for next steps engine

**Deliverable:** API returns next steps and tracks completion

---

### Phase 4: Portal Frontend (Weeks 4-5)

**Goal:** Simple React UI for next steps

- [ ] Scaffold React + Vite app in `portal/` directory
- [ ] Build Dashboard page (list projects with progress bars)
- [ ] Build Project page (phase-based view of documents)
- [ ] Build Document page (embedded Outline + next steps panel)
- [ ] Implement checklist and form interactions
- [ ] Add Dockerfile and Traefik labels
- [ ] Deploy to portal.iyeska.net

**Deliverable:** Clients can view projects, see next steps, mark items complete

---

### Phase 5: Polish & Validation (Week 6)

**Goal:** Production readiness

- [ ] Test with 2-3 real client projects
- [ ] Gather feedback on next steps usefulness
- [ ] Refine next steps based on what clients actually do
- [ ] Add error handling and loading states
- [ ] Write user documentation

**Deliverable:** Ready for client use

---

### Future Phases (Post-MVP)

- **Phase 6:** AI-assisted iteration ("improve this section" in Outline)
- **Phase 7:** Notifications (email when someone completes a step)
- **Phase 8:** Integrations (calendar, task managers)
- **Phase 9:** Team features (organizations, permissions)

---

## User Flows

### Flow 1: New Project Generation

```
Client provides project description
         │
         ▼
Wowasi_ya generates 15 documents
         │
         ▼
Wowasi_ya creates Outline collection
         │
         ▼
Wowasi_ya uploads documents to collection
         │
         ▼
Wowasi_ya creates next steps instances
         │
         ▼
Client receives link to Portal dashboard
         │
         ▼
Client views documents in Outline (via Portal embed)
         │
         ▼
Client works through next steps in Portal
```

### Flow 2: Document Iteration

```
Client clicks "Edit" on document in Portal
         │
         ▼
Opens directly in Outline editor
         │
         ▼
Client edits (or requests AI improvement - future)
         │
         ▼
Outline auto-saves with version history
         │
         ▼
Client returns to Portal to continue next steps
```

### Flow 3: Progress Check

```
Client opens Portal dashboard
         │
         ▼
Sees all projects with progress percentages
         │
         ▼
Clicks into project
         │
         ▼
Sees 5 phases with completion status
         │
         ▼
Drills into specific document
         │
         ▼
Works through next steps
```

---

## Technical Considerations

| Concern | Approach |
|---------|----------|
| **Auth** | Google OAuth for Outline; Portal uses same OAuth or session from Outline |
| **Embedding** | Outline supports iframe embedding for public/shared docs |
| **API rate limits** | Cache Outline API responses; batch document creation |
| **Offline Outline** | Portal gracefully degrades; shows cached doc titles |
| **Mobile** | Portal is responsive; Outline has decent mobile support |
| **Multi-tenancy** | Each client gets their own Outline collection; Portal filters by user |

---

## Outline API Integration

### Creating a Collection (Project)

```python
from outline_wiki_api import OutlineClient

client = OutlineClient(
    api_key=settings.outline_api_key,
    base_url="http://outline:3000"  # Internal Docker network
)

# Create collection for project
collection = client.collections.create(
    name=f"Project: {project.name}",
    description=project.description,
    permission="read_write",  # or "read" for view-only clients
)

# Create documents in collection
for doc_type, content in generated_docs.items():
    client.documents.create(
        title=DOC_TITLES[doc_type],
        text=content,
        collection_id=collection.id,
        publish=True
    )
```

### Sharing with Clients

```python
# Option 1: Public link (anyone with link can view)
client.collections.update(
    collection_id=collection.id,
    sharing=True  # Enables public link
)
public_url = f"https://docs.iyeska.net/s/{collection.url_id}"

# Option 2: Guest invite (client needs Outline account)
client.collections.add_user(
    collection_id=collection.id,
    email="client@example.com",
    permission="read"  # or "read_write"
)
```

---

## Cost Analysis

| Item | Build Everything | Outline + Portal |
|------|------------------|------------------|
| Development time | 400-600 hours | 80-120 hours |
| Infrastructure | Same | Same |
| Ongoing maintenance | High | Low |
| Feature velocity | Slow (building basics) | Fast (focus on differentiator) |

**Savings:** ~400 hours of development time by leveraging Outline.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Outline doesn't meet needs | Evaluate during Phase 1; pivot before Phase 2 if issues |
| API limitations | Review Outline API docs thoroughly; test edge cases early |
| Iframe embedding issues | Test embedding in Phase 1; fallback to link-out |
| Outline project abandoned | It's open source with active community; self-hosted = control |
| Client doesn't want another login | Use public sharing for simple cases |

---

## Files Created

- `docker-compose.outline.yml` - Full stack deployment
- `.env.outline.example` - Environment variable template

---

## Next Steps for This Plan

1. [x] Design Outline integration architecture
2. [x] Create Docker Compose for Outline stack
3. [x] Define port allocations
4. [ ] Review and refine with stakeholders
5. [ ] Execute Phase 1: Deploy Outline
6. [ ] Validate embedding and API before building Portal
