"""
Ouroboros Socratic Interview Engine.

This module conducts a Socratic interview (Phase 0) to reduce requirements ambiguity
for Greenfield and Brownfield software projects. It computes real-time Ambiguity
Scores and gates proceeding to Phase 1 until clarity is established.
"""

import os
import re
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Tuple, Literal
import yaml
from pydantic import BaseModel, Field
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm

# -----------------------------------------------------------------------------
# Pydantic Models for State Management
# -----------------------------------------------------------------------------


class InterviewRound(BaseModel):
    """Represents a single round of the Socratic interview."""

    round_number: int
    perspective: Literal[
        "Researcher", "Simplifier", "Architect", "Breadth-keeper", "Seed-closer"
    ]
    question: str
    user_response: Optional[str] = None
    ambiguity_score: Optional[float] = None
    dimension_scores: Dict[str, float] = Field(default_factory=dict)


class InterviewState(BaseModel):
    """Maintains the full interview session state and metrics."""

    project_name: str
    project_type: Literal["greenfield", "brownfield"] = "greenfield"
    initial_prompt: str
    current_ambiguity: float = 1.0
    rounds: List[InterviewRound] = Field(default_factory=list)
    dimension_clarity: Dict[str, float] = Field(
        default_factory=lambda: {
            "goal": 0.1,
            "constraint": 0.1,
            "success_criteria": 0.1,
            "context": 0.1,
        }
    )
    completed: bool = False


# -----------------------------------------------------------------------------
# Question Templates for Rule-Based Fallback
# -----------------------------------------------------------------------------

QUESTION_TEMPLATES: Dict[str, List[str]] = {
    "Researcher": [
        "Let's dig into the background of {project_name}. What is the primary problem we are trying to solve, and are there existing solutions or tools we should consider as models?",
        "For {project_name}, could you clarify any technical assumptions? Are there specific libraries, protocols, or frameworks you assume are best suited for this task?",
        "What domain-specific concepts or rules in {project_name} should we research and clarify before writing code?",
        "What is the historical background or business driver behind {project_name}? Who is the primary target audience or user?",
    ],
    "Simplifier": [
        "From a Simplifier's view: What is the absolute core MVP (Minimum Viable Product) of {project_name}? If we had to cut 50% of the scope, what remains?",
        "To avoid over-engineering {project_name}, can we simplify any of the features you mentioned? What is the simplest possible path to get a working prototype?",
        "What parts of {project_name} are nice-to-have rather than must-have? Let's explicitly defer or eliminate them for now.",
        "If you had to describe the core workflow of {project_name} in one sentence, what is it, and how can we keep it as simple as possible?",
    ],
    "Architect": [
        "Let's look at the structure of {project_name}. What are the main components (e.g., CLI, database, API, modules) and how do they communicate?",
        "For {project_name}, what are the external interface requirements? Do we need to expose APIs, write files, or integrate with other systems?",
        "How do you envision the data flow within {project_name}? What are the primary data structures or inputs/outputs we are working with?",
        "What are the structural constraints of {project_name}? For example, does it need to run as a single script, a package, or a docker container?",
    ],
    "Breadth-keeper": [
        "As the Breadth-keeper: What are the edge cases for {project_name}? How should we handle bad inputs, network failures, or missing files?",
        "What are the performance, scaling, or security requirements for {project_name}? Are there constraints on memory, speed, or user authorization?",
        "How should we verify the correctness of {project_name}? Do we need a test suite, logging, or runtime assertions?",
        "Are there any concurrent, multi-threaded, or async requirements for {project_name} we should prepare for?",
    ],
    "Seed-closer": [
        "As the Seed-closer: Let's summarize what we have so far. The core goal of {project_name} is established. What is the single most critical acceptance criteria (AC) to prove we succeeded?",
        "To wrap up the specification, what are the absolute 'must-nots' or negative constraints for {project_name} (things the system must NOT do)?",
        "Let's lock down the scope. Are there any final, specific rules or details you want to add before we generate the system specification?",
        "Are you completely satisfied with the boundaries we've defined, or is there any remaining grey area we need to resolve?",
    ],
}


# -----------------------------------------------------------------------------
# Interview Engine
# -----------------------------------------------------------------------------


