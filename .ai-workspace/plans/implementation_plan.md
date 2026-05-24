# Implementation Plan — Ouroboros Lite Evolve Phase (Phase 5)

This plan outlines the architecture, design, and implementation of **Phase 5: Evolve (Evolution)** in Ouroboros Lite. The goal is to build an automated, retroactive anti-regression engine that analyzes development failures, linter issues, test breaks, and stagnation patterns, and patches the system specifications to prevent these errors from reoccurring.

## Goal
Implement the `evolve` command in `ouroboros/cli.py` and the core logic in a new module `ouroboros/evolution.py`. This command will diagnose failures across all development stages (Mechanical, Semantic, Stagnation) and apply permanent patches to:
1. `ouroboros_seed.yaml` under `constraints`
2. `AGENTS.md` under a new `## Anti-Regression Rules` section

This ensures that the AI coding assistant learns from past mistakes and never repeats them.

---

## User Review Required

> [!IMPORTANT]
> **Key Architectural Decisions & User Benefits:**
> - **Self-Patching Constraints:** Appending new constraints to `ouroboros_seed.yaml` guarantees that any future Double Diamond planning or AI execution will honor these new rules.
> - **Session Rule Evolution (`AGENTS.md`):** Appending rules to `AGENTS.md` ensures subsequent Antigravity/AI coding sessions will read and follow the learned rules as part of Rule 6 (Handoff Protocol).
> - **Robust Fallback:** If API keys are missing, the engine will use a robust template-based rules generator to format anti-regression rules based on standard error categorization.

---

## Open Questions

> [!NOTE]
> None. The user has explicitly clarified that the `evolve` feature is not merely a bug-fix utility, but a system-wide patch to prevent regression.

---

## Proposed Changes

### Component: Ouroboros Core Engine

---

#### [NEW] [evolution.py](file:///C:/Users/user/Desktop/jdy_agy/ouroboros/evolution.py)
Create the core evolution logic including diagnostic log parser, anti-regression patch generator, and target files patcher.

- **Class `EvolutionEngine`**:
  - `diagnose_workspace()`: Scans mechanical results (compilation, pytest logs), semantic results (consensus failures), and history (stagnation) to isolate active failures.
  - `generate_patches(failures)`: Calls LLM (or falls back to a categorized rule generator) to create:
    - A new system-level constraint.
    - A new binding session rule.
  - `apply_patches(constraint, rule)`:
    - Deserializes `ouroboros_seed.yaml`, appends the constraint to `constraints`, and serializes it back.
    - Parses `AGENTS.md`, appends the anti-regression rule under the `## Anti-Regression Rules` section, and writes it back.
  - `generate_report(constraint, rule)`: Renders a comprehensive markdown summary of the evolution.

---

#### [MODIFY] [cli.py](file:///C:/Users/user/Desktop/jdy_agy/ouroboros/cli.py)
Add the `@app.command() def evolve(...)` command to the Typer CLI and integrate it into the `welcome` guide.

- Add the `evolve` command to load evaluation reports or auto-discover workspace errors, execute `EvolutionEngine`, apply patches, and display a Rich-formatted panel summarizing the evolution.
- Update `welcome()` command to display the `evolve` command in the onboarding help guide.

---

#### [MODIFY] [test_ouroboros.py](file:///C:/Users/user/Desktop/jdy_agy/tests/test_ouroboros.py)
Add 3 unit tests verifying:
1. `test_evolution_diagnostics()`: Diagnosis of synthetic compilation and pytest failures.
2. `test_evolution_patching()`: Successful yaml and AGENTS.md file updates.
3. `test_evolution_cli_integration()`: Typer CLI invocation of the `evolve` command.

---

## Verification Plan

### Automated Tests
Run the pytest suite to verify that all existing tests and new evolution tests pass 100%:
```powershell
python setup.py
pytest tests/test_ouroboros.py -v
```

### Manual Verification
1. Intentionally introduce a syntax error in a dummy file or fail a semantic requirement.
2. Run `python run_ouroboros.py evaluate`.
3. Run `python run_ouroboros.py evolve`.
4. Verify that:
   - `ouroboros_seed.yaml` constraints list has been updated.
   - `AGENTS.md` has a new section for anti-regression rules containing the prevention patch.
