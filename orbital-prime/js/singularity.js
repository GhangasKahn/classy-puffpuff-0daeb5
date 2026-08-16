// WebGL Singularity / Accretion Disk Physics Shader & Particle Flare
// Pure procedural relativistic gravitational lensing & photon sphere simulation

export class SingularityField {
  constructor(canvas) {
    this.canvas = canvas;
    this.gl = canvas.getContext("webgl", { alpha: false, antialias: false, powerPreference: "high-performance" });
    this.active = true;
    this.lookEl = 0;
    this.lookAz = 0;
    this.targetWarp = 1.0;
    this.warp = 1.0;

    if (!this.gl) {
      this.initFallback2D();
      return;
    }

    this.initGL();
  }

  initGL() {
    const gl = this.gl;
    const vsSource = `
      attribute vec2 a_pos;
      varying vec2 v_uv;
      void main() {
        v_uv = (a_pos + 1.0) * 0.5;
        gl_Position = vec4(a_pos, 0.0, 1.0);
      }
    `;

    // Fast relativistic black hole raymarcher & accretion disc shader
    const fsSource = `
      precision highp float;
      varying vec2 v_uv;
      uniform vec2 u_res;
      uniform float u_time;
      uniform float u_warp;
      uniform float u_el;
      uniform float u_az;

      #define PI 3.14159265359

      // Pseudo-random noise
      float hash(vec2 p) {
        p = fract(p * vec2(123.34, 456.21));
        p += dot(p, p + 45.32);
        return fract(p.x * p.y);
      }

      float noise(vec2 p) {
        vec2 i = floor(p);
        vec2 f = fract(p);
        f = f * f * (3.0 - 2.0 * f);
        float a = hash(i);
        float b = hash(i + vec2(1.0, 0.0));
        float c = hash(i + vec2(0.0, 1.0));
        float d = hash(i + vec2(1.0, 1.0));
        return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
      }

      float fbm(vec2 p) {
        float v = 0.0;
        float a = 0.5;
        vec2 shift = vec2(100.0);
        mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.5));
        for (int i = 0; i < 4; ++i) {
          v += a * noise(p);
          p = rot * p * 2.0 + shift;
          a *= 0.5;
        }
        return v;
      }

      void main() {
        vec2 uv = (gl_FragCoord.xy - 0.5 * u_res.xy) / min(u_res.x, u_res.y);
        
        // Tilt based on current look elevation and elevation angle
        float tilt = 0.28 + sin(u_el * 0.01745) * 0.12;
        vec2 p = uv;
        p.y /= (tilt + 0.35);

        float r = length(uv);
        float rDisk = length(p);

        // Gravitational lensing warp equation
        float rs = 0.22 * u_warp; // Schwarzschild radius
        float photonRing = rs * 1.5;

        // Background space dust / cosmic void gradient
        vec3 col = vec3(0.015, 0.018, 0.024);
        
        // Deep teal-to-electric-amber interstellar gradient
        col += vec3(0.02, 0.06, 0.12) * smoothstep(1.5, 0.0, r);

        // Top & Bottom Gravitational Einstein Rings (Lensed Accretion Ring)
        float lensR = abs(r - photonRing * 1.12);
        float photonGlow = 0.012 / (lensR * lensR + 0.003);
        col += vec3(1.0, 0.78, 0.45) * photonGlow * 0.65;

        // Primary Accretion Disk (horizontal fiery whirlpool)
        if (rDisk > rs * 0.95 && rDisk < 1.8) {
          float angle = atan(p.y, p.x);
          float speed = 1.2 / sqrt(rDisk + 0.1);
          float swirl = angle + u_time * speed * 0.8 + fbm(vec2(rDisk * 8.0, angle * 3.0)) * 0.8;
          
          float density = fbm(vec2(rDisk * 12.0 - u_time * 0.4, swirl * 2.5));
          density *= smoothstep(rs * 0.95, rs * 1.4, rDisk) * smoothstep(1.6, rs * 1.5, rDisk);
          
          // Doppler boosting (left side approaching, hotter and brighter)
          float doppler = 1.0 - (p.x / rDisk) * 0.45;
          
          // Ultra vivid plasma gradient: Hot white-amber -> electric orange -> deep cyan-teal rim
          vec3 plasma = mix(vec3(1.0, 0.42, 0.0), vec3(1.0, 0.92, 0.75), smoothstep(0.3, 0.8, density * doppler));
          plasma = mix(vec3(0.0, 0.65, 0.95) * 0.4, plasma, smoothstep(0.0, 0.4, density));

          // Inner edge ultra-hot glow
          float innerGlow = 0.018 / (abs(rDisk - rs * 1.15) + 0.02);
          col += (plasma * density * 3.2 + vec3(1.0, 0.8, 0.5) * innerGlow) * doppler;
        }

        // Lensed Top Arch (The iconic Interstellar upward fold)
        float topArch = abs(uv.y - sqrt(max(0.0, photonRing * photonRing * 1.8 - uv.x * uv.x * 0.85)));
        float archIntensity = 0.015 / (topArch * topArch + 0.008);
        archIntensity *= smoothstep(0.9, 0.0, abs(uv.x));
        col += vec3(1.0, 0.55, 0.15) * archIntensity * 0.85;

        // Event Horizon: Absolute void black hole interior
        float shadow = smoothstep(rs * 0.98, rs * 1.02, r);
        col *= shadow;

        // Outer cosmic flare & cyan-orange chromatic contrast
        float outerVignette = smoothstep(1.8, 0.2, length(uv));
        col *= outerVignette;

        gl_FragColor = vec4(col, 1.0);
      }
    `;

    const createShader = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    };

