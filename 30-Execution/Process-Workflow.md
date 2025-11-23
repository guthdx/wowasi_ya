# Process Workflow

## End-to-End Project Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                │
│  Project description entered via Web UI or CLI                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 0: AGENT DISCOVERY                      │
│  1. Parse description for keywords                               │
│  2. Match against domain keyword map                             │
│  3. Detect domain intersections                                  │
│  4. Identify stakeholder mentions                                │
│  5. Generate ad hoc agent definitions                            │
│  6. Build execution plan                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRIVACY LAYER CHECK                           │
│  1. Scan for PHI/PII patterns                                    │
│  2. Flag tribal-specific sensitive terms                         │
│  3. Present flagged content to user                              │
│  4. User approves/modifies before proceeding                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: RESEARCH                             │
│  1. Execute generated research agents (via Claude API)           │
│  2. Conduct web searches for:                                    │
│     - Regulations and compliance                                 │
│     - Grants and funding                                         │
│     - Best practices and similar projects                        │
│  3. Compile research brief                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: DOCUMENT GENERATION                  │
│  Batch 1 (parallel): README, Project-Brief, Glossary, Context    │
│  Batch 2: Stakeholder-Notes, Goals, Scope                        │
│  Batch 3: Budget, Timeline, Risks                                │
│  Batch 4: Workflow, SOPs, Task-Backlog                           │
│  Batch 5 (parallel): Meeting-Notes, Status-Updates templates     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: QUALITY CHECK                        │
│  1. Cross-reference consistency                                  │
│  2. Glossary term validation                                     │
│  3. Goal-scope alignment check                                   │
│  4. Flag any warnings/gaps                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT GENERATION                             │
│  1. Write to filesystem (folder structure)                       │
│  2. Export to Obsidian vault (if configured)                     │
│  3. Initialize git repo (if configured)                          │
│  4. Log generation metadata                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER NOTIFICATION                             │
│  Display: completion status, document links, any warnings        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Step Descriptions

### Step 1: User Input
**Responsible:** User
**Input:** Project idea/description (free text)
**Output:** Structured input object

**Process:**
1. User accesses Web UI or CLI
2. Enters project name
3. Enters project description (paragraph to page)
4. Optionally specifies:
   - Known stakeholders
   - Known constraints
   - Target timeline
   - Budget range
   - Output preferences

---

### Step 2: Agent Discovery (Phase 0)
**Responsible:** System (local processing)
**Input:** Project description
**Output:** Agent definitions + execution plan

**Process:**
1. Extract keywords using pattern matching
2. Match keywords against `domain_keyword_map`
3. Check for domain intersections (e.g., healthcare + community)
4. Scan for stakeholder mentions
5. Generate agent YAML definitions
6. Determine parallel vs. sequential execution

**Data Stays Local:** Yes - no API call yet

---

### Step 3: Privacy Layer Check
**Responsible:** System + User
**Input:** Project description + agent prompts
**Output:** Approved/sanitized content for API

**Process:**
1. Scan all text for PHI patterns (SSN, DOB, names, etc.)
2. Scan for PII patterns (addresses, phone numbers, etc.)
3. Flag tribal-specific terms based on sensitivity list
4. Present flagged items to user with context
5. User can:
   - Approve as-is
   - Modify/redact specific items
   - Cancel generation
6. Record approval in audit log

**User Interaction Required:** Yes

---

### Step 4: Research Execution (Phase 1)
**Responsible:** System (Claude API)
**Input:** Approved agent prompts
**Output:** Research findings

**Process:**
1. Execute each research agent via Claude API
2. Each agent conducts web searches as needed
3. Compile findings into structured format
4. Merge into unified research brief
5. Log API interactions

**API Calls:** Yes - logged for audit

---

### Step 5: Document Generation (Phase 2)
**Responsible:** System (Claude API)
**Input:** Research brief + project context
**Output:** 15 markdown documents

**Process:**
1. Generate Batch 1 documents (foundation)
2. Generate Batch 2 (stakeholders + goals)
3. Generate Batch 3 (planning)
4. Generate Batch 4 (execution)
5. Generate Batch 5 (templates)
6. Each batch uses output from previous batches for consistency

**API Calls:** Yes - logged for audit

---

### Step 6: Quality Check (Phase 3)
**Responsible:** System (local processing)
**Input:** Generated documents
**Output:** Validated documents + warnings

**Process:**
1. Extract all glossary terms, verify used consistently
2. Compare goals to scope items
3. Verify budget categories match activities
4. Check timeline milestones against goals
5. Generate warning list for any inconsistencies
6. Flag gaps or missing information

**Data Stays Local:** Yes

---

### Step 7: Output Generation
**Responsible:** System
**Input:** Validated documents
**Output:** Files in configured destinations

**Process:**
1. Create folder structure per starter kit template
2. Write all 15 documents to filesystem
3. If Obsidian configured: copy to vault with proper linking
4. If Git configured: init repo, commit, optionally push
5. Generate metadata file with:
   - Generation timestamp
   - Agents used
   - Sources consulted
   - Warnings

---

### Step 8: User Notification
**Responsible:** System
**Input:** Generation results
**Output:** User-facing summary

**Process:**
1. Display success/failure status
2. List generated documents with links
3. Show any warnings from quality check
4. Provide next steps guidance
5. Offer option to regenerate specific docs

---

## Responsibility Matrix (RACI)

| Step | User | System | Claude API |
|------|------|--------|------------|
| 1. Input | R,A | I | - |
| 2. Agent Discovery | I | R,A | - |
| 3. Privacy Check | A | R | - |
| 4. Research | I | R | A |
| 5. Doc Generation | I | R | A |
| 6. Quality Check | I | R,A | - |
| 7. Output | I | R,A | - |
| 8. Notification | I | R,A | - |

*R=Responsible, A=Accountable, I=Informed*