class InterviewEngine:
    """
    Orchestrates the Socratic requirements interview.
    Computes real-time ambiguity scores and guides the interaction through 5 perspectives.
    Supports OpenAI-compatible LLM APIs and provides a robust rule-based fallback.
    """

    def __init__(
        self, state: Optional[InterviewState] = None, console: Optional[Console] = None
    ):
        self.state = state or InterviewState(project_name="", initial_prompt="")
        self.console = console or Console()
        self.active_perspective: Literal[
            "Researcher", "Simplifier", "Architect", "Breadth-keeper", "Seed-closer"
        ] = "Researcher"
        self.active_question: str = ""

    def calculate_ambiguity(self) -> float:
        """
        Calculates and updates the overall Ambiguity Score based on dimension clarity.
        Formula: Ambiguity = 1 - Sum(clarity_i * weight_i)
        """
        gc = self.state.dimension_clarity.get("goal", 0.0)
        cc = self.state.dimension_clarity.get("constraint", 0.0)
        sc = self.state.dimension_clarity.get("success_criteria", 0.0)
        ctx = self.state.dimension_clarity.get("context", 0.0)

        if self.state.project_type == "greenfield":
            # Greenfield weights: Goal 40%, Constraint 30%, Success Criteria 30%
            weighted_sum = (gc * 0.40) + (cc * 0.30) + (sc * 0.30)
        else:
            # Brownfield weights: Goal 35%, Constraint 25%, Success Criteria 25%, Context 15%
            weighted_sum = (gc * 0.35) + (cc * 0.25) + (sc * 0.25) + (ctx * 0.15)

        ambiguity = 1.0 - weighted_sum
        self.state.current_ambiguity = max(0.0, min(1.0, ambiguity))
        return self.state.current_ambiguity

    def evaluate_clarity_fallback(
        self, response: str, current_perspective: str
    ) -> Dict[str, float]:
        """
        Rule-based clarity calculation when no LLM key is configured.
        Increases dimension clarity based on length, keywords/descriptors, and active perspective.
        """
        scores = dict(self.state.dimension_clarity)
        response_lower = response.lower()

        # 1. Base length bonus (detailed responses reflect greater intent/care)
        length_bonus = 0.0
        if len(response) > 300:
            length_bonus = 0.08
        elif len(response) > 150:
            length_bonus = 0.04
        elif len(response) > 50:
            length_bonus = 0.02

        for k in scores:
            scores[k] = min(1.0, scores[k] + length_bonus)

        # 2. Key descriptor checking (increase clarity by 0.15 for match categories)
        goal_words = [
            "goal",
            "aim",
            "purpose",
            "want to",
            "build",
            "create",
            "solve",
            "deliver",
            "mvp",
            "core",
            "focus",
            "intent",
            "primary",
            "objective",
        ]
        constraint_words = [
            "must",
            "prevent",
            "limit",
            "restrict",
            "cannot",
            "rules",
            "require",
            "bound",
            "platform",
            "version",
            "dependency",
            "constraint",
            "limitations",
        ]
        success_words = [
            "verify",
            "ac",
            "acceptance criteria",
            "test",
            "benchmark",
            "metric",
            "success",
            "done",
            "complete",
            "assert",
            "check",
            "criteria",
            "validation",
        ]
        context_words = [
            "context",
            "legacy",
            "exist",
            "current",
            "integrate",
            "database",
            "api",
            "system",
            "brownfield",
            "previous",
            "background",
            "history",
        ]

        def check_matches(text: str, keywords: list) -> int:
            matches = 0
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
            return matches

        goal_matches = check_matches(response_lower, goal_words)
        constraint_matches = check_matches(response_lower, constraint_words)
        success_matches = check_matches(response_lower, success_words)
        context_matches = check_matches(response_lower, context_words)

        # Apply specific rule-based increase (0.15 for presence of critical markers)
        if goal_matches > 0:
            scores["goal"] = min(1.0, scores["goal"] + 0.15 + (goal_matches - 1) * 0.02)
        if constraint_matches > 0:
            scores["constraint"] = min(
                1.0, scores["constraint"] + 0.15 + (constraint_matches - 1) * 0.02
            )
        if success_matches > 0:
            scores["success_criteria"] = min(
                1.0, scores["success_criteria"] + 0.15 + (success_matches - 1) * 0.02
            )
        if context_matches > 0:
            scores["context"] = min(
                1.0, scores["context"] + 0.15 + (context_matches - 1) * 0.02
            )

        # 3. Perspective Focus Boost (the targeted dimension gets a 0.10 boost)
        p_boost = 0.10
        if current_perspective == "Researcher":
            scores["context"] = min(1.0, scores["context"] + p_boost)
        elif current_perspective == "Simplifier":
            scores["goal"] = min(1.0, scores["goal"] + p_boost)
        elif current_perspective == "Architect":
            scores["constraint"] = min(1.0, scores["constraint"] + p_boost)
        elif current_perspective == "Breadth-keeper":
            scores["success_criteria"] = min(1.0, scores["success_criteria"] + p_boost)
        elif current_perspective == "Seed-closer":
            # Pushes everything up slightly to close the loop
            for k in scores:
                scores[k] = min(1.0, scores[k] + 0.05)

        # Clamping and monotonicity (clarity should not regress)
        for k in scores:
            scores[k] = max(
                self.state.dimension_clarity.get(k, 0.1), min(1.0, scores[k])
            )

        return scores

    def _evaluate_round_llm(
        self, response: str, question: str, perspective: str
    ) -> Optional[Tuple[Dict[str, float], str, str, bool]]:
        """Queries an OpenAI-compatible endpoint to compute scores and generate Socratic questions."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None

        api_base = os.environ.get(
            "OPENAI_API_BASE", "https://api.openai.com/v1/chat/completions"
        )

        system_prompt = (
            "You are Ouroboros Socratic Interviewer, a world-class requirements analyst.\n"
            "Your task is to analyze the requirements of a software project through Socratic questioning.\n"
            "We have 4 dimensions of clarity: goal, constraint, success_criteria, and context.\n"
            "For Greenfield projects, the weights are: Goal (40%), Constraint (30%), Success Criteria (30%).\n"
            "For Brownfield projects, the weights are: Goal (35%), Constraint (25%), Success Criteria (25%), Context (15%).\n"
            "The current ambiguity score is 1.0 - Sum(clarity_i * weight_i).\n"
            "There are 5 Socratic perspectives:\n"
            "- Researcher: Probes background domain knowledge, assumptions, and technology choices.\n"
            "- Simplifier: Seeks to cut scope, focus on the MVP, and eliminate unnecessary complexity.\n"
            "- Architect: Explores structural boundaries, interfaces, data flows, and system integration points.\n"
            "- Breadth-keeper: Ensures no critical area is missed, checking for edge cases, security, error handling, and performance.\n"
            "- Seed-closer: Synthesizes clarifications, checks alignment with the overall vision, and pushes towards the final 'seed spec' completion.\n"
            "\n"
            "Based on the project details, interview history, and the latest user response, perform the following:\n"
            "1. Assess the clarity score (0.0 to 1.0) for each of the 4 dimensions. Ensure they are monotonic (never decrease compared to the current scores unless user explicitly retracts/changes requirements).\n"
            "2. Calculate the updated ambiguity score. If the ambiguity score is <= 0.2, the interview is completed.\n"
            "3. If not completed, identify the dimension with the lowest score and select the most appropriate Socratic perspective to probe it in the next round.\n"
            "4. Generate a highly contextual, sharp Socratic question from that perspective.\n"
            "\n"
            "You MUST respond with a single valid JSON object of this structure:\n"
            "{\n"
            '  "dimension_scores": {\n'
            '    "goal": float,\n'
            '    "constraint": float,\n'
            '    "success_criteria": float,\n'
            '    "context": float\n'
            "  },\n"
            '  "rationale": "Brief rationale for score updates",\n'
            '  "next_perspective": "Researcher" | "Simplifier" | "Architect" | "Breadth-keeper" | "Seed-closer",\n'
            '  "next_question": "Your next Socratic question",\n'
            '  "completed": boolean\n'
            "}\n"
        )

        history_lines = []
        for r in self.state.rounds:
            history_lines.append(f"[{r.perspective}] Q: {r.question}")
            if r.user_response:
                history_lines.append(f"User: {r.user_response}")
        history_str = "\n".join(history_lines)

        user_content = (
            f"Project Name: {self.state.project_name}\n"
            f"Project Type: {self.state.project_type}\n"
            f"Initial Prompt: {self.state.initial_prompt}\n\n"
            f"Previous Interview History:\n{history_str}\n\n"
            f"Latest Perspective: {perspective}\n"
            f"Latest Question: {question}\n"
            f"User's Latest Response: {response}\n\n"
            f"Current Dimension Clarity: {self.state.dimension_clarity}\n"
            f"Please output the updated scores, next perspective, next question, and completed status in valid JSON format."
        )

        payload = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        try:
            req = urllib.request.Request(
                api_base,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"]
                data = json.loads(content)

                scores = data.get("dimension_scores", {})
                for key in ["goal", "constraint", "success_criteria", "context"]:
                    if key not in scores:
                        scores[key] = self.state.dimension_clarity.get(key, 0.1)

                next_perspective = data.get("next_perspective", "Researcher")
                next_question = data.get(
                    "next_question", "Could you clarify the next step?"
                )
                completed = data.get("completed", False)

                return scores, next_perspective, next_question, completed
        except Exception as e:
            if os.environ.get("OUROBOROS_DEBUG"):
                self.console.print(
                    f"[yellow]LLM integration failed: {str(e)}. Seamlessly falling back.[/yellow]"
                )
            return None

    def get_next_question_and_perspective(
        self,
    ) -> Tuple[
        str,
        Literal[
            "Researcher", "Simplifier", "Architect", "Breadth-keeper", "Seed-closer"
        ],
    ]:
        """Determines the next perspective and question using a rule-based fallback model."""
        dims = ["goal", "constraint", "success_criteria"]
        if self.state.project_type == "brownfield":
            dims.append("context")

        all_clear = True
        for d in dims:
            if self.state.dimension_clarity.get(d, 0.0) < 0.8:
                all_clear = False
                break

        if all_clear:
            perspective: Literal[
                "Researcher", "Simplifier", "Architect", "Breadth-keeper", "Seed-closer"
            ] = "Seed-closer"
        else:
            # Find the lowest scoring dimension
            sorted_dims = sorted(
                dims, key=lambda d: self.state.dimension_clarity.get(d, 0.0)
            )
            lowest_dim = sorted_dims[0]

            mapping: Dict[
                str,
                Literal[
                    "Researcher",
                    "Simplifier",
                    "Architect",
                    "Breadth-keeper",
                    "Seed-closer",
                ],
            ] = {
                "goal": "Simplifier",
                "constraint": "Architect",
                "success_criteria": "Breadth-keeper",
                "context": "Researcher",
            }
            perspective = mapping.get(lowest_dim, "Researcher")

        asked_questions = {r.question for r in self.state.rounds}
        templates = QUESTION_TEMPLATES.get(
            perspective, ["Could you expand on this topic?"]
        )

        selected_question = ""
        for t in templates:
            formatted_q = t.format(project_name=self.state.project_name)
            if formatted_q not in asked_questions:
                selected_question = formatted_q
                break

        if not selected_question:
            # Fallback if templates are exhausted
            base_q = templates[0].format(project_name=self.state.project_name)
            selected_question = f"{base_q} (Could you expand further on this aspect?)"

        return selected_question, perspective

    def start_interview(self) -> Tuple[str, str]:
        """Initializes clarity scores based on the initial prompt and returns the first question."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            res = self._evaluate_round_llm(
                response=self.state.initial_prompt,
                question="Initial Prompt Analysis",
                perspective="Researcher",
            )
            if res:
                scores, next_p, next_q, comp = res
                self.state.dimension_clarity = scores
                self.calculate_ambiguity()
                self.active_perspective = next_p
                self.active_question = next_q
                if comp or self.state.current_ambiguity <= 0.2:
                    self.state.completed = True
                return next_q, next_p

        # Rule-based fallback initial setup
        scores = self.evaluate_clarity_fallback(self.state.initial_prompt, "Researcher")
        self.state.dimension_clarity = scores
        self.calculate_ambiguity()

        if self.state.current_ambiguity <= 0.2:
            self.state.completed = True
            return (
                "Requirements are already exceptionally clear! No further questioning needed.",
                "Seed-closer",
            )

        next_q, next_p = self.get_next_question_and_perspective()
        self.active_perspective = next_p
        self.active_question = next_q
        return next_q, next_p

    def submit_response(self, user_response: str) -> float:
        """Processes the user response, updates clarity levels, and queues the next round."""
        round_idx = len(self.state.rounds) + 1

        # Save round data
        current_round = InterviewRound(
            round_number=round_idx,
            perspective=self.active_perspective,
            question=self.active_question,
            user_response=user_response,
            ambiguity_score=1.0,
            dimension_scores={},
        )

        api_key = os.environ.get("OPENAI_API_KEY")
        llm_success = False

        if api_key:
            res = self._evaluate_round_llm(
                response=user_response,
                question=self.active_question,
                perspective=self.active_perspective,
            )
            if res:
                scores, next_p, next_q, comp = res
                self.state.dimension_clarity = scores
                self.calculate_ambiguity()

                current_round.dimension_scores = dict(scores)
                current_round.ambiguity_score = self.state.current_ambiguity
                self.state.rounds.append(current_round)

                self.active_perspective = next_p
                self.active_question = next_q

                if comp or self.state.current_ambiguity <= 0.2:
                    self.state.completed = True
                llm_success = True

        if not llm_success:
            # Rule-based fallback
            scores = self.evaluate_clarity_fallback(
                user_response, self.active_perspective
            )
            self.state.dimension_clarity = scores
            self.calculate_ambiguity()

            current_round.dimension_scores = dict(scores)
            current_round.ambiguity_score = self.state.current_ambiguity
            self.state.rounds.append(current_round)

            if self.state.current_ambiguity <= 0.2:
                self.state.completed = True
            else:
                next_q, next_p = self.get_next_question_and_perspective()
                self.active_perspective = next_p
                self.active_question = next_q

        return self.state.current_ambiguity

    def generate_seed(self, filepath: Optional[str] = None) -> str:
        """Saves the final interview state to a YAML seed file in the workspace."""
        goals = []
        constraints = []
        success_criteria = []
        contexts = []

        for r in self.state.rounds:
            resp = r.user_response or ""
            if r.perspective in ["Simplifier", "Seed-closer"]:
                goals.append(resp)
            elif r.perspective == "Architect":
                constraints.append(resp)
            elif r.perspective == "Breadth-keeper":
                success_criteria.append(resp)
            elif r.perspective == "Researcher":
                contexts.append(resp)

        if not goals:
            goals.append(self.state.initial_prompt)

        seed_data = {
            "ouroboros_version": "0.1.0",
            "project": {
                "name": self.state.project_name,
                "type": self.state.project_type,
                "initial_prompt": self.state.initial_prompt,
            },
            "clarity_metrics": {
                "ambiguity_score": round(self.state.current_ambiguity, 4),
                "dimension_clarity": {
                    k: round(v, 4) for k, v in self.state.dimension_clarity.items()
                },
            },
            "socratic_transcript": [
                {
                    "round": r.round_number,
                    "perspective": r.perspective,
                    "question": r.question,
                    "response": r.user_response,
                    "ambiguity_after": round(r.ambiguity_score or 1.0, 4),
                }
                for r in self.state.rounds
            ],
            "specification": {
                "core_goals": goals,
                "constraints": constraints,
                "acceptance_criteria": success_criteria,
                "architectural_context": (
                    contexts if self.state.project_type == "brownfield" else []
                ),
            },
        }

        yaml_content = yaml.safe_dump(
            seed_data, sort_keys=False, default_flow_style=False
        )

        if not filepath:
            filename = f"{self.state.project_name.lower().replace(' ', '_')}_seed.yaml"
            filepath = os.path.join(os.getcwd(), filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        return filepath

    # -------------------------------------------------------------------------
    # Visual Terminal Rendering (Rich-driven dashboard)
    # -------------------------------------------------------------------------

    def _make_progress_bar(self, score: float, width: int = 20) -> str:
        filled = int(round(score * width))
        empty = width - filled
        bar = "█" * filled + "░" * empty
        percent = int(score * 100)

        if score >= 0.8:
            color = "green"
        elif score >= 0.5:
            color = "yellow"
        else:
            color = "red"

        return f"[{color}]{bar}[/{color}] {percent}%"

    def _render_dashboard(self) -> None:
        """Prints a comprehensive progress report in the terminal."""
        self.console.clear()

        # Color ambiguity score based on value
        amb = self.state.current_ambiguity
        if amb <= 0.2:
            amb_color = "green"
        elif amb <= 0.6:
            amb_color = "yellow"
        else:
            amb_color = "red"

        # Build progress dashboard
        dashboard_lines = [
            f"[bold]Project Name:[/bold] [cyan]{self.state.project_name}[/cyan] ({self.state.project_type.capitalize()})",
            f"[bold]Current Ambiguity Score:[/bold] [{amb_color}]{amb:.4f}[/{amb_color}] (Target: <= 0.20)\n",
            "[bold]Dimension Clarity Tracker:[/bold]",
            f"  Goal Clarity:       {self._make_progress_bar(self.state.dimension_clarity.get('goal', 0.0))}",
            f"  Constraint Clarity: {self._make_progress_bar(self.state.dimension_clarity.get('constraint', 0.0))}",
            f"  Success Criteria:   {self._make_progress_bar(self.state.dimension_clarity.get('success_criteria', 0.0))}",
        ]

        if self.state.project_type == "brownfield":
            dashboard_lines.append(
                f"  Context Clarity:    {self._make_progress_bar(self.state.dimension_clarity.get('context', 0.0))}"
            )
        else:
            dashboard_lines.append(
                f"  Context Clarity:    {self._make_progress_bar(self.state.dimension_clarity.get('context', 0.0))} (Ignored for Greenfield)"
            )

        self.console.print(
            Panel(
                "\n".join(dashboard_lines),
                title="[bold magenta]Ouroboros Requirements Dashboard[/bold magenta]",
                border_style="magenta",
                expand=False,
            )
        )

    def run_interactive(self) -> None:
        """Initiates and runs the full Socratic interactive loop in the terminal."""
        self.console.print(
            Panel(
                Text(
                    "Welcome to the Ouroboros Socratic Interview Engine!\n"
                    "Phase 0: Socratic Clarification & Requirements Gathering",
                    style="bold magenta",
                    justify="center",
                ),
                subtitle="ouroboros-lite v0.1.0",
                border_style="magenta",
            )
        )

        # Check state variables and prompt if missing
        if not self.state.project_name:
            project_name = Prompt.ask(
                "[bold cyan]Enter Project Name[/bold cyan]", default="My AI Project"
            )
            project_type = Prompt.ask(
                "[bold cyan]Enter Project Type[/bold cyan]",
                choices=["greenfield", "brownfield"],
                default="greenfield",
            )
            initial_prompt = Prompt.ask(
                "[bold cyan]Enter your Initial Prompt / Product Vision[/bold cyan]"
            )

            self.state.project_name = project_name
            self.state.project_type = project_type
            self.state.initial_prompt = initial_prompt

        # Start the interview sequence
        q, p = self.start_interview()

        while not self.state.completed:
            self._render_dashboard()

            self.console.print(f"\n[bold magenta][{p} Perspective][/bold magenta]")
            self.console.print(f"[bold white]{q}[/bold white]\n")

            user_resp = Prompt.ask(
                "[bold green]Your Response[/bold green] (type /exit to quit, /skip to bypass)"
            )

            if user_resp.strip().lower() in ["/exit", "/quit"]:
                self.console.print(
                    "[yellow]Interview exited by user. Saving current session state...[/yellow]"
                )
                break

            if user_resp.strip().lower() == "/skip":
                self.console.print(
                    "[dim]Skipping round, continuing Socratic flow...[/dim]"
                )
                user_resp = "Skipped by user. Proceed with general clarification."

            # Update scores & ambiguity
            self.submit_response(user_resp)

            # Move to next question/perspective
            q = self.active_question
            p = self.active_perspective

        # Completion handling
        if self.state.completed:
            self._render_dashboard()
            self.console.print(
                Panel(
                    Text(
                        "🎉 Target Ambiguity Reached (<= 0.20)! Requirements are exceptionally clear. 🎉",
                        style="bold green",
                        justify="center",
                    ),
                    border_style="green",
                )
            )

            should_gen = Confirm.ask(
                "[bold cyan]Would you like to generate the Ouroboros Seed Specification now?[/bold cyan]",
                default=True,
            )
            if should_gen:
                filepath = self.generate_seed()
                self.console.print(
                    f"\n[bold green]Success![/bold green] Seed specification written to:\n[underline]{filepath}[/underline]"
                )
                self.console.print(
                    "\nYou are ready to transition to [bold blue]Phase 1: Double Diamond Planning[/bold blue]!"
                )


# -----------------------------------------------------------------------------
# Typer CLI Entrypoint
# -----------------------------------------------------------------------------

app = typer.Typer(help="Ouroboros Socratic Interview Engine CLI Tool")


@app.command()
def interview(
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Name of the project"
    ),
    type_str: Optional[str] = typer.Option(
        None, "--type", "-t", help="greenfield or brownfield"
    ),
    prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p", help="Initial product vision"
    ),
):
    """Launches the Socratic Interview interactive loop."""
    state = InterviewState(
        project_name=name or "",
        project_type=type_str or "greenfield",
        initial_prompt=prompt or "",
    )
    engine = InterviewEngine(state=state)
    engine.run_interactive()


if __name__ == "__main__":
    app()
