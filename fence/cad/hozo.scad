
// Hozo ほぞ — mortise & tenon with drawbored peg (gate/cap)
include <hashira_lib.scad>

exploded = 1;
tenon_l = 45;
tenon_t = 28;
tenon_w = 50;
explode_gap = 60;

module hozo_assembly() {
  // vertical post stub
  difference() {
    hashira_post(h=280, w=post_w, d=post_d);
    translate([(post_w - tenon_w)/2 - ease/2, -1, 160])
      cube([tenon_w + ease, tenon_l + 2, tenon_t + ease]);
    // peg hole (drawbore offset -1.5mm)
    translate([post_w/2, tenon_l/2, 160 + tenon_t/2])
      rotate([0,90,0]) cylinder(h=post_w + 4, d=peg_d + 0.4, center=true, $fn=24);
  }

  // horizontal member with tenon
  tx = exploded ? -220 - explode_gap : -220;
  translate([tx, 0, 160 + ease/2]) {
    color(wood_rail) {
      cube([220, post_d, 70]);
      translate([220, (post_d - tenon_w)/2, (70 - tenon_t)/2])
        cube([tenon_l, tenon_w, tenon_t]);
    }
    // peg hole in tenon (unoffset) for drawbore
    if (!exploded) {
      translate([220 + tenon_l/2 + 1.5, post_d/2, 35])
        rotate([90,0,0]) peg(h=post_d + 20);
    } else {
      translate([220 + tenon_l + explode_gap, post_d/2, 35])
        rotate([90,0,0]) peg(h=post_d + 20);
    }
  }
}

hozo_assembly();
