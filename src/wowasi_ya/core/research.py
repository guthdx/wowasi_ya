"""Research Engine - Phase 1: Claude API research with web search.

PROVIDER: Claude API (Anthropic) - FIXED
REASON: Web search capability required for research agents
FUTURE: To swap providers, implement BaseLLMClient in llm_client.py with web search support

Architecture Note:
- Research (this file): Always uses Claude for web search
- Generation (generator.py): Uses configurable provider (Llama/Claude)

To add a new research provider:
1. Ensure provider supports web search
2. Create client in llm_client.py implementing BaseLLMClient
3. Update get_research_client() factory
4. Update this file to use the factory instead of direct Anthropic SDK
"""

import asyncio
import logging
from typing import Any

from pydantic import BaseModel, Field

from wowasi_ya.config import Settings, get_settings
from wowasi_ya.models.agent import AgentDefinition, AgentResult

logger = logging.getLogger(__name__)


class ResearchConfig(BaseModel):
    """Configuration for research operations."""

    max_concurrent_agents: int = Field(default=1, ge=1, le=10)  # Reduced to 1 to avoid Claude rate limits
    timeout_seconds: int = Field(default=120, ge=30, le=600)
    enable_web_search: bool = True
    max_search_results: int = Field(default=5, ge=1, le=10)


class ResearchEngine:
    """Engine for executing research agents via Claude API.

    This is Phase 1 - requires API calls (after privacy approval).

    Provider: Claude API (fixed for now)
    Reason: Web search capability required
    """

    def __init__(
        self,
        settings: Settings | None = None,
        config: ResearchConfig | None = None,
    ) -> None:
        """Initialize the research engine.

        Args:
            settings: Application settings (for API key).
            config: Research-specific configuration.
        """
        self.settings = settings or get_settings()
        # Use settings value if no custom config provided
        if config is None:
            config = ResearchConfig(
                max_concurrent_agents=self.settings.max_concurrent_research_agents
            )
        self.config = config
        self._client: Any = None

    def _ensure_client(self) -> Any:
        """Lazily initialize the Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic(
                    api_key=self.settings.anthropic_api_key.get_secret_value()
                )
            except ImportError:
                raise RuntimeError("anthropic package not installed")
        return self._client

    async def execute_agent(
        self,
        agent: AgentDefinition,
        project_context: str,
    ) -> AgentResult:
        """Execute a single research agent.

        Args:
            agent: The agent definition to execute.
            project_context: Sanitized project context for research.

        Returns:
            AgentResult with research findings.
        """
        client = self._ensure_client()

        # Build the research prompt
        prompt = self._build_research_prompt(agent, project_context)

        # Execute the API call
        try:
            # Use web search if enabled
            tools = []
            if self.config.enable_web_search and self.settings.enable_web_search:
                tools = [{"type": "web_search_20250305"}]

            response = client.messages.create(
                model=self.settings.claude_model,
                max_tokens=self.settings.max_generation_tokens,
                tools=tools if tools else None,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse the response
            return self._parse_response(agent, response)

        except Exception as e:
            # Return error result
            return AgentResult(
                agent_id=agent.id,
                findings=[f"Error during research: {e!s}"],
                sources=[],
                recommendations=[],
                raw_response=None,
            )

    def _build_research_prompt(
        self,
        agent: AgentDefinition,
        project_context: str,
    ) -> str:
        """Build the research prompt for an agent.

        Uses specialized prompts for documentation framework agent vs domain agents.
        """
        # Special handling for documentation frameworks agent
        if agent.id == "agent_000_frameworks":
            return self._build_frameworks_research_prompt(agent, project_context)

        # Standard domain research prompt
        questions = "\n".join(f"- {q}" for q in agent.research_questions)
        queries = "\n".join(f"- {q}" for q in agent.search_queries)

        return f"""You are a {agent.role} conducting research for a project.

## Project Context
{project_context}

## Your Research Focus
{agent.role} - Domains: {', '.join(agent.domains)}

## Research Questions to Answer
{questions}

## Suggested Search Queries
{queries}

## Instructions
1. Search the web for current, relevant information
2. Focus on authoritative sources (government, academic, industry standards)
3. Provide specific, actionable findings
4. Include source URLs for all findings
5. Make recommendations based on your research

## Output Format
Provide your findings in this structure:
- KEY FINDINGS: Bullet points of important discoveries
- SOURCES: URLs and references used
- RECOMMENDATIONS: Actionable recommendations for the project
"""

    def _build_frameworks_research_prompt(
        self,
        agent: AgentDefinition,
        project_context: str,
    ) -> str:
        """Build specialized research prompt for documentation frameworks agent.

        This agent provides professional scaffolding for Llama 3.3 70B, which lacks
        web access. Claude gathers frameworks, templates, and examples that Llama
        will use to generate senior-level documentation.
        """
        questions = "\n".join(f"- {q}" for q in agent.research_questions)
        queries = "\n".join(f"- {q}" for q in agent.search_queries)

        return f"""You are a {agent.role} conducting research to provide professional documentation frameworks.

