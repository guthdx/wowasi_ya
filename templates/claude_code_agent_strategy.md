# Claude Code Agent Strategy

This supplement defines how Claude Code agents work together to generate comprehensive project starter kit files.

**Designed for:** Thorough research and document generation
**Compatible with:** Future automation/custom interface integration
**Key Feature:** Dynamic ad hoc agent generation based on project context

---

## Overview

Instead of generating documents from a brief description alone, this strategy uses specialized agents to:
1. **Analyze the project** to identify specialized domains requiring custom agents
2. **Generate ad hoc agents** tailored to the project's unique needs
3. Research context, regulations, similar projects, and stakeholders
4. Generate documents in parallel where possible
5. Ensure real-world grounding with current information

---

## Available Agents

### Core Agents (Always Available)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `web-research-specialist` | Research industry context, regulations, funding sources, similar projects, stakeholder landscape | **Phase 1** - Before any document drafting |
| `general-purpose` | Complex multi-step tasks, parallel document generation, cross-referencing | **Phase 0-3** - Executes ad hoc agents and complex tasks |
| `Explore` | Analyze existing codebases, technical architecture | **Phase 1** - Only for software/tech projects with existing code |

### Ad Hoc Agents (Dynamically Generated)

Ad hoc agents are created in **Phase 0** based on project analysis. They are executed via `general-purpose` with specialized prompts.

---

## Ad Hoc Agent Schema

Every dynamically generated agent follows this schema:

```yaml
agent_definition:
  id: "string (kebab-case, e.g., 'healthcare-compliance-researcher')"
  name: "string (human-readable name)"
  purpose: "string (what this agent accomplishes)"

  domain_triggers:
    keywords: ["list of keywords that triggered this agent"]
    domain_category: "string (e.g., 'healthcare', 'finance', 'agriculture')"

  research_focus:
    primary_questions:
      - "Key question 1 this agent must answer"
      - "Key question 2 this agent must answer"
    search_terms: ["specific search terms to use"]
    source_priorities:
      - "Preferred source type 1 (e.g., 'government sites')"
      - "Preferred source type 2 (e.g., 'academic research')"
    geographic_scope: "string (e.g., 'federal', 'state:AZ', 'tribal', 'international')"

  output_requirements:
    format: "structured | narrative | table | mixed"
    must_include:
      - "Required output element 1"
      - "Required output element 2"
    feed_to_documents:
      - "Document-Name.md (which doc this research feeds)"

  execution:
    estimated_complexity: "low | medium | high"
    can_parallelize: true | false
    depends_on: ["list of other agent IDs, or empty"]
```

### Example Ad Hoc Agent Definition

```yaml
agent_definition:
  id: "tribal-telehealth-compliance"
  name: "Tribal Telehealth Compliance Researcher"
  purpose: "Research healthcare compliance requirements specific to tribal telehealth services"

  domain_triggers:
    keywords: ["telehealth", "tribal", "healthcare", "clinic", "IHS"]
    domain_category: "healthcare"

  research_focus:
    primary_questions:
      - "What HIPAA requirements apply to tribal telehealth?"
      - "What IHS guidelines govern telehealth services?"
      - "What tribal sovereignty considerations affect healthcare data?"
      - "What funding sources exist for tribal telehealth?"
    search_terms:
      - "tribal telehealth HIPAA compliance"
      - "IHS telehealth guidelines 2024"
      - "tribal health data sovereignty"
      - "HRSA tribal telehealth grants"
    source_priorities:
      - "IHS official publications"
      - "HHS/CMS guidance documents"
      - "Tribal health organization reports"
    geographic_scope: "federal + tribal"

  output_requirements:
    format: "structured"
    must_include:
      - "Compliance checklist"
      - "Funding opportunities with deadlines"
      - "Tribal-specific considerations"
    feed_to_documents:
      - "Context-and-Background.md"
      - "Risks-and-Assumptions.md"
      - "Scope-and-Boundaries.md"

  execution:
    estimated_complexity: "high"
    can_parallelize: true
    depends_on: []
```

---

## Domain Analysis Engine

The following logic determines what ad hoc agents to generate:

### Step 1: Keyword Extraction
Parse the project description for domain indicators:

