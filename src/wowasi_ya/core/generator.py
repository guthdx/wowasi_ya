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

# Conservative writing style rules to avoid obvious AI crutches
# (Per user request: "less aggressive" - only target clear AI tells)
WRITING_STYLE_RULES = """
### WRITING STYLE (avoid obvious AI tells)

**Punctuation:**
- Avoid em dashes (—). Use commas, parentheses, or separate sentences instead.
- Exception: You may use 1-2 em dashes maximum if truly needed.

**Banned Vocabulary:** Never use these AI-associated terms:
- delve, tapestry, realm, vibrant, bustling, harness
- leverage (use "use" or "apply"), utilize (use "use")
- seamlessly, meticulous, intricate, pivotal
- underscore, embark, navigate, landscape, foster
- cutting-edge (use "modern" or "new")
- holistic, synergy, synergistic, paradigm

**Transitions:** Avoid these formulaic transitions:
- Furthermore, Moreover, In addition, Additionally
- Firstly, Secondly, Thirdly, In conclusion, To summarize
- Use natural flow instead. Start next thought directly when possible.

**Openings:** Never start a document or section with:
- "In today's..." or "In an era of..."
- "In the ever-evolving landscape..."
- Start with specific facts or direct statements instead.
"""

import re

from wowasi_ya.models.agent import AgentResult
from wowasi_ya.models.document import (
    DOCUMENT_BATCHES,
    Document,
    DocumentBatch,
    DocumentType,
    GeneratedProject,
)
from wowasi_ya.models.project import ProjectInput


