"""Verification script to test the core config and seed implementation.

This runs a round-trip serialization check on our Acceptance Criteria tree
and verifies that the robust LLM fallback mechanism works cleanly.
"""

import os
from ouroboros.config import call_llm
from ouroboros.seed import create_default_seed, save_to_yaml, load_from_yaml


def test_config_fallback():
    print("=== Testing config.py / call_llm (Fallback Mode) ===")
    prompt = "Please explain the Double Diamond phase details and socratic clarification questions for Phase 0."
    response = call_llm(prompt=prompt, provider=None)
    print("Prompt:")
    print(prompt)
    print("\nGenerated Fallback Response:")
    print(response)
    print("-" * 50)
    assert (
        "Socratic" in response
        or "Double Diamond" in response
        or "[Fallback Mock Response]" in response
    )
    print("config.py Fallback verification: PASSED\n")


def test_seed_serialization():
    print("=== Testing seed.py (Pydantic & YAML Roundtrip) ===")
    spec = create_default_seed()

    yaml_filename = "test_ouroboros_seed.yaml"
    if os.path.exists(yaml_filename):
        os.remove(yaml_filename)

    print(f"Serializing default SeedSpec to '{yaml_filename}'...")
    save_to_yaml(spec, yaml_filename)

    print(f"Deserializing from '{yaml_filename}'...")
    loaded_spec = load_from_yaml(yaml_filename)

    print(f"Title: {loaded_spec.title}")
    print(f"Description: {loaded_spec.description}")
    print(f"Number of constraints: {len(loaded_spec.constraints)}")
    print(
        f"Number of architecture decisions: {len(loaded_spec.architecture_decisions)}"
    )
    print(f"Number of top-level ACs: {len(loaded_spec.acceptance_criteria_tree)}")

    # Assert correctness
    assert loaded_spec.title == spec.title
    assert len(loaded_spec.acceptance_criteria_tree) == len(
        spec.acceptance_criteria_tree
    )
    assert loaded_spec.acceptance_criteria_tree[0].id == 100
    assert len(loaded_spec.acceptance_criteria_tree[0].children) == 2
    assert loaded_spec.acceptance_criteria_tree[0].children[0].id == 101

    # Clean up test file
    if os.path.exists(yaml_filename):
        os.remove(yaml_filename)

    print("seed.py Roundtrip verification: PASSED\n")


if __name__ == "__main__":
    test_config_fallback()
    test_seed_serialization()
    print("All core tests executed successfully.")
