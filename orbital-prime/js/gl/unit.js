/* OP-01 hardware unit.
   WebGL raymarch of a cream-plastic encoder, driven by LIVE azimuth/elevation.
   Pointer tilt moves the camera only — it never writes telemetry.
   2D canvas fallback is the same object, same numbers. */

const PAPER = "#e8e2d6";
const INK = "#111111";
const ORANGE = "#ff5a00";
const YELLOW = "#ffe600";
const CREAM = "#f2ede4";

export function encoderAngles(azDeg, elDeg) {
  const az = ((Number(azDeg) % 360) + 360) % 360;
  const el = Math.max(-15, Math.min(90, Number(elDeg) || 0));
  return {
    az,
    el,
    discRad: (az * Math.PI) / 180,
    wedgeRad: (Math.max(0, el) / 90) * Math.PI * 1.5,
    locked: el >= 10
  };
}

export function isLocked(elDeg) {
  return encoderAngles(0, elDeg).locked;
}

const VERT = `
attribute vec2 a;
void main(){ gl_Position = vec4(a, 0.0, 1.0); }
`;

const FRAG = `
precision highp float;
uniform vec2 uRes;
uniform float uAz;
uniform float uEl;
uniform float uLock;
uniform vec2 uPtr;
uniform float uHi;

float sdRoundBox(vec3 p, vec3 b, float r) {
  vec3 q = abs(p) - b + r;
  return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}
float sdCyl(vec3 p, float h, float r) {
  vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
  return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}
mat2 rot(float a) {
  float c = cos(a), s = sin(a);
  return mat2(c, -s, s, c);
}

vec2 map(vec3 p) {
  float az = uAz * 0.01745329251;
  float body = sdRoundBox(p - vec3(0.0, -0.22, 0.0), vec3(0.92, 0.20, 0.58), 0.028);
  vec2 d = vec2(body, 1.0);

  float stripe = sdRoundBox(p - vec3(0.0, -0.05, 0.585), vec3(0.90, 0.028, 0.018), 0.0);
  if (stripe < d.x) d = vec2(stripe, 5.0);

  vec3 pd = p;
  pd.xz = rot(-az) * pd.xz;
  float disc = sdCyl(pd - vec3(0.0, 0.12, 0.0), 0.052, 0.46);
  if (disc < d.x) d = vec2(disc, 2.0);

  float hub = sdCyl(pd - vec3(0.0, 0.20, 0.0), 0.065, 0.11);
  if (hub < d.x) d = vec2(hub, 3.0);
  float pin = sdCyl(pd - vec3(0.0, 0.29, 0.0), 0.035, 0.028);
  if (pin < d.x) d = vec2(pin, 3.0);

  float led = length(p - vec3(0.74, 0.02, 0.42)) - 0.042;
  if (led < d.x) d = vec2(led, 4.0);

  float scr = sdRoundBox(p - vec3(-0.38, -0.18, 0.575), vec3(0.36, 0.09, 0.016), 0.008);
  if (scr < d.x) d = vec2(scr, 6.0);

  float fl = p.y + 0.46;
  if (fl < d.x) d = vec2(fl, 7.0);
  return d;
}

vec3 nrm(vec3 p) {
  vec2 e = vec2(0.0016, 0.0);
  return normalize(vec3(
    map(p + e.xyy).x - map(p - e.xyy).x,
    map(p + e.yxy).x - map(p - e.yxy).x,
    map(p + e.yyx).x - map(p - e.yyx).x
  ));
}

float shadow(vec3 ro, vec3 rd) {
  float t = 0.02;
  float res = 1.0;
  for (int i = 0; i < 18; i++) {
    float h = map(ro + rd * t).x;
    res = min(res, 10.0 * h / t);
    t += clamp(h, 0.02, 0.12);
    if (res < 0.02 || t > 5.0) break;
  }
  return clamp(res, 0.0, 1.0);
}

vec3 albedo(vec3 p, float id) {
  vec3 cream = vec3(0.949, 0.929, 0.894);
  vec3 ink = vec3(0.067);
  vec3 orange = vec3(1.0, 0.353, 0.0);
  vec3 yellow = vec3(1.0, 0.902, 0.0);
  vec3 paper = vec3(0.910, 0.886, 0.839);

  if (id < 1.5) {
    float plate = step(0.78, abs(p.x)) * step(abs(p.z), 0.50) * step(abs(p.y + 0.22), 0.18);
    return mix(cream, ink, plate * 0.08);
  }
  if (id < 2.5) {
    float az = uAz * 0.01745329251;
    vec3 q = p;
    q.xz = rot(-az) * q.xz;
    float ang = atan(q.z, q.x);
    if (ang < 0.0) ang += 6.2831853;
    float span = clamp(uEl, 0.0, 90.0) / 90.0 * 4.7123889;
    float r = length(q.xz);
    vec3 col = cream;
    if (ang < span && r < 0.44 && r > 0.14) col = orange;
    float tick = abs(fract(ang / 0.261799 + 0.5) - 0.5);
    if (tick < 0.04 && r > 0.34 && r < 0.45) col = ink;
    if (r > 0.45) col = ink;
    return col;
  }
  if (id < 3.5) return ink;
  if (id < 4.5) return mix(ink, orange, clamp(uLock, 0.0, 1.0));
  if (id < 5.5) return yellow;
  if (id < 6.5) return vec3(0.12);
  return paper;
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
  vec3 ro = vec3(
    0.0 + uPtr.x * 0.85,
    1.15 + uPtr.y * 0.35,
    2.15
  );
  vec3 ta = vec3(0.0, -0.05, 0.0);
  vec3 ww = normalize(ta - ro);
  vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
  vec3 vv = cross(uu, ww);
  vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.55 * ww);

  float t = 0.0;
  vec2 h = vec2(1.0);
  float maxS = uHi > 0.5 ? 88.0 : 56.0;
  for (int i = 0; i < 88; i++) {
    if (float(i) > maxS) break;
    h = map(ro + rd * t);
    if (h.x < 0.0012 || t > 8.0) break;
    t += h.x * 0.85;
  }

  vec3 paper = vec3(0.910, 0.886, 0.839);
  vec3 col = paper;
  if (h.x < 0.002 && t < 8.0) {
    vec3 p = ro + rd * t;
    vec3 n = nrm(p);
    vec3 l = normalize(vec3(0.55, 0.85, 0.40));
    vec3 alb = albedo(p, h.y);
    float dif = max(dot(n, l), 0.0);
    float amb = 0.38 + 0.22 * n.y;
    float spec = pow(max(dot(reflect(-l, n), normalize(-rd)), 0.0), 48.0);
    float sh = 1.0;
    if (h.y < 6.5) sh = mix(0.45, 1.0, shadow(p + n * 0.02, l));
    col = alb * (amb + dif * 0.85 * sh) + vec3(0.55) * spec * sh * step(h.y, 3.5);
    if (h.y > 3.5 && h.y < 4.5 && uLock > 0.5) col += vec3(1.0, 0.35, 0.0) * 0.35;
    float fog = 1.0 - exp(-0.04 * t * t);
    col = mix(col, paper, fog * 0.15);
  }
  col = pow(clamp(col, 0.0, 1.0), vec3(0.96));
  gl_FragColor = vec4(col, 1.0);
}
`;

