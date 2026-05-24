"""Acceptance Criteria (AC) tree and Seed Specification models.

This module leverages Pydantic for high-fidelity modeling of recursively nested
Acceptance Criteria, constraints, and architecture decisions. It also provides
standard serialization/deserialization utilities to YAML files ('ouroboros_seed.yaml').
"""

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import yaml

class AcceptanceCriteria(BaseModel):
    """Represents a single Acceptance Criterion in a hierarchical tree.

    Attributes:
        id: Unique identifier for the criterion (integer).
        description: Readable details of what must be verified.
        status: Current state of validation (pending, in_progress, passed, failed).
        depends_on: List of parent AC IDs that this criterion depends on.
        children: Sub-criteria that further specify this criterion.
    """
    id: int
    description: str
    status: Literal["pending", "in_progress", "passed", "failed"] = "pending"
    depends_on: List[int] = Field(default_factory=list)
    children: List["AcceptanceCriteria"] = Field(default_factory=list)


# Support self-referential Pydantic recursive definition
AcceptanceCriteria.model_rebuild()


class SeedSpec(BaseModel):
    """The complete seed specification representing Phase 0/1 output.

    Attributes:
        title: The name of the project or feature spec.
        description: A concise summary of the system capabilities.
        acceptance_criteria_tree: Hierarchy of validation goals.
        constraints: Fundamental technical or business boundaries.
        architecture_decisions: Key design choices mapped by their identifier.
    """
    title: str
    description: str
    acceptance_criteria_tree: List[AcceptanceCriteria] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    architecture_decisions: Dict[str, Any] = Field(default_factory=dict)


def load_from_yaml(filepath: str = "ouroboros_seed.yaml") -> SeedSpec:
    """Deserializes a YAML file into a typed SeedSpec model.

    Args:
        filepath: Path to the YAML specification file.

    Returns:
        A fully-validated SeedSpec instance.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"YAML file at '{filepath}' is empty or invalid.")
    return SeedSpec.model_validate(data)


def save_to_yaml(spec: SeedSpec, filepath: str = "ouroboros_seed.yaml") -> None:
    """Serializes a SeedSpec model into a beautifully-formatted YAML file.

    Args:
        spec: The SeedSpec instance to serialize.
        filepath: Destination path of the YAML file.
    """
    data = spec.model_dump()
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data, 
            f, 
            sort_keys=False, 
            allow_unicode=True, 
            indent=2, 
            default_flow_style=False
        )


def create_default_seed() -> SeedSpec:
    """Generates a default SeedSpec tailored to the Debug Survival game."""
    # Top-level acceptance criteria
    ac1 = AcceptanceCriteria(
        id=100,
        description="The game starts from a Monospace/Terminal styled menu scene.",
        status="pending",
        depends_on=[],
        children=[
            AcceptanceCriteria(
                id=101,
                description="Menu provides 'Start Game' and 'Stage Selection' command inputs.",
                status="pending",
                depends_on=[100]
            ),
            AcceptanceCriteria(
                id=102,
                description="Terminal boot-up sequence animation plays upon launching.",
                status="pending",
                depends_on=[100]
            )
        ]
    )

    ac2 = AcceptanceCriteria(
        id=200,
        description="The active play field is controlled by keyboard controls.",
        status="pending",
        depends_on=[],
        children=[
            AcceptanceCriteria(
                id=201,
                description="Arrow keys and WASD shift the player character continuously in 2D space.",
                status="pending",
                depends_on=[200]
            ),
            AcceptanceCriteria(
                id=202,
                description="Collision boundaries prevent the player from moving outside the terminal window canvas.",
                status="pending",
                depends_on=[200]
            )
        ]
    )

    ac3 = AcceptanceCriteria(
        id=300,
        description="Weapons execute auto-fire cycles targeting local bug monsters.",
        status="pending",
        depends_on=[200],
        children=[]
    )

    return SeedSpec(
        title="Jiyoon Debug Survival",
        description="A 2D wave survival action game set in a corrupted IDE where programming bugs are monsters.",
        acceptance_criteria_tree=[ac1, ac2, ac3],
        constraints=[
            "Phaser 3 framework must be used for all scene management and rendering pipelines.",
            "All graphics should use retro ASCII / terminal visual aesthetic styles.",
            "Game must execute perfectly inside standard modern browsers without native installs."
        ],
        architecture_decisions={
            "AD-001": {
                "Title": "Phaser 3 Game Engine Selection",
                "Status": "Accepted",
                "Rationale": "Phaser 3 provides robust rendering speed and high-level 2D abstraction ideal for WebGL/Canvas deployment."
            },
            "AD-002": {
                "Title": "Stateless Simulator Isolation",
                "Status": "Accepted",
                "Rationale": "Separating state ticking from Phaser rendering cycles ensures that pure simulation code is easily unit-tested."
            }
        }
    )
