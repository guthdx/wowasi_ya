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
        - Explicit constraints and rules
        - Hallucination prevention guards
        - Clear structure requirements
        - Cross-document consistency enforcement
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
            documents=all_documents,
            total_word_count=sum(d.word_count for d in all_documents),
            generation_time_seconds=generation_time,
            created_at=start_time,
        )
