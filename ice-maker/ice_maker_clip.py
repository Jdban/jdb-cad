"""Replacement stripper tooth for the ice maker.

Every version and fit test is a frozen `Tooth` (all dimensions in one place),
built by the same geometry functions. Printed versions are frozen in out/ (see
PARTS.md) and are never regenerated over.

    ../.venv/bin/python ice_maker_clip.py list         targets, and which were printed
    ../.venv/bin/python ice_maker_clip.py I5           build a version into out/
    ../.venv/bin/python ice_maker_clip.py test-N       build a fit-test plate
    ../.venv/bin/python ice_maker_clip.py rebuild      the original Tinkercad part, to check vs original/

Units mm. The profile is drawn in XY and is `thick` wide in Z (along the wall).
Coordinates match the original Tinkercad file:
    crossbar (the tooth) runs along X from tooth_x0 to the outer wall
    arm hangs down the outside of the wall (-Y), hook curls under the wall bottom
    slot in the tooth's underside (and keel) rides on the grey blade
"""
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from build123d import Align, Axis, Box, Keep, Plane, Polygon, Pos, extrude, split

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "tools"))
from kit import Build, params_of, row, run, to_bed  # noqa: E402
from label import engrave  # noqa: E402

MIN = (Align.MIN, Align.MIN, Align.MIN)


@dataclass(frozen=True)
class Tooth:
    # tooth (crossbar)
    thick: float = 14.0             # width along the wall (original teeth ~14.5 at the base)
    tooth_x0: float = 16.0
    tooth_x1: float = 51.0          # outer face (moves with arm_shift)
    bar_y0: float = 18.0            # underside
    bar_y1: float = 23.8            # top, before the peaked roof
    roof_peak: float = 26.0
    roof_hip_x: float = 19.0        # ridge starts here; slopes down to tooth_x0
    # arm and hook (outside the wall)
    arm_x0: float = 48.1            # arm inner face = wall outer face
    arm_bottom: float = -22.0
    hook_x0: float = 43.0           # hook tip reaches in to here
    hook_top: float = -19.0
    hook_lip_x: float = 45.9
    hook_lip_y: float = -19.91
    arm_extra: float = 0.0          # longer arm: hook this much lower
    arm_shift: float = 0.0          # arm, hook and outer face this much further out (longer notch)
    # notch over the wall top / stub
    notch_x0: float = 42.0
    notch_x1: float = 48.1          # 48.1 = flush with the arm face (original had 48.0, a 0.1 step)
    notch_depth: float = 3.0
    # slot for the grey blade
    groove_w: float = 2.2           # fits the thin part of the blade (confirmed)
    groove_x: tuple = (16.0, 36.0)
    groove_wide_w: float = 5.0      # near the wall (blade base is 6.37 mm: use 7)
    groove_wide_x: tuple = (36.0, 42.0)
    groove_depth: float = 2.0
    wide_from: float | None = None  # widen the slot through the keel from this X to the wall
    # keel: full-width extension under the tooth, slot running through it
    keel_depth: float = 0.0         # 0 = no keel. Must stay above the water line.
    keel_x: tuple = (16.0, 36.0)
    keel_taper: bool = True         # 45 deg up to the bar at the wall end
    # printing
    lead_in: float = 1.0            # chamfers on the hook tip and notch mouth (slide on, don't catch)
    slot_skin: float = 0.0          # >0: thin printed skin closing the slot (cut out after printing).
                                    #   Default 0: use slicer supports (user preference)

    # positions after arm_shift
    @property
    def x1(self): return self.tooth_x1 + self.arm_shift
    @property
    def ax0(self): return self.arm_x0 + self.arm_shift
    @property
    def nx1(self): return self.notch_x1 + self.arm_shift


def profile(t: Tooth):
    """Crossbar + arm + hook, extruded `thick` in Z, with the notch cut out."""
    s, e, L = t.arm_shift, t.arm_extra, t.lead_in
    bottom, top, lip_y = t.arm_bottom - e, t.hook_top - e, t.hook_lip_y - e
    hx, lx = t.hook_x0 + s, t.hook_lip_x + s
    pts = [
        (t.tooth_x0, t.bar_y0), (t.tooth_x0, t.bar_y1), (t.x1, t.bar_y1), (t.x1, bottom),
        (hx + L, bottom), (hx, bottom + L), (hx, top - L), (hx + L, top),   # chamfered hook tip
        (lx, top), (lx, lip_y), (t.ax0, lip_y), (t.ax0, t.bar_y0),
    ]
    pts = [p for i, p in enumerate(pts) if p != pts[i - 1]]
    body = extrude(Polygon(*pts, align=None), t.thick, dir=(0, 0, 1))
    body -= Pos(t.notch_x0, t.bar_y0 - 1, -1) * Box(
        t.nx1 - t.notch_x0, t.notch_depth + 1, t.thick + 2, align=MIN)
    if L > 0:   # chamfer the notch mouth
        x0, d = t.notch_x0, 0.01
        tri = Polygon((x0 - L, t.bar_y0 - d), (x0 + d, t.bar_y0 - d), (x0 + d, t.bar_y0 + L), align=None)
        body -= Pos(0, 0, -1) * extrude(tri, t.thick + 2, dir=(0, 0, 1))
    return body


