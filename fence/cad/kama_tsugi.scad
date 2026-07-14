
// Kama-tsugi 鎌継ぎ — sickle scarf for lengthening rails
include <hashira_lib.scad>

exploded = 1;
scarf = 140;
hook_w = 22;
hook_d = 28;
explode_gap = 35;

module left_scarf() {
  difference() {
    cube([220, rail_w, rail_t]);
    translate([220 - scarf, -1, rail_t/2])
      cube([scarf + 1, rail_w + 2, rail_t/2 + 1]);
    // hook pocket
    translate([220 - scarf/2 - hook_d/2, (rail_w - hook_w)/2 - 0.4, -0.1])
      cube([hook_d, hook_w + 0.8, rail_t/2 + 0.2]);
  }
  // remaining half + hook
  translate([220 - scarf, 0, 0])
    cube([scarf, rail_w, rail_t/2]);
  translate([220 - scarf/2 - hook_d/2 + 2, (rail_w - hook_w)/2 + 1, 0])
    cube([hook_d - 4, hook_w - 2, rail_t/2]);
}

module right_scarf() {
  difference() {
    cube([220, rail_w, rail_t]);
    translate([-1, -1, -0.1])
      cube([scarf + 1, rail_w + 2, rail_t/2 + 0.1]);
  }
  translate([0, 0, rail_t/2])
    cube([scarf, rail_w, rail_t/2]);
  // sickle hook
  translate([scarf/2 - hook_d/2 + 2, (rail_w - hook_w)/2 + 1, rail_t/2])
    cube([hook_d - 4, hook_w - 2, rail_t/2]);
}

module kama_assembly() {
  color(wood_rail) left_scarf();
  color(wood_post)
    translate([220 - scarf + (exploded ? scarf + explode_gap : 0), 0, 0])
      right_scarf();
}

kama_assembly();
