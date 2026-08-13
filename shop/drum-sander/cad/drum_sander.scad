// DS-18 shop drum sander — parametric OpenSCAD (inches)
// Usage: openscad -o ds18.png --imgsize=1600,1000 --autocenter --viewall drum_sander.scad
// Units: inches. Convert at $fn for preview.

$fn = 48;
inch = 1;

cab_w = 36;
cab_d = 22;
cab_h = 28;
ply = 0.75;
drum_od = 6;
drum_len = 18;
shaft_od = 1;
shaft_len = 24;
table_w = 20;
table_d = 22;
table_lift = 0.9; // gap under drum
explode = 0;      // 0 assembled, 8–16 exploded

c_ply   = [0.77, 0.65, 0.45];
c_ply2  = [0.69, 0.54, 0.34];
c_sand  = [0.83, 0.65, 0.45];
c_steel = [0.54, 0.56, 0.59];
c_dark  = [0.16, 0.18, 0.20];
c_hood  = [0.29, 0.33, 0.38];
c_sw    = [0.77, 0.48, 0.23];

module ply_box(w, h, d) cube([w, d, h]);

module cabinet() {
  color(c_ply) {
    // left / right
    translate([-cab_w/2, -cab_d/2, 0]) cube([ply, cab_d, cab_h]);
    translate([cab_w/2 - ply, -cab_d/2, 0]) cube([ply, cab_d, cab_h]);
    // front / back
    translate([-cab_w/2 + ply, cab_d/2 - ply, 0]) cube([cab_w - 2*ply, ply, cab_h]);
    translate([-cab_w/2 + ply, -cab_d/2, 0]) cube([cab_w - 2*ply, ply, cab_h]);
    // bottom
    translate([-cab_w/2 + ply, -cab_d/2 + ply, 0]) cube([cab_w - 2*ply, cab_d - 2*ply, ply]);
    // motor shelf
    translate([-cab_w/2 + ply, -cab_d/2 + ply, 8]) cube([14, cab_d - 2*ply, ply]);
  }
}

module towers() {
  color(c_ply2) {
    translate([-10.5, -3, cab_h]) cube([ply, 6, 14]);
    translate([10.5 - ply, -3, cab_h]) cube([ply, 6, 14]);
  }
}

module drum_assy() {
  z = cab_h + 8;
  translate([0, 0, explode * 1.2]) {
    color(c_sand)
      rotate([0, 90, 0])
        translate([0, 0, -drum_len/2])
          cylinder(h=drum_len, d=drum_od);
    color(c_steel)
      rotate([0, 90, 0])
        translate([0, 0, -shaft_len/2])
          cylinder(h=shaft_len, d=shaft_od);
    color(c_steel) {
      translate([-9.6, 0, z - (cab_h + 8)]) pillow();
      translate([9.6, 0, z - (cab_h + 8)]) pillow();
    }
  }
}

module pillow() {
  translate([0, 0, cab_h + 8]) {
    cube([3.2, 4.2, 0.7], center=true);
    rotate([0, 90, 0]) cylinder(h=1.8, d=3.2, center=true);
  }
}

module motor() {
  translate([-explode * 1.4, -explode * 0.6, 0]) {
    color(c_dark)
      translate([-10, -2, 11.2])
        rotate([0, 90, 0]) cylinder(h=9, d=6.8, center=true);
    color(c_steel)
      translate([-4.4, -2, 11.2])
        rotate([0, 90, 0]) cylinder(h=0.9, d=4, center=true);
  }
}

module table() {
  z = cab_h + 8 - drum_od/2 - table_lift;
  translate([0, explode * 0.8, -explode * 0.6]) {
    color(c_ply)
      translate([-table_w/2, -table_d/2 + 2, z])
        cube([table_w, table_d, ply]);
    color([0.55, 0.35, 0.17])
      translate([-table_w/2, -table_d/2 + 2, z + ply])
        cube([table_w, 0.75, 3]);
  }
}

module hood() {
  translate([0, 0, explode * 1.4]) color(c_hood) {
    translate([0, -0.4, cab_h + 8.4])
      rotate([0, 90, 0])
        difference() {
          cylinder(h=18.4, d=8.4, center=true);
          cylinder(h=19, d=7.2, center=true);
          translate([-6, 0, -10]) cube([12, 12, 20]);
        }
    translate([0, -6.5, cab_h + 10.2])
      rotate([90, 0, 0]) cylinder(h=4, d=4);
  }
}

module switch() {
  color(c_sw)
    translate([-cab_w/2 - 0.4 - explode, cab_d/2 - 5, 16])
      cube([3.2, 2.2, 4.4]);
}

translate([0, 0, -explode]) cabinet();
towers();
drum_assy();
motor();
table();
hood();
switch();

// shop floor
color([0.16, 0.14, 0.11])
  translate([0, 0, -0.4])
    cube([80, 80, 0.4], center=true);
