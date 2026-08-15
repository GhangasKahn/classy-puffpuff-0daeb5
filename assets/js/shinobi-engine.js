/**
 * ============================================================================
 * SOVEREIGN SITEFORGE v3.0 — SHINOBI//82 KAGE INTERACTIVE ENGINE
 * High-Precision Blade Mechanics, Wolfram Mass Engine & Field Protocols
 * ============================================================================
 */

(function () {
  'use strict';

  // --------------------------------------------------------------------------
  // 1. STATE MANAGEMENT & SYSTEM REGISTRY
  // --------------------------------------------------------------------------
  const SHINOBI_STATE = {
    theme: localStorage.getItem('shinobi_theme') || 'dark',
    audioEnabled: false,
    handedness: 'right', // 'right' | 'left'
    selectedBlade: 'mizu', // 'mizu' | 'kumiko' | 'nata'
    activeLayer: 'assembly', // 'assembly' | 'skeleton' | 'lamination' | 'ura'
    caliperPosition: 35, // mm from heel (0 to 82)
    activeMission: 'river', // 'kumiko' | 'river' | 'trail' | 'niagara' | 'atelier'
    ergoMode: 'precision', // 'precision' | 'power'
    ikejimeSpecies: 'trout', // 'trout' | 'bass' | 'salmon'
    unboxingStage: 1, // 1 to 4
    customComponents: {
      handle: true,
      kusabi: true,
      inlays: true,
      mizu_blade: true,
      kumiko_blade: false,
      nata_blade: false,
      saya: true,
      tag_spike: true,
      tweezers: true,
      wire_s50: true,
      wire_l80: false,
      strop_tether: true,
      kiri_box: false
    }
  };

  // Component Mass Database (Wolfram Solid Geometry Calibrated in Grams)
  const COMPONENT_WEIGHTS = {
    handle: { name: 'Grade 5 Ti Monocoque Handle (Ti-6Al-4V)', weight: 11.20, mat: 'Aerospace Grade 5 Titanium' },
    kusabi: { name: 'Kusabi-Lock™ Titanium Tapered Wedge', weight: 1.10, mat: 'Ti-6Al-4V Precision Wire-EDM' },
    inlays: { name: 'Removable Kurogaki (Black Persimmon) Inlays', weight: 1.80, mat: 'Natural Japanese Kurogaki Wood' },
    mizu_blade: { name: 'MIZU-82 MagnaMax™ Flagship Blade (82mm)', weight: 6.10, mat: 'MagnaMax Steel (63 HRC) + Ti Rail' },
    kumiko_blade: { name: 'KUMIKO-42 Scribing & Joinery Blade (42mm)', weight: 3.42, mat: 'MagnaCut (62.5 HRC) Dead-Flat Back' },
    nata_blade: { name: 'NATA-60 Heavy Trailcraft Chisel Blade (60mm)', weight: 5.10, mat: 'MagnaCut (62.5 HRC) 24° Single Bevel' },
    saya: { name: 'KAGE-SAYA™ Honoki/Urushi Sheath & Palm Swell', weight: 5.10, mat: 'Natural Honoki + Wajima Black Urushi' },
    tag_spike: { name: 'KAGE-TAG™ Diamond Plate & 34mm Brain Spike', weight: 1.90, mat: 'Monocrystalline Diamond + Hardened Ti' },
    tweezers: { name: 'KAGE-TWEEZ™ Beta-Titanium Pinbone Extractor', weight: 0.55, mat: 'Beta-C Titanium Alloy (Spring Tempered)' },
    wire_s50: { name: 'SHINKEI S-50 Nitinol Wire (0.8 × 500mm)', weight: 0.85, mat: 'Shape-Memory Nitinol Alloy' },
    wire_l80: { name: 'SHINKEI L-80 Nitinol Wire (1.2 × 800mm)', weight: 2.45, mat: 'Shape-Memory Nitinol Alloy' },
    strop_tether: { name: '1μm Diamond Strop Film & Dyneema Tether', weight: 0.60, mat: 'Diamond Matrix + Ultra-High Mol. PE' },
    kiri_box: { name: 'Atelier Paulownia (Kiri) Vault Storage Box', weight: 24.00, mat: 'Aged Paulownia + Kurogaki Inset' }
  };

  const MISSION_PRESETS = {
    kumiko: {
      title: 'Kumiko Workshop',
      desc: 'Joinery layout, dovetail scribing & precision chamfering',
      target: 17.52,
      components: {
        handle: true, kusabi: true, inlays: true,
        mizu_blade: false, kumiko_blade: true, nata_blade: false,
        saya: false, tag_spike: false, tweezers: false,
        wire_s50: false, wire_l80: false, strop_tether: false, kiri_box: false
      }
    },
    river: {
      title: 'Backcountry River',
      desc: 'Alpine trout, panfish deboning & fast backcountry carry',
      target: 24.06,
      components: {
        handle: true, kusabi: true, inlays: false,
        mizu_blade: true, kumiko_blade: false, nata_blade: false,
        saya: true, tag_spike: true, tweezers: true,
        wire_s50: true, wire_l80: false, strop_tether: true, kiri_box: false
      }
    },
    trail: {
      title: 'Trailcraft & Seam',
      desc: 'Big game seam deboning, camp food prep & wood carving',
      target: 27.20,
      components: {
        handle: true, kusabi: true, inlays: true,
        mizu_blade: true, kumiko_blade: false, nata_blade: false,
        saya: true, tag_spike: true, tweezers: false,
        wire_s50: false, wire_l80: false, strop_tether: true, kiri_box: false
      }
    },
    niagara: {
      title: 'Niagara Salmon',
      desc: 'Adult Great Lakes Chinook, heavy fish ikijime & power deboning',
      target: 30.66,
      components: {
        handle: true, kusabi: true, inlays: true,
        mizu_blade: true, kumiko_blade: false, nata_blade: false,
        saya: true, tag_spike: true, tweezers: true,
        wire_s50: false, wire_l80: true, strop_tether: true, kiri_box: false
      }
    },
    atelier: {
      title: 'Master Atelier',
      desc: 'Complete 12-piece ecosystem in Paulownia Kiri vault',
      target: 58.36,
      components: {
        handle: true, kusabi: true, inlays: true,
        mizu_blade: true, kumiko_blade: true, nata_blade: true,
        saya: true, tag_spike: true, tweezers: true,
        wire_s50: true, wire_l80: true, strop_tether: true, kiri_box: true
      }
    }
  };

  // --------------------------------------------------------------------------
  // 2. AUDIO SYNTHESIZER (Web Audio API for Tactile Acoustic Feedback)
  // --------------------------------------------------------------------------
  let audioCtx = null;
  function playTactileClick(type = 'click') {
    if (!SHINOBI_STATE.audioEnabled) return;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }

      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      const now = audioCtx.currentTime;

      if (type === 'click') {
        // High-frequency titanium micro-click
        osc.type = 'sine';
        osc.frequency.setValueAtTime(2400, now);
        osc.frequency.exponentialRampToValueAtTime(800, now + 0.04);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.04);
      } else if (type === 'lock') {
        // Metallic acoustic resonance (Kusabi lock snap)
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(440, now + 0.12);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.12);
      }
    } catch (e) {
      console.warn('Audio synthesis disabled or unsupported', e);
    }
  }

  // --------------------------------------------------------------------------
  // 3. INTERACTIVE 2D CANVAS BLADE VISUALIZER
  // --------------------------------------------------------------------------
  class BladeCanvasEngine {
    constructor(canvasId) {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext('2d');
      this.width = this.canvas.width = this.canvas.parentElement.clientWidth * window.devicePixelRatio;
      this.height = this.canvas.height = 380 * window.devicePixelRatio;
      this.mouseX = this.width / 2;
      this.mouseY = this.height / 2;
      this.targetLightX = this.width / 2;
      this.lightX = this.width / 2;
      this.isHovering = false;

      this.initEvents();
      this.animate();
    }

    initEvents() {
      const handleMove = (e) => {
        const rect = this.canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        this.mouseX = (clientX - rect.left) * window.devicePixelRatio;
        this.mouseY = (clientY - rect.top) * window.devicePixelRatio;
        this.targetLightX = this.mouseX;
        this.isHovering = true;
      };

      this.canvas.addEventListener('mousemove', handleMove);
      this.canvas.addEventListener('touchmove', handleMove, { passive: true });
      this.canvas.addEventListener('mouseleave', () => { this.isHovering = false; });
      this.canvas.addEventListener('touchend', () => { this.isHovering = false; });

      window.addEventListener('resize', () => {
        if (!this.canvas) return;
        this.width = this.canvas.width = this.canvas.parentElement.clientWidth * window.devicePixelRatio;
        this.height = this.canvas.height = 380 * window.devicePixelRatio;
      });
    }

    animate() {
      // Smooth light interpolation
      this.lightX += (this.targetLightX - this.lightX) * 0.08;
      this.render();
      requestAnimationFrame(() => this.animate());
    }

    render() {
      const ctx = this.ctx;
      const w = this.width;
      const h = this.height;
      const dpr = window.devicePixelRatio || 1;

      ctx.clearRect(0, 0, w, h);

      // Background Subtle Blueprint Grid
      ctx.strokeStyle = SHINOBI_STATE.theme === 'light' ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.04)';
      ctx.lineWidth = 1 * dpr;
      const step = 30 * dpr;
      for (let x = 0; x < w; x += step) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
      }
      for (let y = 0; y < h; y += step) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      }

      // Center Coordinate Frame
      const centerX = w * 0.52;
      const centerY = h * 0.5;
      const scale = Math.min(w / 700, 1.4) * dpr;

      ctx.save();
      ctx.translate(centerX, centerY);

      // Handedness Inversion if Left Handed
      if (SHINOBI_STATE.handedness === 'left') {
        ctx.scale(1, -1);
      }

      // 1. Draw Grade 5 Titanium Monocoque Handle
      this.drawTitaniumHandle(ctx, scale);

      // 2. Draw Blade Module based on state
      this.drawBladeModule(ctx, scale);

      // 3. Draw Active Layer Inspection Overlays
      if (SHINOBI_STATE.activeLayer === 'skeleton') {
        this.drawStressLoadPaths(ctx, scale);
      } else if (SHINOBI_STATE.activeLayer === 'lamination') {
        this.drawLaminationDovetail(ctx, scale);
      } else if (SHINOBI_STATE.activeLayer === 'ura') {
        this.drawUrasukiMap(ctx, scale);
      }

      // 4. Draw Precision Caliper Dimension Overlay
      this.drawCaliperOverlay(ctx, scale);

      ctx.restore();
    }

    drawTitaniumHandle(ctx, scale) {
      const dpr = window.devicePixelRatio || 1;
      const isDark = SHINOBI_STATE.theme !== 'light';

      ctx.save();
      // Handle bounds: approx x from -240*scale to -20*scale, y from -22*scale to +22*scale
      ctx.beginPath();
      ctx.moveTo(-20 * scale, -14 * scale);
      ctx.lineTo(-140 * scale, -16 * scale);
      ctx.quadraticCurveTo(-220 * scale, -14 * scale, -240 * scale, 0);
      ctx.quadraticCurveTo(-220 * scale, 14 * scale, -140 * scale, 16 * scale);
      ctx.lineTo(-20 * scale, 18 * scale);
      ctx.lineTo(-20 * scale, -14 * scale);
      ctx.closePath();

      // Titanium Metallic Gradient
      const grad = ctx.createLinearGradient(-240 * scale, 0, 0, 0);
      if (isDark) {
        grad.addColorStop(0, '#1c2226');
        grad.addColorStop(0.5, '#2e373d');
        grad.addColorStop(1, '#1e2428');
      } else {
        grad.addColorStop(0, '#c8d0d5');
        grad.addColorStop(0.5, '#e4eaee');
        grad.addColorStop(1, '#bcc5cb');
      }
      ctx.fillStyle = grad;
      ctx.fill();

      ctx.strokeStyle = isDark ? '#47555e' : '#8896a0';
      ctx.lineWidth = 1.5 * dpr;
      ctx.stroke();

      // Skeletal Apertures (Reel Spool Inspired Lightweight Openings)
      const apertures = [
        { x: -70 * scale, y: 0, rx: 24 * scale, ry: 7 * scale },
        { x: -140 * scale, y: 0, rx: 32 * scale, ry: 8 * scale },
        { x: -200 * scale, y: 0, rx: 14 * scale, ry: 5 * scale }
      ];

      apertures.forEach(ap => {
        ctx.beginPath();
        ctx.ellipse(ap.x, ap.y, ap.rx, ap.ry, 0, 0, Math.PI * 2);
        ctx.fillStyle = isDark ? '#0b0d0e' : '#f0f4f7';
        ctx.fill();
        ctx.strokeStyle = isDark ? '#333e46' : '#a0adb6';
        ctx.lineWidth = 1 * dpr;
        ctx.stroke();
      });

      // Kurogaki Persimmon Wood Inlays if active
      if (SHINOBI_STATE.customComponents.inlays) {
        ctx.beginPath();
        ctx.roundRect(-100 * scale, -12 * scale, 24 * scale, 24 * scale, 4 * scale);
        ctx.fillStyle = '#1c1714'; // Kurogaki deep charcoal wood
        ctx.fill();
        ctx.strokeStyle = '#5a4638';
        ctx.stroke();
      }

      // Kusabi Wedge Pin at connection point
      ctx.beginPath();
      ctx.arc(-22 * scale, 0, 4 * scale, 0, Math.PI * 2);
      ctx.fillStyle = '#d43f2a'; // Vermilion lock indicator
      ctx.fill();

      ctx.restore();
    }

    drawBladeModule(ctx, scale) {
      const dpr = window.devicePixelRatio || 1;
      const isDark = SHINOBI_STATE.theme !== 'light';
      const blade = SHINOBI_STATE.selectedBlade;

      ctx.save();
      let bladeLength = 82; // mm
      let spineHeight = 15.2; // mm
      let tipY = 4;

      if (blade === 'mizu') {
        bladeLength = 82; spineHeight = 15.2; tipY = 3;
      } else if (blade === 'kumiko') {
        bladeLength = 42; spineHeight = 13.0; tipY = -6; // Kiridashi point
      } else if (blade === 'nata') {
        bladeLength = 60; spineHeight = 18.0; tipY = 0; // Chisel blunt nose
      }

      const blScale = bladeLength * 2.8 * scale;
      const hScale = spineHeight * 1.5 * scale;

      // Draw MagnaMax/MagnaCut Steel Blade Body
      ctx.beginPath();
      ctx.moveTo(-20 * scale, -12 * scale); // Heel top
      ctx.lineTo(blScale * 0.7, -10 * scale); // Spine straight
      ctx.quadraticCurveTo(blScale * 0.9, -6 * scale, blScale, tipY * scale); // Tip kissaki
      ctx.quadraticCurveTo(blScale * 0.5, hScale * 0.8, -20 * scale, 14 * scale); // Cutting belly & heel
      ctx.closePath();

      // Mirror Steel Gradient with specular shine based on cursor
      const lightRatio = Math.max(0.1, Math.min(0.9, (this.lightX / this.width)));
      const steelGrad = ctx.createLinearGradient(0, -15 * scale, blScale, 15 * scale);
      if (isDark) {
        steelGrad.addColorStop(0, '#707f8a');
        steelGrad.addColorStop(Math.max(0, lightRatio - 0.1), '#9db0bc');
        steelGrad.addColorStop(lightRatio, '#ffffff'); // Specular highlight
        steelGrad.addColorStop(Math.min(1, lightRatio + 0.1), '#8ca0ac');
        steelGrad.addColorStop(1, '#536069');
      } else {
        steelGrad.addColorStop(0, '#55616a');
        steelGrad.addColorStop(lightRatio, '#1f2529');
        steelGrad.addColorStop(1, '#66737c');
      }

      ctx.fillStyle = steelGrad;
      ctx.fill();
      ctx.strokeStyle = isDark ? '#b0c2cd' : '#333e46';
      ctx.lineWidth = 1.2 * dpr;
      ctx.stroke();

      // Shinogi-Zukuri Ridge Line (The Japanese Bevel Transition)
      ctx.beginPath();
      ctx.moveTo(-18 * scale, 0);
      ctx.quadraticCurveTo(blScale * 0.6, 2 * scale, blScale, tipY * scale);
      ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)';
      ctx.lineWidth = 1 * dpr;
      ctx.stroke();

      // Dovetail Lamination Line (Indigo Laser Seam)
      ctx.beginPath();
      ctx.moveTo(-18 * scale, -4 * scale);
      ctx.lineTo(blScale * 0.65, -4 * scale);
      ctx.strokeStyle = '#4e74be'; // Aizome Indigo
      ctx.lineWidth = 2 * dpr;
      ctx.setLineDash([4 * dpr, 2 * dpr]);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.restore();
    }

    drawStressLoadPaths(ctx, scale) {
      const dpr = window.devicePixelRatio || 1;
      ctx.save();
      ctx.strokeStyle = '#22c55e'; // Green strain vector lines
      ctx.lineWidth = 1.5 * dpr;

      // Dorsal Compression Rail
      ctx.beginPath();
      ctx.moveTo(-230 * scale, -10 * scale);
      ctx.lineTo(140 * scale, -8 * scale);
      ctx.stroke();

      // Ventral Tension Rail
      ctx.beginPath();
      ctx.moveTo(-230 * scale, 10 * scale);
      ctx.lineTo(-20 * scale, 12 * scale);
      ctx.stroke();

      // Radiused Diagonal Bridges
      [ -170, -110, -50 ].forEach(x => {
        ctx.beginPath();
        ctx.moveTo(x * scale, -12 * scale);
        ctx.lineTo((x + 20) * scale, 12 * scale);
        ctx.stroke();
      });

      ctx.restore();
    }

    drawLaminationDovetail(ctx, scale) {
      const dpr = window.devicePixelRatio || 1;
      ctx.save();
      ctx.fillStyle = 'rgba(78, 116, 190, 0.25)';
      ctx.fillRect(-20 * scale, -6 * scale, 160 * scale, 16 * scale);
      ctx.strokeStyle = '#4e74be';
      ctx.lineWidth = 2 * dpr;
      ctx.strokeRect(-20 * scale, -6 * scale, 160 * scale, 16 * scale);
      ctx.restore();
    }

    drawUrasukiMap(ctx, scale) {
      const dpr = window.devicePixelRatio || 1;
      ctx.save();
      ctx.fillStyle = 'rgba(212, 63, 42, 0.2)';
      ctx.beginPath();
      ctx.roundRect(0, 0, 150 * scale, 12 * scale, 6 * scale);
      ctx.fill();
      ctx.strokeStyle = '#d43f2a';
      ctx.lineWidth = 1 * dpr;
      ctx.stroke();
      ctx.restore();
    }

    drawCaliperOverlay(ctx, scale) {
      const dpr = window.devicePixelRatio || 1;
      const calX = (SHINOBI_STATE.caliperPosition * 2.8 - 20) * scale;

      ctx.save();
      // Caliper vertical cursor line
      ctx.strokeStyle = '#d43f2a';
      ctx.lineWidth = 1.5 * dpr;
      ctx.setLineDash([3 * dpr, 3 * dpr]);
      ctx.beginPath();
      ctx.moveTo(calX, -40 * scale);
      ctx.lineTo(calX, 40 * scale);
      ctx.stroke();
      ctx.setLineDash([]);

      // Position Tag
      ctx.fillStyle = '#d43f2a';
      ctx.fillRect(calX - 24 * dpr, -46 * scale, 48 * dpr, 16 * dpr);
      ctx.fillStyle = '#ffffff';
      ctx.font = `${9 * dpr}px 'JetBrains Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.fillText(`${SHINOBI_STATE.caliperPosition}mm`, calX, -46 * scale + 12 * dpr);

      ctx.restore();
    }
  }

  // --------------------------------------------------------------------------
  // 4. WOLFRAM MASS & MISSION ENGINE
  // --------------------------------------------------------------------------
  class MassCalculatorEngine {
    constructor() {
      this.initMissionSelectors();
      this.initChecklistListeners();
      this.recalculate();
    }

    initMissionSelectors() {
      const missionBtns = document.querySelectorAll('.mission-btn');
      missionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const missionKey = btn.dataset.mission;
          if (!MISSION_PRESETS[missionKey]) return;

          missionBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          SHINOBI_STATE.activeMission = missionKey;
          const preset = MISSION_PRESETS[missionKey];

          // Apply component preset
          Object.keys(preset.components).forEach(compKey => {
            SHINOBI_STATE.customComponents[compKey] = preset.components[compKey];
            const checkbox = document.getElementById(`comp_${compKey}`);
            if (checkbox) checkbox.checked = preset.components[compKey];
          });

          playTactileClick('lock');
          this.recalculate();
        });
      });
    }

    initChecklistListeners() {
      const checkboxes = document.querySelectorAll('.component-check-item input[type="checkbox"]');
      checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
          const compKey = cb.dataset.component;
          if (compKey && SHINOBI_STATE.customComponents.hasOwnProperty(compKey)) {
            SHINOBI_STATE.customComponents[compKey] = cb.checked;
            playTactileClick('click');
            this.recalculate();
          }
        });
      });
    }

    recalculate() {
      let totalGrams = 0;
      let activeCount = 0;

      Object.keys(SHINOBI_STATE.customComponents).forEach(key => {
        if (SHINOBI_STATE.customComponents[key] && COMPONENT_WEIGHTS[key]) {
          totalGrams += COMPONENT_WEIGHTS[key].weight;
          activeCount++;
        }
      });

      const totalOz = totalGrams / 28.3495;
      const oneOuncePercent = Math.min(100, (totalGrams / 28.3495) * 100);

      // Update DOM Readouts
      const gramsEl = document.getElementById('calcGramsOutput');
      const ozEl = document.getElementById('calcOzOutput');
      const barFillEl = document.getElementById('calcBarFill');
      const countEl = document.getElementById('calcActiveItemCount');

      if (gramsEl) gramsEl.textContent = `${totalGrams.toFixed(2)} g`;
      if (ozEl) ozEl.textContent = `${totalOz.toFixed(3)} oz`;
      if (barFillEl) {
        barFillEl.style.width = `${oneOuncePercent}%`;
        barFillEl.style.backgroundColor = totalGrams > 28.35 ? 'oklch(0.65 0.2 25)' : 'var(--accent-vermilion)';
      }
      if (countEl) countEl.textContent = `${activeCount} Modules Active`;

      // Update Balance Point Estimation
      const balanceEl = document.getElementById('calcBalancePoint');
      if (balanceEl) {
        // Calculated CG relative to choil
        const cg = (7.2 + (totalGrams > 30 ? 1.4 : 0)).toFixed(1);
        balanceEl.textContent = `${cg} mm behind choil`;
      }
    }
  }

  // --------------------------------------------------------------------------
  // 5. GEOMETRY CROSS-SECTION & APEX INSPECTOR
  // --------------------------------------------------------------------------
  class CrossSectionInspector {
    constructor() {
      this.slider = document.getElementById('caliperSlider');
      this.svg = document.getElementById('crossSectionSvg');
      if (!this.slider || !this.svg) return;

      this.slider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value, 10);
        SHINOBI_STATE.caliperPosition = val;
        this.updateReadout(val);
        this.renderSvg(val);
      });

      this.renderSvg(SHINOBI_STATE.caliperPosition);
    }

    updateReadout(pos) {
      const posLabel = document.getElementById('caliperPosLabel');
      const thicknessLabel = document.getElementById('caliperThicknessLabel');
      const angleLabel = document.getElementById('caliperAngleLabel');
      const bevelDesc = document.getElementById('caliperBevelDesc');

      if (posLabel) posLabel.textContent = `${pos} mm`;

      // Distal calculations
      let thickness = (1.55 - (pos / 82) * (1.55 - 0.60)).toFixed(2);
      let angle = pos < 22 ? '15.0° / 17.0° (Reinforced Heel)' : '12.0° / 14.0° (Asymmetric Hamaguri)';

      if (thicknessLabel) thicknessLabel.textContent = `${thickness} mm`;
      if (angleLabel) angleLabel.textContent = angle;
      if (bevelDesc) {
        if (pos < 22) {
          bevelDesc.textContent = 'Reinforced 15°/17° thread-edge for hardwood dovetails, tendons, and cartilage.';
        } else if (pos > 70) {
          bevelDesc.textContent = 'Ultra-thin 0.60mm kissaki point with continuous convex support for caping & joints.';
        } else {
          bevelDesc.textContent = 'Continuous Hamaguri convex belly; Effortless raw fish release & high apex stability.';
        }
      }
    }

    renderSvg(pos) {
      const isRight = SHINOBI_STATE.handedness === 'right';
      const spineWidth = 14 + (1.55 - (pos / 82) * 0.95) * 8; // scaled px
      const urasukiDepth = pos < 70 ? 4 : 0; // terminates before tip

      // Generate dynamic SVG path for the cross section
      const pathData = isRight
        ? `M 100,20 L ${100 + spineWidth},20 Q ${100 + spineWidth * 0.7},120 100,180 Q ${100 - urasukiDepth},100 100,20 Z`
        : `M 100,20 L ${100 - spineWidth},20 Q ${100 - spineWidth * 0.7},120 100,180 Q ${100 + urasukiDepth},100 100,20 Z`;

      this.svg.innerHTML = `
        <defs>
          <linearGradient id="metalGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#4a5568"/>
            <stop offset="50%" stop-color="#e2e8f0"/>
            <stop offset="100%" stop-color="#2d3748"/>
          </linearGradient>
        </defs>
        <!-- Center reference vertical axis -->
        <line x1="100" y1="10" x2="100" y2="190" stroke="#718096" stroke-dasharray="3,3" stroke-width="1"/>
        <!-- Steel Cross Section -->
        <path d="${pathData}" fill="url(#metalGrad)" stroke="#cbd5e0" stroke-width="1.5"/>
        <!-- Micro-apex callout -->
        <circle cx="100" cy="180" r="3" fill="#d43f2a"/>
        <text x="112" y="184" fill="#d43f2a" font-family="'JetBrains Mono', monospace" font-size="10">0.10mm Apex Land</text>
        <!-- Urasuki callout -->
        <text x="30" y="100" fill="#4e74be" font-family="'JetBrains Mono', monospace" font-size="9">Ura Land</text>
        <line x1="68" y1="97" x2="98" y2="97" stroke="#4e74be" stroke-width="1"/>
      `;
    }
  }

  // --------------------------------------------------------------------------
  // 6. TWO-MODE ERGONOMIC SIMULATOR
  // --------------------------------------------------------------------------
  class ErgonomicsSimulator {
    constructor() {
      this.precisionCard = document.getElementById('ergoModePrecision');
      this.powerCard = document.getElementById('ergoModePower');
      this.toggleBtns = document.querySelectorAll('.ergo-toggle-btn');

      this.toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const mode = btn.dataset.mode;
          this.setMode(mode);
        });
      });
    }

    setMode(mode) {
      SHINOBI_STATE.ergoMode = mode;
      playTactileClick('lock');

      this.toggleBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
      });

      if (this.precisionCard && this.powerCard) {
        this.precisionCard.classList.toggle('active', mode === 'precision');
        this.powerCard.classList.toggle('active', mode === 'power');
      }

      const visual = document.getElementById('ergoGripVisual');
      if (visual) {
        if (mode === 'precision') {
          visual.innerHTML = `
            <div style="font-family: var(--font-mono); font-size: 0.8rem; text-align: center; color: var(--accent-vermilion);">
              [ SKELETON 4.2mm PINCH SADDLE ]<br>
              <span style="color: var(--text-tertiary); font-size: 0.72rem;">Direct Tactile Bone/Fiber Resonance</span>
            </div>
          `;
        } else {
          visual.innerHTML = `
            <div style="font-family: var(--font-mono); font-size: 0.8rem; text-align: center; color: var(--accent-success);">
              [ KAGE-SAYA™ 13.5 × 20mm OVAL PALM SWELL ]<br>
              <span style="color: var(--text-tertiary); font-size: 0.72rem;">40% Muscular Fatigue Reduction (NIOSH Standards)</span>
            </div>
          `;
        }
      }
    }
  }

  // --------------------------------------------------------------------------
  // 7. IKEJIME & SHINKEIJIME PROTOCOL GUIDE
  // --------------------------------------------------------------------------
  class IkejimeProtocolEngine {
    constructor() {
      this.speciesBtns = document.querySelectorAll('.species-select-btn');
      this.speciesBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          this.speciesBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const species = btn.dataset.species;
          SHINOBI_STATE.ikejimeSpecies = species;
          playTactileClick('click');
          this.updateSpecies(species);
        });
      });
    }

    updateSpecies(sp) {
      const guideData = {
        trout: {
          wire: 'SHINKEI S-50 (0.8mm Nitinol)',
          entry: 'Slightly behind the eye socket, 45° angle towards spine',
          depth: '18–24 mm spike depth into hindbrain',
          drainage: 'Submerge in 2°C alpine stream water for 3 minutes'
        },
        bass: {
          wire: 'SHINKEI S-50 (0.8mm Nitinol)',
          entry: 'Center crown depression above lateral line origin',
          depth: '22–28 mm spike depth into cranial cavity',
          drainage: 'Gill arch severance + iced brine bath'
        },
        salmon: {
          wire: 'SHINKEI L-80 (1.2mm Heavy Nitinol)',
          entry: 'Diamond soft locus between dorsal ridges, 35° forward',
          depth: '34 mm full locking spike penetration',
          drainage: 'Full caudal severance & continuous iced flush'
        }
      };

      const data = guideData[sp] || guideData.trout;
      const wireEl = document.getElementById('ikejimeWireSpec');
      const entryEl = document.getElementById('ikejimeEntrySpec');
      const depthEl = document.getElementById('ikejimeDepthSpec');
      const drainEl = document.getElementById('ikejimeDrainSpec');

      if (wireEl) wireEl.textContent = data.wire;
      if (entryEl) entryEl.textContent = data.entry;
      if (depthEl) depthEl.textContent = data.depth;
      if (drainEl) drainEl.textContent = data.drainage;
    }
  }

  // --------------------------------------------------------------------------
  // 8. FOUR-STAGE UNBOXING ATELIER
  // --------------------------------------------------------------------------
  class UnboxingEngine {
    constructor() {
      this.stageBtns = document.querySelectorAll('.stage-tab-btn');
      this.stageDisplay = document.getElementById('unboxingStageFrame');

      this.stageBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          this.stageBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const stage = parseInt(btn.dataset.stage, 10);
          SHINOBI_STATE.unboxingStage = stage;
          playTactileClick('click');
          this.renderStage(stage);
        });
      });
    }

    renderStage(st) {
      if (!this.stageDisplay) return;

      const stageInfo = [
        {
          title: 'Stage I: Echizen Washi Outer Envelope',
          details: 'Hand-made Japanese mulberry paper with cinnabar vermilion seal and calligraphic inspection stamp. Zero plastic wrappers.',
          glyph: '包'
        },
        {
          title: 'Stage II: Paulownia (Kiri) Wood Vault',
          details: 'Precision sliding Kiri box naturally regulating humidity. Inset with solid Kurogaki black persimmon seal block.',
          glyph: '桐'
        },
        {
          title: 'Stage III: Complete 12-Piece Ecosystem',
          details: 'Grade 5 Ti Handle, 3 Blade modules (MIZU, KUMIKO, NATA), KAGE-SAYA sheath, RAILSTONE diamond cassette, 2 Nitinol wires, and tweezers.',
          glyph: '全'
        },
        {
          title: 'Stage IV: Dual Working Configurations',
          details: 'Instant deployment into 24.06g Backcountry River Pack or 17.52g Kumiko Joinery Pocket Carry.',
          glyph: '行'
        }
      ];

      const cur = stageInfo[st - 1];
      this.stageDisplay.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; text-align: center; gap: 16px;">
          <div style="font-family: var(--font-kanji); font-size: 3.5rem; color: var(--accent-vermilion); line-height: 1;">${cur.glyph}</div>
          <h3 style="font-size: 1.3rem;">${cur.title}</h3>
          <p style="max-width: 420px; font-size: 0.9rem; color: var(--text-secondary);">${cur.details}</p>
        </div>
      `;
    }
  }

  // --------------------------------------------------------------------------
  // 9. PROTOTYPE ALLOCATION & CONSULTATION FORM
  // --------------------------------------------------------------------------
  class ConsultationEngine {
    constructor() {
      this.form = document.getElementById('consultationForm');
      this.statusBox = document.getElementById('formStatusMessage');
      if (!this.form) return;

      this.form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleSubmit();
      });
    }

    handleSubmit() {
      const name = document.getElementById('consultName')?.value.trim();
      const email = document.getElementById('consultEmail')?.value.trim();
      const config = document.getElementById('consultConfig')?.value;
      const hand = document.getElementById('consultHand')?.value;
      const batch = document.getElementById('consultBatch')?.value;
      const notes = document.getElementById('consultNotes')?.value.trim();

      if (!name || !email) {
        alert('Please provide your name and verified contact email.');
        return;
      }

      // Generate verifiable client-side specification dossier
      const dossier = {
        project: 'SHINOBI//82 KAGE (Zen-Wu Toolworks Collaboration Candidate)',
        date: new Date().toISOString(),
        candidate: { name, email },
        specifications: {
          configuration: config,
          handedness: hand,
          batchCommitment: batch,
          notes: notes || 'Standard evaluation prototype target'
        },
        metallurgy: {
          bladeSteel: 'MagnaMax (62.5–63.0 HRC Cryo Quench)',
          structure: 'Grade 5 Titanium (Ti-6Al-4V) Monocoque',
          lockingMechanism: 'Kusabi-Lock™ Tapered Wedge'
        }
      };

      // Create downloadable JSON Dossier
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(dossier, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `SHINOBI_82_KAGE_SPEC_${name.replace(/\s+/g, '_')}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();

      // Show honest success feedback
      if (this.statusBox) {
        this.statusBox.className = 'form-status-message success';
        this.statusBox.innerHTML = `
          <strong>Specification Dossier Generated Successfully.</strong><br>
          Your exact technical package has been downloaded. To submit this formal proposal directly to <strong>Luke Lyu</strong> at Zen-Wu Toolworks, you may forward your downloaded dossier or email him at <a href="mailto:luke@zenwutoolworks.com?subject=SHINOBI//82%20KAGE%20Collaboration%20Proposal%20-%20${encodeURIComponent(name)}" style="color: var(--accent-vermilion); font-weight: 600;">luke@zenwutoolworks.com</a>.
        `;
      }

      playTactileClick('lock');
    }
  }

  // --------------------------------------------------------------------------
  // 10. GLOBAL INITIALIZATION & EVENT WIRING
  // --------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Initialization
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const nextTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', nextTheme);
        localStorage.setItem('shinobi_theme', nextTheme);
        SHINOBI_STATE.theme = nextTheme;
        playTactileClick('click');
      });
    }

    // Audio Toggle Initialization
    const audioBtn = document.getElementById('audioToggleBtn');
    if (audioBtn) {
      audioBtn.addEventListener('click', () => {
        SHINOBI_STATE.audioEnabled = !SHINOBI_STATE.audioEnabled;
        audioBtn.classList.toggle('active', SHINOBI_STATE.audioEnabled);
        if (SHINOBI_STATE.audioEnabled) {
          playTactileClick('lock');
        }
      });
    }

    // Handedness Selector
    const handBtns = document.querySelectorAll('.handedness-toggle-btn');
    handBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        handBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        SHINOBI_STATE.handedness = btn.dataset.hand;
        playTactileClick('click');
        const inspector = new CrossSectionInspector();
      });
    });

    // Blade Family Selector
    const bladeCards = document.querySelectorAll('.blade-card');
    bladeCards.forEach(card => {
      card.addEventListener('click', () => {
        bladeCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        SHINOBI_STATE.selectedBlade = card.dataset.blade;
        playTactileClick('lock');
      });
    });

    // Layer Viewport Selector
    const layerBtns = document.querySelectorAll('.layer-btn');
    layerBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        layerBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        SHINOBI_STATE.activeLayer = btn.dataset.layer;
        playTactileClick('click');
      });
    });

    // Mobile Navigation Overlay
    const mobileToggle = document.getElementById('mobileMenuToggle');
    const mobileOverlay = document.getElementById('mobileNavOverlay');
    const mobileClose = document.getElementById('mobileNavClose');
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');

    if (mobileToggle && mobileOverlay) {
      mobileToggle.addEventListener('click', () => {
        mobileOverlay.classList.toggle('open');
      });
      if (mobileClose) {
        mobileClose.addEventListener('click', () => {
          mobileOverlay.classList.remove('open');
        });
      }
      mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
          mobileOverlay.classList.remove('open');
        });
      });
    }

    // Initialize All Subsystems
    window.bladeCanvas = new BladeCanvasEngine('bladeCanvas');
    window.massCalc = new MassCalculatorEngine();
    window.crossSection = new CrossSectionInspector();
    window.ergoSim = new ErgonomicsSimulator();
    window.ikejimeEngine = new IkejimeProtocolEngine();
    window.unboxingEngine = new UnboxingEngine();
    window.consultEngine = new ConsultationEngine();
  });

})();