```yaml
domain_keyword_map:
  healthcare:
    triggers: ["health", "medical", "clinic", "patient", "HIPAA", "telehealth", "hospital", "care", "wellness", "IHS"]
    base_agents:
      - healthcare-compliance-researcher
      - patient-privacy-analyst

  finance:
    triggers: ["budget", "funding", "grant", "loan", "investment", "revenue", "cost", "financial", "treasury"]
    base_agents:
      - funding-source-researcher
      - financial-compliance-analyst

  technology:
    triggers: ["software", "app", "system", "platform", "database", "API", "cloud", "mobile", "web", "automation"]
    base_agents:
      - technology-landscape-analyst
      - security-requirements-researcher

  agriculture:
    triggers: ["farm", "food", "agriculture", "crop", "livestock", "USDA", "harvest", "garden", "soil"]
    base_agents:
      - agricultural-program-researcher
      - food-safety-compliance-analyst

  education:
    triggers: ["school", "training", "curriculum", "student", "teacher", "learning", "education", "workshop"]
    base_agents:
      - education-program-researcher
      - accreditation-requirements-analyst

  infrastructure:
    triggers: ["building", "construction", "road", "water", "utilities", "facility", "housing", "broadband"]
    base_agents:
      - infrastructure-funding-researcher
      - permitting-requirements-analyst

  governance:
    triggers: ["policy", "council", "government", "ordinance", "regulation", "compliance", "sovereignty"]
    base_agents:
      - regulatory-landscape-researcher
      - policy-framework-analyst

  community:
    triggers: ["community", "tribal", "elder", "youth", "family", "cultural", "tradition", "language"]
    base_agents:
      - community-program-researcher
      - cultural-considerations-analyst

  environment:
    triggers: ["environment", "climate", "water", "air", "waste", "conservation", "sustainability", "EPA"]
    base_agents:
      - environmental-compliance-researcher
      - sustainability-analyst
```

### Step 2: Domain Intersection Detection
When multiple domains intersect, generate specialized hybrid agents:

```yaml
intersection_rules:
  healthcare + community:
    generates: "community-health-specialist"
    focus: "Cultural health practices, community health workers, tribal health programs"

  technology + healthcare:
    generates: "health-tech-compliance-analyst"
    focus: "HIPAA tech requirements, health data systems, interoperability standards"

  finance + community:
    generates: "tribal-funding-specialist"
    focus: "Tribal-specific grants, federal tribal programs, sovereignty in funding"

  infrastructure + community:
    generates: "tribal-infrastructure-analyst"
    focus: "BIA programs, tribal utility authorities, housing programs"

  agriculture + community:
    generates: "food-sovereignty-researcher"
    focus: "Tribal food programs, traditional foods, FDPIR, food hubs"

  technology + governance:
    generates: "govtech-analyst"
    focus: "Civic tech, government systems, public sector compliance"

  education + community:
    generates: "tribal-education-specialist"
    focus: "BIE schools, tribal colleges, language preservation, cultural curriculum"
```

### Step 3: Stakeholder-Based Agent Generation
Identify stakeholders mentioned and generate relevant agents:

```yaml
stakeholder_triggers:
  "elder" | "elders":
    generates: "elder-services-researcher"
    focus: "Elder care programs, accessibility, cultural protocols, IHS elder services"

  "youth" | "children" | "kids":
    generates: "youth-programs-researcher"
    focus: "Youth development, education, child welfare, tribal youth programs"

  "tribal council" | "council" | "leadership":
    generates: "tribal-governance-researcher"
    focus: "Tribal governance structures, resolution templates, sovereignty frameworks"

  "researcher" | "research team" | "PI":
    generates: "research-compliance-analyst"
    focus: "IRB requirements, tribal research protocols, data sovereignty in research, PHI/PII handling"

  "community member" | "tribal member" | "member":
    generates: "community-engagement-researcher"
    focus: "Outreach strategies, cultural communication, trust-building, accessibility"

  "farmer" | "rancher" | "producer":
    generates: "agricultural-producer-analyst"
    focus: "USDA programs, tribal agriculture initiatives, producer support, land use"

  "nonprofit" | "organization" | "501c3":
    generates: "nonprofit-operations-researcher"
    focus: "Grant compliance, nonprofit governance, reporting requirements, fiscal sponsorship"

  "small business" | "entrepreneur" | "enterprise":
    generates: "tribal-enterprise-analyst"
    focus: "Tribal business structures, 8(a) certification, economic development, sovereignty in commerce"
```

