/* Click tones. No assets. Off by default until the user un-mutes. */

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
    this.blip("sine", 880, 220, 0.04, 0.05);
  }

  playPassAlert() {
    this.blip("triangle", 440, 660, 0.18, 0.08);
  }

  playModeClick() {
    this.blip("square", 180, 180, 0.02, 0.03);
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
      osc.stop(now + dur);
    } catch { /* ignore autoplay blocks */ }
  }
}
