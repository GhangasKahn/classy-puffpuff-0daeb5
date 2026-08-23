"""
WALTER kernel — single source of truth for the 16" drum sander.

All dimensions are inches. Downstream writers convert to mm.
Used by: gen_walter_cad.py, gen_walter_plans.py, gen_walter_fab.py,
         walter_sander.py (FreeCAD), and the build app JSON dump.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from typing import Iterable, Literal

IN = 25.4
REV = "B"

P = dict(
    # envelope
    base_x=22.00,
    base_y=36.00,
    base_t=0.75,
    wall_t=1.50,
    inner_w=16.50,
    wall_h=20.00,
    # drum
    drum_od=5.00,
    drum_blank=5.125,
    drum_face=16.00,
    drum_z=13.50,
    drum_y=18.00,
    n_discs=21,
    disc_t=0.75,
    gap_every=4,
    gap_mm=0.5,
    end_bell_t=0.125,
    shaft_d=0.75,
    shaft_len=22.00,
    shaft_x0=-0.25,
    key_w=0.1875,
    key_h=0.09375,
    key_len=4.00,
    # table / conveyor
    table_t=0.75,
    uhmw_t=0.125,
    opening_default=1.50,
    opening_max=4.00,
    opening_min=0.06,
    roller_od=2.00,
    roller_cd=26.86,
    roller_y_in=4.57,
    roller_shaft=0.625,
    roller_crown=0.030,
    belt_w=16.00,
    belt_len=60.00,
    platen_y0=5.50,
    platen_y1=30.50,
    # elevation
    acme_d=0.75,
    acme_tpi=6,
    acme_len=12.00,
    acme_y=(10.0, 26.0),
    travel=4.50,
    # drive
    pulley_mot=3.00,
    pulley_drm=4.75,
    pulley_t=0.75,
    motor_hp=1.0,
    motor_rpm=1725,
    motor_od=6.50,
    motor_len=8.00,
    motor_y=28.00,
    motor_z=4.60,
    # dust
    hood_t=0.25,
    port_d=4.00,
    plate_t=0.25,
    plate=6.00,
    # stand (optional cabinet)
    stand_h=32.00,
    stand_t=0.75,
    # capacity
    max_width=16.00,
    min_thick=0.06,
    max_thick=4.00,
)

idle_inner = P["wall_t"]
drive_inner = P["wall_t"] + P["inner_w"]
drive_outer = drive_inner + P["wall_t"]  # 19.50
drum_gap = (P["inner_w"] - P["drum_face"]) / 2.0
drum_x0 = idle_inner + drum_gap
drum_rpm = P["motor_rpm"] * P["pulley_mot"] / P["pulley_drm"]
sfm = math.pi * P["drum_od"] * drum_rpm / 12.0
feed_fpm = (math.pi * P["roller_od"] / 12.0) * 30.0
roller_y_out = P["roller_y_in"] + P["roller_cd"]
acme_x = (idle_inner + drive_inner) / 2.0
platen_len = P["platen_y1"] - P["platen_y0"]


def inch_mm(n: float) -> float:
    return n * IN


def table_top_z(opening: float) -> float:
    return P["drum_z"] - P["drum_od"] / 2.0 - opening


@dataclass
class Box:
    name: str
    group: str
    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float
    color: str = "#c4a574"

    @property
    def kind(self) -> str:
        return "box"


@dataclass
class Cyl:
    name: str
    group: str
    x: float
    y: float
    z: float
    d: float
    h: float
    axis: Literal["x", "y", "z"] = "x"
    color: str = "#7a8288"

    @property
    def kind(self) -> str:
        return "cyl"


Prim = Box | Cyl


def _off(p: Prim, dx: float, dy: float, dz: float) -> Prim:
    p.x += dx
    p.y += dy
    p.z += dz
    return p


def assembly(
    opening: float | None = None,
    explode: float = 0.0,
    cutaway: bool = False,
    stand: bool = False,
    discs: bool = True,
) -> list[Prim]:
    """Return all solids. explode is 0..1. Units: inches."""
    opening = P["opening_default"] if opening is None else opening
    tt = table_top_z(opening)
    e = explode
    parts: list[Prim] = []

    def add(p: Prim, ex=0.0, ey=0.0, ez=0.0):
        parts.append(_off(p, ex * e, ey * e, ez * e))

    # --- frame ---
    add(Box("base", "frame", 0, 0, 0, P["base_x"], P["base_y"], P["base_t"], "#8a6a42"))
    add(Box("rail_idle", "frame", 0.75, 1.0, -1.50, 1.50, P["base_y"] - 2, 1.50, "#6e5638"))
    add(Box("rail_drive", "frame", P["base_x"] - 2.25, 1.0, -1.50, 1.50, P["base_y"] - 2, 1.50, "#6e5638"))
    add(Box("wall_idle", "frame", 0, 0, P["base_t"], P["wall_t"], P["base_y"], P["wall_h"] - P["base_t"], "#c4a574"))
    if not cutaway:
        add(Box("wall_drive", "frame", drive_inner, 0, P["base_t"], P["wall_t"], P["base_y"], P["wall_h"] - P["base_t"], "#b89660"))
    add(Box("stretcher_in", "frame", idle_inner, 1.0, P["base_t"], P["inner_w"], 1.50, 3.50, "#8a6a42"))
    add(Box("stretcher_out", "frame", idle_inner, P["base_y"] - 2.5, P["base_t"], P["inner_w"], 1.50, 3.50, "#8a6a42"))
    add(Box("plate_idle", "steel", idle_inner, P["drum_y"] - 3, P["drum_z"] - 3, P["plate_t"], P["plate"], P["plate"], "#6a7278"))
    if not cutaway:
        add(Box("plate_drive", "steel", drive_inner - P["plate_t"], P["drum_y"] - 3, P["drum_z"] - 3, P["plate_t"], P["plate"], P["plate"], "#6a7278"))

    # --- drum ---
    dz_drum = 8.0
    if discs:
        stack = P["n_discs"] * P["disc_t"]
        x = drum_x0 + (P["drum_face"] - stack) / 2.0
        for i in range(P["n_discs"]):
            add(
                Cyl(f"disc_{i+1:02d}", "drum", x, P["drum_y"], P["drum_z"], P["drum_od"], P["disc_t"] * 0.98, "x",
                    "#8a6a42" if i not in (0, 20) else "#5c656c"),
                ez=dz_drum,
            )
            x += P["disc_t"]
    else:
        add(Cyl("drum_face", "drum", drum_x0, P["drum_y"], P["drum_z"], P["drum_od"], P["drum_face"], "x", "#7a5a3a"), ez=dz_drum)
    add(Cyl("abrasive", "drum", drum_x0, P["drum_y"], P["drum_z"], P["drum_od"] + 0.06, P["drum_face"], "x", "#b4532a"), ez=dz_drum)
    add(Cyl("bell_idle", "steel", drum_x0 - P["end_bell_t"], P["drum_y"], P["drum_z"], P["drum_od"] + 0.04, P["end_bell_t"], "x", "#8a9298"), ez=dz_drum)
    add(Cyl("bell_drive", "steel", drum_x0 + P["drum_face"], P["drum_y"], P["drum_z"], P["drum_od"] + 0.04, P["end_bell_t"], "x", "#8a9298"), ez=dz_drum)
    add(Cyl("shaft", "drum", P["shaft_x0"], P["drum_y"], P["drum_z"], P["shaft_d"], P["shaft_len"], "x", "#d0d4d6"), ez=dz_drum)
    add(Cyl("pulley_drum", "steel", drive_outer + 0.20, P["drum_y"], P["drum_z"], P["pulley_drm"], P["pulley_t"], "x", "#5c656c"), ez=dz_drum)
    add(Cyl("brg_idle", "steel", idle_inner + 0.05, P["drum_y"], P["drum_z"], 2.85, 0.55, "x", "#6a7278"), ez=dz_drum)
    if not cutaway:
        add(Cyl("brg_drive", "steel", drive_inner - 0.60, P["drum_y"], P["drum_z"], 2.85, 0.55, "x", "#6a7278"), ez=dz_drum)
    for i, dy in enumerate((-1.85, 1.85)):
        add(
            Cyl(f"jack_{i}", "steel", idle_inner - 0.85, P["drum_y"] + dy, P["drum_z"] - 3.15,
                0.25, 1.55, "z", "#8a9298"),
            ez=dz_drum,
        )
    add(
        Box("key", "steel", drum_x0 + 0.4, P["drum_y"] - P["key_w"] / 2,
            P["drum_z"] + P["shaft_d"] / 2 - 0.02, P["key_len"], P["key_w"], P["key_h"], "#d0d4d6"),
        ez=dz_drum,
    )

    # --- table / conveyor ---
    dz_tab = -6.0
    add(Box("platen", "table", idle_inner + 0.12, P["platen_y0"], tt - P["table_t"] - P["uhmw_t"],
            P["inner_w"] - 0.24, platen_len, P["table_t"], "#c4a574"), ez=dz_tab)
    add(Box("uhmw", "table", idle_inner + 0.12, P["platen_y0"], tt - P["uhmw_t"],
            P["inner_w"] - 0.24, platen_len, P["uhmw_t"], "#e8eef0"), ez=dz_tab)
    add(Box("way_idle", "table", idle_inner - 0.38, P["platen_y0"] + 1, tt - 2.25,
            0.50, platen_len - 2, 2.00, "#8a6a42"), ez=dz_tab)
    add(Box("way_drive", "table", drive_inner - 0.12, P["platen_y0"] + 1, tt - 2.25,
            0.50, platen_len - 2, 2.00, "#8a6a42"), ez=dz_tab)
    for i, y in enumerate((P["roller_y_in"], roller_y_out)):
        add(Cyl(f"roller_{i}", "conveyor", idle_inner + 0.12, y, tt - P["roller_od"] / 2,
                P["roller_od"], P["inner_w"] - 0.24, "x", "#6a7278"), ez=dz_tab)
        add(Cyl(f"roller_shaft_{i}", "conveyor", -0.5, y, tt - P["roller_od"] / 2,
                P["roller_shaft"], drive_outer + 1.0, "x", "#c5cbcf"), ez=dz_tab)
    add(Box("belt_top", "conveyor", idle_inner + 0.15, P["roller_y_in"], tt,
            P["inner_w"] - 0.30, P["roller_cd"], 0.08, "#1a1a1c"), ez=dz_tab)
    add(Box("belt_bot", "conveyor", idle_inner + 0.15, P["roller_y_in"], tt - P["roller_od"] - 0.08,
            P["inner_w"] - 0.30, P["roller_cd"], 0.08, "#1a1a1c"), ez=dz_tab)
    for i, y in enumerate(P["acme_y"]):
        add(Cyl(f"acme_{i}", "steel", acme_x, y, 2.0, P["acme_d"], P["acme_len"], "z", "#8a9298"), ez=dz_tab)
        add(Cyl(f"lock_{i}", "steel", acme_x + 1.15, y, tt - 2.05, 0.90, 0.40, "z", "#3a3228"), ez=dz_tab)
    add(
        Cyl("handwheel", "steel", acme_x, P["acme_y"][0], 2.0 + P["acme_len"], 4.00, 0.45, "z", "#5c656c"),
        ez=dz_tab,
    )
    add(Box("dro", "table", idle_inner - 0.08, 7.6, tt + 0.15, 0.45, 4.2, 0.85, "#1a1a1c"), ez=dz_tab)

    # --- motor ---
    dx_mot = 8.0
    add(Cyl("motor", "motor", drive_outer + 0.25, P["motor_y"], P["motor_z"],
            P["motor_od"], P["motor_len"], "x", "#161616"), ex=dx_mot)
    add(Cyl("pulley_mot", "steel", drive_outer + 0.20, P["motor_y"], P["motor_z"],
            P["pulley_mot"], P["pulley_t"], "x", "#5c656c"), ex=dx_mot)
    add(Box("hinge_plate", "steel", drive_outer - 0.12, P["motor_y"] - 4, 1.0,
            0.25, 8.5, 7.5, "#5c656c"), ex=dx_mot)
    add(Box("turnbuckle", "steel", drive_outer + 0.35, P["motor_y"] - 5.6, P["motor_z"] - 0.35,
            0.45, 2.1, 0.45, "#8a9298"), ex=dx_mot)
    if not cutaway:
        add(Box("guard", "guard", drive_outer + 0.05, P["drum_y"] - 6, 1.0,
                2.20, 16.5, 16.5, "#c4a574"), ex=6.0)

    # --- hood ---
    dz_hood = 12.0
    add(Box("hood_top", "hood", idle_inner + 0.08, P["drum_y"] - 4.2, P["drum_z"] + 0.4,
            P["inner_w"] - 0.16, 8.4, P["hood_t"], "#3d4a46"), ez=dz_hood)
    add(Box("hood_idle", "hood", idle_inner + 0.08, P["drum_y"] - 4.2, P["drum_z"] - 1.2,
            P["hood_t"], 8.4, 1.6, "#3d4a46"), ez=dz_hood)
    if not cutaway:
        add(Box("hood_drive", "hood", drive_inner - P["hood_t"] - 0.08, P["drum_y"] - 4.2, P["drum_z"] - 1.2,
                P["hood_t"], 8.4, 1.6, "#3d4a46"), ez=dz_hood)
    add(Box("hood_back", "hood", idle_inner + 0.08, P["drum_y"] + 4.0, P["drum_z"] - 1.2,
            P["inner_w"] - 0.16, P["hood_t"], 2.8, "#3d4a46"), ez=dz_hood)
    add(Cyl("port", "steel", acme_x, P["drum_y"] + 4.1, P["drum_z"] + 0.6,
            P["port_d"] + 0.15, 2.2, "y", "#8a9298"), ez=dz_hood)
    add(Box("brush", "hood", idle_inner + 0.1, P["drum_y"] - 4.18, P["drum_z"] - 1.45,
            P["inner_w"] - 0.20, 0.18, 0.40, "#2a241c"), ez=dz_hood)

    add(Box("gearmotor", "motor", -3.2, roller_y_out, tt - P["roller_od"] / 2 - 0.5,
            3.0, 3.0, 3.0, "#161616"), ez=dz_tab)

    if stand:
        add(Box("stand_left", "stand", 0.5, 2.0, -P["stand_h"], 0.75, P["base_y"] - 4, P["stand_h"] - 0.1, "#8a6a42"))
        add(Box("stand_right", "stand", P["base_x"] - 1.25, 2.0, -P["stand_h"], 0.75, P["base_y"] - 4, P["stand_h"] - 0.1, "#8a6a42"))
        add(Box("stand_shelf", "stand", 0.5, 2.0, -P["stand_h"] + 8, P["base_x"] - 1.0, P["base_y"] - 4, 0.75, "#c4a574"))
        add(Box("stand_back", "stand", 0.5, P["base_y"] - 2.75, -P["stand_h"], P["base_x"] - 1.0, 0.75, P["stand_h"] - 0.1, "#6e5638"))

    return parts


def dump_parameters(path: str) -> None:
    data = {
        "rev": REV,
        "name": "WALTER",
        "units": "inch",
        "derived": {
            "idle_inner": idle_inner,
            "drive_inner": drive_inner,
            "drive_outer": drive_outer,
            "drum_x0": drum_x0,
            "drum_rpm": round(drum_rpm, 2),
            "sfm": round(sfm, 1),
            "feed_fpm_at_30rpm": round(feed_fpm, 2),
            "roller_y_out": roller_y_out,
            "acme_x": acme_x,
            "platen_len": platen_len,
        },
        "P": {k: (list(v) if isinstance(v, tuple) else v) for k, v in P.items()},
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


PLYWOOD = [
    dict(id="A", name="Base", size='22.00 × 36.00 × ¾"', qty=1, stock='¾" BB', nest="sheet 1"),
    dict(id="B", name="Idle wall skins", size='20.00 × 36.00 × ¾"', qty=2, stock='¾" BB', nest="sheet 1–2"),
    dict(id="C", name="Drive wall skins", size='20.00 × 36.00 × ¾"', qty=2, stock='¾" BB', nest="sheet 2–3"),
    dict(id="D", name="Stretchers", size='16.50 × 3.50 × ¾"', qty=2, stock='¾" BB', nest="offcuts"),
    dict(id="E", name="Base rails", size='33.00 × 1.50 × 1.50"', qty=2, stock="hard maple", nest="solid"),
    dict(id="F", name="Platen skins", size='16.25 × 25.00 × ¼"', qty=2, stock='¼" BB', nest="¼ sheet"),
    dict(id="G", name="Platen grid", size='¾" strips, ~8 bf', qty=1, stock='¾" BB', nest="offcuts"),
    dict(id="H", name="Table rails", size='25.00 × 2.00 × ½"', qty=2, stock="maple", nest="solid"),
    dict(id="J", name="Drum discs Ø 5.125\"", size='¾" × 21 discs', qty=21, stock='¾" BB', nest="sheet 3"),
    dict(id="K", name="Hood panels", size="¼\" BB, ~4 ft²", qty=1, stock='¼" BB', nest="¼ sheet"),
    dict(id="L", name="Belt guard", size='17 × 17 × ¼" + edges', qty=1, stock='¼" BB', nest="¼ sheet"),
    dict(id="M", name="Nut blocks", size='2.00 × 2.00 × 3.00"', qty=2, stock="maple", nest="solid"),
    dict(id="N", name="Stand sides (opt.)", size='32.00 × 32.00 × ¾"', qty=2, stock='¾" BB', nest="sheet 4"),
    dict(id="P", name="Stand shelf / back (opt.)", size='21 × 32 × ¾"', qty=2, stock='¾" BB', nest="sheet 4"),
]

HARDWARE = [
    dict(item="Shaft ¾\" × 22\" 1144 Stressproof, keyed 3/16\"", qty="1", search="1144 ground 0.75 rod 24", mcmaster=""),
    dict(item="Flange bearing UCFL204-12 (¾\")", qty="2", search="UCFL204-12", mcmaster="6661K13"),
    dict(item="Flange bearing UCFL201-10 (⅝\")", qty="4", search="UCFL201-10", mcmaster="6661K11"),
    dict(item="Aluminum tube 2.00\" OD × 16.25\"", qty="2", search="aluminum round tube 2.000 OD", mcmaster="9056K44"),
    dict(item="Roller shaft ⅝\" × 22\"", qty="2", search="0.625 precision shaft", mcmaster="1346K13"),
    dict(item="Acme screw ¾-6 × 12\"", qty="2", search="acme 3/4-6 12", mcmaster="99030A460"),
    dict(item="Acme nut ¾-6 bronze", qty="2", search="acme nut 3/4-6", mcmaster="6350K15"),
    dict(item="HTD 5 mm 15 mm belt + 16T pulleys", qty="1 set", search="HTD 5mm 15mm", mcmaster=""),
    dict(item="Handwheel 4\" ¾\" bore", qty="1", search="handwheel 4 inch 3/4 bore", mcmaster="6086K52"),
    dict(item="4L pulley 3.00\" ¾\" bore", qty="1", search="4L pulley 3.0 3/4", mcmaster="6245K27"),
    dict(item="4L pulley 4.75\" ¾\" bore", qty="1", search="4L pulley 4.75 3/4", mcmaster="6245K47"),
    dict(item="4L440 link belt", qty="1", search="4L440 link", mcmaster="6191K37"),
    dict(item="Conveyor belt 16\" × 60\" 2-ply PVC endless", qty="1", search="PVC conveyor 16 inch", mcmaster=""),
    dict(item="Motor 1 HP TEFC 1725 RPM 115 V 56C", qty="1", search="1 HP TEFC 1725 56C", mcmaster=""),
    dict(item="24 V DC worm gearmotor ~30 RPM", qty="1", search="24V worm 30 rpm", mcmaster=""),
    dict(item="24 V 5 A PSU + PWM controller", qty="1", search="24V 5A PWM", mcmaster=""),
    dict(item="Magnetic starter / DP contactor + OL", qty="1", search="NEMA 0 starter 115V", mcmaster=""),
    dict(item="E-stop 40 mm mushroom NC", qty="1", search="estop 40mm", mcmaster=""),
    dict(item="Steel plate ¼\" × 6 × 6", qty="2", search="A36 1/4 plate", mcmaster="8910K713"),
    dict(item="Steel plate ¼\" × 8 × 10 (hinge)", qty="1", search="A36 1/4 plate", mcmaster="8910K713"),
    dict(item="UHMW 1/8 × 24 × 48", qty="1", search="UHMW 1/8 sheet", mcmaster="8752K111"),
    dict(item="PSA hook tape 4\" × 5 yd", qty="1", search="hook tape 4 inch PSA", mcmaster=""),
    dict(item="Abrasive rolls 3\" × 25' 80/120/150", qty="3", search="Klingspor 3 inch roll", mcmaster=""),
    dict(item="4\" dust flange + hose", qty="1", search="4 inch dust port", mcmaster=""),
    dict(item="Nylon brush strip 16\"", qty="1", search="brush strip 16", mcmaster=""),
    dict(item="#8 / 5/16 / ¼-20 fasteners + T-nuts", qty="1 kit", search="t-nut 1/4-20", mcmaster=""),
]

FMEA = [
    dict(id="F01", item="Conveyor walk", cause="No crown / PVC oval / sanding belt", effect="Belt shreds, can't feed", sev=8, det=6, prev="0.030\" crown, PVC belt, skew screws"),
    dict(id="F02", item="Drum crack", cause="MDF, no expansion gaps", effect="Out of round, vibration", sev=7, det=5, prev="Birch discs, 0.5 mm gaps every 4"),
    dict(id="F03", item="Table rack", cause="Independent corner screws", effect="Wedge-sanded panels", sev=7, det=4, prev="Dual Acme HTD-timed"),
    dict(id="F04", item="Belt slack on start", cause="Gravity motor mount", effect="Glazed belt, stall", sev=6, det=7, prev="Hinge plate + turnbuckle"),
    dict(id="F05", item="Restart after blink", cause="Plain switch", effect="Drum starts in hands", sev=9, det=3, prev="Magnetic starter / NOVR"),
    dict(id="F06", item="Kickback short stock", cause="Part shorter than platen", effect="Projectile", sev=8, det=4, prev="12\" min or carrier board"),
    dict(id="F07", item="Dust cloud", cause="Hood off / shop-vac", effect="Health, fire load", sev=8, det=8, prev="4\" @ 400 CFM, hood interlock"),
    dict(id="F08", item="Drum taper", cause="No idle jack", effect="Stripe / wedge", sev=5, det=5, prev="¼-20 jack ±0.040\""),
    dict(id="F09", item="Formica score", cause="Abrasive harder than laminate", effect="Platen not flat", sev=4, det=9, prev="HDPE / phenolic face"),
    dict(id="F10", item="Paper glued forever", cause="Permanent Velcro", effect="New drum to change wrap", sev=3, det=8, prev="Hook tape + end-bell slots"),
]
