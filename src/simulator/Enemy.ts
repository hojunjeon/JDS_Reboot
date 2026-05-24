import type { SimEnemy, EnemyType, SimPlayer } from './types';

/**
 * Instantiates a new simulated enemy state based on its type and selected stage.
 * @param id Unique identifier string for tracking in lists
 * @param type The bug classification (SyntaxError, NullPointer, etc.)
 * @param x Initial X coordinate
 * @param y Initial Y coordinate
 * @param stageSelection Current stage (Stage 2 scales Boss HP)
 */
export function createEnemy(
    id: string,
    type: EnemyType,
    x: number,
    y: number,
    stageSelection: number
): SimEnemy {
    let hp = 15;
    let speed = 80;
    let radius = 10;
    let damage = 10;

    switch (type) {
        case 'SYNTAX_ERROR':
            hp = 15;
            speed = 75;
            radius = 10;
            damage = 10;
            break;
        case 'NULL_POINTER':
            hp = 5;
            speed = 150;
            radius = 8;
            damage = 5;
            break;
        case 'SEG_FAULT':
            hp = 60;
            speed = 40;
            radius = 16;
            damage = 25;
            break;
        case 'HEAL_BUG':
            hp = 12;
            speed = 100;
            radius = 10;
            damage = 0; // Fleeing support bug does no contact damage
            break;
        case 'BOSS':
            hp = stageSelection === 2 ? 1600 : 800;
            speed = 60;
            radius = 24;
            damage = 30;
            break;
    }

    return {
        id,
        type,
        x,
        y,
        vx: 0,
        vy: 0,
        hp,
        maxHp: hp,
        speed,
        radius,
        damage,
        customAIState: 0
    };
}

/**
 * Ticks an individual enemy's movement vectors and custom logic.
 * @param enemy The enemy entity to update
 * @param player The current player state reference
 * @param dt Delta time in milliseconds
 */
export function updateEnemy(enemy: SimEnemy, player: SimPlayer, dt: number): void {
    const dx = player.x - enemy.x;
    const dy = player.y - enemy.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    switch (enemy.type) {
        case 'SYNTAX_ERROR':
        case 'NULL_POINTER':
        case 'SEG_FAULT':
            // Pure tracking logic: move directly towards the player
            if (dist > 0) {
                enemy.vx = (dx / dist) * enemy.speed;
                enemy.vy = (dy / dist) * enemy.speed;
            } else {
                enemy.vx = 0;
                enemy.vy = 0;
            }
            break;

        case 'HEAL_BUG':
            // Fleeing logic: move directly away from the player
            if (dist > 0) {
                enemy.vx = (-dx / dist) * enemy.speed;
                enemy.vy = (-dy / dist) * enemy.speed;
            } else {
                // If on top of player, pick a random fleeing direction
                enemy.vx = enemy.speed;
                enemy.vy = 0;
            }
            break;

        case 'BOSS':
            // Boss (Jang Seonhyeong) Orbital Hovering AI
            // customAIState stores the boss's current orbiting angle around the player
            const currentAngle = enemy.customAIState || 0;
            const nextAngle = currentAngle + 0.6 * (dt / 1000); // 0.6 rads/sec rotation speed
            enemy.customAIState = nextAngle;

            // Target coordinates representing an orbiting position 180px away from player
            const targetX = player.x + Math.cos(nextAngle) * 180;
            const targetY = player.y + Math.sin(nextAngle) * 180;

            const tx = targetX - enemy.x;
            const ty = targetY - enemy.y;
            const tdist = Math.sqrt(tx * tx + ty * ty);

            if (tdist > 5) {
                enemy.vx = (tx / tdist) * enemy.speed;
                enemy.vy = (ty / tdist) * enemy.speed;
            } else {
                enemy.vx = 0;
                enemy.vy = 0;
            }
            break;
    }

    // Apply movement
    enemy.x += enemy.vx * (dt / 1000);
    enemy.y += enemy.vy * (dt / 1000);
}
