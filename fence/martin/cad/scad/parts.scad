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

module R_slat(h) { cube([nuki_len, rail_t, h]); }

module C_cap() { cube([cap_len, cap_w, cap_t]); }

module F_planter() { cube([planter_x, planter_y, planter_h]); }

module F_sill() { cube([sill_len, 3.5*25.4, sill_h]); }

module F_tie() { cube([post_x, tie_len, sill_h]); }
