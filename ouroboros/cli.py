"""Ouroboros Lite Main CLI.

Unified command surface integrating Socratic Interviews (Phase 0),
Double Diamond Planning (Phase 2), Verification Pipelines (Phase 4),
and Stagnation Resilience Advising (Phase 3).
"""

import os
import sys
from typing import List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import Ouroboros Lite Modules
from ouroboros.interview import InterviewEngine, InterviewState
from ouroboros.execution import DoubleDiamondPlanner
from ouroboros.evaluation import verify as run_evaluation_verify
from ouroboros.resilience import WorkspaceTracker, StagnationDetector, LateralAdvisor, load_history, save_history
from ouroboros.evolution import EvolutionEngine

app = typer.Typer(
    help="Ouroboros Lite - Specification-first AI coding workflow engine.",
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def interview(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name of the project"),
    type_str: Optional[str] = typer.Option("greenfield", "--type", "-t", help="greenfield or brownfield"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Initial product vision or idea"),
):
    """Launches the Phase 0 Socratic requirements interview loop.
    
    Exposes hidden assumptions, calculates real-time ambiguity,
    and crystallizes requirements into an immutable 'ouroboros_seed.yaml' spec.
    """
    state = InterviewState(
        project_name=name or "",
        project_type=type_str or "greenfield",
        initial_prompt=prompt or ""
    )
    engine = InterviewEngine(state=state)
    engine.run_interactive()


@app.command()
def plan(
    seed: str = typer.Option("ouroboros_seed.yaml", "--seed", "-s", help="Path to seed requirements yaml file"),
    output: str = typer.Option("ouroboros_plan.md", "--output", "-o", help="Filename to output the generated Double Diamond plan")
):
    """Generates the Phase 2 Double Diamond execution plan.
    
    Flattens the seed spec requirements, organizes tasks using Kahn's topological sort
    into dependency-aware parallel execution levels, and creates a gorgeous Mermaid flowchart.
    """
    if not os.path.exists(seed):
        console.print(f"[bold red]Error: Seed specification file not found at '{seed}'.[/bold red]")
        console.print("[yellow]Please run 'python run_ouroboros.py interview' first to generate a seed.[/yellow]")
        raise typer.Exit(code=1)
        
    console.print(f"[bold cyan]💎 Decomposing and Sorting Acceptance Criteria from: {seed}...[/bold cyan]")
    try:
        planner = DoubleDiamondPlanner(seed)
        planner.write_plan(output)
        console.print(Panel(
            Text(f"🎉 Double Diamond execution plan successfully written to:\n[underline]{output}[/underline]\n\n"
                 f"Explore the Mermaid architecture flowcharts and level checklist in the generated markdown file!",
                 style="bold green"),
            title="Planning Completed",
            border_style="green",
            expand=False
        ))
    except Exception as e:
        console.print(f"[bold red]Failed to generate plan: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def evaluate(
    files: Optional[List[str]] = typer.Argument(None, help="List of Python files to evaluate. Auto-discovers active files if omitted."),
    seed: str = typer.Option("ouroboros_seed.yaml", "--seed", "-s", help="Path to seed requirements yaml file"),
    tests: str = typer.Option("tests", "--tests", "-t", help="Directory or file containing pytest units"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional filepath to write the JSON consensus report")
):
    """Executes the Phase 4 Gated 3-stage mechanical and semantic verification pipeline.
    
    Verifies syntactical correctness, runs unit tests and coverage, maps semantic
    compliance against the seed specification, and aggregates votes into a consensus verdict.
    """
    # 1. Seed spec check
    if not os.path.exists(seed):
        console.print(f"[bold red]Error: Seed specification file not found at '{seed}'.[/bold red]")
        raise typer.Exit(code=1)

    # 2. Auto-discover Python files if none specified
    if not files:
        files = []
        exclude_dirs = {".git", ".venv", "venv", "__pycache__", "tests"}
        for root, dirs, filenames in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in filenames:
                if f.endswith(".py") and f != "run_ouroboros.py":
                    files.append(os.path.join(root, f))
                    
        if not files:
            console.print("[bold red]Error: No Python files found in the current workspace to evaluate.[/bold red]")
            raise typer.Exit(code=1)

    # Convert relative paths to standard system paths
    normalized_files = [os.path.normpath(f) for f in files]
    
    console.print(f"[bold cyan]🔍 Target files discovered for evaluation: {', '.join(normalized_files)}[/bold cyan]")
    
    # 3. Trigger evaluation pipeline from evaluation.py
    run_evaluation_verify(
        files=normalized_files,
        seed=seed,
        tests=tests,
        output=output
    )


@app.command()
def status(
    directory: str = typer.Argument(".", help="Path to the workspace directory to scan"),
    history_file: str = typer.Option(".ouroboros_history.json", "--history", "-h", help="Path to history file"),
    metric: Optional[float] = typer.Option(None, "--metric", "-m", help="Current progress score or performance metric (e.g. consensus score)")
):
    """Snapshots the codebase state, appends it to history, and checks for stagnation.
    
    Detects patterns like SPINNING (repetitive code), OSCILLATION (repeating loop),
    or NO_DRIFT (flatlining progress), and advises on rotation of lateral thinking personas.
    """
    if not os.path.exists(directory):
        console.print(f"[bold red]Error: Workspace directory '{directory}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold cyan]🔄 Recording workspace state snapshot and checking stagnation patterns...[/bold cyan]")
    
    # Load history
    history = load_history(history_file)
    next_id = history[-1].step_id + 1 if history else 1
    
    # Snapshot
    wt = WorkspaceTracker()
    new_step = wt.snapshot_workspace(directory, next_id, metric)
    history.append(new_step)
    
    # Analyze
    detector = StagnationDetector()
    report = detector.analyze(history)
    
    # Advise
    advisor = LateralAdvisor()
    advice = advisor.advise(report)
    
    # Save updated history
    save_history(history_file, history)
    
    # Render Report using rich
    console.print("\n")
    if report.stagnation_detected:
        border = "yellow"
        title = "⚠️ Stagnation Alert!"
    else:
        border = "green"
        title = "✅ System Health Clear"
        
    console.print(Panel(
        f"[bold]Detected Patterns:[/bold]\n"
        f" - SPINNING (identical repeat): {'[bold yellow]YES[/bold yellow]' if report.spinning_detected else 'No'}\n"
        f" - OSCILLATION (alternating):  {'[bold yellow]YES[/bold yellow]' if report.oscillation_detected else 'No'}\n"
        f" - NO_DRIFT (metric stall):    {'[bold yellow]YES[/bold yellow]' if report.nodrift_detected else 'No'}\n\n"
        f"[bold]Recommended Persona Rotation:[/bold]\n"
        f"👉 [bold green]{advice.recommended_persona}[/bold green]\n"
        f"{advice.persona_description}\n\n"
        f"[bold]Why this helps:[/bold]\n"
        f"{advice.explanation}",
        title=title,
        border_style=border,
        expand=False
    ))
    
    if report.stagnation_detected:
        console.print("\n[bold yellow]💡 Actionable Lateral Thinking Tasks:[/bold yellow]")
        for i, item in enumerate(advice.action_items, 1):
            console.print(f"  {i}. {item}")
        console.print(f"\n[bold magenta]🤔 Lateral Question:[/bold magenta]\n[italic]\"{advice.lateral_thinking_prompt}\"[/italic]\n")


@app.command()
def evolve(
    files: Optional[List[str]] = typer.Argument(None, help="List of Python files to evaluate. Auto-discovers active files if omitted."),
    seed: str = typer.Option("ouroboros_seed.yaml", "--seed", "-s", help="Path to seed requirements yaml file"),
    tests: str = typer.Option("tests", "--tests", "-t", help="Directory or file containing pytest units"),
    agents: str = typer.Option("AGENTS.md", "--agents", "-a", help="Path to binding session rules file"),
    history: str = typer.Option(".ouroboros_history.json", "--history", "-h", help="Path to history file"),
):
    """Executes the Phase 5 Evolution and Anti-Regression Patching.
    
    Diagnoses mechanical, semantic, and stagnation failures, synthesizes permanent
    anti-regression constraints and binding session rules, and patches them back.
    """
    # 1. Seed spec check
    if not os.path.exists(seed):
        console.print(f"[bold red]Error: Seed specification file not found at '{seed}'.[/bold red]")
        raise typer.Exit(code=1)

    # 2. Auto-discover Python files if none specified
    if not files:
        files = []
        exclude_dirs = {".git", ".venv", "venv", "__pycache__", "tests"}
        for root, dirs, filenames in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in filenames:
                if f.endswith(".py") and f != "run_ouroboros.py":
                    files.append(os.path.join(root, f))
                    
        if not files:
            console.print("[bold red]Error: No Python files found in the current workspace to evaluate.[/bold red]")
            raise typer.Exit(code=1)

    normalized_files = [os.path.normpath(f) for f in files]
    
    console.print("[bold cyan]🔄 Running diagnostic scans across all development stages...[/bold cyan]")
    
    try:
        engine = EvolutionEngine(seed_path=seed, agents_path=agents, history_path=history)
        failures = engine.diagnose_workspace(normalized_files, test_path=tests)
        
        if not failures:
            console.print(Panel(
                Text("✅ System Health Clear!\n\nNo active syntax errors, linter violations, test breaks, or stagnation loops detected in the workspace.",
                     style="bold green"),
                title="Evolution Succeeded",
                border_style="green",
                expand=False
            ))
            return

        console.print(f"[yellow]⚠️ Diagnosed {len(failures)} failures. Synthesizing anti-regression patches...[/yellow]")
        patches = engine.generate_patches(failures)
        
        console.print("[yellow]🔧 Applying permanent spec patches and binding rules to prevent recurrence...[/yellow]")
        yaml_patched, agents_patched = engine.apply_patches(patches)
        
        # Output markdown report
        console.print("\n")
        console.print(Panel(
            Text(f"🎉 Ouroboros has successfully evolved!\n\n"
                 f" - ouroboros_seed.yaml: Added {yaml_patched} new system constraints.\n"
                 f" - AGENTS.md: Added {agents_patched} new binding session rules.\n\n"
                 f"Future coding sessions and execution planning will now strictly follow these patches to prevent reoccurrence.",
                 style="bold green"),
            title="System Self-Healed",
            border_style="green",
            expand=False
        ))
        
        # Also print detailed logs if any changes made
        console.print("\n[bold cyan]📋 Detailed Anti-Regression Patches Applied:[/bold cyan]")
        for idx, p in enumerate(patches, 1):
            console.print(f"  [bold]{idx}. Recurrence Prevention Rule:[/bold] [italic]\"{p.session_rule}\"[/italic]")
            console.print(f"     [bold]System Constraint Patched:[/bold] [dim]\"{p.constraint}\"[/dim]")
            
    except Exception as e:
        console.print(f"[bold red]Failed during evolution phase: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def welcome():
    """Outputs the onboarding and welcome guide for Ouroboros Lite."""
    console.print(Panel(
        Text("o ------------ o\n"
             "O U R O B O R O S   L I T E\n"
             "o ------------ o\n\n"
             "Specification-First Workflow Engine for AI Coding.\n\n"
             "Stop Prompting. Start Specifying.\n\n"
             "Available Commands:\n"
             "  - interview  - Socratic interview to define seed specification\n"
             "  - plan       - Sort criteria and generate Double Diamond plan\n"
             "  - evaluate   - Mechanical & semantic 3-stage validation\n"
             "  - status     - Snapshot workspace & stagnation checks\n"
             "  - evolve     - Retrospectively patch specs to prevent regression\n"
             "  - welcome    - Onboarding guide", 
             style="bold magenta", justify="center"),
        border_style="magenta",
        expand=False
    ))


if __name__ == "__main__":
    app()
