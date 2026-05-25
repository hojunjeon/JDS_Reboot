"""Ouroboros Evolution and Anti-Regression Framework.

Diagnoses failures from Mechanical, Semantic, and Stagnation checks,
generates permanent specifications and session rule patches,
and writes them back to prevent these problems from ever reoccurring.
"""

import os
import re
import sys
import json
import time
import yaml
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

# Core Ouroboros imports
from ouroboros.seed import load_from_yaml, save_to_yaml
from ouroboros.evaluation import MechanicalEvaluator, SemanticEvaluator
from ouroboros.resilience import StagnationDetector, load_history


class FailureDiagnosis(BaseModel):
    """Diagnosed failure containing details of what went wrong."""

    category: str = Field(description="MECHANICAL, SEMANTIC, or STAGNATION")
    source: str = Field(
        description="Name of the file, test, requirement, or pattern causing failure"
    )
    error_message: str = Field(
        description="Detailed error trace, stdout, or description of failure"
    )


class EvolutionPatch(BaseModel):
    """Concrete system patches generated to prevent failure recurrence."""

    constraint: str = Field(
        description="A system constraint to append to ouroboros_seed.yaml"
    )
    session_rule: str = Field(
        description="An anti-regression rule to append to AGENTS.md"
    )
    explanation: str = Field(
        description="Analytical justification for why this patch prevents future failure"
    )


