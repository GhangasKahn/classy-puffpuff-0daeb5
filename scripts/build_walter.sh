#!/usr/bin/env bash
# WALTER — kernel CAD → meshes/renders → plan sheets → fab package.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAD="$ROOT/sander/walter/cad"
RENDERS="$ROOT/sander/walter/renders"
FREECADCMD="${FREECADCMD:-freecadcmd}"

if [[ -x /home/ubuntu/tools/squashfs-root/usr/bin/freecadcmd ]]; then
  FREECADCMD=/home/ubuntu/tools/squashfs-root/usr/bin/freecadcmd
fi

mkdir -p "$RENDERS" "$CAD/exports" "$ROOT/sander/walter/fab"

echo "==> Kernel CAD (STL / OBJ / SVG renders / parameters.json)"
python3 "$ROOT/scripts/gen_walter_cad.py"

echo "==> Plan sheets W-1 … W-14 (SVG)"
python3 "$ROOT/scripts/gen_walter_plans.py"

echo "==> Fab package (BOM, cut lists, FMEA, templates)"
python3 "$ROOT/scripts/gen_walter_fab.py"

if command -v "$FREECADCMD" >/dev/null 2>&1; then
  echo "==> FreeCAD (FCStd / STEP from kernel)"
  (cd "$CAD" && "$FREECADCMD" walter_sander.py 2>&1 | grep -E "WALTER|Capacity|Drum|Drive|Feed|Envelope|wrote" || true)
else
  echo "freecadcmd not found — kernel STL/OBJ already written"
fi

if command -v openscad >/dev/null 2>&1; then
  echo "==> OpenSCAD preview renders"
  cd "$CAD"
  openscad -o "$RENDERS/walter_iso.png"     --imgsize=1600,1000 --colorscheme=BeforeDawn --autocenter --viewall walter_sander.scad
  openscad -o "$RENDERS/walter_infeed.png"  --imgsize=1400,1000 --colorscheme=BeforeDawn --camera=280,0,350,0,0,180 --projection=o walter_sander.scad
  openscad -o "$RENDERS/walter_drive.png"   --imgsize=1600,900  --colorscheme=BeforeDawn --camera=0,-900,350,280,450,180 --projection=o walter_sander.scad
  openscad -o "$RENDERS/walter_cutaway.png" --imgsize=1600,1000 --colorscheme=BeforeDawn -D 'cutaway=true' --autocenter --viewall walter_sander.scad
  openscad -o "$RENDERS/walter_stand.png"   --imgsize=1400,1100 --colorscheme=BeforeDawn -D 'show_stand=true' --autocenter --viewall walter_sander.scad
else
  echo "openscad not found — SVG isometric renders already written"
fi

echo "WALTER package done."
