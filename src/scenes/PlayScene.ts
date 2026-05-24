import Phaser from 'phaser';
import { Simulator } from '../simulator/Simulator';
import type { PlayerInput, SimState } from '../simulator/types';
import { SoundFX } from '../renderer/SoundFX';

/**
 * PlayScene: Sandbox Wave Survival Scene.
 * Receives Stage and Weapon selection, executes the Stateless Simulator,
 * and renders game states dynamically using sharp, glowing monospace ASCII symbols.
 */
export class PlayScene extends Phaser.Scene {
    private simulator!: Simulator;
    private stageSelection = 1;
    private weaponSelection = 'PYTHON';

    // Track active key maps
    private wasdInputs!: {
        W: Phaser.Input.Keyboard.Key;
        A: Phaser.Input.Keyboard.Key;
        S: Phaser.Input.Keyboard.Key;
        D: Phaser.Input.Keyboard.Key;
    };
    private arrowCursors!: Phaser.Types.Input.Keyboard.CursorKeys;

    // Rendered Game Object Pools using ID mappings to avoid memory leakage
    private playerText!: Phaser.GameObjects.Text;
    private enemyTexts: Map<string, Phaser.GameObjects.Text> = new Map();
    private projectileTexts: Map<string, Phaser.GameObjects.Text> = new Map();
    private itemTexts: Map<string, Phaser.GameObjects.Text> = new Map();

    // HUD Display elements
    private sidebarText!: Phaser.GameObjects.Text;
    private sidebarBorder!: Phaser.GameObjects.Graphics;

    private lastHp = 100;
    private glitchTimer = 0;
    private playedEndSound = false;

    constructor() {
        super({ key: 'PlayScene' });
    }

    init(data: { stage?: number; weapon?: string }): void {
        this.stageSelection = data.stage ?? 1;
        this.weaponSelection = data.weapon ?? 'PYTHON';

        // Clean maps from previous sessions
        this.enemyTexts.clear();
        this.projectileTexts.clear();
        this.itemTexts.clear();

        this.lastHp = 100;
        this.glitchTimer = 0;
        this.playedEndSound = false;
    }

