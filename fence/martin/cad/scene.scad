// MARTIN — Prairie removable fence render scene (OpenSCAD)
// Composed from FreeCAD-exported STLs. Sit-on-grade timber ladder — no concrete.
// Usage: openscad -o out.png --imgsize=1600,1000 --autocenter --viewall scene.scad

show_ground = true;

c_timber   = [0.55, 0.57, 0.58];
c_ballast  = [0.42, 0.40, 0.36];
c_ground   = [0.28, 0.34, 0.24];
c_drive    = [0.32, 0.32, 0.33];

color(c_timber)  import("exports/martin_timber.stl");
color(c_ballast) import("exports/martin_ballast.stl");

if (show_ground) {
  color(c_ground)
    translate([-200, 200, -2])
      cube([4000, 2200, 4]);
  color(c_drive)
    translate([-200, -2400, -5*25.4])
      cube([4000, 2300, 4]);
}
