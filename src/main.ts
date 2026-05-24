import './style.css';
import Phaser from 'phaser';
import { GameConfig } from './config';

/**
 * Game Bootstrap Entry Point.
 * Loads stylesheets and mounts the customized Phaser engine configuration.
 */
window.addEventListener('load', () => {
    try {
        new Phaser.Game(GameConfig);
        console.log("[INIT] Jiyoon Debug Survival initialized successfully.");
    } catch (error) {
        console.error("[CRITICAL] Failed to initialize Phaser Game:", error);
    }
});
