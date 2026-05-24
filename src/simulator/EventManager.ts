import type { SimState } from './types';
import { createEnemy } from './Enemy';

/**
 * Updates the simulation game timer and handles timeline events.
 * Spawns waves, triggers "Indentation Panic" at 30s, spawns Boss at 60s, and spawns Boss reinforcements.
 * @param state The shared simulator game state to modify
 * @param dt Delta time in milliseconds
 * @param nextEnemyId ID generator callback
 */
export function handleTimelineEvents(
    state: SimState,
    dt: number,
    nextEnemyId: () => string
): void {
    const prevTimer = state.gameTimer;
    state.gameTimer += dt / 1000;

    const difficultyMultiplier = state.stageSelection === 2 ? 2.0 : 1.0;

    // 1. Triggers "Indentation Panic" wave precisely at the 30-second boundary
    if (prevTimer < 30 && state.gameTimer >= 30) {
        const count = 18; // Deluge wave density
        const radius = 250; // Spawns outside the immediate visual threshold of player

        for (let i = 0; i < count; i++) {
            const angle = (i * 2 * Math.PI) / count;
            const spawnX = state.player.x + Math.cos(angle) * radius;
            const spawnY = state.player.y + Math.sin(angle) * radius;

            // Constrain coords to avoid spawning entirely out-of-bounds
            const clampedX = Math.max(15, Math.min(state.width - 15, spawnX));
            const clampedY = Math.max(15, Math.min(state.height - 15, spawnY));

            state.enemies.push(
                createEnemy(nextEnemyId(), 'SYNTAX_ERROR', clampedX, clampedY, state.stageSelection)
            );
        }
        console.log("[EVENT] INDENTATION PANIC DELUGE TRIGGERED!");
    }

    // 2. Triggers Boss (Jang Seonhyeong) deployment precisely at the 60-second boundary
    if (prevTimer < 60 && state.gameTimer >= 60 && !state.bossSpawned) {
        state.bossSpawned = true;
        // Spawn boss at top center
        const boss = createEnemy(
            nextEnemyId(),
            'BOSS',
            state.width / 2,
            120,
            state.stageSelection
        );
        state.enemies.push(boss);
        console.log("[EVENT] RIVAL BOSS JANG SEONHYEONG SPAWNED!");
    }

    // 3. Boss logic and reinforcement cycles
    if (state.bossSpawned && !state.bossDefeated) {
        const boss = state.enemies.find(e => e.type === 'BOSS');
        if (!boss || boss.hp <= 0) {
            state.bossDefeated = true;
            state.isStageClear = true;
            console.log("[EVENT] RIVAL BOSS COMPILATION CLEARED!");
        } else {
            // Boss spawns rotating syntax shields at intervals to protect itself
            const spawnInterval = 4.0;
            const prevInterval = Math.floor(prevTimer / spawnInterval);
            const currInterval = Math.floor(state.gameTimer / spawnInterval);

            if (currInterval > prevInterval) {
                // Stage 2 (Inferno) Boss spawns 4 shields; Stage 1 spawns 2 shields.
                const shieldCount = state.stageSelection === 2 ? 4 : 2;
                for (let i = 0; i < shieldCount; i++) {
                    const angle = (i * 2 * Math.PI) / shieldCount + state.gameTimer;
                    const spawnX = boss.x + Math.cos(angle) * 60;
                    const spawnY = boss.y + Math.sin(angle) * 60;
                    state.enemies.push(
                        createEnemy(nextEnemyId(), 'SYNTAX_ERROR', spawnX, spawnY, state.stageSelection)
                    );
                }
            }
        }
    }

    // 4. Regular Wave Spawning (only active prior to Boss deployment)
    if (!state.bossSpawned) {
        // Spawning intervals scale with stage selection difficulty (2x faster in Stage 2)
        const spawnInterval = 1.8 / difficultyMultiplier;
        const prevInterval = Math.floor(prevTimer / spawnInterval);
        const currInterval = Math.floor(state.gameTimer / spawnInterval);

        if (currInterval > prevInterval) {
            // Spawn random bugs with probability weights:
            // 55% SyntaxError, 20% NullPointer, 15% SegFault, 10% HealBug
            const rand = Math.random();
            let type: any = 'SYNTAX_ERROR';

            if (rand < 0.55) {
                type = 'SYNTAX_ERROR';
            } else if (rand < 0.75) {
                type = 'NULL_POINTER';
            } else if (rand < 0.90) {
                type = 'SEG_FAULT';
            } else {
                type = 'HEAL_BUG';
            }

            // Spawn at random coordinates along the screen borders, moving inwards
            let spawnX = 0;
            let spawnY = 0;
            const borderSelection = Math.floor(Math.random() * 4);
            const boundaryOffset = 20;

            switch (borderSelection) {
                case 0: // Top Border
                    spawnX = Math.random() * state.width;
                    spawnY = boundaryOffset;
                    break;
                case 1: // Bottom Border
                    spawnX = Math.random() * state.width;
                    spawnY = state.height - boundaryOffset;
                    break;
                case 2: // Left Border
                    spawnX = boundaryOffset;
                    spawnY = Math.random() * state.height;
                    break;
                case 3: // Right Border
                    spawnX = state.width - boundaryOffset;
                    spawnY = Math.random() * state.height;
                    break;
            }

            state.enemies.push(
                createEnemy(nextEnemyId(), type, spawnX, spawnY, state.stageSelection)
            );
        }
    }
}