---

## Workflow Phases

### Phase 0: Agent Discovery & Generation

**Purpose:** Analyze the project description and dynamically generate specialized agents tailored to the specific project context.

**Trigger:** Always runs first, before any research or document creation.

#### Step 0.1: Parse Project Description
Extract key elements from the user's project description:

```yaml
extraction_targets:
  - Project type indicators (software, infrastructure, program, grant, etc.)
  - Domain keywords (health, agriculture, finance, etc.)
  - Stakeholder mentions (elders, council, researchers, etc.)
  - Geographic/jurisdictional scope (tribal, federal, state, local)
  - Technical requirements (systems, platforms, integrations)
  - Compliance mentions (HIPAA, IRB, USDA, sovereignty)
  - Funding/resource references (grants, budgets, in-kind)
  - Timeline indicators (urgent, phased, long-term)
  - Infrastructure context (on-prem, hybrid, air-gapped, cloud)
```

#### Step 0.2: Domain Matching
Run extracted keywords against `domain_keyword_map` to identify relevant domains.

Example analysis:
```
Input: "telehealth system for tribal elders with diabetes management"

Detected domains:
  - healthcare (telehealth, diabetes, management)
  - technology (system)
  - community (tribal, elders)

Domain count: 3 → triggers intersection analysis
```

#### Step 0.3: Intersection Analysis
Check for domain intersections using `intersection_rules` to generate hybrid agents.

```
Intersections found:
  - healthcare + community → generates "community-health-specialist"
  - technology + healthcare → generates "health-tech-compliance-analyst"
```

#### Step 0.4: Stakeholder Agent Generation
Match stakeholder mentions against `stakeholder_triggers`.

```
Stakeholders detected: "elders"
  → generates "elder-services-researcher"
```

#### Step 0.5: Context-Specific Agent Customization
For each triggered agent, customize based on project specifics:

```yaml
customization_rules:
  # Adjust for sovereignty context
  if "tribal" in project:
    add_to_all_agents:
      - "Tribal data sovereignty implications"
      - "Federal trust responsibility considerations"
      - "Tribal council approval requirements"

  # Adjust for regulated data
  if "PHI" or "health" or "patient" in project:
    add_to_all_agents:
      - "HIPAA compliance requirements"
      - "Data localization requirements"
      - "Minimum necessary standard"

  # Adjust for research context
  if "research" or "study" or "IRB" in project:
    add_to_all_agents:
      - "Tribal IRB protocols"
      - "Data ownership and repatriation"
      - "Community benefit requirements"

  # Adjust for infrastructure constraints
  if "air-gapped" or "on-prem" or "enclave" in project:
    add_to_all_agents:
      - "Offline-capable solutions"
      - "Local data storage requirements"
      - "Network isolation considerations"
```

#### Step 0.6: Generate Full Agent Definitions
For each triggered agent, create complete definition using the Ad Hoc Agent Schema:

```yaml
# Example: Generated agent for telehealth + elders project
agent_definition:
  id: "tribal-elder-telehealth-specialist"
  name: "Tribal Elder Telehealth Specialist"
  purpose: "Research telehealth solutions appropriate for tribal elder populations"

  domain_triggers:
    keywords: ["telehealth", "elder", "tribal", "diabetes"]
    domain_category: "healthcare + community"

  research_focus:
    primary_questions:
      - "What telehealth platforms work in rural/low-bandwidth environments?"
      - "What are IHS telehealth reimbursement policies?"
      - "What accessibility considerations exist for elder users?"
      - "What tribal telehealth programs have succeeded and why?"
      - "What diabetes remote monitoring tools are HIPAA-compliant?"
    search_terms:
      - "tribal telehealth elder care"
      - "IHS diabetes management telehealth"
      - "rural telehealth low bandwidth"
      - "tribal health data sovereignty telehealth"
    source_priorities:
      - "IHS official guidance"
      - "CMS tribal telehealth policies"
      - "National Indian Health Board resources"
      - "Tribal health department case studies"
    geographic_scope: "federal + tribal"

  output_requirements:
    format: "structured"
    must_include:
      - "Platform comparison (with sovereignty analysis)"
      - "Compliance checklist"
      - "Elder accessibility requirements"
      - "Funding opportunities"
    feed_to_documents:
      - "Context-and-Background.md"
      - "Scope-and-Boundaries.md"
      - "Risks-and-Assumptions.md"
      - "Initial-Budget.md"

  execution:
    estimated_complexity: "high"
    can_parallelize: true
    depends_on: []
```

