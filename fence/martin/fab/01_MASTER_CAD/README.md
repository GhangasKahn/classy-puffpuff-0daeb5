# Master CAD

Controlling geometry: `fence/martin/martin_kernel.py` (inches).
FreeCAD script: `fence/martin/cad/martin_fence.py` — run `freecadcmd martin_fence.py` to rebuild FCStd/STEP/STL for Rev F.2 (2×4 ribbons + motif solids).
OpenSCAD: `fence/martin/cad/scad/main.scad` (parameters.scad is regenerated from the kernel; `rail_h = 88.9` mm = 3.50″).

**Checked-in `martin.FCStd` / STEP / timber STL may lag the kernel if FreeCAD was not available in this environment.** Do not mill ribbon thickness from an unrecomputed solid. Use the kernel, P-302, and OpenSCAD parameters.
