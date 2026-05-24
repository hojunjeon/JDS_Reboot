# Jiyoon Debug Survival — Step-by-Step Game Implementation Checklist

This checklist tracks progress across the topological execution levels defined in `ouroboros_plan.md`. 
Every task corresponds directly to an Acceptance Criterion (AC) and lists specific files, classes, and verification steps.

---

## Pre-Requisites & Project Setup
- [ ] **Task 0.1: Package Installation & Configuration**
  - **Action**: Install Phaser 3, TypeScript types, and setup bundler compatibility.
  - **Commands to run**:
    ```bash
    npm install phaser
    npm install --save-dev @types/phaser
    ```
  - **Files modified**: `package.json`
- [ ] **Task 0.2: Configure Phaser Boot Canvas**
  - **Action**: Set up `src/config.ts` and update `src/main.ts` to boot the Phaser Game engine configured with a retro 800x600 px monochrome window.
  - **Files modified**: `src/config.ts`, `src/main.ts`

---

## Level 1: Discover (Basic Scene Shells, Controls & HUD Initialization)
*(Total Parallel Tasks: 3)*

### 1. Scene Core Shell Setup
- [ ] **Task 1.1: `AC100` — Monospace/Terminal Styled Menu scene**
  - **Action**: Create `BootScene.ts` and `MenuScene.ts` with basic rendering bounds, utilizing `Fira Code` or `Courier New` monospace CSS typography. Setup basic Phaser scene entry structures.
  - **Target Files**: `src/scenes/BootScene.ts`, `src/scenes/MenuScene.ts`
  - **Verification**: Launch Vite dev server, confirm scenes mount in the browser without compiling errors.

### 2. Player Input Integration
- [ ] **Task 1.2: `AC200` — Active play field controlled by keyboard**
  - **Action**: Setup Phaser keyboard cursors (`W`, `A`, `S`, `D` and `Arrow Keys`) listener mappings in `src/scenes/PlayScene.ts`.
  - **Target Files**: `src/scenes/PlayScene.ts`
  - **Verification**: Keyboard triggers console logging logs verifying key presses are registered in the update loop.

### 3. Diagnostics Layout
- [ ] **Task 1.3: `AC600` — Game HUD and retro diagnostics display**
  - **Action**: Implement the HTML layout wrapper or text dashboard structure in `PlayScene` to reserve bounds for the retro side panel diagnostic metrics.
  - **Target Files**: `src/scenes/PlayScene.ts`
  - **Verification**: Side dashboard shows a mock panel box reading `CPU TEMP: 98 C` and `SYSTEM CORES: SAFE`.

---

## Level 2: Define (Core Gameplay Systems & Interactions)
*(Total Parallel Tasks: 11)*

### 1. Interactive Monospace Menu Setup
- [ ] **Task 2.1: `AC101` — Start, Stage, and Weapon selection commands**
  - **Action**: Implement keyboard selection navigation logic (`W`/`S` keys) inside `MenuScene.ts` to highlight active command configurations. Add support for triggering play mode transition on pressing `ENTER` or clicking commands.
  - **Target Files**: `src/scenes/MenuScene.ts`
  - **Verification**: Confirm selections dynamically update highlighted text styling.
- [ ] **Task 2.2: `AC102` — Terminal boot-up sequence animation**
  - **Action**: Implement timed line-printing logic inside `BootScene.ts` utilizing typing effects for the BIOS print statements.
  - **Target Files**: `src/scenes/BootScene.ts`
  - **Verification**: Verify that the BIOS log plays sequentially for 2 seconds before letting the player press any key to enter.
- [ ] **Task 2.3: `AC103` — Weapon Selection screen displaying stats**
  - **Action**: Draw custom ASCII cards for Python, C/C++, and Java within `MenuScene.ts` showing explicit damage/speed numbers and flavor descriptions.
  - **Target Files**: `src/scenes/MenuScene.ts`
  - **Verification**: Selecting a weapon updates the display cards to match.