    create(): void {
        // Instantiate the Simulator confining the action sandbox to 580x600 px,
        // leaving the remaining right 220px of the 800x600 terminal for the diagnostics sidebar.
        this.simulator = new Simulator({
            width: 580,
            height: 600,
            stage: this.stageSelection,
            weapon: this.weaponSelection as any
        });

        // Initialize Keyboard Key mappings
        if (this.input.keyboard) {
            this.wasdInputs = {
                W: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W),
                A: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A),
                S: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S),
                D: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D)
            };
            this.arrowCursors = this.input.keyboard.createCursorKeys();
        }

        // Draw visual divider boundary separating sandbox play zone from side panel
        this.sidebarBorder = this.add.graphics();
        this.sidebarBorder.lineStyle(2, 0x00b300, 0.7); // Dim green borders
        this.sidebarBorder.lineBetween(585, 0, 585, 600);

        // Sidebar diagnostic text layout
        this.sidebarText = this.add.text(595, 20, '', {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '14px',
            color: '#00f500',
            lineSpacing: 7
        });

        // Create player character representation
        this.playerText = this.add.text(0, 0, '@', {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '22px',
            color: '#33ff33',
            fontStyle: 'bold'
        }).setOrigin(0.5);

        this.lastHp = this.simulator.state.player.hp;
    }

    update(_time: number, delta: number): void {
        // 1. Gather player inputs
        const inputState: PlayerInput = {
            up: this.wasdInputs.W.isDown || this.arrowCursors.up.isDown,
            down: this.wasdInputs.S.isDown || this.arrowCursors.down.isDown,
            left: this.wasdInputs.A.isDown || this.arrowCursors.left.isDown,
            right: this.wasdInputs.D.isDown || this.arrowCursors.right.isDown
        };

        // Update glitch timer
        if (this.glitchTimer > 0) {
            this.glitchTimer -= delta;
        }

        // 2. Tick the pure TS stateless simulation loop
        // Standardize time delta to max 50ms per frame to prevent extreme simulation jumps if tab goes inactive
        const cappedDelta = Math.min(delta, 50);
        this.simulator.tick(cappedDelta, inputState);

        const simState = this.simulator.state;

        // Check if player took damage to trigger screen shake and visual glitch
        if (simState.player.hp < this.lastHp) {
            this.cameras.main.shake(200, 0.02);
            this.glitchTimer = 350; // trigger visual corruption for 350ms
        }
        this.lastHp = simState.player.hp;

        // 3. Check for terminal victory or failure game conditions
        if (simState.isGameOver || simState.isStageClear) {
            if (simState.isGameOver && !this.playedEndSound) {
                SoundFX.playGameOver();
                this.playedEndSound = true;
            } else if (simState.isStageClear && !this.playedEndSound) {
                SoundFX.playVictory();
                this.playedEndSound = true;
            }

            this.cameras.main.flash(180, 200, 0, 0);
            this.time.delayedCall(200, () => {
                this.scene.start('ResultScene', {
                    isGameOver: simState.isGameOver,
                    isStageClear: simState.isStageClear,
                    gameTimer: simState.gameTimer,
                    killCount: simState.killCount,
                    weapon: this.weaponSelection,
                    stage: this.stageSelection
                });
            });
            return;
        }

        // 4. Render the current simulator state entities
        this.renderSimulation(simState);

        // 5. Update the diagnostics side dashboard panel
        this.renderSidebarHUD(simState);
    }

    /**
     * Translates coordinates and status parameters from simulator structures to sharp, colored ASCII characters.
     */
    private renderSimulation(state: SimState): void {
        // A. Position player '@' char
        if (this.glitchTimer > 0) {
            // Apply physical coordinate glitch shakes to player glyph
            this.playerText.setPosition(
                state.player.x + (Math.random() * 8 - 4),
                state.player.y + (Math.random() * 8 - 4)
            );
        } else {
            this.playerText.setPosition(state.player.x, state.player.y);
        }
        
        // Dynamic Player flicker if invulnerable
        if (state.player.invulnerableTimer > 0) {
            this.playerText.setVisible(Math.floor(state.player.invulnerableTimer * 20) % 2 === 0);
        } else {
            this.playerText.setVisible(true);
        }

        // B. Render minor/boss enemies
        const currentEnemyIds = new Set<string>();
        for (const enemy of state.enemies) {
            currentEnemyIds.add(enemy.id);

            let textObject = this.enemyTexts.get(enemy.id);
            if (!textObject) {
                // Instantiates dynamic font attributes depending on bug classification types
                let glyph = 'S';
                let color = '#ff3333'; // Red default
                let size = '16px';
                let style = 'normal';

                switch (enemy.type) {
                    case 'SYNTAX_ERROR':
                        glyph = 'S';
                        color = '#ff4444'; // Red error alert
                        size = '16px';
                        break;
                    case 'NULL_POINTER':
                        glyph = 'N';
                        color = '#ff00ff'; // Vibrant Cyan magenta alert
                        size = '14px';
                        style = 'bold';
                        break;
                    case 'SEG_FAULT':
                        glyph = 'F';
                        color = '#ffb000'; // Slow Tank Amber error
                        size = '22px';
                        style = 'bold';
                        break;
                    case 'HEAL_BUG':
                        glyph = 'H';
                        color = '#00ffff'; // Support healing blue fleeing bug
                        size = '16px';
                        break;
                    case 'BOSS':
                        glyph = 'B';
                        color = '#ff0000'; // Blinking main boss
                        size = '32px';
                        style = 'bold';
                        break;
                }

                textObject = this.add.text(enemy.x, enemy.y, glyph, {
                    fontFamily: 'Courier New, Courier, Consolas, monospace',
                    fontSize: size,
                    color: color,
                    fontStyle: style
                }).setOrigin(0.5);

                this.enemyTexts.set(enemy.id, textObject);
            } else {
                // Update coordinates
                textObject.setPosition(enemy.x, enemy.y);
                // Flash Boss characters
                if (enemy.type === 'BOSS') {
                    textObject.setVisible(Math.floor(state.gameTimer * 5) % 2 === 0 ? true : false);
                }
            }
        }

        // Garbage collect dead bugs
        for (const [id, txt] of this.enemyTexts.entries()) {
            if (!currentEnemyIds.has(id)) {
                txt.destroy();
                this.enemyTexts.delete(id);
            }
        }

        // C. Render weapon projectiles
        const currentProjIds = new Set<string>();
        for (const proj of state.projectiles) {
            currentProjIds.add(proj.id);

            let textObject = this.projectileTexts.get(proj.id);
            if (!textObject) {
                let glyph = '*';
                let color = '#33ff33';
                let size = '12px';

                switch (proj.type) {
                    case 'PYTHON':
                        glyph = 'o';
                        color = '#33ff33';
                        size = '11px';
                        break;
                    case 'CPP':
                        glyph = '=';
                        color = '#ffffff';
                        size = '12px';
                        break;
                    case 'JAVA':
                        glyph = '■';
                        color = '#ffff33';
                        size = '14px';
                        break;
                }

                textObject = this.add.text(proj.x, proj.y, glyph, {
                    fontFamily: 'Courier New, Courier, Consolas, monospace',
                    fontSize: size,
                    color: color,
                    fontStyle: 'bold'
                }).setOrigin(0.5);

                this.projectileTexts.set(proj.id, textObject);
            } else {
                textObject.setPosition(proj.x, proj.y);
            }
        }

        // Garbage collect dead projectiles
        for (const [id, txt] of this.projectileTexts.entries()) {
            if (!currentProjIds.has(id)) {
                txt.destroy();
                this.projectileTexts.delete(id);
            }
        }

        // D. Render dropped capsule items
        const currentItemIds = new Set<string>();
        for (const item of state.items) {
            currentItemIds.add(item.id);

            let textObject = this.itemTexts.get(item.id);
            if (!textObject) {
                textObject = this.add.text(item.x, item.y, '♥', {
                    fontFamily: 'Courier New, Courier, Consolas, monospace',
                    fontSize: '16px',
                    color: '#00ff66',
                    fontStyle: 'bold'
                }).setOrigin(0.5);

                this.itemTexts.set(item.id, textObject);
            } else {
                textObject.setPosition(item.x, item.y);
            }
        }

        // Garbage collect resolved capsules
        for (const [id, txt] of this.itemTexts.entries()) {
            if (!currentItemIds.has(id)) {
                txt.destroy();
                this.itemTexts.delete(id);
            }
        }
    }

    /**
     * Ticks sidebar details showing player HP progress bars, compilation timer and diagnostics logs.
     */
    private renderSidebarHUD(state: SimState): void {
        // Compile HP Bar [██████░░░░]
        const hpPercent = Math.max(0, state.player.hp / state.player.maxHp);
        const barSegmentsCount = 10;
        const activeSegments = Math.round(hpPercent * barSegmentsCount);
        const emptySegments = barSegmentsCount - activeSegments;
        const hpBarStr = '[' + '█'.repeat(activeSegments) + '░'.repeat(emptySegments) + ']';

        // Compile Formatted Timer MM:SS.CC
        const minutes = Math.floor(state.gameTimer / 60);
        const seconds = Math.floor(state.gameTimer % 60);
        const centiseconds = Math.floor((state.gameTimer % 1) * 100);
        const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`;

        // Determine System Status Strings
        let statusStr = "SYSTEM_NORMAL";
        if (state.player.invulnerableTimer > 0) {
            statusStr = "SHIELD_ACTIVE";
        } else if (state.gameTimer >= 30 && state.gameTimer <= 33) {
            statusStr = "INDENTATION_PANIC";
        } else if (state.bossSpawned) {
            statusStr = "BOSS_INTRUSION";
        }

        // Compile and output dynamic HUD lines
        const lines = [
            "=======================",
            "  JIYOON IDE SANDBOX   ",
            "=======================",
            " [SYSTEM DIAGNOSTICS]  ",
            "-----------------------",
            ` ENV:      STAGE_${state.stageSelection}`,
            ` WEAPON:   ${state.player.activeWeapon}.PY`,
            ` RUN TIME: ${timeStr}`,
            ` RESOLVED: ${state.killCount.toString().padStart(3, '0')} BUGS`,
            "-----------------------",
            " [PLAYER CORE COORD]   ",
            ` X: ${Math.round(state.player.x).toString().padStart(3, '0')} | Y: ${Math.round(state.player.y).toString().padStart(3, '0')}`,
            "-----------------------",
            " [PLAYER CORE HEALTH]  ",
            ` CORE HP:  ${state.player.hp.toString().padStart(3, ' ')} / ${state.player.maxHp}`,
            ` HP BAR:   ${hpBarStr}`,
            ` STATUS:   ${statusStr}`,
            "-----------------------",
            " [MEMORY ANALYTICS]    ",
            ` STACK PT: 0x${(1024 + Math.round(state.gameTimer * 8)).toString(16).toUpperCase()}`,
            ` HEAP LEK: ${(0.05 + state.killCount * 0.12).toFixed(2)} MB`,
            ` THREADS:  ${(4 + Math.floor(state.gameTimer / 10)).toString()} ACTIVE`,
            "======================="
        ];

        if (this.glitchTimer > 0 && Math.random() < 0.5) {
            // Inject hardware heap corruption dump symbols inside visual log lines
            const glitchLines = [...lines];
            for (let i = 0; i < glitchLines.length; i++) {
                if (Math.random() < 0.25) {
                    glitchLines[i] = `!!! HEAP CORRUPTION DETECTED: 0x${Math.floor(Math.random() * 16777215).toString(16).toUpperCase()} !!!`;
                }
            }
            this.sidebarText.setText(glitchLines.join('\n'));
            this.sidebarText.setColor('#ff3333');
            this.sidebarText.setPosition(
                595 + (Math.random() * 10 - 5),
                20 + (Math.random() * 10 - 5)
            );
        } else {
            this.sidebarText.setText(lines.join('\n'));
            this.sidebarText.setColor('#00f500');
            this.sidebarText.setPosition(595, 20);
        }
    }
}
