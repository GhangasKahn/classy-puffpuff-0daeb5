/* AUTO-GENERATED from cad/walter_ds16.py — do not edit */
window.WALTER_DATA = {
  "meta": {
    "name": "WALTER",
    "code": "DS-16",
    "subtitle": "Dedicated drum thickness sander \u00b7 15.5\u2033 \u00b7 geometry Rev B \u00b7 fab B.2",
    "revision": "B",
    "fabricationRev": "B.2",
    "capacity": 15.5,
    "drumOd": 5.0,
    "drumRpm": 1035.0,
    "motorHp": 0.5,
    "surfaceFpm": 1355.0,
    "parallelTol": 0.003,
    "lineage": "ShopNotes 86 \u2192 Ron Walters \u2192 Rev A solid table \u2192 Rev B geometry"
  },
  "modernizations": [
    "Dual \u00bd-10 Acme table screws, chain-coupled \u2014 coarse lift stays coplanar",
    "Left screw uncouples for taper; dog stop returns to parallel home",
    "UHMW ways let into side rebates \u2014 table cannot rack, and still fits",
    "Housed stretchers (\u00bc\u2033 dados) + through-screws for racking stiffness",
    "Stack-drill side panels as a pair; floating idler bearing (axial pad, not YZ slots)",
    "Torsion-box table + phenolic / tooling-plate wear face",
    "Spring hold-down rollers infeed + outfeed \u2014 kills snipe and chatter",
    "Full-width truing sled; re-clock after paper wrap to \u00b10.003\u2033",
    "Dial-indicator pad on drive side; 0.001\u2033 pass schedule",
    "Optional \u215b\u2033 slow oscillation (gear motor) to erase spiral tracks",
    "Pack-bore disc jig + static balance of end discs"
  ],
  "parts": [
    {
      "id": "sides",
      "fabIds": [
        "P-001L",
        "P-001R"
      ],
      "group": "frame",
      "label": "Side panels P-001L/R",
      "detail": "0.75\u2033 BB \u00b7 stack-drill then inner-face dado/rebate",
      "color": "#c4a574",
      "sheet": "P001L_side_drive.svg"
    },
    {
      "id": "ways",
      "fabIds": [
        "P-007"
      ],
      "group": "frame",
      "label": "UHMW ways P-007",
      "detail": "Rebate 0.520\u2033 \u00b7 project 0.230\u2033 \u00b7 J-002",
      "color": "#d9dcde",
      "sheet": "P007_uhmw_way.svg"
    },
    {
      "id": "base",
      "fabIds": [
        "P-002",
        "P-003"
      ],
      "group": "frame",
      "label": "Base + stretchers",
      "detail": "P-003 housed 17\u2033 \u00b7 J-001",
      "color": "#a89070",
      "sheet": "A01_frame.svg"
    },
    {
      "id": "drum",
      "fabIds": [
        "P-008",
        "P-009"
      ],
      "group": "drum",
      "label": "Sanding drum",
      "detail": "\u23005\u2033 \u00d7 15.75\u2033 \u00b7 pack-bored \u00b7 P-008/P-009",
      "color": "#b8a990",
      "sheet": "A02_drum.svg"
    },
    {
      "id": "shaft",
      "fabIds": [
        "P-010",
        "H-001",
        "H-002"
      ],
      "group": "drum",
      "label": "Shaft + bearings",
      "detail": "P-010 \u00b7 J-006 fixed \u00b7 J-007 float",
      "color": "#8a9098",
      "sheet": "P010_shaft.svg"
    },
    {
      "id": "table",
      "fabIds": [
        "P-004",
        "P-005",
        "P-006"
      ],
      "group": "table",
      "label": "Torsion-box table",
      "detail": "P-004/P-005/P-006 \u00b7 J-003/J-004",
      "color": "#cfd3d5",
      "sheet": "A03_table.svg"
    },
    {
      "id": "elev",
      "fabIds": [
        "P-016",
        "H-007",
        "H-008"
      ],
      "group": "table",
      "label": "Dual Acme lift",
      "detail": "H-007/H-008 \u00b7 left clutch \u00b7 home dog",
      "color": "#6e7578",
      "sheet": "P016_nut_block.svg"
    },
    {
      "id": "rollers",
      "fabIds": [
        "P-014",
        "H-009"
      ],
      "group": "table",
      "label": "Hold-down rollers",
      "detail": "P-014 \u00b7 0.030\u2033 below drum",
      "color": "#5a6068",
      "sheet": "A05_holddowns.svg"
    },
    {
      "id": "motor",
      "fabIds": [
        "P-012",
        "H-006"
      ],
      "group": "drive",
      "label": "Motor + pulleys",
      "detail": "0.5 HP \u00b7 coplanar 3\u2033/5\u2033",
      "color": "#4a5058",
      "sheet": "A04_drive.svg"
    },
    {
      "id": "hood",
      "fabIds": [
        "P-011"
      ],
      "group": "hood",
      "label": "Dust hood",
      "detail": "P-011 kerf-bent \u00b7 4\u2033 port",
      "color": "#9aa8a0",
      "sheet": "P011_hood.svg"
    }
  ],
  "cutList": [
    {
      "qty": 1,
      "size": "30\" \u00d7 22\" \u00d7 0.75\"",
      "sizeMm": "762 \u00d7 559 \u00d7 19 mm",
      "stock": "Baltic birch plywood",
      "use": "P-001L Side panel, drive (left) \u2014 Stack-drill wit",
      "partId": "P-001L"
    },
    {
      "qty": 1,
      "size": "30\" \u00d7 22\" \u00d7 0.75\"",
      "sizeMm": "762 \u00d7 559 \u00d7 19 mm",
      "stock": "Baltic birch plywood",
      "use": "P-001R Side panel, idler (right) \u2014 Identical hole",
      "partId": "P-001R"
    },
    {
      "qty": 1,
      "size": "18\" \u00d7 22\" \u00d7 0.75\"",
      "sizeMm": "457 \u00d7 559 \u00d7 19 mm",
      "stock": "Baltic birch plywood",
      "use": "P-002 Base deck \u2014 Width follows ply_actual so 18",
      "partId": "P-002"
    },
    {
      "qty": 3,
      "size": "17\" \u00d7 4\" \u00d7 0.75\"",
      "sizeMm": "432 \u00d7 102 \u00d7 19 mm",
      "stock": "Baltic birch plywood",
      "use": "P-003 Stretcher \u2014 Do not use stretchers as the t",
      "partId": "P-003"
    },
    {
      "qty": 2,
      "size": "16\" \u00d7 22\" \u00d7 0.75\"",
      "sizeMm": "406 \u00d7 559 \u00d7 19 mm",
      "stock": "Baltic birch plywood",
      "use": "P-004 Table torsion-box skin",
      "partId": "P-004"
    },
    {
      "qty": 8,
      "size": "15.5\" \u00d7 1.25\" \u00d7 0.5\"",
      "sizeMm": "394 \u00d7 32 \u00d7 13 mm",
      "stock": "Baltic birch or MDF",
      "use": "P-005 Torsion-box ribs \u2014 Qty is typical for 4\u2033 o",
      "partId": "P-005"
    },
    {
      "qty": 1,
      "size": "16\" \u00d7 22\" \u00d7 0.5\"",
      "sizeMm": "406 \u00d7 559 \u00d7 13 mm",
      "stock": "Phenolic sheet or MIC-6 / cast tooling plate",
      "use": "P-006 Table wear face \u2014 This is the inspection p",
      "partId": "P-006"
    },
    {
      "qty": 2,
      "size": "22\" \u00d7 0.75\" \u00d7 0.75\"",
      "sizeMm": "559 \u00d7 19 \u00d7 19 mm",
      "stock": "UHMW-PE",
      "use": "P-007 UHMW way \u2014 Projects 0.230\u2033 past inner face",
      "partId": "P-007"
    },
    {
      "qty": 19,
      "size": "5.125\" \u00d7 5.125\" \u00d7 0.75\"",
      "sizeMm": "130 \u00d7 130 \u00d7 19 mm",
      "stock": "MDF",
      "use": "P-008 Drum disc, core",
      "partId": "P-008"
    },
    {
      "qty": 2,
      "size": "5.125\" \u00d7 5.125\" \u00d7 0.75\"",
      "sizeMm": "130 \u00d7 130 \u00d7 19 mm",
      "stock": "Baltic birch plywood",
      "use": "P-009 Drum disc, end \u2014 BB ends resist crushing a",
      "partId": "P-009"
    },
    {
      "qty": 1,
      "size": "22.5\" \u00d7 0.75\" \u00d7 0.75\"",
      "sizeMm": "572 \u00d7 19 \u00d7 19 mm",
      "stock": "Precision-ground CRS / TG&P",
      "use": "P-010 Drum shaft \u2014 Precision-ground CRS or TG&P,",
      "partId": "P-010"
    },
    {
      "qty": 1,
      "size": "18\" \u00d7 12\" \u00d7 0.25\"",
      "sizeMm": "457 \u00d7 305 \u00d7 6 mm",
      "stock": "Birch or pine plywood",
      "use": "P-011 Dust hood blank \u2014 Kerf-bent \u00bc\u2033 pine/birch ",
      "partId": "P-011"
    },
    {
      "qty": 1,
      "size": "12\" \u00d7 8\" \u00d7 0.75\"",
      "sizeMm": "305 \u00d7 203 \u00d7 19 mm",
      "stock": "Baltic birch plywood",
      "use": "P-012 Motor pivot cradle",
      "partId": "P-012"
    },
    {
      "qty": 1,
      "size": "16\" \u00d7 8\" \u00d7 0.75\"",
      "sizeMm": "406 \u00d7 203 \u00d7 19 mm",
      "stock": "MDF or Baltic birch",
      "use": "P-013 Full-width truing sled \u2014 As wide as the dr",
      "partId": "P-013"
    },
    {
      "qty": 2,
      "size": "18\" \u00d7 3\" \u00d7 0.75\"",
      "sizeMm": "457 \u00d7 76 \u00d7 19 mm",
      "stock": "Hardwood or 1\u00bd\u2033 aluminum angle",
      "use": "P-014 Hold-down roller yoke \u2014 Board feet net 0.5",
      "partId": "P-014"
    },
    {
      "qty": 1,
      "size": "12\" \u00d7 12\" \u00d7 0.75\"",
      "sizeMm": "305 \u00d7 305 \u00d7 19 mm",
      "stock": "MDF",
      "use": "P-015 Disc pack-bore jig",
      "partId": "P-015"
    },
    {
      "qty": 2,
      "size": "2.5\" \u00d7 2\" \u00d7 1.5\"",
      "sizeMm": "64 \u00d7 51 \u00d7 38 mm",
      "stock": "Hardwood or aluminum + bronze nut",
      "use": "P-016 Acme bronze nut block",
      "partId": "P-016"
    }
  ],
  "hardware": [
    {
      "item": "4-bolt flange bearing, \u00be\u2033 bore, sealed, FIXED (drive)",
      "qty": "1",
      "id": "H-001"
    },
    {
      "item": "4-bolt flange bearing, \u00be\u2033 bore, sealed, FLOATING (idler)",
      "qty": "1",
      "id": "H-002"
    },
    {
      "item": "3\u2033 motor 4L pulley",
      "qty": "1",
      "id": "H-003"
    },
    {
      "item": "5\u2033 drum 4L pulley",
      "qty": "1",
      "id": "H-004"
    },
    {
      "item": "4L / A-section V-belt (size to center distance)",
      "qty": "1",
      "id": "H-005"
    },
    {
      "item": "0.5 HP 1725 RPM TEFC motor, 115 V",
      "qty": "1",
      "id": "H-006"
    },
    {
      "item": "\u00bd\u2033-10 Acme rod \u00d7 12\u2033 + bronze nut + flange",
      "qty": "2",
      "id": "H-007"
    },
    {
      "item": "#25 chain + \u00bd\u2033-bore sprockets + master link + left clutch/dog",
      "qty": "1",
      "id": "H-008"
    },
    {
      "item": "Rubber roller \u23001.25\" \u00d7 ~15.75\"",
      "qty": "2",
      "id": "H-009"
    },
    {
      "item": "Dial indicator 0.001\u2033 + mag base",
      "qty": "1",
      "id": "H-021"
    },
    {
      "item": "Optional 60\u201390 RPM gearmotor + scotch yoke oscillator",
      "qty": "1",
      "id": "H-025"
    }
  ],
  "assembly": [
    {
      "id": "a1",
      "phase": "frame",
      "title": "Template & stack-drill sides",
      "body": "Clamp P-001L/R face-to-face. Drill bearing CL at Y 11\u2033 / Z 18.5\u2033, Acme holes, indicator pad as one stack (S-008)."
    },
    {
      "id": "a2",
      "phase": "frame",
      "title": "Dados, way rebates, box + UHMW",
      "body": "Split the pair. Dado J-001 (0.25\u2033) and rebate J-002 (0.520\u2033) on inner faces only. Glue P-003, square diagonals, bond P-007."
    },
    {
      "id": "a3",
      "phase": "drum",
      "title": "Pack-bore discs & laminate drum",
      "body": "Bandsaw P-008/P-009 oversize. Stack in P-015; ream \u2300\u00be\u2033 as a pack (J-005). Key, 1 mm MDF relief, static-balance P-009."
    },
    {
      "id": "a4",
      "phase": "drum",
      "title": "Fixed drive bearing, floating idler",
      "body": "H-001 locked on P-001L (J-006). H-002 on axial-float slots on P-001R (J-007)."
    },
    {
      "id": "a5",
      "phase": "drive",
      "title": "Motor cradle, coplanar pulleys, lock",
      "body": "Straightedge across H-003/H-004. Gravity tension, lock P-012 (J-008)."
    },
    {
      "id": "a6",
      "phase": "table",
      "title": "Torsion-box table + wear face",
      "body": "P-004 + P-005 @ 4\u2033 o.c., glue. Flatten. Bond P-006. Diagonals \u2264 0.004\u2033."
    },
    {
      "id": "a7",
      "phase": "table",
      "title": "Dual Acme lift + chain couple",
      "body": "P-016 + H-007. H-008 chain. Left clutch + home dog. Table must rise in the ways without twist."
    },
    {
      "id": "a8",
      "phase": "table",
      "title": "Hold-down roller yokes",
      "body": "P-014 + H-009. Set 0.030\u2033 below drum OD, paper on. Too much spring = snipe."
    },
    {
      "id": "a9",
      "phase": "hood",
      "title": "Kerf-bend dust hood",
      "body": "P-011 kerf, wet, glue, fill. H-019 4\u2033 port. Clear oscillator stroke if fitted."
    },
    {
      "id": "a10",
      "phase": "wrap",
      "title": "True drum on full-width sled",
      "body": "P-013 abrasive face-up on the ways. TIR \u2264 0.002\u2033. Then H-022 Velcro + spiral paper."
    },
    {
      "id": "a11",
      "phase": "tune",
      "title": "Indicator clock A/B \u2014 parallel home",
      "body": "Paper on. |A\u2212B| \u2264 0.003\u2033. Lock home dog. Record the reading."
    },
    {
      "id": "a12",
      "phase": "tune",
      "title": "Test panel + pass schedule",
      "body": "80 / 120 / 180. Caliper four corners. If scatter > 0.003\u2033, re-clock. Finish at 0.001\u2033."
    }
  ],
  "phases": [
    {
      "id": "frame",
      "label": "01 Frame"
    },
    {
      "id": "drum",
      "label": "02 Drum"
    },
    {
      "id": "drive",
      "label": "03 Drive"
    },
    {
      "id": "table",
      "label": "04 Table"
    },
    {
      "id": "hood",
      "label": "05 Hood"
    },
    {
      "id": "wrap",
      "label": "06 Wrap"
    },
    {
      "id": "tune",
      "label": "07 Tune"
    }
  ],
  "quality": [
    {
      "check": "Table flatness",
      "spec": "\u2264 0.004\u2033 on both diagonals",
      "tool": "Straightedge + feelers on wear face"
    },
    {
      "check": "Drum TIR (paper off)",
      "spec": "\u2264 0.002\u2033 TIR",
      "tool": "Dial indicator on drum OD, mid-span"
    },
    {
      "check": "Drum \u2225 table (paper on)",
      "spec": "|A\u2212B| \u2264 0.003\u2033 over 15.5\u2033",
      "tool": "Indicator at A (drive) and B (idler)"
    },
    {
      "check": "Way coplanar",
      "spec": "No twist; table slides without bind",
      "tool": "Winding sticks / indicator on both UHMW"
    },
    {
      "check": "Pulley coplanar",
      "spec": "Faces flush; belt tracks center",
      "tool": "Straightedge across both pulley faces"
    },
    {
      "check": "Hold-down set",
      "spec": "Rollers 0.030\u2033 below drum OD",
      "tool": "Feeler under roller vs drum (paper on)"
    },
    {
      "check": "Thickness scatter",
      "spec": "\u2264 0.003\u2033 after finish pass",
      "tool": "Caliper 4 corners of test panel"
    }
  ],
  "calibration": [
    {
      "id": "c1",
      "title": "Disconnect power",
      "body": "Unplug. Hood off. Paper off for TIR; paper on for A/B parallel."
    },
    {
      "id": "c2",
      "title": "Seat the table in the ways",
      "body": "Raise/lower through full travel. No bind, no rock. Winding sticks on wear face \u2014 no twist."
    },
    {
      "id": "c3",
      "title": "Drum TIR",
      "body": "Indicator on mid-span OD. Rotate by hand. If > 0.002\u2033, re-true on P-013 before wrapping."
    },
    {
      "id": "c4",
      "title": "Wrap & re-clock",
      "body": "Velcro then spiral paper. Paper is not uniform \u2014 A/B will change. This is the measurement that matters."
    },
    {
      "id": "c5",
      "title": "A/B parallel",
      "body": "Same indicator height, drive then idler. Uncouple left Acme; 1/10 turn \u2248 0.1000\u2033. Recouple. Set home dog."
    },
    {
      "id": "c6",
      "title": "Hold-down height",
      "body": "Feelers under each roller vs drum. 0.030\u2033 below. Leading snipe \u2192 ease outfeed spring; trailing \u2192 ease infeed."
    },
    {
      "id": "c7",
      "title": "Witness board",
      "body": "6\u2033 \u00d7 16\u2033 maple, 80 grit, one pass. Ridge at overlap = idler high/low. Caliper corners. Log in the Build app."
    },
    {
      "id": "c8",
      "title": "Taper mode (optional)",
      "body": "Uncouple left, drop idler a few thousandths, sand, then return to home dog \u2014 do not re-invent parallel each time."
    }
  ],
  "passes": [
    {
      "grit": "80",
      "depth": "0.008\u2033",
      "use": "Flatten / mill marks / glue"
    },
    {
      "grit": "120",
      "depth": "0.004\u2033",
      "use": "Thickness to +0.008\u2033 of final"
    },
    {
      "grit": "180",
      "depth": "0.001\u2033",
      "use": "Finish pass; optional 90\u00b0 cross"
    },
    {
      "grit": "220",
      "depth": "0.001\u2033",
      "use": "Veneer / figured maple \u2014 hold-downs on"
    }
  ],
  "safety": [
    "Hood ON is the primary guard \u2014 open only when stopped and unplugged.",
    "Hold-downs on. Hands never under the drum. ~12\u2033 min length or a sled.",
    "Small parts ride a longer sled (kickback risk).",
    "Light passes only. Back off if the motor bogs.",
    "Eye, hearing, respirator when truing MDF."
  ],
  "gallery": [
    {
      "src": "../plans/IDX_drawings.svg",
      "title": "Drawing index",
      "kind": "plan",
      "group": "index",
      "code": "IDX"
    },
    {
      "src": "../plans/D1_general.svg",
      "title": "D-1 General",
      "kind": "plan",
      "group": "overview",
      "code": "D-1"
    },
    {
      "src": "../plans/D2_frame.svg",
      "title": "D-2 Frame",
      "kind": "plan",
      "group": "overview",
      "code": "D-2"
    },
    {
      "src": "../plans/D3_drum.svg",
      "title": "D-3 Drum",
      "kind": "plan",
      "group": "overview",
      "code": "D-3"
    },
    {
      "src": "../plans/D4_drive.svg",
      "title": "D-4 Drive",
      "kind": "plan",
      "group": "overview",
      "code": "D-4"
    },
    {
      "src": "../plans/D5_hood.svg",
      "title": "D-5 Hood",
      "kind": "plan",
      "group": "overview",
      "code": "D-5"
    },
    {
      "src": "../plans/D6_cutlist.svg",
      "title": "D-6 Cut list",
      "kind": "plan",
      "group": "overview",
      "code": "D-6"
    },
    {
      "src": "../plans/D7_geometry.svg",
      "title": "D-7 Geometry",
      "kind": "plan",
      "group": "overview",
      "code": "D-7"
    },
    {
      "src": "../plans/D8_holddowns.svg",
      "title": "D-8 Hold-downs",
      "kind": "plan",
      "group": "overview",
      "code": "D-8"
    },
    {
      "src": "../plans/D9_model.svg",
      "title": "D-9 3D views",
      "kind": "plan",
      "group": "overview",
      "code": "D-9"
    },
    {
      "src": "../plans/D10_lumberyard.svg",
      "title": "D-10 Lumberyard",
      "kind": "plan",
      "group": "overview",
      "code": "D-10"
    },
    {
      "src": "../plans/D11_register.svg",
      "title": "D-11 Part register",
      "kind": "plan",
      "group": "overview",
      "code": "D-11"
    },
    {
      "src": "../plans/D12_joinery.svg",
      "title": "D-12 Joinery & QA",
      "kind": "plan",
      "group": "overview",
      "code": "D-12"
    },
    {
      "src": "../plans/P001L_side_drive.svg",
      "title": "P-001L Side, drive",
      "kind": "part",
      "group": "part",
      "code": "P-001L"
    },
    {
      "src": "../plans/P001R_side_idler.svg",
      "title": "P-001R Side, idler",
      "kind": "part",
      "group": "part",
      "code": "P-001R"
    },
    {
      "src": "../plans/P002_base.svg",
      "title": "P-002 Base deck",
      "kind": "part",
      "group": "part",
      "code": "P-002"
    },
    {
      "src": "../plans/P003_stretcher.svg",
      "title": "P-003 Stretcher",
      "kind": "part",
      "group": "part",
      "code": "P-003"
    },
    {
      "src": "../plans/P004_table_skin.svg",
      "title": "P-004 Table skin",
      "kind": "part",
      "group": "part",
      "code": "P-004"
    },
    {
      "src": "../plans/P005_table_ribs.svg",
      "title": "P-005 Table ribs",
      "kind": "part",
      "group": "part",
      "code": "P-005"
    },
    {
      "src": "../plans/P006_wear_face.svg",
      "title": "P-006 Wear face",
      "kind": "part",
      "group": "part",
      "code": "P-006"
    },
    {
      "src": "../plans/P007_uhmw_way.svg",
      "title": "P-007 UHMW way",
      "kind": "part",
      "group": "part",
      "code": "P-007"
    },
    {
      "src": "../plans/P008_disc_core.svg",
      "title": "P-008 Disc, core",
      "kind": "part",
      "group": "part",
      "code": "P-008"
    },
    {
      "src": "../plans/P009_disc_end.svg",
      "title": "P-009 Disc, end",
      "kind": "part",
      "group": "part",
      "code": "P-009"
    },
    {
      "src": "../plans/P010_shaft.svg",
      "title": "P-010 Shaft",
      "kind": "part",
      "group": "part",
      "code": "P-010"
    },
    {
      "src": "../plans/P011_hood.svg",
      "title": "P-011 Dust hood",
      "kind": "part",
      "group": "part",
      "code": "P-011"
    },
    {
      "src": "../plans/P012_motor_cradle.svg",
      "title": "P-012 Motor cradle",
      "kind": "part",
      "group": "part",
      "code": "P-012"
    },
    {
      "src": "../plans/P013_truing_sled.svg",
      "title": "P-013 Truing sled",
      "kind": "part",
      "group": "part",
      "code": "P-013"
    },
    {
      "src": "../plans/P014_roller_yoke.svg",
      "title": "P-014 Roller yoke",
      "kind": "part",
      "group": "part",
      "code": "P-014"
    },
    {
      "src": "../plans/P015_pack_bore.svg",
      "title": "P-015 Pack-bore jig",
      "kind": "part",
      "group": "part",
      "code": "P-015"
    },
    {
      "src": "../plans/P016_nut_block.svg",
      "title": "P-016 Nut block",
      "kind": "part",
      "group": "part",
      "code": "P-016"
    },
    {
      "src": "../plans/A01_frame.svg",
      "title": "A-01 Frame assembly",
      "kind": "assembly",
      "group": "assembly",
      "code": "A-01"
    },
    {
      "src": "../plans/A02_drum.svg",
      "title": "A-02 Drum assembly",
      "kind": "assembly",
      "group": "assembly",
      "code": "A-02"
    },
    {
      "src": "../plans/A03_table.svg",
      "title": "A-03 Table assembly",
      "kind": "assembly",
      "group": "assembly",
      "code": "A-03"
    },
    {
      "src": "../plans/A04_drive.svg",
      "title": "A-04 Drive assembly",
      "kind": "assembly",
      "group": "assembly",
      "code": "A-04"
    },
    {
      "src": "../plans/A05_holddowns.svg",
      "title": "A-05 Hold-downs",
      "kind": "assembly",
      "group": "assembly",
      "code": "A-05"
    },
    {
      "src": "../plans/H01_hardware.svg",
      "title": "H-01 Hardware",
      "kind": "hardware",
      "group": "hardware",
      "code": "H-01"
    },
    {
      "src": "../renders/iso_assembled.svg",
      "title": "Iso assembled",
      "kind": "render",
      "group": "render",
      "code": "ISO-A"
    },
    {
      "src": "../renders/iso_exploded.svg",
      "title": "Iso exploded",
      "kind": "render",
      "group": "render",
      "code": "ISO-E"
    },
    {
      "src": "../renders/ortho_front.svg",
      "title": "Front solid",
      "kind": "render",
      "group": "render",
      "code": "ORTHO-F"
    },
    {
      "src": "../renders/ortho_side.svg",
      "title": "Drive side",
      "kind": "render",
      "group": "render",
      "code": "ORTHO-S"
    }
  ],
  "lumberyard": [
    {
      "where": "Plywood",
      "item": "\u00be\u2033 Baltic birch (18 mm Euro BB is the usual substitute)",
      "qty": "2 sheets 5\u2032\u00d75\u2032",
      "use": "P-001L/R, P-002, P-003, P-004, P-012, P-014"
    },
    {
      "where": "MDF",
      "item": "\u00be\u2033 MDF",
      "qty": "24\u2033 \u00d7 48\u2033",
      "use": "P-008 \u00d719 + P-015 + P-005 if no \u00bd\u2033 offcuts"
    },
    {
      "where": "Plywood",
      "item": "\u00bc\u2033 birch or pine ply",
      "qty": "24\u2033 \u00d7 24\u2033",
      "use": "P-011 hood blank"
    },
    {
      "where": "Plastics / order",
      "item": "\u00bd\u2033 phenolic or \u215c\u2033 MIC-6 / cast tooling plate",
      "qty": "16\u2033 \u00d7 22\u2033",
      "use": "P-006 wear face \u2014 metrology surface"
    },
    {
      "where": "Plastics",
      "item": "UHMW bar \u00be\u2033 \u00d7 \u00be\u2033",
      "qty": "48\u2033",
      "use": "P-007 ways, let into J-002 rebate"
    },
    {
      "where": "Hardwood / metal",
      "item": "Hardwood \u00be\u2033 or 1\u00bd\u2033 aluminum angle",
      "qty": "36\u2033",
      "use": "P-014 yokes"
    },
    {
      "where": "Abrasives",
      "item": "Hook Velcro 4\u2033 PSA + 3\u2033 loop paper 80/120/180/220",
      "qty": "1 roll + 4 grits",
      "use": "H-022 spiral wrap after truing"
    },
    {
      "where": "Glue",
      "item": "Titebond III + thin CA",
      "qty": "1 qt + 1 oz",
      "use": "H-023 torsion box, drum, Velcro edges"
    }
  ],
  "fasteners": [
    {
      "qty": "100",
      "item": "#8 \u00d7 1\u00bc\u2033 coarse cabinet screws",
      "use": "H-014"
    },
    {
      "qty": "50",
      "item": "#8 \u00d7 2\u2033 coarse screws (sides into stretchers)",
      "use": "H-015"
    },
    {
      "qty": "8",
      "item": "\u00bc-20 T-nuts + 1\u00bc\u2033 hex bolts + washers",
      "use": "H-016"
    },
    {
      "qty": "8",
      "item": "5/16-18 \u00d7 1\u2033 hex + nylock + washer (flange bearings)",
      "use": "Confirm flange hole."
    },
    {
      "qty": "6",
      "item": "Star knobs \u215c-16 + 1\u00bd\u2033 studs + washers",
      "use": "Way locks and yokes."
    },
    {
      "qty": "4",
      "item": "Shoulder bolts 5/16 \u00d7 1\u00bd\u2033",
      "use": "H-012"
    },
    {
      "qty": "4",
      "item": "Light compression springs ~\u00be\u2033 OD",
      "use": "Too stiff = snipe."
    },
    {
      "qty": "2",
      "item": "\u215c\u2033 drill rod / bolts \u00d7 17\u2033 (roller axles)",
      "use": "H-010"
    }
  ],
  "downloads": [
    {
      "href": "../pack/WALTER-DS16-RevB.zip",
      "label": "Shop pack (ZIP)",
      "note": "Plans, BOM, CAD \u2014 Save to Files",
      "download": "WALTER-DS16-RevB.zip",
      "share": true,
      "primary": true
    },
    {
      "href": "../pocket/",
      "label": "Pocket field card",
      "note": "Phone shop floor \u00b7 Add to Home Screen"
    },
    {
      "href": "../pack/BOM.csv",
      "label": "BOM.csv",
      "note": "Make + buy with part IDs",
      "download": "WALTER-DS16-BOM.csv"
    },
    {
      "href": "../pack/parts.csv",
      "label": "parts.csv",
      "note": "Fabrication register",
      "download": "WALTER-DS16-parts.csv"
    },
    {
      "href": "../pack/joints.csv",
      "label": "joints.csv",
      "note": "Joinery schedule",
      "download": "WALTER-DS16-joints.csv"
    },
    {
      "href": "../pack/fasteners.csv",
      "label": "fasteners.csv",
      "note": "Hardware-aisle list",
      "download": "WALTER-DS16-fasteners.csv"
    },
    {
      "href": "../pack/lumberyard.csv",
      "label": "lumberyard.csv",
      "note": "Store-trip sheet goods",
      "download": "WALTER-DS16-lumberyard.csv"
    },
    {
      "href": "../pack/fabrication.json",
      "label": "fabrication.json",
      "note": "Machine-readable SSOT",
      "download": "WALTER-DS16-fabrication.json"
    },
    {
      "href": "../cad/walter_ds16.py",
      "label": "walter_ds16.py",
      "note": "Parametric engineering source",
      "download": "walter_ds16.py"
    },
    {
      "href": "../cad/walter_ds16.scad",
      "label": "walter_ds16.scad",
      "note": "OpenSCAD solid model",
      "download": "walter_ds16.scad"
    },
    {
      "href": "../model/",
      "label": "3D viewer",
      "note": "Orbit / explode"
    },
    {
      "href": "../plans/IDX_drawings.svg",
      "label": "IDX SVG",
      "note": "Drawing index",
      "download": "IDX_drawings.svg"
    },
    {
      "href": "../plans/P001L_side_drive.svg",
      "label": "P-001L SVG",
      "note": "Drive side panel",
      "download": "P001L_side_drive.svg"
    },
    {
      "href": "../plans/H01_hardware.svg",
      "label": "H-01 SVG",
      "note": "Illustrated hardware",
      "download": "H01_hardware.svg"
    },
    {
      "href": "../plans/D11_register.svg",
      "label": "D-11 SVG",
      "note": "Part register",
      "download": "D11_register.svg"
    },
    {
      "href": "../plans/D12_joinery.svg",
      "label": "D-12 SVG",
      "note": "Joinery & QA",
      "download": "D12_joinery.svg"
    },
    {
      "href": "../",
      "label": "Design page",
      "note": "Overview"
    }
  ],
  "sources": [
    {
      "label": "Ron Walters drum sander (woodgears)",
      "href": "https://woodgears.ca/reader/walters/drum_sander.html"
    },
    {
      "label": "Walters build walkthrough (YouTube)",
      "href": "https://youtu.be/W-5Sj6kBVic"
    },
    {
      "label": "Simon Heslop variant",
      "href": "https://woodgears.ca/sander/drum.html"
    },
    {
      "label": "Pat Hawley / Wandel free plans",
      "href": "https://woodgears.ca/sander/plans/"
    }
  ],
  "tools": [
    "Table saw / track saw",
    "Dado stack or router (J-001, J-002)",
    "Drill press + pack-bore jig P-015",
    "Dial indicator 0.001\u2033 + mag base",
    "Feelers / winding sticks / calipers",
    "Clamps \u00b7 squares",
    "Dust collector 4\u2033"
  ]
};
