"""Ouroboros Resilience and Stagnation Framework.

Detects patterns of developmental stagnation and provides lateral thinking advising:
1. SPINNING: Identical file hash repeating (threshold: 3 checks).
2. OSCILLATION: Alternating changes A -> B -> A -> B (threshold: 2 cycles / 5 states).
3. NO_DRIFT: Drift in performance or score metric <= 0.01 over 3 steps.
4. Advisor: Rotating developer personas (Hacker, Simplifier, Architect, Contrarian) with actionable prompts.
"""

import os
import sys
import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Initialize CLI and Console
app = typer.Typer(help="Ouroboros Resilience & Stagnation Advisor CLI")
console = Console()

# --- 1. Data Models ---


class FileState(BaseModel):
    """Holds a snapshot of a file path and its cryptographic content hash."""

    filepath: str = Field(description="Normalized relative path to the file")
    content_hash: str = Field(description="SHA-256 hash of the file contents")


class StepState(BaseModel):
    """Represents the complete state of the codebase at a specific point in time."""

    step_id: int = Field(description="Sequential step identifier")
    timestamp: float = Field(
        default_factory=time.time, description="Unix timestamp of the snapshot"
    )
    files: List[FileState] = Field(
        default_factory=list, description="State snapshots of all tracked files"
    )
    metric_value: Optional[float] = Field(
        default=None, description="Progress or performance score metric at this step"
    )


class StagnationReport(BaseModel):
    """Detailed diagnostic breakdown of detected stagnation patterns."""

    spinning_detected: bool = Field(description="True if SPINNING pattern is found")
    spinning_files: List[str] = Field(
        default_factory=list, description="Files stuck in identical repeating hashes"
    )
    oscillation_detected: bool = Field(
        description="True if OSCILLATION pattern is found"
    )
    oscillation_files: List[str] = Field(
        default_factory=list, description="Files repeating alternating change cycles"
    )
    nodrift_detected: bool = Field(
        description="True if progress metrics have flatlined"
    )
    drift_range: Optional[float] = Field(
        default=None, description="Maximum variance of metrics over the window"
    )
    stagnation_detected: bool = Field(
        description="True if any stagnation pattern is detected"
    )


class ResilienceAdvice(BaseModel):
    """Actionable lateral thinking advice for rotating developer personas."""

    stagnation_report: StagnationReport = Field(
        description="The underlying stagnation analysis report"
    )
    recommended_persona: str = Field(
        description="Hacker, Simplifier, Architect, or Contrarian"
    )
    persona_description: str = Field(
        description="Core philosophy and operational goals of this persona"
    )
    explanation: str = Field(
        description="Analytical justification for recommending this rotation"
    )
    action_items: List[str] = Field(
        default_factory=list, description="Specific tactical code adjustments"
    )
    lateral_thinking_prompt: str = Field(
        description="Reframing question to disrupt structural deadlocks"
    )


# --- 2. Stagnation Detector ---


class StagnationDetector:
    """Core algorithmic engine evaluating historical change paths for stagnation patterns."""

    @staticmethod
    def detect_spinning(
        history: List[StepState], threshold: int = 3
    ) -> Tuple[bool, List[str]]:
        """Detects if any file hash has remained identical for at least N consecutive steps.

        Threshold = 3 checks means: Step t-2 == Step t-1 == Step t.
        """
        if len(history) < threshold:
            return False, []

        spinning_files = []
        recent_steps = history[-threshold:]

        # Gather all file paths in the latest step
        latest_files = {f.filepath for f in recent_steps[-1].files}

        for filepath in latest_files:
            hashes = []
            file_exists_in_all = True
            for step in recent_steps:
                match = next((f for f in step.files if f.filepath == filepath), None)
                if match:
                    hashes.append(match.content_hash)
                else:
                    file_exists_in_all = False
                    break

            if file_exists_in_all and len(hashes) == threshold:
                # If all hashes are identical
                if len(set(hashes)) == 1:
                    spinning_files.append(filepath)

        return len(spinning_files) > 0, spinning_files

    @staticmethod
    def detect_oscillation(
        history: List[StepState], cycles: int = 2
    ) -> Tuple[bool, List[str]]:
        """Detects if any file exhibits alternating changes A -> B -> A -> B over 2 cycles.

        2 cycles of alternation requires a sequence of length 5 (e.g. [A, B, A, B, A]) where:
        - H0 == H2 == H4
        - H1 == H3
        - H0 != H1
        """
        required_len = (cycles * 2) + 1
        if len(history) < required_len:
            return False, []

        oscillation_files = []
        recent_steps = history[-required_len:]

        latest_files = {f.filepath for f in recent_steps[-1].files}

        for filepath in latest_files:
            hashes = []
            file_exists_in_all = True
            for step in recent_steps:
                match = next((f for f in step.files if f.filepath == filepath), None)
                if match:
                    hashes.append(match.content_hash)
                else:
                    file_exists_in_all = False
                    break

            if file_exists_in_all and len(hashes) == required_len:
                # Check for alternating pattern: A -> B -> A -> B -> A
                # [H0, H1, H2, H3, H4]
                h0, h1, h2, h3, h4 = hashes
                if h0 == h2 == h4 and h1 == h3 and h0 != h1:
                    oscillation_files.append(filepath)

        return len(oscillation_files) > 0, oscillation_files

    @staticmethod
    def detect_no_drift(
        history: List[StepState], threshold_steps: int = 3, delta: float = 0.01
    ) -> Tuple[bool, Optional[float]]:
        """Detects if progress metrics have stalled, with a max drift range <= delta over N steps."""
        if len(history) < threshold_steps:
            return False, None

        recent_steps = history[-threshold_steps:]
        metrics = [
            step.metric_value for step in recent_steps if step.metric_value is not None
        ]

        if len(metrics) < threshold_steps:
            # Not enough steps containing metrics
            return False, None

        drift_range = max(metrics) - min(metrics)
        stalled = drift_range <= delta
        return stalled, drift_range

    def analyze(self, history: List[StepState]) -> StagnationReport:
        """Runs all stagnation algorithms over history and aggregates findings."""
        spinning, spin_files = self.detect_spinning(history)
        oscillation, osc_files = self.detect_oscillation(history)
        nodrift, drift_range = self.detect_no_drift(history)

        stagnant = spinning or oscillation or nodrift

        return StagnationReport(
            spinning_detected=spinning,
            spinning_files=spin_files,
            oscillation_detected=oscillation,
            oscillation_files=osc_files,
            nodrift_detected=nodrift,
            drift_range=drift_range,
            stagnation_detected=stagnant,
        )


