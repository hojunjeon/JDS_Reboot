import Phaser from 'phaser';

/**
 * MenuScene: Retro DOS IDE prompt config menu.
 * Supports Stage selection (Stage 1/2) and Weapon selection (Python, C++, Java).
 * Full keyboard inputs with dynamic visual updates of ASCII stats cards.
 */
export class MenuScene extends Phaser.Scene {
    private selectedRow = 0; // 0 = STAGE, 1 = WEAPON
    private stageOption = 1; // 1 = Stage 1, 2 = Stage 2
    private weaponIndex = 0; // 0 = PYTHON, 1 = CPP, 2 = JAVA
    private weapons: Array<{ key: string; name: string; card: string }> = [
        {
            key: 'PYTHON',
            name: 'PYTHON.PY (Homing Scripts)',
            card: [
                "+--------------------------------------------+",
                "| PYTHON.PY - AUTOMATED HOMING SCRIPTS       |",
                "| * DAM: 10   | SPEED: 250   | PIERCE: 1     |",
                "| * TRAJECTORY: Continuously homes in on     |",
                "|   the nearest compiled bug coordinates.    |",
                "| \"Reliable automation script. Standard      |",
                "|  debugging weapon.\"                        |",
                "+--------------------------------------------+"
            ].join('\n')
        },
        {
            key: 'CPP',
            name: 'CPP.CPP (Fast Piercing Ray)',
            card: [
                "+--------------------------------------------+",
                "| CPP.CPP - DIRECT MEMORY COMPILED RAY BEAM  |",
                "| * DAM: 18   | SPEED: 450   | PIERCE: 5     |",
                "| * TRAJECTORY: High speed direct ray.       |",
                "|   Pierces through up to 5 bug collisions.  |",
                "| \"Extremely fast execution, highly volatile  |",
                "|  and pierces the stack easily.\"            |",
                "+--------------------------------------------+"
            ].join('\n')
        },
        {
            key: 'JAVA',
            name: 'JAVA.CLASS (Orbit Shields)',
            card: [
                "+--------------------------------------------+",
                "| JAVA.CLASS - DEFENSIVE ORBIT SHIELD MODULE |",
                "| * DAM: 12   | SPEED: Orbit | PIERCE: INF   |",
                "| * TRAJECTORY: Spawns 3 orbiting shield     |",
                "|   blocks rotating around core coords.      |",
                "| \"Persistent shield structures blocking     |",
                "|  all basic compiler intruder bugs.\"        |",
                "+--------------------------------------------+"
            ].join('\n')
        }
    ];

    private stageRowText!: Phaser.GameObjects.Text;
    private weaponRowText!: Phaser.GameObjects.Text;
    private statsCardText!: Phaser.GameObjects.Text;

    private upKey!: Phaser.Input.Keyboard.Key;
    private downKey!: Phaser.Input.Keyboard.Key;
    private leftKey!: Phaser.Input.Keyboard.Key;
    private rightKey!: Phaser.Input.Keyboard.Key;
    private enterKey!: Phaser.Input.Keyboard.Key;
    private spaceKey!: Phaser.Input.Keyboard.Key;

    constructor() {
        super({ key: 'MenuScene' });
    }

