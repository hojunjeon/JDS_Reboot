"""Ouroboros Evaluation Framework.

Provides three-stage verification for Python codebases:
1. Stage 1 (Mechanical): Syntactical compile checks, pytest execution, lint check, and coverage tracking.
2. Stage 2 (Semantic): Gathers modified files and reviews requirements in ouroboros_seed.yaml (LLM or regex fallback).
3. Stage 3 (Consensus): Aggregates votes/evaluations and computes a formal consensus report with mathematical Ambiguity Index.
"""

import os
import sys
import subprocess
import hashlib
import re
import ast
import py_compile
import urllib.request
import json
import yaml
from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Initialize typer app and console
app = typer.Typer(help="Ouroboros Evaluation Framework CLI")
console = Console()

# --- 1. Data Models ---


class MechanicalEvaluationResult(BaseModel):
    """Result of Stage 1: Mechanical verification."""

    compile_success: bool = Field(
        description="True if all checked files compiled successfully"
    )
    compile_details: Dict[str, str] = Field(
        default_factory=dict, description="Detailed status/error per file"
    )
    tests_passed: Optional[bool] = Field(
        default=None, description="True if unit tests ran and passed"
    )
    tests_stdout: Optional[str] = Field(
        default=None, description="Standard output from test runner"
    )
    tests_stderr: Optional[str] = Field(
        default=None, description="Standard error from test runner"
    )
    tests_exit_code: Optional[int] = Field(
        default=None, description="Exit code from test runner"
    )
    lint_passed: Optional[bool] = Field(
        default=None, description="True if lint check passed"
    )
    lint_output: Optional[str] = Field(
        default=None, description="Output from linter check"
    )
    coverage_percentage: Optional[float] = Field(
        default=None, description="Parsed coverage percentage if available"
    )
    overall_success: bool = Field(description="True if all mechanical checks succeeded")


class RequirementStatus(BaseModel):
    """Evaluation status for a single requirement."""

    requirement: str = Field(description="The requirement name or description")
    satisfied: bool = Field(description="Whether the requirement is satisfied")
    confidence: float = Field(
        description="Confidence rating of evaluation between 0.0 and 1.0"
    )
    reasoning: str = Field(description="Detailed explanation/evidence of the status")


class SemanticEvaluationResult(BaseModel):
    """Result of Stage 2: Semantic requirement verification."""

    seed_file_path: Optional[str] = Field(
        default=None, description="Path to seed yaml file used"
    )
    reviewed_files: List[str] = Field(
        default_factory=list, description="List of files reviewed"
    )
    requirements_statuses: List[RequirementStatus] = Field(
        default_factory=list, description="Status list for requirements"
    )
    overall_score: float = Field(
        description="Semantic compliance score between 0.0 and 100.0"
    )
    passed: bool = Field(description="True if semantic checks met passing threshold")
    evaluator_type: str = Field(description="LLM or REGEX-CHECKLIST")


class ConsensusReport(BaseModel):
    """Result of Stage 3: Consensus aggregation."""

    consensus_score: float = Field(
        description="Aggregate consensus score between 0.0 and 100.0"
    )
    mechanical_ok: bool = Field(description="True if mechanical checks passed")
    semantic_ok: bool = Field(description="True if semantic checks passed consensus")
    total_judges: int = Field(description="Number of evaluations/judges factored in")
    agreement_rate: float = Field(
        description="Percentage of requirements where all judges agree (0-100)"
    )
    ambiguity_index: float = Field(
        description="Normalized Ambiguity Index (0.0 to 1.0, where 0.0 is perfect agreement)"
    )
    satisfied_requirements: List[str] = Field(
        default_factory=list, description="Requirements agreed to be satisfied"
    )
    unsatisfied_requirements: List[str] = Field(
        default_factory=list, description="Requirements agreed to be unsatisfied"
    )
    conflicts: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of requirements with conflicting votes"
    )
    verdict: str = Field(description="Formal verdict: APPROVED, REJECTED, or AMBIGUOUS")
    summary_markdown: str = Field(description="Formatted markdown summary report")


# --- 2. Stage 1: Mechanical Evaluator ---


