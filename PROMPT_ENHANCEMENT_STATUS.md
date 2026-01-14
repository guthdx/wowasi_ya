# Prompt Enhancement Project - Status Report
**Date:** January 13, 2026
**Status:** ✅ Truncation Issue SOLVED - Streaming enabled for long documents
**Current Work:** Evaluating writing quality on test generation
**Next Session:** Review generated docs, tune prompts if AI slop persists

---

## January 13, 2026 - Truncation Fix

### Problem
Documents were being truncated mid-sentence (e.g., SOP ending at "Current stak") due to 8,192 token output limit.

### Solution Implemented
1. **Streaming enabled** in `llm_client.py` for Claude API calls with `max_tokens > 8000`
2. **Token limit increased** to 32,000 in `.env` (`MAX_GENERATION_TOKENS=32000`)
3. **Missing method added** to `quality.py` (`generate_quality_report`)

### Test Results
- **Generated:** 15 complete documents, 55,143 total words
- **Largest document:** SOPs.md at 10,360 words (previously truncated)
- **Published to Outline:** https://docs.iyeska.net/collection/EOIe0xThEw

### Provider Comparison (from research)
| Provider | Max Output Tokens | Cost/1M Output |
|----------|------------------|----------------|
| Claude Sonnet 4.5 | 64,000 | $15 |
| GPT-5.2 | 128,000 | $14 |
| Llama 3.3 70B (local) | 2,048-8,192 | $0 |

**Decision:** Using Claude Sonnet 4.5 for generation solves truncation and may improve writing quality.

---

## Problem Identified

Generated documents were **too generic and not professional enough** - they looked like "entry-level employee's attempt instead of a seasoned, experienced person's output."

**Root Cause:** The local LLM (Llama 3.3 70B) lacks web access and was working with minimal professional scaffolding, resulting in junior-level output.

---

## Solution Implemented

### Two-Stage Intelligence Architecture

```
Stage 1: Claude (with web search)
├─ Frameworks research agent (runs on EVERY project)
│  ├─ Gathers professional standards (SMART, RACI, risk matrices, etc.)
│  ├─ Finds concrete examples of senior-level documentation
│  ├─ Extracts industry templates and best practices
│  └─ Returns detailed frameworks for local LLM to use
│
└─ Domain agents gather project-specific research

Stage 2: Llama (or Claude fallback)
├─ Receives frameworks research from Stage 1
├─ Uses document-type-specific expert prompts (ALL 15 NOW ENHANCED)
├─ Generates with senior-level quality markers
└─ Cross-references previous documents
```

---

## All 15 Enhanced Prompts

### Phase 1 - Pilot Documents (December 15, 2025)

**1. Initial Budget (`_build_budget_prompt()`)**
- Role: "Senior Program Director with 15+ years managing multi-million dollar budgets"
- Requirements: 7+ sections, 1500+ words, budget summary table
- Structure: Budget Overview, Personnel, Operating, Indirect, Narrative, ROI, Risks
- Quality markers: Strategic thinking, evidence-based, anticipatory, risk-aware

**2. Risks and Assumptions (`_build_risks_prompt()`)**
- Role: "Senior Risk Management Analyst with 15+ years"
- Requirements: 9+ sections, 8-12 risks, 2000+ words, risk register table
- Structure: Overview, Matrix, Strategic/Operational/Financial/Compliance Risks, Assumptions
- Quality markers: Quantitative assessment, specificity, actionable mitigation, cascading analysis

**3. SOPs (`_build_sops_prompt()`)**
- Role: "Senior Operations Manager with 15+ years"
- Requirements: 8+ sections, 6-8 complete SOPs, 2000+ words, RACI matrix
- Structure: Overview, RACI, Core Procedures, Communications, Quality, Change Management
- Quality markers: Procedural clarity, tool-specific, exception handling, quality gates

### Phase 2 - Strategic Documents (December 27, 2025)

