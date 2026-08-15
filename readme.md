# SHINOBI // 82 KAGE — Sovereign SiteForge v3.0 Architecture

**The Sub-Ounce JDM Cutting Instrument & Joinery System**  
*Proposed Collaboration Candidate for Luke Lyu / Zen-Wu Toolworks*

---

## 1. Executive Summary

SHINOBI//82 KAGE is a polymorphic, cinematic, award-grade digital experience and technical specification for a sub-ounce modular cutting system. It synthesizes traditional Japanese blade geometry (*Shinogi-zukuri*, *Kataba*, *Hamaguri* convex bevel, and *Urasuki* hollow) with hyper-modern aerospace metallurgy (MagnaMax™ at 62.5–63.0 HRC, Grade 5 Ti-6Al-4V monocoque, and zero-screw Kusabi-Lock™ architecture).

### Core Performance Metrics
- **Bare Knife Mass:** 18.40 g (0.649 oz) — Solid CAD geometry verified
- **Backcountry River System:** 24.06 g (0.849 oz) — Knife + Honoki/Urushi Saya + S-50 Nitinol Wire + Diamond Tag
- **Full Field System:** 26.55 g (0.936 oz) — Under the absolute 1.00 oz ceiling
- **Steel Metallurgy:** MagnaMax™ Stainless PM (62.5–63.0 HRC Cryogenic Plate Quench)
- **Reference Back Tolerance:** < 0.02 mm dead-flat coplanar lands for Kumiko woodworking layout
- **Synthetic Plastic Content:** 0.000% (Certified Zero Plastic)

---

## 2. The Three Modular Blade Architectures

1. **MIZU-82 (82 mm):** The River & Everyday Field Flagship. 60/40 Asymmetric Hamaguri convex bevel (12°/14° apex, 15°/17° heel) with distal flexibility for tracing trout ribs, salmon frames, and big-game seam deboning.
2. **KUMIKO-42 (42 mm):** The Scribing & Joinery Kogatana. 100% dead-flat reference back (<0.02 mm) with a 15.0° single flat bevel for marking dovetails and fitting precision Kumiko lattice work.
3. **NATA-60 (60 mm):** The Camp Chisel. Heavy 2.2 mm spine with a 24.0° single flat chisel bevel for controlled push-cuts, camp notching, and wood paring.

---

## 3. Subsystem Innovations

- **Kusabi-Lock™ Monocoque:** A precision Wire-EDM titanium tapered wedge enabling instant, zero-screw, zero-tool blade swaps without stripping or loosening.
- **Two-Mode Ergonomics:** Bare 4.2 mm skeleton handle with pinch saddle for tactile bone tracing, converting into a 13.5 × 20 mm oval palm swell via the snapped KAGE-SAYA™ sheath (40% grip fatigue reduction).
- **Integrated Ikejime & Shinkeijime Protocol:** 34 mm locking brain spike housed in the KAGE-TAG™ diamond sharpening plate, paired with S-50 (0.8 mm) and L-80 (1.2 mm) superelastic shape-memory Nitinol spinal wires.
- **RAILSTONE Field Sharpening Cassette:** Reversible 600/1200 grit monocrystalline diamond plate with integrated 12°, 14°, 15°, and 17° sharpening index guides and a 1 μm deburring diamond strop.
- **Zero-Plastic Material Ledger:** Grade 5 Titanium (Ti-6Al-4V), Natural Kurogaki (black persimmon) inlays, Honoki magnolia wood, cured natural Wajima Urushi tree lacquer, and Nitinol alloy.

---

## 4. Frontend Engineering & Performance Standards

- **Design System:** Native CSS OKLCH color space tokens, fluid typographic hierarchy via `clamp()`, and responsive grid composition.
- **Interactive Engines:**
  - `BladeCanvasEngine`: High-DPI interactive canvas with specular light reflection across the *Shinogi* line, handedness inversion (Right-Hand 60/40 vs Left-Hand Mirrored), and multi-layer structural overlays (Assembly, Load Paths, Dovetail Seam, Ura Map).
  - `MassCalculatorEngine`: Wolfram-calibrated solid CAD mass engine supporting 5 mission presets and granular 13-component toggle with live gram/ounce recalculation and center-of-gravity tracking.
  - `CrossSectionInspector`: Live continuous SVG caliper inspector from 0 mm (heel) to 82 mm (kissaki).
  - `ErgonomicsSimulator`: Interactive biomechanical mode switch (Precision vs Power).
  - `IkejimeProtocolEngine`: Species-specific humane dispatch workflow (Alpine Trout, Smallmouth Bass, Niagara Chinook Salmon).
  - `UnboxingEngine`: 4-stage visual unboxing atelier (Echizen Washi, Paulownia Kiri Vault, 12-Piece System, Field Packs).
  - `ConsultationEngine`: Client-side verifiable specification dossier generator (JSON export + direct email integration).
- **Accessibility:** WCAG 2.2 Level AA compliant, full keyboard accessibility, visible focus states, ARIA landmarks, skip links, and `prefers-reduced-motion` fallbacks.

---

## 5. Development & Deployment

To run locally:
```bash
python3 -m http.server 8080
```
Then visit `http://localhost:8080`.

Netlify deployment is configured at the root directory via `netlify.toml`.
