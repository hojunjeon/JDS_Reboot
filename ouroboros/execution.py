"""Ouroboros Lite - Double Diamond Execution Planner and Kahn's Topological Sort.
"""

from typing import List, Tuple, Dict, Set, Optional
from pathlib import Path
import logging
from rich.console import Console

from ouroboros.seed import SeedSpec, AcceptanceCriteria, load_from_yaml

logger = logging.getLogger("ouroboros.execution")
console = Console()

def flatten_ac_tree(ac_list: List[AcceptanceCriteria]) -> List[AcceptanceCriteria]:
    """Recursively flattens the acceptance criteria tree into a flat list of items."""
    flat = []
    for ac in ac_list:
        flat.append(ac)
        if ac.children:
            flat.extend(flatten_ac_tree(ac.children))
    return flat

def sanitize_mermaid_label(text: str) -> str:
    """Sanitizes text to make it safe for Mermaid node labels."""
    clean = text.replace('"', "'").replace('[', '(').replace(']', ')')
    if len(clean) > 50:
        clean = clean[:47] + "..."
    return clean

def generate_mermaid_diagram(criteria: List[AcceptanceCriteria]) -> str:
    """Generates a Mermaid dependency diagram from the acceptance criteria list."""
    lines = ["graph TD"]
    all_ids = {ac.id for ac in criteria}
    
    for ac in criteria:
        label = sanitize_mermaid_label(ac.description)
        lines.append(f'    AC{ac.id}["AC{ac.id}: {label}"]')
        for dep in ac.depends_on:
            if dep in all_ids:
                lines.append(f"    AC{dep} --> AC{ac.id}")
                
    return "\n".join(lines)

def classify_ac_phase(ac: AcceptanceCriteria, total_levels: int, ac_level: int) -> str:
    """Classifies an Acceptance Criterion into one of the four Double Diamond phases.
    
    Classification rules:
    - Check description/id keywords:
       - Discover: research, interview, clarify, goal, problem, question, socratic, explore, discover, ambiguity
       - Define: spec, define, requirement, criteria, schema, model, scope, boundary, constraints
       - Design: design, architecture, mock, ui, ux, wireframe, plan, flowchart, diagram, layout, setup
       - Deliver: implement, code, develop, build, test, verify, evaluate, cli, integration, deploy, run, execution
    - If no keyword matches, use the topological level index relative to total levels:
       - level < total_levels * 0.25 -> Discover
       - level < total_levels * 0.50 -> Define
       - level < total_levels * 0.75 -> Design
       - otherwise -> Deliver
    """
    desc_lower = ac.description.lower()
    id_str = str(ac.id)
    
    # Discover keywords
    discover_kws = ["research", "interview", "clarify", "goal", "problem", "question", "socratic", "explore", "discover", "ambiguity"]
    if any(kw in desc_lower or kw in id_str for kw in discover_kws):
        return "Discover"
        
    # Define keywords
    define_kws = ["spec", "define", "requirement", "criteria", "schema", "model", "scope", "boundary", "constraints"]
    if any(kw in desc_lower or kw in id_str for kw in define_kws):
        return "Define"
        
    # Design keywords
    design_kws = ["design", "architecture", "mock", "ui", "ux", "wireframe", "plan", "flowchart", "diagram", "layout", "setup"]
    if any(kw in desc_lower or kw in id_str for kw in design_kws):
        return "Design"
        
    # Deliver keywords
    deliver_kws = ["implement", "code", "develop", "build", "test", "verify", "evaluate", "cli", "integration", "deploy", "run", "execution"]
    if any(kw in desc_lower or kw in id_str for kw in deliver_kws):
        return "Deliver"
        
    # Fallback to level-based distribution
    if total_levels <= 1:
        return "Deliver"
    
    ratio = ac_level / total_levels
    if ratio < 0.25:
        return "Discover"
    elif ratio < 0.50:
        return "Define"
    elif ratio < 0.75:
        return "Design"
    else:
        return "Deliver"

