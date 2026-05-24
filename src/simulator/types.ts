export interface Position {
    x: number;
    y: number;
}

export interface Velocity {
    vx: number;
    vy: number;
}

export type WeaponType = 'PYTHON' | 'CPP' | 'JAVA';

export type EnemyType = 'SYNTAX_ERROR' | 'NULL_POINTER' | 'SEG_FAULT' | 'HEAL_BUG' | 'BOSS';

export interface PlayerInput {
    up: boolean;
    down: boolean;
    left: boolean;
    right: boolean;
}

export interface SimPlayer {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    maxHp: number;
    hp: number;
    speed: number;
    activeWeapon: WeaponType;
    invulnerableTimer: number;
}

export interface SimEnemy {
    id: string;
    type: EnemyType;
    x: number;
    y: number;
    vx: number;
    vy: number;
    hp: number;
    maxHp: number;
    speed: number;
    radius: number;
    damage: number;
    customAIState?: number; // Used for fleeing logic or boss patterns
}

export interface SimProjectile {
    id: string;
    type: WeaponType;
    x: number;
    y: number;
    vx: number;
    vy: number;
    damage: number;
    radius: number;
    pierceRemaining: number;
    homingTargetId?: string; // Used for homing projectiles (Python)
    angle?: number; // Used for orbiting projectiles (Java)
}

export interface SimItem {
    id: string;
    x: number;
    y: number;
    radius: number;
    healAmount: number;
}

export interface SimEvent {
    id: string;
    triggerTime: number;
    name: string;
    triggered: boolean;
}

export interface SimState {
    width: number;
    height: number;
    player: SimPlayer;
    enemies: SimEnemy[];
    projectiles: SimProjectile[];
    items: SimItem[];
    gameTimer: number;
    killCount: number;
    bossSpawned: boolean;
    bossDefeated: boolean;
    isStageClear: boolean;
    isGameOver: boolean;
    stageSelection: number; // 1 = Main Loop Corruption, 2 = Heap Leak Inferno
}
