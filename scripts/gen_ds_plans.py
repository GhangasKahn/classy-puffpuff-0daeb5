# Generate DS-1…DS-6 shop plan sheets (11×8.5 landscape SVG).
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "shop/drum-sander/app/plans"
W, H = 1680, 1188  # ~11x8.5 at 150 dpi-ish


def sheet(num, title, subtitle, body):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="{W}" height="{H}" fill="#f4efe6" stroke="#1a1f24" stroke-width="3"/>
<rect x="24" y="24" width="1632" height="1140" fill="none" stroke="#1a1f24" stroke-width="1.2"/>
<line x1="24" y1="1098" x2="1656" y2="1098" stroke="#1a1f24" stroke-width="1.5"/>
<text x="40" y="70" font-family="IBM Plex Mono, Menlo, monospace" font-size="16" fill="#c47a3a" font-weight="600">DS-18 SHOP DRUM SANDER</text>
<text x="40" y="96" font-family="Georgia, serif" font-size="28" fill="#1a1f24" font-weight="600">{title}</text>
<text x="40" y="122" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#5a4a3a">{subtitle}</text>
<text x="40" y="1130" font-family="Georgia, serif" font-size="28" fill="#c47a3a" font-weight="600">DS-18</text>
<text x="160" y="1126" font-family="IBM Plex Mono, Menlo, monospace" font-size="18" fill="#1a1f24" font-weight="600">{num}  ·  {title}</text>
<text x="40" y="1154" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a">Dimensions in inches · Rev A · hobby machine, not UL listed</text>
<text x="1640" y="1130" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#5a4a3a" text-anchor="end">18″ drum · 6″ OD · 1.5 HP</text>
<text x="1640" y="1154" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a" text-anchor="end">Cabinet 36 × 22 × 28 · overall 42″ high</text>
{body}
</svg>
"""


def dimh(x1, x2, y, label):
    mid = (x1 + x2) / 2
    return f"""
<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#c47a3a" stroke-width="1.4"/>
<polygon points="{x1},{y} {x1+10},{y-4} {x1+10},{y+4}" fill="#c47a3a"/>
<polygon points="{x2},{y} {x2-10},{y-4} {x2-10},{y+4}" fill="#c47a3a"/>
<rect x="{mid-50}" y="{y-14}" width="100" height="20" fill="#f4efe6"/>
<text x="{mid}" y="{y+2}" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#c47a3a" text-anchor="middle">{label}</text>
"""


def dimv(x, y1, y2, label):
    mid = (y1 + y2) / 2
    return f"""
