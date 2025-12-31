# WOWASI_YA_LOCAL_MODEL_EVALUATION_EXAMPLES.md

## Purpose

This document captures representative prompts used to test a local large language model (LLM) in the wowasi_ya project, summarizes the responses produced by the model, and documents the evaluation process used to assess model suitability for structured, multi-document project generation.

This file is intended to:
- Preserve testing context
- Prevent drift or confusion across development agents
- Provide a repeatable evaluation reference

---

## 1. Test Scenario Overview

**Model Tested:** Llama 3.3 70B (local, via Ollama)  
**Role Under Test:** Model B (Senior Writer)  
**Primary Capability Being Evaluated:**
- Multi-document consistency
- Instruction adherence
- Hallucination avoidance
- Professional tone and structure
- Constraint discipline

---

## 2. Example Prompt 1 — Structured Planning Document

### Prompt Used

```
Write a project scope and boundaries document for a Tribal health department
launching a mobile maternal health outreach program.

Constraints:
- Limited funding
- Small staff (nurses + community health workers)
- 9-month launch timeline

Include:
- In-scope items
- Out-of-scope items
- Assumptions
- Constraints

Use clear markdown headings.
Do not invent technologies, grants, or partners.
```

### Model Response (Excerpt)

```
## IN SCOPE
- Mobile outreach visits by nurses and community health workers
- Prenatal checkups and basic health education
- Referral coordination with the main clinic

## OUT OF SCOPE
- Construction of new healthcare facilities
- Advanced obstetric procedures
- Telehealth platform development

## ASSUMPTIONS
- Community leaders will support outreach efforts
- The main clinic can accept referrals

## CONSTRAINTS
- Limited funding
- Staffing capacity
- Geographic dispersion of communities
```

### Evaluation Notes

- Fully adhered to constraints
- No hallucinated technologies or funding sources
- Logical, realistic scope definition
- Tone appropriate for public-sector planning

**Result:** Pass

---

## 3. Example Prompt 2 — Risk & Mitigation Consistency Test

### Prompt Used

```
Continue a multi-document project planning exercise.

Using the same mobile maternal health outreach scenario, write a Risk & Mitigation
Plan that remains fully consistent with prior documents.

Rules:
- Do not introduce new infrastructure
- Do not contradict earlier scope assumptions
- Focus on realistic operational risks
```

### Model Response (Excerpt)

```
## TOP RISKS
1. Staffing shortages affecting visit schedules
2. Limited community engagement reducing participation
3. Referral coordination delays

## MITIGATION STRATEGIES
- Flexible scheduling and workload management
- Early engagement with community leaders
- Clear referral communication processes
```

### Evaluation Notes

- Demonstrated cross-document awareness
- Risks derived logically from earlier constraints
- Mitigations feasible under low-resource conditions

**Result:** Pass

---

## 4. Example Prompt 3 — Instruction Discipline Stress Test

### Prompt Used

```
Write a high-level roadmap for the project.

Rules:
- No specific technologies
- No dollar amounts
- Use phases only
- Keep it under 12 months
```

### Model Response (Excerpt)

```
## Phase 1 (Months 1–3)
Program design, staffing alignment, and community coordination

## Phase 2 (Months 4–6)
Pilot outreach visits and instructor preparation

## Phase 3 (Months 7–9)
Full pilot operation, monitoring, and refinement
```

### Evaluation Notes

- Exact compliance with time constraint
- No numerical costs introduced
- Clear sequencing without over-specification

**Result:** Pass

---

## 5. Evaluation Process Used

The following evaluation framework is applied to each test output.

### 5.1 Instruction Following
- Were all explicit rules followed?
- Were required sections present?
- Was formatting correct?

### 5.2 Constraint Discipline
- Did the model respect funding, staffing, and timeline limits?
- Did it avoid overreach or scope creep?

### 5.3 Hallucination Avoidance
- No invented technologies
- No named vendors, grants, or laws
- No fabricated statistics

### 5.4 Cross-Document Consistency
- Does the output align with earlier documents?
- Are assumptions stable across documents?

### 5.5 Tone and Professional Quality
- Suitable for Tribal, nonprofit, or public-sector audiences
- Clear, neutral, and non-salesy language

Each category is scored informally on a 1–5 scale.
Any failure in hallucination avoidance or constraint discipline results in rejection.

---

## 6. Summary Assessment

Based on repeated testing:

- Llama 3.3 70B demonstrates strong suitability as **Model B**
- Handles structured prompts reliably
- Maintains consistency across documents
- Avoids hallucination under pressure
- Produces professional, usable planning language

This model is approved for use in the wowasi_ya document-generation pipeline.

---

## End of File
