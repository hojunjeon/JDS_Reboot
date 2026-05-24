import Phaser from 'phaser';

/**
 * BootScene: Terminal BIOS startup self-test & boot animation scene.
 * Simulates sequential hardware checks and warning notifications in green monospace logs.
 */
export class BootScene extends Phaser.Scene {
    private bootLogs: string[] = [
        "JDS BIOS v1.0.4 - BOOT RECORD OK",
        "CPU: JIYOON CORE DUO @ 3.33GHz",
        "RAM: 640KB SYSTEM CONVENTIONAL MEMORY",
        "VERIFYING SECTOR 0x00F8... SUCCESS",
        "INITIALIZING COMPILER PARSER LIBRARIES... SUCCESS",
        "COMPILING STACK OVERFLOW SANITIZERS... SUCCESS",
        "[WARNING] CRITICAL CORRUPTION FOUND IN DIRECTORY: /src/sandbox/",
        "[WARNING] INTRUSION PATTERNS IDENTIFIED: BUGS_DELUGE_V2026",
        "",
        "READY FOR LIVE DEBUGGING INJECTOR.",
        "[ PRESS ANY KEY TO INITIALIZE IDE_SANDBOX.EXE ]"
    ];

    private currentLineIndex = 0;
    private renderedLines: string[] = [];
    private consoleText!: Phaser.GameObjects.Text;
    private cursorState = true;

    constructor() {
        super({ key: 'BootScene' });
    }

    create(): void {
        // Render text box using custom monospace font styles
        this.consoleText = this.add.text(45, 55, '', {
            fontFamily: 'Courier New, Courier, Consolas, Fira Code, monospace',
            fontSize: '18px',
            color: '#00f500', // Vibrant Retro Neon Green
            lineSpacing: 10
        });

        // Trigger typing simulation
        this.renderNextLog();

        // Standard block cursor blinking loop
        this.time.addEvent({
            delay: 400,
            callback: () => {
                this.cursorState = !this.cursorState;
                this.refreshConsoleContent();
            },
            loop: true
        });
    }

    /**
     * Recursively prints logs line-by-line with slight randomized delays.
     */
    private renderNextLog(): void {
        if (this.currentLineIndex < this.bootLogs.length) {
            this.renderedLines.push(this.bootLogs[this.currentLineIndex]);
            this.currentLineIndex++;
            this.refreshConsoleContent();

            // Random delay to match realistic BIOS load speeds
            const randomizedDelay = Phaser.Math.Between(100, 240);
            this.time.delayedCall(randomizedDelay, () => this.renderNextLog());
        } else {
            // Listen for any key down event to trigger ide boot transitions
            this.input.keyboard?.once('keydown', () => {
                // Flash camera or shake screen for CRT boot transition
                this.cameras.main.shake(120, 0.015);
                this.time.delayedCall(150, () => {
                    this.scene.start('MenuScene');
                });
            });
        }
    }

    /**
     * Refreshes text displays incorporating blinking prompt blocks.
     */
    private refreshConsoleContent(): void {
        let textResult = this.renderedLines.join('\n');
        if (this.cursorState) {
            textResult += '\n█';
        }
        this.consoleText.setText(textResult);
    }
}