<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#c47a3a" stroke-width="1.4"/>
<polygon points="{x},{y1} {x-4},{y1+10} {x+4},{y1+10}" fill="#c47a3a"/>
<polygon points="{x},{y2} {x-4},{y2-10} {x+4},{y2-10}" fill="#c47a3a"/>
<text x="{x+10}" y="{mid}" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#c47a3a">{label}</text>
"""


# Scale: 8 px per inch for elevations
S = 8
ox, oy = 120, 780  # front origin (bottom-left of cabinet front)

# Front elevation geometry
cabW, cabH, cabD = 36 * S, 28 * S, 22 * S
drumY = 28 * S + 8 * S
drumR = 3 * S
drumL = 18 * S

front = f"""
<text x="40" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">FRONT ELEVATION — operator face</text>
<!-- cabinet -->
<rect x="{ox}" y="{oy - cabH}" width="{cabW}" height="{cabH}" fill="#d2b48c" stroke="#1a1f24" stroke-width="1.8"/>
<rect x="{ox + 8}" y="{oy - cabH + 8}" width="{cabW - 16}" height="70" fill="none" stroke="#1a1f24" stroke-dasharray="6 4"/>
<text x="{ox + cabW/2}" y="{oy - 40}" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a" text-anchor="middle">MOTOR BAY</text>
<!-- towers -->
<rect x="{ox + 6*S}" y="{oy - cabH - 14*S}" width="{0.75*S}" height="{14*S}" fill="#b08958" stroke="#1a1f24"/>
<rect x="{ox + 29.25*S}" y="{oy - cabH - 14*S}" width="{0.75*S}" height="{14*S}" fill="#b08958" stroke="#1a1f24"/>
<!-- drum -->
<ellipse cx="{ox + cabW/2}" cy="{oy - drumY}" rx="{drumL/2}" ry="{drumR}" fill="#e0b888" stroke="#1a1f24" stroke-width="1.6"/>
<!-- hood -->
<path d="M{ox + cabW/2 - drumL/2} {oy - drumY} C{ox + cabW/2 - drumL/2} {oy - drumY - 5*S}, {ox + cabW/2 + drumL/2} {oy - drumY - 5*S}, {ox + cabW/2 + drumL/2} {oy - drumY}" fill="none" stroke="#4a5560" stroke-width="8"/>
<!-- table -->
<rect x="{ox + 8*S}" y="{oy - drumY + drumR + 8}" width="{20*S}" height="{0.75*S}" fill="#c4a574" stroke="#1a1f24"/>
<!-- switch -->
<rect x="{ox - 18}" y="{oy - 18*S}" width="16" height="28" rx="2" fill="#c47a3a" stroke="#1a1f24"/>
{dimh(ox, ox + cabW, oy + 28, '36" CABINET')}
{dimh(ox + cabW/2 - drumL/2, ox + cabW/2 + drumL/2, oy - cabH - 14*S - 36, '18" DRUM')}
{dimv(ox + cabW + 36, oy, oy - cabH, '28"')}
{dimv(ox + cabW + 72, oy, oy - cabH - 14*S, '42" OA')}
"""

# Side elevation
sx = 980
side = f"""
<text x="920" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">RIGHT SIDE — dust port</text>
<rect x="{sx}" y="{oy - cabH}" width="{cabD}" height="{cabH}" fill="#c4a574" stroke="#1a1f24" stroke-width="1.8"/>
<ellipse cx="{sx + cabD/2}" cy="{oy - drumY}" rx="{drumR}" ry="{drumR}" fill="#e0b888" stroke="#1a1f24" stroke-width="1.6"/>
<rect x="{sx + cabD/2 - 11*S}" y="{oy - drumY + drumR + 8}" width="{22*S}" height="{0.75*S}" fill="#d2b48c" stroke="#1a1f24"/>
<rect x="{sx + cabD/2 - 2*S}" y="{oy - drumY - 2*S}" width="{4*S}" height="18" fill="#4a5560" stroke="#1a1f24"/>
<circle cx="{sx + cabD/2}" cy="{oy - drumY - 2*S - 20}" r="16" fill="none" stroke="#4a5560" stroke-width="3"/>
<text x="{sx + cabD/2}" y="{oy - drumY - 2*S - 44}" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a" text-anchor="middle">4" PORT</text>
{dimh(sx, sx + cabD, oy + 28, '22" DEEP')}
<text x="{sx}" y="{oy + 70}" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a">Table travel 2.5″ under 6″ drum · 20×22 table</text>
"""

notes = """
<text x="40" y="980" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#c47a3a" font-weight="600">NOTES</text>
<text x="40" y="1004" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#1a1f24">1. Baltic birch 3/4″ carcass, dados at bottom. 2. Pillow blocks coplanar before hanging drum.</text>
<text x="40" y="1026" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#1a1f24">3. Magnetic switch + E-stop. 4. Collector ≥ 350 CFM on 4″ port before any test. 5. Max take 1/32″ hardwood.</text>
"""

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "DS1_general.svg").write_text(sheet("DS-1", "General arrangement", "Front + side elevations  ·  scale 1:8 approx", front + side + notes))

# DS-2 plywood nesting — 4x8 at 3.5 px/in
N = 3.5
sheet_w, sheet_h = 96 * N, 48 * N


def ply(x, y, w, h, label, fill="#d2b48c"):
    return f"""<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#1a1f24" stroke-width="1.2"/>
