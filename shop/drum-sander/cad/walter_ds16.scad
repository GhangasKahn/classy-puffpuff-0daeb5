// WALTER DS-16 Rev B — OpenSCAD solid model (inches)
// Authoritative numbers: walter_ds16.py → parameters.scad
//   X = across drum (drive +X)   Y = feed depth (infeed −Y)   Z = up
// Set explode > 0 for an exploded preview. F5 preview / F6 render.

include <parameters.scad>;

$fn = 48;
explode = 0; // 0 assembled · try 5 for exploded

module side_panel() {
  difference() {
    color("#c4a574") cube([side_t, side_d, side_h]);
    // way rebate (inner face is +X on left panel)
    translate([side_t - way_rebate, way_end_inset, way_z])
      cube([way_rebate + 0.05, side_d - 2 * way_end_inset, way_stock]);
    // stretcher housings (Y from infeed, Z = rail bottom, ¾″ tall)
    for (z = [6, 12, 20])
      translate([side_t - stretcher_housing, stretcher_dado_y0, z])
        cube([stretcher_housing + 0.05, stretcher_h, side_t]);
    translate([-0.1, drum_y, drum_z]) rotate([0, 90, 0])
      cylinder(h=side_t + 0.2, d=shaft_od + 0.08);
  }
}

module stretcher(z) {
  color("#8a7355")
    translate([side_t - stretcher_housing, stretcher_dado_y0, z])
      cube([stretcher_len, stretcher_h, side_t]);
}

module way_left() {
  color("#d9dcde")
    translate([side_t - way_rebate, way_end_inset, way_z])
      cube([way_stock, side_d - 2 * way_end_inset, way_stock]);
}
module way_right() {
  color("#d9dcde")
    translate([side_t + clear - way_project, way_end_inset, way_z])
      cube([way_stock, side_d - 2 * way_end_inset, way_stock]);
}

module table() {
  translate([side_t + (clear - table_w) / 2, 0, table_z]) {
    color("#c4b8a4") cube([table_w, table_d, table_t - 0.25]);
    color("#d9dcde") translate([0, 0, table_t - 0.25]) cube([table_w, table_d, 0.25]);
  }
}

module acme(x, y) {
  color("#8a9098") translate([x, y, 2]) cylinder(h=16, d=0.5);
}

module drum_stack() {
  translate([side_t + clear / 2, drum_y, drum_z]) rotate([0, 90, 0]) {
    color("#b8a990") cylinder(h=drum_len, d=drum_od, center=true);
    color("#8a9098") cylinder(h=shaft_len, d=shaft_od, center=true);
    color("#8a7355")
      for (i = [0:20])
        rotate([0, 0, i * 17])
          translate([drum_od / 2, 0, -drum_len / 2 + i * 0.72])
            cube([0.08, 0.35, 0.9], center=true);
  }
}

module flange(x) {
  translate([x, drum_y, drum_z]) rotate([0, 90, 0]) {
    color("#6e7578") cylinder(h=0.45, d=2.8, center=true);
    color("#8a9098") cylinder(h=0.7, d=1.4, center=true);
  }
}

module pulley_drum() {
  translate([side_t + clear + 1.15, drum_y, drum_z]) rotate([0, 90, 0])
    color("#5a6068") cylinder(h=0.9, d=5.0, center=true);
}

module motor() {
  translate([side_t + 2.2, 3, 2]) {
    color("#4a5058") cube([6, 8, 6]);
    translate([6.1, 4, 3.2]) rotate([0, 90, 0])
      color("#5a6068") cylinder(h=0.8, d=3.0);
  }
}

module roller(y) {
  translate([side_t + clear / 2, y, table_z + table_t + roller_od / 2 + 0.35])
    rotate([0, 90, 0])
      color("#5a6068") cylinder(h=roller_len, d=roller_od, center=true);
}

module yoke(y) {
  translate([side_t + 0.4, y - 0.4, table_z + table_t + 1.4])
    color("#8a7355") cube([clear - 0.8, 0.8, 0.4]);
}

module hood() {
  translate([side_t + 0.6, drum_y, drum_z]) {
    color("#9aa8a0", 0.5)
      rotate([90, 0, 90])
        rotate_extrude(angle=180)
          translate([4.6, 0, 0]) square([0.9, clear - 1.2]);
    translate([clear - 1.4, 0, 4.4]) rotate([0, 90, 0])
      color("#7a8f68") cylinder(h=1.4, d=dust_port_od);
  }
}

color("#a89070") cube([W, side_d, 0.75]);

translate([-explode, 0, 0]) { side_panel(); way_left(); }
translate([explode, 0, 0]) {
  translate([W, 0, 0]) mirror([1, 0, 0]) side_panel();
  way_right();
}

stretcher(6);
stretcher(12);
stretcher(20);

translate([0, 0, -explode * 0.7]) {
  table();
  acme(acme_x0, acme_y0);
  acme(acme_x1, acme_y1);
}

translate([0, 0, explode * 0.9]) {
  drum_stack();
  flange(side_t + 0.25);
  flange(side_t + clear - 0.25);
  pulley_drum();
}

translate([0, -explode * 1.2, 0]) motor();

translate([0, 0, explode * 0.25]) {
  roller(7.4);
  roller(14.6);
  yoke(7.4);
  yoke(14.6);
}

translate([0, 0, explode * 1.7]) hood();