def roof(t: Tooth):
    """Peaked top: triangle across the width, ridge along X, hipped at the tip end."""
    tri = Plane.YZ.offset(t.tooth_x0) * Polygon(
        (t.bar_y1, 0), (t.roof_peak, t.thick / 2), (t.bar_y1, t.thick), align=None)
    r = extrude(tri, t.x1 - t.tooth_x0)
    hip = Plane(origin=(t.tooth_x0, t.bar_y1, 0),
                z_dir=(-(t.roof_peak - t.bar_y1), t.roof_hip_x - t.tooth_x0, 0))
    return split(r, bisect_by=hip, keep=Keep.BOTTOM)


def slots(t: Tooth):
    c, d = t.thick / 2, t.keel_depth
    y0 = t.bar_y0 - d - 1
    g = Pos(t.groove_x[0] - 1, y0, c - t.groove_w / 2) * Box(
        t.groove_x[1] - t.groove_x[0] + 1, t.bar_y0 + t.groove_depth - y0, t.groove_w, align=MIN)
    g += Pos(t.groove_wide_x[0], t.bar_y0 - 1, c - t.groove_wide_w / 2) * Box(
        t.groove_wide_x[1] - t.groove_wide_x[0] + 0.01, t.groove_depth + 1, t.groove_wide_w, align=MIN)
    if t.wide_from is not None:
        g += Pos(t.wide_from, y0, c - t.groove_wide_w / 2) * Box(
            t.groove_wide_x[1] - t.wide_from + 0.01, t.bar_y0 + t.groove_depth - y0, t.groove_wide_w, align=MIN)
    return g


def keel(t: Tooth):
    (x0, x1), d, top = t.keel_x, t.keel_depth, t.bar_y0 + 0.5   # sinks into the bar: one solid
    if t.keel_taper:
        pts = [(x0, top), (x0, t.bar_y0 - d), (x1 - d, t.bar_y0 - d), (x1, t.bar_y0), (x1, top)]
    else:
        pts = [(x0, top), (x0, t.bar_y0 - d), (x1, t.bar_y0 - d), (x1, top)]
    return extrude(Polygon(*pts, align=None), t.thick, dir=(0, 0, 1))


def tooth(t: Tooth, for_print=False):
    """The whole part in the in-use position. for_print adds the slot skin if set."""
    part = profile(t) + roof(t)
    if t.keel_depth <= 0:
        return part - slots(t)
    part = part + keel(t) - slots(t)
    if for_print and t.slot_skin > 0:
        x0 = t.keel_x[0]
        x1 = t.keel_x[1] - t.keel_depth if t.keel_taper else t.keel_x[1]
        part += Pos(x0, t.bar_y0 - t.keel_depth, t.thick / 2 - t.groove_w / 2 - 0.05) * Box(
            x1 - x0, t.slot_skin, t.groove_w + 0.1, align=MIN)
        if t.wide_from is not None and t.wide_from < x1:
            part += Pos(t.wide_from, t.bar_y0 - t.keel_depth, t.thick / 2 - t.groove_wide_w / 2 - 0.05) * Box(
                x1 - t.wide_from, t.slot_skin, t.groove_wide_w + 0.1, align=MIN)
    return part


# ------------------------------------------------------------------ versions
ORIGINAL = Tooth(lead_in=0.0, notch_x1=48.0)       # "Ice Maker Fix JDB (4)": I1
KEEL3 = replace(ORIGINAL, keel_depth=3.0)
VERSIONS = {   # id: (tooth, print orientation, engrave the id?, what changed)
    "I1": (ORIGINAL, "flat", False, "Original Tinkercad tooth (rebuild), 2 mm groove, no keel"),
    "I2": (KEEL3, "standing", False, "3 mm keel, printed standing (snapped at the neck)"),
    "I3": (replace(KEEL3, lead_in=1.0, slot_skin=0.6), "flat", False,
           "3 mm keel, flat with slot skin and lead-ins"),
    "I4": (replace(KEEL3, lead_in=1.0, slot_skin=0.6, notch_x1=48.1, wide_from=28.0,
                   groove_wide_w=7.0, arm_extra=0.5), "flat", True,
           "Slot 7 mm near the wall (blade base 6.37), arm +0.5"),
    # Next version: start from I5 with slot_skin=0.0 (supports instead of a skin).
}
VERSIONS["I5"] = (replace(VERSIONS["I4"][0], arm_shift=0.5), "flat", True,
                  "I4 + notch 6.6 mm to the arm (N6.6 won)")

PETG_CARD = [["Filament", "PETG (colored)", "Pick any PETG preset, e.g. Generic PETG"],
             ["Wall loops", "6", "Default 2"],
             ["Sparse infill density", "100%", "Default 15%"]]


