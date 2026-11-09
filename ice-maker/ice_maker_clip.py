"""Replacement stripper tooth for the ice maker.

Rebuild of "Ice Maker Fix JDB (4).stl" (Jul 2025, the long-arm part) plus a
full-width keel under the tooth with the blade slot running through it, so the
grey blade stops the tooth sliding sideways along the wall.

Run:  ../.venv/bin/python ice_maker_clip.py [--rebuild]
Units mm. The profile is drawn in XY and is THICK wide in Z (the width along
the wall). Coordinates match the original Tinkercad file.

    crossbar (the tooth) runs along X from TOOTH_X0 to the outer wall
    arm hangs down the outside of the wall (-Y), hook curls under the wall
    groove in the crossbar's underside rides on the grey blade
"""
import sys
from pathlib import Path

from build123d import (
    Align, Axis, Box, Compound, Text, Plane, Polygon, Pos, Keep, Mesher, export_step, export_stl,
    extrude, split,
)

OUT = Path(__file__).parent / "out"
MIN = (Align.MIN, Align.MIN, Align.MIN)

THICK = 14.0                 # tooth width along the wall (original teeth ~14.5)

# crossbar / tooth
TOOTH_X0, TOOTH_X1 = 16.0, 51.0
BAR_Y0, BAR_Y1 = 18.0, 23.8  # underside and top (before the peaked roof)
ROOF_PEAK = 26.0             # ridge height at mid-width
ROOF_HIP_X = 19.0            # ridge starts here; slopes down to TOOTH_X0

# arm and hook (outside of the wall)
ARM_X0 = 48.1                # inner face of the arm = outer face of the wall
ARM_BOTTOM = -22.0
HOOK_X0 = 43.0               # hook tip reaches in to here
HOOK_TOP = -19.0             # top of the hook tip
HOOK_LIP_X = 45.9            # small step in the hook
HOOK_LIP_Y = -19.91
ARM_EXTRA = 0.0              # lengthen the arm: moves the hook this much lower (more room
                             #   to get it under the wall bottom; a little looser vertically)

# pocket over the wall top / tooth stub
WALL_NOTCH_X = (42.0, 48.0)
WALL_NOTCH_DEPTH = 3.0

# groove for the grey blade
GROOVE_W = 2.2               # narrow part
GROOVE_X = (16.0, 36.0)
GROOVE_WIDE_W = 5.0          # wider part near the wall
GROOVE_WIDE_X = (36.0, 42.0)
GROOVE_DEPTH = 2.0

# Lead-in chamfers on the hook tip and the notch mouth, so the part slides over
# the wall edges when snapping on instead of catching (less bending at the neck).
LEAD_IN = 1.0

# Printing flat (every layer holds the whole J: strongest for snapping on) would
# leave the blade slot's ceiling hanging over air. A thin sacrificial skin across
# the slot's bottom turns that into a short bridge. Slice it off before installing.
SLOT_SKIN = 0.6

# NEW: keel. The tooth is made deeper at full width, with the blade slot
# running up through it, so the blade can't slip out sideways. Full width
# (~6 mm each side of the slot) so nothing thin can snap off into the ice.
KEEL_DEPTH = 5.0             # extra depth below the crossbar underside. Keep it
                             #   ABOVE the water line or ice freezes around it
                             #   (old part had 2 mm and was fine)
KEEL_X = (16.0, 36.0)        # along the narrow part of the groove
KEEL_TAPER = True            # 45 deg slope up to the bar at the wall end, to clear
                             #   the blade's thicker base (where the groove widens)


