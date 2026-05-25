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
        // The shield count scales with the weapon level (Level 1: 3, Level 2: 4, Level 3: 5, Level 4: 6, Level 5: 8).
        const shieldCount = player.weaponLevel === 1 ? 3
                          : player.weaponLevel === 2 ? 4
                          : player.weaponLevel === 3 ? 5
                          : player.weaponLevel === 4 ? 6
                          : 8;

        const activeJavaShields = projectiles.filter(p => p.type === 'JAVA');
        if (activeJavaShields.length < shieldCount) {
            // Clear existing Java projectiles to avoid duplicates
            for (let i = projectiles.length - 1; i >= 0; i--) {
                if (projectiles[i].type === 'JAVA') {
                    projectiles.splice(i, 1);
                }
            }
            // Spawn fresh orbiting shields spread evenly across the circle
            const damage = 12 + (player.weaponLevel - 1) * 4;
            const radius = player.weaponLevel >= 5 ? 12 : 8;
            for (let i = 0; i < shieldCount; i++) {
                const angle = (i * 2 * Math.PI) / shieldCount;
                const orbitRadius = 70;
                projectiles.push({
                    id: nextProjId(),
                    type: 'JAVA',
                    x: player.x + Math.cos(angle) * orbitRadius,
                    y: player.y + Math.sin(angle) * orbitRadius,
                    vx: 0,
                    vy: 0,
                    damage,
                    radius,
                    pierceRemaining: 999999, // Infinite pierce for shields
                    angle: angle
                });
            }
        }
        return 0; // Persistent weapon has no fire cooldown
    }

    // Standard projectile weapons
    if (cooldown <= 0) {
        if (player.activeWeapon === 'PYTHON') {
            const target = findNearestEnemy(player.x, player.y, enemies);
            if (target) {
                // Determine shot count, damage, speed, and cooldown based on weapon level
                const shotCount = player.weaponLevel >= 5 ? 3 : player.weaponLevel >= 3 ? 2 : 1;
                const damage = 10 + (player.weaponLevel - 1) * 4;
                const speed = 250 + (player.weaponLevel - 1) * 20;

                for (let i = 0; i < shotCount; i++) {
                    const dx = target.x - player.x;
                    const dy = target.y - player.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    // Angular spread for multi-projectile firing patterns
                    const angleOffset = (i - (shotCount - 1) / 2) * 0.15;
                    let vx = dist > 0 ? (dx / dist) * speed : 0;
                    let vy = dist > 0 ? (dy / dist) * speed : -speed;

                    if (shotCount > 1 && dist > 0) {
                        const baseAngle = Math.atan2(dy, dx);
                        const finalAngle = baseAngle + angleOffset;
                        vx = Math.cos(finalAngle) * speed;
                        vy = Math.sin(finalAngle) * speed;
                    }

                    projectiles.push({
                        id: nextProjId(),
                        type: 'PYTHON',
                        x: player.x,
                        y: player.y,
                        vx,
                        vy,
                        damage,
                        radius: 5,
                        pierceRemaining: 1, // Single-target impact
                        homingTargetId: target.id
                    });
                }
                SoundFX.playShoot();
                cooldown = player.weaponLevel >= 4 ? 0.35 : 0.45;
            }
        } else if (player.activeWeapon === 'CPP') {
            const target = findNearestEnemy(player.x, player.y, enemies);
            const baseSpeed = 450 + (player.weaponLevel - 1) * 25;
            const damage = 18 + (player.weaponLevel - 1) * 6;
            const pierce = 5 + (player.weaponLevel - 1) * 2;
            const shotCount = player.weaponLevel >= 5 ? 3 : player.weaponLevel >= 3 ? 2 : 1;

            if (target) {
                const dx = target.x - player.x;
                const dy = target.y - player.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                for (let i = 0; i < shotCount; i++) {
                    const angleOffset = (i - (shotCount - 1) / 2) * 0.1;
                    let vx = 0;
                    let vy = -baseSpeed;

                    if (dist > 0) {
                        const baseAngle = Math.atan2(dy, dx);
                        const finalAngle = baseAngle + angleOffset;
                        vx = Math.cos(finalAngle) * baseSpeed;
                        vy = Math.sin(finalAngle) * baseSpeed;
                    }

                    projectiles.push({
                        id: nextProjId(),
                        type: 'CPP',
                        x: player.x,
                        y: player.y,
                        vx,
                        vy,
                        damage,
                        radius: 4,
                        pierceRemaining: pierce
                    });
                }
            } else {
                // Fail-safe default trajectory pointing up
                for (let i = 0; i < shotCount; i++) {
                    const angleOffset = (i - (shotCount - 1) / 2) * 0.1;
                    projectiles.push({
                        id: nextProjId(),
                        type: 'CPP',
                        x: player.x,
                        y: player.y,
                        vx: Math.sin(angleOffset) * baseSpeed,
                        vy: -Math.cos(angleOffset) * baseSpeed,
                        damage,
                        radius: 4,
                        pierceRemaining: pierce
                    });
                }
            }
            SoundFX.playShoot();
            cooldown = player.weaponLevel >= 4 ? 0.35 : 0.45;
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
            // Shield speed scales up with the player's weapon level
            const orbitSpeed = 3.2 + (player.weaponLevel - 1) * 0.5;
            const nextAngle = currentAngle + orbitSpeed * elapsed;
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
                const speed = 250 + (player.weaponLevel - 1) * 20;
                if (dist > 0) {
                    proj.vx = (dx / dist) * speed;
                    proj.vy = (dy / dist) * speed;
                }
            }

            // Move homing projectiles
            proj.x += proj.vx * elapsed;
            proj.y += proj.vy * elapsed;
        } else {
            // C++ piercing beam and BOSS_BULLET move in a strict straight line
            proj.x += proj.vx * elapsed;
            proj.y += proj.vy * elapsed;
        }
    }
}
