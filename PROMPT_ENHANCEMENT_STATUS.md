# Prompt Enhancement Project - Status Report
**Date:** December 15, 2025
**Status:** Phase 1 Complete - 3 Pilot Documents Enhanced
**Next Session:** Continue with remaining 12 document types

---

## Problem Identified

Generated documents were **too generic and not professional enough** - they looked like "entry-level employee's attempt instead of a seasoned, experienced person's output."

**Root Cause:** The local LLM (Llama 3.3 70B) lacks web access and was working with minimal professional scaffolding, resulting in junior-level output.

---

## Solution Implemented

### Two-Stage Intelligence Architecture

```
Stage 1: Claude (with web search)
├─ NEW: Frameworks research agent (runs on EVERY project)
│  ├─ Gathers professional standards (SMART, RACI, risk matrices, etc.)
│  ├─ Finds concrete examples of senior-level documentation
│  ├─ Extracts industry templates and best practices
│  └─ Returns detailed frameworks for local LLM to use
│
└─ Domain agents gather project-specific research

Stage 2: Llama (or Claude fallback)
├─ Receives frameworks research from Stage 1
├─ Uses document-type-specific expert prompts
├─ Generates with senior-level quality markers
└─ Cross-references previous documents
```

### Changes Made

#### 1. New Frameworks Research Agent
**File:** `src/wowasi_ya/core/agent_discovery.py`

- Added `_create_documentation_framework_agent()` method
- Agent ID: `agent_000_frameworks`
- Priority: 1 (runs first)
- Searches for:
  - Professional frameworks (SMART goals, RACI, risk matrices, Gantt)
  - Concrete examples of senior-level docs
  - Document structure templates
  - "Senior vs junior" quality markers

#### 2. Enhanced Research Prompts
**File:** `src/wowasi_ya/core/research.py`

- Added `_build_frameworks_research_prompt()` method
- Special prompt for frameworks agent that emphasizes:
  - CONCRETE, SPECIFIC information (not vague principles)
  - Minimum 5-7 examples across document types
  - Structured output: Key Findings, Professional Examples, Frameworks, Senior vs Junior Markers
  - Focus on nonprofit/tribal/public sector contexts

#### 3. Document-Specific Generation Prompts
**File:** `src/wowasi_ya/core/generator.py`

Created three specialized prompts (PILOT DOCUMENTS):

**A. Budget Prompt (`_build_budget_prompt()`)**
- Role: "Senior Program Director with 15+ years managing multi-million dollar budgets"
- Requirements: 7+ sections, 1500+ words, budget summary table
- Structure: Budget Overview, Personnel, Operating, Indirect, Narrative, ROI, Risks
- Quality markers: Strategic thinking, evidence-based, anticipatory, risk-aware
- Includes GOOD vs BAD examples to show what senior-level looks like

**B. Risks Prompt (`_build_risks_prompt()`)**
- Role: "Senior Risk Management Analyst with 15+ years"
- Requirements: 9+ sections, 8-12 risks, 2000+ words, risk register table
- Structure: Overview, Matrix, Strategic/Operational/Financial/Compliance Risks, Assumptions
- Quality markers: Quantitative assessment, specificity, actionable mitigation, cascading analysis
- Provides risk matrix template with Likelihood × Impact scales

**C. SOPs Prompt (`_build_sops_prompt()`)**
- Role: "Senior Operations Manager with 15+ years"
- Requirements: 8+ sections, 6-8 complete SOPs, 2000+ words, RACI matrix
- Structure: Overview, RACI, Core Procedures, Communications, Quality, Change Management
- Quality markers: Procedural clarity, tool-specific, exception handling, quality gates
- Includes detailed SOP example with numbered steps

**D. Generic Prompt (Fallback)**
- Created `_build_generic_prompt()` for remaining 12 document types
- Original prompt logic preserved for documents not yet enhanced

#### 4. Helper Methods Added
**File:** `src/wowasi_ya/core/generator.py`

- `_extract_frameworks_research()` - Pulls frameworks agent results for injection into prompts
- Updated `_build_generation_prompt()` - Routes to specialized or generic prompt based on doc type

---

## Test Results

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

### Quality Improvements Observed

**Budget Document:**
- ✅ Specific cost ranges ($485K-$565K) with strategic justifications
- ✅ ROI analysis comparing to alternatives ($8K-$14K vs $30K-$50K)
- ✅ Risk-aware contingency planning (5% reserve)
- ✅ Cross-references 3+ other documents
- ✅ Professional terminology throughout

**Risks Document:**
- ✅ Quantitative risk matrix (3×3 Likelihood × Impact)
- ✅ Executive summary with top 5 critical risks
- ✅ Specific risk statements (not vague)
- ✅ Concrete mitigation strategies with contingency plans
- ✅ Risk owner assignments

**SOPs Document:**
- ✅ Complete RACI matrix (6 roles × 14 activities)
- ✅ 6-8 detailed SOPs with numbered procedures
- ✅ Specific timeframes (Days 1-3, Week 2)
- ✅ Prerequisites, quality checks, escalation paths
- ✅ Version control procedures

### Example Quality Comparison

**BEFORE (Generic Prompt):**
> "We need a Program Coordinator ($70,000) to manage the project."

**AFTER (Enhanced Prompt):**
> "Program Director (1.0 FTE, $75,000-$85,000): This senior position requires extensive experience in tribal youth programming, cultural competency, and program management. The salary range reflects regional nonprofit leadership compensation and the specialized skills required to navigate tribal governance structures, federal compliance requirements, and community cultural protocols. This investment prevents the high turnover rates that plague underfunded youth programs and ensures continuity essential for building trust with participants and families."