#### Step 0.7: Build Execution Plan
Organize generated agents into parallel batches where possible:

```yaml
execution_plan:
  parallel_batch_1:  # No dependencies - run simultaneously
    - elder-services-researcher
    - health-tech-compliance-analyst
  parallel_batch_2:  # Depends on batch 1 context
    - tribal-elder-telehealth-specialist
    - community-health-specialist
  sequential:  # Must run in order
    - integration-analyst (synthesizes all research)
```

#### Phase 0 Output
Complete output from agent discovery:

```yaml
phase_0_output:
  project_analysis:
    detected_domains: ["healthcare", "technology", "community"]
    detected_intersections: ["healthcare+community", "technology+healthcare"]
    detected_stakeholders: ["elders"]
    project_type: "software_tech + community_tribal"
    geographic_scope: "tribal + federal"
    compliance_flags: ["HIPAA", "tribal_sovereignty", "elder_accessibility"]
    infrastructure_context: "hybrid (on-prem data, cloud-optional services)"

  generated_agents:
    - agent_definition: { id: "elder-services-researcher", ... }
    - agent_definition: { id: "health-tech-compliance-analyst", ... }
    - agent_definition: { id: "tribal-elder-telehealth-specialist", ... }
    - agent_definition: { id: "community-health-specialist", ... }

  execution_plan:
    total_agents: 4
    parallel_batches: 2
    estimated_research_time: "thorough"

  context_flags:
    requires_sovereignty_analysis: true
    requires_hipaa_review: true
    requires_accessibility_review: true
    air_gapped_considerations: false
```

---

### Phase 1: Research & Discovery

Before drafting any documents, execute all agents (core + ad hoc) to gather real-world context.

#### Step 1.1: Context Research
**Agent:** `web-research-specialist`
**Trigger:** Always run first
**Research targets based on project type:**

```yaml
software_tech:
  - Technology landscape and alternatives
  - Security considerations and compliance (SOC2, HIPAA, etc.)
  - Similar open source or commercial solutions
  - Integration patterns and APIs
  - Licensing implications

business_ops:
  - Industry best practices
  - Regulatory requirements
  - Similar programs/initiatives
  - Vendor landscape
  - Typical cost structures

community_tribal:
  - Relevant federal/state regulations
  - Grant and funding opportunities (USDA, HUD, IHS, foundations)
  - Similar community initiatives and lessons learned
  - Cultural/sovereignty considerations
  - Required compliance frameworks

general:
  - Market context
  - Stakeholder landscape
  - Risk factors in similar projects
  - Timeline benchmarks from comparable efforts
```

#### Step 1.2: Technical Discovery (if applicable)
**Agent:** `Explore`
**Trigger:** Only if project involves existing codebase
**Research targets:**
- Current architecture and patterns
- Dependencies and integrations
- Technical debt or constraints
- Relevant documentation in code

#### Step 1.3: Compile Research Summary
After agent research completes, compile findings into a structured research brief:
```markdown
## Research Brief

### Industry/Domain Context
[findings]

### Regulatory/Compliance Factors
[findings]

### Similar Projects/Precedents
[findings]

### Stakeholder Landscape
[findings]

### Risk Factors Identified
[findings]

### Funding/Resource Opportunities
[findings]
```

---

### Phase 2: Document Generation

With research complete, generate the 15 project files.

#### Parallel Generation Strategy

**Batch 1 - Foundation Documents** (can run in parallel)
- README.md
- Project-Brief.md
- Glossary.md
- Context-and-Background.md

**Batch 2 - Stakeholder & Goals** (depends on Batch 1)
- Stakeholder-Notes.md
- Goals-and-Success-Criteria.md
- Scope-and-Boundaries.md

**Batch 3 - Planning Documents** (depends on Batch 2)
- Initial-Budget.md
- Timeline-and-Milestones.md
- Risks-and-Assumptions.md

**Batch 4 - Execution Documents** (depends on Batch 3)
- Process-Workflow.md
- SOPs.md
- Task-Backlog.md

**Batch 5 - Templates** (no dependencies, can run anytime)
- Meeting-Notes.md
- Status-Updates.md

#### Agent Assignment for Complex Documents

