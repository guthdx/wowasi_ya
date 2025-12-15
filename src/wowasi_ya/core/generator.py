"""Document Generator - Phase 2: Generate 15 project documents.

Provider: Configurable (Llama CPP via Cloudflare or Claude API)
See: core/llm_client.py for provider abstraction
"""

import logging
from datetime import datetime
from typing import Any

from wowasi_ya.config import Settings, get_settings
from wowasi_ya.core.llm_client import BaseLLMClient, get_generation_client

logger = logging.getLogger(__name__)
from wowasi_ya.models.agent import AgentResult
from wowasi_ya.models.document import (
    DOCUMENT_BATCHES,
    Document,
    DocumentBatch,
    DocumentType,
    GeneratedProject,
)
from wowasi_ya.models.project import ProjectInput


# Document templates with folder mappings
DOCUMENT_CONFIG: dict[DocumentType, dict[str, str]] = {
    DocumentType.README: {
        "folder": "00-Overview",
        "filename": "README.md",
        "title": "Project Overview",
    },
    DocumentType.PROJECT_BRIEF: {
        "folder": "00-Overview",
        "filename": "Project-Brief.md",
        "title": "Project Brief",
    },
    DocumentType.GLOSSARY: {
        "folder": "00-Overview",
        "filename": "Glossary.md",
        "title": "Glossary",
    },
    DocumentType.CONTEXT_BACKGROUND: {
        "folder": "10-Discovery",
        "filename": "Context-and-Background.md",
        "title": "Context and Background",
    },
    DocumentType.STAKEHOLDER_NOTES: {
        "folder": "10-Discovery",
        "filename": "Stakeholder-Notes.md",
        "title": "Stakeholder Notes",
    },
    DocumentType.GOALS_SUCCESS: {
        "folder": "20-Planning",
        "filename": "Goals-and-Success-Criteria.md",
        "title": "Goals and Success Criteria",
    },
    DocumentType.SCOPE_BOUNDARIES: {
        "folder": "20-Planning",
        "filename": "Scope-and-Boundaries.md",
        "title": "Scope and Boundaries",
    },
    DocumentType.INITIAL_BUDGET: {
        "folder": "20-Planning",
        "filename": "Initial-Budget.md",
        "title": "Initial Budget",
    },
    DocumentType.TIMELINE_MILESTONES: {
        "folder": "20-Planning",
        "filename": "Timeline-and-Milestones.md",
        "title": "Timeline and Milestones",
    },
    DocumentType.RISKS_ASSUMPTIONS: {
        "folder": "20-Planning",
        "filename": "Risks-and-Assumptions.md",
        "title": "Risks and Assumptions",
    },
    DocumentType.PROCESS_WORKFLOW: {
        "folder": "30-Execution",
        "filename": "Process-Workflow.md",
        "title": "Process Workflow",
    },
    DocumentType.SOPS: {
        "folder": "30-Execution",
        "filename": "SOPs.md",
        "title": "Standard Operating Procedures",
    },
    DocumentType.TASK_BACKLOG: {
        "folder": "30-Execution",
        "filename": "Task-Backlog.md",
        "title": "Task Backlog",
    },
    DocumentType.MEETING_NOTES: {
        "folder": "40-Comms",
        "filename": "Meeting-Notes.md",
        "title": "Meeting Notes",
    },
    DocumentType.STATUS_UPDATES: {
        "folder": "40-Comms",
        "filename": "Status-Updates.md",
        "title": "Status Updates",
    },
}