- [ ] **Task 2.4: `AC104` — Result Screen Game Over and Stage Clear states**
  - **Action**: Create `ResultScene.ts` with explicit logic for processing parameter status strings passed from `PlayScene` (`isStageClear`, `isGameOver`).
  - **Target Files**: `src/scenes/ResultScene.ts`
  - **Verification**: Passing status parameters renders the corresponding "SYSTEM OVERFLOW" or "COMPILATION SUCCESS" text.

### 2. Player Motion & Clamping
- [ ] **Task 2.5: `AC201` — Continuous 2D Player shifting via keyboard**
  - **Action**: Implement player simulator updating under `src/simulator/Player.ts` reacting to key flags. Integrate movement in diagonal axes.
  - **Target Files**: `src/simulator/Player.ts`, `src/simulator/Simulator.ts`
  - **Verification**: Verify player simulator moves correctly under uniform speed settings.
- [ ] **Task 2.6: `AC202` — Collision boundaries clamp player to canvas window**
  - **Action**: Implement bounds checking using the simulator limits `width` and `height`, preventing player coordinates from straying beyond active sandbox boundaries.
  - **Target Files**: `src/simulator/Simulator.ts`
  - **Verification**: Hold right/down direction key for 10 seconds; confirm player X/Y coordinates do not exceed canvas limits.

### 3. Weapons & Entity Management
- [ ] **Task 2.7: `AC300` — Weapons execute auto-fire cycles targeting bugs**
  - **Action**: Build core auto-fire timers within `src/simulator/Weapon.ts`. Ticking the timer spawns projectile records inside the simulator state.
  - **Target Files**: `src/simulator/Weapon.ts`, `src/simulator/Simulator.ts`
  - **Verification**: Simulator ticks generate periodic projectile arrays.
- [ ] **Task 2.8: `AC400` — Enemy spawn waves and behavior models**
  - **Action**: Construct the timeline spawns framework under `src/simulator/EventManager.ts` and standard velocity-tracking functions under `src/simulator/Enemy.ts`.
  - **Target Files**: `src/simulator/EventManager.ts`, `src/simulator/Enemy.ts`
  - **Verification**: Spawners output base coordinates of generic trackers surrounding the center.
- [ ] **Task 2.9: `AC500` — Stage Clear Boss Event**
  - **Action**: Implement timeline trigger checking that switches state flags when the game clock hits exactly 60.0 seconds.
  - **Target Files**: `src/simulator/EventManager.ts`
  - **Verification**: At timer ticks > 60, regular enemy spawner intervals halt.

### 4. Aesthetics & HUD Integration
- [ ] **Task 2.10: `AC601` — HUD panels tracking HP, timer, kills, active weapon**
  - **Action**: Integrate real-time diagnostics string compiling inside `PlayScene.ts` rendering current `Simulator` state values into tabular ASCII status displays.
  - **Target Files**: `src/scenes/PlayScene.ts`
  - **Verification**: HP bar updates visually to match the simulated player's core health state.
- [ ] **Task 2.11: `AC602` — CRT scanlines, flicker, and monospace styling**
  - **Action**: Set up global rules in `src/style.css` displaying scanlines, retro flicker keys, and container glow parameters.
  - **Target Files**: `src/style.css`, `index.html`
  - **Verification**: Scanline lines display visibly over standard canvas rendering.

---

## Level 3: Design (Detailed Logic & Custom Behaviors)
*(Total Parallel Tasks: 9)*

### 1. Specific Weapon Mechanics
- [ ] **Task 3.1: `AC301` — Python Weapon: Homing shots targeting nearest bug**
  - **Action**: Implement Python targeting routines that find the closest active enemy by calculating Euclidean distances, then updating projectile velocity vectors every frame to home in on coordinates.
  - **Target Files**: `src/simulator/Weapon.ts`
  - **Verification**: Homing projectiles correct their flight path dynamically when the target moves.
