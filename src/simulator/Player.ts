import type { SimPlayer, PlayerInput, WeaponType } from './types';

/**
 * Creates a new simulated player state.
 * @param x Initial X coordinate
 * @param y Initial Y coordinate
 * @param activeWeapon The selected starting weapon
 */
export function createPlayer(x: number, y: number, activeWeapon: WeaponType): SimPlayer {
    return {
        x,
        y,
        vx: 0,
        vy: 0,
        radius: 12, // Hitbox radius
        maxHp: 100,
        hp: 100,
        speed: 200, // Speed in pixels per second
        activeWeapon,
        invulnerableTimer: 0, // Duration remaining of invulnerability
        xp: 0,
        level: 1,
        xpNeeded: 10,
        weaponLevel: 1,
        safeModeTimer: 0
    };
}

/**
 * Ticks the player simulation logic, including movements and invulnerability timers.
 * @param player The current player state reference to modify
 * @param input Player inputs from keyboard cursors
 * @param dt Delta time in milliseconds
 */
export function updatePlayer(player: SimPlayer, input: PlayerInput, dt: number): void {
    let dx = 0;
    let dy = 0;

    if (input.up) {
        dy -= 1;
    }
    if (input.down) {
        dy += 1;
    }
    if (input.left) {
        dx -= 1;
    }
    if (input.right) {
        dx += 1;
    }

    // Normalize diagonal movement speed so moving diagonally isn't faster
    if (dx !== 0 && dy !== 0) {
        const factor = Math.sqrt(0.5); // equivalent to 1 / Math.sqrt(2)
        dx *= factor;
        dy *= factor;
    }

    player.vx = dx * player.speed;
    player.vy = dy * player.speed;

    // Shift player position relative to time step
    player.x += player.vx * (dt / 1000);
    player.y += player.vy * (dt / 1000);

    // Tick down invulnerability frames
    if (player.invulnerableTimer > 0) {
        player.invulnerableTimer = Math.max(0, player.invulnerableTimer - dt / 1000);
    }

    // Tick down Safe Mode timer
    if (player.safeModeTimer > 0) {
        player.safeModeTimer = Math.max(0, player.safeModeTimer - dt / 1000);
        // While safe mode is active, maintain player invulnerability
        if (player.invulnerableTimer < player.safeModeTimer) {
            player.invulnerableTimer = player.safeModeTimer;
        }
    }
}
