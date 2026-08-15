#!/usr/bin/env python3
"""Studio stills from the production STL solids. Washi ground, TOGI map, 3/4 light."""

from __future__ import annotations

from pathlib import Path

import vtk
from PIL import Image

CAD = Path(__file__).resolve().parents[1]
STL = CAD / "stl"
TEX = CAD.parent / "assets" / "cad" / "togi-albedo.png"
OUT = CAD.parent / "assets" / "studio"
OUT.mkdir(parents=True, exist_ok=True)

KIND = {
    "01-frame": "metal",
    "02-mizu": "steel",
    "03-kumiko": "steel",
    "04-nata": "steel",
    "05-saya": "wood",
    "06-spike": "steel",
    "07-togi": "metal",
    "08-tweezer": "metal",
    "09-cassette": "metal",
    "10-s50": "steel",
    "11-l80": "steel",
    "12-locator": "cloth",
    "13-wedge": "metal",
    "14-chest": "wood",
}

COLORS = {
    "metal": (0.62, 0.60, 0.56),
    "steel": (0.90, 0.88, 0.82),
    "wood": (0.88, 0.78, 0.58),
    "cloth": (0.93, 0.89, 0.80),
}


def load_poly(path: Path) -> vtk.vtkPolyData:
    r = vtk.vtkSTLReader()
    r.SetFileName(str(path))
    r.Update()
    norms = vtk.vtkPolyDataNormals()
    norms.SetInputConnection(r.GetOutputPort())
    norms.ComputePointNormalsOn()
    norms.SplittingOn()
    norms.SetFeatureAngle(40)
    norms.Update()
    return norms.GetOutput()


def box_uvs(poly: vtk.vtkPolyData) -> None:
    bounds = poly.GetBounds()
    sx = max(bounds[1] - bounds[0], 1e-6)
    sy = max(bounds[3] - bounds[2], 1e-6)
    sz = max(bounds[5] - bounds[4], 1e-6)
    pts = poly.GetPoints()
    nrm = poly.GetPointData().GetNormals()
    tcoords = vtk.vtkFloatArray()
    tcoords.SetNumberOfComponents(2)
    tcoords.SetName("TextureCoordinates")
    tcoords.SetNumberOfTuples(pts.GetNumberOfPoints())
    scale = 2.2 / max(sx, sy, sz)
    for i in range(pts.GetNumberOfPoints()):
        x, y, z = pts.GetPoint(i)
        nx, ny, nz = (0, 0, 1) if nrm is None else nrm.GetTuple(i)
        ax, ay, az = abs(nx), abs(ny), abs(nz)
        if ax >= ay and ax >= az:
            u, v = y * scale, z * scale
        elif ay >= ax and ay >= az:
            u, v = x * scale, z * scale
        else:
            u, v = x * scale, y * scale
        tcoords.SetTuple2(i, u, v)
    poly.GetPointData().SetTCoords(tcoords)


def actor_for(stem: str) -> vtk.vtkActor:
    poly = load_poly(STL / f"{stem}.stl")
    box_uvs(poly)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    kind = KIND.get(stem, "metal")
    color = COLORS[kind]
    prop = actor.GetProperty()
    prop.SetColor(*color)
    prop.SetSpecular(0.72 if kind in ("metal", "steel") else 0.12)
    prop.SetSpecularPower(36 if kind == "steel" else 22)
    prop.SetAmbient(0.38)
    prop.SetDiffuse(0.95)
    if TEX.exists() and kind in ("metal", "steel", "wood"):
        png = vtk.vtkPNGReader()
        png.SetFileName(str(TEX))
        tex = vtk.vtkTexture()
        tex.SetInputConnection(png.GetOutputPort())
        tex.RepeatOn()
        tex.InterpolateOn()
        actor.SetTexture(tex)
        if kind == "steel":
            prop.SetColor(0.96, 0.94, 0.88)
        if kind == "wood":
            prop.SetColor(0.98, 0.90, 0.72)
        if kind == "metal":
            prop.SetColor(0.78, 0.75, 0.70)
    return actor


def studio_window(w: int, h: int) -> tuple[vtk.vtkRenderer, vtk.vtkRenderWindow]:
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.93, 0.89, 0.82)
    ren.SetBackground2(0.86, 0.80, 0.70)
    ren.GradientBackgroundOn()
    key = vtk.vtkLight()
    key.SetPosition(80, 120, 90)
    key.SetFocalPoint(0, 0, 0)
    key.SetColor(1.0, 0.96, 0.88)
    key.SetIntensity(1.15)
    fill = vtk.vtkLight()
    fill.SetPosition(-70, 30, -40)
    fill.SetColor(0.62, 0.70, 0.78)
    fill.SetIntensity(0.45)
    rim = vtk.vtkLight()
    rim.SetPosition(10, -40, 80)
    rim.SetColor(1, 1, 1)
    rim.SetIntensity(0.35)
    ren.AddLight(key)
    ren.AddLight(fill)
    ren.AddLight(rim)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(w, h)
    return ren, rw


def save(rw: vtk.vtkRenderWindow, dest: Path) -> None:
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.SetScale(1)
    w2i.Update()
    png_path = dest.with_suffix(".png")
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(png_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    img = Image.open(png_path).convert("RGB")
    img.save(dest.with_suffix(".webp"), "WEBP", quality=86, method=4)
    img.resize((min(900, img.width), int(img.height * min(900, img.width) / img.width)), Image.Resampling.LANCZOS).save(
        dest.with_name(dest.stem + "-sm.webp"), "WEBP", quality=80, method=4
    )
    png_path.unlink(missing_ok=True)
    print(" ", dest.with_suffix(".webp").name)


def render_part(stem: str, w: int = 1400, h: int = 1000) -> None:
    ren, rw = studio_window(w, h)
    actor = actor_for(stem)
    ren.AddActor(actor)
    cam = ren.GetActiveCamera()
    ren.ResetCamera()
    cam.Azimuth(-35)
    cam.Elevation(22)
    cam.Dolly(1.15)
    ren.ResetCameraClippingRange()
    rw.Render()
    save(rw, OUT / stem)


def render_kit() -> None:
    order = ["01-frame", "02-mizu", "05-saya", "07-togi", "06-spike", "08-tweezer", "13-wedge"]
    ren, rw = studio_window(1800, 1100)
    x = 0.0
    for stem in order:
        actor = actor_for(stem)
        poly = actor.GetMapper().GetInput()
        b = poly.GetBounds()
        actor.SetPosition(x - b[0], -b[2], -b[4])
        ren.AddActor(actor)
        x += (b[1] - b[0]) + 14.0
    cam = ren.GetActiveCamera()
    ren.ResetCamera()
    cam.Azimuth(-28)
    cam.Elevation(18)
    cam.Dolly(1.05)
    ren.ResetCameraClippingRange()
    rw.Render()
    save(rw, OUT / "00-kit")


def main() -> None:
    print("Rendering studio stills…")
    render_kit()
    for stem in KIND:
        if (STL / f"{stem}.stl").exists():
            render_part(stem)
    print("done", OUT)


if __name__ == "__main__":
    main()
