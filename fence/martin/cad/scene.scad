// MARTIN — Prairie removable fence render scene (OpenSCAD)
// Composed from FreeCAD-exported STLs.
// Usage: openscad -o out.png --imgsize=1600,1000 --autocenter --viewall scene.scad

show_below = true;
show_ground = true;

// owner gray timber + concrete pad palette
c_timber   = [0.55, 0.57, 0.58];   // painted gray
c_concrete = [0.70, 0.70, 0.68];
c_gravel   = [0.40, 0.39, 0.37];
c_sleeve   = [0.45, 0.50, 0.48];
c_ground   = [0.28, 0.34, 0.24];
c_drive    = [0.32, 0.32, 0.33];

color(c_timber)   import("exports/martin_timber.stl");
color(c_concrete) import("exports/martin_concrete.stl");
color(c_sleeve)   import("exports/martin_sleeve.stl");

if (show_below) {
  color(c_gravel) import("exports/martin_gravel.stl");
}

if (show_ground) {
  // garden side
  color(c_ground)
    translate([-200, 200, -2])
      cube([4000, 2200, 4]);
  // driveway side (drop-off visualized)
  color(c_drive)
    translate([-200, -2400, -5*25.4])
      cube([4000, 2300, 4]);
}