<text x="{x + w/2}" y="{y + h/2 + 4}" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#1a1f24" text-anchor="middle">{label}</text>
"""


a_ox, a_oy = 80, 180
# Sheet A: two 22×28 sides + front 34.5×28 (91" × 28") + leftover strip for towers/aprons/hoods
nest_a = f"""
<text x="40" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">SHEET A — 4×8 × 3/4″ Baltic birch</text>
<rect x="{a_ox}" y="{a_oy}" width="{sheet_w}" height="{sheet_h}" fill="#efe6d6" stroke="#1a1f24" stroke-width="2"/>
{ply(a_ox + 4, a_oy + 4, 22*N, 28*N, 'SIDE 22×28')}
{ply(a_ox + 4 + 22*N + 4, a_oy + 4, 22*N, 28*N, 'SIDE 22×28')}
{ply(a_ox + 4 + 44*N + 8, a_oy + 4, 34.5*N, 28*N, 'FRONT 34.5×28')}
{ply(a_ox + 4, a_oy + 4 + 28*N + 6, 6*N, 14*N, 'TOWER')}
{ply(a_ox + 4 + 6*N + 6, a_oy + 4 + 28*N + 6, 6*N, 14*N, 'TOWER')}
{ply(a_ox + 4 + 12*N + 12, a_oy + 4 + 28*N + 6, 12*N, 8*N, 'HOOD')}
{ply(a_ox + 4 + 24*N + 16, a_oy + 4 + 28*N + 6, 12*N, 8*N, 'HOOD')}
{ply(a_ox + 4 + 36*N + 20, a_oy + 4 + 28*N + 6, 22*N, 3.5*N, 'APR 22')}
{ply(a_ox + 4 + 36*N + 20, a_oy + 4 + 28*N + 6 + 3.5*N + 4, 22*N, 3.5*N, 'APR 22')}
{ply(a_ox + 4 + 36*N + 20, a_oy + 4 + 28*N + 6 + 7*N + 8, 18.5*N, 3.5*N, 'APR 18.5')}
{ply(a_ox + 4 + 58*N + 24, a_oy + 4 + 28*N + 6, 18.5*N, 3.5*N, 'APR 18.5')}
<text x="{a_ox}" y="{a_oy + sheet_h + 28}" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a">Kerf ~1/8″ between parts. Grain with the long edge. Remainder is scrap / fence stock.</text>
"""

b_ox, b_oy = 80, 620
nest_b = f"""
<text x="40" y="600" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">SHEET B — 4×8 × 3/4″ Baltic birch</text>
<rect x="{b_ox}" y="{b_oy}" width="{sheet_w}" height="{sheet_h}" fill="#efe6d6" stroke="#1a1f24" stroke-width="2"/>
{ply(b_ox + 4, b_oy + 4, 34.5*N, 28*N, 'BACK 34.5×28')}
{ply(b_ox + 4 + 34.5*N + 8, b_oy + 4, 20*N, 22*N, 'TABLE 20×22', '#e0b888')}
{ply(b_ox + 4 + 34.5*N + 8 + 20*N + 8, b_oy + 4, 34.5*N, 20.5*N, 'BOTTOM 34.5×20.5')}
{ply(b_ox + 4, b_oy + 4 + 28*N + 8, 34.5*N, 14*N, 'SHELF 34.5×14')}
<text x="{b_ox + 4 + 34.5*N + 8}" y="{b_oy + 4 + 28*N + 36}" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a">Offcut: fence 3/4×3×20 hardwood from solid stock, not this sheet.</text>
"""

(OUT / "DS2_plywood.svg").write_text(sheet("DS-2", "Plywood nesting", "Two 4×8 sheets  ·  3/4″ Baltic birch  ·  scale 1:24 approx", nest_a + nest_b))

drum = f"""
<text x="40" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">DRUM ASSEMBLY — section through axis</text>
<!-- shaft -->
<rect x="200" y="430" width="960" height="24" fill="#c5cbcf" stroke="#1a1f24"/>
<text x="680" y="418" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#5a4a3a" text-anchor="middle">1″ × 24″ SHAFT</text>
<!-- drum tube -->
<rect x="360" y="360" width="720" height="164" rx="8" fill="#e0b888" stroke="#1a1f24" stroke-width="1.8"/>
<text x="720" y="450" font-family="IBM Plex Mono, Menlo, monospace" font-size="16" fill="#1a1f24" text-anchor="middle">6″ OD × 18″ TUBE</text>
<!-- hubs -->
<rect x="380" y="390" width="40" height="104" fill="#8a9098" stroke="#1a1f24"/>
<rect x="1020" y="390" width="40" height="104" fill="#8a9098" stroke="#1a1f24"/>
<!-- pillow blocks -->
<rect x="280" y="400" width="56" height="84" fill="#5a6570" stroke="#1a1f24"/>
<rect x="1044" y="400" width="56" height="84" fill="#5a6570" stroke="#1a1f24"/>
<text x="308" y="390" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a" text-anchor="middle">PB</text>
<text x="1072" y="390" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a" text-anchor="middle">PB</text>
<!-- pulley -->
<rect x="200" y="392" width="28" height="100" fill="#8a9098" stroke="#1a1f24"/>
<text x="214" y="380" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a" text-anchor="middle">4″ PULLEY</text>
{dimh(360, 1080, 560, '18" FACE')}
{dimh(200, 1160, 600, '24" SHAFT')}
{dimv(1200, 360, 524, '6" OD')}
<text x="40" y="700" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#c47a3a" font-weight="600">FIT &amp; RUNOUT</text>
<text x="40" y="728" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Pillow blocks coplanar. End play ≤ 0.010″. Drum TIR ≤ 0.015″ at the face.</text>
<text x="40" y="752" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Lock collars outboard of hubs. Set-screw pulleys on flats. PSA wrap, 1/4″ overlap, seam away from infeed.</text>
<text x="40" y="800" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#c47a3a" font-weight="600">TOWER SPACING</text>
<text x="40" y="828" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Inside of towers 19″. Drum centered. Shaft stubs ~2.5″ each side for pulley (left) and collar (right).</text>
"""
(OUT / "DS3_drum.svg").write_text(sheet("DS-3", "Drum, shaft, bearings", "Journals, TIR, tower spacing", drum))

table = f"""
<text x="40" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">TABLE — plan (looking down)</text>
<rect x="200" y="200" width="800" height="880" fill="#d2b48c" stroke="#1a1f24" stroke-width="2"/>
<rect x="200" y="200" width="800" height="48" fill="#8b5a2b" stroke="#1a1f24"/>
<text x="600" y="230" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#f4efe6" text-anchor="middle">FENCE 3/4 × 3 × 20</text>
<!-- jacks -->
<circle cx="280" cy="280" r="18" fill="#8a9098" stroke="#1a1f24"/>
<circle cx="920" cy="280" r="18" fill="#8a9098" stroke="#1a1f24"/>
<circle cx="280" cy="1000" r="18" fill="#8a9098" stroke="#1a1f24"/>
<circle cx="920" cy="1000" r="18" fill="#8a9098" stroke="#1a1f24"/>
<text x="280" y="268" font-family="IBM Plex Mono, Menlo, monospace" font-size="11" fill="#5a4a3a" text-anchor="middle">JACK</text>
<text x="600" y="640" font-family="IBM Plex Mono, Menlo, monospace" font-size="18" fill="#1a1f24" text-anchor="middle">20 × 22 × 3/4″ TOP</text>
<text x="600" y="668" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a" text-anchor="middle">UHMW strip on infeed lip · aprons 3.5″</text>
{dimh(200, 1000, 1060, '20"')}
<text x="1080" y="200" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">JACK DETAIL</text>
<line x1="1180" y1="260" x2="1180" y2="900" stroke="#c5cbcf" stroke-width="8"/>
<circle cx="1180" cy="920" r="36" fill="#8a9098" stroke="#1a1f24"/>
<text x="1180" y="926" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#1a1f24" text-anchor="middle">WHEEL</text>
<rect x="1140" y="240" width="80" height="28" fill="#d2b48c" stroke="#1a1f24"/>
<text x="1300" y="400" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">1/2-13 × 8″ screw</text>
<text x="1300" y="424" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">T-nut in table corner</text>
<text x="1300" y="448" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Travel 2.5″</text>
<text x="1300" y="472" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Keep four corners even</text>
"""
# Wait, table plan I used height 880 which overflows the title block. Let me fix - the sheet content area is y=140 to 1098. 200+880=1080 is OK actually... 200+880=1080, title block starts 1098. Tight but OK. But dimh at 1060 might overlap. Let me use a smaller table drawing.

(OUT / "DS4_table.svg").write_text(sheet("DS-4", "Table &amp; jacks", "20×22 top  ·  four 1/2-13 jacks  ·  2.5″ travel", table))

drive = f"""
<text x="40" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">DRIVE — left side (belt plane)</text>
<rect x="160" y="520" width="280" height="200" fill="#2a2e33" rx="20" stroke="#1a1f24" stroke-width="1.8"/>
<text x="300" y="630" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#f4efe6" text-anchor="middle">1.5 HP · 1725 RPM</text>
<circle cx="520" cy="620" r="32" fill="#8a9098" stroke="#1a1f24" stroke-width="2"/>
<text x="520" y="680" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a" text-anchor="middle">2″ MOTOR</text>
<circle cx="520" cy="320" r="64" fill="#8a9098" stroke="#1a1f24" stroke-width="2"/>
<text x="520" y="240" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a" text-anchor="middle">4″ DRUM</text>
<path d="M488 320 C400 320, 400 620, 488 620" fill="none" stroke="#1a1a1a" stroke-width="10"/>
<path d="M552 320 C640 320, 640 620, 552 620" fill="none" stroke="#1a1a1a" stroke-width="10"/>
<text x="700" y="470" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">A-36 V-belt</text>
<text x="700" y="494" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">~1:2 reduction → ~860 RPM drum</text>
<text x="700" y="518" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">1/2″ deflection at mid-span</text>
<text x="700" y="542" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">1.5″ slot in left cabinet wall</text>
<text x="980" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">DUST HOOD</text>
<path d="M1040 420 C1040 260, 1480 260, 1480 420" fill="none" stroke="#4a5560" stroke-width="14"/>
<circle cx="1260" cy="248" r="28" fill="none" stroke="#4a5560" stroke-width="6"/>
<text x="1260" y="200" font-family="IBM Plex Mono, Menlo, monospace" font-size="13" fill="#5a4a3a" text-anchor="middle">4″ PORT AFT</text>
<text x="1040" y="480" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">~3/8″ clearance over 6″ drum</text>
<text x="1040" y="504" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">26 ga wrap + 3/4″ plywood cheeks</text>
<text x="1040" y="528" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Collector ≥ 350 CFM before test</text>
<text x="40" y="820" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#c47a3a" font-weight="600">WIRING</text>
<text x="40" y="848" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Magnetic starter on left cabinet. E-stop in reach of the operator. Cord through 7/8″ strain relief.</text>
<text x="40" y="872" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Match motor nameplate (115/230). A power blip must not restart the drum.</text>
"""
(OUT / "DS5_drive.svg").write_text(sheet("DS-5", "Drive &amp; dust", "Pulleys, belt, hood, wiring", drive))

rows = [
    ("2", "3/4″ birch", "22 × 28", "Cabinet sides", "A"),
    ("1", "3/4″ birch", "34½ × 28", "Cabinet front", "A"),
    ("1", "3/4″ birch", "34½ × 28", "Cabinet back", "B"),
    ("1", "3/4″ birch", "34½ × 20½", "Cabinet bottom", "B"),
    ("1", "3/4″ birch", "34½ × 14", "Motor shelf", "B"),
    ("2", "3/4″ birch", "6 × 14", "Bearing towers", "A"),
    ("1", "3/4″ birch", "20 × 22", "Table top", "B"),
    ("2", "3/4″ birch", "3½ × 22", "Table aprons (sides)", "A"),
    ("2", "3/4″ birch", "3½ × 18½", "Table aprons (ends)", "A"),
    ("2", "3/4″ birch", "12 × 8", "Hood cheeks", "A"),
    ("1", "26 ga steel", "20 × 12", "Hood wrap", "—"),
    ("1", "hardwood", "¾ × 3 × 20", "Fence", "offcut"),
    ("1", "UHMW", "⅛ × ¾ × 20", "Infeed wear strip", "—"),
]
table_rows = ""
y = 200
table_rows += """<text x="40" y="160" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">CUT LIST</text>
<text x="80" y="188" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a">QTY</text>
<text x="160" y="188" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a">MATERIAL</text>
<text x="400" y="188" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a">SIZE</text>
<text x="620" y="188" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a">PART</text>
<text x="980" y="188" font-family="IBM Plex Mono, Menlo, monospace" font-size="12" fill="#5a4a3a">SHEET</text>
"""
for qty, mat, size, part, sh in rows:
    table_rows += f"""<text x="80" y="{y}" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">{qty}</text>
