"""Agent Discovery Service - Phase 0: Local keyword parsing and agent generation."""

import re
from dataclasses import dataclass

from wowasi_ya.models.agent import AgentDefinition, DomainMatch
from wowasi_ya.models.project import ProjectInput


@dataclass
class DomainKeywords:
    """Domain with associated keywords for matching."""

    domain: str
    keywords: list[str]
    stakeholders: list[str]
    agent_templates: list[dict[str, str]]


# Domain keyword mappings based on claude_code_agent_strategy.md
DOMAIN_MAPPINGS: list[DomainKeywords] = [
    DomainKeywords(
        domain="healthcare",
        keywords=[
            "health",
            "medical",
            "clinic",
            "hospital",
            "patient",
            "hipaa",
            "phi",
            "treatment",
            "diagnosis",
            "wellness",
            "telehealth",
            "ihs",
            "indian health service",
        ],
        stakeholders=["patients", "healthcare providers", "administrators", "regulators"],
        agent_templates=[
            {
                "role": "Healthcare Compliance Researcher",
                "focus": "HIPAA, IHS regulations, tribal health sovereignty",
            },
            {
                "role": "Healthcare Best Practices Analyst",
                "focus": "Clinical workflows, patient safety, quality metrics",
            },
        ],
    ),
    DomainKeywords(
        domain="education",
        keywords=[
            "school",
            "education",
            "student",
            "teacher",
            "curriculum",
            "learning",
            "training",
            "workshop",
            "tribal college",
            "bie",
            "ferpa",
        ],
        stakeholders=["students", "educators", "administrators", "parents", "tribal education dept"],
        agent_templates=[
            {
                "role": "Education Policy Researcher",
                "focus": "FERPA, BIE requirements, tribal education sovereignty",
            },
            {
                "role": "Curriculum Development Analyst",
                "focus": "Best practices, cultural integration, assessment methods",
            },
        ],
    ),
    DomainKeywords(
        domain="tribal_governance",
        keywords=[
            "tribe",
            "tribal",
            "sovereignty",
            "nation",
            "council",
            "reservation",
            "treaty",
            "self-governance",
            "self-determination",
            "bia",
        ],
        stakeholders=["tribal council", "tribal members", "federal agencies", "state agencies"],
        agent_templates=[
            {
                "role": "Tribal Policy Researcher",
                "focus": "Federal Indian law, sovereignty principles, treaty rights",
            },
            {
                "role": "Governance Best Practices Analyst",
                "focus": "Self-governance models, administrative procedures",
            },
        ],
    ),
    DomainKeywords(
        domain="grants_funding",
        keywords=[
            "grant",
            "funding",
            "budget",
            "proposal",
            "funder",
            "foundation",
            "federal grant",
            "state grant",
            "nonprofit",
        ],
        stakeholders=["funders", "grant administrators", "program staff", "finance team"],
        agent_templates=[
            {
                "role": "Grants Researcher",
                "focus": "Funding opportunities, eligibility requirements, deadlines",
            },
            {
                "role": "Proposal Best Practices Analyst",
                "focus": "Successful proposal strategies, compliance requirements",
            },
        ],
    ),
    DomainKeywords(
        domain="technology",
        keywords=[
            "software",
            "app",
            "application",
            "system",
            "database",
            "api",
            "cloud",
            "infrastructure",
            "cybersecurity",
            "data",
        ],
        stakeholders=["developers", "IT staff", "end users", "security team"],
        agent_templates=[
            {
                "role": "Technology Standards Researcher",
                "focus": "Industry standards, security requirements, compliance",
            },
            {
                "role": "Technical Architecture Analyst",
                "focus": "Best practices, scalability, maintainability",
            },
        ],
    ),
    DomainKeywords(
        domain="rural_community",
        keywords=[
            "rural",
            "remote",
            "community",
            "village",
            "broadband",
            "connectivity",
            "infrastructure",
            "transportation",
        ],
        stakeholders=["community members", "local government", "service providers"],
        agent_templates=[
            {
                "role": "Rural Development Researcher",
                "focus": "USDA programs, connectivity initiatives, infrastructure grants",
            },
            {
                "role": "Community Needs Analyst",
                "focus": "Best practices for rural service delivery",
            },
        ],
    ),
]


