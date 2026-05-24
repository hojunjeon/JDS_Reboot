"""Unit tests for Ouroboros Lite Seed parsing and Double Diamond planning.
"""

import pytest
from pathlib import Path
from ouroboros.seed import SeedSpec, AcceptanceCriteria, save_to_yaml, load_from_yaml
from ouroboros.execution import DoubleDiamondPlanner, classify_ac_phase
from ouroboros.resilience import (
    StagnationDetector,
    LateralAdvisor,
    StepState,
    FileState,
    StagnationReport
)
from ouroboros.evaluation import (
    MechanicalEvaluator,
    SemanticEvaluator,
    ConsensusBuilder,
    MechanicalEvaluationResult,
    SemanticEvaluationResult,
    RequirementStatus
)

def test_seed_spec_serialization(tmp_path):
    yaml_file = tmp_path / "ouroboros_seed.yaml"
    
    criteria = [
        AcceptanceCriteria(id=100, description="Discover phase requirements", depends_on=[]),
        AcceptanceCriteria(id=101, description="Define scope", depends_on=[100]),
        AcceptanceCriteria(id=102, description="Design architecture", depends_on=[101]),
        AcceptanceCriteria(id=103, description="Implement code and evaluate", depends_on=[102]),
    ]
    spec = SeedSpec(
        title="Jiyoon Debug Survival",
        description="A 2D wave survival action game",
        acceptance_criteria_tree=criteria,
        constraints=["Must use Python 3.12", "Must not use external databases"],
        architecture_decisions={}
    )
    
    save_to_yaml(spec, yaml_file)
    
    # Reload and check
    loaded = load_from_yaml(yaml_file)
    assert loaded.title == "Jiyoon Debug Survival"
    assert len(loaded.constraints) == 2
    assert len(loaded.acceptance_criteria_tree) == 4
    assert loaded.acceptance_criteria_tree[0].id == 100
    assert loaded.acceptance_criteria_tree[1].depends_on == [100]

def test_topological_sort_no_cycle(tmp_path):
    yaml_file = tmp_path / "ouroboros_seed.yaml"
    
    criteria = [
        AcceptanceCriteria(id=100, description="Research and Socratic interview", depends_on=[]),
        AcceptanceCriteria(id=200, description="Define schema", depends_on=[100]),
        AcceptanceCriteria(id=300, description="Architecture design", depends_on=[]),
        AcceptanceCriteria(id=400, description="Implement and test", depends_on=[200, 300]),
    ]
    spec = SeedSpec(title="Test DAG", description="Test Desc", acceptance_criteria_tree=criteria)
    save_to_yaml(spec, yaml_file)
    
    planner = DoubleDiamondPlanner(yaml_file)
    levels, has_cycle = planner.plan()
    
    assert not has_cycle
    assert len(levels) == 3
    
    # Level 1: 100 and 300
    level_1_ids = [ac.id for ac in levels[0]]
    assert 100 in level_1_ids
    assert 300 in level_1_ids
    assert len(level_1_ids) == 2
    
    # Level 2: 200
    level_2_ids = [ac.id for ac in levels[1]]
    assert level_2_ids == [200]
    
    # Level 3: 400
    level_3_ids = [ac.id for ac in levels[2]]
    assert level_3_ids == [400]

def test_topological_sort_with_cycle(tmp_path):
    yaml_file = tmp_path / "ouroboros_seed.yaml"
    
    criteria = [
        AcceptanceCriteria(id=100, description="Research phase", depends_on=[300]),
        AcceptanceCriteria(id=200, description="Define phase", depends_on=[100]),
        AcceptanceCriteria(id=300, description="Design phase", depends_on=[200]),
    ]
    spec = SeedSpec(title="Test Cycle", description="Test Desc", acceptance_criteria_tree=criteria)
    save_to_yaml(spec, yaml_file)
    
    planner = DoubleDiamondPlanner(yaml_file)
    levels, has_cycle = planner.plan()
    
    assert has_cycle
    assert len(levels) == 3
    assert levels[0][0].id == 100
    assert levels[1][0].id == 200
    assert levels[2][0].id == 300

