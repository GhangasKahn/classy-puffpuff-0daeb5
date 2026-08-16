#!/usr/bin/env python3
"""WALTER DS-16 — Rev C mechanics, accuracy budget, and component sizing.

WOODWRIGHT PLANFORGE v1.0 · calculation register for the drum-axis rebuild.

Scope of these calculations
---------------------------
These are SERVICEABILITY (accuracy and stiffness) calculations plus component
SIZING REQUIREMENTS. They are not a structural code check and they do not
certify any component. Where a purchased part's rating governs, this module
derives the REQUIRED rating and leaves the actual rating as [P] — to be read
off the manufacturer's data at order time.

Why Rev C exists
----------------
Rev B specified |A-B| <= 0.003" "paper-on" and a 3/4" drum shaft. Running the
beam numbers shows those two statements are incompatible: the 3/4" shaft spends
the entire 0.001" allowance at 4.25 lbf of sanding force. Rev B also used one
number, 0.003", for two physically different quantities — a no-load ALIGNMENT
check and a delivered THICKNESS VARIATION. Rev C separates them, then makes the
structure stiff enough that neither is governed by the shaft.

Evidence classes: [G] given [M] measured [S] sourced [D] derived
                  [A] assumed [E] estimated [T] test-based [P] professional/vendor
Units: inch, pound-force, second. Millimetres are interface-only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# 0. Material and physical constants
# ---------------------------------------------------------------------------
# Standard handbook engineering constants. Tagged [A] deliberately: this module
# has not opened a mill certificate. They are adequate for a stiffness estimate
# and are NOT used for any allowable-stress or code claim.

E_STEEL = 29.0e6      # psi, carbon steel                              [A]
E_ALUM = 10.0e6       # psi, 6061-T6                                   [A]
E_PLY = 1.5e6         # psi, Baltic birch plywood, flatwise            [A]
RHO_STEEL = 0.284     # lb/in^3                                        [A]
RHO_ALUM = 0.098      # lb/in^3                                        [A]
RHO_BB = 0.0245       # lb/in^3, ~42 pcf Baltic birch                  [A]
RHO_MDF = 0.0278      # lb/in^3, ~48 pcf                               [A]
RHO_PHENOLIC = 0.0506  # lb/in^3                                       [A]
G_IN = 386.09         # in/s^2, standard gravity                       [S]

UHMW_ALLOW_PSI = 500.0  # long-term compressive working stress, conservative [A]


# ---------------------------------------------------------------------------
# 1. Rev C controlling parameters
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MechSpec:
    """Rev C drum-axis and precision parameters.

    Anything a builder must measure rather than trust is marked in `notes`.
    """

    # --- carried forward from Rev B geometry (unchanged machine envelope) ---
    capacity_width: float = 15.5        # [G]
    clear_between_sides: float = 16.5   # [G] inner span, the hard constraint
    side_thick: float = 0.75            # [M] measure the actual sheet
    drum_od: float = 5.0                # [G]
    drum_length: float = 15.75          # [G]

    # --- Rev C drum axis (was 3/4" shaft + MDF disc stack) ---
    shaft_od: float = 1.25              # [D] from the stiffness sweep
    shaft_length: float = 24.0          # [D] span + pulley + stub
    shell_od: float = 5.0               # [G] finished drum OD
    shell_wall: float = 0.25            # [D] 6061 tube wall
    plug_inset: float = 0.25            # [D] plug centroid inboard of drum end
    plug_thick: float = 1.5             # [D] bond + shaft grip length
    bearing_offset: float = 0.35        # [A] ball CL outboard of side face.
    #                                     VERIFY on the bearing you buy.
    roller_setbelow_ref: float = 0.030  # [G] hold-down rollers below drum OD

    # --- precision interfaces ---
    gib_clearance: float = 0.0015       # [D] target running clearance, gib set
    jack_thread_tpi: float = 28.0       # [G] 1/4-28 micro-adjust jack screw
    jack_arm_pivot_to_screw: float = 6.0   # [D] L1
    jack_arm_pivot_to_bearing: float = 1.25  # [D] L2

    # --- lift ---
    acme_major: float = 0.5             # [G] 1/2-10 Acme
    acme_tpi: float = 10.0              # [G]
    acme_thread_half_angle: float = 14.5  # [S] Acme form
    acme_friction: float = 0.15         # [A] bronze on steel, waxed
    handwheel_divisions: int = 40       # [D]

    # --- drive ---
    motor_rpm: float = 1725.0           # [G] nameplate
    motor_hp: float = 1.0               # [D] see CALC-C14 sizing note
    pulley_motor: float = 3.5           # [D] selected sheave
    pulley_drum: float = 5.0            # [D]

    # --- load bracket -------------------------------------------------------
    # Sanding normal force is the weakest input in the whole package. It is
    # bracketed, and every accuracy result is also expressed as an ALLOWABLE
    # force so the builder can work backwards from what the machine can hold.
    force_bracket: tuple = (10.0, 20.0, 40.0)   # [E] lbf total, drum on work
    force_reference: float = 20.0                # [E] used for reported values
    shaft_deflection_allowance: float = 0.001    # [D] shaft share of TV budget

    # --- specification split (the Rev C correction) ---
    aln_spec: float = 0.003             # [G] no-load alignment |A-B|
    tv_spec: float = 0.005              # [D] delivered thickness variation
    table_flat_spec: float = 0.003      # [D] over the 15.5" contact line
    drum_tir_spec: float = 0.0015       # [D] paper-on

    # --- duty / life targets ---
    bearing_life_hours: float = 5000.0  # [D]
    dust_duct_dia: float = 4.0          # [G]
    dust_transport_fpm: float = 4000.0  # [A] typical chip transport velocity
    hood_face_w: float = 16.5           # [D]
    hood_face_h: float = 5.0            # [D]

    # --- solo handling ---
    solo_lift_limit: float = 50.0       # [A] confirm with the builder

    notes: tuple = (
        "bearing_offset is the only drum-axis dimension that depends on a "
        "purchased part. Measure the flange bearing before drilling P-001.",
        "force_bracket is ESTIMATED. Accuracy results are therefore reported "
        "as allowable force, which is verifiable by test.",
    )


MECH = MechSpec()


# ---------------------------------------------------------------------------
# 2. Section properties and beam solutions
# ---------------------------------------------------------------------------


def i_round(d: float) -> float:
    """Second moment of area, solid round."""
    return math.pi * d ** 4 / 64.0


def i_tube(od: float, wall: float) -> float:
    idia = od - 2.0 * wall
    return math.pi * (od ** 4 - idia ** 4) / 64.0


def defl_two_point_center(w_total: float, span: float, a: float, e: float, i: float) -> float:
    """Simply supported span, two equal loads w_total/2 at `a` from each support.
    Returns deflection at mid-span.  d = P a (3L^2 - 4a^2) / (24 E I)
    """
    p = w_total / 2.0
    return p * a * (3.0 * span ** 2 - 4.0 * a ** 2) / (24.0 * e * i)


def defl_udl_center(w_per_in: float, span: float, e: float, i: float) -> float:
    """Simply supported, full-span uniform load. d = 5 w L^4 / (384 E I)."""
    return 5.0 * w_per_in * span ** 4 / (384.0 * e * i)


def defl_udl_central_patch(w_total: float, span: float, patch: float,
                           e: float, i: float, n: int = 4001) -> float:
    """Simply supported span, total load spread over a centered patch.

    Numeric double integration of M/EI with v(0)=v(L)=0. Used for the Rev B
    comparison case, where the load lands directly on the bare shaft.
    """
    dx = span / (n - 1)
    x0, x1 = (span - patch) / 2.0, (span + patch) / 2.0
    w_q = w_total / patch
    shear = w_total / 2.0
    moment = [0.0] * n
    for k in range(1, n):
        xk = (k - 1) * dx
        if x0 <= xk <= x1:
            shear -= w_q * dx
        moment[k] = moment[k - 1] + shear * dx
    slope = 0.0
    v = [0.0] * n
    for k in range(1, n):
        slope += moment[k - 1] / (e * i) * dx
        v[k] = v[k - 1] + slope * dx
    tilt = v[-1] / span
    return max(abs(v[k] - tilt * (k * dx)) for k in range(n))


# ---------------------------------------------------------------------------
# 3. Derived drum-axis geometry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AxisGeom:
    bearing_span: float
    shell_span: float
    plug_station: float
    shaft_overhang: float
    i_shaft: float
    i_shell: float
    ei_shaft: float
    ei_shell: float
    shell_id: float


def axis_geom(m: MechSpec = MECH) -> AxisGeom:
    span = m.clear_between_sides + 2.0 * m.side_thick + 2.0 * m.bearing_offset
    shell_span = m.drum_length - 2.0 * m.plug_inset
    plug_station = (span - shell_span) / 2.0
    i_sh = i_round(m.shaft_od)
    i_tb = i_tube(m.shell_od, m.shell_wall)
    return AxisGeom(
        bearing_span=span,
        shell_span=shell_span,
        plug_station=plug_station,
        shaft_overhang=(span - m.drum_length) / 2.0,
        i_shaft=i_sh,
        i_shell=i_tb,
        ei_shaft=E_STEEL * i_sh,
        ei_shell=E_ALUM * i_tb,
        shell_id=m.shell_od - 2.0 * m.shell_wall,
    )


AXIS = axis_geom(MECH)


def drum_crown(force: float, m: MechSpec = MECH, g: AxisGeom | None = None) -> dict[str, float]:
    """Load-induced crown of the Rev C drum, SERIES model.

    The abrasive load lands on the shell OD. The shell spans plug to plug. The
    plugs sit on the shaft, which spans bearing to bearing and sees the two plug
    reactions as point loads. Deflections add in series.

    No bonded-composite assumption is made: the shell is not glued to the shaft
    along its length, so claiming EI_shaft + EI_shell would overstate stiffness.
    """
    g = g or AXIS
    d_shaft = defl_two_point_center(force, g.bearing_span, g.plug_station,
                                    E_STEEL, g.i_shaft)
    d_shell = defl_udl_center(force / g.shell_span, g.shell_span, E_ALUM, g.i_shell)
    return {
        "shaft": d_shaft,
        "shell": d_shell,
        "total": d_shaft + d_shell,
        "share_shaft": d_shaft / (d_shaft + d_shell) if (d_shaft + d_shell) else 0.0,
    }


def drum_crown_revb(force: float, m: MechSpec = MECH) -> float:
    """Rev B comparison: bare 3/4" shaft, MDF disc stack non-structural.

    A stack of separately bored discs keyed to a shaft cannot be relied on for
    composite bending: the disc-to-disc interfaces slip. Treating the stack as
    non-structural is the defensible assumption.
    """
    span = m.clear_between_sides + 2.0 * m.side_thick + 2.0 * 0.55
    return defl_udl_central_patch(force, span, m.drum_length, E_STEEL, i_round(0.75))


def allowable_force(m: MechSpec = MECH, g: AxisGeom | None = None) -> float:
    """Sanding force that exactly consumes the shaft deflection allowance.

    Linear elastic, so this scales directly off the reference case.
    """
    ref = drum_crown(m.force_reference, m, g)["total"]
    return m.force_reference * m.shaft_deflection_allowance / ref


# ---------------------------------------------------------------------------
# 4. Accuracy budgets — the Rev C specification correction
# ---------------------------------------------------------------------------


def _budget(rows: list[tuple[str, float, str]]) -> dict[str, Any]:
    worst = sum(v for _, v, _ in rows)
    rss = math.sqrt(sum(v * v for _, v, _ in rows))
    return {
        "rows": [{"term": k, "value": v, "evidence": e} for k, v, e in rows],
        "worst_case": worst,
        "rss": rss,
    }


def alignment_budget(m: MechSpec = MECH) -> dict[str, Any]:
    """ALN — no-load alignment check |A-B| across the capacity width.

    This is a SETUP measurement: indicator at station A (drive) and station B
    (idler), drum stationary, paper on, no workpiece, no cut force. Deflection
    does not appear here because there is no load.
    """
    res = micro_adjust(m)
    b = _budget([
        ("Drum TIR, paper-on", m.drum_tir_spec, "T"),
        ("Micro-adjust setting resolution at work", res["at_work_15deg"], "D"),
        ("Indicator + stand repeatability", 0.0005, "A"),
        ("Drum straightness over 15.5 in", 0.0005, "T"),
    ])
    b["spec"] = m.aln_spec
    b["pass_worst"] = b["worst_case"] <= m.aln_spec
    b["pass_rss"] = b["rss"] <= m.aln_spec
    return b


def thickness_variation_budget(m: MechSpec = MECH, rev: str = "C") -> dict[str, Any]:
    """TV — delivered thickness variation across a 15.5 in board, under cut.

    This is what the user actually feels. It is necessarily larger than the
    alignment number, and Rev B was wrong to quote one figure for both.
    """
    if rev == "B":
        rows = [
            ("Alignment residual after setup", 0.003, "A"),
            ("Load-induced drum crown @20 lbf", drum_crown_revb(m.force_reference, m), "D"),
            ("Way/shoe X play, table rock", 0.020, "G"),
            ("Table flatness over contact line", 0.004, "G"),
            ("Lift backlash, unspecified", 0.005, "E"),
            ("Abrasive thickness variation", 0.002, "A"),
            ("Feed and handling", 0.001, "A"),
        ]
    else:
        rows = [
            ("Alignment residual after setup", m.aln_spec, "T"),
            ("Load-induced drum crown @20 lbf",
             drum_crown(m.force_reference, m)["total"], "D"),
            ("Way/gib X play, preloaded", m.gib_clearance, "D"),
            ("Table flatness over contact line", 0.002, "T"),
            ("Lift backlash, compression + lock", 0.0, "D"),
            ("Abrasive thickness variation", 0.002, "A"),
            ("Feed and handling", 0.001, "A"),
        ]
    b = _budget(rows)
    b["spec"] = m.tv_spec
    b["pass_worst"] = b["worst_case"] <= m.tv_spec
    b["pass_rss"] = b["rss"] <= m.tv_spec
    b["rev"] = rev
    return b


# ---------------------------------------------------------------------------
# 5. Component sizing
# ---------------------------------------------------------------------------


def micro_adjust(m: MechSpec = MECH, g: AxisGeom | None = None) -> dict[str, float]:
    """Idler-end parallelism micro-adjust: pivot plate + fine-thread jack screw.

    The drive bearing is the fixed pivot and the axis datum. The idler bearing
    rides a plate that rotates about a transverse pin; a jack screw at radius L1
    lifts the bearing at radius L2, so the mechanical reduction is L2/L1.
    """
    g = g or AXIS
    lead = 1.0 / m.jack_thread_tpi
    ratio = m.jack_arm_pivot_to_bearing / m.jack_arm_pivot_to_screw
    per_rev = lead * ratio
    at_work = per_rev * (m.capacity_width / g.bearing_span)
    return {
        "lead": lead,
        "ratio": ratio,
        "per_rev_at_bearing": per_rev,
        "per_rev_at_work": at_work,
        "at_work_30deg": at_work / 12.0,
        "at_work_15deg": at_work / 24.0,
        "required_selfalign_deg": math.degrees(math.atan(m.aln_spec / m.capacity_width)),
    }


def lift_screw(load_lbf: float, m: MechSpec = MECH) -> dict[str, Any]:
    """Power-screw statics for one of two 1/2-10 Acme lift screws.

    T = F dm/2 * (L + pi mu dm sec a) / (pi dm - mu L sec a)
    Self-locking when mu >= L / (pi dm).
    """
    pitch = 1.0 / m.acme_tpi
    dm = m.acme_major - pitch / 2.0
    lead = pitch
    mu = m.acme_friction
    sec_a = 1.0 / math.cos(math.radians(m.acme_thread_half_angle))
    f = load_lbf / 2.0
    torque = f * dm / 2.0 * (lead + math.pi * mu * dm * sec_a) / (
        math.pi * dm - mu * lead * sec_a)
    threshold = lead / (math.pi * dm)
    return {
        "pitch": pitch,
        "mean_dia": dm,
        "lead": lead,
        "load_per_screw": f,
        "torque_raise_lbf_in": torque,
        "self_locking": mu >= threshold,
        "selflock_threshold_mu": threshold,
        "travel_per_rev": lead,
        "resolution_per_division": lead / m.handwheel_divisions,
    }


def bearing_requirement(radial_lbf: float, rpm: float, m: MechSpec = MECH) -> dict[str, Any]:
    """Required basic dynamic capacity C for a target L10 life.

    L10_hours = (1e6 / (60 n)) (C/P)^3   ->   C = P (L10 * 60 n / 1e6)^(1/3)

    The result is a REQUIREMENT on the purchased insert. The actual C is [P]:
    read it from the manufacturer's table at order time.
    """
    hours = m.bearing_life_hours
    c_req = radial_lbf * (hours * 60.0 * rpm / 1.0e6) ** (1.0 / 3.0)
    return {
        "load_per_bearing": radial_lbf,
        "rpm": rpm,
        "life_hours": hours,
        "c_required": c_req,
        "evidence": "D requirement; actual C is [P] from vendor data",
    }


def drive_options(m: MechSpec = MECH) -> list[dict[str, Any]]:
    """Sheave combinations with drum RPM, surface speed, torque and belt pull."""
    out = []
    for dm_p, dd_p in ((3.0, 5.0), (3.5, 5.0), (4.0, 5.0), (3.0, 4.0), (4.0, 4.0)):
        rpm = m.motor_rpm * dm_p / dd_p
        sfpm = math.pi * m.drum_od / 12.0 * rpm
        torque = 5252.0 * m.motor_hp / rpm * 12.0     # lbf-in at the drum shaft
        belt_pull = torque / (dd_p / 2.0)
        out.append({
            "motor_sheave": dm_p,
            "drum_sheave": dd_p,
            "drum_rpm": rpm,
            "surface_fpm": sfpm,
            "torque_lbf_in": torque,
            "belt_pull_lbf": belt_pull,
            "selected": abs(dm_p - m.pulley_motor) < 1e-9 and abs(dd_p - m.pulley_drum) < 1e-9,
        })
    return out


def belt_length(center_distance: float, d_small: float, d_large: float) -> float:
    """Approximate V-belt pitch length."""
    c = center_distance
    return 2.0 * c + math.pi * (d_large + d_small) / 2.0 + (d_large - d_small) ** 2 / (4.0 * c)


def unbalance_allowance(rpm: float, force_limit_lbf: float = 1.0) -> dict[str, float]:
    """Allowable residual static unbalance U = m*r for a dynamic force limit.

    F = (U/g) * omega^2  ->  U = F * g / omega^2
    """
    omega = rpm * 2.0 * math.pi / 60.0
    u_lb_in = force_limit_lbf * G_IN / omega ** 2
    return {
        "rpm": rpm,
        "force_limit": force_limit_lbf,
        "u_lb_in": u_lb_in,
        "u_oz_in": u_lb_in * 16.0,
        "tape_grams_at_r2_5": u_lb_in / 2.5 * 453.592,
    }


def critical_speed(m: MechSpec = MECH, g: AxisGeom | None = None,
                   mass_lb: float | None = None) -> dict[str, float]:
    """First bending natural frequency, conservative.

    Uses the SHAFT alone for EI while carrying the FULL drum mass — a deliberate
    lower bound on frequency. f1 = (pi / 2 L^2) sqrt(EI / m')
    """
    g = g or AXIS
    mass_lb = mass_lb if mass_lb is not None else drum_mass(m)["total"]
    m_prime = (mass_lb / g.bearing_span) / G_IN
    f1 = (math.pi / 2.0) / g.bearing_span ** 2 * math.sqrt(g.ei_shaft / m_prime)
    op_hz = drum_rpm(m) / 60.0
    return {"f1_hz": f1, "operating_hz": op_hz, "ratio": f1 / op_hz if op_hz else 0.0}


def drum_rpm(m: MechSpec = MECH) -> float:
    return m.motor_rpm * m.pulley_motor / m.pulley_drum


def surface_fpm(m: MechSpec = MECH) -> float:
    return math.pi * m.drum_od / 12.0 * drum_rpm(m)


def dust_requirement(m: MechSpec = MECH) -> dict[str, float]:
    area_ft2 = math.pi * (m.dust_duct_dia / 12.0) ** 2 / 4.0
    cfm = area_ft2 * m.dust_transport_fpm
    hood_ft2 = m.hood_face_w * m.hood_face_h / 144.0
    return {
        "duct_area_ft2": area_ft2,
        "required_cfm": cfm,
        "hood_face_ft2": hood_ft2,
        "hood_face_fpm": cfm / hood_ft2 if hood_ft2 else 0.0,
    }


def way_bearing_stress(load_lbf: float, way_width: float = 2.5,
                       shoe_height: float = 4.0, ways: int = 2) -> dict[str, float]:
    area = ways * way_width * shoe_height
    sigma = load_lbf / area
    return {
        "contact_area_in2": area,
        "stress_psi": sigma,
        "allowable_psi": UHMW_ALLOW_PSI,
        "margin": UHMW_ALLOW_PSI / sigma if sigma else 0.0,
    }


# ---------------------------------------------------------------------------
# 6. Mass and stability
# ---------------------------------------------------------------------------


def drum_mass(m: MechSpec = MECH, g: AxisGeom | None = None) -> dict[str, float]:
    g = g or AXIS
    shell = math.pi / 4.0 * (m.shell_od ** 2 - g.shell_id ** 2) * m.drum_length * RHO_ALUM
    shaft = math.pi / 4.0 * m.shaft_od ** 2 * m.shaft_length * RHO_STEEL
    plugs = 2.0 * math.pi / 4.0 * (g.shell_id ** 2 - m.shaft_od ** 2) * m.plug_thick * RHO_ALUM
    return {"shell": shell, "shaft": shaft, "plugs": plugs,
            "total": shell + shaft + plugs}


def drum_mass_option_b(m: MechSpec = MECH) -> float:
    """Option B disc-stack drum mass, for the no-lathe alternative."""
    return math.pi / 4.0 * m.drum_od ** 2 * m.drum_length * RHO_MDF


def module_masses(m: MechSpec = MECH) -> list[dict[str, Any]]:
    """Handling masses against the solo lift limit."""
    def box(t, w, l, rho, q=1):
        return t * w * l * rho * q

    side = box(0.75, 22, 30, RHO_BB)
    base = box(0.75, 22, 18.0, RHO_BB)
    skins = box(0.5, 22, 16, RHO_BB, 2)
    ribs = box(0.5, 1.0, 16, RHO_BB, 6)
    wear = box(0.5, 22, 16, RHO_PHENOLIC)
    table = skins + ribs + wear
    drum = drum_mass(m)["total"]
    frame = 2 * side + base + 6.0
    rows = [
        ("Side panel P-001L or R", side),
        ("Base deck P-002", base),
        ("Table assembly A-TABLE", table),
        ("Drum assembly A-DRUM", drum),
        ("Frame subassembly A-FRAME", frame),
        ("Motor (nameplate class)", 30.0),
    ]
    out = []
    for name, mass in rows:
        out.append({
            "module": name,
            "mass_lb": mass,
            "solo_ok": mass <= m.solo_lift_limit,
            "limit_lb": m.solo_lift_limit,
        })
    out.append({
        "module": "MACHINE TOTAL (assembled)",
        "mass_lb": frame + table + drum + 30.0,
        "solo_ok": False,
        "limit_lb": m.solo_lift_limit,
    })
    return out


def stability(m: MechSpec = MECH, footprint_depth: float = 22.0,
              cg_height: float = 15.0) -> dict[str, float]:
    total = module_masses(m)[-1]["mass_lb"]
    tip_force = total * (footprint_depth / 2.0) / cg_height
    feed_force = m.force_reference * 0.4      # [E] friction share of normal force
    return {
        "machine_lb": total,
        "footprint_depth": footprint_depth,
        "cg_height": cg_height,
        "tip_force_lbf": tip_force,
        "feed_force_lbf": feed_force,
        "margin": tip_force / feed_force if feed_force else 0.0,
    }


# ---------------------------------------------------------------------------
# 7. Calculation register
# ---------------------------------------------------------------------------


def mech_calculations(m: MechSpec = MECH) -> list[dict[str, Any]]:
    """The Rev C calculation register. Every row is recomputed on import."""
    g = axis_geom(m)
    crown = drum_crown(m.force_reference, m, g)
    crown_b = drum_crown_revb(m.force_reference, m)
    f_allow = allowable_force(m, g)
    aln = alignment_budget(m)
    tv_c = thickness_variation_budget(m, "C")
    tv_b = thickness_variation_budget(m, "B")
    adj = micro_adjust(m, g)
    masses = drum_mass(m, g)
    lift = lift_screw(module_masses(m)[2]["mass_lb"] + 8.0 + 20.0, m)
    brg = bearing_requirement((masses["total"] + m.force_reference) / 2.0,
                              drum_rpm(m), m)
    crit = critical_speed(m, g)
    dust = dust_requirement(m)
    stab = stability(m)
    stress = way_bearing_stress(module_masses(m)[2]["mass_lb"] + 28.0)
    unb = unbalance_allowance(drum_rpm(m), 1.0)
    sel = [d for d in drive_options(m) if d["selected"]][0]

    rows: list[dict[str, Any]] = [
        {
            "id": "CALC-C01",
            "question": "Does the Rev B 3/4 in shaft hold the accuracy spec?",
            "method": "Simply supported beam, load patch over drum, numeric M/EI",
            "inputs": f"d=0.75 in, I={i_round(0.75):.5f} in^4, E={E_STEEL:.2g} psi, "
                      f"span={m.clear_between_sides + 2 * m.side_thick + 1.1:.3f} in, W=20 lbf [E]",
            "equation": "double integration of M(x)/EI, v(0)=v(L)=0",
            "result": f"{crown_b * 1000:.2f} mil crown at 20 lbf",
            "criterion": f"<= {m.shaft_deflection_allowance * 1000:.0f} mil",
            "margin": f"allowable force only {m.force_reference * m.shaft_deflection_allowance / crown_b:.2f} lbf",
            "verdict": "FAIL — governs Rev C redesign",
            "evidence": "D on E-class load",
        },
        {
            "id": "CALC-C02",
            "question": "Rev C load-induced drum crown",
            "method": "Series model: shell plug-to-plug, then shaft bearing-to-bearing",
            "inputs": f"shaft {m.shaft_od:g} in (I={g.i_shaft:.4f}), shell {m.shell_od:g}x{m.shell_wall:g} "
                      f"(I={g.i_shell:.3f}), span={g.bearing_span:.3f}, a={g.plug_station:.3f}",
            "equation": "d = P a (3L^2-4a^2)/(24EI) + 5 w Ls^4/(384 E I)",
            "result": f"{crown['total'] * 1000:.3f} mil at 20 lbf "
                      f"(shaft {crown['share_shaft'] * 100:.0f}% of it)",
            "criterion": f"<= {m.shaft_deflection_allowance * 1000:.0f} mil",
            "margin": f"{crown_b / crown['total']:.0f}x stiffer than Rev B",
            "verdict": "PASS",
            "evidence": "D",
        },
        {
            "id": "CALC-C03",
            "question": "What sanding force may the drum axis carry?",
            "method": "Linear scaling of CALC-C02 to the allowance",
            "inputs": f"allowance {m.shaft_deflection_allowance:.4f} in",
            "equation": "F_allow = F_ref * allowance / d_ref",
            "result": f"{f_allow:.1f} lbf",
            "criterion": "must exceed realistic hand-feed force",
            "margin": f"{f_allow / m.force_reference:.1f}x the 20 lbf reference",
            "verdict": "PASS — no longer structure-limited",
            "evidence": "D",
        },
        {
            "id": "CALC-C04",
            "question": "Alignment budget, no load (ALN)",
            "method": "Worst-case sum and RSS of setup terms",
            "inputs": "; ".join(f"{r['term']} {r['value'] * 1000:.2f} mil" for r in aln["rows"]),
            "equation": "sum and sqrt(sum of squares)",
            "result": f"worst {aln['worst_case'] * 1000:.2f} mil, RSS {aln['rss'] * 1000:.2f} mil",
            "criterion": f"|A-B| <= {m.aln_spec * 1000:.0f} mil",
            "margin": f"RSS uses {aln['rss'] / m.aln_spec * 100:.0f}% of spec",
            "verdict": "PASS" if aln["pass_worst"] else "PASS on RSS, tight on worst case",
            "evidence": "D",
        },
        {
            "id": "CALC-C05",
            "question": "Delivered thickness variation, Rev B vs Rev C (TV)",
            "method": "Error budget under cut load across 15.5 in",
            "inputs": "see G-003 budget tables",
            "equation": "sum and RSS",
            "result": f"Rev B RSS {tv_b['rss'] * 1000:.1f} mil -> Rev C RSS {tv_c['rss'] * 1000:.1f} mil",
            "criterion": f"TV <= {m.tv_spec * 1000:.0f} mil",
            "margin": f"{tv_b['rss'] / tv_c['rss']:.1f}x improvement",
            "verdict": "PASS on RSS" if tv_c["pass_rss"] else "FAIL",
            "evidence": "D",
        },
        {
            "id": "CALC-C06",
            "question": "Is 0.003 in a legitimate single specification?",
            "method": "Compare the two budgets that Rev B collapsed into one number",
            "inputs": f"ALN RSS {aln['rss'] * 1000:.2f} mil vs TV RSS {tv_c['rss'] * 1000:.2f} mil",
            "equation": "n/a — specification audit",
            "result": "Two different quantities; TV cannot equal ALN",
            "criterion": "one spec per measurable quantity",
            "margin": "n/a",
            "verdict": "Rev B spec DEFECT — split into ALN-01 and TV-01",
            "evidence": "D",
        },
        {
            "id": "CALC-C07",
            "question": "Parallelism micro-adjust resolution",
            "method": "Fine-thread jack on a pivot plate, reduction L2/L1",
            "inputs": f"1/4-{m.jack_thread_tpi:g} lead {adj['lead']:.5f} in, "
                      f"L1={m.jack_arm_pivot_to_screw:g}, L2={m.jack_arm_pivot_to_bearing:g}",
            "equation": "rise = lead x L2/L1; at work x capacity/span",
            "result": f"{adj['per_rev_at_work'] * 1000:.2f} mil/rev at the work; "
                      f"{adj['at_work_15deg'] * 1000:.3f} mil per 15 deg",
            "criterion": f"resolution <= 1/5 of {m.aln_spec * 1000:.0f} mil",
            "margin": f"{m.aln_spec / adj['at_work_15deg']:.0f}x finer than spec",
            "verdict": "PASS",
            "evidence": "D",
        },
        {
            "id": "CALC-C08",
            "question": "Required bearing self-aligning capability",
            "method": "Angle subtended by the alignment spec",
            "inputs": f"{m.aln_spec:g} in over {m.capacity_width:g} in",
            "equation": "atan(spec / width)",
            "result": f"{adj['required_selfalign_deg']:.4f} deg",
            "criterion": "within the insert's static misalignment rating",
            "margin": "trivial for any spherical-seat insert",
            "verdict": "PASS — confirm rating [P]",
            "evidence": "D",
        },
        {
            "id": "CALC-C09",
            "question": "Lift screw torque and back-drive behaviour",
            "method": "Power-screw statics, Acme form",
            "inputs": f"dm={lift['mean_dia']:.3f} in, lead={lift['lead']:.3f} in, "
                      f"mu={m.acme_friction:g} [A], load {lift['load_per_screw']:.1f} lbf/screw",
            "equation": "T = F dm/2 (L + pi mu dm sec a)/(pi dm - mu L sec a)",
            "result": f"{lift['torque_raise_lbf_in']:.2f} lbf-in per screw to raise",
            "criterion": f"self-locking requires mu >= {lift['selflock_threshold_mu']:.4f}",
            "margin": f"mu {m.acme_friction:g} vs {lift['selflock_threshold_mu']:.4f}",
            "verdict": "PASS — self-locking, will not back-drive",
            "evidence": "D on A-class friction",
        },
        {
            "id": "CALC-C10",
            "question": "Lift resolution at the handwheel",
            "method": "Lead divided by graduations",
            "inputs": f"lead {lift['lead']:.3f} in, {m.handwheel_divisions} divisions",
            "equation": "lead / divisions",
            "result": f"{lift['resolution_per_division'] * 1000:.2f} mil per division",
            "criterion": f"<= finish pass {1.0:.0f} mil is not required; must be readable",
            "margin": "one division is a legible finish increment",
            "verdict": "PASS",
            "evidence": "D",
        },
        {
            "id": "CALC-C11",
            "question": "Required bearing dynamic capacity",
            "method": "ISO-form L10 life inverted for C",
            "inputs": f"P={brg['load_per_bearing']:.1f} lbf, n={brg['rpm']:.0f} rpm, "
                      f"L10={brg['life_hours']:.0f} h",
            "equation": "C = P (L10 x 60 n / 1e6)^(1/3)",
            "result": f"C >= {brg['c_required']:.0f} lbf",
            "criterion": "vendor C must exceed this",
            "margin": "specify by requirement, not by appearance",
            "verdict": "REQUIREMENT — confirm C [P]",
            "evidence": "D",
        },
        {
            "id": "CALC-C12",
            "question": "Drum speed and surface speed at the selected sheaves",
            "method": "Ratio and circumference",
            "inputs": f"{m.motor_rpm:g} rpm, {m.pulley_motor:g} in / {m.pulley_drum:g} in",
            "equation": "n = n_m d_m/d_d ; sfpm = pi D n / 12",
            "result": f"{sel['drum_rpm']:.0f} rpm, {sel['surface_fpm']:.0f} sfpm",
            "criterion": "1200-2000 sfpm band for wood [A]",
            "margin": f"belt pull {sel['belt_pull_lbf']:.1f} lbf at {m.motor_hp:g} hp",
            "verdict": "PASS — see M-102 for the full option table",
            "evidence": "D",
        },
        {
            "id": "CALC-C13",
            "question": "Allowable residual drum unbalance",
            "method": "Rotating force from static unbalance",
            "inputs": f"{unb['rpm']:.0f} rpm, force limit {unb['force_limit']:.1f} lbf",
            "equation": "U = F g / omega^2",
            "result": f"U <= {unb['u_oz_in']:.2f} oz-in",
            "criterion": "1 lbf rotating force at the bearings",
            "margin": f"~{unb['tape_grams_at_r2_5']:.1f} g of tape at r=2.5 in is the whole allowance",
            "verdict": "Balance by knife-edge test, record [T]",
            "evidence": "D",
        },
        {
            "id": "CALC-C14",
            "question": "First bending critical speed",
            "method": "Uniform simply supported beam, shaft EI with full drum mass",
            "inputs": f"EI={g.ei_shaft:.3g} lb-in^2, m={drum_mass(m)['total']:.1f} lb, "
                      f"L={g.bearing_span:.3f} in",
            "equation": "f1 = (pi/2L^2) sqrt(EI/m')",
            "result": f"f1 >= {crit['f1_hz']:.0f} Hz vs {crit['operating_hz']:.1f} Hz operating",
            "criterion": "f1 >= 2x operating",
            "margin": f"{crit['ratio']:.0f}x",
            "verdict": "PASS — conservative lower bound",
            "evidence": "D",
        },
        {
            "id": "CALC-C15",
            "question": "Dust extraction requirement",
            "method": "Duct area x transport velocity; hood face velocity",
            "inputs": f"{m.dust_duct_dia:g} in duct, {m.dust_transport_fpm:.0f} fpm [A]",
            "equation": "CFM = A V",
            "result": f"{dust['required_cfm']:.0f} CFM; hood face {dust['hood_face_fpm']:.0f} fpm",
            "criterion": "collector must deliver this AT THE MACHINE",
            "margin": "a shop vac will not do this",
            "verdict": "REQUIREMENT on the collector",
            "evidence": "D",
        },
        {
            "id": "CALC-C16",
            "question": "Way bearing stress on the UHMW",
            "method": "Projected contact area",
            "inputs": f"{stress['contact_area_in2']:.1f} in^2 total",
            "equation": "sigma = P / A",
            "result": f"{stress['stress_psi']:.1f} psi",
            "criterion": f"<= {stress['allowable_psi']:.0f} psi long-term [A]",
            "margin": f"{stress['margin']:.0f}x",
            "verdict": "PASS — the way is precision-limited, not stress-limited",
            "evidence": "D",
        },
        {
            "id": "CALC-C17",
            "question": "Tipping stability against feed force",
            "method": "Restoring vs overturning moment about the base edge",
            "inputs": f"{stab['machine_lb']:.0f} lb, footprint {stab['footprint_depth']:g} in, "
                      f"CG {stab['cg_height']:g} in [E]",
            "equation": "F_tip = W (d/2) / h",
            "result": f"{stab['tip_force_lbf']:.0f} lbf to tip vs {stab['feed_force_lbf']:.0f} lbf feed",
            "criterion": ">= 3x margin",
            "margin": f"{stab['margin']:.0f}x",
            "verdict": "PASS — still bolt or cleat the stand",
            "evidence": "D on E-class CG",
        },
        {
            "id": "CALC-C18",
            "question": "Solo handling of every module",
            "method": "Volume x density per module vs lift limit",
            "inputs": f"limit {m.solo_lift_limit:g} lbf [A]",
            "equation": "m = V rho",
            "result": "; ".join(f"{r['module'].split()[0]} {r['mass_lb']:.0f} lb"
                                for r in module_masses(m)[:5]),
            "criterion": f"each module <= {m.solo_lift_limit:g} lb",
            "margin": "assembled machine must be built in place",
            "verdict": "PASS per module; assembled total exceeds the limit by design",
            "evidence": "D",
        },
    ]
    return rows


def mech_decisions() -> list[dict[str, str]]:
    m, g = MECH, AXIS
    crown = drum_crown(m.force_reference)
    return [
        {"id": "D-040",
         "decision": "Split the single 0.003 in spec into ALN-01 (no-load alignment) "
                     "and TV-01 (delivered thickness variation, 0.005 in)",
         "reason": "Rev B quoted one number for two different measurable quantities. "
                   "The error budgets differ by a factor of two and no machine can "
                   "make them equal.",
         "evidence": "CALC-C04, CALC-C05, CALC-C06", "rev": "C"},
        {"id": "D-041",
         "decision": f"Drum axis rebuilt: {m.shaft_od:g} in shaft, structural "
                     f"{m.shell_od:g} in x {m.shell_wall:g} in 6061 shell, plugs "
                     f"{m.plug_inset:g} in inboard, bearings {m.bearing_offset:g} in off the side face",
         "reason": f"The 3/4 in shaft spent the whole accuracy allowance at 4.25 lbf. "
                   f"Rev C crowns {crown['total'] * 1000:.2f} mil at 20 lbf, "
                   f"{drum_crown_revb(20.0) / crown['total']:.0f}x stiffer.",
         "evidence": "CALC-C01, CALC-C02, CALC-C03", "rev": "C"},
        {"id": "D-042",
         "decision": "Adjustable tapered gib on the idler way replaces the 0.020 in "
                     "sliding clearance; target 0.0015 in running clearance",
         "reason": "Way play was the largest single term in the Rev B thickness budget.",
         "evidence": "CALC-C05", "rev": "C"},
        {"id": "D-043",
         "decision": "Idler bearing on a pivot plate with a 1/4-28 jack screw, "
                     "6.00 in / 1.25 in arm reduction",
         "reason": "Parallelism must be settable finer than the spec. Resolution is "
                   "0.26 mil per 15 deg at the work.",
         "evidence": "CALC-C07", "rev": "C"},
        {"id": "D-044",
         "decision": "Lift screws carry the table in compression; always approach the "
                     "setting from below and lock the ways before cutting",
         "reason": "Removes screw backlash from the budget without an anti-backlash nut. "
                   "Screws are self-locking, so the table cannot drift down.",
         "evidence": "CALC-C09", "rev": "C"},
        {"id": "D-045",
         "decision": "Bearings specified by required dynamic capacity C, not by bore alone",
         "reason": "Rev B named a bearing by appearance. Rev C states the requirement so "
                   "any vendor's data can be checked against it.",
         "evidence": "CALC-C11", "rev": "C"},
        {"id": "D-046",
         "decision": f"Re-sheave to {m.pulley_motor:g} in / {m.pulley_drum:g} in "
                     f"-> {drum_rpm(m):.0f} rpm, {surface_fpm(m):.0f} sfpm",
         "reason": "Rev B ran 1355 sfpm, low for finish work. The option table lets the "
                   "builder trade finish against unbalance sensitivity.",
         "evidence": "CALC-C12, CALC-C13", "rev": "C"},
        {"id": "D-047",
         "decision": "Keep the MDF disc-stack drum as documented Option B",
         "reason": "A shop without lathe access cannot make the shell and plugs. Option B "
                   "is honest about its accuracy penalty rather than hidden.",
         "evidence": "CALC-C01", "rev": "C"},
        {"id": "D-048",
         "decision": "Housed dado plus through-bolts with backing washers for the frame, "
                     "not screws alone",
         "reason": "User standard: never rely on glue alone for primary structure, and "
                   "a machine frame must be re-tightenable and knock-down.",
         "evidence": "joinery-and-tolerance-standards.md hierarchy item 4", "rev": "C"},
    ]


def report() -> str:
    m = MECH
    g = axis_geom(m)
    lines = [
        "WALTER DS-16 — Rev C mechanics report",
        f"  bearing span         {g.bearing_span:.3f} in",
        f"  shell span           {g.shell_span:.3f} in",
        f"  shaft point loads at {g.plug_station:.3f} in from bearings",
        f"  drum mass            {drum_mass(m)['total']:.2f} lb",
        f"  drum rpm / sfpm      {drum_rpm(m):.0f} / {surface_fpm(m):.0f}",
        "",
    ]
    for c in mech_calculations(m):
        lines.append(f"{c['id']}  {c['question']}")
        lines.append(f"    result    {c['result']}")
        lines.append(f"    criterion {c['criterion']}")
        lines.append(f"    verdict   {c['verdict']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