- [ ] **Task 3.2: `AC302` — C/C++ Weapon: Fast piercing straight-line direct debug rays**
  - **Action**: Implement direct ray firing mechanics. Calculate linear velocity towards target at firing instant. Allow projectile to puncture up to 5 enemies.
  - **Target Files**: `src/simulator/Weapon.ts`
  - **Verification**: Bullet continues moving linearly on contact, reducing health of consecutive enemies on line.
- [ ] **Task 3.3: `AC303` — Java Weapon: Orbiting defensive shields rotating around player**
  - **Action**: Spawn 3 shield entities that rotate around player coordinates mathematically based on current angle values.
  - **Target Files**: `src/simulator/Weapon.ts`
  - **Verification**: Projectile coordinates rotate in a fixed radius around the moving player.

### 2. Specific Enemy Behaviors
- [ ] **Task 3.4: `AC401` — SyntaxError: Basic coordinates tracker**
  - **Action**: Implement path vectors for `SYNTAX_ERROR` that move directly towards the player's current X/Y coordinates.
  - **Target Files**: `src/simulator/Enemy.ts`
  - **Verification**: The enemy constantly tracks and moves towards the player character.
- [ ] **Task 3.5: `AC402` — NullPointer: Fast speed tracker**
  - **Action**: Create high-speed velocity tracker for `NULL_POINTER` config, using low base HP stats.
  - **Target Files**: `src/simulator/Enemy.ts`
  - **Verification**: Enemy approaches the player rapidly but is resolved with a single attack.
- [ ] **Task 3.6: `AC403` — SegFault: Heavy tanker**
  - **Action**: Implement high health, high contact damage, and low movement speed profiles for `SEG_FAULT` bugs.
  - **Target Files**: `src/simulator/Enemy.ts`
  - **Verification**: Tanks multiple bullet impacts and deals high HP damage to player on collision.
- [ ] **Task 3.7: `AC404` — HealBug: Fleeing support dropping HP recovery items**
  - **Action**: Code fleeing algorithms under `src/simulator/Enemy.ts` where velocity direction moves directly opposite to the player's coordinates. On death, instantiate a `SimItem` at the enemy's coordinates.
  - **Target Files**: `src/simulator/Enemy.ts`, `src/simulator/Simulator.ts`
  - **Verification**: HealBug flees on player approach, dropping green recovery capsule item when killed.
- [ ] **Task 3.8: `AC405` — Indentation Panic Event: Triggers at 30s**
  - **Action**: Add logic to `EventManager.ts` spawning 15-20 basic syntax errors at coordinates around the player's viewport at the 30-second mark.
  - **Target Files**: `src/simulator/EventManager.ts`
  - **Verification**: Timeline event triggers precisely at `gameTimer = 30`, spawning a deluge of syntax error bugs.

### 3. Boss Spawn Sequence
- [ ] **Task 3.9: `AC501` — Rival Boss 'Jang Seonhyeong' spawns at 60s**
  - **Action**: Implement spawn trigger for Rival Boss at exactly 60 seconds with unique boss patterns (e.g. circling paths, bullet bursts).
  - **Target Files**: `src/simulator/Enemy.ts`, `src/simulator/EventManager.ts`
  - **Verification**: Game timer reaches 60s, triggering Boss spawn visual prompts and halts standard minor spawns.

---

## Level 4: Deliver (Win/Loss Transitions & Polish)
*(Total Parallel Tasks: 1)*

### 1. Boss Defeat & Stage Transitions
- [ ] **Task 4.1: `AC502` — Defeating Boss triggers Stage Clear transition**
  - **Action**: Implement transition checks inside `Simulator.ts` checking if the Boss's health <= 0. If true, set `isStageClear = true` and halt all basic simulations, initiating transition sequence to `ResultScene`.
  - **Target Files**: `src/simulator/Simulator.ts`, `src/scenes/PlayScene.ts`
  - **Verification**: Defeating the boss opens the stage clear diagnostics screen showing final scores.

---

## Zero-Placeholder Rule Enforcement
Every file created MUST follow the strict constraints outlined in `AGENTS.md`. No `TODO` comments, ellipses, or placeholder code blocks. Every function, state, and loop MUST be fully completed and executable.
