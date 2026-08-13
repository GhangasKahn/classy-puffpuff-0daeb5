// Semantic parts — millimetres. Include parameters.scad first.
include <parameters.scad>;

module L_post(part_id="L-001") {
    // blank standing on tenon tip at z=-post_tenon_h
    cube([post_x, post_y, post_body_h]);
    translate([(post_x-post_tenon_x)/2, (post_y-post_tenon_y)/2, -post_tenon_h])
        cube([post_tenon_x, post_tenon_y, post_tenon_h]);
}

module R_nuki(part_id="R-001") {
    cube([nuki_len, rail_t, rail_h]);
}

module C_cap() { cube([cap_len, cap_w, cap_t]); }

module B_board(h) { cube([board_w, board_t, h]); }

module F_pad() { cube([pad_len, pad_width, pad_thick]); }

module F_pier() { cube([pier_xy, pier_xy, pier_h]); }
