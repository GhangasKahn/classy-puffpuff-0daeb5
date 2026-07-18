#!/usr/bin/env bash
# MARTIN — FreeCAD model → exports → renders → plan sheets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAD="$ROOT/fence/martin/cad"
RENDERS="$ROOT/fence/martin/renders"
FREECADCMD="${FREECADCMD:-freecadcmd}"

# Prefer extracted AppImage if present
if [[ -x /home/ubuntu/tools/squashfs-root/usr/bin/freecadcmd ]]; then
  FREECADCMD=/home/ubuntu/tools/squashfs-root/usr/bin/freecadcmd
fi

echo "==> FreeCAD build (model + FCStd/STEP/STL exports)"
(cd "$CAD" && "$FREECADCMD" martin_fence.py 2>&1 | grep -E "MARTIN|Run length|Height|Gate|Post|Bay|Drop" || true)

if command -v openscad >/dev/null 2>&1; then
  echo "==> OpenSCAD preview renders"
  mkdir -p "$RENDERS"
  cd "$CAD"
  openscad -o "$RENDERS/martin_iso.png"   --imgsize=1600,1000 --colorscheme=BeforeDawn --autocenter --viewall scene.scad
  openscad -o "$RENDERS/martin_front.png" --imgsize=1800,700  --colorscheme=BeforeDawn --camera=1816,-9000,900,1816,0,800 --projection=o scene.scad
  openscad -o "$RENDERS/martin_gate.png"  --imgsize=1200,1100 --colorscheme=BeforeDawn --camera=500,-4500,900,500,0,800 scene.scad
  openscad -o "$RENDERS/martin_pier.png"  --imgsize=1000,1200 --colorscheme=BeforeDawn --camera=200,-2500,400,45,0,0 scene.scad
  openscad -o "$RENDERS/martin_below.png" --imgsize=1400,1000 --colorscheme=BeforeDawn -D 'show_ground=false' --camera=1816,-7000,-200,1816,0,-200 scene.scad
else
  echo "openscad not found — skipping preview renders"
fi

echo "==> Plan sheets (SVG)"
python3 "$ROOT/scripts/gen_martin_plans.py"

echo "Done."
