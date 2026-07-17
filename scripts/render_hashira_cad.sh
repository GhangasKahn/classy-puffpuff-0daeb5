#!/usr/bin/env bash
# Render / export HASHIRA OpenSCAD models via OpenSCAD CLI.
# Companion to the openscad-mcp server (.mcp.json) for Cursor agents.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAD="$ROOT/fence/cad"
RENDERS="$CAD/renders"
EXPORTS="$CAD/exports"
OPENSCAD="${OPENSCAD_PATH:-openscad}"

mkdir -p "$RENDERS" "$EXPORTS"

models=(nuki watari_ago hozo ne_tsugi ari_kake kama_tsugi bay)

echo "Using: $($OPENSCAD --version 2>&1 | head -1)"

render_one() {
  local m="$1" exploded="$2" out="$3"
  "$OPENSCAD" -o "$RENDERS/$out" \
    --imgsize=1200,900 \
    --colorscheme=BeforeDawn \
    --autocenter --viewall \
    -D "exploded=${exploded}" \
    -D 'show_cladding=1' \
    "$CAD/${m}.scad" 2>>"$EXPORTS/${m}.log"
}

for m in "${models[@]}"; do
  src="$CAD/${m}.scad"
  echo "==> export STL $m"
  "$OPENSCAD" -o "$EXPORTS/${m}.stl" \
    -D 'exploded=0' \
    -D 'show_cladding=1' \
    "$src" 2>"$EXPORTS/${m}.log"

  echo "==> render $m (exploded + assembled)"
  render_one "$m" 1 "${m}_iso.png"
  render_one "$m" 0 "${m}_assembled.png"
done

echo "Done."
ls -la "$RENDERS" "$EXPORTS" | sed -n '1,100p'
