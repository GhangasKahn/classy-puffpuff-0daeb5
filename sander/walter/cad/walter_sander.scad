// WALTER — 16" closed-frame drum thickness sander
// Parametric shop-build CAD. Units: millimetres.
// Numbers come from parameters.scad (generated from walter_kernel.py).
//
//   python3 scripts/gen_walter_cad.py
//   openscad -o walter_iso.png --imgsize=1600,1000 --autocenter --viewall walter_sander.scad
//
// Lineage: Ron Walters / ShopNotes #86 problems, redesigned.
// This is an original engineering model — not a copy of copyrighted magazine drawings.

$fn = 48;
include <parameters.scad>

show_hood    = true;
show_belt    = true;
show_motor   = true;
show_guard   = true;
show_stand   = false;
cutaway      = false;   // hide drive-side wall to reveal drum

idle_outer_x  = 0;
idle_inner_x  = wall_t;
drive_inner_x = wall_t + inner_w;
drive_outer_x = drive_inner_x + wall_t;
drum_gap      = (inner_w - drum_face) / 2;
drum_x0       = idle_inner_x + drum_gap;
opening       = opening_default;
table_top_z   = drum_z - drum_od/2 - opening;
platen_len    = platen_y1 - platen_y0;
roller_y_out  = roller_y_in + roller_cd;
acme_x        = (idle_inner_x + drive_inner_x) / 2;
motor_x       = drive_outer_x + inch(0.25);
pulley_mot_d  = pulley_mot;
pulley_drm_d  = pulley_drm;

c_ply    = [0.82, 0.72, 0.52];
c_ply2   = [0.72, 0.62, 0.44];
c_steel  = [0.45, 0.48, 0.50];
c_shaft  = [0.70, 0.72, 0.74];
c_drum   = [0.55, 0.48, 0.38];
c_hdpe   = [0.88, 0.90, 0.92];
c_belt   = [0.18, 0.18, 0.20];
c_motor  = [0.12, 0.12, 0.13];
c_abr    = [0.62, 0.42, 0.22];
c_hood   = [0.35, 0.38, 0.36];
c_uhmw   = [0.92, 0.93, 0.94];

module ply_box(x, y, z, dx, dy, dz, col=c_ply) {
  color(col) translate([x, y, z]) cube([dx, dy, dz]);
}

module tube(od, id, h) {
  difference() {
    cylinder(h=h, d=od);
    translate([0,0,-1]) cylinder(h=h+2, d=id);
  }
}

module flange_bearing(bore=inch(0.75)) {
  color(c_steel) {
    hull() {
      for (s=[-1,1]) translate([0, s*inch(1.85), 0])
        cylinder(h=inch(0.55), d=inch(1.1));
    }
    cylinder(h=inch(0.55), d=inch(2.85));
    translate([0,0,-inch(0.15)]) cylinder(h=inch(0.85), d=inch(1.85));
  }
}

module frame() {
  // base
  ply_box(0, 0, 0, base_x, base_y, base_t, c_ply2);
  // rails under base
  ply_box(inch(0.75), inch(1.0), -inch(1.50), inch(1.50), base_y-inch(2), inch(1.50), c_ply2);
  ply_box(base_x-inch(2.25), inch(1.0), -inch(1.50), inch(1.50), base_y-inch(2), inch(1.50), c_ply2);

  // idle wall (doubled 3/4")
  if (true)
    ply_box(idle_outer_x, 0, base_t, wall_t, base_y, wall_h-base_t);

  // drive wall
  if (!cutaway)
    ply_box(drive_inner_x, 0, base_t, wall_t, base_y, wall_h-base_t);

  // stretchers
  ply_box(idle_inner_x, inch(1.0), base_t, inner_w, inch(1.50), inch(3.50), c_ply2);
  ply_box(idle_inner_x, base_y-inch(2.5), base_t, inner_w, inch(1.50), inch(3.50), c_ply2);

  // steel bearing plates on inner faces
  color(c_steel) {
    translate([idle_inner_x, drum_y-inch(3), drum_z-inch(3)])
      cube([inch(0.25), inch(6), inch(6)]);
    if (!cutaway)
      translate([drive_inner_x-inch(0.25), drum_y-inch(3), drum_z-inch(3)])
        cube([inch(0.25), inch(6), inch(6)]);
  }
}

module drum() {
  translate([drum_x0, drum_y, drum_z]) rotate([0,90,0]) {
    color(c_drum) cylinder(h=drum_face, d=drum_od);
    color(c_abr)  tube(drum_od+inch(0.06), drum_od-0.2, drum_face);
    // end bells
    color(c_steel) {
      translate([0,0,-inch(0.125)]) cylinder(h=inch(0.125), d=drum_od+inch(0.05));
      translate([0,0,drum_face])    cylinder(h=inch(0.125), d=drum_od+inch(0.05));
    }
  }
  // shaft
  color(c_shaft)
    translate([shaft_x0, drum_y, drum_z]) rotate([0,90,0])
      cylinder(h=shaft_len, d=shaft_d);

  // drum pulley (drive end, outboard of wall)
  color(c_steel)
    translate([drive_outer_x+inch(0.20), drum_y, drum_z]) rotate([0,90,0])
      cylinder(h=pulley_t, d=pulley_drm_d);

  // bearings
  translate([idle_inner_x+inch(0.05), drum_y, drum_z]) rotate([0,90,0])
    flange_bearing();
  if (!cutaway)
    translate([drive_inner_x+inch(0.10), drum_y, drum_z]) rotate([0,-90,0])
      flange_bearing();
}