# --- 3. Lateral Thinking Advisor ---


class LateralAdvisor:
    """Recommends specific cognitive/developer persona rotations depending on identified stagnation."""

    PERSONAS = {
        "Hacker": {
            "description": "Rapid prototyping, brute-force speed, and ignoring aesthetic/refactoring debt.",
            "philosophy": "Break constraints by making it work immediately using whatever means necessary.",
            "prompts": [
                "What is the simplest, ugliest way to get this code operational within 10 minutes?",
                "Can you bypass the current elegant structure and hardcode a quick proof of concept?",
                "Write a quick, raw script in the scratch/ directory to verify the underlying math directly.",
            ],
        },
        "Simplifier": {
            "description": "Radical code reduction, consolidating interfaces, and deleting redundant structures.",
            "philosophy": "Complexity is a liability. Stagnation occurs because there is too much to manage.",
            "prompts": [
                "Identify and delete 30% of the code you wrote in the last 3 steps.",
                "How would you implement this if you were forbidden from using any helper classes?",
                "Can you merge two distinct modules into a single, straightforward procedural block?",
            ],
        },
        "Architect": {
            "description": "Structural clean-up, component decoupling, formal interface contracts, and complete typing.",
            "philosophy": "Systems stall when structural boundaries are fuzzy, creating accidental circular dependencies.",
            "prompts": [
                "Draw a strict boundary between these modules. No module should know the internal states of the other.",
                "Write clear Pydantic schemas or abstract base classes specifying exact inputs and outputs.",
                "Verify every function signature. Ensure type safety is perfectly airtight with zero 'Any' annotations.",
            ],
        },
        "Contrarian": {
            "description": "Challenging core design decisions, reversing course, and doing the opposite of standard advice.",
            "philosophy": "When standard logic spins in circles, you must intentionally adopt a radical alternative.",
            "prompts": [
                "Assume the exact opposite of your current design assumptions is true. How would you code it?",
                "What happens if you throw away the last files and try a completely different library or algorithm?",
                "If this bug is actually a features, how does the system design transform to accommodate it?",
            ],
        },
    }

    def advise(self, report: StagnationReport) -> ResilienceAdvice:
        """Determines the best persona rotation and constructs actionable lateral thinking guidance."""
        if not report.stagnation_detected:
            return ResilienceAdvice(
                stagnation_report=report,
                recommended_persona="None",
                persona_description="The project is currently drifting productively and avoiding structural stagnation.",
                explanation="No stagnation triggers fired. Continue with your standard engineering strategy.",
                action_items=[
                    "Maintain current progress velocity.",
                    "Continue writing unit tests.",
                ],
                lateral_thinking_prompt="How can you accelerate the next development milestone without introducing technical debt?",
            )

        # Decide Persona rotation based on stagnation details
        if report.oscillation_detected:
            # Oscillation indicates going back and forth. This requires either:
            # - A Simplifier (to delete the code that creates the oscillation)
            # - An Architect (to decouple the components causing side effects)
            persona = "Simplifier"
            desc = self.PERSONAS[persona]
            explanation = (
                "OSCILLATION detected. You are likely reverting/re-applying changes repeatedly "
                "because fixing one issue triggers another. A Simplifier mindset will break this cycle "
                "by removing unnecessary abstractions and simplifying the underlying data flows."
            )
            action_items = [
                "Locate the alternating file changes and merge conflicting logic into one direct pipeline.",
                "Delete secondary features that are cluttering your main algorithm's code paths.",
                "Remove redundant wrappers or helper utilities and write flat procedural code.",
            ]
            prompt = desc["prompts"][0]

        elif report.spinning_detected:
            # Spinning means repeating the exact same file hashes. We need a Contrarian or Hacker.
            persona = "Contrarian"
            desc = self.PERSONAS[persona]
            explanation = (
                "SPINNING detected. The system state is identical across several iterations, indicating "
                "the agent or developer is trapped in a logical loop. A Contrarian mindset is recommended "
                "to challenge key assumptions and force a completely different direction."
            )
            action_items = [
                "Intentionally write an implementation that does the absolute opposite of what you've tried.",
                "Draft a completely new approach in a temporary file and compare the two strategies.",
                "Question your core assumptions: Is this file division or data architecture actually necessary?",
            ]
            prompt = desc["prompts"][1]

        else:  # NO_DRIFT
            # Drift stall: metrics are completely flat. Hacker is best to shake things up.
            persona = "Hacker"
            desc = self.PERSONAS[persona]
            explanation = (
                "NO_DRIFT detected. The progress metrics are flatlining, indicating development has "
                "stalled in a localized optimum. A Hacker mindset will shock the system by hacking together "
                "a quick, functional solution to bypass the roadblock and restore positive drift."
            )
            action_items = [
                "Write a raw, ugly hack to force the progress metric up immediately.",
                "Bypass strict object models or elegant architectures for a few lines to establish connectivity.",
                "Create a fast prototype in the scratch/ directory to quickly explore and isolate the mathematical bottleneck.",
            ]
            prompt = desc["prompts"][2]

        return ResilienceAdvice(
            stagnation_report=report,
            recommended_persona=persona,
            persona_description=f"{desc['description']}\n[italic]{desc['philosophy']}[/italic]",
            explanation=explanation,
            action_items=action_items,
            lateral_thinking_prompt=prompt,
        )