def test_phase_classification():
    # Test keyword matching
    ac_discover = AcceptanceCriteria(id=100, description="Conduct socratic interview and clarify ambiguity")
    assert classify_ac_phase(ac_discover, 4, 3) == "Discover"
    
    ac_define = AcceptanceCriteria(id=200, description="Establish criteria limits and system boundaries")
    assert classify_ac_phase(ac_define, 4, 3) == "Define"
    
    ac_design = AcceptanceCriteria(id=300, description="Draw structural layout and database design blueprints")
    assert classify_ac_phase(ac_design, 4, 0) == "Design"
    
    ac_deliver = AcceptanceCriteria(id=400, description="Write final python cli execution and verify compliance")
    assert classify_ac_phase(ac_deliver, 4, 0) == "Deliver"
    
    # Test fallback based on levels
    ac_fallback_first = AcceptanceCriteria(id=500, description="Generic item")
    assert classify_ac_phase(ac_fallback_first, 4, 0) == "Discover"
    
    ac_fallback_second = AcceptanceCriteria(id=600, description="Generic item")
    assert classify_ac_phase(ac_fallback_second, 4, 1) == "Define"
    
    ac_fallback_third = AcceptanceCriteria(id=700, description="Generic item")
    assert classify_ac_phase(ac_fallback_third, 4, 2) == "Design"
    
    ac_fallback_fourth = AcceptanceCriteria(id=800, description="Generic item")
    assert classify_ac_phase(ac_fallback_fourth, 4, 3) == "Deliver"

def test_generate_plan_markdown(tmp_path):
    yaml_file = tmp_path / "ouroboros_seed.yaml"
    output_plan = tmp_path / "ouroboros_plan.md"
    
    criteria = [
        AcceptanceCriteria(id=100, description="Research details", depends_on=[]),
        AcceptanceCriteria(id=200, description="Define rules", depends_on=[100]),
        AcceptanceCriteria(id=300, description="Mock wireframes", depends_on=[200]),
        AcceptanceCriteria(id=400, description="Implement and deploy", depends_on=[300]),
    ]
    spec = SeedSpec(title="Build a website", description="Simple site", acceptance_criteria_tree=criteria, constraints=["Constraint A"])
    save_to_yaml(spec, yaml_file)
    
    planner = DoubleDiamondPlanner(yaml_file)
    planner.write_plan(output_plan)
    
    assert output_plan.exists()
    content = output_plan.read_text(encoding="utf-8")
    
    assert "Ouroboros Lite Double Diamond Execution Plan" in content
    assert "Build a website" in content
    assert "Constraint A" in content
    assert "graph TD" in content
    assert "AC100" in content
    assert "AC200" in content
    assert "Discover" in content
    assert "Define" in content
    assert "Design" in content
    assert "Deliver" in content
    assert "Level 1" in content


# --- Ouroboros Evaluation & Resilience Tests ---

def test_mechanical_syntax_checking(tmp_path):
    """Tests syntax checking on valid and invalid Python source files."""
    valid_file = tmp_path / "valid.py"
    valid_file.write_text("def hello(name: str) -> str:\n    return f'Hello {name}'\n", encoding="utf-8")
    
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("def hello(name:\n    return f'Hello'\n", encoding="utf-8")  # syntax error
    
    success, details = MechanicalEvaluator.check_syntax([str(valid_file), str(invalid_file)])
    
    assert success is False
    assert details[str(valid_file)] == "OK"
    assert "Syntax Error" in details[str(invalid_file)]


def test_mechanical_linter_fallback(tmp_path):
    """Tests style fallback when Black/Flake8 are bypassed or unavailable."""
    bad_style_file = tmp_path / "bad_style.py"
    bad_style_file.write_text("a = 1  \n", encoding="utf-8")  # trailing whitespace
    
    me = MechanicalEvaluator()
    success, output = me.run_linter([str(bad_style_file)])
    assert isinstance(success, bool)
    assert isinstance(output, str)


def test_semantic_regex_checklist():
    """Tests that the regex-based semantic checker correctly scans code constructs."""
    se = SemanticEvaluator()
    
    good_code = {
        "main.py": (
            "from pydantic import BaseModel, Field\n\n"
            "class Configuration(BaseModel):\n"
            "    name: str = Field(description='The name')\n\n"
            "def run_engine(steps: List[int]) -> bool:\n"
            "    # Code contains no placeholders\n"
            "    return True\n"
        )
    }
    
    type_req = {"name": "Type Safety", "description": "All python code must be fully-typed with return types and parameters annotated", "pattern": "type_safety"}
    type_status = se._regex_check_file(type_req, good_code)
    assert type_status.satisfied is True
    assert type_status.confidence >= 0.8
    
    placeholder_req = {"name": "No Placeholders", "description": "No placeholders, empty ellipses (...), or TODO comments", "pattern": "no_placeholders"}
    placeholder_status = se._regex_check_file(placeholder_req, {"main.py": "def test():\n    pass\n"})
    assert placeholder_status.satisfied is False
    
    pydantic_req = {"name": "Pydantic usage", "description": "Use pydantic BaseModel class and Field definitions", "pattern": "pydantic_use"}
    pydantic_status = se._regex_check_file(pydantic_req, good_code)
    assert pydantic_status.satisfied is True