**4. Goals and Success Criteria (`_build_goals_prompt()`)**
- Role: "Senior Strategic Planner with 15+ years"
- Requirements: 8+ sections, 2000+ words, SMART goals table, OKR framework
- Structure: Executive Summary, Strategic Vision, Objectives, KPIs, Success Metrics, Dependencies
- Quality markers: SMART format, measurable targets, baseline comparisons, milestone tracking
- Includes: Metrics tracking table with baselines/targets/measurement methods

**5. Timeline and Milestones (`_build_timeline_prompt()`)**
- Role: "Senior Project Manager with 15+ years (PMP preferred)"
- Requirements: 8+ sections, 1800+ words, Gantt-style ASCII timeline
- Structure: Overview, Critical Path, Phase Breakdown, Dependencies, Risk Buffers, Resource Loading
- Quality markers: Critical path identification, float calculations, dependency mapping
- Includes: ASCII timeline visualization with milestones

**6. Project Brief (`_build_project_brief_prompt()`)**
- Role: "Senior Program Director with 15+ years writing executive briefings"
- Requirements: 10+ sections, 2000+ words, executive summary format
- Structure: One-Page Summary, Background, Objectives, Scope, Budget, Timeline, Team, Risks, Success Criteria, Approvals
- Quality markers: Decision-enabling, C-suite ready, strategic alignment, investment thesis

**7. Stakeholder Notes (`_build_stakeholder_prompt()`)**
- Role: "Senior Stakeholder Engagement Specialist with 15+ years"
- Requirements: 9+ sections, 2000+ words, power/interest grid, RACI matrix
- Structure: Overview, Mapping, Power/Interest Analysis, Engagement Strategy, Communication Plan
- Quality markers: Political awareness, influence mapping, engagement cadence, risk identification
- Includes: Power/Interest grid visualization, stakeholder register table

### Phase 3 - Planning Documents (December 27, 2025)

**8. Scope and Boundaries (`_build_scope_prompt()`)**
- Role: "Senior Project Manager with 15+ years of scope management experience"
- Requirements: 10+ sections, 1800+ words, in-scope/out-of-scope tables
- Structure: Executive Summary, In-Scope, Out-of-Scope, Deliverables, Constraints, Assumptions, Change Control
- Quality markers: Clear boundaries, scope creep prevention, change management process
- Includes: Deliverables table with acceptance criteria

**9. Process Workflow (`_build_process_workflow_prompt()`)**
- Role: "Senior Process Engineer with 15+ years in process design"
- Requirements: 8+ sections, 2000+ words, ASCII process diagrams
- Structure: Overview, Core Workflows, Decision Points, Handoffs, Exception Handling, Integration
- Quality markers: Clear swim lanes, decision logic, error handling, SLA awareness
- Includes: ASCII workflow diagrams for each major process

**10. Context and Background (`_build_context_prompt()`)**
- Role: "Senior Policy Analyst with 15+ years in environmental scanning"
- Requirements: 9+ sections, 2000+ words, PESTLE analysis table
- Structure: Executive Summary, Historical, Current State, PESTLE Analysis, Stakeholder Landscape, Gaps, Opportunities
- Quality markers: Evidence-based, properly cited, systems thinking, tribal/cultural context
- Includes: PESTLE analysis table with implications

### Phase 4 - Operational Documents (December 27, 2025)

**11. Task Backlog (`_build_task_backlog_prompt()`)**
- Role: "Senior Agile Coach with 15+ years in project delivery"
- Requirements: 8+ sections, 1800+ words, prioritized task tables
- Structure: Overview, Epic Breakdown, Sprint/Phase Planning, MoSCoW Prioritization, Dependencies, Acceptance Criteria
- Quality markers: Clear prioritization, effort estimation, dependency awareness, definition of done
- Includes: Backlog table with MoSCoW priority and effort estimates

**12. Meeting Notes (`_build_meeting_notes_prompt()`)**
- Role: "Senior Executive Assistant with 15+ years supporting C-suite"
- Requirements: 6+ sections, meeting templates, action item tracking
- Structure: Template Overview, Kickoff Agenda, Status Meeting Template, Decision Log, Action Items, RACI
- Quality markers: Clear ownership, deadline tracking, decision documentation, escalation paths
- Includes: Meeting agenda template, action item tracker table