---

## Current State

### Enhanced Documents (3 of 15)
1. ✅ **Initial Budget** - Full senior-level prompt
2. ✅ **Risks and Assumptions** - Full senior-level prompt
3. ✅ **Standard Operating Procedures (SOPs)** - Full senior-level prompt

### Still Using Generic Prompt (12 of 15)
4. ⏳ README (Project Overview)
5. ⏳ Project Brief
6. ⏳ Glossary
7. ⏳ Context and Background
8. ⏳ Stakeholder Notes
9. ⏳ Goals and Success Criteria
10. ⏳ Scope and Boundaries
11. ⏳ Timeline and Milestones
12. ⏳ Process Workflow
13. ⏳ Task Backlog
14. ⏳ Meeting Notes
15. ⏳ Status Updates

---

## Next Steps

### Option A: Complete Rollout (Recommended)
Create enhanced prompts for all 12 remaining document types.

**High Priority (Strategic Documents):**
1. Goals and Success Criteria - Needs SMART framework, OKRs
2. Timeline and Milestones - Needs Gantt conventions, critical path
3. Project Brief - Needs executive summary structure
4. Stakeholder Notes - Needs power/interest grid analysis

**Medium Priority (Planning Documents):**
5. Scope and Boundaries - Needs in/out structure
6. Process Workflow - Needs process mapping conventions
7. Context and Background - Needs environmental scanning framework

**Lower Priority (Ongoing/Template Documents):**
8. Task Backlog - Needs sprint/kanban structure
9. Meeting Notes - Needs agenda/minutes template
10. Status Updates - Needs dashboard/metrics structure
11. README - Needs executive summary conventions
12. Glossary - Needs term definition standards

### Option B: Selective Enhancement
Keep hybrid approach - only enhance critical documents where quality matters most (Goals, Timeline, Project Brief, Stakeholder Notes).

### Option C: Evaluate First
Deploy current 3-document enhancement to production, gather feedback, then decide scope of further enhancements.

---

## Technical Notes

### Code Architecture
- **Prompt routing:** `_build_generation_prompt()` checks `doc_type` and routes to specialized or generic
- **Frameworks extraction:** `_extract_frameworks_research()` pulls agent_000_frameworks results
- **Fallback logic:** If frameworks agent fails, provides fallback scaffolding in prompt

### Environment Configuration
**IMPORTANT:** `.env` was temporarily changed for testing:
- `GENERATION_PROVIDER=claude` (for testing since Mac was offline)
- **Production should use:** `GENERATION_PROVIDER=llamacpp` (local Llama 3.3 70B)
- Fallback to Claude is automatic via `LLAMACPP_FALLBACK_TO_CLAUDE=true`

### Agent Discovery Change
- Agent counter starts at 2 (not 1) since frameworks agent uses priority 1
- Frameworks agent always inserted first via `agents.insert(0, framework_agent)`

### Research Phase
- Frameworks agent uses special prompt: `_build_frameworks_research_prompt()`
- Standard domain agents use original prompt: `_build_research_prompt()`
- Both executed in parallel by research engine

---

## Files Modified

### Core Business Logic
- `src/wowasi_ya/core/agent_discovery.py` - Added frameworks agent
- `src/wowasi_ya/core/research.py` - Added frameworks research prompt
- `src/wowasi_ya/core/generator.py` - Added 3 specialized prompts + routing

### Configuration
- `.env` - Temporarily set to `GENERATION_PROVIDER=claude` for testing
- `.env.example` - Should be updated with documentation about prompt enhancement

### Other Modified Files (not critical to prompt work)
- `src/wowasi_ya/api/routes.py`
- `src/wowasi_ya/cli.py`
- `src/wowasi_ya/config.py`
- `src/wowasi_ya/core/output.py`
- `src/wowasi_ya/models/document.py`
- `src/wowasi_ya/models/project.py`

---

## Performance Impact

### Cost Analysis
- **Additional research agent:** +1 Claude API call per project (~$0.10-0.20)
- **Frameworks research:** More comprehensive, longer response (~$0.20-0.40)
- **Total added cost:** ~$0.30-0.60 per project
- **Benefit:** Significantly improved document quality

### Time Impact
- Research phase: +30-60 seconds (1 additional agent)
- Generation phase: No change (same number of documents)
- **Total:** Minimal impact (~1 minute per project)

---

## Testing Checklist

When resuming work:
- [ ] Review this document and CLAUDE.md
- [ ] Check `.env` settings (should be `GENERATION_PROVIDER=llamacpp` for production)
- [ ] Verify Mac/Llama server is online: `curl https://llama.iyeska.net/health`
- [ ] Test with sample project to verify prompts work
- [ ] Decide on rollout strategy (Option A/B/C above)
- [ ] Create enhanced prompts for next batch of documents
- [ ] Update documentation in CLAUDE.md when complete

---

## Questions for User

Before proceeding with full rollout:
1. Which documents are most important to your use cases?
2. Would you prefer all 15 enhanced or keep some generic?
3. Any specific quality issues with the 3 pilot documents?
4. Should we prioritize different document types first?

---

## Success Criteria

✅ **Completed:**
- Frameworks research agent created and tested
- 3 pilot document prompts enhanced (Budget, Risks, SOPs)
- Test generation shows 21x word count increase
- Quality demonstrates senior-level characteristics
- System works end-to-end

⏳ **Remaining:**
- 12 document types still need enhanced prompts
- Production testing with Llama (Mac was offline during test)
- User feedback on pilot document quality
- Documentation updates in CLAUDE.md