def profile_solid():
    """Crossbar + arm + hook, extruded THICK in Z."""
    ARM_BOTTOM_, HOOK_TOP_, HOOK_LIP_Y_ = (ARM_BOTTOM - ARM_EXTRA, HOOK_TOP - ARM_EXTRA,
                                           HOOK_LIP_Y - ARM_EXTRA)
    pts = [
        (TOOTH_X0, BAR_Y0), (TOOTH_X0, BAR_Y1), (TOOTH_X1, BAR_Y1),
        (TOOTH_X1, ARM_BOTTOM_),
        (HOOK_X0 + LEAD_IN, ARM_BOTTOM_), (HOOK_X0, ARM_BOTTOM_ + LEAD_IN),   # chamfered hook tip
        (HOOK_X0, HOOK_TOP_ - LEAD_IN), (HOOK_X0 + LEAD_IN, HOOK_TOP_),
        (HOOK_LIP_X, HOOK_TOP_), (HOOK_LIP_X, HOOK_LIP_Y_), (ARM_X0, HOOK_LIP_Y_),
        (ARM_X0, BAR_Y0),
    ]
    pts = [p for i, p in enumerate(pts) if p != pts[i - 1]]
    body = extrude(Polygon(*pts, align=None), THICK, dir=(0, 0, 1))
    body -= Pos(WALL_NOTCH_X[0], BAR_Y0 - 1, -1) * Box(
        WALL_NOTCH_X[1] - WALL_NOTCH_X[0], WALL_NOTCH_DEPTH + 1, THICK + 2, align=MIN)
    if LEAD_IN > 0:   # chamfer the notch mouth (inner edge)
        x0, e = WALL_NOTCH_X[0], 0.01
        tri = Polygon((x0 - LEAD_IN, BAR_Y0 - e), (x0 + e, BAR_Y0 - e), (x0 + e, BAR_Y0 + LEAD_IN), align=None)
        body -= Pos(0, 0, -1) * extrude(tri, THICK + 2, dir=(0, 0, 1))
    return body


def roof():
    """Peaked top: triangle across the width, ridge along X, hipped at the inner end."""
    tri = Plane.YZ.offset(TOOTH_X0) * Polygon(
        (BAR_Y1, 0), (ROOF_PEAK, THICK / 2), (BAR_Y1, THICK), align=None)
    r = extrude(tri, TOOTH_X1 - TOOTH_X0)
    hip = Plane(origin=(TOOTH_X0, BAR_Y1, 0),
                z_dir=(-(ROOF_PEAK - BAR_Y1), ROOF_HIP_X - TOOTH_X0, 0))
    return split(r, bisect_by=hip, keep=Keep.BOTTOM)


def grooves(keel_depth=0.0, groove_w=None):
    groove_w = GROOVE_W if groove_w is None else groove_w
    c = THICK / 2
    y0 = BAR_Y0 - keel_depth - 1
    g = Pos(GROOVE_X[0] - 1, y0, c - groove_w / 2) * Box(
        GROOVE_X[1] - GROOVE_X[0] + 1, BAR_Y0 + GROOVE_DEPTH - y0, groove_w, align=MIN)
    g += Pos(GROOVE_WIDE_X[0], BAR_Y0 - 1, c - GROOVE_WIDE_W / 2) * Box(
        GROOVE_WIDE_X[1] - GROOVE_WIDE_X[0] + 0.01, GROOVE_DEPTH + 1, GROOVE_WIDE_W, align=MIN)
    return g


def keel(depth=None):
    """Full-width extension under the tooth, side view tapered at the wall end."""
    x0, x1 = KEEL_X
    d = KEEL_DEPTH if depth is None else depth
    top = BAR_Y0 + 0.5  # sink into the crossbar so it's one solid
    if KEEL_TAPER:
        pts = [(x0, top), (x0, BAR_Y0 - d), (x1 - d, BAR_Y0 - d), (x1, BAR_Y0), (x1, top)]
    else:
        pts = [(x0, top), (x0, BAR_Y0 - d), (x1, BAR_Y0 - d), (x1, top)]
    return extrude(Polygon(*pts, align=None), THICK, dir=(0, 0, 1))


def clip(with_keel: bool, groove_w=None, keel_depth=None, print_skin=False):
    keel_depth = KEEL_DEPTH if keel_depth is None else keel_depth
    groove_w = GROOVE_W if groove_w is None else groove_w
    part = profile_solid() + roof()
    if not (with_keel and keel_depth > 0):
        return part - grooves(0.0, groove_w)
    part += keel(keel_depth)
    part -= grooves(keel_depth, groove_w)
    if print_skin and SLOT_SKIN > 0:
        # thin wall closing the slot along the keel's flat bottom (cut off after printing)
        x0, x1 = KEEL_X[0], (KEEL_X[1] - keel_depth) if KEEL_TAPER else KEEL_X[1]
        part += Pos(x0, BAR_Y0 - keel_depth, THICK / 2 - groove_w / 2 - 0.05) * Box(
            x1 - x0, SLOT_SKIN, groove_w + 0.1, align=MIN)
    return part