class AgentDiscoveryService:
    """Service for discovering and generating research agents based on project input.

    This is Phase 0 - runs entirely locally without API calls.
    """

    def __init__(self) -> None:
        """Initialize the agent discovery service."""
        self.domain_mappings = DOMAIN_MAPPINGS

    def analyze_project(self, project: ProjectInput) -> list[DomainMatch]:
        """Analyze project description and identify relevant domains.

        Args:
            project: Project input with name and description.

        Returns:
            List of matched domains with confidence scores.
        """
        text = f"{project.name} {project.description} {project.additional_context or ''}"
        text_lower = text.lower()

        matches: list[DomainMatch] = []

        for domain_def in self.domain_mappings:
            matched_keywords: list[str] = []

            for keyword in domain_def.keywords:
                # Use word boundary matching for more accurate results
                pattern = rf"\b{re.escape(keyword)}\b"
                if re.search(pattern, text_lower):
                    matched_keywords.append(keyword)

            if matched_keywords:
                # Calculate confidence based on keyword matches
                confidence = min(len(matched_keywords) / 3.0, 1.0)
                matches.append(
                    DomainMatch(
                        domain=domain_def.domain,
                        keywords=matched_keywords,
                        confidence=confidence,
                        stakeholders=domain_def.stakeholders,
                    )
                )

        # Sort by confidence descending
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    def generate_agents(
        self,
        project: ProjectInput,
        domain_matches: list[DomainMatch],
    ) -> list[AgentDefinition]:
        """Generate research agent definitions based on domain matches.

        Args:
            project: Project input.
            domain_matches: Matched domains from analyze_project.

        Returns:
            List of agent definitions for the research phase.
        """
        agents: list[AgentDefinition] = []
        # Start at 2 since frameworks agent has priority 1
        agent_counter = 2

        for match in domain_matches:
            domain_def = next(
                (d for d in self.domain_mappings if d.domain == match.domain),
                None,
            )
            if not domain_def:
                continue

            for template in domain_def.agent_templates:
                agent = AgentDefinition(
                    id=f"agent_{agent_counter:03d}",
                    name=f"{match.domain.replace('_', ' ').title()} - {template['role']}",
                    role=template["role"],
                    domains=[match.domain],
                    research_questions=self._generate_research_questions(
                        project, match, template
                    ),
                    search_queries=self._generate_search_queries(project, match, template),
                    priority=agent_counter,
                )
                agents.append(agent)
                agent_counter += 1

        return agents

    def _generate_research_questions(
        self,
        project: ProjectInput,
        match: DomainMatch,
        template: dict[str, str],
    ) -> list[str]:
        """Generate research questions for an agent."""
        questions = [
            f"What are the key regulations and compliance requirements for {match.domain.replace('_', ' ')} projects?",
            f"What are best practices for {template['focus']}?",
            f"What stakeholder considerations apply to {', '.join(match.stakeholders[:2])}?",
            f"What common challenges and solutions exist for {match.domain.replace('_', ' ')} initiatives?",
        ]
        return questions

    def _generate_search_queries(
        self,
        project: ProjectInput,
        match: DomainMatch,
        template: dict[str, str],
    ) -> list[str]:
        """Generate web search queries for an agent."""
        queries = [
            f"{match.domain.replace('_', ' ')} {template['focus']} best practices 2024",
            f"{match.domain.replace('_', ' ')} compliance requirements",
            f"{project.name} {match.domain.replace('_', ' ')} regulations",
        ]
        return queries

    def _create_documentation_framework_agent(self, project: ProjectInput) -> AgentDefinition:
        """Create universal agent that gathers professional documentation frameworks.

        This agent runs for EVERY project to provide Llama with professional
        scaffolding (frameworks, templates, examples) it needs since it lacks web access.

        Args:
            project: Project input.

        Returns:
            Documentation frameworks agent definition.
        """
        return AgentDefinition(
            id="agent_000_frameworks",
            name="Documentation Frameworks & Professional Standards",
            role="Senior Documentation Architect with 15+ years in nonprofit, tribal, and public sector",
            domains=["documentation", "professional_standards", "project_management"],
            research_questions=[
                "What are the industry-standard frameworks for professional project documentation? (e.g., SMART goals, RACI charts, risk matrices, Gantt conventions)",
                "What are best practices and formatting conventions for executive-level project documentation in nonprofit/public sector?",
                "What are concrete examples of well-written budget narratives, risk assessments, and SOPs for similar organizations?",
                "What are the key differences between junior-level and senior-level project documentation in terms of depth, specificity, and strategic thinking?",
                "What professional templates and structures are commonly used for project briefs, stakeholder notes, and status updates?",
            ],
            search_queries=[
                "nonprofit project documentation best practices 2024",
                "professional project management frameworks SMART goals RACI",
                "executive-level budget narrative examples public sector",
                "risk assessment matrix templates nonprofit organizations",
                "standard operating procedures SOP templates government agencies",
                "project timeline Gantt chart best practices",
                "stakeholder analysis frameworks project management",
                "senior project manager documentation vs junior",
            ],
            priority=1,  # Highest priority - runs first
        )

    def discover(self, project: ProjectInput) -> tuple[list[DomainMatch], list[AgentDefinition]]:
        """Run full discovery process.

        Args:
            project: Project input.

        Returns:
            Tuple of (domain_matches, agent_definitions).
        """
        matches = self.analyze_project(project)
        agents = self.generate_agents(project, matches)

        # ALWAYS add the documentation frameworks agent as first priority
        framework_agent = self._create_documentation_framework_agent(project)
        agents.insert(0, framework_agent)

        return matches, agents