def _is_content_truncated(content: str) -> tuple[bool, str]:
    """Check if generated content appears truncated.

    Returns:
        Tuple of (is_truncated, reason).
    """
    if not content or not content.strip():
        return True, "Content is empty"

    content = content.strip()

    # Check 1: Unbalanced code blocks
    code_block_count = content.count("```")
    if code_block_count % 2 != 0:
        return True, "Unbalanced code blocks"

    # Check 2: Ending mid-sentence
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if lines:
        last_line = lines[-1]

        # Skip check for special line types
        skip_patterns = [
            r"^#+\s",  # Heading
            r"^\|.*\|$",  # Table row
            r"^```",  # Code block marker
            r"^---$",  # Horizontal rule
            r"^[-*+]\s",  # List item
            r"^\d+\.\s",  # Numbered list
        ]
        is_special = any(re.match(p, last_line) for p in skip_patterns)

        if not is_special:
            valid_endings = (".", "!", "?", ":", ")", "]", '"', "'", "`", "*", "_")
            if not last_line.endswith(valid_endings):
                return True, f"Ends mid-sentence: '{last_line[-40:]}'"

    # Check 3: Incomplete markdown at end
    incomplete_patterns = [
        (r"\*\*[^*]+$", "Unclosed bold"),
        (r"\[[^\]]*$", "Unclosed link"),
    ]
    for pattern, reason in incomplete_patterns:
        if re.search(pattern, content[-200:]):
            return True, reason

    return False, ""


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
        max_retries: int = 2,
    ) -> Document:
        """Generate a single document with truncation detection and retry.

        Args:
            doc_type: Type of document to generate.
            project: Project input.
            research_results: Results from research phase.
            previous_docs: Previously generated documents for context.
            max_retries: Maximum retry attempts if truncation detected.

        Returns:
            Generated document.
        """
        client = await self._get_client()
        config = DOCUMENT_CONFIG[doc_type]

        prompt = self._build_generation_prompt(
            doc_type, project, research_results, previous_docs
        )

        # Progressive token limits for retries
        # NOTE: Keep max at 8192 to avoid Claude API streaming requirement
        # (requests >10 min require streaming which we don't support yet)
        base_tokens = min(self.settings.max_generation_tokens, 8192)
        token_multipliers = [1.0, 1.0, 1.0]  # Don't escalate - stay at 8192 max

        last_content = ""
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Calculate tokens for this attempt
                current_max_tokens = int(base_tokens * token_multipliers[min(attempt, len(token_multipliers) - 1)])

                # Use abstracted LLM client (works with both Claude and Llama)
                content = await client.generate(
                    prompt=prompt,
                    max_tokens=current_max_tokens,
                    temperature=0.7,
                )

                last_content = content

                # Check for truncation
                is_truncated, reason = _is_content_truncated(content)

                if is_truncated:
                    if attempt < max_retries:
                        logger.warning(
                            f"Document {doc_type.value} appears truncated ({reason}). "
                            f"Retrying with higher token limit (attempt {attempt + 2}/{max_retries + 1})"
                        )
                        continue
                    else:
                        # Final attempt still truncated - log warning but proceed
                        logger.warning(
                            f"Document {doc_type.value} still truncated after {max_retries + 1} attempts: {reason}. "
                            f"Proceeding with best result ({len(content.split())} words)"
                        )

                # Success or final attempt
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
                last_error = e
                logger.error(f"Error generating {doc_type} (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    continue
                break

        # All attempts failed - return error or best content
        if last_content:
            logger.warning(f"Returning partial content for {doc_type} after errors")
            return Document(
                type=doc_type,
                title=config["title"],
                content=last_content,
                folder=config["folder"],
                filename=config["filename"],
                generated_at=datetime.utcnow(),
                word_count=len(last_content.split()),
            )

        # Complete failure
        return Document(
            type=doc_type,
            title=config["title"],
            content=f"# {config['title']}\n\n*Error generating document: {last_error!s}*",
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
        # Route to specialized prompts for each document type
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

        builder = prompt_builders.get(doc_type)
        if builder:
            return builder(project, research_results, previous_docs)

        # Fallback to generic prompt (should not be reached with all 15 mapped)
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

{WRITING_STYLE_RULES}

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

{WRITING_STYLE_RULES}

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

{WRITING_STYLE_RULES}

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

{WRITING_STYLE_RULES}

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

    def _build_goals_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Goals and Success Criteria document.

        Leverages frameworks research to generate senior-level goal-setting documentation.
        """
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Strategic Planner with 15+ years of experience** defining goals and success metrics for nonprofit, tribal, and public sector organizations.

You are known for goal frameworks that:
- Use SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound) rigorously
- Distinguish between outputs, outcomes, and impact
- Include leading AND lagging indicators
- Create clear line-of-sight from activities to strategic objectives
- Balance ambitious vision with realistic milestones

## DOCUMENT TO WRITE
Goals and Success Criteria

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

Use the goal-setting frameworks, OKR structures, and professional examples from the frameworks above.

## YOUR TASK

Write a comprehensive Goals and Success Criteria document that demonstrates senior-level strategic planning.

### REQUIRED STRUCTURE

1. **Executive Summary**
   - Project vision statement (1-2 sentences)
   - Primary goal in plain language
   - Why this matters (strategic context)
   - How success will be measured (high-level)

2. **Goal Framework Overview**
   - Methodology used (SMART, OKR, Logic Model, or hybrid)
   - How goals cascade from strategic to operational
   - How success criteria were determined
   - Alignment with organizational mission (if applicable)

3. **Strategic Goals** (2-3 high-level goals)
   For each strategic goal:
   - Goal statement (clear, measurable)
   - Strategic rationale (why this matters)
   - Alignment (how it connects to organizational priorities)
   - Time horizon (when to achieve)
   - Key success indicators

4. **Operational Objectives** (4-6 specific objectives)
   For each objective, apply SMART criteria:
   - **S**pecific: Exactly what will be accomplished?
   - **M**easurable: What metrics will track progress?
   - **A**chievable: Is this realistic given resources?
   - **R**elevant: How does this support strategic goals?
   - **T**ime-bound: What is the deadline?

5. **Success Metrics & KPIs**
   Include a metrics table with:
   - Metric name
   - Type (output/outcome/impact)
   - Baseline (current state)
   - Target (desired state)
   - Measurement method
   - Frequency of measurement
   - Responsible party

6. **Leading vs. Lagging Indicators**
   - Leading indicators (predictive, early warning)
   - Lagging indicators (results, confirmation)
   - How both will be used for decision-making

7. **Outputs, Outcomes, and Impact**
   - **Outputs:** Direct deliverables (what we produce)
   - **Outcomes:** Short-term changes (what happens as a result)
   - **Impact:** Long-term change (ultimate difference made)
   - Logic model or theory of change narrative

8. **Success Criteria by Phase**
   - Phase 1 criteria (what "success" looks like early)
   - Phase 2 criteria (mid-project milestones)
   - Final success criteria (project completion)
   - Post-project sustainability indicators

9. **Measurement & Evaluation Plan**
   - Data collection methods
   - Evaluation timeline
   - Who will conduct evaluation
   - How findings will be used

10. **Risks to Goal Achievement**
    - Key assumptions that must hold true
    - Dependencies on external factors
    - Reference to Risks document for detailed analysis

### SMART GOAL EXAMPLE

**GOOD (Senior-level):**
> **Objective 2.1: Community Engagement Baseline**
>
> **Specific:** Conduct comprehensive community needs assessment across three target communities (Eagle Butte, Fort Thompson, Lower Brule), gathering input from minimum 150 community members including elders, youth, parents, and service providers.
>
> **Measurable:**
> - 150+ survey responses completed (50+ per community)
> - 6 focus groups conducted (2 per community)
> - 12 key informant interviews completed
> - Assessment report with statistical analysis delivered
>
> **Achievable:** Based on similar assessments conducted by partner organizations and available community liaisons in each location. Timeline accounts for cultural protocols and seasonal considerations.
>
> **Relevant:** Directly supports Strategic Goal 1 (Community-Centered Design) and ensures project activities are grounded in actual community priorities rather than external assumptions.
>
> **Time-bound:** Complete within first 90 days of project launch (Months 1-3), with preliminary findings available by Day 60 to inform Phase 2 planning.
>
> **Success Indicators:**
> - Response rate ≥60% of invited participants
> - Geographic representation across all three communities
> - Demographic diversity matching community composition
> - Actionable recommendations in final report

**BAD (Junior-level):**
> **Goal:** Do a community survey to find out what people need.
> **Success:** Get enough responses to write a report.

### METRICS TABLE TEMPLATE

| Metric | Type | Baseline | Target | Method | Frequency | Owner |
|--------|------|----------|--------|--------|-----------|-------|
| Participants served | Output | 0 | 200 | Registration system | Monthly | Coordinator |
| Satisfaction score | Outcome | N/A | ≥4.0/5.0 | Survey | Quarterly | Evaluator |
| Skills improvement | Outcome | Pre-test | 20% gain | Pre/post assessment | End of cohort | Coordinator |

### SENIOR-LEVEL QUALITY MARKERS

Your document must demonstrate:

✓ **SMART Rigor:** Every objective meets all five SMART criteria explicitly
✓ **Hierarchy:** Clear cascade from vision → goals → objectives → metrics
✓ **Balance:** Mix of quantitative and qualitative measures
✓ **Leading Indicators:** Early warning metrics, not just final results
✓ **Theory of Change:** Logical connection from activities to impact
✓ **Realistic Targets:** Grounded in research, benchmarks, or organizational capacity
✓ **Accountability:** Clear ownership for each metric

### STRICT CONSTRAINTS

1. **DO NOT invent:** Specific numerical targets without basis (use ranges or "TBD pending baseline")
2. **DO NOT fabricate:** Baseline data, benchmarks, or historical performance
3. **DO use:** Placeholders where data will come from discovery ("Baseline TBD in Month 1")
4. **DO cross-reference:** Budget, Timeline, Scope documents to ensure alignment
5. **DO distinguish:** Outputs (activities) from Outcomes (changes) from Impact (long-term)
6. **MUST include:** At least one metrics/KPI table in Markdown format

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Goals and Success Criteria

Include:
- At least 10 major sections (H2 headings)
- 2-3 strategic goals with 4-6 operational objectives
- At least one comprehensive metrics table
- Minimum 1800 words
- Cross-references to at least 3 other documents
- SMART criteria explicitly addressed for each objective

Write the complete Goals and Success Criteria document now.
"""

    def _build_timeline_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Timeline and Milestones document.

        Leverages frameworks research to generate senior-level project scheduling.
        """
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Project Manager (PMP) with 15+ years of experience** developing project schedules for nonprofit, tribal, and public sector organizations.

You are known for timelines that:
- Use industry-standard project scheduling conventions (Gantt, milestones, dependencies)
- Identify critical path activities and schedule risks
- Build in appropriate buffers for nonprofit/tribal contexts
- Account for cultural and seasonal considerations
- Balance ambition with realistic resource constraints

## DOCUMENT TO WRITE
Timeline and Milestones

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

Use the scheduling frameworks, milestone structures, and professional examples from the frameworks above.

## YOUR TASK

Write a comprehensive Timeline and Milestones document that demonstrates senior-level project scheduling.

### REQUIRED STRUCTURE

1. **Timeline Overview**
   - Total project duration (start to end)
   - Major phases and their timeframes
   - Key assumptions affecting the schedule
   - Critical success factors for timeline adherence

2. **Project Phases**
   Define major phases (typically 3-5):
   - Phase name and duration
   - Phase objectives (what will be accomplished)
   - Key activities within the phase
   - Phase deliverables
   - Phase completion criteria (how we know it's done)
   - Dependencies on previous phases

3. **Milestone Schedule**
   Include milestone table with:
   - Milestone ID (M-001, M-002, etc.)
   - Milestone name
   - Target date (or Month/Week)
   - Phase
   - Description
   - Deliverables due
   - Success criteria
   - Dependencies

4. **Critical Path Analysis**
   - Activities on the critical path (zero float)
   - Schedule risks if critical activities slip
   - Alternative paths and their float time
   - Buffer strategy for critical path protection

5. **Gantt Chart Representation**
   ASCII/text-based timeline showing:
   - Phases and their duration
   - Key milestones marked
   - Dependencies between activities
   - Parallel workstreams where applicable

6. **Activity Schedule by Phase**
   For each phase, detailed activities:
   - Activity name
   - Duration (days/weeks)
   - Start date (relative)
   - End date (relative)
   - Dependencies (what must finish first)
   - Resources required
   - Deliverables produced

7. **Resource Loading**
   - When key resources are needed
   - Peak demand periods
   - Resource conflicts and resolution strategy
   - Reference to Budget document for resource costs

8. **Schedule Risks & Buffers**
   - Known schedule risks (reference Risks document)
   - Buffer time built into timeline
   - Contingency triggers (when to use buffer)
   - Acceleration strategies if behind schedule

9. **External Dependencies**
   - Approvals needed from stakeholders
   - External deliverables or inputs required
   - Seasonal or cultural considerations
   - Grant or funding cycles that affect timing

10. **Schedule Management Approach**
    - How progress will be tracked
    - Status reporting frequency
    - Change control for schedule changes
    - Escalation for schedule issues

### GANTT CHART EXAMPLE (ASCII)

```
Phase/Activity          | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10| M11| M12|
------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
PHASE 1: Planning       |████████████|    |    |    |    |    |    |    |    |    |    |
  Needs Assessment      |████████|    |    |    |    |    |    |    |    |    |    |    |
  Stakeholder Mapping   |████|    |    |    |    |    |    |    |    |    |    |    |    |
  Design Workshops      |    |████████|    |    |    |    |    |    |    |    |    |    |
  ◆ M-001: Plan Approved|    |    |  ◆ |    |    |    |    |    |    |    |    |    |
PHASE 2: Implementation |    |    |    |████████████████████████|    |    |    |    |
  Cohort 1 Launch       |    |    |    |████████████|    |    |    |    |    |    |    |
  Cohort 2 Launch       |    |    |    |    |    |████████████|    |    |    |    |    |
  ◆ M-002: Mid-Point    |    |    |    |    |    |    |  ◆ |    |    |    |    |    |
PHASE 3: Evaluation     |    |    |    |    |    |    |    |    |████████████████|    |
  Data Collection       |    |    |    |    |    |    |    |    |████████|    |    |    |
  Final Report          |    |    |    |    |    |    |    |    |    |████████|    |    |
  ◆ M-003: Project End  |    |    |    |    |    |    |    |    |    |    |    |  ◆ |
```
◆ = Milestone

### MILESTONE TABLE EXAMPLE

| ID | Milestone | Target | Phase | Deliverables | Success Criteria |
|----|-----------|--------|-------|--------------|------------------|
| M-001 | Planning Complete | Month 3 | 1 | Approved project plan, stakeholder buy-in | Sign-off from all key stakeholders |
| M-002 | Mid-Point Review | Month 6 | 2 | Progress report, 50% of participants engaged | On-track metrics, no critical risks |
| M-003 | Project Completion | Month 12 | 3 | Final report, sustainability plan | All deliverables accepted |

### SENIOR-LEVEL QUALITY MARKERS

Your document must demonstrate:

✓ **Phased Approach:** Clear phases with defined entry/exit criteria
✓ **Dependencies:** Explicit relationships between activities and milestones
✓ **Critical Path:** Identification of schedule-critical activities
✓ **Buffers:** Realistic contingency time built in
✓ **Context-Aware:** Accounts for cultural, seasonal, and organizational factors
✓ **Resource-Linked:** Timeline aligned with Budget and staffing plan
✓ **Risk-Aware:** References schedule risks from Risks document

### EXAMPLE OF SENIOR-LEVEL SCHEDULE NARRATIVE

**GOOD (Senior-level):**
> **Phase 2: Implementation (Months 4-9)**
>
> This phase represents the core service delivery period and is on the critical path. The 6-month duration accounts for:
> - Two cohorts of 25 participants each (staggered by 8 weeks)
> - Cultural calendar considerations (avoiding major ceremonies in June)
> - Learning curve for newly hired staff in first cohort
> - 2-week buffer between cohorts for process improvement
>
> **Critical Dependencies:**
> - Phase 1 approval (M-001) must be complete
> - Program Coordinator hired and onboarded (per Budget document)
> - Partnership agreements signed (per Stakeholder Notes)
>
> **Schedule Risk:** If Cohort 1 recruitment takes longer than 3 weeks, we will activate the waitlist strategy from Phase 1 planning. A 4-week delay in Cohort 1 would compress the buffer between cohorts but not affect the overall project end date.

**BAD (Junior-level):**
> **Phase 2 (Months 4-9):** Run the program for 6 months. Start with Cohort 1 and then do Cohort 2.

### STRICT CONSTRAINTS

1. **DO NOT invent:** Specific dates unless clearly marked as targets/estimates
2. **DO NOT ignore:** Dependencies between activities and phases
3. **DO use:** Relative timing (Month 1, Week 3) rather than calendar dates unless specified
4. **DO account for:** Cultural and seasonal factors relevant to tribal/nonprofit contexts
5. **DO cross-reference:** Budget (resources), Scope (deliverables), Risks (schedule risks)
6. **MUST include:** At least one milestone table and one visual timeline representation

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Timeline and Milestones

Include:
- At least 10 major sections (H2 headings)
- 3-5 project phases with activities
- Minimum 8-12 milestones in table format
- ASCII Gantt chart or timeline visualization
- Critical path identification
- Minimum 1800 words
- Cross-references to at least 3 other documents

Write the complete Timeline and Milestones document now.
"""

    def _build_project_brief_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Project Brief document.

        Leverages frameworks research to generate senior-level executive summary.
        """
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Program Officer with 15+ years of experience** writing executive briefs for nonprofit, tribal, and public sector leadership.

You are known for project briefs that:
- Capture attention in the first paragraph
- Communicate complex projects in accessible language
- Balance comprehensiveness with brevity
- Anticipate executive questions and address them proactively
- Provide clear decision points and ask

## DOCUMENT TO WRITE
Project Brief

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

Use the executive summary structures and professional examples from the frameworks above.

## YOUR TASK

Write a comprehensive Project Brief that demonstrates senior-level executive communication.

### REQUIRED STRUCTURE

1. **Executive Summary** (First section, crucial)
   - Project name and one-sentence description
   - The problem/opportunity being addressed (2-3 sentences)
   - Proposed solution (2-3 sentences)
   - Key outcomes and impact expected
   - Total investment required (range)
   - Timeline at a glance

2. **Problem Statement**
   - Current situation and its challenges
   - Who is affected and how
   - Consequences of not acting
   - Evidence/data supporting the need (from research)
   - Root causes being addressed

3. **Proposed Solution**
   - Project approach in plain language
   - Why this approach (evidence or best practice)
   - Key activities and deliverables
   - What makes this approach appropriate for the context
   - Alternatives considered and why not chosen

4. **Target Population & Beneficiaries**
   - Who will be served (demographics, geography)
   - Estimated reach (numbers)
   - Selection criteria (if applicable)
   - Community involvement in design

5. **Expected Outcomes & Impact**
   - Short-term outcomes (within project period)
   - Long-term impact (beyond project)
   - How outcomes will be measured
   - Reference to Goals document for detail

6. **Project Team & Partnerships**
   - Lead organization and qualifications
   - Key roles (not names, but positions)
   - Partner organizations and their roles
   - Community advisory involvement

7. **Budget Overview**
   - Total project cost (range)
   - Major cost categories (summary)
   - Cost per beneficiary (if calculable)
   - Funding sources (if known)
   - Reference to Budget document for detail

8. **Timeline Overview**
   - Project duration
   - Major phases and milestones
   - Key decision points
   - Reference to Timeline document for detail

9. **Risk Summary**
   - Top 3-5 risks in plain language
   - Mitigation strategies (brief)
   - Reference to Risks document for detail

10. **The Ask / Decision Required**
    - What decision or action is needed
    - From whom
    - By when
    - What happens next if approved

### EXAMPLE OF SENIOR-LEVEL EXECUTIVE SUMMARY

**GOOD (Senior-level):**
> **Executive Summary**
>
> The **Tribal Youth Mentorship Program** addresses a critical gap in support services for Native youth ages 14-21 in the Standing Rock region, where youth suicide rates are 2.5x the national average and high school graduation rates lag 15 points below state averages.
>
> This 24-month initiative pairs 200 tribal youth with trained adult mentors from their communities, combining one-on-one relationships with culturally-grounded group activities including language revitalization, traditional skills, and academic support. The program model is adapted from the evidence-based Big Brothers Big Sisters framework with significant cultural modifications developed in partnership with tribal elders and youth advisory councils.
>
> **Expected Impact:** 75% of participants will show improved school attendance, 60% will demonstrate increased cultural connectedness (validated scale), and the program will train 50 community members as certified mentors creating sustained capacity.
>
> **Investment:** $485,000-$565,000 over 24 months ($2,400-$2,800 per youth served)
>
> **Timeline:** Planning (Months 1-3), Implementation (Months 4-21), Evaluation (Months 22-24)
>
> **Decision Required:** Program approval and funding authorization by Tribal Council, requested by March 15.

**BAD (Junior-level):**
> **Summary:** We want to start a mentorship program for youth. It will help them do better in school and learn about their culture. We need funding to make it happen.

### SENIOR-LEVEL QUALITY MARKERS

Your document must demonstrate:

✓ **Hook:** First paragraph compels reader to continue
✓ **Evidence-Based:** Claims supported by data/research
✓ **Accessible:** Complex concepts in plain language
✓ **Comprehensive:** All key questions answered
✓ **Action-Oriented:** Clear ask and next steps
✓ **Contextual:** Appropriate for nonprofit/tribal governance
✓ **Connected:** References other project documents appropriately

### STRICT CONSTRAINTS

1. **DO NOT invent:** Statistics, funding amounts, or organizational details not in research/context
2. **DO NOT use:** Jargon without explanation or excessive acronyms
3. **DO write:** For busy executives (clear headers, scannable format)
4. **DO include:** Specific numbers and ranges where possible
5. **DO reference:** Other documents for detailed information
6. **MUST be:** Self-contained enough to understand project without reading other docs

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Project Brief

Include:
- At least 10 major sections (H2 headings)
- Compelling executive summary as first section
- Summary table or at-a-glance box
- Clear "Ask" or decision section
- Minimum 1500 words
- Cross-references to at least 4 other documents

Write the complete Project Brief document now.
"""

    def _build_stakeholder_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Stakeholder Notes document.

        Leverages frameworks research to generate senior-level stakeholder analysis.
        """
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Community Engagement Specialist with 15+ years of experience** in stakeholder analysis for nonprofit, tribal, and public sector projects.

You are known for stakeholder analyses that:
- Use power/interest grids to prioritize engagement
- Map formal AND informal influence networks
- Anticipate concerns and develop proactive responses
- Respect cultural protocols and community dynamics
- Create actionable engagement strategies

## DOCUMENT TO WRITE
Stakeholder Notes

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

Use the stakeholder analysis frameworks, power/interest grids, and professional examples from the frameworks above.

## YOUR TASK

Write comprehensive Stakeholder Notes that demonstrate senior-level community engagement planning.

### REQUIRED STRUCTURE

1. **Stakeholder Analysis Overview**
   - Purpose of this analysis
   - Methodology used (power/interest grid, influence mapping)
   - How stakeholders were identified
   - Cultural considerations in engagement

2. **Stakeholder Categories**
   Define major categories:
   - **Primary Stakeholders:** Directly affected by the project
   - **Secondary Stakeholders:** Indirectly affected
   - **Key Decision-Makers:** Authority to approve/block
   - **Influencers:** Shape opinions without formal authority
   - **Implementation Partners:** Will help deliver

3. **Power/Interest Grid**
   Create matrix:
   - High Power, High Interest: Manage Closely
   - High Power, Low Interest: Keep Satisfied
   - Low Power, High Interest: Keep Informed
   - Low Power, Low Interest: Monitor

   | Stakeholder Group | Power | Interest | Strategy |
   |-------------------|-------|----------|----------|
   | Example Group     | High  | High     | Manage Closely |

4. **Detailed Stakeholder Profiles**
   For each key stakeholder group:
   - Role and relationship to project
   - Interests and motivations
   - Potential concerns or objections
   - Influence on project success
   - Engagement strategy
   - Key messages
   - Communication preferences

5. **Formal Authority Map**
   - Who has approval authority
   - Decision-making processes
   - Governance structures
   - Compliance/regulatory stakeholders

6. **Informal Influence Network**
   - Community leaders and elders
   - Opinion shapers
   - Gatekeepers to communities
   - Cultural advisors
   - Historical relationships that matter

7. **Potential Supporters & Champions**
   - Who will advocate for the project
   - How to engage and empower them
   - Resources they can contribute
   - Recognition and acknowledgment

8. **Potential Resisters & Concerns**
   - Who may oppose or be skeptical
   - Root causes of concern
   - Legitimate issues to address
   - Engagement approach to build trust
   - When to escalate concerns

9. **Cultural & Protocol Considerations**
   - Traditional decision-making processes
   - Respect protocols (titles, introductions)
   - Timing considerations (ceremonies, seasons)
   - Language and communication norms
   - Historical context affecting trust

10. **Engagement Strategy Matrix**
    | Stakeholder | Engagement Level | Method | Frequency | Responsible |
    |-------------|-----------------|--------|-----------|-------------|
    | Group A     | Collaborate     | In-person | Weekly  | Director    |
    | Group B     | Consult         | Email     | Monthly | Coordinator |

11. **Communication Plan Summary**
    - Key messages by stakeholder group
    - Communication channels
    - Feedback mechanisms
    - Escalation paths

12. **Stakeholder Risks**
    - Risks related to stakeholder relationships
    - Reference to Risks document
    - Monitoring approach

### POWER/INTEREST GRID EXAMPLE

```
                    INTEREST
                 Low          High
            ┌──────────┬──────────┐
       High │  KEEP    │  MANAGE  │
            │SATISFIED │ CLOSELY  │
    POWER   ├──────────┼──────────┤
            │ MONITOR  │   KEEP   │
       Low  │  (Min)   │ INFORMED │
            └──────────┴──────────┘
```

### EXAMPLE OF SENIOR-LEVEL STAKEHOLDER PROFILE

**GOOD (Senior-level):**
> **Stakeholder Group: Tribal Council**
>
> **Role:** Governing body with approval authority over programs and funding
>
> **Power:** High (formal approval required; can allocate resources or redirect)
> **Interest:** High (youth outcomes directly affect community priorities)
> **Strategy:** Manage Closely
>
> **Interests & Motivations:**
> - Youth wellbeing is stated Council priority (2024 Strategic Plan)
> - Economic development through workforce preparation
> - Cultural preservation and language revitalization
> - Accountability for grant funding and program outcomes
>
> **Potential Concerns:**
> - Sustainability after initial funding ends
> - Capacity burden on existing staff
> - Past program failures creating skepticism
> - Ensuring equitable access across districts
>
> **Engagement Strategy:**
> - Formal quarterly briefings at Council meetings
> - Monthly written updates to Council liaison
> - Invitation to participate in program events
> - Early involvement in any scope or budget changes
>
> **Key Messages:**
> - Program designed with community input (reference assessment)
> - Built-in sustainability plan from Day 1
> - Aligned with Council's stated priorities
> - Clear accountability and reporting structure
>
> **Cultural Protocol:**
> - Request formal agenda item through established process
> - Provide materials 2 weeks in advance
> - Begin with acknowledgment of Council authority
> - Be prepared for extended deliberation timeline

**BAD (Junior-level):**
> **Tribal Council:** Important stakeholder. Need to get their approval. Should meet with them regularly.

### SENIOR-LEVEL QUALITY MARKERS

Your document must demonstrate:

✓ **Systematic Analysis:** Power/interest grid completed for all groups
✓ **Cultural Intelligence:** Respects protocols and informal networks
✓ **Proactive:** Anticipates concerns before they become issues
✓ **Actionable:** Specific engagement strategies, not just descriptions
✓ **Balanced:** Considers both supporters and potential resisters
✓ **Realistic:** Acknowledges constraints on engagement capacity
✓ **Connected:** References communication in SOPs, risks in Risk document

### STRICT CONSTRAINTS

1. **DO NOT name:** Specific individuals (use roles/positions)
2. **DO NOT assume:** Relationships or dynamics not evidenced in research
3. **DO respect:** Tribal sovereignty and community self-determination
4. **DO acknowledge:** Historical context that affects trust
5. **DO include:** Both formal authority AND informal influence
6. **MUST have:** Power/interest grid or equivalent matrix

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Stakeholder Notes

Include:
- At least 12 major sections (H2 headings)
- Power/interest grid (table or ASCII)
- Minimum 6-8 detailed stakeholder profiles
- Engagement strategy matrix
- Minimum 2000 words
- Cross-references to at least 3 other documents

Write the complete Stakeholder Notes document now.
"""

    def _build_scope_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Scope and Boundaries document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Project Manager with 15+ years of experience** defining project scope for nonprofit, tribal, and public sector organizations.

You are known for scope documents that:
- Clearly distinguish what IS and IS NOT included
- Prevent scope creep through explicit boundaries
- Define acceptance criteria for deliverables
- Align scope with resources, timeline, and goals
- Use professional in-scope/out-of-scope format

## DOCUMENT TO WRITE
Scope and Boundaries

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

## YOUR TASK

Write a comprehensive Scope and Boundaries document.

### REQUIRED STRUCTURE

1. **Scope Overview**
   - Project purpose in 2-3 sentences
   - How scope was determined
   - Alignment with organizational priorities

2. **In-Scope (Included)**
   - Major deliverables with descriptions
   - Services/activities to be performed
   - Geographic boundaries
   - Time boundaries
   - Target populations included

3. **Out-of-Scope (Excluded)**
   - Explicitly excluded activities (with rationale)
   - Future phases not in current scope
   - Related work handled elsewhere
   - Why exclusions were made

4. **Deliverables**
   For each deliverable:
   - Name and description
   - Acceptance criteria
   - Quality standards
   - Responsible party
   - Due date (reference Timeline)

5. **Constraints**
   - Budget constraints (reference Budget)
   - Timeline constraints (reference Timeline)
   - Resource constraints
   - Regulatory/compliance constraints
   - Technical constraints

6. **Assumptions**
   - Key assumptions underlying scope
   - What must remain true for scope to hold
   - Reference to Risks document

7. **Scope Change Management**
   - Process for requesting changes
   - Who approves scope changes
   - Impact assessment requirements
   - Documentation requirements

8. **Success Criteria**
   - How we know scope is complete
   - Acceptance process
   - Sign-off requirements

### IN-SCOPE / OUT-OF-SCOPE TABLE EXAMPLE

| Category | In-Scope | Out-of-Scope |
|----------|----------|--------------|
| Services | Mentorship matching, training | Mental health counseling (referred out) |
| Geography | Three reservation communities | Urban populations, off-reservation |
| Population | Youth ages 14-21 | Adults, children under 14 |
| Timeline | 24-month implementation | Long-term sustainability (future phase) |

### SENIOR-LEVEL QUALITY MARKERS

✓ **Explicit Boundaries:** Crystal clear what's in and out
✓ **Rationale:** Explains WHY exclusions were made
✓ **Measurable:** Deliverables have acceptance criteria
✓ **Change-Ready:** Process for handling scope changes
✓ **Integrated:** References Budget, Timeline, Goals documents

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Scope and Boundaries

Include:
- At least 8 major sections
- In-scope/out-of-scope table
- Deliverables with acceptance criteria
- Minimum 1500 words
- Cross-references to at least 3 other documents

Write the complete Scope and Boundaries document now.
"""

    def _build_process_workflow_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Process Workflow document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Operations Consultant with 15+ years of experience** designing workflows for nonprofit, tribal, and public sector organizations.

You are known for process documentation that:
- Uses industry-standard process mapping conventions
- Shows clear inputs, activities, outputs, and decision points
- Identifies handoffs between roles/teams
- Includes swim lanes for complex multi-party processes
- Balances detail with readability

## DOCUMENT TO WRITE
Process Workflow

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

## YOUR TASK

Write a comprehensive Process Workflow document.

### REQUIRED STRUCTURE

1. **Process Overview**
   - Purpose of this document
   - Major processes covered
   - How processes connect to project goals

2. **Process Map Legend**
   - Symbols used (start/end, activities, decisions, connectors)
   - How to read the diagrams

3. **Core Project Processes**
   For each major process:
   - Process name and ID
   - Process owner (role)
   - Trigger (what starts it)
   - Inputs required
   - Steps/activities (numbered)
   - Decision points (with criteria)
   - Outputs produced
   - Handoffs to other processes

4. **Process Flow Diagrams**
   ASCII/text-based process maps:
   ```
   [Start] → [Activity 1] → <Decision?> → Yes → [Activity 2] → [End]
                               ↓
                              No → [Alternative] → [End]
   ```

5. **Swim Lane Diagrams**
   For multi-party processes showing who does what

6. **Process Dependencies**
   - Which processes must complete before others
   - Parallel vs. sequential processes
   - Integration points

7. **Quality Checkpoints**
   - Where quality is verified
   - Criteria for proceeding

8. **Exception Handling**
   - What happens when process fails
   - Escalation paths
   - Recovery procedures

9. **Process Metrics**
   - How process performance is measured
   - Target cycle times
   - Quality indicators

10. **Continuous Improvement**
    - How processes will be reviewed
    - Feedback mechanisms
    - Update procedures

### ASCII PROCESS DIAGRAM EXAMPLE

```
PARTICIPANT INTAKE PROCESS
==========================

[START: Application Received]
         │
         ▼
┌─────────────────────────┐
│ 1. Review Application   │ ← Coordinator
│    (2 business days)    │
└───────────┬─────────────┘
            │
            ▼
       <Complete?>
        /      \\
      Yes       No
       │         │
       ▼         ▼
┌──────────┐  ┌──────────────┐
│ 2. Eli-  │  │ Request      │
│ gibility │  │ Missing Info │
│ Check    │  └──────┬───────┘
└────┬─────┘         │
     │               ▼
     │          [WAIT: 5 days]
     │               │
     ▼               ▼
<Eligible?>     <Received?>
  /    \\         /     \\
Yes     No      Yes     No
 │       │       │       │
 ▼       ▼       │       ▼
[Accept] [Deny]  │    [Close]
 │       │       │
 └───────┴───────┘
         │
         ▼
    [END: Decision Made]
```

### SENIOR-LEVEL QUALITY MARKERS

✓ **Visual Clarity:** Process diagrams anyone can follow
✓ **Complete:** All major processes documented
✓ **Measurable:** Cycle times and quality criteria included
✓ **Exception-Ready:** Handles failures gracefully
✓ **Role-Clear:** Who does what is explicit
✓ **Connected:** References SOPs for detailed procedures

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Process Workflow

Include:
- At least 10 major sections
- Minimum 3-5 ASCII process diagrams
- Decision points with criteria
- Minimum 1800 words
- Cross-references to SOPs and Timeline documents

Write the complete Process Workflow document now.
"""

    def _build_context_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Context and Background document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Research Analyst with 15+ years of experience** writing environmental scans and context analyses for nonprofit, tribal, and public sector organizations.

You are known for context documents that:
- Synthesize complex environments into clear narratives
- Use PESTLE or similar frameworks systematically
- Ground projects in evidence and data
- Acknowledge what is known AND unknown
- Connect context to project decisions

## DOCUMENT TO WRITE
Context and Background

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

## YOUR TASK

Write a comprehensive Context and Background document.

### REQUIRED STRUCTURE

1. **Executive Context Summary**
   - Why this project now
   - Key environmental factors
   - What the research tells us

2. **Organizational Context**
   - Lead organization background
   - Relevant history and experience
   - Current capacity and strengths
   - Previous related work

3. **Community/Geographic Context**
   - Demographics of target area
   - Geographic considerations
   - Cultural context (especially for tribal projects)
   - Historical context affecting the work

4. **Problem/Opportunity Analysis**
   - Current state description
   - Root causes identified
   - Evidence of need (data, research)
   - Gap analysis

5. **Environmental Scan (PESTLE)**
   - **P**olitical factors
   - **E**conomic factors
   - **S**ocial factors
   - **T**echnological factors
   - **L**egal/regulatory factors
   - **E**nvironmental factors

6. **Landscape Analysis**
   - Similar programs/initiatives
   - What's worked elsewhere
   - Lessons learned from others
   - How this project is different

7. **Stakeholder Landscape**
   - Key players in this space
   - Potential partners
   - Reference to Stakeholder Notes

8. **Funding & Resource Landscape**
   - Funding environment
   - Available resources
   - Competition for resources

9. **Trends & Future Outlook**
   - Relevant trends affecting the project
   - Anticipated changes
   - Opportunities and threats

10. **Implications for Project Design**
    - How context shapes our approach
    - Key decisions informed by research
    - Remaining questions to investigate

### ENVIRONMENTAL SCAN TABLE EXAMPLE

| Factor | Current State | Implication for Project |
|--------|--------------|------------------------|
| Political | New tribal leadership supportive | Window of opportunity |
| Economic | High unemployment (18%) | Strong need, competition for jobs |
| Social | Youth outmigration trend | Urgency to engage youth |
| Technical | Limited broadband | In-person focus required |
| Legal | ICWA compliance needed | Built into all processes |
| Environmental | Rural, spread-out communities | Transportation consideration |

### SENIOR-LEVEL QUALITY MARKERS

✓ **Evidence-Based:** Claims supported by research findings
✓ **Systematic:** Uses recognized frameworks (PESTLE)
✓ **Balanced:** Acknowledges uncertainties and limitations
✓ **Actionable:** Context connects to project decisions
✓ **Current:** Uses recent/relevant information
✓ **Respectful:** Appropriate framing for community context

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Context and Background

Include:
- At least 10 major sections
- Environmental scan table
- Evidence from research findings
- Minimum 1800 words
- Cross-references to Stakeholder Notes and Goals

Write the complete Context and Background document now.
"""

    def _build_task_backlog_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Task Backlog document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Agile Coach with 15+ years of experience** organizing work for nonprofit, tribal, and public sector projects.

You are known for backlogs that:
- Use clear prioritization frameworks (MoSCoW, Value/Effort)
- Break work into actionable, estimable tasks
- Connect tasks to goals and deliverables
- Balance immediate needs with strategic priorities
- Adapt agile concepts for non-software contexts

## DOCUMENT TO WRITE
Task Backlog

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

## YOUR TASK

Write a comprehensive Task Backlog document.

### REQUIRED STRUCTURE

1. **Backlog Overview**
   - Purpose and how to use this document
   - Prioritization methodology (MoSCoW or Value/Effort)
   - How backlog connects to Timeline and Goals
   - Update and refinement cadence

2. **Backlog Structure**
   - Epics (large bodies of work)
   - Features/Initiatives (medium chunks)
   - Tasks/Stories (actionable items)
   - How they relate

3. **Prioritization Framework**
   - Priority levels and definitions
   - Criteria for prioritization
   - Who makes priority decisions
   - How to handle competing priorities

4. **Backlog by Phase**
   Organized by project phase (from Timeline):
   - Phase 1 tasks
   - Phase 2 tasks
   - Phase 3 tasks
   - etc.

5. **Initial Backlog Table**

   | ID | Task | Epic | Priority | Effort | Phase | Owner | Status |
   |----|------|------|----------|--------|-------|-------|--------|
   | T-001 | Example task | Planning | Must Have | M | 1 | Coordinator | Not Started |

6. **Epic Descriptions**
   For each major epic:
   - Epic name and ID
   - Goal/purpose
   - Key tasks within epic
   - Success criteria
   - Dependencies

7. **Sprint/Iteration Planning**
   - Recommended iteration length
   - Capacity planning approach
   - How to select tasks for iteration
   - Definition of Done

8. **Backlog Maintenance**
   - Refinement schedule
   - Who participates
   - How items are added/removed
   - Tracking approach

9. **Dependencies & Blockers**
   - External dependencies
   - Internal dependencies
   - How to flag and resolve blockers

10. **Completion Tracking**
    - How progress is measured
    - Burndown/burnup approach (if applicable)
    - Reporting frequency

### MoSCoW PRIORITIZATION EXAMPLE

- **Must Have:** Critical for phase success, non-negotiable
- **Should Have:** Important but not critical, can adjust timing
- **Could Have:** Desirable if time/resources permit
- **Won't Have (this phase):** Explicitly deferred to future

### EFFORT ESTIMATION

- **XS:** < 2 hours
- **S:** 2-4 hours
- **M:** 1-3 days
- **L:** 1-2 weeks
- **XL:** > 2 weeks (should be broken down)

### SENIOR-LEVEL QUALITY MARKERS

✓ **Actionable:** Tasks are concrete and doable
✓ **Prioritized:** Clear ranking with rationale
✓ **Estimated:** Effort levels assigned
✓ **Connected:** Links to Goals, Timeline, Scope
✓ **Maintainable:** Clear process for updates
✓ **Appropriate:** Adapts agile for nonprofit context

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Task Backlog

Include:
- At least 10 major sections
- Initial backlog table with 20+ tasks
- Epic descriptions
- Prioritization framework
- Minimum 1500 words
- Cross-references to Timeline and Goals

Write the complete Task Backlog document now.
"""

    def _build_meeting_notes_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Meeting Notes template document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Administrative Professional with 15+ years of experience** documenting meetings for nonprofit, tribal, and public sector organizations.

You are known for meeting documentation that:
- Captures decisions and action items clearly
- Uses consistent, professional templates
- Respects cultural protocols in formal settings
- Enables accountability through clear assignments
- Creates an audit trail for governance

## DOCUMENT TO WRITE
Meeting Notes (Template and Initial Entries)

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

## YOUR TASK

Write a Meeting Notes document with templates and initial meeting entries.

### REQUIRED STRUCTURE

1. **Meeting Documentation Overview**
   - Purpose of meeting documentation
   - Types of meetings for this project
   - Documentation standards
   - Distribution and storage

2. **Meeting Template**
   Provide a reusable template:
   ```
   ## [Meeting Type] - [Date]

   **Date:**
   **Time:**
   **Location/Platform:**
   **Facilitator:**
   **Note-taker:**

   ### Attendees
   - [Name/Role] - Present/Absent

   ### Agenda
   1.
   2.

   ### Discussion Notes

   ### Decisions Made
   - Decision 1:
   - Decision 2:

   ### Action Items
   | Item | Owner | Due Date | Status |
   |------|-------|----------|--------|

   ### Next Meeting
   - Date:
   - Agenda items:

   ### Attachments/References
   ```

3. **Meeting Types**
   For this project:
   - Team meetings (frequency, typical agenda)
   - Stakeholder meetings (format, protocols)
   - Advisory/governance meetings (formal requirements)
   - Working sessions (documentation needs)

4. **Pre-Meeting Checklist**
   - Agenda distribution timeline
   - Materials to prepare
   - Room/platform setup
   - Attendee confirmation

5. **Meeting Facilitation Guidelines**
   - Opening protocols (especially for formal/tribal settings)
   - Time management
   - Participation encouragement
   - Conflict navigation

6. **Action Item Tracking**
   - How action items are assigned
   - Follow-up process
   - Escalation for overdue items
   - Integration with Task Backlog

7. **Decision Documentation**
   - What requires documentation
   - Decision authority levels
   - How to document dissent
   - Sign-off requirements

8. **Sample Meeting Entries**
   Include 2-3 sample meeting notes:
   - Project kickoff meeting
   - First team meeting
   - Stakeholder check-in

9. **Cultural Considerations**
   - Opening/closing protocols
   - Elder/leadership acknowledgment
   - Consensus vs. voting
   - Language considerations

10. **Meeting Archive**
    - Filing system
    - Naming conventions
    - Retention policy
    - Access permissions

### ACTION ITEM TABLE FORMAT

| ID | Action Item | Owner | Due | Priority | Status | Notes |
|----|-------------|-------|-----|----------|--------|-------|
| A-001 | Draft community outreach plan | Coordinator | Week 2 | High | In Progress | |

### SENIOR-LEVEL QUALITY MARKERS

✓ **Consistent:** Same format every time
✓ **Actionable:** Clear owners and due dates
✓ **Accessible:** Easy to find and reference
✓ **Appropriate:** Respects cultural protocols
✓ **Complete:** Captures decisions, not just discussion
✓ **Accountable:** Enables follow-up

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Meeting Notes

Include:
- At least 10 major sections
- Reusable meeting template
- 2-3 sample meeting entries
- Action item tracking format
- Minimum 1500 words
- Cross-references to SOPs and Timeline

Write the complete Meeting Notes document now.
"""

    def _build_status_updates_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Status Updates template document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Program Manager with 15+ years of experience** writing status reports for nonprofit, tribal, and public sector funders and stakeholders.

You are known for status updates that:
- Tell the story of progress clearly
- Use RAG (Red/Amber/Green) status effectively
- Balance brevity with completeness
- Anticipate stakeholder questions
- Maintain accountability without blame

## DOCUMENT TO WRITE
Status Updates (Template and Initial Entry)

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

## YOUR TASK

Write a Status Updates document with templates and initial entry.

### REQUIRED STRUCTURE

1. **Status Reporting Overview**
   - Purpose and audience
   - Reporting cadence (weekly, monthly, quarterly)
   - Distribution list by report type
   - Escalation thresholds

2. **Status Report Template**
   Provide reusable template:
   ```
   # Project Status Update - [Period]

   **Report Date:**
   **Reporting Period:**
   **Prepared By:**
   **Overall Status:** 🟢 Green / 🟡 Amber / 🔴 Red

   ## Executive Summary
   [2-3 sentences on overall status]

   ## Status Dashboard
   | Area | Status | Trend | Notes |
   |------|--------|-------|-------|
   | Schedule | 🟢 | → | On track |
   | Budget | 🟡 | ↓ | Minor variance |
   | Scope | 🟢 | → | No changes |
   | Risks | 🟢 | ↑ | Improving |
   | Quality | 🟢 | → | Meeting standards |

   ## Progress This Period
   - Accomplishment 1
   - Accomplishment 2

   ## Upcoming Activities
   - Next week:
   - Next month:

   ## Issues & Blockers
   | Issue | Impact | Action | Owner | Target |
   |-------|--------|--------|-------|--------|

   ## Risks Update
   [Changes to risk status]

   ## Budget Status
   - Spent to date:
   - Remaining:
   - Variance:

   ## Decisions Needed
   [If any]

   ## Metrics Snapshot
   [Key KPIs from Goals document]
   ```

3. **RAG Status Definitions**
   - 🟢 **Green:** On track, no issues
   - 🟡 **Amber:** At risk, mitigation underway
   - 🔴 **Red:** Off track, escalation needed
   - Define thresholds for each

4. **Reporting Schedule**
   - Weekly updates (who, what, when)
   - Monthly reports (format, audience)
   - Quarterly reports (comprehensive)
   - Ad-hoc escalations

5. **Metrics Dashboard**
   Key metrics to track regularly:
   - Progress metrics (from Goals)
   - Budget metrics
   - Timeline metrics
   - Quality metrics

6. **Escalation Criteria**
   - What triggers escalation
   - Who is notified
   - Response expectations
   - Documentation requirements

7. **Sample Status Update**
   Complete example for Month 1 or Week 1

8. **Stakeholder-Specific Formats**
   - Internal team updates
   - Leadership briefings
   - Funder reports
   - Community updates

9. **Status Meeting Agenda**
   If status meetings accompany reports:
   - Standing agenda items
   - Time allocations
   - Participant expectations

10. **Historical Tracking**
    - How to maintain status history
    - Trend analysis
    - Lessons learned capture

### STATUS DASHBOARD EXAMPLE

| Category | Status | Last Period | Trend | Commentary |
|----------|--------|-------------|-------|------------|
| Overall | 🟢 | 🟢 | → | Solid start to project |
| Schedule | 🟢 | 🟢 | → | Phase 1 on track |
| Budget | 🟢 | 🟢 | → | 8% spent, aligned to plan |
| Scope | 🟢 | 🟢 | → | No change requests |
| Resources | 🟡 | 🟢 | ↓ | Coordinator position open |
| Risks | 🟢 | 🟡 | ↑ | Key risk mitigated |

### SENIOR-LEVEL QUALITY MARKERS

✓ **At-a-Glance:** Status clear in 30 seconds
✓ **Honest:** Doesn't hide problems
✓ **Action-Oriented:** Issues have owners and plans
✓ **Consistent:** Same format each period
✓ **Forward-Looking:** Anticipates next period
✓ **Metrics-Driven:** Quantitative where possible

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Status Updates

Include:
- At least 10 major sections
- Reusable status report template
- RAG definitions and thresholds
- Sample completed status update
- Minimum 1500 words
- Cross-references to Goals, Budget, Timeline, Risks

Write the complete Status Updates document now.
"""

    def _build_readme_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for README/Project Overview document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Technical Writer with 15+ years of experience** creating project documentation for diverse audiences.

You are known for README documents that:
- Orient new readers quickly
- Serve as the "front door" to all project documentation
- Balance high-level overview with navigation to details
- Work for multiple audiences (team, stakeholders, external)
- Stay current as the single source of truth

## DOCUMENT TO WRITE
README (Project Overview)

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

## YOUR TASK

Write a comprehensive README that serves as the project's central navigation document.

### REQUIRED STRUCTURE

1. **Project Title & Tagline**
   - Clear, memorable title
   - One-line description of purpose

2. **Quick Overview**
   - What this project is (2-3 sentences)
   - Why it matters
   - Who it serves
   - Current status

3. **At a Glance**
   Quick-reference table:
   | | |
   |---|---|
   | **Duration** | X months |
   | **Budget** | $X - $Y |
   | **Lead Organization** | Name |
   | **Key Contact** | Role |
   | **Status** | Phase X |

4. **The Problem We're Solving**
   - Brief problem statement
   - Who is affected
   - Why action is needed now

5. **Our Approach**
   - Solution overview
   - Key strategies
   - What makes this approach effective

6. **Key Deliverables**
   - Major outputs
   - Expected outcomes
   - Timeline highlights

7. **Document Navigation**
   Guide to the documentation set:

   | Document | Purpose | Audience |
   |----------|---------|----------|
   | Project Brief | Executive summary | Leadership |
   | Goals | Success metrics | All |
   | Timeline | Schedule | Team |
   | etc. | | |

8. **Project Team**
   - Key roles (not names)
   - Responsibilities
   - Contact information

9. **How to Get Involved**
   - For team members
   - For stakeholders
   - For partners

10. **Quick Links**
    - Key documents
    - Important contacts
    - External resources

11. **Version History**
    - Document updates
    - Major project milestones

### DOCUMENT NAVIGATION TABLE EXAMPLE

| Folder | Document | Description |
|--------|----------|-------------|
| 00-Overview | README.md | This document - start here |
| 00-Overview | Project-Brief.md | Executive summary for decision-makers |
| 00-Overview | Glossary.md | Key terms and definitions |
| 10-Discovery | Context-and-Background.md | Research and environmental scan |
| 10-Discovery | Stakeholder-Notes.md | Stakeholder analysis and engagement |
| 20-Planning | Goals-and-Success-Criteria.md | SMART objectives and KPIs |
| 20-Planning | Scope-and-Boundaries.md | What's in and out of scope |
| ... | ... | ... |

### SENIOR-LEVEL QUALITY MARKERS

✓ **Welcoming:** Orients new readers immediately
✓ **Navigable:** Clear paths to find information
✓ **Current:** Reflects actual project status
✓ **Audience-Aware:** Works for multiple readers
✓ **Concise:** Overview without overwhelming detail
✓ **Maintained:** Version history shows updates

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # {project.name}

Include:
- At least 11 major sections
- At-a-glance summary table
- Document navigation table
- Version history section
- Minimum 1200 words
- Cross-references to ALL other documents

Write the complete README document now.
"""

    def _build_glossary_prompt(
        self,
        project: ProjectInput,
        research_results: list[AgentResult],
        previous_docs: list[Document],
    ) -> str:
        """Build specialized prompt for Glossary document."""
        research_summary = self._compile_research_summary(research_results)
        frameworks = self._extract_frameworks_research(research_results)
        prev_context = self._get_previous_context(previous_docs)

        return f"""You are a **Senior Documentation Specialist with 15+ years of experience** creating reference materials for diverse audiences.

You are known for glossaries that:
- Define terms clearly without jargon
- Include context-specific meanings
- Respect cultural and community terminology
- Support readers of varying expertise levels
- Stay current as projects evolve

## DOCUMENT TO WRITE
Glossary

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

## YOUR TASK

Write a comprehensive Glossary for this project.

### REQUIRED STRUCTURE

1. **How to Use This Glossary**
   - Purpose and scope
   - How terms are organized
   - How to suggest additions
   - Related resources

2. **Project-Specific Terms**
   Terms unique to this project:
   - Project name meanings
   - Internal terminology
   - Program-specific language

3. **Domain/Industry Terms**
   Relevant professional terminology:
   - Field-specific terms
   - Regulatory/compliance terms
   - Best practice terminology

4. **Cultural & Community Terms**
   Especially for tribal/community projects:
   - Cultural terminology
   - Community-specific language
   - Respectful usage guidance
   - Pronunciation guides (if applicable)

5. **Acronyms & Abbreviations**
   | Acronym | Full Term | Definition |
   |---------|-----------|------------|
   | TBD | To Be Determined | |

6. **Technical Terms**
   Technology and systems terminology

7. **Organizational Terms**
   - Organization-specific terminology
   - Role titles
   - Governance terms

8. **Main Glossary (A-Z)**
   Alphabetical listing:

   ### A

   **Term:** Definition. Context for how it's used in this project. *See also: Related Term*

   ### B
   ...

9. **Terms by Category**
   Alternative organization for quick reference:
   - Planning terms
   - Operations terms
   - Financial terms
   - etc.

10. **Version & Updates**
    - How glossary is maintained
    - Change log
    - Suggestion process

### GLOSSARY ENTRY FORMAT

**Term Name** (pronunciation if needed)
: Primary definition in plain language.
: *Context:* How this term is specifically used in this project.
: *Example:* "The [term] was used when..."
: *See also:* Related Term 1, Related Term 2

### EXAMPLE ENTRIES

**Cohort**
: A group of participants who begin and progress through a program together.
: *Context:* In this project, each cohort consists of 25 youth who start the mentorship program at the same time and meet together for group activities.
: *See also:* Participant, Mentor

**SMART Goals**
: Goals that are Specific, Measurable, Achievable, Relevant, and Time-bound.
: *Context:* All project objectives in the Goals document follow SMART criteria to ensure clear accountability.
: *See also:* KPI, Success Criteria

**Elder** (cultural term)
: A respected community member recognized for wisdom, experience, and cultural knowledge.
: *Context:* This project includes an Elder Advisory Council that provides cultural guidance and helps ensure programming is culturally appropriate.
: *Note:* The term carries significant cultural weight and should be used respectfully.
: *See also:* Advisory Council, Cultural Protocol

### SENIOR-LEVEL QUALITY MARKERS

✓ **Accessible:** Definitions anyone can understand
✓ **Contextualized:** Shows how terms apply to this project
✓ **Respectful:** Cultural terms handled appropriately
✓ **Complete:** Covers all terminology in project docs
✓ **Organized:** Easy to find terms quickly
✓ **Living:** Process for updates

{WRITING_STYLE_RULES}

### OUTPUT FORMAT

Markdown document starting with: # Glossary

Include:
- At least 10 major sections
- Minimum 40-50 glossary entries
- Acronym table
- Multiple organization methods (A-Z and by category)
- Minimum 1500 words
- Terms drawn from all other project documents

Write the complete Glossary document now.
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
