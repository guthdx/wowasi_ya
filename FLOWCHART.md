# Wowasi_ya System Flow

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                               │
│  "Create documentation for my healthcare patient portal app"    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 0: AGENT DISCOVERY                      │
│                         (LOCAL - NO API)                         │
│                                                                  │
│  • Parse keywords (healthcare, patient, portal)                 │
│  • Match domains (HIPAA, medical, security)                     │
│  • Generate research agents (3-7 agents)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRIVACY SCREENING                             │
│                    (LOCAL - NO API)                              │
│                                                                  │
│  • Scan for PII/PHI (Presidio)                                  │
│  • Flag sensitive data                                          │
│  • Show findings to user                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  USER APPROVES? │
                    └────┬──────┬────┘
                        YES    NO
                         │      └──> CANCEL
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 1: RESEARCH                               │
│                  PROVIDER: CLAUDE API                            │
│                  (WEB SEARCH ENABLED)                            │
│                                                                  │
│  Each research agent:                                           │
│  1. Searches web for current information                        │
│  2. Finds regulations (HIPAA, compliance)                       │
│  3. Gathers best practices                                      │
│  4. Compiles findings                                           │
│                                                                  │
│  Example agents:                                                │
│  • HIPAA Compliance Researcher                                  │
│  • Healthcare Security Analyst                                  │
│  • Patient Data Privacy Specialist                              │
│                                                                  │
│  Cost: ~$2-5 per project                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: DOCUMENT GENERATION                        │
│              PROVIDER: LLAMA 3.3 70B (PRIMARY)                   │
│              VIA: Cloudflare Tunnel (llama.iyeska.net)          │
│              FALLBACK: Claude API (if Mac offline)              │
│                                                                  │
│  Generate 15 documents in 5 batches:                            │
│                                                                  │
│  Batch 1 - Overview (3 docs)                                    │
│    ├─ README.md                                                 │
│    ├─ Project-Brief.md                                          │
│    └─ Glossary.md                                               │
│                                                                  │
│  Batch 2 - Discovery (2 docs)                                   │
│    ├─ Context-and-Background.md                                 │
│    └─ Stakeholder-Notes.md                                      │
│                                                                  │
│  Batch 3 - Planning (5 docs)                                    │
│    ├─ Goals-and-Success-Criteria.md                             │
│    ├─ Scope-and-Boundaries.md                                   │
│    ├─ Initial-Budget.md                                         │
│    ├─ Timeline-and-Milestones.md                                │
│    └─ Risks-and-Assumptions.md                                  │
│                                                                  │
│  Batch 4 - Execution (3 docs)                                   │
│    ├─ Process-Workflow.md                                       │
│    ├─ SOPs.md                                                   │
│    └─ Task-Backlog.md                                           │
│                                                                  │
│  Batch 5 - Communications (2 docs)                              │
│    ├─ Meeting-Notes.md                                          │
│    └─ Status-Updates.md                                         │
│                                                                  │
│  Each document:                                                 │
│  • Uses research findings as context                            │
│  • References previous docs for consistency                     │
│  • Professional, structured markdown                            │
│                                                                  │
│  Cost: $0 (local inference) or ~$3-10 (Claude fallback)        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                PHASE 3: QUALITY CHECK                            │
│                (LOCAL - NO API)                                  │
│                                                                  │
│  • Cross-reference all 15 documents                             │
│  • Check for consistency                                        │
│  • Validate completeness                                        │
│  • Flag issues for review                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 4: OUTPUT                                 │
│                  (LOCAL - NO API)                                │
│                                                                  │
│  Write documents to:                                            │
│  • Filesystem (./output/)                                       │
│  • Obsidian vault (optional)                                    │
│  • Git repository (optional)                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   COMPLETE!    │
                    │  15 documents  │
                    └────────────────┘
```

---

## Network Flow: Where Things Happen

```
┌──────────────────────────────────────────────────────────────────┐
│                     M4 MAC (YOUR LAPTOP)                          │
│                     Location: Anywhere                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Llama CPP Server (localhost:8080)                          │ │
│  │ Model: Llama 3.3 70B Instruct Q4_K_M                       │ │
│  │ Purpose: Document Generation (Phase 2)                     │ │
│  │ Cost: $0                                                   │ │
│  └─────────────────────────┬──────────────────────────────────┘ │
│                            │                                     │
│  ┌────────────────────────▼──────────────────────────────────┐ │
│  │ Cloudflare Tunnel                                         │ │
│  │ Exposes: https://llama.iyeska.net                        │ │
│  │ Target: localhost:8080                                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               │ HTTPS via Cloudflare
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│              UBUNTU SERVER (IYESKA - 192.168.11.20)               │
│              Location: IYESKA Network                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Wowasi Backend (Port 8001)                                 │ │
│  │                                                             │ │
│  │ Phase 0: Agent Discovery      → Local processing           │ │
│  │ Phase 1: Privacy Check        → Local processing           │ │
│  │ Phase 2: Research             → Calls Claude API ──────────┼─┐
│  │ Phase 3: Document Generation  → Calls llama.iyeska.net     │ │
│  │                                  (your Mac via Cloudflare) │ │
│  │ Phase 4: Quality Check        → Local processing           │ │
│  │ Phase 5: Output               → Local filesystem           │ │
│  └─────────────────────────┬──────────────────────────────────┘ │
│                            │                                     │
│  ┌────────────────────────▼──────────────────────────────────┐ │
│  │ Cloudflare Tunnel                                         │ │
│  │ Exposes: https://wowasi.iyeska.net                       │ │
│  │ Target: localhost:8001                                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────────┘
                               │                                    │
                               │ HTTPS                              │
                               │                              HTTPS │
