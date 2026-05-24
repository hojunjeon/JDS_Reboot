# Refinement Implementation Plan - Jiyoon Debug Survival Polish

This plan outlines the implementation of high-fidelity arcade polish, Web Audio API retro 8-bit sound effects, gameplay balance adjustments, and performance/CRT glitch optimizations.

## 1. Web Audio API Retro Sound Effects (`src/renderer/SoundFX.ts`)
We will programmatically synthesize classic retro 8-bit sound effects using the browser's native `AudioContext` and `OscillatorNode`. This avoids loading heavy external audio assets and provides low-latency, custom-synthesized SFX.

### Synthesizer Specs:
- **`playShoot()`**: Square-wave sweep (800Hz -> 150Hz in 0.12s) to represent Python/C++ compiler fire.
- **`playShield()`**: Short resonance tone (sine wave 300Hz modulated with high-frequency pitch sweep, 0.08s) representing Java orbiting shield collision.
- **`playHit()`**: Sawtooth noise-glitch impact tone (200Hz -> 40Hz in 0.18s) with rapid volume decay.
- **`playExplosion()`**: White-noise generator coupled with a lowpass filter sweep (cutoff frequency 400Hz down to 10Hz in 0.25s) representing bug resolution.
- **`playPowerUp()`**: A fast ascending arpeggio sweep (3 rapid notes: C5 -> E5 -> G5) when picking up recovery items.
- **`playVictory()`**: Neon celebratory ascending arpeggio (C5 -> E5 -> G5 -> C6) using triangle waves.
- **`playGameOver()`**: Descending minor arpeggio (A4 -> F4 -> C4 -> A3) representing stack overflow.

## 2. Gameplay Balancing (Python Weapon)
- Update the firing cooldown of the **Python** weapon from `700ms` (`0.7`s) to `450ms` (`0.45`s) to make it highly competitive in high-density Stage 2 waves.

## 3. Collision Performance Optimizations & Monster Capping
- **Monster Capping**: Enforce a hard cap of `50` active bugs inside the spawner (`Simulator.ts` / `EventManager.ts`) to maintain perfect 60 FPS pacing.
- **Pre-filtering**: Introduce a quick box-bounding pre-filtering check:
  $$\text{Math.abs}(dx) < r \quad \text{and} \quad \text{Math.abs}(dy) < r$$
  before computing the squared Euclidean distance check.

## 4. CRT Glitches and Damage Feedback
- Introduce a terminal screen shake and red-tinted CRT chromatic glitch shader effect or DOM-styled layout glitch when the player takes damage in `PlayScene.ts`.

## 5. Verification & Compilation Check
- Run local TypeScript compiling and Vite build to confirm zero warnings or errors.
- Ensure all files contain NO placeholders or TODO stubs.
