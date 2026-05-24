import type { SimState, PlayerInput, WeaponType } from './types';
import { createPlayer, updatePlayer } from './Player';
import { updateEnemy } from './Enemy';
import { fireWeapon, updateProjectiles } from './Weapon';
import { handleTimelineEvents } from './EventManager';
import { SoundFX } from '../renderer/SoundFX';

/**
 * Main Stateless Simulator Engine.
 * Manages game loop ticks, clamping limits, circular collision detection, and win/loss verification.
 */
export class Simulator {
    public state: SimState;
    private enemyIdCounter = 0;
    private projIdCounter = 0;
    private itemIdCounter = 0;
    private weaponCooldown = 0;

    constructor(config: { width: number; height: number; stage: number; weapon: WeaponType }) {
        const player = createPlayer(config.width / 2, config.height / 2, config.weapon);

        this.state = {
            width: config.width,
            height: config.height,
            player,
            enemies: [],
            projectiles: [],
            items: [],
            gameTimer: 0,
            killCount: 0,
            bossSpawned: false,
            bossDefeated: false,
            isStageClear: false,
            isGameOver: false,
            stageSelection: config.stage
        };
    }

    private nextEnemyId = (): string => {
        this.enemyIdCounter++;
        return `enemy_${this.enemyIdCounter}`;
    };

    private nextProjId = (): string => {
        this.projIdCounter++;
        return `proj_${this.projIdCounter}`;
    };

    private nextItemId = (): string => {
        this.itemIdCounter++;
        return `item_${this.itemIdCounter}`;
    };

    /**
     * Ticks the core logic steps by a fraction of time step delta.
     * @param dt Delta time in milliseconds
     * @param input Raw player input keys flag indicators
     */
    public tick(dt: number, input: PlayerInput): void {
        // Prevent updates if game state has reached terminal status
        if (this.state.isGameOver || this.state.isStageClear) {
            return;
        }

        // 1. Move Player
        updatePlayer(this.state.player, input, dt);

        // Clamp player strictly inside visual canvas borders
        const pRadius = this.state.player.radius;
        this.state.player.x = Math.max(pRadius, Math.min(this.state.width - pRadius, this.state.player.x));
        this.state.player.y = Math.max(pRadius, Math.min(this.state.height - pRadius, this.state.player.y));

        // 2. Coordinate spawning waves / timeline events
        handleTimelineEvents(this.state, dt, this.nextEnemyId);

        // Enforce maximum active enemy limit of 50 bugs to guarantee consistent frame pacing
        if (this.state.enemies.length > 50) {
            const boss = this.state.enemies.find(e => e.type === 'BOSS');
            let otherEnemies = this.state.enemies.filter(e => e.type !== 'BOSS');
            const allowedOthersCount = boss ? 49 : 50;
            if (otherEnemies.length > allowedOthersCount) {
                otherEnemies = otherEnemies.slice(0, allowedOthersCount);
            }
            this.state.enemies = boss ? [...otherEnemies, boss] : otherEnemies;
        }

        // 3. Execute weapon triggers and firing rates
        this.weaponCooldown = fireWeapon(
            this.state.player,
            this.state.enemies,
            this.state.projectiles,
            this.weaponCooldown,
            dt,
            this.nextProjId
        );

        // 4. Tick projectile paths
        updateProjectiles(this.state.projectiles, this.state.enemies, this.state.player, dt);

        // 5. Tick enemy movements and behaviors
        for (const enemy of this.state.enemies) {
            updateEnemy(enemy, this.state.player, dt);

            // Clamp minor enemies inside coordinate margins to keep active in battleground
            const eRad = enemy.radius;
            enemy.x = Math.max(eRad, Math.min(this.state.width - eRad, enemy.x));
            enemy.y = Math.max(eRad, Math.min(this.state.height - eRad, enemy.y));
        }

        // 6. Mathematical Collision Resolution Pipeline
        this.resolveCollisions();

        // 7. Flush out expired / inactive elements
        this.cleanupEntities();

        // 8. Verify Win / Loss constraints
        this.checkGameConditions();
    }