def flat_for_print(part):
    """Print orientation: lying flat as modelled (Z = tooth width, layers hold the whole J)."""
    bb = part.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * part


# ------------------------------------------------------------ fit-test tops
# Just the tooth (no arm/hook) so it slides on and off the blade easily.
# Cut at the end of the wall notch so it sits on the wall at the real height.
FIT_TESTS = [            # (label, slot width, keel depth) -- 2.2 slot confirmed to fit
    ("K3", GROOVE_W, 3.0),
    ("K5", GROOVE_W, 5.0),
    ("K8", GROOVE_W, 8.0),
]
LABEL_DEPTH = 0.5
LABEL_SIZE = 5.5


def fit_test(label, groove_w, keel_depth):
    part = clip(True, groove_w, keel_depth)
    part = part & Pos(0, 0, -1) * Box(WALL_NOTCH_X[1], 40, THICK + 2, align=MIN)  # tooth only, no hook
    # engrave the label on the outer side face (Z=0), reading upward in print orientation
    face = Plane(origin=((TOOTH_X0 + KEEL_X[1]) / 2 - 1, (BAR_Y0 - keel_depth + BAR_Y1) / 2, 0),
                 x_dir=(0, 1, 0), z_dir=(0, 0, -1))
    txt = face * Text(label, font_size=LABEL_SIZE)
    part -= extrude(txt, LABEL_DEPTH, dir=(0, 0, 1))
    # print orientation: tooth tip on the bed, wall end up
    part = part.rotate(Axis.Y, -90)
    bb = part.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * part


def write(part, name, step=True):
    OUT.mkdir(exist_ok=True)
    export_stl(part, str(OUT / f"{name}.stl"), tolerance=0.005, angular_tolerance=0.1)
    if step:
        export_step(part, str(OUT / f"{name}.step"))
    bb = part.bounding_box().size
    print(f"wrote {name}  volume={part.volume:.0f} mm3  size={bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f}")


if __name__ == "__main__":
    if "--rebuild" in sys.argv:
        write(clip(with_keel=False), "ice-tooth_rebuild", step=False)
    elif "--keel" in sys.argv:
        # one-off full part at another keel depth, e.g. --keel 3 -> ice-tooth_keel3_print
        depth = float(sys.argv[sys.argv.index("--keel") + 1])
        name = f"ice-tooth_keel{depth:g}"
        if "--arm-extra" in sys.argv:   # e.g. --arm-extra 1.5 -> ice-tooth_keel3_arm+1.5_print
            ARM_EXTRA = float(sys.argv[sys.argv.index("--arm-extra") + 1])
            name += f"_arm+{ARM_EXTRA:g}"
        part = clip(with_keel=True, keel_depth=depth)
        write(part, name)
        printable = flat_for_print(clip(with_keel=True, keel_depth=depth, print_skin=True))
        write(printable, f"{name}_print", step=False)
        mesher = Mesher()
        mesher.add_shape(printable)
        mesher.write(str(OUT / f"{name}_print.3mf"))
    else:
        part = clip(with_keel=True)
        write(part, "ice-tooth_keel")
        # Print flat (strongest for snapping on; standing up it snapped at the neck
        # above the notch). The slot skin makes the slot ceiling a short bridge.
        printable = flat_for_print(clip(with_keel=True, print_skin=True))
        write(printable, "ice-tooth_keel_print", step=False)
        mesher = Mesher()
        mesher.add_shape(printable)
        mesher.write(str(OUT / "ice-tooth_keel_print.3mf"))

        # fit-test set: one row on the plate, 8 mm apart, plus a 3MF of separate objects
        tests, x = [], 0.0
        for label, w, d in FIT_TESTS:
            t = fit_test(label, w, d)
            bb = t.bounding_box()
            tests.append(Pos(x, 0, 0) * t)
            x += bb.size.X + 8
        write(Compound(tests), "ice-tooth_fit-test-set_print", step=False)
        mesher = Mesher()
        for t in tests:
            mesher.add_shape(t)
        mesher.write(str(OUT / "ice-tooth_fit-test-set_print.3mf"))
