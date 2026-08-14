// Joinery cutters (nuki mortise, kusabi slot, tie mortise)
include <parameters.scad>;
module nuki_mortise() {
    cube([post_x+2, rail_t+1, rail_h+1], center=true);
}
module kusabi_slot() {
    cube([0.625*25.4, post_y+2, 1.125*25.4], center=true);
}