┌──────────────────────────────▼───────────┐                       │
│            END USERS                      │                       │
│   (via https://wowasi.iyeska.net)        │                       │
└───────────────────────────────────────────┘                       │
                                                                    │
┌───────────────────────────────────────────────────────────────────▼──┐
│                        CLAUDE API (Anthropic)                         │
│                        Purpose: Research with Web Search              │
│                        Cost: ~$2-5 per project                        │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Provider Decision Flow

```
                    ┌──────────────────────┐
                    │  Phase 1: Research   │
                    └──────────┬───────────┘
                               │
                               │ Always uses Claude
                               │ (web search required)
                               │
                               ▼
                    ┌──────────────────────┐
                    │   CLAUDE API         │
                    │   + Web Search       │
                    └──────────┬───────────┘
                               │
                               │ Research complete
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Phase 2: Generation  │
                    └──────────┬───────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │ Check: Is Mac Llama online?  │
                │ (Health check to Mac)        │
                └────┬──────────────────┬──────┘
                     │                  │
                    YES                NO
                     │                  │
                     ▼                  ▼
          ┌──────────────────┐   ┌─────────────────┐
          │  LLAMA 3.3 70B   │   │  CLAUDE API     │
          │  (via Cloudflare)│   │  (Fallback)     │
          │  Cost: $0        │   │  Cost: ~$3-10   │
          └──────────────────┘   └─────────────────┘
                     │                  │
                     └────────┬─────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │ 15 Documents     │
                   │ Generated        │
                   └──────────────────┘
```

---

## Cost Breakdown by Phase

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE              │ PROVIDER        │ COST                  │
├─────────────────────────────────────────────────────────────┤
│ 0. Discovery       │ Local           │ $0                    │
│ 1. Privacy Check   │ Local           │ $0                    │
│ 2. Research        │ Claude API      │ $2-5                  │
│ 3. Generation      │ Llama (Primary) │ $0                    │
│                    │ Claude (Fallback)│ $3-10 (if needed)    │
│ 4. Quality Check   │ Local           │ $0                    │
│ 5. Output          │ Local           │ $0                    │
├─────────────────────────────────────────────────────────────┤
│ TOTAL (typical)    │ Hybrid          │ $2-5 per project      │
│ TOTAL (Mac offline)│ Full Claude     │ $5-15 per project     │
├─────────────────────────────────────────────────────────────┤
│ Old (Full Claude)  │ Claude Only     │ $5-15 per project     │
│ SAVINGS            │                 │ 60-70%                │
└─────────────────────────────────────────────────────────────┘
```

---

## Timeline: Typical Project Generation

```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│  0-2s    │ Phase 0: Agent Discovery (local keyword matching)   │
│          │                                                      │
│  2-5s    │ Privacy Check (local PII/PHI scan)                  │
│          │                                                      │
│  5-8s    │ User reviews and approves privacy flags             │
│          │                                                      │
│  8-30s   │ Phase 1: Research (3-7 agents × Claude API)        │
│          │         Each agent searches web, compiles findings  │
│          │                                                      │
│  30-180s │ Phase 2: Generation (15 documents × Llama)         │
│          │         • Batch 1: Overview (3 docs)   ~20s         │
│          │         • Batch 2: Discovery (2 docs)  ~15s         │
│          │         • Batch 3: Planning (5 docs)   ~40s         │
│          │         • Batch 4: Execution (3 docs)  ~25s         │
│          │         • Batch 5: Comms (2 docs)      ~15s         │
│          │                                                      │
│  180-185s│ Phase 3: Quality Check (local validation)           │
│          │                                                      │
│  185-190s│ Phase 4: Output (write to filesystem)               │
│          │                                                      │
│  DONE!   │ Total: ~3-4 minutes for complete project            │
│          │                                                      │
└────────────────────────────────────────────────────────────────┘

Note: Times vary based on:
- Llama inference speed (M4 GPU performance)
- Claude API response time
- Network latency to Cloudflare
```

---

## Data Sovereignty & Privacy

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHERE YOUR DATA LIVES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ YOUR INFRASTRUCTURE (Full Control)                     │    │
│  │                                                         │    │
│  │  • User input: Ubuntu server                           │    │
│  │  • Agent discovery: Ubuntu server (local)              │    │
│  │  • Privacy screening: Ubuntu server (local)            │    │
│  │  • Document generation: M4 Mac (local inference)       │    │
│  │  • Quality check: Ubuntu server (local)                │    │
│  │  • Output files: Ubuntu server (local filesystem)      │    │
│  │  • Audit logs: Ubuntu server (local database)          │    │
│  │                                                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ EXTERNAL SERVICES (Temporary, Privacy-Approved)        │    │
│  │                                                         │    │
│  │  • Research queries: Claude API (after user approval)  │    │
│  │    - Sanitized text only (PII removed if requested)    │    │
│  │    - Web search results                                │    │
│  │    - Logged in audit trail                             │    │
│  │                                                         │    │
│  │  • Document generation: Claude API (fallback only)     │    │
│  │    - Only when Mac offline                             │    │
│  │    - Also logged in audit trail                        │    │
│  │                                                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Example: Healthcare Project Flow

```
INPUT:
------
Project Name: "Patient Portal MVP"
Description: "HIPAA-compliant web app for patients to view medical
             records, schedule appointments, and message doctors"

STEP 1 - DISCOVERY (Local, 2s):
--------------------------------
Keywords extracted: patient, medical, HIPAA, appointments, doctors
Domains matched: Healthcare, HIPAA Compliance, Security, Web Applications
Agents generated:
  1. HIPAA Compliance Researcher
  2. Healthcare Security Analyst
  3. Patient Data Privacy Specialist
  4. Medical Records Management Expert
  5. Healthcare UX Researcher

STEP 2 - PRIVACY CHECK (Local, 3s):
------------------------------------
Scanning input... ✓ No PII/PHI detected
Ready for API calls

STEP 3 - RESEARCH (Claude API, 25s):
-------------------------------------
Agent 1 (HIPAA): Searches "HIPAA compliance requirements 2025"
  → Finds: Latest regulations, technical safeguards, BAAs
  → Cost: ~$0.50

Agent 2 (Security): Searches "healthcare web app security best practices"
  → Finds: Encryption standards, audit logging, access controls
  → Cost: ~$0.50

Agent 3 (Privacy): Searches "patient data privacy regulations"
  → Finds: State laws, consent requirements, data retention
  → Cost: ~$0.50

... (agents 4 & 5 execute in parallel)

Total research: ~$2.50

STEP 4 - GENERATION (Llama via Cloudflare, 120s):
--------------------------------------------------
Batch 1 (Overview):
  ✓ README.md - Project overview with HIPAA context
  ✓ Project-Brief.md - MVP scope with compliance requirements
  ✓ Glossary.md - Healthcare & technical terms

Batch 2 (Discovery):
  ✓ Context-and-Background.md - Healthcare landscape, regulations
  ✓ Stakeholder-Notes.md - Patients, doctors, admin staff

Batch 3 (Planning):
  ✓ Goals-and-Success-Criteria.md - HIPAA certification, UX metrics
  ✓ Scope-and-Boundaries.md - MVP features, compliance boundaries
  ✓ Initial-Budget.md - Development, compliance audit, hosting
  ✓ Timeline-and-Milestones.md - Development phases, certification
  ✓ Risks-and-Assumptions.md - Compliance risks, tech assumptions

Batch 4 (Execution):
  ✓ Process-Workflow.md - Development workflow with security review
  ✓ SOPs.md - Deployment, incident response, audit procedures
  ✓ Task-Backlog.md - Prioritized tasks with compliance items

Batch 5 (Communications):
  ✓ Meeting-Notes.md - Template for stakeholder meetings
  ✓ Status-Updates.md - Template for progress reports

Cost: $0 (local Llama)

STEP 5 - QUALITY CHECK (Local, 5s):
------------------------------------
Cross-referencing documents...
✓ HIPAA mentioned consistently across all docs
✓ Budget aligns with timeline
✓ Risks referenced in scope and goals
No issues found.

STEP 6 - OUTPUT (Local, 2s):
-----------------------------
Writing 15 documents to:
  /home/guthdx/projects/wowasi_ya/output/Patient-Portal-MVP/

COMPLETE!
---------
Total time: 3 minutes 37 seconds
Total cost: $2.50
Documents: 15 professional markdown files
```

---

## Key Advantages of This Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  ✓ COST EFFECTIVE                                            │
│    60-70% cheaper than full Claude                           │
│    $2-5 vs $5-15 per project                                 │
│                                                               │
│  ✓ PRIVACY FIRST                                             │
│    Document generation happens locally on your Mac           │
│    Only research queries go to external API                  │
│    User approval required before any API calls               │
│                                                               │
│  ✓ LOCATION INDEPENDENT                                      │
│    Works from home, coffee shop, hotel, conference           │
│    Cloudflare Tunnel handles routing (no VPN)                │
│    Mac just needs internet connection                        │
│                                                               │
│  ✓ RESILIENT                                                 │
│    Auto-fallback to Claude if Mac offline                    │
│    Always produces results                                   │
│    Health monitoring built-in                                │
│                                                               │
│  ✓ FUTURE-PROOF                                              │
│    Easy to swap providers (abstraction layer)                │
│    Can add new models without changing core code             │
│    Well-documented migration paths                           │
│                                                               │
│  ✓ QUALITY CONTROLLED                                        │
│    Web search for current information (research)             │
│    Cross-reference validation (quality check)                │
│    Audit logging (compliance)                                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```
