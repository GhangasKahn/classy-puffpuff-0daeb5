// STELE — render scene composed from FreeCAD-exported STLs
// Usage: openscad -o out.png -D 'show_below_grade=false' scene.scad

show_below_grade = false;
show_ground = true;

// material palette — Onondaga limestone, cedar, concrete, gravel
c_masonry  = [0.80, 0.76, 0.64];
c_timber   = [0.55, 0.38, 0.22];
c_concrete = [0.62, 0.62, 0.60];
c_gravel   = [0.35, 0.34, 0.32];
c_ground   = [0.30, 0.36, 0.26];

color(c_masonry)  import("exports/stele_masonry.stl");
color(c_timber)   import("exports/stele_timber.stl");

if (show_below_grade) {
  color(c_concrete) import("exports/stele_concrete.stl");
  color(c_gravel)   import("exports/stele_gravel.stl");
}

if (show_ground) {
  color(c_ground)
    translate([-1500, -2200, -60])
      cube([13500, 4400, 60]);
}
