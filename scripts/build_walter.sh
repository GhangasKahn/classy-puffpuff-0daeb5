#!/usr/bin/env bash
# WALTER — 16" drum sander CAD → optional renders → plan sheets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAD="$ROOT/sander/walter/cad"
RENDERS="$ROOT/sander/walter/renders"
FREECADCMD="${FREECADCMD:-freecadcmd}"

if [[ -x /home/ubuntu/tools/squashfs-root/usr/bin/freecadcmd ]]; then
  FREECADCMD=/home/ubuntu/tools/squashfs-root/usr/bin/freecadcmd
fi

mkdir -p "$RENDERS" "$CAD/exports"

if command -v "$FREECADCMD" >/dev/null 2>&1; then
  echo "==> FreeCAD build (model + FCStd/STEP/STL exports)"
  (cd "$CAD" && "$FREECADCMD" walter_sander.py 2>&1 | grep -E "WALTER|Capacity|Drum|Drive|Feed|Envelope|wrote" || true)
else
  echo "freecadcmd not found — skipping STEP/STL (SVG plans do not need it)"
fi

if command -v openscad >/dev/null 2>&1; then
  echo "==> OpenSCAD preview renders"
  cd "$CAD"
  openscad -o "$RENDERS/walter_iso.png"     --imgsize=1600,1000 --colorscheme=BeforeDawn --autocenter --viewall walter_sander.scad
  openscad -o "$RENDERS/walter_infeed.png"  --imgsize=1400,1000 --colorscheme=BeforeDawn --camera=280,0,350,0,0,180 --projection=o walter_sander.scad
  openscad -o "$RENDERS/walter_drive.png"   --imgsize=1600,900  --colorscheme=BeforeDawn --camera=0,-900,350,280,450,180 --projection=o walter_sander.scad
  openscad -o "$RENDERS/walter_cutaway.png" --imgsize=1600,1000 --colorscheme=BeforeDawn -D 'cutaway=true' --autocenter --viewall walter_sander.scad
else
  echo "openscad not found — skipping preview renders"
fi

echo "==> Plan sheets (SVG)"
python3 "$ROOT/scripts/gen_walter_plans.py"

echo "Done."