class MechanicalEvaluator:
    """Performs mechanical validations such as compile checks, pytest execution, and linting."""

    @staticmethod
    def check_syntax(file_paths: List[str]) -> Tuple[bool, Dict[str, str]]:
        """Verifies that all specified Python files are syntactically valid."""
        success = True
        details = {}
        for path in file_paths:
            if not os.path.exists(path):
                details[path] = "File not found"
                success = False
                continue
            if not path.endswith(".py"):
                details[path] = "Skipped (not a Python file)"
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                ast.parse(content, filename=path)
                # Double-check with py_compile
                py_compile.compile(path, doraise=True)
                details[path] = "OK"
            except Exception as e:
                success = False
                details[path] = f"Syntax Error: {str(e)}"
        return success, details

    @staticmethod
    def run_tests(
        test_path: str = "tests", cwd: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str], int, Optional[float]]:
        """Runs pytest on the workspace and captures exit code, output, and coverage."""
        cmd = [sys.executable, "-m", "pytest", test_path, "--tb=short"]

        # Try to append coverage options if pytest-cov is installed
        try:
            import pytest_cov

            cmd.extend(["--cov=ouroboros", "--cov-report=term"])
        except ImportError:
            pytest_cov_available = False

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=cwd, check=False
            )
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
            passed = exit_code == 0

            # Try to extract coverage percentage from stdout
            coverage = None
            cov_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout)
            if cov_match:
                coverage = float(cov_match.group(1))

            return passed, stdout, stderr, exit_code, coverage
        except FileNotFoundError:
            return False, None, "pytest not found or executable unavailable", -1, None
        except Exception as e:
            return False, None, f"Execution failed: {str(e)}", -1, None

    @staticmethod
    def run_linter(
        file_paths: List[str], cwd: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Runs flake8 or black lint checks if installed. Falls back to a custom AST stylistic check."""
        # Try black formatting check
        black_cmd = [sys.executable, "-m", "black", "--check"] + file_paths
        try:
            res = subprocess.run(
                black_cmd, capture_output=True, text=True, cwd=cwd, check=False
            )
            if res.returncode == 0:
                return True, "Black style check passed successfully."
            else:
                return (
                    False,
                    f"Black formatting issues found:\n{res.stderr or res.stdout}",
                )
        except Exception:
            # Fall back to flake8
            flake_cmd = [sys.executable, "-m", "flake8"] + file_paths
            try:
                res = subprocess.run(
                    flake_cmd, capture_output=True, text=True, cwd=cwd, check=False
                )
                if res.returncode == 0:
                    return True, "Flake8 style check passed successfully."
                else:
                    return False, f"Flake8 violations found:\n{res.stdout}"
            except Exception:
                # Custom AST-based stylistic rule engine fallback
                violations = []
                for path in file_paths:
                    if not os.path.exists(path) or not path.endswith(".py"):
                        continue
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            # Rule 1: No trailing whitespace
                            if line.rstrip("\n") != line.rstrip():
                                violations.append(
                                    f"{path}:{i}: Trailing whitespace detected."
                                )
                            # Rule 2: Line too long (PEP 8 max 120 here for flexibility)
                            if len(line) > 120:
                                violations.append(
                                    f"{path}:{i}: Line too long ({len(line)} > 120 chars)."
                                )
                    except Exception as e:
                        violations.append(f"{path}: Failed to inspect style: {str(e)}")
                if not violations:
                    return (
                        True,
                        "AST-based stylistic fallback checks passed successfully (Black/Flake8 not installed).",
                    )
                return False, "AST-based stylistic violations found:\n" + "\n".join(
                    violations[:20]
                )

    def evaluate(
        self, file_paths: List[str], test_path: str = "tests", cwd: Optional[str] = None
    ) -> MechanicalEvaluationResult:
        """Executes all mechanical tests and compiles the results."""
        compile_ok, compile_details = self.check_syntax(file_paths)

        # Only run tests if syntax is compilation-clean
        tests_passed, stdout, stderr, exit_code, coverage = (
            None,
            None,
            None,
            None,
            None,
        )
        if compile_ok and os.path.exists(os.path.join(cwd or "", test_path)):
            tests_passed, stdout, stderr, exit_code, coverage = self.run_tests(
                test_path, cwd
            )

        lint_passed, lint_out = self.run_linter(file_paths, cwd)

        overall = (
            compile_ok and (tests_passed is not False) and (lint_passed is not False)
        )

        return MechanicalEvaluationResult(
            compile_success=compile_ok,
            compile_details=compile_details,
            tests_passed=tests_passed,
            tests_stdout=stdout,
            tests_stderr=stderr,
            tests_exit_code=exit_code,
            lint_passed=lint_passed,
            lint_output=lint_out,
            coverage_percentage=coverage,
            overall_success=overall,
        )


# --- 3. Stage 2: Semantic Evaluator ---


class SemanticEvaluator:
    """Verifies that high-level and structural requirements are satisfied, via LLM or regex rules."""

    DEFAULT_SEED_REQUIREMENTS = [
        {
            "name": "Type Safety",
            "description": "All operational Python code must be fully-typed with return types and parameters annotated (PEP 484).",
            "pattern": "type_safety",
        },
        {
            "name": "No Placeholders",
            "description": "Core implementation contains no stub code, TODOs, comments containing placeholder phrases, or empty ellipses (...).",
            "pattern": "no_placeholders",
        },
        {
            "name": "Robust Pydantic Modeling",
            "description": "Validation and data exchange schemas must utilize Pydantic v2 BaseModel classes with descriptive Field metadata.",
            "pattern": "pydantic_use",
        },
        {
            "name": "Resilience Stagnation Metrics",
            "description": "Engine must implement stagnation checks for SPINNING, OSCILLATION, and NO_DRIFT using appropriate numeric and hash histories.",
            "pattern": "stagnation_checks",
        },
        {
            "name": "Lateral Thinking Advisor",
            "description": "Advisor must dynamically recommend distinct developer personas (Hacker, Simplifier, Architect, Contrarian) with specific rationales.",
            "pattern": "persona_rotation",
        },
    ]

    def __init__(self, seed_path: Optional[str] = None):
        self.seed_path = seed_path
        self.requirements = self._load_seed_requirements()

    def _load_seed_requirements(self) -> List[Dict[str, Any]]:
        """Loads requirements list from seed yaml or falls back to defaults."""
        if self.seed_path and os.path.exists(self.seed_path):
            try:
                with open(self.seed_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    # Try to extract requirements or constraints list
                    reqs = data.get("requirements", []) or data.get("constraints", [])
                    if isinstance(reqs, list) and reqs:
                        parsed = []
                        for idx, r in enumerate(reqs):
                            if isinstance(r, dict):
                                parsed.append(
                                    {
                                        "name": r.get("name", f"Req-{idx}"),
                                        "description": r.get("description", str(r)),
                                        "pattern": r.get("pattern", "generic"),
                                    }
                                )
                            else:
                                parsed.append(
                                    {
                                        "name": f"Requirement-{idx}",
                                        "description": str(r),
                                        "pattern": "generic",
                                    }
                                )
                        return parsed
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Failed to load seed file {self.seed_path}: {e}. Using defaults.[/yellow]"
                )
        return self.DEFAULT_SEED_REQUIREMENTS

    def _call_llm(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Performs a self-contained API request to OpenAI, Gemini, or Anthropic depending on active keys."""
        openai_key = os.environ.get("OPENAI_API_KEY")
        gemini_key = os.environ.get("GEMINI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        if not (openai_key or gemini_key or anthropic_key):
            return None

        try:
            if anthropic_key:
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                }
            elif gemini_key:
                url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
                headers = {
                    "Authorization": f"Bearer {gemini_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "gemini-2.5-flash",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                }
            else:  # openai_key
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                }

            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=req_data, headers=headers, method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                resp_data = json.loads(response.read().decode("utf-8"))

            if anthropic_key:
                return resp_data["content"][0]["text"]
            else:
                return resp_data["choices"][0]["message"]["content"]
        except Exception as e:
            console.print(
                f"[red]LLM API call failed: {e}. Falling back to Regex Checklist.[/red]"
            )
            return None

    def _regex_check_file(
        self, requirement: Dict[str, Any], file_contents: Dict[str, str]
    ) -> RequirementStatus:
        """Robust fallback heuristic engine verifying semantic rules against source code constructs."""
        desc = requirement["description"].lower()
        name = requirement["name"].lower()

        # Join all contents for cross-file scanning
        all_code = "\n".join(file_contents.values())

        satisfied = False
        confidence = 0.8
        reasoning = ""

        if "type" in name or "type" in desc:
            # Type annotation check
            # Look for annotations in parameters or return type ->
            # A completely untyped file will lack any return annotations or standard typing imports
            def_count = len(re.findall(r"def\s+\w+", all_code))
            annotated_def_count = len(
                re.findall(
                    r"def\s+\w+\(.*?.*?\) -> [A-Za-z_\[\]\s,]+:", all_code, re.DOTALL
                )
            )

            if def_count == 0:
                satisfied = True
                confidence = 0.5
                reasoning = "No Python function definitions found to verify type-checking annotations."
            elif (
                annotated_def_count / def_count >= 0.8
                or "List[" in all_code
                or "Dict[" in all_code
                or "Optional[" in all_code
            ):
                satisfied = True
                confidence = 0.85
                reasoning = f"Verified type annotations: Found active typing annotations (e.g. typing imports, -> return markers) for {annotated_def_count}/{def_count} defined functions."
            else:
                satisfied = False
                confidence = 0.9
                reasoning = "Low density of type annotations found. Ensure both parameter type hints and '-> ReturnType:' markers are complete."

        elif "placeholder" in name or "placeholder" in desc:
            # Check for stub markers like "TODO", "pass", "...", "FIXME"
            # However, if 'pass' or '...' is inside docstrings or complex regexes, ignore.
            # Look for standalone pass or ellipsis in block scope
            has_todo = bool(re.search(r"#\s*(TODO|FIXME|XXX)", all_code, re.IGNORECASE))

            # Simple heuristic for ellipsis or pass as the ONLY body statement
            # E.g. a line containing just pass, ..., or placeholders
            placeholder_lines = []
            for filepath, content in file_contents.items():
                for idx, line in enumerate(content.splitlines(), 1):
                    clean_line = line.strip()
                    if clean_line in (
                        "pass",
                        "...",
                        '"""TODO"""',
                        "raise NotImplementedError",
                    ):
                        # Ensure it's not inside a comment or docstring block easily
                        placeholder_lines.append(f"{filepath}:L{idx} ({clean_line})")

            if has_todo or placeholder_lines:
                satisfied = False
                confidence = 0.95
                reasons = []
                if has_todo:
                    reasons.append("Active TODO/FIXME comments found in source code.")
                if placeholder_lines:
                    reasons.append(
                        f"Standard placeholders found at: {', '.join(placeholder_lines[:3])}"
                    )
                reasoning = " ".join(reasons)
            else:
                satisfied = True
                confidence = 0.9
                reasoning = "No obvious developer stubs, active TODO comments, or standalone 'pass'/'...' statement blocks found."

        elif "pydantic" in name or "pydantic" in desc or "model" in name:
            # Check for Pydantic v2 usage: importing BaseModel, Field
            imported_pydantic = "pydantic" in all_code or "BaseModel" in all_code
            has_fields = "Field(" in all_code or "model_validator" in all_code

            if imported_pydantic:
                satisfied = True
                confidence = 0.9
                reasoning = "Successfully found Pydantic classes (BaseModel) and metadata Field declarations integrated."
            else:
                satisfied = False
                confidence = 0.8
                reasoning = "Pydantic BaseModel/Field declarations could not be identified in the modified files."

        elif "stagnation" in name or "stagnation" in desc or "resilience" in name:
            # Check for SPINNING, OSCILLATION, NO_DRIFT logic
            has_spinning = (
                "SPINNING" in all_code or "spinning" in all_code or "hash" in all_code
            )
            has_oscillation = (
                "OSCILLATION" in all_code
                or "oscillation" in all_code
                or "cycle" in all_code
            )
            has_nodrift = "NO_DRIFT" in all_code or "drift" in all_code

            checks = []
            if has_spinning:
                checks.append("SPINNING hash repeat")
            if has_oscillation:
                checks.append("OSCILLATION alternating")
            if has_nodrift:
                checks.append("NO_DRIFT scale delta")

            if len(checks) >= 2:
                satisfied = True
                confidence = 0.9
                reasoning = f"Stagnation pattern algorithms detected in implementation code. Matches identified for: {', '.join(checks)}."
            else:
                satisfied = False
                confidence = 0.85
                reasoning = f"Could not verify all required stagnation patterns. Missing patterns in: {[p for p in ['SPINNING', 'OSCILLATION', 'NO_DRIFT'] if p.lower() not in all_code.lower()]}."

        elif "persona" in name or "persona" in desc or "advisor" in name:
            # Check for developer personas
            personas = ["Hacker", "Simplifier", "Architect", "Contrarian"]
            found = [p for p in personas if p in all_code or p.lower() in all_code]

            if len(found) >= 3:
                satisfied = True
                confidence = 0.95
                reasoning = f"Stagnation & lateral advisor configuration validated. Found persona identifiers: {', '.join(found)}."
            else:
                satisfied = False
                confidence = 0.9
                reasoning = f"Missing lateral persona strategies. Found: {found}. Expected rotation personas: {personas}."

        else:
            # General fallback check: Look for the occurrence of important terms in description
            words = [
                w
                for w in re.findall(r"\b\w{4,}\b", desc)
                if w
                not in ("must", "should", "ensure", "verify", "requirements", "satisfy")
            ]
            matches = [w for w in words if w in all_code.lower()]
            match_rate = len(matches) / len(words) if words else 1.0

            if match_rate >= 0.35:
                satisfied = True
                confidence = 0.6
                reasoning = f"Generic rule match passed: Code contains keyword correlation of {match_rate:.1%} with requirement terms ({', '.join(matches[:4])})."
            else:
                satisfied = False
                confidence = 0.6
                reasoning = f"Failed correlation match: Only {match_rate:.1%} of keywords matching the requirement description were found."

        return RequirementStatus(
            requirement=requirement["name"],
            satisfied=satisfied,
            confidence=confidence,
            reasoning=reasoning,
        )

    def evaluate(self, file_paths: List[str]) -> SemanticEvaluationResult:
        """Reviews modified files against seed requirements using LLM or robust regex heuristics."""
        file_contents = {}
        for path in file_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        file_contents[path] = f.read()
                except Exception as e:
                    console.print(
                        f"[yellow]Skipping file read for {path}: {e}[/yellow]"
                    )

        if not file_contents:
            return SemanticEvaluationResult(
                seed_file_path=self.seed_path,
                reviewed_files=file_paths,
                requirements_statuses=[
                    RequirementStatus(
                        requirement=req["name"],
                        satisfied=False,
                        confidence=1.0,
                        reasoning="No operational source files were provided or successfully read.",
                    )
                    for req in self.requirements
                ],
                overall_score=0.0,
                passed=False,
                evaluator_type="ERROR",
            )

        # Attempt LLM Semantic evaluation
        llm_system = (
            "You are Ouroboros Semantic Judge, an elite AI code evaluator.\n"
            "Analyze the provided source code files against the listed requirements.\n"
            "For each requirement, provide a structured evaluation in JSON format containing:\n"
            " - requirement: Name of requirement\n"
            " - satisfied: true/false\n"
            " - confidence: float between 0.0 and 1.0\n"
            " - reasoning: brief, evidence-backed proof from the code.\n"
            "Respond ONLY with a valid JSON array containing these objects. No markdown wraps, no extra text."
        )

        prompt_data = {
            "requirements": self.requirements,
            "codebase": {
                path: content[:20000] for path, content in file_contents.items()
            },  # truncate to prevent token issues
        }

        llm_response = self._call_llm(json.dumps(prompt_data, indent=2), llm_system)

        statuses = []
        evaluator_type = "LLM"

        if llm_response:
            try:
                # Strip markdown code wraps if present
                clean_json = llm_response.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(
                        r"^```(?:json)?\n|```$", "", clean_json, flags=re.MULTILINE
                    ).strip()

                parsed_statuses = json.loads(clean_json)
                for item in parsed_statuses:
                    statuses.append(RequirementStatus(**item))
            except Exception as e:
                console.print(
                    f"[yellow]Failed to parse LLM evaluation JSON response: {e}. Falling back to Regex Checklist.[/yellow]"
                )
                statuses = []

        if not statuses:
            # Fallback: Regex evaluation
            evaluator_type = "REGEX-CHECKLIST"
            for req in self.requirements:
                status = self._regex_check_file(req, file_contents)
                statuses.append(status)

        # Calculate score
        satisfied_count = sum(1 for s in statuses if s.satisfied)
        total_count = len(statuses)
        score = (satisfied_count / total_count) * 100.0 if total_count > 0 else 100.0
        passed = score >= 80.0  # 80% threshold

        return SemanticEvaluationResult(
            seed_file_path=self.seed_path,
            reviewed_files=list(file_contents.keys()),
            requirements_statuses=statuses,
            overall_score=score,
            passed=passed,
            evaluator_type=evaluator_type,
        )


# --- 4. Stage 3: Consensus Aggregator ---


class ConsensusBuilder:
    """Aggregates multiple semantic votes and mechanical checks into a single formal consensus report."""

    @staticmethod
    def calculate_ambiguity_index(
        votes_matrix: List[List[bool]],
    ) -> Tuple[float, float]:
        """Calculates consensus agreement rate and normalized mathematical Ambiguity Index.

        Formula:
        Ambiguity Index = (4 / R) * sum(p_r * (1 - p_r))
        Where p_r is the proportion of positive votes for requirement r, and R is the number of requirements.
        This bounds the Ambiguity Index precisely between 0.0 (perfect agreement) and 1.0 (50/50 split on all items).
        """
        if not votes_matrix or not votes_matrix[0]:
            return 100.0, 0.0

        num_requirements = len(votes_matrix)
        num_judges = len(votes_matrix[0])

        agreements = 0
        total_variance_sum = 0.0

        for r_votes in votes_matrix:
            p_r = sum(r_votes) / num_judges
            total_variance_sum += p_r * (1.0 - p_r)
            if p_r == 1.0 or p_r == 0.0:
                agreements += 1

        agreement_rate = (agreements / num_requirements) * 100.0
        ambiguity_index = (4.0 / num_requirements) * total_variance_sum

        return agreement_rate, ambiguity_index

    def build_report(
        self,
        mechanical_result: MechanicalEvaluationResult,
        semantic_results: List[SemanticEvaluationResult],
    ) -> ConsensusReport:
        """Gathers multiple semantic judgments and the mechanical check to establish consensus."""
        total_judges = len(semantic_results)

        if total_judges == 0:
            return ConsensusReport(
                consensus_score=0.0,
                mechanical_ok=mechanical_result.overall_success,
                semantic_ok=False,
                total_judges=0,
                agreement_rate=0.0,
                ambiguity_index=1.0,
                verdict="REJECTED",
                summary_markdown="### Consensus Report\nNo semantic judges available.",
            )

        # Get list of unique requirement names across all judges
        all_req_names = []
        for res in semantic_results:
            for s in res.requirements_statuses:
                if s.requirement not in all_req_names:
                    all_req_names.append(s.requirement)

        # Build votes matrix: row = requirement, col = judge vote (bool)
        votes_matrix = []
        satisfied_reqs = []
        unsatisfied_reqs = []
        conflicts = []

        for req_name in all_req_names:
            req_votes = []
            reasons = []
            for judge_idx, res in enumerate(semantic_results):
                # Find matching requirement in this judge's report
                status_item = next(
                    (s for s in res.requirements_statuses if s.requirement == req_name),
                    None,
                )
                vote = status_item.satisfied if status_item else False
                req_votes.append(vote)

                judge_name = f"Judge-{judge_idx} ({res.evaluator_type})"
                reason_text = (
                    status_item.reasoning if status_item else "No evaluation provided."
                )
                reasons.append(
                    f"- **{judge_name}**: {'[SATISFIED]' if vote else '[FAILED]'} {reason_text}"
                )

            votes_matrix.append(req_votes)
            positive_votes = sum(req_votes)

            # Simple majority voting rule
            is_satisfied = positive_votes > (total_judges / 2)

            # Record status
            if positive_votes == total_judges:
                satisfied_reqs.append(req_name)
            elif positive_votes == 0:
                unsatisfied_reqs.append(req_name)
            else:
                # Disagreement exists!
                conflicts.append(
                    {
                        "requirement": req_name,
                        "positive_votes": positive_votes,
                        "total_votes": total_judges,
                        "majority_verdict": is_satisfied,
                        "details": "\n".join(reasons),
                    }
                )
                if is_satisfied:
                    satisfied_reqs.append(req_name)
                else:
                    unsatisfied_reqs.append(req_name)

        # Calculate agreement statistics
        agreement_rate, ambiguity_index = self.calculate_ambiguity_index(votes_matrix)

        # Calculate scores
        avg_semantic_score = (
            sum(r.overall_score for r in semantic_results) / total_judges
        )

        # Absolute Veto: If mechanical fails, we penalize the overall consensus score heavily
        mechanical_ok = mechanical_result.overall_success
        consensus_score = (
            avg_semantic_score if mechanical_ok else avg_semantic_score * 0.4
        )

        semantic_ok = len(unsatisfied_reqs) == 0 and len(conflicts) == 0

        # Decide Verdict
        if not mechanical_ok:
            verdict = "REJECTED"
        elif len(unsatisfied_reqs) > 0:
            verdict = "REJECTED"
        elif ambiguity_index > 0.35:
            verdict = "AMBIGUOUS"
        else:
            verdict = "APPROVED"

        # Generate summary markdown report
        markdown = []
        markdown.append("# ⚖️ Ouroboros Verification & Consensus Report\n")

        # Verdict Banner
        if verdict == "APPROVED":
            markdown.append(
                "> [!IMPORTANT]\n> **VERDICT: APPROVED** ✅\n> Code compiles successfully, passes unit tests, and satisfies all requirements with high consensus.\n"
            )
        elif verdict == "AMBIGUOUS":
            markdown.append(
                "> [!WARNING]\n> **VERDICT: AMBIGUOUS** ⚠️\n> Mechanical validation succeeded, but semantic judges disagreed on key requirements. Action required to resolve variance.\n"
            )
        else:
            markdown.append(
                "> [!CAUTION]\n> **VERDICT: REJECTED** ❌\n> Code has failed mechanical checks (compilation/tests) or has confirmed requirement gaps.\n"
            )

        markdown.append("## 📊 Summary Metrics\n")
        markdown.append(
            f"- **Consensus Score**: `{consensus_score:.1f}/100.0` (Veto factored: `{'No' if mechanical_ok else 'Yes'}`)"
        )
        markdown.append(
            f"- **Mechanical Validation**: `{'PASS' if mechanical_ok else 'FAIL'}`"
        )
        markdown.append(
            f"- **Semantic Consensus**: `{'PASS' if semantic_ok else 'FAIL'}`"
        )
        markdown.append(
            f"- **Agreement Rate**: `{agreement_rate:.1f}%` ({len(satisfied_reqs) + len(unsatisfied_reqs) - len(conflicts)}/{len(all_req_names)} in perfect sync)"
        )
        markdown.append(
            f"- **Ambiguity Index**: `{ambiguity_index:.3f}` (Scale: 0.0 = perfect agreement, 1.0 = total disagreement)\n"
        )

        # Mechanical Details Section
        markdown.append("## ⚙️ Stage 1: Mechanical Health Report\n")
        markdown.append(
            f"- **Compilation Status**: `{'CLEAN' if mechanical_result.compile_success else 'ERRORS'}`"
        )
        if mechanical_result.compile_details:
            markdown.append("  *File Compilation Breakdown:*")
            for f, st in mechanical_result.compile_details.items():
                markdown.append(f"  - `{os.path.basename(f)}`: {st}")

        markdown.append(
            f"- **Unit Tests**: `{'PASSED' if mechanical_result.tests_passed else 'FAILED/SKIPPED'}` (Exit Code: `{mechanical_result.tests_exit_code}`)"
        )
        if mechanical_result.coverage_percentage is not None:
            markdown.append(
                f"- **Code Coverage**: `{mechanical_result.coverage_percentage:.1f}%` Check"
            )
        markdown.append(
            f"- **Style Check (Linter)**: `{'PASSED' if mechanical_result.lint_passed else 'ISSUES FOUND'}`\n"
        )

        # Requirements Breakdown Section
        markdown.append("## 🎯 Stage 2: Requirement Compliance Status\n")
        markdown.append("### Satisfied Requirements")
        for req in satisfied_reqs:
            if req not in [c["requirement"] for c in conflicts]:
                markdown.append(f"- [x] **{req}** (Unanimous agreement)")
            else:
                markdown.append(f"- [x] **{req}** (Majority rule)")

        if unsatisfied_reqs:
            markdown.append("\n### Unsatisfied Requirements")
            for req in unsatisfied_reqs:
                markdown.append(f"- [ ] **{req}** (Definite failure)")

        # Disagreements/Ambiguities Section
        if conflicts:
            markdown.append("\n## ⚖️ Stage 3: Judge Disagreements & Conflicts")
            markdown.append(
                "The semantic judges had conflicting evaluations on the following requirements:"
            )
            for conf in conflicts:
                markdown.append(f"\n### Requirement: {conf['requirement']}")
                markdown.append(
                    f"- **Disagreement Ratio**: `{conf['positive_votes']}/{conf['total_votes']}` positive votes."
                )
                markdown.append(
                    f"- **Majority Decision**: `{'Satisfied' if conf['majority_verdict'] else 'Unsatisfied'}`"
                )
                markdown.append("- **Detailed Judge Reasoning:**")
                markdown.append(conf["details"])

        summary_md = "\n".join(markdown)

        return ConsensusReport(
            consensus_score=consensus_score,
            mechanical_ok=mechanical_ok,
            semantic_ok=semantic_ok,
            total_judges=total_judges,
            agreement_rate=agreement_rate,
            ambiguity_index=ambiguity_index,
            satisfied_requirements=satisfied_reqs,
            unsatisfied_requirements=unsatisfied_reqs,
            conflicts=conflicts,
            verdict=verdict,
            summary_markdown=summary_md,
        )


# --- 5. CLI Execution & Orchestrator ---


@app.command()
def verify(
    files: List[str] = typer.Argument(..., help="List of Python files to evaluate"),
    seed: Optional[str] = typer.Option(
        None, "--seed", "-s", help="Path to seed requirements yaml file"
    ),
    tests: str = typer.Option(
        "tests", "--tests", "-t", help="Directory or file containing pytest units"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional filepath to write the JSON consensus report",
    ),
):
    """Executes the full Ouroboros 3-stage mechanical, semantic, and consensus evaluation."""
    console.print(
        "[bold cyan]🤖 Initializing Ouroboros Verification Pipeline...[/bold cyan]"
    )

    # 1. Mechanical evaluation
    console.print(
        "[yellow]🔨 Stage 1: Running Mechanical Verification (AST compilation, tests, formatting)...[/yellow]"
    )
    me = MechanicalEvaluator()
    mech_result = me.evaluate(files, test_path=tests)

    # 2. Semantic evaluation
    console.print(
        "[yellow]🧠 Stage 2: Performing Semantic Review against seed requirements...[/yellow]"
    )
    se = SemanticEvaluator(seed_path=seed)

    # Run multiple evaluation profiles to build a consensus (e.g. LLM judge and robust Regex checklist judge)
    sem_results = []

    # Judge 1: General semantic checker (automatically picks LLM if key is available, else Regex)
    judge1 = se.evaluate(files)
    sem_results.append(judge1)

    # Judge 2: Pure strict regex heuristic checklist to act as independent vote
    # Force fallback checklist review to verify correlation robustness
    orig_eval_type = se.evaluate
    se_checklist = SemanticEvaluator(seed_path=seed)
    # Patch to skip LLM to get a raw check
    se_checklist._call_llm = lambda prompt, system: None
    judge2 = se_checklist.evaluate(files)
    sem_results.append(judge2)

    # 3. Consensus Building
    console.print(
        "[yellow]⚖️ Stage 3: Aggregating votes and generating Consensus Report...[/yellow]"
    )
    cb = ConsensusBuilder()
    report = cb.build_report(mech_result, sem_results)

    # Render Output using Rich
    console.print("\n")
    if report.verdict == "APPROVED":
        panel_color = "green"
        status_icon = "✅"
    elif report.verdict == "AMBIGUOUS":
        panel_color = "yellow"
        status_icon = "⚠️"
    else:
        panel_color = "red"
        status_icon = "❌"

    console.print(
        Panel(
            f"[bold]Verdict: {report.verdict} {status_icon}[/bold]\n\n"
            f"Consensus Score: [bold]{report.consensus_score:.1f}/100.0[/bold]\n"
            f"Ambiguity Index: [bold]{report.ambiguity_index:.3f}[/bold]\n"
            f"Agreement Rate: {report.agreement_rate:.1f}%\n"
            f"Mechanical Health: {'[bold green]PASS[/bold green]' if report.mechanical_ok else '[bold red]FAIL[/bold red]'}",
            title="Ouroboros Consensus Summary",
            border_style=panel_color,
            expand=False,
        )
    )

    # Write report if requested
    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
            console.print(f"[green]Report saved successfully to: {output}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to save JSON output: {e}[/red]")

    # Print markdown contents for user visibility
    console.print("\n[bold]--- Report Detail ---[/bold]")
    console.print(report.summary_markdown)


if __name__ == "__main__":
    app()
