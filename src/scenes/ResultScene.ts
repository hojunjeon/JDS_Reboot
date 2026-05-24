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
        // Compile outcome title blocks
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
        const borderLines = "==========================================================";
        const dividerLines = "----------------------------------------------------------";

        const logLines = [
            borderLines,
            "      JIYOON IDE SANDBOX — STACK CORE LOG DIAGNOSTICS",
            borderLines,
            "",
            statusTitle,
            ` ${statusSub}`,
            "",
            dividerLines,
            " ENVIRONMENT AND COMPILATION SUMMARY METRICS:",
            ` * INTRUDER SANDBOX RUN TIME : ${timeStr}`,
            ` * COMPILED BUGS RESOLVED    : ${this.killCount} ENEMY CORE FILES`,
            ` * WEAPON INJECTOR TYPE      : ${this.weaponSelection}.PY`,
            ` * CORE HEAP CRASH DETECTED  : ${this.isGameOver ? "TRUE (CORE DEPLETED)" : "FALSE (COMPILED OK)"}`,
            ` * MOCKED TARGET COMPILER    : JIYOON_CORE_GCC_v12.2.0`,
            dividerLines,
            " ACTIONS AVAILABLE IN CORES SHELL:",
            " [R]   RECOMPILE & RE-RUN IDE_SANDBOX.EXE",
            " [ESC] FLUSH STACK AND RETURN TO SHELL MAIN MENU",
            dividerLines
        ];

        // Draw logs in warm amber or warning red depending on state
        this.add.text(50, 50, logLines.join('\n'), {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '16px',
            color: this.isStageClear ? '#00f500' : '#ffb000', // Success green vs failure amber
            lineSpacing: 8
        });

        // Highlight status title row in specific alert colors
        // Let's create key bindings
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
