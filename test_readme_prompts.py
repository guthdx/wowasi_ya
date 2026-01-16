#!/usr/bin/env python3
"""Compare two README prompt versions for Oahe Legacy Living project."""

import asyncio
import os
from pathlib import Path

# Project context extracted from existing documents
PROJECT_CONTEXT = """
PROJECT NAME: Oahe Legacy Living

PROJECT DESCRIPTION:
An intergenerational assisted living facility designed specifically for aging farmers,
ranchers, and tribal elders along the Missouri River near Forest City, South Dakota.

KEY FACTS:
- Location: Forest City, SD (near tribal reservation land)
- Capacity: 50-80 bed assisted living facility
- Duration: 24 months (2025-2027)
- Budget: $4.2 - $4.8 million
- Lead Organization: Rooted Communities LLC
- Project Owner: Kelsey Scott
- Target Opening: 2026-2027
- Tagline: "Where Kinship is Keystone"

PROBLEM BEING ADDRESSED:
- 18 nursing homes closed across South Dakota between 2015-2023
- 225,744 elders projected by 2035 requiring care
- Rural families are asset-rich (land) but cash-poor
- Tribal elders face cultural barriers in existing care facilities
- Traditional care models disconnect elders from land, culture, and community

INNOVATIVE APPROACH:
1. Legacy Exchange Model: Families can transition land ownership in exchange for care
   services, preserving family legacies while ensuring sustainable funding
2. Nature-Integrated Design: Therapeutic gardens, outdoor spaces, Missouri River connections
3. Cultural Sensitivity: Programming for tribal elders and agricultural families
4. Intergenerational Programming: Connecting elders with young farmers, knowledge transfer
5. Community Integration: Facility serves as community hub, not isolation

STAKEHOLDERS:
- Aging farmers and ranchers
- Tribal elders and tribal governance
- Rural families facing care decisions
- Young farmers seeking mentorship and land access
- Healthcare providers and state agencies
- Potential funders (foundations, government programs)

RESEARCH FINDINGS:
- South Dakota faces unprecedented elder care crisis
- Rural communities have median ages exceeding state averages
- Farm families have significant land assets but limited liquid capital
- Traditional nursing home model economically unsustainable in rural settings
- Historical trauma affects tribal elder care preferences
- State-level political support exists for innovative rural healthcare solutions
"""

PROMPT_ORIGINAL = """You are an expert technical writer and project documentation specialist.

Your task is to generate a comprehensive README document for the following project.

The README should:
- Provide a clear overview of the project
- Explain the purpose and goals of the project
- Describe the intended audience and stakeholders
- Summarize the project scope and boundaries
- Highlight key features or components
- Explain how this project fits into the broader organizational or community context

Use the following context:
- Project name and description
- Research findings from multiple domain experts
- Applicable frameworks, best practices, and reference materials
- Relevant background and stakeholder information

The tone should be professional, clear, and accessible to both technical and non-technical audiences.

The document should be well-structured, thorough, and easy to read. Use headings, subheadings, and bullet points where appropriate.

Avoid unnecessary jargon, but do not oversimplify complex ideas.

Write in complete sentences and cohesive paragraphs. Ensure logical flow between sections.

Return the output in valid Markdown format.

PROJECT CONTEXT:
{context}
"""

PROMPT_MODIFIED = """You are a senior practitioner writing a README for a real project that will be read by decision-makers, collaborators, and potential funders.

This is not marketing copy and not an explainer essay. Write with clarity, restraint, and specificity.

TASK:
Generate a README document that clearly establishes what this project is, why it exists, and how it fits into its operating context.

REQUIRED CONTENT:
Include the following sections, in this order:
1. Project Overview
2. Purpose and Intent
3. Intended Audience and Stakeholders
4. Scope and Boundaries
5. Key Components or Capabilities
6. Organizational or Community Context

Use the provided project context and research findings. Prefer concrete details over generalized statements.

STYLE CONSTRAINTS (MANDATORY):
- Do not use em-dashes (— or --).
- Avoid filler or transitional phrases such as:
  "it is important to note"
  "in order to"
  "robust"
  "comprehensive"
  "leveraging"
  "this document aims to"
- Prefer short, declarative sentences.
- Avoid symmetrical paragraph structure.
- Do not explain concepts unless explanation is necessary for understanding the project.
- Write as someone accountable for the work, not as an external consultant describing it.

QUALITY BAR:
- Be precise rather than expansive.
- Say less, but make each sentence do work.
- If a statement cannot be tied to the provided context, omit it.

FORMAT:
- Valid Markdown
- Clear section headers
- Bullet points only where they add clarity, not decoration

Return only the README content. Do not include meta commentary.

PROJECT CONTEXT:
{context}
"""


async def generate_readme(prompt_template: str, prompt_name: str) -> str:
    """Generate README using the given prompt template."""
    import anthropic

    client = anthropic.AsyncAnthropic()

    full_prompt = prompt_template.format(context=PROJECT_CONTEXT)

    print(f"\n{'='*60}")
    print(f"Generating README with: {prompt_name}")
    print(f"{'='*60}")

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )

    content = message.content[0].text

    # Save to file
    output_dir = Path("output/prompt_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"README_{prompt_name}.md"
    output_path = output_dir / filename
    output_path.write_text(content)

    print(f"Saved to: {output_path}")
    print(f"Word count: {len(content.split())}")
    print(f"Character count: {len(content)}")

    return content


async def main():
    """Run comparison test."""
    print("\n" + "="*60)
    print("README PROMPT COMPARISON TEST")
    print("Project: Oahe Legacy Living")
    print("="*60)

    # Generate with both prompts
    original = await generate_readme(PROMPT_ORIGINAL, "original")
    modified = await generate_readme(PROMPT_MODIFIED, "modified")

    # Quick analysis
    print("\n" + "="*60)
    print("QUICK COMPARISON")
    print("="*60)

    # Count em-dashes
    original_emdash = original.count("—") + original.count("--")
    modified_emdash = modified.count("—") + modified.count("--")
    print(f"\nEm-dash count:")
    print(f"  Original: {original_emdash}")
    print(f"  Modified: {modified_emdash}")

    # Count filler phrases
    filler_phrases = [
        "it is important",
        "in order to",
        "robust",
        "comprehensive",
        "leveraging",
        "this document aims",
        "furthermore",
        "moreover",
    ]

    print(f"\nFiller phrase occurrences:")
    for phrase in filler_phrases:
        orig_count = original.lower().count(phrase)
        mod_count = modified.lower().count(phrase)
        if orig_count > 0 or mod_count > 0:
            print(f"  '{phrase}': Original={orig_count}, Modified={mod_count}")

    print(f"\nOutput files saved to: output/prompt_comparison/")
    print(f"  - README_original.md")
    print(f"  - README_modified.md")
    print("\nReview both files to compare quality.")


if __name__ == "__main__":
    asyncio.run(main())