    const program = gl.createProgram();
    gl.attachShader(program, createShader(gl.VERTEX_SHADER, vsSource));
    gl.attachShader(program, createShader(gl.FRAGMENT_SHADER, fsSource));
    gl.linkProgram(program);
    this.program = program;

    const posLoc = gl.getAttribLocation(program, "a_pos");
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1,  1, -1, -1,  1,
      -1,  1,  1, -1,  1,  1
    ]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    this.uRes = gl.getUniformLocation(program, "u_res");
    this.uTime = gl.getUniformLocation(program, "u_time");
    this.uWarp = gl.getUniformLocation(program, "u_warp");
    this.uEl = gl.getUniformLocation(program, "u_el");
    this.uAz = gl.getUniformLocation(program, "u_az");

    this.startTime = performance.now();
  }

  initFallback2D() {
    this.ctx = this.canvas.getContext("2d");
  }

  setLook(az, el) {
    this.lookAz = az || 0;
    this.lookEl = el || 0;
  }

  pulse() {
    this.warp = 1.45;
  }

  render() {
    if (!this.canvas) return;
    const w = this.canvas.parentElement ? this.canvas.parentElement.clientWidth : window.innerWidth;
    const h = this.canvas.parentElement ? this.canvas.parentElement.clientHeight : window.innerHeight;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5); // Snappy mobile render scale
    const bw = Math.round(w * dpr);
    const bh = Math.round(h * dpr);

    if (this.canvas.width !== bw || this.canvas.height !== bh) {
      this.canvas.width = bw;
      this.canvas.height = bh;
    }

    this.warp += (1.0 - this.warp) * 0.08;

    if (this.gl) {
      const gl = this.gl;
      gl.viewport(0, 0, bw, bh);
      gl.useProgram(this.program);

      const elapsed = (performance.now() - this.startTime) * 0.001;
      gl.uniform2f(this.uRes, bw, bh);
      gl.uniform1f(this.uTime, elapsed);
      gl.uniform1f(this.uWarp, this.warp);
      gl.uniform1f(this.uEl, this.lookEl);
      gl.uniform1f(this.uAz, this.lookAz);

      gl.drawArrays(gl.TRIANGLES, 0, 6);
    } else if (this.ctx) {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, bw, bh);
      const cx = bw / 2, cy = bh / 2, r = Math.min(bw, bh) * 0.3;
      const grad = ctx.createRadialGradient(cx, cy, r * 0.8, cx, cy, r * 2.2);
      grad.addColorStop(0, "#000000");
      grad.addColorStop(0.2, "#ff6a00");
      grad.addColorStop(0.6, "#00e5ff");
      grad.addColorStop(1, "transparent");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, bw, bh);
    }
  }
}

// Brutalist Synthesized Sound Effects (Pure Web Audio API, Zero Assets)
export class CyberAudioEngine {
  constructor() {
    this.ctx = null;
    this.muted = false;
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
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1480, now);
      osc.frequency.exponentialRampToValueAtTime(320, now + 0.04);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.04);
    } catch {}
  }

  playPassAlert() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.setValueAtTime(880, now + 0.08);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.22);
    } catch {}
  }

  playModeClick() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;
    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(2400, now);
      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.015);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.015);
    } catch {}
  }
}