class DoubleDiamondPlanner:
    """Planner that organizes Acceptance Criteria tree into dependency-aware parallel execution levels."""
    
    def __init__(self, spec_path: Path | str):
        self.spec_path = Path(spec_path)
        self.spec: Optional[SeedSpec] = None
        self.flat_criteria: List[AcceptanceCriteria] = []
        self.levels: List[List[AcceptanceCriteria]] = []
        self.has_cycle: bool = False
        self.ac_phases: Dict[int, str] = {}
        
    def load_spec(self) -> None:
        """Loads the specification from the seed spec path."""
        self.spec = load_from_yaml(str(self.spec_path))
        if self.spec:
            self.flat_criteria = flatten_ac_tree(self.spec.acceptance_criteria_tree)
        
    def plan(self) -> Tuple[List[List[AcceptanceCriteria]], bool]:
        """Runs Kahn's topological sort on flat ACs and categorizes into Double Diamond phases.
        
        Returns:
            A tuple of (levels, has_cycle) where levels is a list of levels (each level
            is a list of concurrent criteria) and has_cycle indicates if a cycle was found.
        """
        if not self.spec:
            self.load_spec()
            
        assert self.spec is not None
        criteria = self.flat_criteria
        
        if not criteria:
            self.levels = []
            self.has_cycle = False
            return self.levels, self.has_cycle
            
        all_ids = {ac.id for ac in criteria}
        ac_by_id = {ac.id: ac for ac in criteria}
        
        # Build adjacency list and compute in-degree
        adj_list: Dict[int, List[int]] = {ac.id: [] for ac in criteria}
        in_degree: Dict[int, int] = {ac.id: 0 for ac in criteria}
        
        for ac in criteria:
            for dep in ac.depends_on:
                if dep in all_ids:
                    adj_list[dep].append(ac.id)
                    in_degree[ac.id] += 1
                    
        # Find all vertices with in-degree 0
        queue = [ac_id for ac_id in all_ids if in_degree[ac_id] == 0]
        # Keep deterministic ordering based on original index in flattened list
        id_to_index = {ac.id: idx for idx, ac in enumerate(criteria)}
        queue.sort(key=lambda ac_id: id_to_index[ac_id])
        
        sorted_levels: List[List[AcceptanceCriteria]] = []
        sorted_count = 0
        
        while queue:
            current_level_ids = list(queue)
            queue.clear()
            
            level_ac: List[AcceptanceCriteria] = []
            for ac_id in current_level_ids:
                level_ac.append(ac_by_id[ac_id])
                sorted_count += 1
                
                for neighbor in adj_list[ac_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
                        
            # Keep level items deterministic based on original index
            level_ac.sort(key=lambda ac: id_to_index[ac.id])
            sorted_levels.append(level_ac)
            
            # Re-sort the queue deterministically
            queue.sort(key=lambda ac_id: id_to_index[ac_id])
            
        if sorted_count < len(criteria):
            # Cycle detected! Fall back to sequential execution
            self.has_cycle = True
            # Create sequential levels: each AC is its own level, in original order
            self.levels = [[ac] for ac in criteria]
            logger.warning("Dependency cycle detected in acceptance criteria! Falling back to sequential execution.")
        else:
            self.has_cycle = False
            self.levels = sorted_levels
            
        # Group and classify criteria into phases
        total_levels = len(self.levels)
        for level_idx, level in enumerate(self.levels):
            for ac in level:
                phase = classify_ac_phase(ac, total_levels, level_idx)
                self.ac_phases[ac.id] = phase
                
        return self.levels, self.has_cycle

    def generate_plan_markdown(self) -> str:
        """Generates a structured execution plan in Markdown."""
        if not self.spec:
            raise ValueError("Specification is not loaded or planned. Call plan() first.")
            
        criteria = self.flat_criteria
        total_tasks = len(criteria)
        num_levels = len(self.levels)
        concurrency_factor = (total_tasks / num_levels) if num_levels > 0 else 0.0
        
        md = []
        md.append("# Ouroboros Lite Double Diamond Execution Plan")
        md.append("")
        
        # 1. Executive Summary
        md.append("## Executive Summary")
        md.append("")
        md.append(f"**Primary Goal (Title):** {self.spec.title}")
        md.append(f"**Description:** {self.spec.description}")
        md.append("")
        md.append("### Planning Metrics")
        md.append(f"- **Total Acceptance Criteria (Tasks):** {total_tasks}")
        md.append(f"- **Total Parallel Execution Levels:** {num_levels}")
        md.append(f"- **Concurrency Factor (Avg Tasks/Level):** {concurrency_factor:.2f}")
        
        if self.has_cycle:
            md.append("- **Execution Mode:** Sequential (Fallback due to cycle detection)")
            md.append("")
            md.append("> [!WARNING]")
            md.append("> **Dependency Cycle Detected!**")
            md.append("> Ouroboros has detected a circular dependency in the acceptance criteria tree.")
            md.append("> The engine has gracefully fallen back to sequential execution. Please inspect your acceptance criteria dependencies in `ouroboros_seed.yaml` to unlock parallel level execution.")
        else:
            md.append("- **Execution Mode:** Parallel (Topological Sort optimized)")
        md.append("")
        
        # Constraints Section
        if self.spec.constraints:
            md.append("### System Constraints")
            for c in self.spec.constraints:
                md.append(f"- {c}")
            md.append("")
            
        # 2. Dependency Visualization
        if criteria:
            md.append("## Dependency Visualization")
            md.append("")
            md.append("```mermaid")
            md.append(generate_mermaid_diagram(criteria))
            md.append("```")
            md.append("")
            
        # 3. Double Diamond Phases Breakdown
        md.append("## Double Diamond Phase Breakdown")
        md.append("")
        md.append("The Double Diamond consists of four stages: Discover (understanding the problem), Define (scope and specifications), Design (technical and UI architecture), and Deliver (implementation and evaluation).")
        md.append("")
        
        phases = ["Discover", "Define", "Design", "Deliver"]
        phase_descriptions = {
            "Discover": "Initial research, requirement gathering, and Socratic clarification of goals.",
            "Define": "Scoping, boundary definition, constraint cataloging, and precise spec definition.",
            "Design": "Technical blueprinting, data modeling, algorithm design, and UI architecture.",
            "Deliver": "Implementation, test-driven validation, and final mechanical and semantic compliance check."
        }
        
        for phase in phases:
            md.append(f"### Phase: {phase}")
            md.append(f"*{phase_descriptions[phase]}*")
            md.append("")
            
            # Find all tasks in this phase and group them by level index
            phase_tasks = []
            for lvl_idx, level in enumerate(self.levels):
                for ac in level:
                    if self.ac_phases.get(ac.id) == phase:
                        phase_tasks.append((lvl_idx + 1, ac))
                        
            if not phase_tasks:
                md.append("*(No tasks assigned to this phase)*")
                md.append("")
                continue
                
            md.append("| Task ID | Level | Description | Dependencies |")
            md.append("| --- | --- | --- | --- |")
            for lvl_num, ac in phase_tasks:
                deps_str = ", ".join(f"AC{d}" for d in ac.depends_on) if ac.depends_on else "None"
                desc_clean = ac.description.replace("\n", " ").strip()
                md.append(f"| `AC{ac.id}` | L{lvl_num} | {desc_clean} | `{deps_str}` |")
            md.append("")
            
        # 4. Master Parallel Execution Levels
        md.append("## Master Step-by-Step Execution Path")
        md.append("")
        md.append("Developers or subagents should execute these levels sequentially. However, **all tasks within a single level can be executed concurrently** because their dependencies have been satisfied.")
        md.append("")
        
        for lvl_idx, level in enumerate(self.levels):
            lvl_num = lvl_idx + 1
            md.append(f"### Level {lvl_num}")
            if self.has_cycle:
                md.append("*(Sequential execution fallback)*")
            else:
                concurrency_count = len(level)
                md.append(f"*(Parallel execution enabled: **{concurrency_count}** concurrent tasks)*")
            md.append("")
            
            for ac in level:
                phase = self.ac_phases.get(ac.id, "Deliver")
                deps_str = f" (requires {', '.join(f'AC{d}' for d in ac.depends_on)})" if ac.depends_on else ""
                md.append(f"- [ ] **`AC{ac.id}`** [{phase}]: {ac.description}{deps_str}")
            md.append("")
            
        return "\n".join(md)

    def write_plan(self, output_path: Path | str) -> None:
        """Runs the planner and writes the final execution plan file in Markdown."""
        self.plan()
        plan_md = self.generate_plan_markdown()
        
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(plan_md)
            
        logger.info(f"Successfully generated execution plan at: {out_path.resolve()}")
