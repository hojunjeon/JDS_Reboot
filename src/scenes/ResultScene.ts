import Phaser from 'phaser';

/**
 * ResultScene: Performance analytics / stack overflow report screen.
 * Displays diagnostic log dump depending on sandbox win/loss outcomes,
 * and handles keyboard actions to recompile (R) or exit (ESC).
 */
export class ResultScene extends Phaser.Scene {
    private isGameOver = false;
    private isStageClear = false;
    private gameTimer = 0;
    private killCount = 0;
    private weaponSelection = 'PYTHON';
    private stageSelection = 1;

    private rKey!: Phaser.Input.Keyboard.Key;
    private escKey!: Phaser.Input.Keyboard.Key;

    constructor() {
        super({ key: 'ResultScene' });
    }

    init(data: {
        isGameOver?: boolean;
        isStageClear?: boolean;
        gameTimer?: number;
        killCount?: number;
        weapon?: string;
        stage?: number;
    }): void {
        this.isGameOver = data.isGameOver ?? false;
        this.isStageClear = data.isStageClear ?? false;
        this.gameTimer = data.gameTimer ?? 0;
        this.killCount = data.killCount ?? 0;
        this.weaponSelection = data.weapon ?? 'PYTHON';
        this.stageSelection = data.stage ?? 1;
    }

    create(): void {
        // 1. Render premium IDE blue-slate background asset
        const bg = this.add.image(0, 0, 'bg_alt1').setOrigin(0, 0);
        bg.setDisplaySize(800, 600);

        // 2. Draw high-fidelity double bordered window panel (Vibrant cyber oklch colors)
        const panel = this.add.graphics();
        // Dim translucent backing
        panel.fillStyle(0x020617, 0.92); // Midnight slate blue
        panel.fillRect(40, 30, 720, 540);

        // Border color: Neon cyan (#00f0ff) for victory, Red alert (#ff3355) for stack crash
        const themeColor = this.isStageClear ? 0x00f0ff : 0xff3355;
        panel.lineStyle(2, themeColor, 0.85);
        panel.strokeRect(40, 30, 720, 540);

        // Soft secondary outer border
        panel.lineStyle(1, 0x00b300, 0.35);
        panel.strokeRect(36, 26, 728, 548);

        // 3. Render Locked Player alt3 avatar in result screen status card
        const avatarFrameColor = this.isStageClear ? 0x00ffcc : 0xffaa00;
        panel.lineStyle(2, avatarFrameColor, 0.8);
        panel.strokeRect(580, 80, 130, 130);
        panel.lineStyle(1, 0x005533, 0.5);
        panel.strokeRect(576, 76, 138, 138);

        const avatarImage = this.add.image(645, 145, 'player_alt3');
        avatarImage.setDisplaySize(110, 110);

        // Avatar Status caption
        const statusTextStr = this.isStageClear ? "STATUS: COMPILED\nTHREAD_SAFE" : "STATUS: CRASHED\nSTACK_DUMPED";
        const statusColorStr = this.isStageClear ? "#33ffcc" : "#ffa300";
        this.add.text(645, 225, statusTextStr, {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '11px',
            color: statusColorStr,
            align: 'center',
            lineSpacing: 5
        }).setOrigin(0.5, 0);

        // 4. Compile outcome title blocks
        let statusTitle = " [ STATUS: RUNTIME_ERROR: STACK_OVERFLOW ] ";
        let statusSub = "CRITICAL HEAP OVERFLOW IN LIVE SANDBOX CORE DETECTED.";

        if (this.isStageClear) {
            statusTitle = " [ STATUS: COMPILATION SUCCESSFUL ] ";
            statusSub = "SUCCESSFULLY SURVIVED WAVE CORRUPTIONS. BUG RESOLVED.";
        }

        // Format Centiseconds Timer MM:SS.CC
        const minutes = Math.floor(this.gameTimer / 60);
        const seconds = Math.floor(this.gameTimer % 60);
        const centiseconds = Math.floor((this.gameTimer % 1) * 100);
        const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`;

        // Construct ascii double-border metrics sheet
        const borderLines = "=======================================================";
        const dividerLines = "-------------------------------------------------------";

        const logLines = [
            borderLines,
            "     JIYOON IDE SANDBOX — STACK CORE LOG DIAGNOSTICS",
            borderLines,
            "",
            statusTitle,
            ` ${statusSub}`,
            "",
            dividerLines,
            " ENVIRONMENT AND COMPILATION SUMMARY METRICS:",
            ` * INTRUDER SANDBOX RUN TIME : ${timeStr}`,
            ` * COMPILED BUGS RESOLVED    : ${this.killCount} ENEMY CORE FILES`,
            ` * WEAPON INJECTOR TYPE      : ${this.weaponSelection}.EXE`,
            ` * CORE HEAP CRASH DETECTED  : ${this.isGameOver ? "TRUE (STACK OVERFLOW)" : "FALSE (COMPILED OK)"}`,
            ` * MOCKED TARGET COMPILER    : JIYOON_CORE_GCC_v12.2.0`,
            ` * CORRUPTION EVENT SCALING  : STAGE_${this.stageSelection} ENV`,
            dividerLines,
            " ACTIONS AVAILABLE IN CORE SHELL:",
            " [R]   RECOMPILE & RE-RUN IDE_SANDBOX.EXE",
            " [ESC] FLUSH STACK AND RETURN TO SHELL MAIN MENU",
            dividerLines
        ];

        // Draw logs in green for Stage Clear success, and amber for Game Over failure
        const textColorStr = this.isStageClear ? '#00f500' : '#ffb000';
        this.add.text(60, 60, logLines.join('\n'), {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '15px',
            color: textColorStr,
            lineSpacing: 8
        });

        // 5. Initialize keys
        if (this.input.keyboard) {
            this.rKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.R);
            this.escKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ESC);
        }
    }

    update(): void {
        if (Phaser.Input.Keyboard.JustDown(this.rKey)) {
            this.cameras.main.shake(120, 0.015);
            this.time.delayedCall(130, () => {
                this.scene.start('PlayScene', {
                    stage: this.stageSelection,
                    weapon: this.weaponSelection
                });
            });
        }

        if (Phaser.Input.Keyboard.JustDown(this.escKey)) {
            this.cameras.main.shake(100, 0.012);
            this.time.delayedCall(110, () => {
                this.scene.start('MenuScene');
            });
        }
    }
}
