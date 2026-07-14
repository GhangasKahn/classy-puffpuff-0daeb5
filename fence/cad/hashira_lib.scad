// HASHIRA — shared dimensions (mm)
// Tunable via -D on the command line / OpenSCAD MCP variables

post_w = 89;          // ~3.5" nominal 4x4
post_d = 89;
post_h = 1800;        // above-grade height shown
rail_w = 89;          // rail width (through post face)
rail_t = 38;          // rail thickness
rail_len = 1800;      // bay center-to-center approx
bay_cc = 1800;        // post center spacing
cap_overhang = 18;
cap_h = 28;

// rail elevations from post bottom (above grade in model)
rail_z_low = 200;
rail_z_mid = 900;
rail_z_top = 1500;

ease = 1.2;           // seasonal mortise ease
peg_d = 10;
wood_post = [0.55, 0.35, 0.18];
wood_rail = [0.42, 0.52, 0.34];
wood_peg  = [0.72, 0.62, 0.42];

module hashira_post(h=post_h, w=post_w, d=post_d) {
  color(wood_post) cube([w, d, h], center=false);
}

module hashira_cap(w=post_w, d=post_d, oh=cap_overhang, h=cap_h) {
  color([0.88, 0.85, 0.78])
  translate([-oh, -oh, 0])
    linear_extrude(height=h, scale=0.72)
      square([w + 2*oh, d + 2*oh], center=false);
}

module nuki_rail(len=rail_len, w=rail_w, t=rail_t) {
  color(wood_rail) cube([len, w, t], center=false);
}

module peg(h=post_d + 20, d=peg_d) {
  color(wood_peg) cylinder(h=h, d=d, $fn=24);
}