class DocumentGenerator:
    """Generator for creating project documentation.

    This is Phase 2 - requires LLM calls.
    Documents are generated in batches per Process-Workflow.md.

    Provider is configurable via GENERATION_PROVIDER env var:
    - "llamacpp": Llama 3.3 70B via Cloudflare Tunnel (cost-effective)
    - "claude": Claude API (fallback or explicit choice)
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the document generator.

        Args:
            settings: Application settings.
        """
        self.settings = settings or get_settings()
        self._client: BaseLLMClient | None = None

    async def _get_client(self) -> BaseLLMClient:
        """Get LLM client with intelligent fallback.

        Returns:
            LLM client instance (Llama or Claude).
        """
        if self._client is None:
            self._client = await get_generation_client(self.settings)
        return self._client

    async def generate_document(
        self,
        doc_type: DocumentType,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> Document:
        """Generate a single document.

        Args:
            doc_type: Type of document to generate.
            project: Project input.
            research_results: Results from research phase.
            previous_docs: Previously generated documents for context.

        Returns:
            Generated document.
        """
        client = await self._get_client()
        config = DOCUMENT_CONFIG[doc_type]

        prompt = self._build_generation_prompt(
            doc_type, project, research_results, previous_docs
        )

        try:
            # Use abstracted LLM client (works with both Claude and Llama)
            content = await client.generate(
                prompt=prompt,
                max_tokens=self.settings.max_generation_tokens,
                temperature=0.7,
            )

            return Document(
                type=doc_type,
                title=config["title"],
                content=content,
                folder=config["folder"],
                filename=config["filename"],
                generated_at=datetime.utcnow(),
                word_count=len(content.split()),
            )

        except Exception as e:
            logger.error(f"Error generating {doc_type}: {e}")
            # Return error document
            return Document(
                type=doc_type,
                title=config["title"],
                content=f"# {config['title']}\n\n*Error generating document: {e!s}*",
                folder=config["folder"],
                filename=config["filename"],
                word_count=0,
            )

    def _build_generation_prompt(
        self,
        doc_type: DocumentType,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build the generation prompt for a document.

        Enhanced for Llama 3.3 70B with:
        - Document-type-specific expert prompts
        - Professional frameworks and templates from research
        - Explicit constraints and rules
        - Hallucination prevention guards
        - Cross-document consistency enforcement
        """
        # Use specialized prompts for pilot documents
        if doc_type == DocumentType.INITIAL_BUDGET:
            return self._build_budget_prompt(project, research_results, previous_docs)
        elif doc_type == DocumentType.RISKS_ASSUMPTIONS:
            return self._build_risks_prompt(project, research_results, previous_docs)
        elif doc_type == DocumentType.SOPS:
            return self._build_sops_prompt(project, research_results, previous_docs)

        # Fallback to generic prompt for other document types
        return self._build_generic_prompt(doc_type, project, research_results, previous_docs)

    def _build_generic_prompt(
        self,
        doc_type: DocumentType,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build generic generation prompt for non-specialized document types.

        This is the original prompt logic for documents that haven't been
        enhanced with specialized prompts yet.
        """
        config = DOCUMENT_CONFIG[doc_type]

        # Compile research findings
        research_summary = self._compile_research_summary(research_results)

        # Get relevant previous documents
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are writing a professional project planning document for a real organization.

## DOCUMENT TO WRITE
{config['title']}

## PROJECT CONTEXT
**Project Name:** {project.name}
**Project Description:** {project.description}
{f"**Additional Context:** {project.additional_context}" if project.additional_context else ""}

## RESEARCH FINDINGS
{research_summary}

## PREVIOUS DOCUMENTS (for consistency)
{prev_context}

## STRICT RULES (you must follow all of these)

1. **Format:** Write in Markdown format only
2. **Start with:** An H1 heading (# {config['title']})
3. **Tone:** Professional, clear, neutral language suitable for nonprofit, tribal, or public-sector organizations
4. **Structure:** Include clear sections with H2 headings (##) and subsections with H3 headings (###) where appropriate
5. **Consistency:** Align with information from previous documents - do not contradict earlier assumptions, scope, or constraints
6. **Research Integration:** Reference relevant findings from the research section where applicable

## CONSTRAINTS (do not violate these)

1. **DO NOT invent:** Specific technologies, vendor names, product names, or software platforms unless mentioned in research findings
2. **DO NOT fabricate:** Statistics, dollar amounts, grant names, or funding sources unless provided in project context
3. **DO NOT add:** New stakeholders, team members, or organizational partners not mentioned in project description or previous documents
4. **DO NOT include:** Marketing language, sales pitches, or promotional content
5. **DO NOT contradict:** Information from previous documents - maintain consistency across all documentation

## REQUIRED SECTIONS

Include the following in your document:
- Introduction or overview paragraph
- Multiple main sections with descriptive H2 headings
- Subsections with H3 headings where detail is needed
- Concluding summary or next steps (where appropriate for document type)

## OUTPUT FORMAT

Provide ONLY the Markdown document content.
- Start with: # {config['title']}
- Use proper Markdown formatting
- Keep language professional and factual
- Ensure all information is grounded in the project context and research findings provided

Write the complete document now.
"""

    def _build_budget_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Initial Budget document.

        Leverages frameworks research to generate senior-level budget narrative.
        """
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Program Director with 15+ years of experience** managing multi-million dollar budgets in nonprofit, tribal, and public sector organizations.

You are known for budget narratives that:
- Connect every line item to strategic objectives
- Anticipate funder questions and address them proactively
- Use industry-standard categories and formatting
- Include clear justifications grounded in research and organizational capacity

## DOCUMENT TO WRITE
Initial Budget

## PROJECT CONTEXT
**Project Name:** {project.name}
**Project Description:** {project.description}
{f"**Additional Context:** {project.additional_context}" if project.additional_context else ""}

## PREVIOUS DOCUMENTS (for consistency)
{prev_context}

## RESEARCH FINDINGS
{research_summary}

## PROFESSIONAL FRAMEWORKS & TEMPLATES
{frameworks}

Use the budget categories, narrative structures, and professional examples from the frameworks above.

## YOUR TASK

Write a comprehensive Initial Budget document that demonstrates senior-level financial planning.

### REQUIRED STRUCTURE

Use these standard budget sections:

1. **Budget Overview**
   - Total project cost (range or estimate based on project scope)
   - Funding strategy (if applicable from context)
   - Budget period and fiscal year considerations
   - Key assumptions underlying the budget

2. **Personnel Costs**
   - Key roles required (based on project scope, not invented names)
   - FTE allocations and justifications
   - Salary ranges appropriate to nonprofit/tribal/public sector
   - Benefits as percentage of salaries (typically 25-35%)
   - Explain WHY these positions are necessary (link to project goals)

3. **Operating Expenses**
   - Use standard categories: Supplies, Equipment, Travel, Communications, etc.
   - Provide cost ranges and justifications
   - Reference industry benchmarks where appropriate
   - Flag any significant or unusual expenses

4. **Indirect Costs**
   - Administrative overhead (typical range: 10-20% for nonprofits)
   - Facilities and utilities allocation
   - Justification for indirect rate

5. **Budget Narrative**
   - For each major cost category, explain:
     * What it includes
     * Why it's necessary (strategic connection)
     * How the amount was determined
     * Any assumptions or dependencies

6. **Cost-Effectiveness Analysis**
   - How this budget achieves maximum impact
   - Comparison to similar projects (if data available from research)
   - Value proposition for funders

7. **Budget Risks & Contingencies**
   - Potential cost overruns and their likelihood
   - Mitigation strategies
   - Contingency plan (typical: 5-10% contingency reserve)

### SENIOR-LEVEL QUALITY MARKERS

Your document must demonstrate:

✓ **Strategic Thinking:** Every cost ties back to project goals and success criteria
✓ **Evidence-Based:** Costs based on research, benchmarks, or organizational data (cite previous documents)
✓ **Anticipatory:** Address obvious funder questions before they're asked
✓ **Realistic:** Costs appropriate for nonprofit/tribal/public sector context
✓ **Professional Formatting:** Use tables where appropriate (Markdown format)
✓ **Risk-Aware:** Acknowledge uncertainties and explain assumptions

### EXAMPLE OF SENIOR-LEVEL BUDGET NARRATIVE

**GOOD (Senior-level):**
> **Program Coordinator (1.0 FTE, $65,000-$75,000):** This role is essential for day-to-day project management and stakeholder coordination. The salary range reflects regional nonprofit compensation data (see Context document) and ensures we can attract a candidate with 5+ years of relevant experience. Without dedicated coordination, our timeline risks (see Risks document) become significantly more likely. This position manages the five workstreams identified in our Process Workflow and serves as primary liaison to the three key stakeholder groups.

**BAD (Junior-level):**
> **Program Coordinator ($70,000):** We need someone to manage the project and coordinate with stakeholders.

### STRICT CONSTRAINTS

1. **DO NOT invent:** Specific dollar amounts unless they're clearly estimates with ranges
2. **DO NOT name:** Specific vendors, products, or external consultants
3. **DO NOT fabricate:** Grant amounts, funding commitments, or revenue projections
4. **DO use:** Ranges, categories, industry benchmarks, and clearly labeled assumptions
5. **DO cross-reference:** Previous documents (Goals, Scope, Timeline, Risks) to show integration
6. **DO acknowledge:** What you don't know ("Pending stakeholder consultation..." or "To be determined during Month 1...")

### OUTPUT FORMAT

Markdown document starting with: # Initial Budget

Include:
- At least 7 major sections (H2 headings)
- At least 2-3 subsections (H3) per major section
- Minimum 1500 words (aim for depth and professionalism)
- At least one budget summary table (Markdown format)
- Cross-references to at least 2 other documents

Write the complete Initial Budget document now.
"""

    def _build_risks_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Risks and Assumptions document.

        Leverages frameworks research to generate senior-level risk assessment.
        """
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Risk Management Analyst with 15+ years of experience** in nonprofit, tribal, and public sector project management.

You are known for risk assessments that:
- Use quantitative risk matrices (Likelihood × Impact)
- Include concrete, actionable mitigation strategies
- Distinguish between risks and assumptions
- Anticipate cascading effects and dependencies
- Balance comprehensiveness with readability for executives

## DOCUMENT TO WRITE
Risks and Assumptions

## PROJECT CONTEXT
**Project Name:** {project.name}
**Project Description:** {project.description}
{f"**Additional Context:** {project.additional_context}" if project.additional_context else ""}

## PREVIOUS DOCUMENTS (for consistency)
{prev_context}

## RESEARCH FINDINGS
{research_summary}

## PROFESSIONAL FRAMEWORKS & TEMPLATES
{frameworks}

Use the risk matrix frameworks, assessment structures, and professional examples from the frameworks above.

## YOUR TASK

Write a comprehensive Risks and Assumptions document that demonstrates senior-level risk management.

### REQUIRED STRUCTURE

1. **Risk Assessment Overview**
   - Purpose and scope of this risk assessment
   - Risk rating methodology (define your Likelihood × Impact scale)
   - How this assessment will be used and updated
   - Executive summary of top 3-5 risks

2. **Risk Matrix & Definitions**
   - Define your rating scales (Low/Medium/High or 1-5)
   - Likelihood scale with concrete criteria
   - Impact scale with concrete criteria
   - Risk score calculation (Likelihood × Impact)

3. **Strategic Risks** (High-level, big picture)
   - Risks to overall project viability
   - External environmental risks
   - Stakeholder and political risks
   - Each risk must include:
     * Risk statement (clear, specific)
     * Likelihood rating + justification
     * Impact rating + justification
     * Current mitigation measures
     * Contingency plans
     * Risk owner or responsible party (role, not name)

4. **Operational Risks** (Day-to-day execution)
   - Timeline and schedule risks
   - Resource availability risks
   - Technical and implementation risks
   - Same structure as Strategic Risks

5. **Financial Risks**
   - Budget overrun scenarios
   - Funding uncertainty
   - Cost escalation risks
   - Same structure as above

6. **Compliance & Regulatory Risks**
   - Legal and regulatory requirements
   - Data privacy and security (if applicable)
   - Grant compliance (if applicable)

7. **Key Assumptions**
   - Critical assumptions this project depends on
   - Validity of each assumption (how confident are we?)
   - What happens if assumption proves false?
   - Validation plan (how will we test/verify?)

8. **Risk Mitigation Strategy**
   - Overall approach to risk management
   - Monitoring and review schedule
   - Escalation procedures
   - Risk ownership and accountability

9. **Risk Register Summary Table**
   - Markdown table with: Risk ID, Risk Name, Category, Likelihood, Impact, Score, Status

### RISK MATRIX TEMPLATE

Use a standard 3×3 or 5×5 matrix:

**Likelihood Scale:**
- **High (3):** >50% probability, expected to occur
- **Medium (2):** 20-50% probability, may occur
- **Low (1):** <20% probability, unlikely but possible

**Impact Scale:**
- **High (3):** Major impact on timeline (>3 months), budget (>20%), or scope
- **Medium (2):** Moderate impact requiring plan adjustments
- **Low (1):** Minor impact, easily absorbed

**Risk Score:** Likelihood × Impact (1-9)
- **Critical (7-9):** Immediate attention required
- **Significant (4-6):** Active monitoring and mitigation
- **Minor (1-3):** Document and monitor

### EXAMPLE OF SENIOR-LEVEL RISK STATEMENT

**GOOD (Senior-level):**
> **Risk R-003: Key Stakeholder Availability**
>
> **Statement:** Tribal Council members may have limited availability during Q2 (April-June) due to traditional ceremonial obligations, potentially delaying approval of Phase 1 deliverables.
>
> **Likelihood:** Medium (2) - Based on historical patterns from similar projects and input from Stakeholder Notes document
> **Impact:** Medium (2) - Would delay timeline by 4-6 weeks but wouldn't compromise project viability
> **Risk Score:** 4 (Significant - Active Mitigation Required)
>
> **Current Mitigation:**
> - Schedule critical approval meetings in Q1 and Q3
> - Build 6-week buffer into Timeline (see Milestones document)
> - Establish backup approval authority in writing
> - Use asynchronous review periods to maximize flexibility
>
> **Contingency Plan:** If approval is delayed beyond buffer period, we can parallelize Phase 2 planning activities that don't require formal approval, minimizing overall schedule impact.
>
> **Risk Owner:** Program Director (in coordination with Tribal Liaison)

**BAD (Junior-level):**
> **Risk:** Stakeholders might not be available.
> **Impact:** Could cause delays.
> **Mitigation:** Try to schedule meetings in advance.

### SENIOR-LEVEL QUALITY MARKERS

Your document must demonstrate:

✓ **Quantitative Assessment:** Every risk has Likelihood, Impact, and Score ratings with justifications
✓ **Specificity:** Risks are concrete and specific, not vague or generic
✓ **Actionable Mitigation:** Each mitigation is specific, realistic, and assigned to a role
✓ **Cross-Document Integration:** References Budget, Timeline, Stakeholder documents
✓ **Cascading Analysis:** Considers how one risk might trigger others
✓ **Executive-Ready:** Summary table and top-risks section for quick decision-making

### STRICT CONSTRAINTS

1. **DO NOT invent:** Specific people's names, external organizations, or past incidents
2. **DO NOT exaggerate:** Keep likelihood and impact ratings realistic and evidence-based
3. **DO use:** Risk management terminology correctly (mitigate, transfer, accept, avoid)
4. **DO cross-reference:** Previous documents to ground risks in project specifics
5. **DO acknowledge:** Uncertainty ("Based on available information..." "Pending stakeholder consultation...")
6. **MUST include:** At least 8-12 distinct risks across categories

### OUTPUT FORMAT

Markdown document starting with: # Risks and Assumptions

Include:
- At least 9 major sections (H2 headings)
- Minimum 8-12 distinct risks with full analysis
- At least one risk register summary table
- Minimum 2000 words (depth is critical for risk assessment)
- Cross-references to at least 3 other documents

Write the complete Risks and Assumptions document now.
"""

    def _build_sops_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Standard Operating Procedures (SOPs) document.

        Leverages frameworks research to generate senior-level SOP documentation.
        """
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Operations Manager with 15+ years of experience** writing SOPs for nonprofit, tribal, and public sector organizations.

You are known for SOPs that:
- Use clear, numbered procedures that anyone can follow
- Include decision trees and escalation paths
- Define roles and responsibilities (RACI format)
- Specify tools, templates, and documentation requirements
- Balance thoroughness with usability

## DOCUMENT TO WRITE
Standard Operating Procedures (SOPs)

## PROJECT CONTEXT
**Project Name:** {project.name}
**Project Description:** {project.description}
{f"**Additional Context:** {project.additional_context}" if project.additional_context else ""}

## PREVIOUS DOCUMENTS (for consistency)
{prev_context}

## RESEARCH FINDINGS
{research_summary}

## PROFESSIONAL FRAMEWORKS & TEMPLATES
{frameworks}

Use the SOP formats, RACI structures, and professional examples from the frameworks above.

## YOUR TASK

Write comprehensive Standard Operating Procedures that demonstrate senior-level operational planning.

### REQUIRED STRUCTURE

1. **SOP Overview**
   - Purpose and scope of these procedures
   - Who should use this document (audience)
   - How SOPs will be maintained and updated
   - Version control and approval process

2. **Roles & Responsibilities (RACI Matrix)**
   - Define key roles for this project (Program Director, Coordinator, etc.)
   - Use RACI format for major activities:
     * **R**esponsible: Who does the work
     * **A**ccountable: Who has final authority
     * **C**onsulted: Who provides input
     * **I**nformed: Who needs to know
   - Present as Markdown table

3. **Core Operating Procedures**

For each major procedure, include:
   - **Procedure Name & ID** (e.g., SOP-001: Monthly Reporting)
   - **Purpose:** Why this procedure exists
   - **Frequency:** When/how often it happens
   - **Responsible Role:** Who leads this
   - **Step-by-Step Process:** Numbered steps with clear actions
   - **Required Tools/Templates:** What you need
   - **Quality Checks:** How to verify it's done correctly
   - **Escalation:** What to do if problems arise

Minimum procedures to include:
   - Project kickoff and onboarding
   - Regular team meetings and communications
   - Progress tracking and status reporting
   - Budget monitoring and expense approval
   - Risk monitoring and issue escalation
   - Stakeholder communication and approvals
   - Quality assurance and deliverable review
   - Change request management
   - Document management and version control

4. **Communication Protocols**
   - Meeting schedules and formats
   - Status update templates and distribution
   - Escalation paths for issues
   - Stakeholder communication guidelines

5. **Document Management**
   - File naming conventions
   - Version control procedures
   - Where documents are stored
   - Backup and archival procedures

6. **Quality Assurance**
   - Deliverable review process
   - Quality criteria and checklists
   - Approval workflows

7. **Issue & Change Management**
   - How to log and track issues
   - Change request process
   - Approval thresholds (what needs sign-off)

8. **Compliance & Record-Keeping**
   - Required documentation for audits (if applicable)
   - Retention policies
   - Privacy and confidentiality procedures (if applicable)

### RACI MATRIX EXAMPLE

| Activity | Program Director | Coordinator | Finance Lead | Stakeholder Group |
|----------|-----------------|-------------|--------------|-------------------|
| Monthly Status Report | A | R | C | I |
| Budget Reallocation | A | C | R | I |
| Stakeholder Meetings | A,R | C | I | C |

### EXAMPLE OF SENIOR-LEVEL SOP

**GOOD (Senior-level):**

> **SOP-003: Monthly Status Reporting**
>
> **Purpose:** Ensure consistent, timely communication of project progress to all stakeholders and maintain audit trail for grant compliance.
>
> **Frequency:** Monthly, due by 5th business day of following month
>
> **Responsible Role:** Program Coordinator
> **Accountable Role:** Program Director
>
> **Prerequisites:**
> - Completed timesheets from all team members
> - Updated budget tracking spreadsheet
> - Risk register review completed
> - All deliverables for the month logged
>
> **Procedure:**
>
> 1. **Gather Data** (Days 1-3 of month)
>    - Collect timesheets from all team members
>    - Run budget variance report from finance system
>    - Review risk register for changes
>    - Compile list of completed deliverables
>    - Note any issues or blockers encountered
>
> 2. **Draft Report** (Day 3-4)
>    - Use Monthly Status Template (shared drive: /Templates/Status-Report.docx)
>    - Complete all required sections:
>      * Executive Summary (2-3 sentences)
>      * Progress Against Timeline (reference Gantt chart)
>      * Budget Status (variance analysis)
>      * Risks & Issues (changes from last month)
>      * Next Month's Priorities
>      * Decisions Needed (if any)
>    - Include quantitative metrics (% complete, budget burn rate, etc.)
>
> 3. **Internal Review** (Day 4)
>    - Send draft to Program Director by 9 AM
>    - Program Director reviews and provides feedback by 5 PM
>    - Coordinator incorporates feedback
>
> 4. **Quality Check** (Day 4-5)
>    - Verify all data is accurate and sourced
>    - Check for consistency with previous reports
>    - Ensure no contradictions with other project documents
>    - Proofread for professional tone and clarity
>
> 5. **Distribution** (Day 5)
>    - Send final report to distribution list (see Communications Protocol)
>    - Post to shared drive: /Reports/YYYY-MM-Status-Report.pdf
>    - Log distribution in tracking system
>    - Set reminder for next month's report
>
> **Quality Checks:**
> - [ ] All required sections completed
> - [ ] Metrics match finance system data
> - [ ] Risk changes reflected in risk register
> - [ ] Professional formatting and tone
> - [ ] No TBD or placeholder text
>
> **Escalation:**
> - If data is unavailable: Notify Program Director immediately and note gap in report
> - If significant variances or issues: Schedule urgent meeting before distribution
> - If deadline will be missed: Notify stakeholders 48 hours in advance with revised date

**BAD (Junior-level):**
> **Monthly Status Report**
> The coordinator should send a status report each month. Include what was done and what's coming up.

### SENIOR-LEVEL QUALITY MARKERS

Your document must demonstrate:

✓ **Procedural Clarity:** Every SOP has numbered steps anyone could follow
✓ **RACI Defined:** Clear accountability for each major activity
✓ **Tool-Specific:** Names templates, systems, and tools (even if generic)
✓ **Exception Handling:** Includes "what if" scenarios and escalation paths
✓ **Quality Gates:** Built-in checkpoints to prevent errors
✓ **Cross-Referenced:** Links to other project documents and templates

### STRICT CONSTRAINTS

1. **DO NOT invent:** Specific software products, proprietary tools, or vendor names unless in research
2. **DO NOT name:** Specific individuals (use roles: "Program Director" not "Jane Smith")
3. **DO use:** Generic but specific terms ("project management system", "shared drive", "finance tracking spreadsheet")
4. **DO include:** At least 6-8 complete SOPs with full detail
5. **DO cross-reference:** Other project documents (Timeline, Budget, Risks, Process Workflow)
6. **MUST include:** At least one RACI matrix table

### OUTPUT FORMAT

Markdown document starting with: # Standard Operating Procedures

Include:
- At least 8 major sections (H2 headings)
- At least 6-8 complete SOPs with numbered procedures
- At least one RACI matrix table (Markdown format)
- Minimum 2000 words (SOPs require significant detail)
- Cross-references to at least 3 other documents
- Checklists where appropriate (using Markdown checkbox format)

Write the complete Standard Operating Procedures document now.
"""

    def _extract_frameworks_research(self, results: list[AgentResult]) -> str:
        """Extract frameworks research from agent results.

        Specifically looks for the frameworks agent (agent_000_frameworks)
        and compiles its findings for use in generation prompts.
        """
        frameworks_agent = next(
            (r for r in results if r.agent_id == "agent_000_frameworks"),
            None,
        )

        if not frameworks_agent or not frameworks_agent.raw_response:
            return """No frameworks research available. Use your best judgment based on industry standards for:
- SMART goals criteria
- RACI matrix structure
- Risk assessment matrices (Likelihood × Impact)
- Standard budget categories for nonprofits
- Professional SOP formatting with numbered procedures"""

        # Return the full raw response from frameworks agent
        # This contains the structured frameworks, examples, and standards that Claude researched
        return frameworks_agent.raw_response

    def _compile_research_summary(self, results: list[AgentResult]) -> str:
        """Compile research results into a summary."""
        if not results:
            return "No research results available."

        sections = []
        for result in results:
            if result.findings:
                findings = "\n".join(f"  - {f}" for f in result.findings[:5])
                sections.append(f"### Agent: {result.agent_id}\n{findings}")

        return "\n\n".join(sections) if sections else "No findings available."

    def _get_previous_context(self, docs: list[Document]) -> str:
        """Get context from previous documents."""
        if not docs:
            return "No previous documents."

        # Include titles and brief excerpts
        context_parts = []
        for doc in docs[-3:]:  # Last 3 documents for context
            excerpt = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
            context_parts.append(f"**{doc.title}:**\n{excerpt}")

        return "\n\n".join(context_parts)

    async def generate_batch(
        self,
        batch: DocumentBatch,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> list[Document]:
        """Generate all documents in a batch.

        Args:
            batch: Batch definition.
            project: Project input.
            research_results: Research results.
            previous_docs: Previously generated documents.

        Returns:
            List of generated documents.
        """
        documents = []
        for doc_type in batch.document_types:
            doc = await self.generate_document(
                doc_type, project, research_results, previous_docs + documents
            )
            documents.append(doc)
        return documents

    async def generate_all(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
    ) -> GeneratedProject:
        """Generate all 15 documents in proper batch order.

        Args:
            project: Project input.
            research_results: Research results from Phase 1.

        Returns:
            Complete generated project.
        """
        start_time = datetime.utcnow()
        all_documents: list[Document] = []

        # Process batches in order (respecting dependencies)
        for batch in DOCUMENT_BATCHES:
            docs = await self.generate_batch(
                batch, project, research_results, all_documents
            )
            all_documents.extend(docs)

        end_time = datetime.utcnow()
        generation_time = (end_time - start_time).total_seconds()

        return GeneratedProject(
            project_name=project.name,
            project_area=project.area,
            documents=all_documents,
            total_word_count=sum(d.word_count for d in all_documents),
            generation_time_seconds=generation_time,
            created_at=start_time,
        )