module table_and_conveyor() {
  // platen
  ply_box(idle_inner_x+inch(0.12), platen_y0, table_top_z-table_t-uhmw_t,
          inner_w-inch(0.24), platen_len, table_t, c_ply);
  // UHMW face
  color(c_uhmw)
    translate([idle_inner_x+inch(0.12), platen_y0, table_top_z-uhmw_t])
      cube([inner_w-inch(0.24), platen_len, uhmw_t]);

  // side rails (slide in dados)
  ply_box(idle_inner_x-inch(0.38), platen_y0+inch(1), table_top_z-inch(2.25),
          inch(0.50), platen_len-inch(2), inch(2.00), c_ply2);
  ply_box(drive_inner_x-inch(0.12), platen_y0+inch(1), table_top_z-inch(2.25),
          inch(0.50), platen_len-inch(2), inch(2.00), c_ply2);

  // rollers
  for (y=[roller_y_in, roller_y_out]) {
    color(c_steel)
      translate([idle_inner_x+inch(0.12), y, table_top_z-roller_od/2])
        rotate([0,90,0]) cylinder(h=inner_w-inch(0.24), d=roller_od);
    color(c_shaft)
      translate([idle_outer_x-inch(0.5), y, table_top_z-roller_od/2])
        rotate([0,90,0]) cylinder(h=drive_outer_x+inch(1.0), d=roller_shaft);
  }

  if (show_belt) {
    color(c_belt) {
      // top span
      translate([idle_inner_x+inch(0.15), roller_y_in, table_top_z])
        cube([inner_w-inch(0.30), roller_cd, inch(0.08)]);
      // bottom span
      translate([idle_inner_x+inch(0.15), roller_y_in, table_top_z-roller_od-inch(0.08)])
        cube([inner_w-inch(0.30), roller_cd, inch(0.08)]);
    }
  }

  // Acme screws
  color(c_steel)
    for (y=acme_y)
      translate([acme_x, y, inch(2.0)])
        cylinder(h=inch(12.0), d=acme_d);
}

module motor_pack() {
  if (!show_motor) return;
  color(c_motor)
    translate([motor_x, motor_y, motor_z]) rotate([0,90,0])
      cylinder(h=motor_len, d=motor_od);
  // motor pulley
  color(c_steel)
    translate([drive_outer_x+inch(0.20), motor_y, motor_z]) rotate([0,90,0])
      cylinder(h=pulley_t, d=pulley_mot_d);
  // V-belt (simplified torus-ish loop)
  if (show_belt) {
    color([0.12,0.12,0.12])
      hull() {
        translate([drive_outer_x+inch(0.55), drum_y, drum_z])
          rotate([0,90,0]) cylinder(h=inch(0.5), d=pulley_drm_d+inch(0.3));
        translate([drive_outer_x+inch(0.55), motor_y, motor_z])
          rotate([0,90,0]) cylinder(h=inch(0.5), d=pulley_mot_d+inch(0.3));
      }
  }
  // hinged mount plate
  color(c_steel)
    translate([drive_outer_x-inch(0.12), motor_y-inch(4), inch(1.0)])
      cube([inch(0.25), inch(8.5), inch(7.5)]);
}

module hood() {
  if (!show_hood) return;
  color(c_hood, 0.85) {
    // inverted U over drum
    translate([idle_inner_x+inch(0.08), drum_y-inch(4.2), drum_z+inch(0.4)])
      cube([inner_w-inch(0.16), inch(8.4), hood_t]);
    translate([idle_inner_x+inch(0.08), drum_y-inch(4.2), drum_z-inch(1.2)])
      cube([hood_t, inch(8.4), inch(1.6)]);
    if (!cutaway)
      translate([drive_inner_x-hood_t-inch(0.08), drum_y-inch(4.2), drum_z-inch(1.2)])
        cube([hood_t, inch(8.4), inch(1.6)]);
    // back panel + port
    translate([idle_inner_x+inch(0.08), drum_y+inch(4.0), drum_z-inch(1.2)])
      cube([inner_w-inch(0.16), hood_t, inch(2.8)]);
  }
  color(c_steel)
    translate([acme_x, drum_y+inch(4.1), drum_z+inch(0.6)]) rotate([-90,0,0])
      tube(port_d+inch(0.15), port_d-inch(0.10), inch(2.2));
}

module belt_guard() {
  if (!show_guard || cutaway) return;
  color(c_ply, 0.7)
    translate([drive_outer_x+inch(0.05), drum_y-inch(6), inch(1.0)])
      cube([inch(2.20), inch(16.5), inch(16.5)]);
}

module gearmotor() {
  // 24V conveyor drive on idle-side outfeed roller
  color(c_motor)
    translate([idle_outer_x-inch(3.2), roller_y_out, table_top_z-roller_od/2-inch(0.5)])
      cube([inch(3.0), inch(3.0), inch(3.0)]);
}

module stand() {
  if (!show_stand) return;
  ply_box(inch(0.5), inch(2.0), -stand_h, inch(0.75), base_y-inch(4), stand_h-inch(0.1), c_ply2);
  ply_box(base_x-inch(1.25), inch(2.0), -stand_h, inch(0.75), base_y-inch(4), stand_h-inch(0.1), c_ply2);
  ply_box(inch(0.5), inch(2.0), -stand_h+inch(8), base_x-inch(1.0), base_y-inch(4), inch(0.75));
  ply_box(inch(0.5), base_y-inch(2.75), -stand_h, base_x-inch(1.0), inch(0.75), stand_h-inch(0.1), c_ply2);
}

frame();
drum();
table_and_conveyor();
motor_pack();
hood();
belt_guard();
gearmotor();
stand();
