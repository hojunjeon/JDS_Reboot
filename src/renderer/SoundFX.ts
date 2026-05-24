/**
 * SoundFX: Native Web Audio API 8-Bit Retro Synthesizer.
 * Programmatically generates retro sci-fi and arcade game sound effects
 * without relying on external file assets, satisfying browser audio policies.
 */
export class SoundFX {
    private static audioCtx: AudioContext | null = null;

    /**
     * Initializes and returns the lazy-loaded AudioContext instance.
     * Resumes the context if suspended due to browser autoplay protections.
     */
    private static getContext(): AudioContext | null {
        if (typeof window === 'undefined') {
            return null;
        }

        if (!this.audioCtx) {
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            if (AudioContextClass) {
                this.audioCtx = new AudioContextClass();
            }
        }

        if (this.audioCtx && this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        return this.audioCtx;
    }

    /**
     * Helper to create a standard oscillator-gain-destination chain.
     */
    private static createChain(
        type: OscillatorType,
        startFreq: number,
        gainVal: number,
        duration: number
    ): { osc: OscillatorNode; gainNode: GainNode; ctx: AudioContext } | null {
        const ctx = this.getContext();
        if (!ctx) return null;

        const osc = ctx.createOscillator();
        const gainNode = ctx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(startFreq, ctx.currentTime);

        gainNode.gain.setValueAtTime(gainVal, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);

        osc.connect(gainNode);
        gainNode.connect(ctx.destination);

        return { osc, gainNode, ctx };
    }

    /**
     * playShoot(): Square-wave sweep (high-to-low pitch) representing Python/C++ compiler fire.
     */
    public static playShoot(): void {
        const chain = this.createChain('square', 800, 0.04, 0.12);
        if (!chain) return;

        const { osc, ctx } = chain;
        osc.frequency.exponentialRampToValueAtTime(150, ctx.currentTime + 0.12);
        osc.start();
        osc.stop(ctx.currentTime + 0.12);
    }

    /**
     * playShield(): Orbiting resonance tone (short sine-wave vibration) for Java orbiting shield collision.
     */
    public static playShield(): void {
        const chain = this.createChain('sine', 350, 0.08, 0.08);
        if (!chain) return;

        const { osc, ctx } = chain;
        osc.frequency.linearRampToValueAtTime(600, ctx.currentTime + 0.04);
        osc.frequency.linearRampToValueAtTime(350, ctx.currentTime + 0.08);
        osc.start();
        osc.stop(ctx.currentTime + 0.08);
    }

    /**
     * playHit(): Sawtooth noise-glitch impact tone for player damage.
     */
    public static playHit(): void {
        const chain = this.createChain('sawtooth', 180, 0.08, 0.18);
        if (!chain) return;

        const { osc, ctx } = chain;
        osc.frequency.linearRampToValueAtTime(40, ctx.currentTime + 0.18);
        osc.start();
        osc.stop(ctx.currentTime + 0.18);
    }

    /**
     * playExplosion(): Short white noise / low frequency crash for bug resolution.
     */
    public static playExplosion(): void {
        const ctx = this.getContext();
        if (!ctx) return;

        // Synthesize short white noise buffer
        const duration = 0.25;
        const bufferSize = ctx.sampleRate * duration;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }

        const noise = ctx.createBufferSource();
        noise.buffer = buffer;

        // Apply dynamic lowpass filter sweep for muffled retro explosion crash
        const filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(400, ctx.currentTime);
        filter.frequency.exponentialRampToValueAtTime(10, ctx.currentTime + duration);

        const gainNode = ctx.createGain();
        gainNode.gain.setValueAtTime(0.08, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);

        noise.connect(filter);
        filter.connect(gainNode);
        gainNode.connect(ctx.destination);

        noise.start();
        noise.stop(ctx.currentTime + duration);
    }

    /**
     * playPowerUp(): Upward arpeggio sweep when picking up recovery items.
     */
    public static playPowerUp(): void {
        const ctx = this.getContext();
        if (!ctx) return;

        const now = ctx.currentTime;
        const notes = [523.25, 659.25, 783.99]; // C5, E5, G5
        const noteLength = 0.06;

        notes.forEach((freq, idx) => {
            const time = now + idx * noteLength;
            const osc = ctx.createOscillator();
            const gainNode = ctx.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, time);

            gainNode.gain.setValueAtTime(0.05, time);
            gainNode.gain.exponentialRampToValueAtTime(0.0001, time + noteLength);

            osc.connect(gainNode);
            gainNode.connect(ctx.destination);

            osc.start(time);
            osc.stop(time + noteLength);
        });
    }

    /**
     * playVictory(): Simple 3-note ascending neon celebratory arpeggio.
     */
    public static playVictory(): void {
        const ctx = this.getContext();
        if (!ctx) return;

        const now = ctx.currentTime;
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        const noteLength = 0.12;

        notes.forEach((freq, idx) => {
            const time = now + idx * noteLength;
            const osc = ctx.createOscillator();
            const gainNode = ctx.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, time);

            gainNode.gain.setValueAtTime(0.06, time);
            gainNode.gain.exponentialRampToValueAtTime(0.0001, time + noteLength);

            osc.connect(gainNode);
            gainNode.connect(ctx.destination);

            osc.start(time);
            osc.stop(time + noteLength);
        });
    }

    /**
     * playGameOver(): Descending minor arpeggio representing stack overflow.
     */
    public static playGameOver(): void {
        const ctx = this.getContext();
        if (!ctx) return;

        const now = ctx.currentTime;
        const notes = [440.00, 349.23, 261.63, 220.00]; // A4, F4, C4, A3
        const noteLength = 0.15;

        notes.forEach((freq, idx) => {
            const time = now + idx * noteLength;
            const osc = ctx.createOscillator();
            const gainNode = ctx.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(freq, time);

            gainNode.gain.setValueAtTime(0.06, time);
            gainNode.gain.exponentialRampToValueAtTime(0.0001, time + noteLength);

            osc.connect(gainNode);
            gainNode.connect(ctx.destination);

            osc.start(time);
            osc.stop(time + noteLength);
        });
    }
}