    create(): void {
        // Draw double-border top title decoration
        const borderLines = "================================================================";
        
        this.add.text(50, 45, [
            borderLines,
            "  JIYOON DEBUG SURVIVAL (JDS) — MONOSPACE TERMINAL SHELL",
            borderLines
        ].join('\n'), {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '18px',
            color: '#00f500', // Neon green
            lineSpacing: 6
        });

        // Draw Player Avatar Frame & Image (Locked alternative 3 player avatar)
        const avatarFrame = this.add.graphics();
        // Outer border
        avatarFrame.lineStyle(2, 0x00f500, 0.8);
        avatarFrame.strokeRect(600, 140, 120, 120);
        // Inner border
        avatarFrame.lineStyle(1, 0x00b300, 0.4);
        avatarFrame.strokeRect(596, 136, 128, 128);

        // Add Avatar image
        const avatarImage = this.add.image(660, 200, 'player_alt3');
        avatarImage.setDisplaySize(100, 100);

        // Avatar Caption text
        this.add.text(660, 275, [
            "AVATAR: LOCK_3",
            "NEON HACKER CAT"
        ].join('\n'), {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '11px',
            color: '#00f500',
            align: 'center',
            lineSpacing: 4
        }).setOrigin(0.5, 0);

        // Config row displays
        this.stageRowText = this.add.text(50, 160, '', {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '18px',
            color: '#00f500',
            lineSpacing: 8
        });

        this.weaponRowText = this.add.text(50, 210, '', {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '18px',
            color: '#00f500',
            lineSpacing: 8
        });

        // Weapon specification Card Box
        this.statsCardText = this.add.text(50, 270, '', {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '16px',
            color: '#ffb000', // Warm amber glow for weapon stats cards
            lineSpacing: 8
        });

        // Instructions Footer
        this.add.text(50, 470, [
            "----------------------------------------------------------",
            " [W / S] Navigate rows   |  [A / D] Select option configurations",
            " [ENTER / SPACE] Compile and RUN IDE_SANDBOX.EXE",
            "----------------------------------------------------------"
        ].join('\n'), {
            fontFamily: 'Courier New, Courier, Consolas, monospace',
            fontSize: '15px',
            color: '#00f500',
            lineSpacing: 8
        });

        // Map controls
        if (this.input.keyboard) {
            this.upKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W);
            this.downKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S);
            this.leftKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A);
            this.rightKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D);
            this.enterKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.ENTER);
            this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);

            // Alternate arrow controls
            this.input.keyboard.on('keydown', (event: KeyboardEvent) => {
                if (event.key === 'ArrowUp') this.changeSelectedRow(-1);
                if (event.key === 'ArrowDown') this.changeSelectedRow(1);
                if (event.key === 'ArrowLeft') this.toggleOptionValue(-1);
                if (event.key === 'ArrowRight') this.toggleOptionValue(1);
            });
        }

        // Draw initial parameters
        this.redrawMenu();
    }

    update(): void {
        // Trigger movements via specific WASD maps
        if (Phaser.Input.Keyboard.JustDown(this.upKey)) {
            this.changeSelectedRow(-1);
        }
        if (Phaser.Input.Keyboard.JustDown(this.downKey)) {
            this.changeSelectedRow(1);
        }
        if (Phaser.Input.Keyboard.JustDown(this.leftKey)) {
            this.toggleOptionValue(-1);
        }
        if (Phaser.Input.Keyboard.JustDown(this.rightKey)) {
            this.toggleOptionValue(1);
        }

        if (Phaser.Input.Keyboard.JustDown(this.enterKey) || Phaser.Input.Keyboard.JustDown(this.spaceKey)) {
            this.launchSandboxSimulation();
        }
    }

    private changeSelectedRow(direction: number): void {
        this.selectedRow = (this.selectedRow + direction + 2) % 2;
        this.redrawMenu();
    }

    private toggleOptionValue(direction: number): void {
        if (this.selectedRow === 0) {
            // Toggle Stage selection
            this.stageOption = this.stageOption === 1 ? 2 : 1;
        } else {
            // Toggle Weapon selection index
            this.weaponIndex = (this.weaponIndex + direction + this.weapons.length) % this.weapons.length;
        }
        this.redrawMenu();
    }

    /**
     * Refreshes text parameters highlighting the active selection and stats cards.
     */
    private redrawMenu(): void {
        const activeStageText = this.stageOption === 1 
            ? "STAGE 1: MAIN_LOOP_CORRUPTION (60s Limit)" 
            : "STAGE 2: HEAP_LEAK_INFERNO (2x Spawner rate)";

        const activeWeaponName = this.weapons[this.weaponIndex].name;

        // Render Stage Selection Row
        if (this.selectedRow === 0) {
            this.stageRowText.setText(` -> STAGE:  < ${activeStageText} >`);
            this.stageRowText.setColor('#33ff33');
            this.weaponRowText.setText(`    WEAPON:   < ${activeWeaponName} >`);
            this.weaponRowText.setColor('#00b300'); // dim green
        } else {
            this.stageRowText.setText(`    STAGE:   < ${activeStageText} >`);
            this.stageRowText.setColor('#00b300'); // dim green
            this.weaponRowText.setText(` -> WEAPON: < ${activeWeaponName} >`);
            this.weaponRowText.setColor('#33ff33');
        }

        // Draw active weapon stats card
        this.statsCardText.setText(this.weapons[this.weaponIndex].card);
    }

    private launchSandboxSimulation(): void {
        this.cameras.main.shake(150, 0.015);
        this.time.delayedCall(160, () => {
            this.scene.start('PlayScene', {
                stage: this.stageOption,
                weapon: this.weapons[this.weaponIndex].key
            });
        });
    }
}