class EvolutionEngine:
    """Core engine driving Phase 5: Evolution and Anti-Regression Patching."""

    def __init__(
        self,
        seed_path: str = "ouroboros_seed.yaml",
        agents_path: str = "AGENTS.md",
        history_path: str = ".ouroboros_history.json",
    ):
        self.seed_path = seed_path
        self.agents_path = agents_path
        self.history_path = history_path

    def diagnose_workspace(
        self, files: List[str], test_path: str = "tests"
    ) -> List[FailureDiagnosis]:
        """Runs mechanical, semantic, and stagnation evaluations to isolate all failure patterns."""
        failures = []

        # 1. Mechanical diagnosis
        me = MechanicalEvaluator()
        mech_res = me.evaluate(files, test_path=test_path)

        if not mech_res.compile_success:
            for f, err in mech_res.compile_details.items():
                if "Syntax Error" in err:
                    failures.append(
                        FailureDiagnosis(
                            category="MECHANICAL",
                            source=os.path.basename(f),
                            error_message=err,
                        )
                    )

        if mech_res.tests_passed is False:
            failures.append(
                FailureDiagnosis(
                    category="MECHANICAL",
                    source="pytest suite",
                    error_message=mech_res.tests_stderr
                    or mech_res.tests_stdout
                    or "Unit test execution failed.",
                )
            )

        if mech_res.lint_passed is False:
            failures.append(
                FailureDiagnosis(
                    category="MECHANICAL",
                    source="linter / style checks",
                    error_message=mech_res.lint_output
                    or "Style compliance check failed.",
                )
            )

        # 2. Semantic diagnosis
        if os.path.exists(self.seed_path):
            se = SemanticEvaluator(seed_path=self.seed_path)
            # Use raw regex fallback checklist review to identify unsatisfied items deterministically
            se._call_llm = lambda prompt, sys_prompt: None
            sem_res = se.evaluate(files)

            for status in sem_res.requirements_statuses:
                if not status.satisfied:
                    failures.append(
                        FailureDiagnosis(
                            category="SEMANTIC",
                            source=status.requirement,
                            error_message=status.reasoning,
                        )
                    )

        # 3. Stagnation diagnosis
        if os.path.exists(self.history_path):
            history = load_history(self.history_path)
            detector = StagnationDetector()
            report = detector.analyze(history)

            if report.stagnation_detected:
                patterns = []
                if report.spinning_detected:
                    patterns.append(
                        f"SPINNING (identical file repeating: {', '.join(report.spinning_files)})"
                    )
                if report.oscillation_detected:
                    patterns.append(
                        f"OSCILLATION (alternating cycles: {', '.join(report.oscillation_files)})"
                    )
                if report.nodrift_detected:
                    patterns.append(
                        f"NO_DRIFT (metric flatline with drift range {report.drift_range})"
                    )

                failures.append(
                    FailureDiagnosis(
                        category="STAGNATION",
                        source="stagnation detection",
                        error_message=f"Codebase drift stalled due to active patterns: {', '.join(patterns)}",
                    )
                )

        return failures

    def generate_patches(
        self, failures: List[FailureDiagnosis]
    ) -> List[EvolutionPatch]:
        """Calls the LLM (or falls back to an elite template generator) to synthesize anti-regression rules."""
        if not failures:
            return []

        openai_key = os.environ.get("OPENAI_API_KEY")
        gemini_key = os.environ.get("GEMINI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        patches = []

        if openai_key or gemini_key or anthropic_key:
            # Prepare LLM call
            from ouroboros.evaluation import SemanticEvaluator

            se = SemanticEvaluator()

            llm_system = (
                "You are Ouroboros Evolution Engine, an expert AI systems designer.\n"
                "Analyze the provided list of development failures. For each failure, construct a permanent system-level patch.\n"
                "Each patch must contain:\n"
                " 1. constraint: A project-wide constraint to prevent this bug/failure from ever repeating (e.g. 'Must use Phaser 3 unique scene keys to prevent scene registration overlaps').\n"
                " 2. session_rule: A binding session rule to append to AGENTS.md (e.g. 'RULE: Always verify Phaser 3 scene names and keys are registered uniquely in the scene class definition').\n"
                " 3. explanation: Concise technical reasoning explaining how these rule and constraint changes eliminate this type of failure.\n"
                'Respond ONLY with a valid JSON array of objects with these keys: ["constraint", "session_rule", "explanation"]. No markdown wrapping or other text.'
            )

            prompt = json.dumps([f.model_dump() for f in failures], indent=2)
            llm_response = se._call_llm(prompt, llm_system)

            if llm_response:
                try:
                    clean_json = llm_response.strip()
                    if clean_json.startswith("```"):
                        clean_json = re.sub(
                            r"^```(?:json)?\n|```$", "", clean_json, flags=re.MULTILINE
                        ).strip()

                    parsed = json.loads(clean_json)
                    for item in parsed:
                        patches.append(EvolutionPatch(**item))
                except Exception as e:
                    print(
                        f"[Evolution Engine Warning] LLM parse failed: {e}. Falling back to Rule-Based templates."
                    )
                    patches = []

        # Rule-Based template fallback
        if not patches:
            for f in failures:
                constraint = ""
                session_rule = ""
                explanation = ""

                if f.category == "MECHANICAL":
                    if "syntax" in f.error_message.lower():
                        constraint = f"Python modules in the codebase must strictly compile under PEP 8 and avoid compilation or syntax errors in {f.source}."
                        session_rule = f"RULE: Before saving or submitting code in '{f.source}', always run standard syntax checks or python compilation checks to verify 0 syntax bugs."
                        explanation = f"Adds a compilation check rule to prevent syntactically broken code from ever being committed to '{f.source}'."
                    elif "pytest" in f.source:
                        constraint = "All unit tests in the tests/ directory must run cleanly and return exit code 0."
                        session_rule = "RULE: Ensure the automated setup suite and all tests in tests/ pass cleanly prior to completing development checkpoints."
                        explanation = "Enforces a strict automated test pass constraint to stop regressions before they hit production."
                    else:
                        constraint = "Python modules must conform to lint standards, passing style checks without trailing whitespace or formatting warnings."
                        session_rule = "RULE: Run black or stylistic linters to verify zero format warnings before saving changes."
                        explanation = "Guarantees aesthetic clean code structure by enforcing linter compliance."

                elif f.category == "SEMANTIC":
                    constraint = f"Core implementation must explicitly implement and successfully satisfy the requirement: {f.source}."
                    session_rule = f"RULE: Prioritize complete functional verification of requirement '{f.source}' by mapping appropriate test units and checking compliance."
                    explanation = f"Upgrades requirement '{f.source}' to a permanent system-wide constraint, forcing subsequent iterations to implement it."

                else:  # STAGNATION
                    constraint = "Avoid developmental loops and maintain progressive performance/metrics improvements without stagnation or spinning."
                    session_rule = "RULE: If stagnation (SPINNING or OSCILLATION) is detected, immediately rotate developer personas and apply a Simplifier or Contrarian approach."
                    explanation = "Enforces developer persona rotation rules to disrupt local developmental loops."

                patches.append(
                    EvolutionPatch(
                        constraint=constraint,
                        session_rule=session_rule,
                        explanation=explanation,
                    )
                )

        return patches

    def apply_patches(self, patches: List[EvolutionPatch]) -> Tuple[int, int]:
        """Appends constraints to yaml specification and anti-regression rules to AGENTS.md."""
        yaml_count = 0
        agents_count = 0

        if not patches:
            return 0, 0

        # 1. Patch ouroboros_seed.yaml constraints
        if os.path.exists(self.seed_path):
            try:
                spec = load_from_yaml(self.seed_path)
                existing_constraints = [c.lower() for c in spec.constraints]

                for p in patches:
                    if p.constraint.lower() not in existing_constraints:
                        spec.constraints.append(p.constraint)
                        yaml_count += 1

                if yaml_count > 0:
                    save_to_yaml(spec, self.seed_path)
            except Exception as e:
                print(f"[Evolution Engine Error] Failed to patch seed YAML: {e}")

        # 2. Patch AGENTS.md anti-regression rules
        if os.path.exists(self.agents_path):
            try:
                with open(self.agents_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Build rules content
                new_rules_text = []
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                for p in patches:
                    rule_line = f"- **Anti-Regression Patch [{timestamp}]**: {p.session_rule} *(Reason: {p.explanation})*"
                    # Avoid appending duplicate rules
                    if p.session_rule not in content:
                        new_rules_text.append(rule_line)
                        agents_count += 1

                if agents_count > 0:
                    # Look for ## Anti-Regression Rules section or create one
                    section_header = "## Anti-Regression Rules"
                    if section_header in content:
                        # Append to existing section
                        pattern = re.compile(
                            rf"({section_header}.*?)(?=\n##|$)", re.DOTALL
                        )
                        match = pattern.search(content)
                        if match:
                            section_content = match.group(1).rstrip()
                            updated_section = (
                                section_content
                                + "\n"
                                + "\n".join(new_rules_text)
                                + "\n"
                            )
                            content = content.replace(section_content, updated_section)
                    else:
                        # Append to the end of the file
                        content = (
                            content.rstrip()
                            + "\n\n"
                            + section_header
                            + "\n\n"
                            + "\n".join(new_rules_text)
                            + "\n"
                        )

                    with open(self.agents_path, "w", encoding="utf-8") as f:
                        f.write(content)
            except Exception as e:
                print(f"[Evolution Engine Error] Failed to patch AGENTS.md: {e}")

        return yaml_count, agents_count

    def generate_report(
        self,
        failures: List[FailureDiagnosis],
        patches: List[EvolutionPatch],
        yaml_patched: int,
        agents_patched: int,
    ) -> str:
        """Constructs a stunning markdown report detailing diagnosed errors and implemented patches."""
        markdown = []
        markdown.append("# 🧬 Ouroboros Evolution & Anti-Regression Report\n")
        markdown.append(
            f"> [!IMPORTANT]\n> **Ouroboros self-healed!** Retrospectively patched the system specifications to prevent future failures.\n"
        )

        markdown.append("## 🔍 Diagnosed System Failures")
        markdown.append(
            f"Found **{len(failures)}** active failure patterns across current development stages:\n"
        )

        for idx, f in enumerate(failures, 1):
            markdown.append(f"### {idx}. [{f.category}] {f.source}")
            markdown.append(f"```text\n{f.error_message}\n```\n")

        markdown.append("## 🛡️ Anti-Regression Rules & Constraints Patches")
        markdown.append(
            f"Successfully generated **{len(patches)}** permanent system modifications:\n"
        )

        for idx, p in enumerate(patches, 1):
            markdown.append(f"### Patch {idx}: {p.explanation}")
            markdown.append(f'- **System Constraint**: *"{p.constraint}"*')
            markdown.append(f'- **Binding Session Rule**: *"{p.session_rule}"*\n')

        markdown.append("## 💾 Files Update Summary")
        markdown.append(
            f"- `ouroboros_seed.yaml`: Added **{yaml_patched}** new constraints."
        )
        markdown.append(
            f"- `AGENTS.md`: Added **{agents_patched}** new anti-regression rules.\n"
        )

        return "\n".join(markdown)
