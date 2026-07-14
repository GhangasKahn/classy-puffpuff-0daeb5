
// Ne-tsugi 根継ぎ — foot splice for rotten post butts
include <hashira_lib.scad>

exploded = 1;
splice_h = 160;
hook = 28;
explode_gap = 50;

module upper_post() {
  difference() {
    cube([post_w, post_d, 320]);
    // female scarf pocket
    translate([-1, -1, 0])
      cube([post_w/2 + 1, post_d + 2, splice_h]);
    translate([post_w/2 - 1, post_d/2 - hook/2, splice_h/2 - hook/2])
      cube([post_w/2 + 2, hook, hook]);
  }
}

module lower_stub() {
  union() {
    cube([post_w, post_d, 220]);
    // male scarf
    translate([0, 0, 220])
      cube([post_w/2, post_d, splice_h]);
    translate([post_w/2, post_d/2 - (hook - 2)/2, 220 + splice_h/2 - (hook - 2)/2])
      cube([post_w/2, hook - 2, hook - 2]);
  }
}

module ne_tsugi_assembly() {
  color(wood_post) translate([0, 0, exploded ? 220 + splice_h + explode_gap : 220])
    upper_post();
  color(wood_rail) lower_stub();
  // grade line marker
  color([0.36, 0.48, 0.30])
    translate([-40, -40, 180])
      cube([post_w + 80, post_d + 80, 2]);
}

ne_tsugi_assembly();