# --- 4. Workspace Helper ---


class WorkspaceTracker:
    """Manages workspace snapshots, file hashing, and history logging."""

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        """Computes the SHA-256 hash of a file's contents."""
        hasher = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def snapshot_workspace(
        self, directory: str, step_id: int, metric_value: Optional[float] = None
    ) -> StepState:
        """Scans the directory for Python files and captures their paths and hashes."""
        files_state = []
        for root, _, files in os.walk(directory):
            # Ignore virtual environments, git folders, and caches
            if any(
                p in root
                for p in [
                    ".git",
                    "__pycache__",
                    "venv",
                    ".venv",
                    "env",
                    "egg-info",
                    ".antigravitycli",
                ]
            ):
                continue

            for filename in files:
                if filename.endswith(".py") or filename.endswith(".yaml"):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, directory)
                    h = self.compute_sha256(full_path)
                    if h:
                        files_state.append(FileState(filepath=rel_path, content_hash=h))

        return StepState(
            step_id=step_id,
            timestamp=time.time(),
            files=files_state,
            metric_value=metric_value,
        )


# --- 5. CLI Implementation ---


def load_history(filepath: str) -> List[StepState]:
    """Loads step history from a local JSON file."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [StepState(**item) for item in data]
    except Exception as e:
        console.print(f"[red]Error loading history from {filepath}: {e}[/red]")
    return []


def save_history(filepath: str, history: List[StepState]):
    """Saves step history to a local JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in history], f, indent=2)
    except Exception as e:
        console.print(f"[red]Failed to save history to {filepath}: {e}[/red]")


@app.command()
def record(
    directory: str = typer.Argument(
        ..., help="Path to the workspace directory to scan"
    ),
    history_file: str = typer.Option(
        ".ouroboros_history.json", "--history", "-h", help="Path to history file"
    ),
    metric: Optional[float] = typer.Option(
        None, "--metric", "-m", help="Current performance or progress metric value"
    ),
):
    """Snapshots the codebase state, appends it to history, and checks for stagnation."""
    console.print("[bold cyan]🔄 Recording workspace state snapshot...[/bold cyan]")

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

    # Render Report
    console.print("\n")
    if report.stagnation_detected:
        border = "yellow"
        title = "⚠️ Stagnation Alert!"
    else:
        border = "green"
        title = "✅ System Health Clear"

    console.print(
        Panel(
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
            expand=False,
        )
    )

    if report.stagnation_detected:
        console.print(
            "\n[bold yellow]💡 Actionable Lateral Thinking Tasks:[/bold yellow]"
        )
        for i, item in enumerate(advice.action_items, 1):
            console.print(f"  {i}. {item}")
        console.print(
            f'\n[bold magenta]🤔 Lateral Question:[/bold magenta]\n[italic]"{advice.lateral_thinking_prompt}"[/italic]\n'
        )


if __name__ == "__main__":
    app()
