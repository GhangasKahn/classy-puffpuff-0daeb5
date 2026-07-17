
// Nuki 貫 — through-rail joint (exploded + assembled toggle)
include <hashira_lib.scad>

exploded = 1; // 1 = exploded teaching view, 0 = assembled
explode_gap = 70;

module nuki_assembly() {
  // post with through mortise
  difference() {
    hashira_post(h=420, w=post_w, d=post_d);
    translate([-1, (post_d - rail_w)/2 - ease/2, 180])
      cube([post_w + 2, rail_w + ease, rail_t + ease]);
  }

  // through rail
  translate([
    exploded ? -rail_len*0.35 - explode_gap : -rail_len*0.35,
    (post_d - rail_w)/2,
    180 + ease/2
  ]) nuki_rail(len=rail_len*0.7);

  // wedges / pegs
  if (!exploded) {
    translate([post_w + 8, post_d/2, 180 + rail_t/2])
      rotate([90,0,0]) peg(h=post_d + 16);
  } else {
    translate([post_w + explode_gap + 30, post_d/2, 180 + rail_t/2])
      rotate([90,0,0]) peg(h=post_d + 16);
  }
}

nuki_assembly();
