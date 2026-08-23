/* Click tones. No assets. Off by default until the user un-mutes.
   Lock acquire is a short filtered burst, not a jingle. */

export class ClickEngine {
  constructor() {
    this.ctx = null;
    this.muted = true;
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  playLockTick() {
    this.blip("sine", 880, 220, 0.05, 0.045);
    this.noise(0.028, 0.03, 2200);
  }

  playLockAcquire() {
    this.blip("triangle", 196, 784, 0.22, 0.07);
    this.blip("sine", 392, 1176, 0.16, 0.035);
    this.noise(0.07, 0.045, 1100);
  }

  playPassAlert() {
    this.blip("triangle", 330, 660, 0.2, 0.08);
    this.blip("sine", 660, 330, 0.28, 0.05);
    this.noise(0.05, 0.03, 800);
  }

  playModeClick() {
    this.blip("square", 180, 140, 0.025, 0.028);
    this.noise(0.018, 0.02, 1600);
  }

  noise(dur, gain, freq) {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const n = Math.max(1, Math.floor(this.ctx.sampleRate * dur));
      const buf = this.ctx.createBuffer(1, n, this.ctx.sampleRate);
      const data = buf.getChannelData(0);
      for (let i = 0; i < n; i++) data[i] = Math.random() * 2 - 1;
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      const bp = this.ctx.createBiquadFilter();
      bp.type = "bandpass";
      bp.frequency.setValueAtTime(freq, now);
      bp.Q.setValueAtTime(1.4, now);
      const g = this.ctx.createGain();
      g.gain.setValueAtTime(gain, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + dur);
      src.connect(bp);
      bp.connect(g);
      g.connect(this.ctx.destination);
      src.start(now);
      src.stop(now + dur);
    } catch { /* ignore autoplay blocks */ }
  }

  blip(type, f0, f1, dur, gain) {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const g = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(f0, now);
      if (f1 !== f0) osc.frequency.exponentialRampToValueAtTime(Math.max(1, f1), now + dur);
      g.gain.setValueAtTime(gain, now);
      g.gain.exponentialRampToValueAtTime(0.001, now + dur);
      osc.connect(g);
      g.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + dur + 0.01);
    } catch { /* ignore autoplay blocks */ }
  }
}
