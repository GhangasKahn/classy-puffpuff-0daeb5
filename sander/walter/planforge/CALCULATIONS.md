# WALTER calculations — WOODWRIGHT PLANFORGE

Controlling units: inches. These identities are [D] arithmetic from `walter_kernel.py`.
They are not coupon tests and not a PE analysis.

## CAL-001 Drum speed
`drum_rpm = motor_rpm × pulley_mot / pulley_drm`
= 1725 × 3.00 / 4.75 = **1089.47 r/min**

## CAL-002 Surface speed
`sfm = π × drum_od × drum_rpm / 12`
= π × 5.00 × 1089.47 / 12 = **1426.1 ft/min**

## CAL-003 Feed (at 30 r/min roller)
`feed_fpm = π × roller_od / 12 × 30`
= π × 2.00 / 12 × 30 = **15.71 ft/min**
PWM target band 0–16 FPM [G].

## CAL-004 Elevation
`pitch = 1 / acme_tpi = 1/6 = 0.1667 in/rev` on ¾-6 Acme.
Travel 4.50 in [G].

## CAL-005 Face gap
`(inner_w − drum_face) / 2 = (16.50 − 16.00) / 2 = 0.25 in` each side.

## Limitations
Do not treat these as allowable loads, heat-build, or tracking guarantees.
Q02 / Q04 / Q09 are the shop tests. Electrical FLA is [P] from the nameplate.
