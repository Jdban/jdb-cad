"""Example parametric part showing the kit's conventions.

A simple L bracket with two screw holes. Run from the project root:
    .venv/bin/python examples/bracket.py
Writes examples/out/: STEP (in-use orientation), STL + 3MF (print orientation),
and a .settings.json card the viewer shows next to the model.
"""
import json
from pathlib import Path

from build123d import (
    Align, Box, Cylinder, Mesher, Pos, Rot, export_step, export_stl, fillet, Axis,
)

OUT = Path(__file__).parent / "out"
MIN = (Align.MIN, Align.MIN, Align.MIN)

# ---- key dimensions (mm): edit these, rerun -------------------------------
WIDTH = 30.0         # along the bracket
LEG_A = 40.0         # horizontal leg length
LEG_B = 30.0         # vertical leg height
THICK = 4.0
INNER_FILLET = 4.0   # rounds the inside corner: the stress point
HOLE_D = 4.5         # M4 clearance


def bracket():
    part = Box(LEG_A, WIDTH, THICK, align=MIN) + Box(THICK, WIDTH, LEG_B, align=MIN)
    inner = part.edges().filter_by(Axis.Y).sort_by_distance((THICK, 0, THICK))[0]
    part = fillet(inner, INNER_FILLET)
    part -= Pos(LEG_A * 0.65, WIDTH / 2, 0) * Cylinder(HOLE_D / 2, THICK * 3)
    part -= Pos(0, WIDTH / 2, LEG_B * 0.65) * Rot(0, 90, 0) * Cylinder(HOLE_D / 2, THICK * 3)
    return part


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    part = bracket()
    export_step(part, str(OUT / "bracket.step"))
    # Print orientation: here the in-use orientation already prints well
    # (both legs grow from the bed, the fillet keeps layers across the corner).
    export_stl(part, str(OUT / "bracket_print.stl"), tolerance=0.01, angular_tolerance=0.1)
    mesher = Mesher()
    mesher.add_shape(part)
    mesher.write(str(OUT / "bracket_print.3mf"))
    (OUT / "bracket_print.settings.json").write_text(json.dumps({
        "title": "Example bracket",
        "settings": [["Wall loops", "6", "Default 2: thin parts print solid"]],
        "note": "Only list settings that differ from the slicer defaults.",
    }, indent=2))
    print(f"volume {part.volume / 1000:.1f} cm3")
