
// Ari-kake 蟻掛け — dovetail half-lap corner
include <hashira_lib.scad>

exploded = 1;
lap_t = rail_t / 2;
tail = 36;
flare = 10;
explode_gap = 40;

module dove_male() {
  // rail A
  difference() {
    cube([240, rail_w, rail_t]);
    translate([240 - 70, -1, lap_t])
      cube([71, rail_w + 2, lap_t + 1]);
  }
  // dovetail
  translate([240 - 70, rail_w/2, lap_t])
    linear_extrude(height=lap_t)
      polygon(points=[
        [0, -tail/2],
        [70, -tail/2 - flare],
        [70,  tail/2 + flare],
        [0,  tail/2]
      ]);
}

module dove_female() {
  difference() {
    cube([240, rail_w, rail_t]);
    translate([-1, -1, -0.1])
      cube([71, rail_w + 2, lap_t + 0.1]);
    translate([0, rail_w/2, -0.1])
      linear_extrude(height=lap_t + 0.2)
        polygon(points=[
          [0, -tail/2 - 0.4],
          [70, -tail/2 - flare - 0.4],
          [70,  tail/2 + flare + 0.4],
          [0,  tail/2 + 0.4]
        ]);
  }
}

module ari_kake_assembly() {
  color(wood_rail) dove_male();
  color(wood_post)
    translate([
      exploded ? 240 + explode_gap - 70 : 240 - 70,
      exploded ? rail_w + explode_gap : 0,
      0
    ])
    rotate([0, 0, exploded ? 0 : 90])
      translate([0, 0, 0]) dove_female();
}

// better corner presentation
module ari_corner() {
  color(wood_rail) {
    // X member
    difference() {
      cube([260, rail_w, rail_t]);
      translate([260-80, -1, lap_t]) cube([81, rail_w+2, lap_t+1]);
    }
    translate([260-80, rail_w/2, lap_t])
      linear_extrude(lap_t)
        polygon([[0,-tail/2],[80,-tail/2-flare],[80,tail/2+flare],[0,tail/2]]);
  }
  color(wood_post)
  translate([260 - 80 + (exploded ? explode_gap : 0), exploded ? rail_w + explode_gap : rail_w, 0])
  rotate([0,0,90]) {
    difference() {
      cube([260, rail_w, rail_t]);
      translate([-1,-1,-0.1]) cube([81, rail_w+2, lap_t+0.1]);
      translate([0, rail_w/2, -0.1])
        linear_extrude(lap_t+0.2)
          polygon([[0,-tail/2-0.5],[80,-tail/2-flare-0.5],[80,tail/2+flare+0.5],[0,tail/2+0.5]]);
    }
  }
}

ari_corner();
