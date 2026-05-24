# Ouroboros Lite Double Diamond Execution Plan

## Executive Summary

**Primary Goal (Title):** Jiyoon Debug Survival
**Description:** A 2D wave survival action game set in a corrupted IDE where programming bugs are monsters.

### Planning Metrics
- **Total Acceptance Criteria (Tasks):** 24
- **Total Parallel Execution Levels:** 4
- **Concurrency Factor (Avg Tasks/Level):** 6.00
- **Execution Mode:** Parallel (Topological Sort optimized)

### System Constraints
- Phaser 3 framework must be used for all scene management and rendering pipelines.
- All graphics should use retro ASCII / terminal visual aesthetic styles.
- Game must execute perfectly inside standard modern browsers without native installs.
- No Placeholders: Core implementation contains no stub code, TODOs, comments containing placeholder phrases, or empty ellipses (...).

## Dependency Visualization

```mermaid
graph TD
    AC100["AC100: The game starts from a Monospace/Terminal style..."]
    AC101["AC101: Menu provides 'Start Game', 'Stage Selection', ..."]
    AC100 --> AC101
    AC102["AC102: Terminal boot-up sequence animation plays upon ..."]
    AC100 --> AC102
    AC103["AC103: Weapon Selection screen displays stats and desc..."]
    AC100 --> AC103
    AC104["AC104: Result Screen correctly handles Game Over and S..."]
    AC100 --> AC104
    AC200["AC200: The active play field is controlled by keyboard..."]
    AC201["AC201: Arrow keys and WASD shift the player character ..."]
    AC200 --> AC201
    AC202["AC202: Collision boundaries prevent the player from mo..."]
    AC200 --> AC202
    AC300["AC300: Weapons execute auto-fire cycles targeting loca..."]
    AC200 --> AC300
    AC301["AC301: Python Weapon: Automatic firing of home-in shot..."]
    AC300 --> AC301
    AC302["AC302: C/C++ Weapon: Fast, straight line piercing proj..."]
    AC300 --> AC302
    AC303["AC303: Java Weapon: Orbiting defensive shield rotating..."]
    AC300 --> AC303
    AC400["AC400: Enemy spawn waves and behavior models are activ..."]
    AC200 --> AC400
    AC401["AC401: SyntaxError basic tracker: pursues player coord..."]
    AC400 --> AC401
    AC402["AC402: NullPointer fast tracker: high movement speed, ..."]
    AC400 --> AC402
    AC403["AC403: SegFault heavy tanker: slow movement speed, hig..."]
    AC400 --> AC403
    AC404["AC404: HealBug fleeing support: flees from player, dro..."]
    AC400 --> AC404
    AC405["AC405: Stage Event 'Indentation Panic': triggers at 30..."]
    AC400 --> AC405
    AC500["AC500: Stage Clear Boss Event."]
    AC200 --> AC500
    AC501["AC501: Rival Debug Boss 'Jang Seonhyeong' spawns preci..."]
    AC500 --> AC501
    AC502["AC502: Defeating the Boss halts basic spawns and trigg..."]
    AC501 --> AC502
    AC600["AC600: Game HUD and retro diagnostics display."]
    AC601["AC601: HUD panels track HP, game timer, kill count, cu..."]
    AC600 --> AC601
    AC602["AC602: CRT scanlines, glitch effects, and monospace fo..."]
    AC600 --> AC602
```

## Double Diamond Phase Breakdown

The Double Diamond consists of four stages: Discover (understanding the problem), Define (scope and specifications), Design (technical and UI architecture), and Deliver (implementation and evaluation).

### Phase: Discover
*Initial research, requirement gathering, and Socratic clarification of goals.*

| Task ID | Level | Description | Dependencies |
| --- | --- | --- | --- |
| `AC100` | L1 | The game starts from a Monospace/Terminal styled menu scene. | `None` |
| `AC200` | L1 | The active play field is controlled by keyboard controls. | `None` |
| `AC600` | L1 | Game HUD and retro diagnostics display. | `None` |

### Phase: Define
*Scoping, boundary definition, constraint cataloging, and precise spec definition.*

| Task ID | Level | Description | Dependencies |
| --- | --- | --- | --- |
| `AC101` | L2 | Menu provides 'Start Game', 'Stage Selection', and 'Weapon Selection' command inputs. | `AC100` |
| `AC102` | L2 | Terminal boot-up sequence animation plays upon launching the game. | `AC100` |
| `AC103` | L2 | Weapon Selection screen displays stats and descriptions of the 3 starting weapons. | `AC100` |
| `AC104` | L2 | Result Screen correctly handles Game Over and Stage Clear states. | `AC100` |
| `AC201` | L2 | Arrow keys and WASD shift the player character continuously in 2D space. | `AC200` |
| `AC202` | L2 | Collision boundaries prevent the player from moving outside the terminal window canvas. | `AC200` |
| `AC300` | L2 | Weapons execute auto-fire cycles targeting local bug monsters. | `AC200` |
| `AC400` | L2 | Enemy spawn waves and behavior models are active in the arena. | `AC200` |
| `AC500` | L2 | Stage Clear Boss Event. | `AC200` |
| `AC601` | L2 | HUD panels track HP, game timer, kill count, current weapon, and active event/boss status in terminal theme. | `AC600` |
| `AC602` | L2 | CRT scanlines, glitch effects, and monospace fonts establish terminal IDE aesthetic. | `AC600` |