**13. Status Updates (`_build_status_updates_prompt()`)**
- Role: "Senior PMO Director with 15+ years in executive reporting"
- Requirements: 8+ sections, 1500+ words, RAG status dashboard
- Structure: Executive Dashboard, Overall Status, Milestone Progress, Budget Status, Risks, Escalations, Next Period
- Quality markers: RAG indicators, trend analysis, variance reporting, executive-ready
- Includes: RAG status table with trend indicators

### Phase 5 - Reference Documents (December 27, 2025)

**14. README (`_build_readme_prompt()`)**
- Role: "Senior Technical Writer with 15+ years in documentation"
- Requirements: 10+ sections, 1500+ words, document navigation table
- Structure: Project Overview, Quick Start, Document Index, Team, Contact, FAQ, Changelog
- Quality markers: Scannable, well-organized, cross-referenced, onboarding-friendly
- Includes: Document navigation table with links to all 15 docs

**15. Glossary (`_build_glossary_prompt()`)**
- Role: "Senior Technical Editor with 15+ years in terminology management"
- Requirements: 6+ sections, 1200+ words, A-Z definitions
- Structure: Overview, Project Terms, Domain Terms, Acronyms, Cross-References, Sources
- Quality markers: Consistent format, cross-referenced, context-appropriate, tribal/cultural sensitivity
- Includes: Alphabetized definition tables with sources

---

## Technical Implementation

### Prompt Routing (generator.py:207-236)

```python
prompt_builders = {
    # Phase 1 - Enhanced pilot documents
    DocumentType.INITIAL_BUDGET: self._build_budget_prompt,
    DocumentType.RISKS_ASSUMPTIONS: self._build_risks_prompt,
    DocumentType.SOPS: self._build_sops_prompt,
    # Phase 2 - Strategic documents
    DocumentType.GOALS_SUCCESS: self._build_goals_prompt,
    DocumentType.TIMELINE_MILESTONES: self._build_timeline_prompt,
    DocumentType.PROJECT_BRIEF: self._build_project_brief_prompt,
    DocumentType.STAKEHOLDER_NOTES: self._build_stakeholder_prompt,
    # Phase 3 - Planning documents
    DocumentType.SCOPE_BOUNDARIES: self._build_scope_prompt,
    DocumentType.PROCESS_WORKFLOW: self._build_process_workflow_prompt,
    DocumentType.CONTEXT_BACKGROUND: self._build_context_prompt,
    # Phase 4 - Operational documents
    DocumentType.TASK_BACKLOG: self._build_task_backlog_prompt,
    DocumentType.MEETING_NOTES: self._build_meeting_notes_prompt,
    DocumentType.STATUS_UPDATES: self._build_status_updates_prompt,
    # Phase 5 - Reference documents
    DocumentType.README: self._build_readme_prompt,
    DocumentType.GLOSSARY: self._build_glossary_prompt,
}
```

### Each Prompt Includes

1. **Expert Persona** - Senior-level role with 15+ years experience
2. **Project Context** - Name, description, domain, key constraints
3. **Research Findings** - Compiled from Claude web search agents
4. **Frameworks Knowledge** - Professional standards from frameworks agent
5. **Previous Documents** - Cross-reference context for consistency
6. **Required Structure** - Specific sections and formatting
7. **GOOD vs BAD Examples** - Show what senior-level looks like
8. **Quality Markers** - Specific traits to demonstrate
9. **Strict Constraints** - Hallucination prevention, format rules
10. **Output Format** - Markdown with tables/diagrams

---

## Test Results (Phase 1)

### Test Project Details
- **Name:** Tribal Youth Mentorship Program
- **Generation Provider:** Claude (Mac was offline during test)
- **Command:** `wowasi generate "Tribal Youth Mentorship..." --skip-privacy`