Use `general-purpose` agent for documents requiring:
- Cross-referencing multiple research findings
- Complex budget calculations
- Detailed workflow design
- Comprehensive risk analysis

---

### Phase 3: Quality & Integration

#### Cross-Reference Check
Verify consistency across documents:
- [ ] Goals align with scope
- [ ] Budget categories match planned activities
- [ ] Timeline milestones match goals
- [ ] Risks address scope dependencies
- [ ] Task backlog covers all process steps
- [ ] Glossary includes all terms used in documents

#### Output Format
All documents output with separators for easy parsing:
```
--- FILE: filename.md ---
[content]

--- FILE: next-filename.md ---
[content]
```

---

## Automation Interface Schema

For future custom interface integration, here's the expected input/output schema:

### Input Schema
```json
{
  "project_name": "string",
  "project_type": "software_tech | business_ops | community_tribal | mixed",
  "description": "string (detailed project description)",
  "known_stakeholders": ["array of stakeholder names/roles"],
  "known_constraints": ["array of known limitations"],
  "target_timeline": "string (e.g., '6 months', '1 year')",
  "budget_range": "string (e.g., '$10k-$50k', 'unknown')",
  "existing_codebase": "string (path) | null",
  "existing_infrastructure": {
    "systems": ["pfSense", "Proxmox", "AD DS", etc.],
    "network": ["VLANs", "VPNs", "air-gapped segments"],
    "constraints": ["on-prem only", "hybrid allowed", "cloud OK"]
  },
  "compliance_context": ["HIPAA", "tribal_sovereignty", "IRB", etc.],
  "research_depth": "light | moderate | thorough"
}
```

### Output Schema
```json
{
  "phase_0_analysis": {
    "detected_domains": ["list of domains identified"],
    "detected_intersections": ["list of domain intersections"],
    "detected_stakeholders": ["list of stakeholders"],
    "compliance_flags": ["list of compliance requirements"],
    "infrastructure_context": "string (summary)"
  },
  "generated_agents": [
    {
      "id": "agent-id",
      "name": "Human Readable Name",
      "purpose": "What this agent researches",
      "primary_questions": ["list of questions"],
      "feed_to_documents": ["list of documents this informs"]
    }
  ],
  "research_brief": "string (markdown - compiled from all agent outputs)",
  "files": [
    {
      "filename": "README.md",
      "path": "00-Overview/README.md",
      "content": "string (markdown)"
    }
  ],
  "metadata": {
    "core_agents_used": ["web-research-specialist", "Explore", etc.],
    "ad_hoc_agents_generated": ["list of dynamically created agents"],
    "research_sources": ["list of URLs/sources consulted"],
    "generation_timestamp": "ISO datetime",
    "warnings": ["any issues, gaps, or recommendations identified"],
    "sovereignty_notes": ["tribal data sovereignty considerations"],
    "compliance_checklist": ["compliance items to verify"]
  }
}
```

---

## Invocation Examples

### Example 1: Health Research Infrastructure
```
Input: "Set up a secure data enclave for tribal health research with diabetes outcomes data"

Phase 0 Agent Discovery:
  detected_domains: [healthcare, technology, community, governance]
  detected_intersections: [healthcare+community, technology+healthcare]
  compliance_flags: [HIPAA, tribal_sovereignty, IRB, PHI]
  infrastructure_context: air-gapped/on-prem

  generated_agents:
    - research-compliance-analyst (IRB, tribal research protocols)
    - health-tech-compliance-analyst (HIPAA tech requirements)
    - tribal-data-sovereignty-specialist (data ownership, repatriation)
    - secure-enclave-architect (air-gapped design patterns)

Phase 1 Research:
  - Execute all generated agents in parallel
  - web-research-specialist: tribal health research enclaves, HIPAA-compliant research platforms
  - Explore: existing infrastructure (Proxmox, AD DS, network segmentation)

Phase 2 Generation:
  - Batch 1-5 with emphasis on:
    - Scope-and-Boundaries.md (data sovereignty, what stays in enclave)
    - Risks-and-Assumptions.md (compliance, breach scenarios)
    - SOPs.md (data access, researcher onboarding, audit trails)
```

