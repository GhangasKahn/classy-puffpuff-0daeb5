#!/usr/bin/env bash
# STELE — full pipeline: FreeCAD model -> exports -> renders -> plan sheets.
#
# Requirements:
#   * FreeCAD (freecadcmd). Override binary with FREECADCMD=/path/to/freecadcmd
#     (AppImage users: ./FreeCAD.AppImage --appimage-extract, then point at
#      squashfs-root/usr/bin/freecadcmd)
#   * OpenSCAD for the colored preview renders (optional)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAD="$ROOT/fence/stele/cad"
RENDERS="$ROOT/fence/stele/renders"
FREECADCMD="${FREECADCMD:-freecadcmd}"

echo "==> FreeCAD build (model + FCStd/STEP/STL exports)"
(cd "$CAD" && "$FREECADCMD" stele_fence.py 2>&1 | grep -E "STELE|Run length|Pier top|Arch crown" || true)

if command -v openscad >/dev/null 2>&1; then
  echo "==> OpenSCAD preview renders"
  mkdir -p "$RENDERS"
  cd "$CAD"
  openscad -o "$RENDERS/stele_iso.png"   --imgsize=1600,1000 --colorscheme=BeforeDawn --autocenter --viewall scene.scad
  openscad -o "$RENDERS/stele_front.png" --imgsize=1800,700  --colorscheme=BeforeDawn --camera=5970,-13000,1100,5970,0,1100 --projection=o scene.scad
  openscad -o "$RENDERS/stele_gate.png"  --imgsize=1300,1100 --colorscheme=BeforeDawn --camera=8170,-7400,1750,8170,0,1350 scene.scad
  openscad -o "$RENDERS/stele_pier.png"  --imgsize=1000,1200 --colorscheme=BeforeDawn --camera=2100,-3600,2400,0,0,1000 scene.scad
  openscad -o "$RENDERS/stele_below.png" --imgsize=1300,1100 --colorscheme=BeforeDawn -D 'show_below_grade=true' -D 'show_ground=false' --camera=2600,-7000,-400,1220,0,-100 scene.scad
else
  echo "openscad not found — skipping preview renders"
fi

echo "==> Plan sheets (SVG)"
python3 "$ROOT/scripts/gen_stele_plans.py"

echo "Done."