def version_card(vid, t, orient):
    rows = list(PETG_CARD)
    if t.keel_depth > 0 and t.slot_skin <= 0 and orient == "flat":
        rows.append(["Enable support", "On (tree)", "Only under the blade slot ceiling. Not build-plate-only"])
    if orient == "flat" and t.slot_skin > 0:
        note = ("Prints FLAT, no supports, don't auto-orient. Before installing, cut out the thin skin "
                "across the bottom of the slot, away from the ice maker.")
    elif orient == "flat":
        note = ("Prints FLAT, don't auto-orient. Pull the supports out of the slot with pliers, away "
                "from the ice maker, and check no bits are left.")
    else:
        note = "Prints standing on the arm's outer face. Layer lines cross the neck above the notch (weak)."
    return {"title": f"{vid}: ice maker tooth", "settings": rows, "note": note}


def build_version(vid):
    t, orient, label, what = VERSIONS[vid]
    printable = tooth(t, for_print=True)
    if label:   # ID on the arm's outer face, running along it (touches nothing)
        printable = engrave(printable, vid, origin=(t.x1, 0.0, t.thick / 2),
                            normal=(1, 0, 0), up=(0, 0, 1), size=5.0, depth=0.5)
    if orient == "standing":
        printable = printable.rotate(Axis.Y, 90)   # arm face down, tooth up
    return Build(printable=to_bed(printable), part=tooth(t), params=params_of(t) | {"orient": orient},
                 settings=version_card(vid, t, orient), describe=what)


# ----------------------------------------------------------------- fit tests
# Tops only, no hook, so they slide on and off. One variable per set.
TOP_LABEL = dict(size=4.5, depth=0.5)


def top_piece(t: Tooth, label):
    """Tooth only (cut at the notch end), label along the side, standing on its tip."""
    part = tooth(t) & Pos(0, 0, -1) * Box(t.nx1, 40, t.thick + 2, align=MIN)
    part = engrave(part, label, origin=(27.0, (t.bar_y0 + t.bar_y1) / 2 + 0.2, 0.0),
                   normal=(0, 0, -1), up=(0, 1, 0), **TOP_LABEL)
    return part.rotate(Axis.Y, -90)


def notch_piece(t: Tooth, label, arm_stub=12.0):
    """Top + short arm stub (no hook), label on top, flat."""
    part = tooth(t, for_print=True)
    y_cut = t.bar_y0 + t.notch_depth - arm_stub
    part = part & Pos(0, y_cut, -1) * Box(80, 40, t.thick + 2, align=MIN)
    return engrave(part, label, origin=(27.0, (t.bar_y0 + t.bar_y1) / 2 - 0.5, t.thick),
                   normal=(0, 0, 1), up=(0, 1, 0), size=4.0, depth=0.5)


TOP = replace(ORIGINAL, lead_in=1.0)                   # tops as printed on 2026-11-08/09
NOTCH_BASE = replace(VERSIONS["I4"][0], arm_extra=0.0)
TESTS = {   # name: (pieces [(label, tooth)], kind, layout axis, what it tests)
    "test-K": ([(f"K{d:g}", replace(TOP, keel_depth=d)) for d in (3.0, 5.0, 8.0)], "top", 0,
               "Keel depth vs water line"),
    "test-EW": ([("E30", replace(TOP, keel_depth=3.0, keel_x=(16.0, 30.0))),
                 ("E26", replace(TOP, keel_depth=3.0, keel_x=(16.0, 26.0))),
                 ("W30", replace(TOP, keel_depth=3.0, wide_from=30.0))], "top", 0,
                "Where the keel hits the blade base near the wall"),
    "test-N": ([(f"N{6.1 + s:g}", replace(NOTCH_BASE, arm_shift=s)) for s in (-0.5, 0.0, 0.5, 1.0)],
               "notch", 1, "Notch length from the wall top to the arm"),
}


def build_test(name):
    pieces, kind, axis, what = TESTS[name]
    parts = [top_piece(t, lab) if kind == "top" else notch_piece(t, lab) for lab, t in pieces]
    card = {"title": f"{name}: {what} ({' / '.join(lab for lab, _ in pieces)})",
            "settings": [["Process preset", "0.28mm Extra Draft", "Default 0.20mm Standard: fit test only"]],
            "note": "Don't auto-orient. No hook, so nothing to snap: slide each on and compare."}
    return Build(printable=row(parts, gap=8.0 if axis == 0 else 6.0, axis=axis),
                 params={lab: params_of(t) for lab, t in pieces} | {"kind": kind},
                 settings=card, describe=what)


def build_rebuild():
    """Original Tinkercad part, to check against original/ (tools/compare.py)."""
    return Build(printable=to_bed(tooth(ORIGINAL)), part=tooth(ORIGINAL), params=params_of(ORIGINAL),
                 describe="Rebuild of the original (4) part")


TARGETS = {vid: (lambda vid=vid: build_version(vid)) for vid in VERSIONS}
TARGETS |= {name: (lambda name=name: build_test(name)) for name in TESTS}
TARGETS["rebuild"] = build_rebuild
for vid in VERSIONS:
    TARGETS[vid].__doc__ = VERSIONS[vid][3]
for name in TESTS:
    TARGETS[name].__doc__ = TESTS[name][3]

if __name__ == "__main__":
    run(TARGETS, __file__, HERE / "out")