    /**
     * Resolves interactions between active game layers: bullets vs bugs, bugs vs player, items vs player.
     */
    private resolveCollisions(): void {
        const player = this.state.player;
        const enemies = this.state.enemies;
        const projectiles = this.state.projectiles;
        const items = this.state.items;

        // A. Projectiles vs Enemies Collision Resolution
        for (const proj of projectiles) {
            if (proj.pierceRemaining <= 0) continue;

            for (const enemy of enemies) {
                if (enemy.hp <= 0) continue;

                const dx = proj.x - enemy.x;
                const dy = proj.y - enemy.y;
                const collisionDist = proj.radius + enemy.radius;

                // Box-bounding pre-filtering before heavy circular check
                if (Math.abs(dx) < collisionDist && Math.abs(dy) < collisionDist) {
                    // Squared distance checks to bypass heavy Math.sqrt execution
                    if (dx * dx + dy * dy < collisionDist * collisionDist) {
                        enemy.hp -= proj.damage;
                        proj.pierceRemaining--;

                        if (proj.type === 'JAVA') {
                            SoundFX.playShield();
                        }

                        // Trigger death routines
                        if (enemy.hp <= 0) {
                            this.state.killCount++;
                            SoundFX.playExplosion();

                            // HealBug spawns recovery capsule upon resolution
                            if (enemy.type === 'HEAL_BUG') {
                                items.push({
                                    id: this.nextItemId(),
                                    x: enemy.x,
                                    y: enemy.y,
                                    radius: 8,
                                    healAmount: 25 // Recovers 25 points of health
                                });
                            }
                        }

                        // Break early if projectile has expended its piercing limit
                        if (proj.pierceRemaining <= 0) {
                            break;
                        }
                    }
                }
            }
        }

        // B. Enemies vs Player Collision Resolution
        if (player.hp > 0 && player.invulnerableTimer <= 0) {
            for (const enemy of enemies) {
                if (enemy.hp <= 0) continue;

                const dx = player.x - enemy.x;
                const dy = player.y - enemy.y;
                const collisionDist = player.radius + enemy.radius;

                // Box-bounding pre-filtering before heavy circular check
                if (Math.abs(dx) < collisionDist && Math.abs(dy) < collisionDist) {
                    if (dx * dx + dy * dy < collisionDist * collisionDist) {
                        if (enemy.damage > 0) {
                            player.hp = Math.max(0, player.hp - enemy.damage);
                            player.invulnerableTimer = 1.0; // 1 full second of safety buffer
                            console.log(`[COLLISION] Hit by ${enemy.type}! Player HP: ${player.hp}`);
                            SoundFX.playHit();
                            break; // Player triggered invuln; no further impact calculations this tick
                        }
                    }
                }
            }
        }

        // C. Health Capsule Items vs Player Collision Resolution
        if (player.hp > 0) {
            for (let i = items.length - 1; i >= 0; i--) {
                const item = items[i];
                const dx = player.x - item.x;
                const dy = player.y - item.y;
                const collisionDist = player.radius + item.radius;

                // Box-bounding pre-filtering before heavy circular check
                if (Math.abs(dx) < collisionDist && Math.abs(dy) < collisionDist) {
                    if (dx * dx + dy * dy < collisionDist * collisionDist) {
                        player.hp = Math.min(player.maxHp, player.hp + item.healAmount);
                        console.log(`[ITEM] HEAL capsule absorbed. Player HP: ${player.hp}`);
                        SoundFX.playPowerUp();
                        items.splice(i, 1);
                    }
                }
            }
        }
    }

    /**
     * Garbage collects out of bounds and dead projectiles/enemies.
     */
    private cleanupEntities(): void {
        this.state.projectiles = this.state.projectiles.filter(proj => {
            if (proj.pierceRemaining <= 0) return false;
            if (proj.type === 'JAVA') return true; // Orbiting block persistent
            return (
                proj.x >= -60 &&
                proj.x <= this.state.width + 60 &&
                proj.y >= -60 &&
                proj.y <= this.state.height + 60
            );
        });

        this.state.enemies = this.state.enemies.filter(e => e.hp > 0);
    }

    /**
     * Checks if current ticks trigger game terminal constraints (HP <= 0 or Boss resolved).
     */
    private checkGameConditions(): void {
        if (this.state.player.hp <= 0) {
            this.state.isGameOver = true;
            console.log("[TERMINAL] Game Over! Core player health is 0.");
        }

        if (this.state.bossSpawned && this.state.bossDefeated) {
            this.state.isStageClear = true;
            console.log("[TERMINAL] Stage Clear! Boss compiled and debugged.");
        }
    }
}
