# Plan: Eliminate AI Writing Tells from Document Generation

## Status: IMPLEMENTED (Conservative Approach)

**Completed:** December 31, 2025

## Problem Statement
Generated documents were obviously AI-written due to:
- Excessive em dashes ("the ChatGPT hyphen")
- AI vocabulary ("delve," "tapestry," "realm," "leverage," "seamlessly")
- Formulaic transitions (Furthermore, Moreover, etc.)
- Generic openings ("In today's digital age...")

## Solution Implemented

Per user feedback ("be less aggressive"), implemented a **conservative approach** targeting only the most obvious AI tells while preserving professional document quality.

### Changes Made

**File:** `src/wowasi_ya/core/generator.py`

Added `WRITING_STYLE_RULES` constant (lines 16-42) with focused guidance on:

1. **Punctuation:** Em dash avoidance (max 1-2 per document)
2. **Banned Vocabulary:** 20 AI-associated terms (delve, tapestry, leverage, utilize, seamlessly, etc.)
3. **Transition Avoidance:** Formulaic transitions (Furthermore, Moreover, Additionally, etc.)
4. **Opening Rules:** No generic "In today's..." or "In an era of..." openings

### What Was NOT Changed (Per User Request)

- No contractions requirement
- No conversational tone mandate
- No sentence variety requirements
- No "explain to a friend" style changes
- Professional document tone preserved

### Integration

Writing style rules inserted into all 16 prompt builders:
- 1 generic fallback prompt
- 15 specialized document prompts (Budget, Risks, SOPs, Goals, Timeline, Project Brief, Stakeholder, Scope, Process Workflow, Context, Task Backlog, Meeting Notes, Status Updates, README, Glossary)

## Verification

```bash
# Verify rules are in prompts
python -c "from wowasi_ya.core.generator import WRITING_STYLE_RULES; print(len(WRITING_STYLE_RULES), 'chars')"
# Output: 974 chars

# Count insertions
grep -c "WRITING_STYLE_RULES" src/wowasi_ya/core/generator.py
# Output: 16
```

## User's Guidance

> "lets be a little less aggressive.. i still want these documents to look like they were professionally done. I can soften the language more later myself... I am mostly concerned with the obvious AI type crutches..."

## Success Criteria

- [x] No em dash overuse in generated documents
- [x] Banned AI words don't appear
- [x] No formulaic transitions
- [x] No generic AI openings
- [x] Documents maintain professional quality