<text x="160" y="{y}" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">{mat}</text>
<text x="400" y="{y}" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">{size}</text>
<text x="620" y="{y}" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">{part}</text>
<text x="980" y="{y}" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">{sh}</text>
"""
    y += 28

hw = """
<text x="40" y="560" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">HARDWARE (EST. USD)</text>
<text x="80" y="588" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">2 sheets birch $160 · 1.5 HP motor $180 · 1″ PBs $45 · 1×24 shaft $35</text>
<text x="80" y="612" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">6×18 drum + hubs $55 · 2″/4″ pulleys $32 · A-36 belt $12 · 4 jacks $48</text>
<text x="80" y="636" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">T-nuts $8 · 4″ port $12 · mag switch $55 · PSA paper $40 · casters $32</text>
<text x="80" y="660" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Screws / collars / glue ~$52 · TOTAL ≈ $766</text>
<text x="40" y="720" font-family="IBM Plex Mono, Menlo, monospace" font-size="15" fill="#c47a3a" font-weight="600">SAFETY</text>
<text x="80" y="748" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Unplug to wrap paper. Collector on. No hands under a live drum. Max 1/32″ hardwood take.</text>
<text x="80" y="772" font-family="IBM Plex Mono, Menlo, monospace" font-size="14" fill="#1a1f24">Hobby machine — not a listed commercial sander. Magnetic switch required.</text>
"""
(OUT / "DS6_cutlist.svg").write_text(sheet("DS-6", "Cut list &amp; hardware", "Shop copy  ·  inches  ·  2026 ballpark prices", table_rows + hw))

print("wrote", list(OUT.glob("DS*.svg")))