function compile(gl, type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(s) || "shader compile failed";
    gl.deleteShader(s);
    throw new Error(log);
  }
  return s;
}

function makeProgram(gl) {
  const vs = compile(gl, gl.VERTEX_SHADER, VERT);
  const fs = compile(gl, gl.FRAGMENT_SHADER, FRAG);
  const p = gl.createProgram();
  gl.attachShader(p, vs);
  gl.attachShader(p, fs);
  gl.bindAttribLocation(p, 0, "a");
  gl.linkProgram(p);
  gl.deleteShader(vs);
  gl.deleteShader(fs);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
    throw new Error(gl.getProgramInfoLog(p) || "program link failed");
  }
  return p;
}

export function drawUnit2d(ctx, w, h, look, ptr = { x: 0, y: 0 }) {
  const e = encoderAngles(look?.az ?? 0, look?.el ?? 0);
  const cx = w * 0.5 + ptr.x * w * 0.04;
  const cy = h * 0.52 + ptr.y * h * 0.03;
  const s = Math.min(w, h);

  ctx.fillStyle = PAPER;
  ctx.fillRect(0, 0, w, h);

  const bw = s * 0.78;
  const bh = s * 0.34;
  const bx = cx - bw / 2;
  const by = cy - bh * 0.15;

  ctx.fillStyle = "#cfc8ba";
  ctx.fillRect(bx + 8, by + bh + 10, bw, 10);

  ctx.fillStyle = CREAM;
  ctx.strokeStyle = INK;
  ctx.lineWidth = 2;
  ctx.fillRect(bx, by, bw, bh);
  ctx.strokeRect(bx, by, bw, bh);

  ctx.fillStyle = YELLOW;
  ctx.fillRect(bx, by, 10, bh);
  ctx.strokeRect(bx, by, 10, bh);

  ctx.fillStyle = INK;
  ctx.fillRect(bx + 18, by + bh - 28, bw * 0.38, 18);
  ctx.fillStyle = YELLOW;
  ctx.font = `700 ${Math.max(10, s * 0.028)}px "Space Mono", monospace`;
  ctx.textBaseline = "middle";
  ctx.fillText("OP-01", bx + 26, by + bh - 19);

  const dx = cx + s * 0.02;
  const dy = by - s * 0.02;
  const R = s * 0.22;

  ctx.beginPath();
  ctx.arc(dx, dy, R + 4, 0, Math.PI * 2);
  ctx.fillStyle = INK;
  ctx.fill();

  ctx.beginPath();
  ctx.arc(dx, dy, R, 0, Math.PI * 2);
  ctx.fillStyle = CREAM;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = INK;
  ctx.stroke();

  ctx.save();
  ctx.translate(dx, dy);
  ctx.rotate(e.discRad);
  ctx.fillStyle = ORANGE;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.arc(0, 0, R * 0.92, -Math.PI / 2, -Math.PI / 2 + e.wedgeRad, false);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = INK;
  ctx.lineWidth = 1.5;
  for (let i = 0; i < 24; i++) {
    const a = (i / 24) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(Math.cos(a) * R * 0.78, Math.sin(a) * R * 0.78);
    ctx.lineTo(Math.cos(a) * R * 0.96, Math.sin(a) * R * 0.96);
    ctx.stroke();
  }
  ctx.fillStyle = CREAM;
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.28, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = INK;
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = INK;
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.07, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  ctx.fillStyle = INK;
  ctx.beginPath();
  ctx.moveTo(dx, dy - R - 10);
  ctx.lineTo(dx + 7, dy - R + 4);
  ctx.lineTo(dx - 7, dy - R + 4);
  ctx.closePath();
  ctx.fill();

  const ledX = bx + bw - 22;
  const ledY = by + 22;
  ctx.beginPath();
  ctx.arc(ledX, ledY, 8, 0, Math.PI * 2);
  ctx.fillStyle = e.locked ? ORANGE : INK;
  ctx.fill();
  ctx.strokeStyle = INK;
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = INK;
  ctx.font = `700 ${Math.max(9, s * 0.022)}px "Space Mono", monospace`;
  ctx.textAlign = "right";
  ctx.fillText(`${e.az.toFixed(0)}° AZ`, bx + bw - 14, by + bh - 36);
  ctx.fillText(`${e.el.toFixed(0)}° EL`, bx + bw - 14, by + bh - 18);
  ctx.textAlign = "left";
}

