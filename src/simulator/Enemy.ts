import type { SimEnemy, EnemyType, SimPlayer, SimProjectile } from './types';

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
        customAIState: 0,
        phase: 1,
        dashTimer: 0,
        dashTargetX: 0,
        dashTargetY: 0,
        isDashing: false,
        shootCooldown: 1.0
    };
}

/**
 * Ticks an individual enemy's movement vectors and custom logic.
 * @param enemy The enemy entity to update
 * @param player The current player state reference
 * @param dt Delta time in milliseconds
 * @param projectiles Reference to projectiles array to add spawned boss bullets
 * @param nextProjId ID generator callback for spawned boss bullets
 */
export function updateEnemy(
    enemy: SimEnemy,
    player: SimPlayer,
    dt: number,
    projectiles?: SimProjectile[],
    nextProjId?: () => string
): void {
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
            // Two-Phase Boss AI: 'Jang Seonhyeong'
            // Phase 1 (HP > 50%): Orbital hovering around the player while firing radiant bullet rings
            // Phase 2 (HP <= 50%): Fast red glitch hyper-dashes targeting locked player positions

            // Determine current active phase
            const hpPercent = enemy.hp / enemy.maxHp;
            if (hpPercent <= 0.5) {
                if (enemy.phase !== 2) {
                    enemy.phase = 2;
                    enemy.isDashing = false;
                    enemy.dashTimer = 0;
                    console.log("[BOSS] HP <= 50%! Transferred to Phase 2: Red Glitch Hyper-Dashes!");
                }
            } else {
                enemy.phase = 1;
            }

            if (enemy.phase === 1) {
                // Orbital Hovering AI
                const currentAngle = enemy.customAIState || 0;
                const nextAngle = currentAngle + 0.6 * (dt / 1000); // 0.6 rads/sec rotation speed
                enemy.customAIState = nextAngle;

                // Orbiting position 180px away from the player
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

                // Phase 1: Radiant Bullets firing ring patterns
                if (enemy.shootCooldown === undefined) {
                    enemy.shootCooldown = 1.0;
                }
                enemy.shootCooldown -= dt / 1000;
                if (enemy.shootCooldown <= 0 && projectiles && nextProjId) {
                    enemy.shootCooldown = 2.0; // Fire a radiant burst every 2 seconds
                    
                    const bulletCount = 6;
                    const bulletSpeed = 150;
                    const damage = 15;
                    for (let i = 0; i < bulletCount; i++) {
                        const angle = (i * 2 * Math.PI) / bulletCount;
                        projectiles.push({
                            id: nextProjId(),
                            type: 'BOSS_BULLET',
                            x: enemy.x,
                            y: enemy.y,
                            vx: Math.cos(angle) * bulletSpeed,
                            vy: Math.sin(angle) * bulletSpeed,
                            damage,
                            radius: 6,
                            pierceRemaining: 1,
                            isEnemy: true
                        });
                    }
                }
            } else {
                // Phase 2: Red Glitch Hyper-Dashes State Machine
                if (enemy.isDashing) {
                    // Dashing: Continue traveling towards locked targets
                    if (enemy.dashTimer === undefined) enemy.dashTimer = 0;
                    enemy.dashTimer -= dt / 1000;

                    if (enemy.dashTimer <= 0) {
                        // Dash completes, stop dashing, trigger cooldown cycle
                        enemy.isDashing = false;
                        enemy.dashTimer = 0; // Reset cooldown timer to 0
                        enemy.vx = 0;
                        enemy.vy = 0;

                        // Shoot a 3-bullet narrow burst directly towards the player
                        if (projectiles && nextProjId && dist > 0) {
                            const baseAngle = Math.atan2(dy, dx);
                            const bulletSpeed = 200;
                            const bulletDamage = 18;
                            for (let i = -1; i <= 1; i++) {
                                const angle = baseAngle + i * 0.2;
                                projectiles.push({
                                    id: nextProjId(),
                                    type: 'BOSS_BULLET',
                                    x: enemy.x,
                                    y: enemy.y,
                                    vx: Math.cos(angle) * bulletSpeed,
                                    vy: Math.sin(angle) * bulletSpeed,
                                    damage: bulletDamage,
                                    radius: 6,
                                    pierceRemaining: 1,
                                    isEnemy: true
                                });
                            }
                        }
                    }
                } else {
                    // Resting/Hovering between dashes
                    if (enemy.dashTimer === undefined) enemy.dashTimer = 0;
                    enemy.dashTimer += dt / 1000;

                    if (enemy.dashTimer >= 2.0) {
                        // Trigger next dash, lock on to player position
                        enemy.dashTargetX = player.x;
                        enemy.dashTargetY = player.y;
                        enemy.isDashing = true;
                        enemy.dashTimer = 0.8; // Dash duration 800ms

                        const tx = enemy.dashTargetX - enemy.x;
                        const ty = enemy.dashTargetY - enemy.y;
                        const tdist = Math.sqrt(tx * tx + ty * ty);
                        const dashSpeed = 380; // Glitch speed burst!

                        if (tdist > 0) {
                            enemy.vx = (tx / tdist) * dashSpeed;
                            enemy.vy = (ty / tdist) * dashSpeed;
                        } else {
                            enemy.vx = dashSpeed;
                            enemy.vy = 0;
                        }
                    } else {
                        // Hover slowly directly towards the player
                        const slowSpeed = 50;
                        if (dist > 5) {
                            enemy.vx = (dx / dist) * slowSpeed;
                            enemy.vy = (dy / dist) * slowSpeed;
                        } else {
                            enemy.vx = 0;
                            enemy.vy = 0;
                        }
                    }
                }
            }
            break;
    }

    // Apply movement
    enemy.x += enemy.vx * (dt / 1000);
    enemy.y += enemy.vy * (dt / 1000);
}
