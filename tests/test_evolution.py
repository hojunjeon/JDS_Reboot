"""Unit tests for Ouroboros Lite Phase 5: Evolve (Evolution & Anti-Regression Engine)."""

import os
import pytest
from pathlib import Path
from typer.testing import CliRunner

from ouroboros.seed import SeedSpec, AcceptanceCriteria, save_to_yaml, load_from_yaml
from ouroboros.evolution import EvolutionEngine, FailureDiagnosis, EvolutionPatch
from ouroboros.cli import app

runner = CliRunner()


def test_evolution_rule_based_fallback():
    """Tests the rule-based fallback generation of patches when no LLM key is available."""
    failures = [
        FailureDiagnosis(
            category="MECHANICAL",
            source="broken_file.py",
            error_message="SyntaxError: invalid syntax",
        ),
        FailureDiagnosis(
            category="SEMANTIC",
            source="Type Safety",
            error_message="Function signatures lack explicit parameter annotations.",
        ),
        FailureDiagnosis(
            category="STAGNATION",
            source="stagnation detection",
            error_message="Workspace metric flatlined (NO_DRIFT).",
        ),
    ]

    engine = EvolutionEngine()
    # Force fallback by mocking API keys to empty
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["ANTHROPIC_API_KEY"] = ""

    patches = engine.generate_patches(failures)

    assert len(patches) == 3

    # Assert mechanical patch properties
    assert "broken_file.py" in patches[0].constraint
    assert "broken_file.py" in patches[0].session_rule

    # Assert semantic patch properties
    assert "Type Safety" in patches[1].constraint
    assert "Type Safety" in patches[1].session_rule

    # Assert stagnation patch properties
    assert "stagnation" in patches[2].constraint.lower()
    assert "stagnation" in patches[2].session_rule.lower()


def test_evolution_diagnostics_and_patching(tmp_path):
    """Tests diagnosis of syntax errors and applying patches to target yaml and AGENTS.md."""
    # 1. Setup temporary targets
    seed_file = tmp_path / "test_seed.yaml"
    agents_file = tmp_path / "TEST_AGENTS.md"

    # Create fake seed
    spec = SeedSpec(
        title="Test Survival Project",
        description="A simple wave defense shooter",
        constraints=[" Phaser 3 must be used."],
    )
    save_to_yaml(spec, seed_file)

    # Create fake AGENTS.md
    agents_content = (
        "# Test Session Rules\n\n## RULE 1: Workspace root\nSome rule content here.\n"
    )
    agents_file.write_text(agents_content, encoding="utf-8")

    # 2. Diagnose a fake syntax error
    bad_python_file = tmp_path / "bad_syntax.py"
    bad_python_file.write_text(
        "def hello(\n    pass\n", encoding="utf-8"
    )  # Syntax Error

    engine = EvolutionEngine(seed_path=str(seed_file), agents_path=str(agents_file))

    failures = engine.diagnose_workspace(
        [str(bad_python_file)], test_path="invalid_test_dir"
    )

    assert len(failures) >= 1
    syntax_failure = next((f for f in failures if f.source == "bad_syntax.py"), None)
    assert syntax_failure is not None
    assert syntax_failure.category == "MECHANICAL"
    assert "Syntax Error" in syntax_failure.error_message

    # 3. Apply evolution patches
    patches = engine.generate_patches(failures)
    yaml_patched, agents_patched = engine.apply_patches(patches)

    assert yaml_patched > 0
    assert agents_patched > 0

    # Verify yaml constraints list updated
    updated_spec = load_from_yaml(seed_file)
    assert len(updated_spec.constraints) > 1
    assert any("bad_syntax.py" in c for c in updated_spec.constraints)

    # Verify AGENTS.md was patched with ## Anti-Regression Rules section
    updated_agents = agents_file.read_text(encoding="utf-8")
    assert "## Anti-Regression Rules" in updated_agents
    assert "bad_syntax.py" in updated_agents


def test_evolution_cli_integration(tmp_path):
    """Tests Typer CLI integration of the evolve command with clear system health."""
    # Create valid seed to pass verification checks
    seed_file = tmp_path / "test_seed.yaml"
    spec = SeedSpec(
        title="Valid project", description="Just for testing", constraints=[]
    )
    save_to_yaml(spec, seed_file)

    # Invoke CLI evolve command
    result = runner.invoke(
        app,
        [
            "evolve",
            "--seed",
            str(seed_file),
            "--tests",
            "invalid_tests_dir",  # skip tests
        ],
    )

    # Cli executes successfully
    assert result.exit_code == 0
    # Rich UI outputs clear panel
    assert "Evolution Succeeded" in result.stdout or "Ouroboros" in result.stdout