function reduced() {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function initUnit({ glCanvas, fallbackCanvas, stage }) {
  const look = { az: 0, el: 0, lock: false };
  const ptr = { x: 0, y: 0 };
  const targetPtr = { x: 0, y: 0 };
  let mode = "2d";
  let gl = null;
  let prog = null;
  let loc = null;
  let raf = 0;
  let visible = true;
  let dirty = true;
  let destroyed = false;
  let buf = null;

  const hi = typeof navigator !== "undefined"
    && !/Mobi|Android/i.test(navigator.userAgent || "");

  try {
    gl = glCanvas.getContext("webgl", {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      powerPreference: "low-power",
      preserveDrawingBuffer: false
    });
    if (!gl) throw new Error("no webgl");
    prog = makeProgram(gl);
    buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.useProgram(prog);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    loc = {
      res: gl.getUniformLocation(prog, "uRes"),
      az: gl.getUniformLocation(prog, "uAz"),
      el: gl.getUniformLocation(prog, "uEl"),
      lock: gl.getUniformLocation(prog, "uLock"),
      ptr: gl.getUniformLocation(prog, "uPtr"),
      hi: gl.getUniformLocation(prog, "uHi")
    };
    mode = "webgl";
    fallbackCanvas.hidden = true;
    fallbackCanvas.setAttribute("aria-hidden", "true");
    glCanvas.hidden = false;
    glCanvas.removeAttribute("aria-hidden");
  } catch {
    mode = "2d";
    gl = null;
    glCanvas.hidden = true;
    glCanvas.setAttribute("aria-hidden", "true");
    fallbackCanvas.hidden = false;
    fallbackCanvas.removeAttribute("aria-hidden");
  }

  function size2d() {
    const parent = stage || fallbackCanvas.parentElement;
    const w = Math.max(1, parent.clientWidth);
    const h = Math.max(1, parent.clientHeight);
    const dpr = Math.min((typeof window !== "undefined" && window.devicePixelRatio) || 1, 2);
    const bw = Math.round(w * dpr);
    const bh = Math.round(h * dpr);
    if (fallbackCanvas.width !== bw || fallbackCanvas.height !== bh) {
      fallbackCanvas.width = bw;
      fallbackCanvas.height = bh;
      fallbackCanvas.style.width = w + "px";
      fallbackCanvas.style.height = h + "px";
    }
    const ctx = fallbackCanvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w, h };
  }

  function sizeGl() {
    const parent = stage || glCanvas.parentElement;
    const w = Math.max(1, parent.clientWidth);
    const h = Math.max(1, parent.clientHeight);
    const dpr = Math.min((typeof window !== "undefined" && window.devicePixelRatio) || 1, hi ? 1.5 : 1);
    const bw = Math.max(1, Math.round(w * dpr));
    const bh = Math.max(1, Math.round(h * dpr));
    if (glCanvas.width !== bw || glCanvas.height !== bh) {
      glCanvas.width = bw;
      glCanvas.height = bh;
      glCanvas.style.width = w + "px";
      glCanvas.style.height = h + "px";
    }
    return { bw, bh };
  }

  function paint() {
    if (destroyed) return;
    if (mode === "webgl" && gl && prog) {
      const { bw, bh } = sizeGl();
      gl.viewport(0, 0, bw, bh);
      gl.useProgram(prog);
      gl.uniform2f(loc.res, bw, bh);
      gl.uniform1f(loc.az, look.az);
      gl.uniform1f(loc.el, look.el);
      gl.uniform1f(loc.lock, look.lock ? 1 : 0);
      gl.uniform2f(loc.ptr, ptr.x, ptr.y);
      gl.uniform1f(loc.hi, hi ? 1 : 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    } else {
      const { ctx, w, h } = size2d();
      drawUnit2d(ctx, w, h, look, ptr);
    }
    dirty = false;
  }

  function loop() {
    if (destroyed) return;
    raf = requestAnimationFrame(loop);
    if (!visible) return;
    if (typeof document !== "undefined" && document.hidden) return;
    if (!reduced()) {
      ptr.x += (targetPtr.x - ptr.x) * 0.12;
      ptr.y += (targetPtr.y - ptr.y) * 0.12;
      if (Math.abs(ptr.x - targetPtr.x) > 0.001 || Math.abs(ptr.y - targetPtr.y) > 0.001) dirty = true;
    }
    if (dirty) paint();
  }

  function onPtr(ev) {
    if (!stage) return;
    const r = stage.getBoundingClientRect();
    const nx = ((ev.clientX - r.left) / r.width) * 2 - 1;
    const ny = ((ev.clientY - r.top) / r.height) * 2 - 1;
    targetPtr.x = Math.max(-1, Math.min(1, nx)) * 0.65;
    targetPtr.y = Math.max(-1, Math.min(1, -ny)) * 0.45;
    if (reduced()) {
      ptr.x = targetPtr.x;
      ptr.y = targetPtr.y;
      dirty = true;
      paint();
    }
  }

  function onLeave() {
    targetPtr.x = 0;
    targetPtr.y = 0;
    if (reduced()) {
      ptr.x = 0;
      ptr.y = 0;
      dirty = true;
      paint();
    }
  }

  const io = typeof IntersectionObserver === "function"
    ? new IntersectionObserver((entries) => {
      visible = entries.some((e) => e.isIntersecting);
      if (visible) {
        dirty = true;
        paint();
      }
    }, { threshold: 0.05 })
    : null;
  if (io && stage) io.observe(stage);

  if (stage) {
    stage.addEventListener("pointermove", onPtr);
    stage.addEventListener("pointerleave", onLeave);
  }

  const onResize = () => {
    dirty = true;
    paint();
  };
  if (typeof window !== "undefined") window.addEventListener("resize", onResize);

  paint();
  if (!reduced()) raf = requestAnimationFrame(loop);
  else {
    const canvas = mode === "webgl" ? glCanvas : fallbackCanvas;
    canvas.setAttribute("data-reduced", "1");
  }

  function describe() {
    const e = encoderAngles(look.az, look.el);
    const host = mode === "webgl" ? glCanvas : fallbackCanvas;
    host.setAttribute(
      "aria-label",
      `OP-01 hardware unit. Azimuth ${e.az.toFixed(0)} degrees. Elevation ${e.el.toFixed(0)} degrees. Encoder follows live lock. Pointer tilt is camera only.`
    );
  }

  return {
    get mode() { return mode; },
    setLook({ az, el }) {
      const e = encoderAngles(az, el);
      if (e.az === look.az && e.el === look.el && e.locked === look.lock) return;
      look.az = e.az;
      look.el = e.el;
      look.lock = e.locked;
      dirty = true;
      describe();
      if (reduced() || !visible) paint();
    },
    setPointer(nx, ny) {
      targetPtr.x = nx;
      targetPtr.y = ny;
    },
    destroy() {
      destroyed = true;
      cancelAnimationFrame(raf);
      io?.disconnect();
      if (stage) {
        stage.removeEventListener("pointermove", onPtr);
        stage.removeEventListener("pointerleave", onLeave);
      }
      if (typeof window !== "undefined") window.removeEventListener("resize", onResize);
      if (gl && buf) gl.deleteBuffer(buf);
      if (gl && prog) gl.deleteProgram(prog);
    }
  };
}