### Example 2: Tribal Agriculture Program
```
Input: "Establish a tribal food hub with cold storage, connecting local producers to school nutrition programs"

Phase 0 Agent Discovery:
  detected_domains: [agriculture, community, infrastructure, finance]
  detected_intersections: [agriculture+community, finance+community]
  compliance_flags: [USDA, food_safety, tribal_sovereignty]
  stakeholders: [farmers, tribal council, schools]

  generated_agents:
    - food-sovereignty-researcher (tribal food programs, FDPIR)
    - agricultural-program-researcher (USDA grants, producer support)
    - tribal-funding-specialist (federal tribal programs)
    - food-safety-compliance-analyst (cold chain, licensing)

Phase 1 Research:
  - Execute generated agents
  - web-research-specialist: tribal food hubs, Farm to School tribal programs, USDA Community Facilities grants

Phase 2 Generation:
  - Batch 1-5 with emphasis on:
    - Initial-Budget.md (construction, equipment, operating costs)
    - Timeline-and-Milestones.md (grant cycles, construction phases)
    - Stakeholder-Notes.md (producers, schools, council buy-in)
    - Process-Workflow.md (producer intake, storage, distribution)
```

### Example 3: Nonprofit Financial System
```
Input: "Implement fund accounting system for tribal nonprofit with multiple grant sources"

Phase 0 Agent Discovery:
  detected_domains: [finance, technology, governance, community]
  detected_intersections: [finance+community, technology+governance]
  compliance_flags: [grant_compliance, nonprofit_accounting, tribal_sovereignty]
  stakeholders: [nonprofit board, tribal council, funders]

  generated_agents:
    - nonprofit-operations-researcher (fund accounting requirements)
    - tribal-funding-specialist (federal grant compliance)
    - financial-compliance-analyst (audit requirements, cost allocation)
    - technology-landscape-analyst (accounting platforms, on-prem vs cloud)

Phase 1 Research:
  - Execute generated agents
  - web-research-specialist: tribal nonprofit accounting, indirect cost rate negotiation, fund accounting software

Phase 2 Generation:
  - Batch 1-5 with emphasis on:
    - Process-Workflow.md (grant setup, expense tracking, reporting)
    - SOPs.md (cost allocation, time tracking, audit prep)
    - Risks-and-Assumptions.md (audit findings, grant disallowances)
    - Scope-and-Boundaries.md (which grants, which fiscal years)
```

### Example 4: Infrastructure Modernization
```
Input: "Migrate from legacy Windows file shares to modern document management while maintaining air-gapped security"

Phase 0 Agent Discovery:
  detected_domains: [technology, governance, infrastructure]
  detected_intersections: [technology+governance]
  compliance_flags: [data_sovereignty, air_gapped, PHI_possible]
  infrastructure_context: on-prem, AD DS, existing VLANs

  generated_agents:
    - technology-landscape-analyst (document management options)
    - security-requirements-researcher (air-gapped DMS solutions)
    - tribal-data-sovereignty-specialist (data location, vendor access)

Phase 1 Research:
  - Execute generated agents
  - web-research-specialist: on-prem document management, SharePoint vs alternatives, air-gapped deployments
  - Explore: existing AD DS structure, file share permissions, VLAN architecture

Phase 2 Generation:
  - Batch 1-5 with emphasis on:
    - Process-Workflow.md (migration phases, user training)
    - Risks-and-Assumptions.md (data loss, permission mapping, downtime)
    - Timeline-and-Milestones.md (pilot, department rollouts)
    - SOPs.md (file naming, folder structure, access requests)
```

---

## Usage in Claude Code

To use this strategy manually in Claude Code:

1. Provide your project description
2. Request: "Use the agent strategy to research and generate project starter kit files"
3. Claude Code will:
   - Invoke `web-research-specialist` for thorough context gathering
   - Compile research brief
   - Generate documents in batches
   - Output all files with separators

---

## Version History

- **v1.0** - Initial strategy definition
- **v1.1** - Added Phase 0: Agent Discovery & Generation
  - Dynamic ad hoc agent creation based on project analysis
  - Domain keyword mapping and intersection detection
  - Stakeholder-based agent triggers
  - Context-specific customization rules (sovereignty, HIPAA, air-gapped, research)
  - Updated examples for tribal health research, agriculture, nonprofit finance, infrastructure
  - Enhanced automation schemas with Phase 0 output
  - Aligned with user context: tribal, rural, sovereignty-focused environments

Designed for Claude Code with Task tool agent support.
