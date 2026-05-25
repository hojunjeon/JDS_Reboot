import Phaser from 'phaser';
import { Simulator } from '../simulator/Simulator';
import type { PlayerInput, SimState } from '../simulator/types';
import { SoundFX } from '../renderer/SoundFX';

// Collection of real code snippets scrolling down the background
const CODE_SNIPPETS = [
    "function tick(dt) {",
    "  let dx = player.x - enemy.x;",
    "  if (invulnerable) return;",
    "  resolveCollisions();",
    "  sys_status = 'OK';",
    "  #include <iostream>",
    "  std::cout << 'JDS_INIT';",
    "  public class Sandbox {",
    "  import * as phaser from 'phaser';",
    "  const cap = Math.min(delta, 50);",
    "  if (bossDefeated) compile();",
    "  Object.assign(state, {",
    "  while (activeThreads < 8) {"
];

/**
 * PlayScene: Sandbox Wave Survival Scene.
 * Receives Stage and Weapon selection, executes the Stateless Simulator,
 * and renders game states dynamically using high-fidelity pixel sprites,
 * scrolling IDE code background, orbiting shield trajectories, and interactive level-up cards.
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
    private playerSprite!: Phaser.GameObjects.Image;
    private enemyTexts: Map<string, Phaser.GameObjects.Text> = new Map();
    private projectileTexts: Map<string, Phaser.GameObjects.Text> = new Map();
    private itemTexts: Map<string, Phaser.GameObjects.Text> = new Map();

    // HUD & Polish Display elements
    private sidebarText!: Phaser.GameObjects.Text;
    private sidebarBorder!: Phaser.GameObjects.Graphics;
    private sidebarGraphics!: Phaser.GameObjects.Graphics;
    private sidebarPortrait!: Phaser.GameObjects.Image;
    private javaOrbitGraphics!: Phaser.GameObjects.Graphics;
    private playerHpBar!: Phaser.GameObjects.Graphics;

    // Scrolling code background systems
    private codeLines: Array<{ text: Phaser.GameObjects.Text; speed: number }> = [];

    // Interactive level-up upgrade card overlays (Vampire Survivors style)
    private isLevelUpPaused = false;
    private levelUpGroup!: Phaser.GameObjects.Container;
    private selectedCardIndex = 0; // 0, 1, or 2
    private levelUpCards: Array<{ title: string; desc: string; action: () => void }> = [];
    private lastLevel = 1;

    private lastHp = 100;
    private glitchTimer = 0;
    private playedEndSound = false;

    constructor() {
        super({ key: 'PlayScene' });
    }

    init(data: { stage?: number; weapon?: string }): void {
        this.stageSelection = data.stage ?? 1;
        this.weaponSelection = data.weapon ?? 'PYTHON';

        // Clean maps and arrays from previous sessions
        this.enemyTexts.clear();
        this.projectileTexts.clear();
        this.itemTexts.clear();
        this.codeLines = [];

        this.lastHp = 100;
        this.glitchTimer = 0;
        this.playedEndSound = false;
        this.isLevelUpPaused = false;
        this.selectedCardIndex = 0;
        this.lastLevel = 1;
    }

    create(): void {
        // 1. Instantiate the Simulator confining the action sandbox to 580x600 px,
        // leaving the remaining right 220px of the 800x600 terminal for the diagnostics sidebar.
        this.simulator = new Simulator({
            width: 580,
            height: 600,
            stage: this.stageSelection,
            weapon: this.weaponSelection as any
        });

        this.lastLevel = this.simulator.state.player.level;

        // 2. Render premium IDE blue-slate gradient background asset
        const bg = this.add.image(0, 0, 'bg_alt1').setOrigin(0, 0);
        bg.setDisplaySize(585, 600);

        // 3. Render scrolling code background overlay
        for (let i = 0; i < 15; i++) {
            const x = Phaser.Math.Between(15, 380);
            const y = Phaser.Math.Between(0, 600);
            const speed = Phaser.Math.Between(15, 35);
            const snippet = CODE_SNIPPETS[Phaser.Math.Between(0, CODE_SNIPPETS.length - 1)];

            const txt = this.add.text(x, y, snippet, {
                fontFamily: 'Courier New, Courier, Consolas, monospace',
                fontSize: '13px',
                color: '#00f0ff', // Cyber neon cyan code color
            });
            txt.setAlpha(0.06);
            txt.setDepth(-10); // Placed way behind characters and action layers

            this.codeLines.push({ text: txt, speed });
        }

        // 4. Initialize Keyboard Key mappings
        if (this.input.keyboard) {
            this.wasdInputs = {
                W: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W),
                A: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A),
                S: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S),
                D: this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D)
            };
            this.arrowCursors = this.input.keyboard.createCursorKeys();
        }

        // 5. Draw visual divider boundary separating sandbox play zone from side panel
        this.sidebarBorder = this.add.graphics();
        this.sidebarBorder.lineStyle(2, 0x00b300, 0.7); // Dim green borders
        this.sidebarBorder.lineBetween(585, 0, 585, 600);

        // 6. Draw Player Avatar Goggles Frame & Image at the top of the sidebar HUD
        this.sidebarGraphics = this.add.graphics();
        this.sidebarGraphics.lineStyle(2, 0x00f500, 0.7);
        this.sidebarGraphics.strokeRect(645, 20, 100, 100);
        this.sidebarGraphics.lineStyle(1, 0x00b300, 0.4);
        this.sidebarGraphics.strokeRect(641, 16, 108, 108);

        this.sidebarPortrait = this.add.image(695, 70, 'player_alt3');
        this.sidebarPortrait.setDisplaySize(80, 80);

        // 7. Sidebar diagnostic text layout placed below the portrait
        this.sidebarText = this.add.text(595, 145, '', {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '11px',
            color: '#00f500',
            lineSpacing: 5
        });

        // 8. Create player character representation (using locked player_alt3 sprite)
        this.playerSprite = this.add.image(0, 0, 'player_alt3').setOrigin(0.5);
        this.playerSprite.setDisplaySize(32, 32);

        // 9. Graphics objects for orbit and HUD HP bars
        this.javaOrbitGraphics = this.add.graphics();
        this.javaOrbitGraphics.setDepth(-1); // Orbit path lines should go behind characters
        this.playerHpBar = this.add.graphics();

        // 10. Instantiate Level Up Upgrade pauses overlay container
        this.levelUpGroup = this.add.container(0, 0);
        this.levelUpGroup.setDepth(100); // Renders on top of absolutely everything else
        this.levelUpGroup.setVisible(false);

        this.lastHp = this.simulator.state.player.hp;
    }

    update(_time: number, delta: number): void {
        const cappedDelta = Math.min(delta, 50);

        // Handle level up overlays inputs if active
        if (this.isLevelUpPaused) {
            this.handleLevelUpInputs();
            return;
        }

        // 1. Gather player inputs
        const inputState: PlayerInput = {
            up: this.wasdInputs.W.isDown || this.arrowCursors.up.isDown,
            down: this.wasdInputs.S.isDown || this.arrowCursors.down.isDown,
            left: this.wasdInputs.A.isDown || this.arrowCursors.left.isDown,
            right: this.wasdInputs.D.isDown || this.arrowCursors.right.isDown
        };

        // Update glitch timer
        if (this.glitchTimer > 0) {
            this.glitchTimer -= cappedDelta;
        }

        // 2. Scroll background code lines
        for (const line of this.codeLines) {
            line.text.y += line.speed * (cappedDelta / 1000);
            if (line.text.y > 600) {
                line.text.y = -20;
                line.text.x = Phaser.Math.Between(15, 380);
                line.text.setText(CODE_SNIPPETS[Phaser.Math.Between(0, CODE_SNIPPETS.length - 1)]);
            }
        }

        // 3. Tick the pure TS stateless simulation loop
        // Standardize time delta to max 50ms per frame to prevent extreme simulation jumps if tab goes inactive
        this.simulator.tick(cappedDelta, inputState);

        const simState = this.simulator.state;

        // Check if player took damage to trigger screen shake and visual glitch
        if (simState.player.hp < this.lastHp) {
            this.cameras.main.shake(200, 0.02);
            this.glitchTimer = 350; // trigger visual corruption for 350ms
        }
        this.lastHp = simState.player.hp;

        // Check if player leveled up to trigger upgrade cards pauses overlay (Vampire Survivors style)
        if (simState.player.level > this.lastLevel) {
            this.triggerLevelUpOverlay();
            this.lastLevel = simState.player.level;
            return;
        }

        // 4. Check for terminal victory or failure game conditions
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

        // 5. Render the current simulator state entities
        this.renderSimulation(simState);

        // 6. Update the diagnostics side dashboard panel
        this.renderSidebarHUD(simState);
    }

    /**
     * Translates coordinates and status parameters from simulator structures to sharp, colored ASCII characters.
     */
    private renderSimulation(state: SimState): void {
        // A. Position player 'player_alt3' sprite
        if (this.glitchTimer > 0) {
            // Apply physical coordinate glitch shakes to player sprite
            this.playerSprite.setPosition(
                state.player.x + (Math.random() * 8 - 4),
                state.player.y + (Math.random() * 8 - 4)
            );
        } else {
            this.playerSprite.setPosition(state.player.x, state.player.y);
        }
        
        // Dynamic Player flicker if invulnerable
        if (state.player.invulnerableTimer > 0) {
            this.playerSprite.setVisible(Math.floor(state.player.invulnerableTimer * 20) % 2 === 0);
        } else {
            this.playerSprite.setVisible(true);
        }

        // Draw mini HP HUD bar below the player
        this.playerHpBar.clear();
        if (state.player.hp < state.player.maxHp && state.player.hp > 0) {
            const barW = 36;
            const barH = 5;
            const barX = state.player.x - barW / 2;
            const barY = state.player.y + 20;

            // HP Bar Background (red)
            this.playerHpBar.fillStyle(0xcc3333, 0.8);
            this.playerHpBar.fillRect(barX, barY, barW, barH);

            // HP Bar Foreground (green)
            const hpRatio = state.player.hp / state.player.maxHp;
            this.playerHpBar.fillStyle(0x33ff33, 0.9);
            this.playerHpBar.fillRect(barX, barY, barW * hpRatio, barH);

            // HP Bar Border
            this.playerHpBar.lineStyle(1, 0x000000, 1);
            this.playerHpBar.strokeRect(barX, barY, barW, barH);
        }

        // Draw Java protective orbiting ring path
        this.javaOrbitGraphics.clear();
        if (state.player.activeWeapon === 'JAVA') {
            this.javaOrbitGraphics.lineStyle(1.5, 0xffff33, 0.12);
            this.javaOrbitGraphics.strokeCircle(state.player.x, state.player.y, 70);
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
                        break;
                    case 'SEG_FAULT':
                        glyph = 'F';
                        color = '#ffb000'; // Slow Tank Amber error
                        size = '22px';
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
                        break;
                }

                textObject = this.add.text(enemy.x, enemy.y, glyph, {
                    fontFamily: 'Courier New, Courier, Consolas, monospace',
                    fontSize: size,
                    color: color,
                    fontStyle: 'bold'
                }).setOrigin(0.5);

                this.enemyTexts.set(enemy.id, textObject);
            } else {
                // Update coordinates
                textObject.setPosition(enemy.x, enemy.y);
                // Flash Boss characters in Phase 2 dashed glitches
                if (enemy.type === 'BOSS') {
                    const customCast = enemy as any;
                    const isDashing = customCast.isDashing || false;
                    if (isDashing) {
                        textObject.setVisible(Math.floor(state.gameTimer * 20) % 2 === 0);
                        textObject.setColor('#ff3333');
                    } else {
                        textObject.setVisible(true);
                        textObject.setColor(customCast.phase === 2 ? '#ff0055' : '#ff0000');
                    }
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
                    case 'BOSS_BULLET' as any:
                        glyph = '¤';
                        color = '#ff3355';
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
                let glyph = '♥';
                let color = '#00ff66';
                const customCast = item as any;

                if (customCast.type === 'LOG') {
                    glyph = '♦';
                    color = '#00f5ff'; // Cyan for LOG XP chips
                } else if (customCast.type === 'CLEAR_CACHE') {
                    glyph = '♣';
                    color = '#ff33ff'; // Magenta for purge cache
                } else if (customCast.type === 'SAFE_MODE') {
                    glyph = '▲';
                    color = '#ffff33'; // Yellow golden for safe mode shielding
                }

                textObject = this.add.text(item.x, item.y, glyph, {
                    fontFamily: 'Courier New, Courier, Consolas, monospace',
                    fontSize: '16px',
                    color: color,
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

        // Compile XP Bar [███░░░░░░░]
        const xpPercent = Math.max(0, state.player.xp / state.player.xpNeeded);
        const xpActiveSegments = Math.round(xpPercent * barSegmentsCount);
        const xpEmptySegments = barSegmentsCount - xpActiveSegments;
        const xpBarStr = '[' + '█'.repeat(xpActiveSegments) + '░'.repeat(xpEmptySegments) + ']';

        // Compile Formatted Timer MM:SS.CC
        const minutes = Math.floor(state.gameTimer / 60);
        const seconds = Math.floor(state.gameTimer % 60);
        const centiseconds = Math.floor((state.gameTimer % 1) * 100);
        const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`;

        // Determine System Status Strings
        let statusStr = "SYSTEM_NORMAL";
        if (state.player.invulnerableTimer > 0) {
            statusStr = state.player.safeModeTimer > 0 ? "SAFE_MODE_ON" : "INVULN_ACTIVE";
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
            ` WEAPON:   ${state.player.activeWeapon}.EXE`,
            ` WPN LV:   LEVEL_${state.player.weaponLevel}`,
            ` RUN TIME: ${timeStr}`,
            ` RESOLVED: ${state.killCount.toString().padStart(3, '0')} BUGS`,
            "-----------------------",
            " [PLAYER CORE COORD]   ",
            ` X: ${Math.round(state.player.x).toString().padStart(3, '0')} | Y: ${Math.round(state.player.y).toString().padStart(3, '0')}`,
            "-----------------------",
            " [PLAYER STACK LEVEL]  ",
            ` LEVEL:    LEVEL_${state.player.level}`,
            ` XP STACK: ${state.player.xp} / ${state.player.xpNeeded}`,
            ` XP BAR:   ${xpBarStr}`,
            "-----------------------",
            " [PLAYER CORE HEALTH]  ",
            ` CORE HP:  ${state.player.hp.toString().padStart(3, ' ')} / ${state.player.maxHp}`,
            ` HP BAR:   ${hpBarStr}`,
            ` STATUS:   ${statusStr}`,
            "======================="
        ];

        if (this.glitchTimer > 0 && Math.random() < 0.5) {
            // Inject hardware heap corruption dump symbols inside visual log lines
            this.sidebarText.setText(lines.map(l => Math.random() < 0.2 ? "!!! CORRUPTION DETECTED !!!" : l).join('\n'));
            this.sidebarText.setColor('#ff3333');
            this.sidebarText.setPosition(
                595 + (Math.random() * 8 - 4),
                145 + (Math.random() * 8 - 4)
            );
        } else {
            this.sidebarText.setText(lines.join('\n'));
            this.sidebarText.setColor('#00f500');
            this.sidebarText.setPosition(595, 145);
        }
    }

    /**
     * Pauses simulation ticking and draws the 3 level-up cards overlay.
     */
    private triggerLevelUpOverlay(): void {
        this.isLevelUpPaused = true;
        this.selectedCardIndex = 0;

        const simState = this.simulator.state;
        this.levelUpCards = [
            {
                title: "WEAPON PATCH",
                desc: "Increase weapon damage,\nfire rate, and scale.\n[Level up Weapon]",
                action: () => {
                    simState.player.weaponLevel++;
                }
            },
            {
                title: "MEMORY HOTFIX",
                desc: "Reallocate memory cells\nto recover 50 HP.\n[Recover health]",
                action: () => {
                    simState.player.hp = Math.min(simState.player.maxHp, simState.player.hp + 50);
                }
            },
            {
                title: "CPU OVERCLOCK",
                desc: "Boost core thread speed\nby 15% (increases movement).\n[Increase Speed]",
                action: () => {
                    simState.player.speed = Math.min(380, simState.player.speed + 30);
                }
            }
        ];

        this.levelUpGroup.setVisible(true);
        this.drawLevelUpCards();
        SoundFX.playPowerUp();
    }

    /**
     * Renders Vampire Survivors style upgrade card interfaces.
     */
    private drawLevelUpCards(): void {
        this.levelUpGroup.removeAll(true);

        // A dark, semi-transparent backing overlay
        const backing = this.add.graphics();
        backing.fillStyle(0x020617, 0.85); // Theme 1 deep midnight slate blue
        backing.fillRect(0, 0, 585, 600);
        this.levelUpGroup.add(backing);

        // Large title frame
        const titleText = this.add.text(292, 100, "=== RUNTIME CORE UPGRADE REQUIRED ===", {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '18px',
            color: '#00f500',
            fontStyle: 'bold'
        }).setOrigin(0.5);
        this.levelUpGroup.add(titleText);

        const subTitleText = this.add.text(292, 130, "Select a hotfix to optimize stack environment threads:", {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '11px',
            color: '#00b300'
        }).setOrigin(0.5);
        this.levelUpGroup.add(subTitleText);

        // Draw 3 Choice Cards
        const startX = 40;
        const cardW = 150;
        const cardH = 220;
        const gap = 20;

        for (let i = 0; i < 3; i++) {
            const x = startX + i * (cardW + gap);
            const y = 180;

            const isHovered = i === this.selectedCardIndex;
            const borderCol = isHovered ? 0x00ffff : 0x004488; // neon cyber cyan highlight vs dim slate blue
            const textCol = isHovered ? '#00ffff' : '#0077aa';
            const bgCol = isHovered ? 0x0b192c : 0x020617; // Midnight slate vs sapphire dark blue

            const cardGraphics = this.add.graphics();
            // Fill
            cardGraphics.fillStyle(bgCol, 0.98);
            cardGraphics.fillRect(x, y, cardW, cardH);
            // Double Border outline style
            cardGraphics.lineStyle(isHovered ? 3 : 1, borderCol, 1);
            cardGraphics.strokeRect(x, y, cardW, cardH);
            if (isHovered) {
                cardGraphics.lineStyle(1.5, 0x00f0ff, 0.5);
                cardGraphics.strokeRect(x - 3, y - 3, cardW + 6, cardH + 6);
            }
            this.levelUpGroup.add(cardGraphics);

            // Card contents
            const card = this.levelUpCards[i];
            const titleGo = this.add.text(x + cardW / 2, y + 25, card.title, {
                fontFamily: 'Courier New, Courier, Consolas, monospace',
                fontSize: '13px',
                color: textCol,
                fontStyle: 'bold'
            }).setOrigin(0.5);
            this.levelUpGroup.add(titleGo);

            const divider = this.add.text(x + cardW / 2, y + 45, "---------", {
                fontFamily: 'Courier New, Courier, Consolas, monospace',
                fontSize: '11px',
                color: textCol
            }).setOrigin(0.5);
            this.levelUpGroup.add(divider);

            const descGo = this.add.text(x + cardW / 2, y + 75, card.desc, {
                fontFamily: 'Courier New, Courier, Consolas, monospace',
                fontSize: '11px',
                color: isHovered ? '#ffb000' : '#885500', // vibrant amber vs dark brown
                align: 'center',
                lineSpacing: 6
            }).setOrigin(0.5, 0);
            this.levelUpGroup.add(descGo);

            if (isHovered) {
                const selectPrompt = this.add.text(x + cardW / 2, y + 190, "[ ENTER / SPACE ]", {
                    fontFamily: 'Courier New, Courier, Consolas, monospace',
                    fontSize: '10px',
                    color: '#00ffff',
                    fontStyle: 'bold'
                }).setOrigin(0.5);
                this.levelUpGroup.add(selectPrompt);
            }
        }

        // Selection Instructions bottom panel
        const selectorPrompt = this.add.text(292, 450, "[A / D] Navigate Cards  |  [ENTER / SPACE] Inject Compiler Patch", {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '11px',
            color: '#00f500'
        }).setOrigin(0.5);
        this.levelUpGroup.add(selectorPrompt);
    }

    /**
     * Listens and manages upgrade choices inside levels overlays.
     */
    private handleLevelUpInputs(): void {
        const justLeft = Phaser.Input.Keyboard.JustDown(this.wasdInputs.A) || 
                          (this.arrowCursors.left && Phaser.Input.Keyboard.JustDown(this.arrowCursors.left));
        const justRight = Phaser.Input.Keyboard.JustDown(this.wasdInputs.D) || 
                           (this.arrowCursors.right && Phaser.Input.Keyboard.JustDown(this.arrowCursors.right));
        const justConfirm = Phaser.Input.Keyboard.JustDown(this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER)) ||
                            Phaser.Input.Keyboard.JustDown(this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE));

        if (justLeft) {
            this.selectedCardIndex = (this.selectedCardIndex - 1 + 3) % 3;
            SoundFX.playShield(); // short tick sound
            this.drawLevelUpCards();
        } else if (justRight) {
            this.selectedCardIndex = (this.selectedCardIndex + 1) % 3;
            SoundFX.playShield(); // short tick sound
            this.drawLevelUpCards();
        } else if (justConfirm) {
            // Apply selected card patch action
            const selectedCard = this.levelUpCards[this.selectedCardIndex];
            selectedCard.action();

            // Resume simulation
            this.isLevelUpPaused = false;
            this.levelUpGroup.setVisible(false);
            SoundFX.playPowerUp();
        }
    }
}
