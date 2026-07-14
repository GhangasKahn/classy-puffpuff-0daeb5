
// HASHIRA bay — full post + triple nuki + cladding hints + caps
include <hashira_lib.scad>

show_cladding = 1;
cladding_gap = 8;
board_w = 90;
board_t = 18;

module mortised_post() {
  difference() {
    hashira_post();
    for (z = [rail_z_low, rail_z_mid, rail_z_top]) {
      translate([-1, (post_d - rail_w)/2 - ease/2, z])
        cube([post_w + 2, rail_w + ease, rail_t + ease]);
    }
  }
  translate([0, 0, post_h]) hashira_cap();
}

module bay_assembly() {
  // left / right posts
  mortised_post();
  translate([bay_cc, 0, 0]) mortised_post();

  // through rails
  for (z = [rail_z_low, rail_z_mid, rail_z_top]) {
    translate([-120, (post_d - rail_w)/2, z + ease/2])
      nuki_rail(len=bay_cc + post_w + 240);
  }

  // cladding rain-screen boards
  if (show_cladding) {
    board_span = bay_cc - post_w - 20;
    n = floor(board_span / (board_w + cladding_gap));
    start_x = post_w + 10;
    color([0.78, 0.74, 0.62])
    for (i = [0 : n - 1]) {
      translate([
        start_x + i * (board_w + cladding_gap),
        -board_t - 4,
        rail_z_low + rail_t + 10
      ])
        cube([board_w, board_t, rail_z_top - rail_z_low - 20]);
    }
  }

  // grade
  color([0.25, 0.32, 0.22, 0.55])
    translate([-200, -120, -4])
      cube([bay_cc + post_w + 400, post_d + 240, 4]);
}

bay_assembly();
