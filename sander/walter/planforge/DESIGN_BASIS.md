# WALTER Design Basis — WOODWRIGHT PLANFORGE v1.0

**Release state:** FABRICATION-READY WITH CONDITIONS
**Risk class:** R3
**Project:** WPF-WALTER-16-C · kernel 1.2.0 · Rev C
**Units:** inch controlling; millimetre at CAD export only
**Layout:** D1 base top Z0; D2 drum axis Z 13.50 Y 18.00; D3 idle jack zero; D4 Acme nuts clocked

## Verdict
This is a shop-built 16-inch closed-frame drum thickness sander. A competent craftsperson can review, prototype, and — after the listed conditions — build it. It is **not** a PE stamp, not UL listed, not a ShopNotes #86 reprint, and not an unconditional FABRICATION-READY machine.

## Conditions (stop-work until closed)
- Qualified electrician sizes overload heaters to motor FLA and lands 115 V 20 A, grounding, and the magnetic starter [P]
- First-run commissioning is staged: collector on, hood on, no workpiece, then poplar 0.010″ [T]
- Verify every catalog number on the live McMaster / supplier page before purchase [S]
- True the drum OD to 5.000 ±0.010 after glue; do not run an unbalanced blank [T]
- Track the PVC conveyor empty 60 s then loaded before any oak [T]
- E-stop blink test: restore power — drum must not auto-restart [T]
- Do not treat W-sheets, the HTML guidebook, or the Build-app viz as a scaled fabrication drawing — kernel inches control
- Not a permit drawing, not a UL listing, not a substitute for machine-guarding review

## Risk triggers
- Powered abrasive drum ~1089 RPM / ~1.4 kSFM with stored rotational energy
- Ingoing nip at drum-to-work and conveyor rollers
- 115 V motor circuit, magnetic starter, E-stop, 24 V feed — electrical [P]
- Kickback / ejection of short stock
- Combustible fine dust; hood and collector are part of the safeguard
- Belt/pulley pinch outboard of the drive wall
- Homemade machine — not UL listed, not OSHA-certified, not PE-stamped

## Controlling geometry [G]/[D]
- envelope 22.00 × 36.00 × 20.00 in benchtop [G]
- capacity 16.00 in wide × 0.06–4.00 in thick [G]
- drum Ø 5.00 × 16.00 face after true [G/T]
- drum axis D2: Z 13.50, Y 18.00 [G]
- RPM = 1725 × 3.00 / 4.75 = 1089.47 [D]
- SFM = π × 5.00 × rpm / 12 = 1426.1 [D]
- feed at 30 rpm roller = 15.71 FPM [D]
- crown 0.030 in barrel both rollers [G]
- Acme ¾-6 dual, HTD-timed, 4.50 in travel [G]

## Professional review
Licensed/qualified electrician for 115 V. Competent machinery review of guards and first-run. This package is not PE-stamped and is not FABRICATION-READY (unconditional).

## Lineage (observation vs inference)
- Observed [G]: Ron Walters published a ShopNotes-derived drum sander on woodgears.ca and walked the same machine on YouTube W-5Sj6kBVic.
- Observed [G]: dedicated motor, flange bearings, Velcro wrap, dust hood worked; conveyor tracking, MDF drum cracks, Formica platen, gravity belt slack, shim-stock parallelism failed in public.
- Inference: redesign those failure modes. Do not redraw copyrighted magazine art.