### Quality Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Total Words** | 765 (errors) | 16,569 | 21.6x increase |
| **Budget Quality** | Error | 2,500+ words, 7 sections | ✅ Senior-level |
| **Risks Quality** | Error | 12 risks, full analysis | ✅ Senior-level |
| **SOPs Quality** | Error | 8 SOPs, RACI matrix | ✅ Senior-level |

### Example Quality Comparison

**BEFORE (Generic Prompt):**
> "We need a Program Coordinator ($70,000) to manage the project."

**AFTER (Enhanced Prompt):**
> "Program Director (1.0 FTE, $75,000-$85,000): This senior position requires extensive experience in tribal youth programming, cultural competency, and program management. The salary range reflects regional nonprofit leadership compensation and the specialized skills required to navigate tribal governance structures, federal compliance requirements, and community cultural protocols. This investment prevents the high turnover rates that plague underfunded youth programs and ensures continuity essential for building trust with participants and families."

---

## Files Modified

### Core Business Logic
- `src/wowasi_ya/core/agent_discovery.py` - Added frameworks agent
- `src/wowasi_ya/core/research.py` - Added frameworks research prompt
- `src/wowasi_ya/core/generator.py` - Added 15 specialized prompts + dictionary-based routing

### Configuration
- `.env` - Temporarily set to `GENERATION_PROVIDER=claude` for testing
- **Production should use:** `GENERATION_PROVIDER=llamacpp` (local Llama 3.3 70B)

---

## Quality Checker Improvements (December 31, 2025)

Added comprehensive quality validation to `src/wowasi_ya/core/quality.py`:

### Truncation Detection
- Detects incomplete documents (unbalanced code blocks, mid-sentence endings)
- Automatic retry with same token limits (prevents wasteful escalation)
- Reports truncation reason in quality output

### Content Quality Checks
- **Generic Filler Detection** - Flags phrases like "in today's", "plays a crucial role", "furthermore"
- **AI Vocabulary Detection** - Catches words like "delve", "tapestry", "leverage", "seamlessly"
- **Specificity Scoring** - Measures placeholder usage vs concrete details
- **Sentence Variety Analysis** - Checks for natural length variation (burstiness)

### Quality Grading
- A-F grades based on aggregate score
- Separate error/warning/info counts
- Per-document breakdown with word counts

### Generator Changes
- Added `_is_content_truncated()` function
- Retry logic for truncated documents (max 3 attempts)
- Token limits capped at 8192 to avoid Claude streaming requirement

---

## Next Steps

### Immediate (Testing Phase)

1. [ ] Run test generation with quality improvements
2. [ ] Review quality report output
3. [ ] Implement HUMAN_WRITING_STYLE constant (see plan file)
4. [ ] Inject style guide into all 15 prompt builders
5. [ ] Re-test and verify quality score > 70%

### Phase 2: Eliminate AI Writing Tells (Planned)

Add `HUMAN_WRITING_STYLE` constant to generator.py with:
- Banned AI vocabulary (delve, leverage, seamlessly, etc.)
- Em dash usage limits
- Sentence variety requirements
- Formulaic transition bans
- Good/bad style examples

See plan file: `~/.claude/plans/compiled-sleeping-quail.md`

### Future Enhancements

1. **Context-Specific Prompts** - Add industry/domain-specific variations (healthcare, education, tribal governance)
2. **Prompt Tuning** - Adjust based on real-world feedback
3. **Template Library** - Allow users to select prompt intensity (brief vs comprehensive)
4. **Multi-Language Support** - Lakota/Dakota terminology integration

---

## Success Criteria

✅ **COMPLETED:**
- Frameworks research agent created and tested
- All 15 document prompts enhanced with senior-level expert personas
- Dictionary-based routing for clean code architecture
- GOOD/BAD examples in each prompt for quality guidance
- Cross-document consistency enforcement
- Hallucination prevention guards in all prompts

⏳ **Pending:**
- Production testing with Llama 3.3 70B
- Performance benchmarking (token usage, generation time)
- User feedback on document quality
- CLAUDE.md documentation update
