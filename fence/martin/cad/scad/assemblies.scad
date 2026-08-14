include <parameters.scad>;
include <parts.scad>;

module A010_posts() {
    for (i=[0:3]) {
        translate([post_cx[i]-post_x/2, -post_y/2, 0]) L_post();
    }
}
module A020_rails() {
    for (z=rail_cls)
        translate([nuki_x0, -rail_t/2, z-rail_h/2]) R_nuki();
}
module A001_base() {
    translate([-6*25.4, -base_spread_cl/2 - 3.5*25.4/2, -sill_h]) F_sill();
    translate([-6*25.4,  base_spread_cl/2 - 3.5*25.4/2, -sill_h]) F_sill();
    for (i=[0:3])
        translate([post_cx[i]-post_x/2, -tie_len/2, -sill_h]) F_tie();
}
module A000_master() {
    A001_base();
    A010_posts();
    A020_rails();
    translate([cap_x0, -cap_w/2, overall_height-cap_t]) C_cap();
}