def test_consensus_ambiguity_calculation():
    """Tests the mathematical correctness of the Ambiguity Index and agreement rate."""
    votes_matrix = [
        [True, True],
        [True, False]
    ]
    
    agreement_rate, ambiguity_index = ConsensusBuilder.calculate_ambiguity_index(votes_matrix)
    assert agreement_rate == 50.0
    assert ambiguity_index == 0.5


def test_consensus_builder_report():
    """Tests the complete consensus building process and absolute veto logic."""
    cb = ConsensusBuilder()
    
    failed_mech = MechanicalEvaluationResult(
        compile_success=False,
        compile_details={"main.py": "Syntax Error"},
        overall_success=False
    )
    
    judge_res = [
        SemanticEvaluationResult(
            seed_file_path="seed.yaml",
            reviewed_files=["main.py"],
            requirements_statuses=[
                RequirementStatus(requirement="Req 1", satisfied=True, confidence=1.0, reasoning="OK")
            ],
            overall_score=100.0,
            passed=True,
            evaluator_type="REGEX"
        )
    ]
    
    report = cb.build_report(failed_mech, judge_res)
    assert report.verdict == "REJECTED"
    assert report.mechanical_ok is False
    assert report.consensus_score < 50.0


def test_stagnation_spinning():
    """Tests detection of SPINNING pattern: same file hash repeating 3 times."""
    history = [
        StepState(step_id=1, files=[FileState(filepath="a.py", content_hash="hash1")]),
        StepState(step_id=2, files=[FileState(filepath="a.py", content_hash="hash1")]),
        StepState(step_id=3, files=[FileState(filepath="a.py", content_hash="hash1")]),
    ]
    
    spinning, files = StagnationDetector.detect_spinning(history, threshold=3)
    assert spinning is True
    assert "a.py" in files


def test_stagnation_oscillation():
    """Tests detection of OSCILLATION pattern: alternating changes A->B->A->B over 2 cycles."""
    history = [
        StepState(step_id=1, files=[FileState(filepath="b.py", content_hash="hash1")]),
        StepState(step_id=2, files=[FileState(filepath="b.py", content_hash="hash2")]),
        StepState(step_id=3, files=[FileState(filepath="b.py", content_hash="hash1")]),
        StepState(step_id=4, files=[FileState(filepath="b.py", content_hash="hash2")]),
        StepState(step_id=5, files=[FileState(filepath="b.py", content_hash="hash1")]),
    ]
    
    oscillating, files = StagnationDetector.detect_oscillation(history, cycles=2)
    assert oscillating is True
    assert "b.py" in files


def test_stagnation_no_drift():
    """Tests detection of NO_DRIFT pattern: metric variance <= 0.01 over 3 steps."""
    history_stalled = [
        StepState(step_id=1, files=[], metric_value=0.850),
        StepState(step_id=2, files=[], metric_value=0.855),
        StepState(step_id=3, files=[], metric_value=0.852),
    ]
    
    stalled, drift = StagnationDetector.detect_no_drift(history_stalled, threshold_steps=3, delta=0.01)
    assert stalled is True
    assert pytest.approx(drift, 0.0001) == 0.005
    
    history_drifting = [
        StepState(step_id=1, files=[], metric_value=0.85),
        StepState(step_id=2, files=[], metric_value=0.87),
        StepState(step_id=3, files=[], metric_value=0.90),
    ]
    stalled_2, drift_2 = StagnationDetector.detect_no_drift(history_drifting, threshold_steps=3, delta=0.01)
    assert stalled_2 is False


def test_lateral_advisor_recommendations():
    """Tests advisor persona selection depending on exact stagnation triggers."""
    advisor = LateralAdvisor()
    
    report_osc = StagnationReport(
        spinning_detected=False,
        oscillation_detected=True,
        nodrift_detected=False,
        stagnation_detected=True
    )
    advice_osc = advisor.advise(report_osc)
    assert advice_osc.recommended_persona == "Simplifier"
    
    report_spin = StagnationReport(
        spinning_detected=True,
        oscillation_detected=False,
        nodrift_detected=False,
        stagnation_detected=True
    )
    advice_spin = advisor.advise(report_spin)
    assert advice_spin.recommended_persona == "Contrarian"
    
    report_drift = StagnationReport(
        spinning_detected=False,
        oscillation_detected=False,
        nodrift_detected=True,
        stagnation_detected=True
    )
    advice_drift = advisor.advise(report_drift)
    assert advice_drift.recommended_persona == "Hacker"
