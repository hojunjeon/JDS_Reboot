import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene';
import { MenuScene } from './scenes/MenuScene';
import { PlayScene } from './scenes/PlayScene';
import { ResultScene } from './scenes/ResultScene';

/**
 * Phaser 3 configuration for Jiyoon Debug Survival (JDS).
 * Features standard 800x600 layout, scaled to fit parent containers,
 * pixelated image rendering for clean retro ASCII monospace shapes.
 */
export const GameConfig: Phaser.Types.Core.GameConfig = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'game-viewport', // Mount point inside index.html retro wrapper
    backgroundColor: '#0a0a0a', // Deep Obsidian Black
    render: {
        pixelArt: true, // Disables anti-aliasing to render sharp, blocky monospace ASCII characters
        antialias: false
    },
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    scene: [BootScene, MenuScene, PlayScene, ResultScene]
};
export default GameConfig;
