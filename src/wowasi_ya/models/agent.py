"""Agent definition and result models."""

from pydantic import BaseModel, Field


class DomainMatch(BaseModel):
    """A matched domain from the project description."""

    domain: str = Field(..., description="Domain name (e.g., 'healthcare', 'education')")
    keywords: list[str] = Field(default_factory=list, description="Matched keywords")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence score")
    stakeholders: list[str] = Field(
        default_factory=list,
        description="Relevant stakeholders for this domain",
    )


class AgentDefinition(BaseModel):
    """Definition for a research agent."""

    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    role: str = Field(..., description="Agent's research role/focus")
    domains: list[str] = Field(default_factory=list, description="Relevant domains")
    research_questions: list[str] = Field(
        default_factory=list,
        description="Questions this agent should research",
    )
    search_queries: list[str] = Field(
        default_factory=list,
        description="Suggested web search queries",
    )
    priority: int = Field(default=1, ge=1, le=5, description="Agent priority (1=highest)")


class AgentResult(BaseModel):
    """Result from an agent's research."""

    agent_id: str = Field(..., description="ID of the agent that produced this result")
    findings: list[str] = Field(default_factory=list, description="Key findings")
    sources: list[str] = Field(default_factory=list, description="Source URLs or references")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations based on research",
    )
    raw_response: str | None = Field(
        default=None,
        description="Raw response from Claude API",
    )
    # Token usage for cost tracking
    input_tokens: int = Field(default=0, description="Input tokens used")
    output_tokens: int = Field(default=0, description="Output tokens used")
