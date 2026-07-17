
// Watari-ago 渡り顎 — passing jaw / shouldered through rail
include <hashira_lib.scad>

exploded = 1;
haunch = 18;
explode_gap = 80;

module watari_rail() {
  // main through bar with offset shoulders
  union() {
    translate([0, 0, 0]) cube([rail_len*0.7, rail_w, rail_t]);
    // front haunch
    translate([rail_len*0.35 - post_w/2 - haunch, -haunch, 0])
      cube([haunch, rail_w + haunch, rail_t]);
    // back haunch (offset)
    translate([rail_len*0.35 + post_w/2, 0, 0])
      cube([haunch, rail_w + haunch, rail_t]);
  }
}

module watari_ago_assembly() {
  difference() {
    hashira_post(h=420, w=post_w, d=post_d);
    // through mortise
    translate([-1, (post_d - rail_w)/2 - ease/2, 180])
      cube([post_w + 2, rail_w + ease, rail_t + ease]);
    // haunch seats
    translate([-1, -haunch - ease/2, 180])
      cube([haunch + 2, haunch + ease, rail_t + ease]);
    translate([post_w - haunch - 1, post_d - ease/2, 180])
      cube([haunch + 2, haunch + ease, rail_t + ease]);
  }

  translate([
    exploded ? -rail_len*0.35 - explode_gap : -rail_len*0.35,
    (post_d - rail_w)/2,
    180
  ]) color(wood_rail) watari_rail();
}

watari_ago_assembly();