## Mission
Your research will be used by a local AI model (Llama 3.3 70B) that DOES NOT have web access.
You must gather comprehensive professional scaffolding so it can generate senior-level documentation.

## Project Context
{project_context}

## Research Questions to Answer
{questions}

## Suggested Search Queries
{queries}

## Critical Requirements

Your findings must include CONCRETE, SPECIFIC information in these categories:

### 1. Professional Frameworks
Search for and document:
- SMART goals framework (specific criteria and examples)
- RACI matrix structure and usage guidelines
- Risk assessment matrices (likelihood × impact scales)
- Gantt chart conventions and best practices
- Stakeholder analysis frameworks (power/interest grid, etc.)
- Budget categories and narrative structures for nonprofits

### 2. Document Structure Templates
For each document type (Budget, Risk Assessment, SOPs, Timeline, etc.):
- Standard section headings used by professionals
- Typical subsections and organization
- What information goes where
- Common formatting conventions

### 3. Concrete Examples
Find and extract SPECIFIC examples of:
- Well-written budget narratives (what makes them "senior level")
- Professional risk statements with mitigation strategies
- Effective SOP formats and language
- Clear timeline descriptions with milestones
- Executive-level status updates vs junior-level

### 4. Depth & Sophistication Markers
Identify what distinguishes senior-level from junior-level documentation:
- Level of strategic thinking (vs tactical)
- Depth of analysis and justification
- Cross-referencing and consistency
- Anticipation of questions/concerns
- Use of data and evidence

## Output Format

Provide findings in this EXACT structure:

### KEY FINDINGS
- [Specific frameworks, templates, structures you found]
- [Include concrete details, not vague descriptions]
- [Quote specific criteria, scales, categories when possible]

### PROFESSIONAL EXAMPLES
- [Example 1: Type of doc, what made it professional, specific language/structure]
- [Example 2: ...]
- [Include at least 5-7 concrete examples across different document types]

### FRAMEWORKS & STANDARDS
- [Framework name: specific structure/criteria]
- [Include at least 5 major frameworks with details]

### SENIOR VS JUNIOR MARKERS
- [What senior-level documentation includes that junior doesn't]
- [Specific differences in language, depth, structure]

### SOURCES
- [URLs with titles and relevance notes]

### RECOMMENDATIONS
- [How the local AI should use these frameworks]
- [Specific guidance for generating professional documentation]

## Instructions
1. Search extensively - this is foundational research for ALL projects
2. Prioritize authoritative sources (PMI, government style guides, academic)
3. Extract SPECIFIC details, not general principles
4. Include actual examples and concrete templates
5. Focus on nonprofit, tribal, and public sector contexts
"""

    def _parse_response(self, agent: AgentDefinition, response: Any) -> AgentResult:
        """Parse Claude API response into AgentResult."""
        # Extract text content
        raw_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                raw_text += block.text

        # Simple parsing - look for sections
        findings: list[str] = []
        sources: list[str] = []
        recommendations: list[str] = []

        current_section = None
        for line in raw_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            upper_line = line.upper()
            if "KEY FINDINGS" in upper_line or "FINDINGS:" in upper_line:
                current_section = "findings"
            elif "SOURCES:" in upper_line or "REFERENCES:" in upper_line:
                current_section = "sources"
            elif "RECOMMENDATIONS:" in upper_line:
                current_section = "recommendations"
            elif line.startswith(("-", "•", "*")) and current_section:
                content = line.lstrip("-•* ").strip()
                if current_section == "findings":
                    findings.append(content)
                elif current_section == "sources":
                    sources.append(content)
                elif current_section == "recommendations":
                    recommendations.append(content)

        return AgentResult(
            agent_id=agent.id,
            findings=findings or ["No specific findings extracted"],
            sources=sources,
            recommendations=recommendations,
            raw_response=raw_text,
        )

    async def execute_all(
        self,
        agents: list[AgentDefinition],
        project_context: str,
    ) -> list[AgentResult]:
        """Execute all research agents with concurrency control.

        Args:
            agents: List of agents to execute.
            project_context: Sanitized project context.

        Returns:
            List of agent results.
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)

        async def bounded_execute(agent: AgentDefinition) -> AgentResult:
            async with semaphore:
                return await self.execute_agent(agent, project_context)

        tasks = [bounded_execute(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results: list[AgentResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    AgentResult(
                        agent_id=agents[i].id,
                        findings=[f"Agent execution failed: {result!s}"],
                        sources=[],
                        recommendations=[],
                    )
                )
            else:
                final_results.append(result)

        return final_results
