// WALTER DS-16 Rev B — OpenSCAD preview (inches)
// Authoritative dimensions: walter_ds16.py

$fn = 48;

drum_od = 5.0;
drum_len = 15.75;
shaft_od = 0.75;
side_t = 0.75;
side_h = 30;
side_d = 22;
clear = 16.5;
table_t = 1.5;
table_w = 16;
table_d = 22;

module side_panel() {
  color("#c4a574") cube([side_t, side_d, side_h]);
}

module way() {
  color("#d9dcde")
  translate([side_t, 1, 10])
    cube([0.75, side_d - 2, 0.75]);
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
        cylinder(h=22.5, d=shaft_od, center=true);
    }
}

module table() {
  color("#cfd3d5")
  translate([side_t + (clear - table_w)/2, 0.5, 14])
    cube([table_w, table_d, table_t]);
}

module acme(x) {
  color("#8a9098")
  translate([x, 4, 2])
    cylinder(h=16, d=0.5);
}

module roller(y) {
  translate([side_t + clear/2, y, 16.7])
    rotate([0, 90, 0])
      color("#5a6068")
        cylinder(h=drum_len, d=1.25, center=true);
}

module motor() {
  color("#4a5058")
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

side_panel();
translate([side_t + clear, 0, 0]) side_panel();
way();
translate([clear - 0.75, 0, 0]) way();
color("#a89070") cube([clear + 2*side_t, side_d, 0.75]);
stretcher(6);
stretcher(12);
stretcher(20);
drum();
table();
acme(side_t + 2);
acme(side_t + clear - 2);
roller(7.5);
roller(14.5);
motor();
hood();
