import type { SimPlayer, SimEnemy, SimProjectile } from './types';
import { SoundFX } from '../renderer/SoundFX';

/**
 * Finds the nearest enemy to a specific coordinate set.
 * @param x Origin X
 * @param y Origin Y
 * @param enemies List of active enemies
 */
export function findNearestEnemy(x: number, y: number, enemies: SimEnemy[]): SimEnemy | null {
    if (enemies.length === 0) return null;
    let nearest: SimEnemy | null = null;
    let minDist = Infinity;

    for (const enemy of enemies) {
        const dx = enemy.x - x;
        const dy = enemy.y - y;
        const dist = dx * dx + dy * dy; // squared distance to avoid expensive Math.sqrt
        if (dist < minDist) {
            minDist = dist;
            nearest = enemy;
        }
    }
    return nearest;
}

/**
 * Manages the weapon firing cooldows and spawns new projectiles based on active weapons.
 * @param player Current player state
 * @param enemies List of active enemies to target
 * @param projectiles Reference to projectiles array to add spawned entities
 * @param cooldownCurrent The active remaining weapon cooldown
 * @param dt Delta time in milliseconds
 * @param nextProjId ID generator callback
 * @returns Updated weapon cooldown time remaining
 */
export function fireWeapon(
    player: SimPlayer,
    enemies: SimEnemy[],
    projectiles: SimProjectile[],
    cooldownCurrent: number,
    dt: number,
    nextProjId: () => string
): number {
    let cooldown = Math.max(0, cooldownCurrent - dt / 1000);

    if (player.activeWeapon === 'JAVA') {
        // Java uses persistent orbiting shields.
        // We ensure there are exactly 3 shields in orbit.
        const activeJavaShields = projectiles.filter(p => p.type === 'JAVA');
        if (activeJavaShields.length < 3) {
            const startAngles = [0, (2 * Math.PI) / 3, (4 * Math.PI) / 3];
            // Clear existing Java projectiles to avoid duplicate styling
            for (let i = projectiles.length - 1; i >= 0; i--) {
                if (projectiles[i].type === 'JAVA') {
                    projectiles.splice(i, 1);
                }
            }
            // Spawn 3 fresh ones
            for (let i = 0; i < 3; i++) {
                const angle = startAngles[i];
                const orbitRadius = 70;
                projectiles.push({
                    id: nextProjId(),
                    type: 'JAVA',
                    x: player.x + Math.cos(angle) * orbitRadius,
                    y: player.y + Math.sin(angle) * orbitRadius,
                    vx: 0,
                    vy: 0,
                    damage: 12,
                    radius: 8,
                    pierceRemaining: 999999, // infinite pierce for blockades
                    angle: angle
                });
            }
        }
        return 0; // Persistent weapon has no continuous cooldown firing
    }

    // Standard projectile weapons
    if (cooldown <= 0) {
        if (player.activeWeapon === 'PYTHON') {
            const target = findNearestEnemy(player.x, player.y, enemies);
            if (target) {
                // Fire a homing missile targeting this bug
                const dx = target.x - player.x;
                const dy = target.y - player.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const speed = 250;
                const vx = dist > 0 ? (dx / dist) * speed : 0;
                const vy = dist > 0 ? (dy / dist) * speed : -speed;

                projectiles.push({
                    id: nextProjId(),
                    type: 'PYTHON',
                    x: player.x,
                    y: player.y,
                    vx,
                    vy,
                    damage: 10,
                    radius: 5,
                    pierceRemaining: 1, // single target homing
                    homingTargetId: target.id
                });
                SoundFX.playShoot();
                cooldown = 0.45; // Fire every 450ms
            }
        } else if (player.activeWeapon === 'CPP') {
            const target = findNearestEnemy(player.x, player.y, enemies);
            const speed = 450;
            let vx = 0;
            let vy = -speed;

            if (target) {
                // Fire a fast, highly-piercing beam in a straight line towards that bug
                const dx = target.x - player.x;
                const dy = target.y - player.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist > 0) {
                    vx = (dx / dist) * speed;
                    vy = (dy / dist) * speed;
                }
            }

            projectiles.push({
                id: nextProjId(),
                type: 'CPP',
                x: player.x,
                y: player.y,
                vx,
                vy,
                damage: 18,
                radius: 4,
                pierceRemaining: 5 // Pierces up to 5 bugs!
            });
            SoundFX.playShoot();
            cooldown = 0.45; // Fire every 450ms (fast bursts)
        }
    }

    return cooldown;
}

/**
 * Ticks positions, rotations, homing paths, and durations for all active projectiles.
 * @param projectiles Reference to list of projectiles to update
 * @param enemies Active enemies list to guide homing targets
 * @param player Active player position reference
 * @param dt Delta time in milliseconds
 */
export function updateProjectiles(
    projectiles: SimProjectile[],
    enemies: SimEnemy[],
    player: SimPlayer,
    dt: number
): void {
    const elapsed = dt / 1000;

    for (const proj of projectiles) {
        if (proj.type === 'JAVA') {
            // Orbiting Shields rotate mathematically around player center
            const currentAngle = proj.angle ?? 0;
            const nextAngle = currentAngle + 3.2 * elapsed; // 3.2 rads/sec orbit speed
            proj.angle = nextAngle;

            const orbitRadius = 70;
            proj.x = player.x + Math.cos(nextAngle) * orbitRadius;
            proj.y = player.y + Math.sin(nextAngle) * orbitRadius;
            proj.vx = 0;
            proj.vy = 0;
        } else if (proj.type === 'PYTHON') {
            // Homing projectile updates direction towards target bug
            let target: SimEnemy | null = null;
            if (proj.homingTargetId) {
                target = enemies.find(e => e.id === proj.homingTargetId) || null;
            }

            // If target died or wasn't specified, find a new target dynamically
            if (!target || target.hp <= 0) {
                target = findNearestEnemy(proj.x, proj.y, enemies);
                if (target) {
                    proj.homingTargetId = target.id;
                }
            }

            if (target) {
                const dx = target.x - proj.x;
                const dy = target.y - proj.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const speed = 250;
                if (dist > 0) {
                    proj.vx = (dx / dist) * speed;
                    proj.vy = (dy / dist) * speed;
                }
            }

            // Move homing projectiles
            proj.x += proj.vx * elapsed;
            proj.y += proj.vy * elapsed;
        } else {
            // C++ piercing beam moves in a strict straight line
            proj.x += proj.vx * elapsed;
            proj.y += proj.vy * elapsed;
        }
    }
}
