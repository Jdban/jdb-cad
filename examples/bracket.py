"""Example part, and the template for new projects (tools/new_project.sh copies it).

Pattern: every dimension lives in one frozen dataclass; versions and fit tests are
named variations of it (dataclasses.replace); tools/kit.py handles export, plates,
settings cards, frozen (printed) versions and the CLI.

    ../.venv/bin/python bracket.py list
    ../.venv/bin/python bracket.py X1          a version (engraved with its ID)
    ../.venv/bin/python bracket.py test-H      a fit-test plate: one variable, labeled pieces
    ../.venv/bin/python bracket.py freeze X1 "2026-11-10, PETG"   once it's printed
"""
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from build123d import Align, Axis, Box, Cylinder, Pos, Rot, fillet

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "tools"))
from kit import Build, params_of, row, run, to_bed  # noqa: E402
from label import engrave  # noqa: E402

MIN = (Align.MIN, Align.MIN, Align.MIN)


@dataclass(frozen=True)
class Bracket:
    width: float = 30.0          # along the bracket
    leg_a: float = 40.0          # horizontal leg
    leg_b: float = 30.0          # vertical leg
    thick: float = 4.0
    inner_fillet: float = 4.0    # rounds the inside corner: the stress point
    hole_d: float = 4.5          # M4 clearance


def bracket(p: Bracket):
    part = Box(p.leg_a, p.width, p.thick, align=MIN) + Box(p.thick, p.width, p.leg_b, align=MIN)
    inner = part.edges().filter_by(Axis.Y).sort_by_distance((p.thick, 0, p.thick))[0]
    part = fillet(inner, p.inner_fillet)
    part -= Pos(p.leg_a * 0.65, p.width / 2, 0) * Cylinder(p.hole_d / 2, p.thick * 3)
    part -= Pos(0, p.width / 2, p.leg_b * 0.65) * Rot(0, 90, 0) * Cylinder(p.hole_d / 2, p.thick * 3)
    return part


# Versions: ID -> (params, what changed). IDs are a project letter + number.
VERSIONS = {
    "X1": (Bracket(), "First version"),
}
# Fit tests: one variable at a time, small labeled pieces (here: hole size for the screw).
TESTS = {
    "test-H": ([(f"H{d:g}", replace(Bracket(), hole_d=d)) for d in (4.2, 4.5, 4.8)], "M4 hole clearance"),
}


def card(title):
    return {"title": title, "settings": [["Wall loops", "6", "Default 2: thin parts print solid"]]}


def build_version(vid):
    p, what = VERSIONS[vid]
    part = bracket(p)
    # ID on the outside of the vertical leg (a face that touches nothing)
    printable = engrave(part, vid, origin=(0.0, p.width / 2, p.leg_b * 0.3), normal=(-1, 0, 0), up=(0, 0, 1))
    return Build(printable=to_bed(printable), part=part, params=params_of(p), settings=card(vid), describe=what)


def build_test(name):
    pieces, what = TESTS[name]
    # just the feature under test: a tab of the horizontal leg with the hole
    parts = [engrave(bracket(p) & Pos(p.leg_a * 0.65 - 8, 0, 0) * Box(16, p.width, p.thick, align=MIN),
                     lab, origin=(p.leg_a * 0.65, 5.0, p.thick), normal=(0, 0, 1), up=(1, 0, 0), size=3.5)
             for lab, p in pieces]
    return Build(printable=row(parts), params={lab: params_of(p) for lab, p in pieces},
                 settings=card(f"{name}: {what}"), describe=what)


TARGETS = {vid: (lambda vid=vid: build_version(vid)) for vid in VERSIONS}
TARGETS |= {name: (lambda name=name: build_test(name)) for name in TESTS}
for vid, (_, what) in VERSIONS.items():
    TARGETS[vid].__doc__ = what
for name, (_, what) in TESTS.items():
    TARGETS[name].__doc__ = what

if __name__ == "__main__":
    run(TARGETS, __file__, HERE / "out")
