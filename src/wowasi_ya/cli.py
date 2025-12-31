"""Command-line interface for Wowasi_ya."""

import asyncio
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from wowasi_ya import __version__
from wowasi_ya.config import get_settings
from wowasi_ya.core import (
    AgentDiscoveryService,
    DocumentGenerator,
    OutputManager,
    PrivacyLayer,
    QualityChecker,
    ResearchEngine,
)
from wowasi_ya.models.project import ProjectInput

app = typer.Typer(
    name="wowasi",
    help="Wowasi_ya - AI-powered project documentation generator",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Show the current version."""
    console.print(f"Wowasi_ya v{__version__}")


@app.command()
def generate(
    name: Annotated[str, typer.Argument(help="Project name")],
    description: Annotated[str, typer.Argument(help="Project description")],
    context: Annotated[
        Optional[str],
        typer.Option("--context", "-c", help="Additional context"),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: filesystem, obsidian, git"),
    ] = "filesystem",
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory"),
    ] = None,
    skip_privacy: Annotated[
        bool,
        typer.Option("--skip-privacy", help="Skip privacy review (not recommended)"),
    ] = False,
    publish_to_outline: Annotated[
        bool,
        typer.Option("--publish-to-outline", help="Publish to Outline Wiki after generation"),
    ] = False,
    share_outline: Annotated[
        bool,
        typer.Option("--share-outline", help="Enable public sharing link (requires --publish-to-outline)"),
    ] = False,
) -> None:
    """Generate project documentation from a description.

    This command runs the full generation pipeline:
    1. Agent Discovery (local)
    2. Privacy Review (requires approval)
    3. Research (API calls)
    4. Document Generation (API calls)
    5. Quality Check (local)
    6. Output
    7. Publish to Outline (optional, with --publish-to-outline)
    """
    asyncio.run(
        _generate_async(
            name=name,
            description=description,
            context=context,
            output_format=output_format,
            output_dir=output_dir,
            skip_privacy=skip_privacy,
            publish_to_outline=publish_to_outline,
            share_outline=share_outline,
        )
    )


async def _generate_async(
    name: str,
    description: str,
    context: str | None,
    output_format: str,
    output_dir: Path | None,
    skip_privacy: bool,
    publish_to_outline: bool = False,
    share_outline: bool = False,
) -> None:
    """Async implementation of generate command."""
    settings = get_settings()

    # Override output directory if specified
    if output_dir:
        settings.output_dir = output_dir

    project = ProjectInput(
        name=name,
        description=description,
        additional_context=context,
        output_format=output_format,
    )

    console.print(Panel(f"[bold blue]Generating documentation for:[/] {name}"))

    # Phase 0: Agent Discovery
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Phase 0: Discovering agents...", total=None)

        discovery = AgentDiscoveryService()
        domains, agents = discovery.discover(project)

        progress.update(task, completed=True)

    # Show discovered domains
    if domains:
        table = Table(title="Discovered Domains")
        table.add_column("Domain", style="cyan")
        table.add_column("Confidence", style="green")
        table.add_column("Keywords", style="yellow")

        for domain in domains[:5]:
            table.add_row(
                domain.domain.replace("_", " ").title(),
                f"{domain.confidence:.0%}",
                ", ".join(domain.keywords[:3]),
            )
        console.print(table)

    console.print(f"\n[green]✓[/] Discovered {len(agents)} research agents")

    # Privacy Review
    privacy = PrivacyLayer()
    full_text = f"{name} {description} {context or ''}"
    scan_result = privacy.scan(full_text)

    if scan_result.flags and not skip_privacy:
        console.print("\n[yellow]⚠ Privacy Review Required[/]")
        console.print(f"Found {len(scan_result.flags)} potential sensitive items:\n")

        for flag in scan_result.flags[:10]:
            console.print(f"  • [red]{flag.data_type.value}[/]: {flag.context}")

        proceed = typer.confirm("\nProceed with sanitized text?", default=True)
        if not proceed:
            console.print("[red]Generation cancelled.[/]")
            raise typer.Exit(1)

        use_sanitized = True
    else:
        use_sanitized = False
        if scan_result.flags:
            console.print("[yellow]⚠ Privacy check skipped (--skip-privacy)[/]")
        else:
            console.print("[green]✓[/] No privacy concerns detected")

    # Prepare context for API calls
    project_context = scan_result.sanitized_text if use_sanitized else full_text

    # Phase 1: Research
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Phase 1: Researching...", total=None)

        research = ResearchEngine(settings)
        research_results = await research.execute_all(agents, project_context)

        progress.update(task, completed=True)

    console.print(f"[green]✓[/] Completed research with {len(research_results)} agents")

    # Phase 2: Document Generation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Phase 2: Generating documents...", total=None)

        generator = DocumentGenerator(settings)
        generated_project = await generator.generate_all(project, research_results)

        progress.update(task, completed=True)

    console.print(
        f"[green]✓[/] Generated {len(generated_project.documents)} documents "
        f"({generated_project.total_word_count:,} words)"
    )

    # Phase 3: Quality Check
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Phase 3: Quality check...", total=None)

        checker = QualityChecker()
        issues = checker.check_project(generated_project)
        score = checker.get_quality_score(issues)

        progress.update(task, completed=True)

    if issues:
        console.print(f"\n[yellow]Quality Score: {score:.0%}[/]")
        errors = [i for i in issues if i.severity.value == "error"]
        warnings = [i for i in issues if i.severity.value == "warning"]
        console.print(f"  • {len(errors)} errors, {len(warnings)} warnings")
    else:
        console.print(f"\n[green]Quality Score: {score:.0%}[/] - No issues found!")

    # Phase 4: Output
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Phase 4: Writing output...", total=None)

        output = OutputManager(settings)
        paths = await output.write(generated_project, output_format)

        # Auto-sync to Google Drive if enabled
        if settings.enable_gdrive_sync and output_format != "gdrive":
            progress.update(task, description="Phase 4: Syncing to Google Drive...")
            try:
                gdrive_paths = await output.write(generated_project, "gdrive")
                # Mark that Google Drive sync succeeded
                console.print("[green]✓[/] Synced to Google Drive", style="dim")
            except Exception as e:
                # Don't fail the whole operation if gdrive sync fails
                console.print(f"[yellow]⚠[/] Google Drive sync failed: {e}", style="dim")

        progress.update(task, completed=True)

    console.print(f"\n[bold green]✓ Generation complete![/]")
    console.print(f"\nOutput written to:")
    for path in paths[:5]:
        console.print(f"  • {path}")
    if len(paths) > 5:
        console.print(f"  • ... and {len(paths) - 5} more files")

    # Phase 5: Publish to Outline (optional)
    if publish_to_outline:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Phase 5: Publishing to Outline...", total=None)

            try:
                from wowasi_ya.core.outline import OutlinePublisher

                publisher = OutlinePublisher(settings=settings)
                result = await publisher.publish(generated_project, enable_sharing=share_outline)

                progress.update(task, completed=True)
                console.print(f"\n[bold green]✓ Published to Outline![/]")
                console.print(f"  Collection: {result.collection.url}")
                console.print(f"  Documents: {len(result.documents)}")
                if result.public_url:
                    console.print(f"  Public URL: {result.public_url}")

            except ValueError as e:
                progress.update(task, completed=True)
                console.print(f"\n[red]✗ Outline publish failed:[/] {e}")
                console.print("  Hint: Set OUTLINE_API_KEY in .env")
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"\n[red]✗ Outline publish failed:[/] {e}")


@app.command()
def publish(
    project_name: Annotated[str, typer.Argument(help="Project name (folder name in output/)")],
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory containing the project"),
    ] = None,
    share: Annotated[
        bool,
        typer.Option("--share", "-s", help="Enable public sharing link"),
    ] = False,
) -> None:
    """Publish an existing project to Outline Wiki.

    Reads documents from output/{project_name}/ and publishes to Outline.
    Use this for projects that were generated but not published.
    """
    asyncio.run(_publish_async(project_name, output_dir, share))


async def _publish_async(
    project_name: str,
    output_dir: Path | None,
    share: bool,
) -> None:
    """Async implementation of publish command."""
    from wowasi_ya.core.outline import OutlinePublisher
    from wowasi_ya.models.document import Document, DocumentType, GeneratedProject

    settings = get_settings()
    base_dir = (output_dir or settings.output_dir) / project_name

    if not base_dir.exists():
        console.print(f"[red]Error:[/] Project not found: {base_dir}")
        console.print(f"\nAvailable projects:")
        output_root = output_dir or settings.output_dir
        if output_root.exists():
            for p in output_root.iterdir():
                if p.is_dir() and not p.name.startswith("."):
                    console.print(f"  • {p.name}")
        raise typer.Exit(1)

    # Map file paths to document types
    DOC_MAP = {
        "00-Overview/Project-Brief.md": (DocumentType.PROJECT_BRIEF, "00-Overview", "Project-Brief.md"),
        "00-Overview/README.md": (DocumentType.README, "00-Overview", "README.md"),
        "00-Overview/Glossary.md": (DocumentType.GLOSSARY, "00-Overview", "Glossary.md"),
        "10-Discovery/Context-and-Background.md": (DocumentType.CONTEXT_BACKGROUND, "10-Discovery", "Context-and-Background.md"),
        "10-Discovery/Stakeholder-Notes.md": (DocumentType.STAKEHOLDER_NOTES, "10-Discovery", "Stakeholder-Notes.md"),
        "20-Planning/Goals-and-Success-Criteria.md": (DocumentType.GOALS_SUCCESS, "20-Planning", "Goals-and-Success-Criteria.md"),
        "20-Planning/Initial-Budget.md": (DocumentType.INITIAL_BUDGET, "20-Planning", "Initial-Budget.md"),
        "20-Planning/Risks-and-Assumptions.md": (DocumentType.RISKS_ASSUMPTIONS, "20-Planning", "Risks-and-Assumptions.md"),
        "20-Planning/Scope-and-Boundaries.md": (DocumentType.SCOPE_BOUNDARIES, "20-Planning", "Scope-and-Boundaries.md"),
        "20-Planning/Timeline-and-Milestones.md": (DocumentType.TIMELINE_MILESTONES, "20-Planning", "Timeline-and-Milestones.md"),
        "30-Execution/Process-Workflow.md": (DocumentType.PROCESS_WORKFLOW, "30-Execution", "Process-Workflow.md"),
        "30-Execution/SOPs.md": (DocumentType.SOPS, "30-Execution", "SOPs.md"),
        "30-Execution/Task-Backlog.md": (DocumentType.TASK_BACKLOG, "30-Execution", "Task-Backlog.md"),
        "40-Comms/Meeting-Notes.md": (DocumentType.MEETING_NOTES, "40-Comms", "Meeting-Notes.md"),
        "40-Comms/Status-Updates.md": (DocumentType.STATUS_UPDATES, "40-Comms", "Status-Updates.md"),
    }

    console.print(Panel(f"[bold blue]Publishing to Outline:[/] {project_name}"))

    documents = []
    for file_path, (doc_type, folder, filename) in DOC_MAP.items():
        full_path = base_dir / file_path
        if full_path.exists():
            content = full_path.read_text()
            lines = content.strip().split('\n')
            title = lines[0].lstrip('# ').strip() if lines else filename.replace('.md', '')

            documents.append(Document(
                type=doc_type,
                title=title,
                content=content,
                folder=folder,
                filename=filename,
                word_count=len(content.split()),
            ))

    if not documents:
        console.print(f"[red]Error:[/] No documents found in {base_dir}")
        raise typer.Exit(1)

    console.print(f"Found {len(documents)} documents")

    project = GeneratedProject(
        project_name=project_name,
        project_area="04_Iyeska",
        documents=documents,
        total_word_count=sum(d.word_count for d in documents),
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Publishing to Outline...", total=None)

        try:
            publisher = OutlinePublisher(settings=settings)
            result = await publisher.publish(project, enable_sharing=share)

            progress.update(task, completed=True)

        except ValueError as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]✗ Publish failed:[/] {e}")
            console.print("  Hint: Set OUTLINE_API_KEY in .env")
            raise typer.Exit(1)
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]✗ Publish failed:[/] {e}")
            raise typer.Exit(1)

    console.print(f"\n[bold green]✓ Published to Outline![/]")
    console.print(f"  Collection: {result.collection.url}")
    console.print(f"  Documents: {len(result.documents)}")
    if result.public_url:
        console.print(f"  Public URL: {result.public_url}")


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host", "-h", help="Host to bind to")] = "0.0.0.0",
    port: Annotated[int, typer.Option("--port", "-p", help="Port to bind to")] = 8000,
    reload: Annotated[bool, typer.Option("--reload", "-r", help="Enable auto-reload")] = False,
) -> None:
    """Start the API server."""
    import uvicorn

    console.print(f"[bold]Starting Wowasi_ya API server[/]")
    console.print(f"  • Host: {host}")
    console.print(f"  • Port: {port}")
    console.print(f"  • Docs: http://{host}:{port}/docs")

    uvicorn.run(
        "wowasi_ya.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def discover(
    name: Annotated[str, typer.Argument(help="Project name")],
    description: Annotated[str, typer.Argument(help="Project description")],
) -> None:
    """Run only the agent discovery phase (no API calls).

    Useful for testing domain matching and agent generation.
    """
    project = ProjectInput(name=name, description=description)

    discovery = AgentDiscoveryService()
    domains, agents = discovery.discover(project)

    # Show domains
    console.print(Panel("[bold]Discovered Domains[/]"))
    for domain in domains:
        console.print(
            f"  • [cyan]{domain.domain}[/] ({domain.confidence:.0%}): "
            f"{', '.join(domain.keywords)}"
        )

    # Show agents
    console.print(Panel("[bold]Generated Agents[/]"))
    for agent in agents:
        console.print(f"  • [green]{agent.name}[/]")
        console.print(f"    Role: {agent.role}")
        console.print(f"    Questions: {len(agent.research_questions)}")


@app.command()
def privacy_check(
    text: Annotated[str, typer.Argument(help="Text to scan for PII/PHI")],
) -> None:
    """Scan text for sensitive information.

    Useful for testing the privacy detection before running full generation.
    """
    privacy = PrivacyLayer()
    result = privacy.scan(text)

    if result.flags:
        console.print(f"[yellow]Found {len(result.flags)} sensitive items:[/]\n")
        for flag in result.flags:
            console.print(f"  • [red]{flag.data_type.value}[/] (confidence: {flag.confidence:.0%})")
            console.print(f"    Text: {flag.text}")
            console.print(f"    Context: ...{flag.context}...\n")

        console.print("[bold]Sanitized version:[/]")
        console.print(result.sanitized_text)
    else:
        console.print("[green]No sensitive information detected.[/]")


@app.command()
def audit(
    project_id: Annotated[
        Optional[str],
        typer.Option("--project", "-p", help="Filter by project ID"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Maximum entries to show"),
    ] = 20,
) -> None:
    """View audit logs."""
    from wowasi_ya.db.audit import get_audit_logger

    logger = get_audit_logger()
    logs = logger.get_logs(project_id=project_id, limit=limit)

    if not logs:
        console.print("[yellow]No audit logs found.[/]")
        return

    table = Table(title="Audit Logs")
    table.add_column("Time", style="dim")
    table.add_column("Action", style="cyan")
    table.add_column("Project", style="green")
    table.add_column("Status")

    for log in logs:
        status = "[green]✓[/]" if log.success else "[red]✗[/]"
        table.add_row(
            log.timestamp.strftime("%Y-%m-%d %H:%M"),
            log.action.value,
            log.project_id or "-",
            status,
        )

    console.print(table)

    # Show API call summary
    counts = logger.get_api_call_count()
    console.print(f"\n[bold]API Call Summary:[/]")
    console.print(f"  • Research calls: {counts['research_calls']}")
    console.print(f"  • Generation calls: {counts['generation_calls']}")
    console.print(f"  • Total: {counts['total_api_calls']}")


if __name__ == "__main__":
    app()
