# Phase 0: Socratic Requirements Specification for Jiyoon Debug Survival (JDS)

Establish the core specification for the Jiyoon Debug Survival (JDS) game reboot by programmatically executing the Ouroboros Socratic Interview using `docs/00-reboot-start.md` as our source of truth.

## User Review Required

Documenting key structural constraints and architecture decisions that will shape the entire development cycle of the game reboot.

> [!IMPORTANT]
> **Aesthetic and Technology Binding Rules**
> - **Engine**: Phaser 3 must be used for all 2D scene management, input, rendering, and collision handling.
> - **Visuals**: Modern neon aesthetic combined with monospace terminal fonts, retro ASCII textures, subtle glitch effects, and CRT scanlines.
> - **Language**: TypeScript/JavaScript for the web client application.
> - **Architecture**: Game simulation logic must be stateless and isolated from Phaser rendering to guarantee unit-testable game loops.

> [!WARNING]
> **Ouroboros Lite Schema Reconcilation**
> - `ouroboros/interview.py`'s `generate_seed` method produces a schema with `project`, `clarity_metrics`, `socratic_transcript`, and `specification` keys.
> - However, `ouroboros/execution.py`'s `DoubleDiamondPlanner` and our test suites strictly expect the `SeedSpec` schema (`title`, `description`, `acceptance_criteria_tree`, `constraints`, `architecture_decisions`).
> - **Our Solution**: We will generate an `ouroboros_seed.yaml` that perfectly satisfies the `SeedSpec` model to allow seamless execution of `python run_ouroboros.py plan`, but we will also embed the full Socratic transcript and metadata so that the complete Phase 0 Socratic interview history is fully preserved!

## Open Questions

> [!NOTE]
> **Design Decisions to Align on:**
> 1. **Time-based vs Kill-based Boss Spawn**: The reboot document specifies "시간이 충분히 지나면 보스가 등장한다 (Stage 1의 경우 일정 생존 시간 후 등장)". We propose a strict time threshold of 60 seconds for Stage 1. Is this acceptable, or should we make it kill-dependent?
> 2. **SSAFY References**: Should we maintain references to "SSAFY 교실 터미널" and "Jang Seonhyeong" (rival/debug boss), or generalize them to a generic developer school theme? (We recommend keeping them as they add great humor and flavor to the core fantasy).
> 3. **Indentation Panic Event Duration**: We propose that the `Indentation Panic` stage event triggers at 30 seconds and lasts for 10 seconds, during which a high-density barrage of indentation bugs sweep across the screen.

## Proposed Changes

We will create a programmatic interview simulation script to invoke the actual Ouroboros interview logic, complete the rounds based on the reboot start document, and output a rich, fully populated specification.

---

### Ouroboros Specification Pipeline

#### [NEW] [run_interview.py](file:///C:/Users/user/Desktop/jdy_agy/.ai-workspace/scratch/run_interview.py)
A gitignored scratch script that:
1. Instantiates `InterviewEngine` and `InterviewState` from `ouroboros.interview`.
2. Programmatically answers Socratic questions from all 5 perspectives (Researcher, Simplifier, Architect, Breadth-keeper, Seed-closer) using content from `docs/00-reboot-start.md`.
3. Validates the resulting clarity scores and ambiguity ratings.
4. Generates a robust `ouroboros_seed.yaml` that is fully compliant with `SeedSpec` for Phase 1 planning.

#### [MODIFY] [ouroboros_seed.yaml](file:///C:/Users/user/Desktop/jdy_agy/ouroboros_seed.yaml)
Crystallize the complete game requirements into the final seed specification:
- Title: Jiyoon Debug Survival (JDS)
- Detailed `acceptance_criteria_tree` mapping the 6 core components (Menus, Movement, Weapons, Enemies, Boss, HUD).
- Exact technological and styling constraints.
- Formal architectural decisions (Phaser 3 selection, isolated simulation logic).

## Verification Plan

### Automated Tests
- Run our custom script to verify the interview completes successfully:
  ```bash
  python .ai-workspace/scratch/run_interview.py
  ```
- Run Ouroboros tests to verify seed spec compatibility:
  ```bash
  python -m pytest tests/test_ouroboros.py
  ```
- Run the Ouroboros planner to verify successful plan generation:
  ```bash
  python run_ouroboros.py plan
  ```

### Manual Verification
- Review the generated `ouroboros_seed.yaml` and `ouroboros_plan.md` to ensure they map 100% of the game requirements in `docs/00-reboot-start.md` without any placeholder descriptions.