### Phase: Design
*Technical blueprinting, data modeling, algorithm design, and UI architecture.*

| Task ID | Level | Description | Dependencies |
| --- | --- | --- | --- |
| `AC301` | L3 | Python Weapon: Automatic firing of home-in shots targeting the nearest bug monster. | `AC300` |
| `AC302` | L3 | C/C++ Weapon: Fast, straight line piercing projectile representing direct debugging. | `AC300` |
| `AC303` | L3 | Java Weapon: Orbiting defensive shield rotating around the player character. | `AC300` |
| `AC401` | L3 | SyntaxError basic tracker: pursues player coordinates, inflicts contact damage. | `AC400` |
| `AC402` | L3 | NullPointer fast tracker: high movement speed, low base health. | `AC400` |
| `AC403` | L3 | SegFault heavy tanker: slow movement speed, high health, high contact damage. | `AC400` |
| `AC404` | L3 | HealBug fleeing support: flees from player, drops HP recovery item on death. | `AC400` |
| `AC405` | L3 | Stage Event 'Indentation Panic': triggers at 30s, spawns a deluge of indentation bugs. | `AC400` |
| `AC501` | L3 | Rival Debug Boss 'Jang Seonhyeong' spawns precisely at 60 seconds of survival. | `AC500` |

### Phase: Deliver
*Implementation, test-driven validation, and final mechanical and semantic compliance check.*

| Task ID | Level | Description | Dependencies |
| --- | --- | --- | --- |
| `AC502` | L4 | Defeating the Boss halts basic spawns and triggers Stage Clear transition. | `AC501` |

## Master Step-by-Step Execution Path

Developers or subagents should execute these levels sequentially. However, **all tasks within a single level can be executed concurrently** because their dependencies have been satisfied.

### Level 1
*(Parallel execution enabled: **3** concurrent tasks)*

- [ ] **`AC100`** [Discover]: The game starts from a Monospace/Terminal styled menu scene.
- [ ] **`AC200`** [Discover]: The active play field is controlled by keyboard controls.
- [ ] **`AC600`** [Discover]: Game HUD and retro diagnostics display.

### Level 2
*(Parallel execution enabled: **11** concurrent tasks)*

- [ ] **`AC101`** [Define]: Menu provides 'Start Game', 'Stage Selection', and 'Weapon Selection' command inputs. (requires AC100)
- [ ] **`AC102`** [Define]: Terminal boot-up sequence animation plays upon launching the game. (requires AC100)
- [ ] **`AC103`** [Define]: Weapon Selection screen displays stats and descriptions of the 3 starting weapons. (requires AC100)
- [ ] **`AC104`** [Define]: Result Screen correctly handles Game Over and Stage Clear states. (requires AC100)
- [ ] **`AC201`** [Define]: Arrow keys and WASD shift the player character continuously in 2D space. (requires AC200)
- [ ] **`AC202`** [Define]: Collision boundaries prevent the player from moving outside the terminal window canvas. (requires AC200)
- [ ] **`AC300`** [Define]: Weapons execute auto-fire cycles targeting local bug monsters. (requires AC200)
- [ ] **`AC400`** [Define]: Enemy spawn waves and behavior models are active in the arena. (requires AC200)
- [ ] **`AC500`** [Define]: Stage Clear Boss Event. (requires AC200)
- [ ] **`AC601`** [Define]: HUD panels track HP, game timer, kill count, current weapon, and active event/boss status in terminal theme. (requires AC600)
- [ ] **`AC602`** [Define]: CRT scanlines, glitch effects, and monospace fonts establish terminal IDE aesthetic. (requires AC600)

### Level 3
*(Parallel execution enabled: **9** concurrent tasks)*

- [ ] **`AC301`** [Design]: Python Weapon: Automatic firing of home-in shots targeting the nearest bug monster. (requires AC300)
- [ ] **`AC302`** [Design]: C/C++ Weapon: Fast, straight line piercing projectile representing direct debugging. (requires AC300)
- [ ] **`AC303`** [Design]: Java Weapon: Orbiting defensive shield rotating around the player character. (requires AC300)
- [ ] **`AC401`** [Design]: SyntaxError basic tracker: pursues player coordinates, inflicts contact damage. (requires AC400)
- [ ] **`AC402`** [Design]: NullPointer fast tracker: high movement speed, low base health. (requires AC400)
- [ ] **`AC403`** [Design]: SegFault heavy tanker: slow movement speed, high health, high contact damage. (requires AC400)
- [ ] **`AC404`** [Design]: HealBug fleeing support: flees from player, drops HP recovery item on death. (requires AC400)
- [ ] **`AC405`** [Design]: Stage Event 'Indentation Panic': triggers at 30s, spawns a deluge of indentation bugs. (requires AC400)
- [ ] **`AC501`** [Design]: Rival Debug Boss 'Jang Seonhyeong' spawns precisely at 60 seconds of survival. (requires AC500)

### Level 4
*(Parallel execution enabled: **1** concurrent tasks)*

- [ ] **`AC502`** [Deliver]: Defeating the Boss halts basic spawns and triggers Stage Clear transition. (requires AC501)
