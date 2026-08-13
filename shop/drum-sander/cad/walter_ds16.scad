// WALTER DS-16 — OpenSCAD preview model (inches)
// Open in OpenSCAD for a quick 3D sanity check of proportions.
// Authoritative dimensions: walter_ds16.py

$fn = 48;

capacity = 15.5;
drum_od = 5.0;
drum_len = 15.75;
shaft_od = 0.75;
side_t = 0.75;
side_h = 30;
side_d = 22;
clear = 16.5;
table_t = 1.5;
table_w = 16;
table_d = 20;

module side_panel() {
  color("#c4a574")
  cube([side_t, side_d, side_h]);
}

module stretcher(z) {
  color("#8a7355")
  translate([side_t, 2, z])
    cube([clear, 4, 0.75]);
}

module drum() {
  translate([side_t + clear/2, 11, 18.5])
    rotate([0, 90, 0]) {
      color("#b8a990")
        cylinder(h=drum_len, d=drum_od, center=true);
      color("#8a9098")
        cylinder(h=22, d=shaft_od, center=true);
    }
}

module table() {
  color("#d9dcde")
  translate([side_t + (clear - table_w)/2, 1, 14])
    cube([table_w, table_d, table_t]);
}

module motor() {
  color("#5a6068")
  translate([side_t + 2, 3, 2])
    cube([6, 8, 6]);
}

module hood() {
  color("#9aa8a0", 0.55)
  translate([side_t + 1, 7, 20])
    scale([1, 1, 0.7])
      resize([clear - 2, 10, 8])
        sphere(r=5);
}

// Assembly
side_panel();
translate([side_t + clear, 0, 0]) side_panel();
color("#a89070") translate([0, 0, 0]) cube([clear + 2*side_t, side_d, 0.75]);
stretcher(6);
stretcher(12);
stretcher(20);
drum();
table();
motor();
hood();
