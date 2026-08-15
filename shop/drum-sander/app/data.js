/* AUTO-GENERATED from cad/walter_ds16.py — do not edit */
window.WALTER_DATA = {
  "meta": {
    "name": "WALTER",
    "code": "DS-16",
    "subtitle": "Dedicated drum thickness sander \u00b7 15.5\u2033 \u00b7 geometry Rev B \u00b7 fab B.3",
    "revision": "B",
    "fabricationRev": "B.3",
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
  "steps": [
    {
      "step": 1,
      "chapter": "01 Stock",
      "title": "Buy, acclimate, and measure the plywood",
      "goal": "Know your real ply thickness before a single dado is cut.",
      "parts": [],
      "hardware": [],
      "tools": [
        "Calipers",
        "Moisture meter (optional)",
        "Flat floor"
      ],
      "sheets": [
        "D-10",
        "IDX"
      ],
      "actions": [
        "Stand the sheets on edge in the shop for at least 48 hours. Euro BB arrives at 18 mm, not \u00be\u2033.",
        "Caliper the ply in six places. Record the number as ply_actual (model default 0.75\u2033).",
        "If it is not 0.75\u2033, edit ply_actual in cad/walter_ds16.py and regenerate every sheet. Do not shave the 16.5\u2033 inner span to make the old numbers work."
      ],
      "qc": "QC-01",
      "gate": "Measured ply thickness recorded. Inner span stays 16.5\u2033 (419 mm).",
      "hold": "Nothing is cut yet. This is the cheapest place to catch the 18 mm surprise.",
      "warn": "",
      "shows": [],
      "adds": [],
      "correctable": "Everything.",
      "id": "ST-01",
      "of": 14
    },
    {
      "step": 2,
      "chapter": "02 Breakdown",
      "title": "Rough-cut the panels oversize",
      "goal": "Flat, labelled, manageable blanks out of full sheets.",
      "parts": [
        "P-001L",
        "P-001R",
        "P-002",
        "P-003",
        "P-004"
      ],
      "hardware": [],
      "tools": [
        "Track saw or table saw",
        "Straightedge",
        "Sawhorses"
      ],
      "sheets": [
        "D-6",
        "D-10"
      ],
      "actions": [
        "Cut every panel about \u215b\u2033 over width and \u00bc\u2033 over length. Final size comes off one stop later.",
        "Write the part ID on each blank in pencil the moment it leaves the sheet.",
        "Keep the two side blanks as a matched pair \u2014 they get drilled together in ST-04."
      ],
      "qc": "",
      "gate": "All blanks labelled, oversize, and stacked flat.",
      "hold": "",
      "warn": "Full sheets are heavy and awkward. Support the offcut so it cannot drop onto the blade or onto you.",
      "shows": [],
      "adds": [],
      "correctable": "Sizes \u2014 everything is still oversize.",
      "id": "ST-02",
      "of": 14
    },
    {
      "step": 3,
      "chapter": "03 Sides",
      "title": "Cut both sides to final size on one stop",
      "goal": "Two panels that ARE the same size, not two panels that measure the same.",
      "parts": [
        "P-001L",
        "P-001R"
      ],
      "hardware": [],
      "tools": [
        "Table saw + stop block",
        "Framing square"
      ],
      "sheets": [
        "P-001L",
        "P-001R",
        "D-12"
      ],
      "actions": [
        "Set the stop for 30\u2033 and cut both panels (S-001). Do not move the stop between cuts.",
        "Reset for 22\u2033 depth and cut both (S-002).",
        "Mark the INNER face and the INFEED edge on each panel. Those two marks are Datum C and Datum B for the rest of the build."
      ],
      "qc": "QC-02",
      "gate": "Panels identical within a pencil line; inner face and infeed edge marked on both.",
      "hold": "",
      "warn": "",
      "shows": [
        "sides"
      ],
      "adds": [
        "sides"
      ],
      "correctable": "Nothing about panel size after this \u2014 the drum and table depend on it.",
      "id": "ST-03",
      "of": 14
    },
    {
      "step": 4,
      "chapter": "03 Sides",
      "title": "Stack-drill the pair: bearing, flange, pilots",
      "goal": "One hole pattern, drilled once, so the drum axis cannot be crooked.",
      "parts": [
        "P-001L",
        "P-001R"
      ],
      "hardware": [
        "H-001",
        "H-002"
      ],
      "tools": [
        "Drill press",
        "Forstner bits",
        "Clamps",
        "Awl"
      ],
      "sheets": [
        "P-001L",
        "P-001R"
      ],
      "actions": [
        "Clamp the panels face-to-face, inner faces together, infeed edges flush.",
        "Lay out the bearing centreline at Y 11\u2033 from the infeed edge and Z 18.5\u2033 up from the bottom.",
        "Set the actual flange on the panel and transfer its bolt holes. The drawing shows 2.05\u2033 square as a placeholder \u2014 your bearing decides.",
        "Drill the \u23001.125\u2033 shaft clearance and the four bolt holes through both panels at once (S-008).",
        "Drive side only: pilot the motor pivot at Y 4\u2033 / Z 6\u2033 and the indicator pad at Y 8\u2033 / Z 16\u2033."
      ],
      "qc": "QC-02",
      "gate": "Panels separated; hole patterns line up when the panels are flipped face-to-face.",
      "hold": "Stop here until the flange is in your hand. Do not drill this pattern from the drawing alone.",
      "warn": "Clamp hard. A panel that shifts mid-drill gives you two different machines.",
      "shows": [
        "sides"
      ],
      "adds": [
        "sides"
      ],
      "correctable": "Almost nothing. This pattern is the datum for the whole machine.",
      "id": "ST-04",
      "of": 14
    },
    {
      "step": 5,
      "chapter": "03 Sides",
      "title": "Dado the stretcher housings and way rebates",
      "goal": "Inner-face joinery, mirrored \u2014 the one operation where the panels are NOT identical.",
      "parts": [
        "P-001L",
        "P-001R"
      ],
      "hardware": [],
      "tools": [
        "Dado stack or router + edge guide",
        "Test offcut"
      ],
      "sheets": [
        "P-001L",
        "P-001R",
        "D-12"
      ],
      "actions": [
        "Split the pair. From here the panels are mirror images \u2014 work only on the marked inner faces.",
        "Cut three stretcher housings 0.25\u2033 deep \u00d7 0.75\u2033 wide, Y 2\u2033 to 6\u2033, at Z 6, 12, 20\u2033 (J-001, S-006).",
        "Rout the way rebate 0.520\u2033 deep \u00d7 0.75\u2033 wide at Z 10\u2033, stopping 1\u2033 shy of each end (J-002, S-007).",
        "Test the dado width on an offcut of the same ply first. A sloppy housing is a racking frame."
      ],
      "qc": "QC-12",
      "gate": "Rebate 0.520\u2033 deep \u00b10.010\u2033; a scrap of way stock sits 0.230\u2033 proud of the inner face.",
      "hold": "",
      "warn": "Do not dado the panels while they are still stacked. You will get two left-hand sides.",
      "shows": [
        "sides",
        "ways"
      ],
      "adds": [
        "ways"
      ],
      "correctable": "A rebate can go deeper, never shallower.",
      "id": "ST-05",
      "of": 14
    },
    {
      "step": 6,
      "chapter": "04 Frame",
      "title": "Glue the box: stretchers, base, diagonals",
      "goal": "A square, stiff carcase that will not rack when a board is pushed through it.",
      "parts": [
        "P-001L",
        "P-001R",
        "P-002",
        "P-003"
      ],
      "hardware": [
        "H-014",
        "H-015",
        "H-023"
      ],
      "tools": [
        "Long clamps",
        "Framing square",
        "Tape measure",
        "Glue brush"
      ],
      "sheets": [
        "A-01",
        "P-003",
        "P-002"
      ],
      "actions": [
        "Dry-fit all three stretchers (17\u2033, housed 0.25\u2033 each end) into the dados. Check the inner span reads 16.5\u2033.",
        "Glue and clamp. Measure both diagonals and pull them equal before the glue grabs.",
        "Drill and drive #8 \u00d7 2\u2033 screws from outside into each stretcher end.",
        "Screw the base deck on, then measure the diagonals again."
      ],
      "qc": "QC-03",
      "gate": "Diagonals equal within 1/32\u2033. Inner span 16.5\u2033 at top, middle, and bottom.",
      "hold": "Let the glue cure before hanging anything heavy on the box.",
      "warn": "",
      "shows": [
        "sides",
        "base",
        "stretch"
      ],
      "adds": [
        "base",
        "stretch"
      ],
      "correctable": "Squareness \u2014 for about ten minutes.",
      "id": "ST-06",
      "of": 14
    },
    {
      "step": 7,
      "chapter": "04 Frame",
      "title": "Bond the UHMW ways and wax them",
      "goal": "Two coplanar rails for the table to ride on. These, not the stretchers, locate the table.",
      "parts": [
        "P-007"
      ],
      "hardware": [
        "H-023",
        "H-024"
      ],
      "tools": [
        "Winding sticks or straightedge",
        "Dial indicator",
        "Clamps"
      ],
      "sheets": [
        "P-007",
        "A-01"
      ],
      "actions": [
        "Cut two UHMW bars to 22\u2033 and set them into the rebates. They should project 0.230\u2033.",
        "Bond and clamp. Optional: #8 flush screws from the outer face.",
        "Check both ways for twist with winding sticks or an indicator riding a flat bar.",
        "Paste wax only. Never oil \u2014 oil migrates into the wood and into your finish."
      ],
      "qc": "QC-04",
      "gate": "No twist between the two ways. Projection 0.230\u2033 \u00b10.010\u2033 along the full length.",
      "hold": "",
      "warn": "",
      "shows": [
        "sides",
        "base",
        "stretch",
        "ways"
      ],
      "adds": [
        "ways"
      ],
      "correctable": "UHMW can be planed down; it cannot be built back up.",
      "id": "ST-07",
      "of": 14
    },
    {
      "step": 8,
      "chapter": "05 Drum",
      "title": "Pack-bore the discs and laminate the drum",
      "goal": "One stiff cylinder blank on one true axis.",
      "parts": [
        "P-008",
        "P-009",
        "P-015"
      ],
      "hardware": [
        "H-018",
        "H-023"
      ],
      "tools": [
        "Bandsaw",
        "Drill press + reamer",
        "Clamps",
        "Scale"
      ],
      "sheets": [
        "P-008",
        "P-009",
        "P-015",
        "A-02"
      ],
      "actions": [
        "Bandsaw 19 MDF discs and 2 birch ends at \u23005.125\u2033 \u2014 oversize on purpose.",
        "Stack the whole pack in the P-015 jig and ream \u23000.75\u2033 straight through (J-005, S-009). Never bore discs one at a time.",
        "Glue the stack with a 1 mm relief every 4 MDF discs. Birch ends outboard.",
        "Weigh the two end discs against each other and balance them before assembly."
      ],
      "qc": "",
      "gate": "Bore accepts the shaft with light friction. Stack length 15.75\u2033.",
      "hold": "Full cure before the drum ever spins. A delaminated disc at 1035 RPM is a projectile.",
      "warn": "MDF dust is the worst dust in the shop. Respirator and extraction on.",
      "shows": [
        "drum",
        "shaft"
      ],
      "adds": [
        "drum"
      ],
      "correctable": "Outside diameter \u2014 that is what truing is for.",
      "id": "ST-08",
      "of": 14
    },
    {
      "step": 9,
      "chapter": "05 Drum",
      "title": "Hang the shaft: drive FIXED, idler FLOATING",
      "goal": "One bearing defines the axis; the other lets the shaft grow.",
      "parts": [
        "P-010"
      ],
      "hardware": [
        "H-001",
        "H-002",
        "H-017"
      ],
      "tools": [
        "Wrenches",
        "Dial indicator",
        "Feeler gauges"
      ],
      "sheets": [
        "P-010",
        "A-02",
        "P-001R"
      ],
      "actions": [
        "Slide the 22.5\u2033 shaft through the drum and both panels.",
        "Bolt H-001 to the drive side and torque it. That flange is now the drum-axis datum (J-006).",
        "Set H-002 on the 0.25\u2033 pad on the idler side. Snug only \u2014 the shaft must still be able to slide axially (J-007).",
        "Spin the drum by hand through several turns. It should coast, not bind and not ring."
      ],
      "qc": "QC-11",
      "gate": "Shaft turns freely; measurable axial float at the idler end.",
      "hold": "",
      "warn": "Locking both flanges bends the shaft and kills both bearings. Do not do it because it feels tighter.",
      "shows": [
        "sides",
        "base",
        "stretch",
        "ways",
        "drum",
        "shaft"
      ],
      "adds": [
        "shaft"
      ],
      "correctable": "Bearing position, while the bolts are still loose.",
      "id": "ST-09",
      "of": 14
    },
    {
      "step": 10,
      "chapter": "06 Drive",
      "title": "Mount the motor, align the pulleys, lock the cradle",
      "goal": "Belt tension by gravity, then locked so it cannot pump.",
      "parts": [
        "P-012"
      ],
      "hardware": [
        "H-003",
        "H-004",
        "H-005",
        "H-006",
        "H-016"
      ],
      "tools": [
        "Straightedge",
        "Wrenches",
        "Level"
      ],
      "sheets": [
        "P-012",
        "A-04"
      ],
      "actions": [
        "Pivot P-012 on the drive-side hole and hang the 0.5 HP motor on it.",
        "Fit the 3\u2033 motor pulley and the 5\u2033 drum pulley. Lay a straightedge across both faces and shim until they are coplanar.",
        "Let the cradle hang to tension the belt, measure the centre distance, then buy the belt to that number.",
        "Lock the cradle. A cradle that still swings will pump the belt and chirp."
      ],
      "qc": "QC-09",
      "gate": "Pulley faces coplanar; belt tracks centred when the drum is turned by hand.",
      "hold": "Do not connect power yet.",
      "warn": "Mains wiring, switch, and grounding belong to a qualified electrician and your local code. This package does not release electrical work.",
      "shows": [
        "sides",
        "base",
        "stretch",
        "ways",
        "drum",
        "shaft",
        "motor"
      ],
      "adds": [
        "motor"
      ],
      "correctable": "Belt length, before you buy it.",
      "id": "ST-10",
      "of": 14
    },
    {
      "step": 11,
      "chapter": "07 Table",
      "title": "Build the torsion-box table and bond the wear face",
      "goal": "A flat plate that stays flat. This is the surface you measure against forever.",
      "parts": [
        "P-004",
        "P-005",
        "P-006"
      ],
      "hardware": [
        "H-023"
      ],
      "tools": [
        "Clamps and cauls",
        "Straightedge",
        "Feeler gauges",
        "Flat bench"
      ],
      "sheets": [
        "P-004",
        "P-005",
        "P-006",
        "A-03"
      ],
      "actions": [
        "Glue the rib grid at 4\u2033 o.c. between the two skins. Full glue, clamped on a flat reference.",
        "Check the box flat in both directions and on both diagonals. Flatten it before going further.",
        "Bond the phenolic or tooling-plate wear face on top (J-004).",
        "Confirm the finished plan size is 16\u2033 \u00d7 22\u2033 so it enters the ways."
      ],
      "qc": "QC-05",
      "gate": "Wear face flat within 0.004\u2033 on both diagonals.",
      "hold": "Cure fully. Every later measurement trusts this plane.",
      "warn": "",
      "shows": [
        "table"
      ],
      "adds": [
        "table"
      ],
      "correctable": "Flatness, while the box is still open.",
      "id": "ST-11",
      "of": 14
    },
    {
      "step": 12,
      "chapter": "07 Table",
      "title": "Fit the dual Acme lift and chain-couple it",
      "goal": "Both ends of the table rise together, with a home position to return to.",
      "parts": [
        "P-016"
      ],
      "hardware": [
        "H-007",
        "H-008",
        "H-013"
      ],
      "tools": [
        "Wrenches",
        "Drill",
        "Tape measure"
      ],
      "sheets": [
        "P-016",
        "A-03"
      ],
      "actions": [
        "Bolt a bronze nut block under each end of the table.",
        "Fit both \u00bd-10 Acme screws. One turn is 0.1000\u2033 \u2014 that is your fine adjustment.",
        "Chain-couple the two screws so they turn together. Fit the left clutch and the home dog.",
        "Run the table through the full 3.25\u2033 of travel. It must rise without twist or bind."
      ],
      "qc": "QC-12",
      "gate": "Table rises and falls freely through full travel; both ends move the same amount.",
      "hold": "",
      "warn": "",
      "shows": [
        "sides",
        "base",
        "stretch",
        "ways",
        "drum",
        "shaft",
        "motor",
        "table",
        "elev"
      ],
      "adds": [
        "table",
        "elev"
      ],
      "correctable": "Nut block position, before the holes are final.",
      "id": "ST-12",
      "of": 14
    },
    {
      "step": 13,
      "chapter": "08 Hood & hold-downs",
      "title": "Kerf-bend the hood and set the roller yokes",
      "goal": "The guard that is also the dust hood, plus the rollers that kill snipe.",
      "parts": [
        "P-011",
        "P-014"
      ],
      "hardware": [
        "H-009",
        "H-010",
        "H-011",
        "H-012",
        "H-013",
        "H-019"
      ],
      "tools": [
        "Table saw (kerfing)",
        "Feeler gauges",
        "Drill"
      ],
      "sheets": [
        "P-011",
        "P-014",
        "A-05"
      ],
      "actions": [
        "Kerf-bend the hood blank around the drum arc, glue the form, fill the kerfs, and fit the 4\u2033 port.",
        "Hang both roller yokes on shoulder-bolt pivots with light compression springs.",
        "Set each roller 0.030\u2033 below the drum OD with paper on, using feeler gauges.",
        "Check the hood clears the drum, the rollers, and the oscillator stroke if you fitted one."
      ],
      "qc": "QC-08",
      "gate": "Both rollers 0.030\u2033 below drum OD, paper on. Hood seats without touching the drum.",
      "hold": "",
      "warn": "Hood ON is the primary guard. Open it only with the machine stopped and unplugged.",
      "shows": [
        "sides",
        "base",
        "stretch",
        "ways",
        "drum",
        "shaft",
        "motor",
        "table",
        "elev",
        "rollers",
        "hood"
      ],
      "adds": [
        "rollers",
        "hood"
      ],
      "correctable": "Spring rate and roller height, any time.",
      "id": "ST-13",
      "of": 14
    },
    {
      "step": 14,
      "chapter": "09 Commissioning",
      "title": "True, wrap, re-clock, and cut a witness board",
      "goal": "Turn an assembled machine into a calibrated one.",
      "parts": [
        "P-013"
      ],
      "hardware": [
        "H-021",
        "H-022"
      ],
      "tools": [
        "Dial indicator + mag base",
        "Calipers",
        "Test panel",
        "Respirator"
      ],
      "sheets": [
        "Q-101",
        "P-013",
        "A-02"
      ],
      "actions": [
        "Paper off: true the drum with the full-width sled until TIR \u2264 0.002\u2033 mid-span (S-010).",
        "Wrap Velcro, then spiral the paper. Paper thickness is not uniform, so parallel changes here.",
        "Paper on: indicate the drum at the drive end (A) and the idler end (B). Bring |A\u2212B| \u2264 0.003\u2033, then set the home dog (S-011).",
        "Sand a witness board at 80 grit, one pass. Caliper four corners. Scatter must be \u2264 0.003\u2033.",
        "Then work the pass schedule: 0.008\u2033 rough, 0.004\u2033 medium, 0.001\u2033 finish."
      ],
      "qc": "QC-06 \u00b7 QC-07 \u00b7 QC-10",
      "gate": "TIR \u2264 0.002\u2033 paper-off \u00b7 |A\u2212B| \u2264 0.003\u2033 paper-on \u00b7 witness scatter \u2264 0.003\u2033.",
      "hold": "First powered run: hood on, no stock, stand clear of the drum ends, hand on the switch.",
      "warn": "Do not sand stock shorter than about 12\u2033 without the sled. Hands never under the drum or the hold-downs.",
      "shows": [
        "sides",
        "base",
        "stretch",
        "ways",
        "drum",
        "shaft",
        "motor",
        "table",
        "elev",
        "rollers",
        "hood"
      ],
      "adds": [],
      "correctable": "Everything that matters \u2014 which is why you re-clock after every paper change.",
      "id": "ST-14",
      "of": 14
    }
  ],
  "release": {
    "state": "FABRICATION REVIEW",
    "risk_class": "R3",
    "risk_triggers": [
      "Powered spindle: 5\u2033 drum at ~1035 RPM with stored rotational energy",
      "Mains-voltage motor, switch, and cord require qualified electrical work",
      "Ingoing nip between drum and feed rollers; workpiece ejection path",
      "Abrasive dust generation, worst when truing the MDF core"
    ],
    "conditions": [
      "Transfer the purchased 4-bolt flange to the panel before drilling. The bolt square on the drawings is ASSUMED.",
      "Measure ply_actual and regenerate. Keep the 16.5\u2033 inner span; do not shrink it to suit 18 mm stock.",
      "Motor circuit, switch, grounding, and cord: qualified electrician and local code. Not released by this package.",
      "Commission with the hood on and no stock, standing clear of the drum ends.",
      "Confirm TIR, |A\u2212B|, and witness-board scatter before the machine is used on real work."
    ],
    "not_released": [
      "Electrical installation and any code-dependent wiring",
      "Any use as a metal-working or thickness-planing machine",
      "Stock shorter than ~12\u2033 without the sled"
    ]
  },
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
      "src": "../plans/G001_cover.svg",
      "title": "G-001 Cover & release",
      "kind": "guide",
      "group": "guide",
      "code": "G-001"
    },
    {
      "src": "../plans/G002_design_basis.svg",
      "title": "G-002 Design basis",
      "kind": "guide",
      "group": "guide",
      "code": "G-002"
    },
    {
      "src": "../plans/G003_registers.svg",
      "title": "G-003 Evidence & calcs",
      "kind": "guide",
      "group": "guide",
      "code": "G-003"
    },
    {
      "src": "../plans/G004_safety.svg",
      "title": "G-004 Safety & risk",
      "kind": "guide",
      "group": "guide",
      "code": "G-004"
    },
    {
      "src": "../plans/E101_exploded.svg",
      "title": "E-101 Exploded + BOM",
      "kind": "guide",
      "group": "guide",
      "code": "E-101"
    },
    {
      "src": "../plans/Q101_commissioning.svg",
      "title": "Q-101 Commissioning",
      "kind": "guide",
      "group": "guide",
      "code": "Q-101"
    },
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
      "src": "../plans/ST01_step.svg",
      "title": "ST-01 Buy, acclimate, and measure the plywood",
      "kind": "step",
      "group": "step",
      "code": "ST-01"
    },
    {
      "src": "../plans/ST02_step.svg",
      "title": "ST-02 Rough-cut the panels oversize",
      "kind": "step",
      "group": "step",
      "code": "ST-02"
    },
    {
      "src": "../plans/ST03_step.svg",
      "title": "ST-03 Cut both sides to final size on one stop",
      "kind": "step",
      "group": "step",
      "code": "ST-03"
    },
    {
      "src": "../plans/ST04_step.svg",
      "title": "ST-04 Stack-drill the pair: bearing, flange, pilots",
      "kind": "step",
      "group": "step",
      "code": "ST-04"
    },
    {
      "src": "../plans/ST05_step.svg",
      "title": "ST-05 Dado the stretcher housings and way rebates",
      "kind": "step",
      "group": "step",
      "code": "ST-05"
    },
    {
      "src": "../plans/ST06_step.svg",
      "title": "ST-06 Glue the box: stretchers, base, diagonals",
      "kind": "step",
      "group": "step",
      "code": "ST-06"
    },
    {
      "src": "../plans/ST07_step.svg",
      "title": "ST-07 Bond the UHMW ways and wax them",
      "kind": "step",
      "group": "step",
      "code": "ST-07"
    },
    {
      "src": "../plans/ST08_step.svg",
      "title": "ST-08 Pack-bore the discs and laminate the drum",
      "kind": "step",
      "group": "step",
      "code": "ST-08"
    },
    {
      "src": "../plans/ST09_step.svg",
      "title": "ST-09 Hang the shaft: drive FIXED, idler FLOATING",
      "kind": "step",
      "group": "step",
      "code": "ST-09"
    },
    {
      "src": "../plans/ST10_step.svg",
      "title": "ST-10 Mount the motor, align the pulleys, lock the cradle",
      "kind": "step",
      "group": "step",
      "code": "ST-10"
    },
    {
      "src": "../plans/ST11_step.svg",
      "title": "ST-11 Build the torsion-box table and bond the wear face",
      "kind": "step",
      "group": "step",
      "code": "ST-11"
    },
    {
      "src": "../plans/ST12_step.svg",
      "title": "ST-12 Fit the dual Acme lift and chain-couple it",
      "kind": "step",
      "group": "step",
      "code": "ST-12"
    },
    {
      "src": "../plans/ST13_step.svg",
      "title": "ST-13 Kerf-bend the hood and set the roller yokes",
      "kind": "step",
      "group": "step",
      "code": "ST-13"
    },
    {
      "src": "../plans/ST14_step.svg",
      "title": "ST-14 True, wrap, re-clock, and cut a witness board",
      "kind": "step",
      "group": "step",
      "code": "ST-14"
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
      "href": "../guide/",
      "label": "Master build guide",
      "note": "The whole book, in order \u00b7 Print \u2192 PDF",
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
