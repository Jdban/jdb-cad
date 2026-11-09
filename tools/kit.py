"""Shared helpers for part scripts: export, plates, settings cards, frozen versions, CLI.

A part script defines *targets*: functions that return a Build. kit.run() gives it
a small CLI and writes everything into the project's out/ folder:

    <stem>.step / <stem>.stl         in-use orientation (only if Build.part is set)
    <stem>_print.stl / _print.3mf    print orientation (a list = one plate, separate objects)
    <stem>_print.settings.json       settings card for the viewer (only non-default settings)
    <stem>.params.json               every parameter the build used, plus frozen/printed info

Printed versions are FROZEN (kit freeze <stem>): their files are what was actually
printed, and the CLI refuses to overwrite them without --force.

    python part.py list                 show targets and which are frozen
    python part.py I5                   build target I5 into out/
    python part.py I5 --out /tmp/x      build elsewhere (used by tools/regress.py)
    python part.py freeze I5 "2026-11-09, colored PETG"
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from build123d import Compound, Mesher, Pos, export_step, export_stl

STL_TOLERANCE = 0.01        # mm; one value for every script
STL_ANGULAR = 0.1           # radians


@dataclass
class Build:
    printable: object | list          # print-oriented part, or a list of parts for one plate
    params: dict                      # everything that determines the geometry
    part: object | None = None        # in-use orientation (STEP + STL), optional
    settings: dict | None = None      # settings card: {"title", "settings": [[k, v, why]], "note"}
    describe: str = ""                # one line for PARTS.md / list


def to_bed(part):
    """Move a part so its bounding box starts at the origin (lying on Z=0)."""
    bb = part.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * part


def row(parts, gap=8.0, axis=0):
    """Lay parts out in a row along X (axis=0) or Y (axis=1), each on the bed."""
    out, at = [], 0.0
    for p in parts:
        p = to_bed(p)
        size = p.bounding_box().size
        out.append(Pos(at, 0, 0) * p if axis == 0 else Pos(0, at, 0) * p)
        at += (size.X if axis == 0 else size.Y) + gap
    return out


def params_of(obj) -> dict:
    """Dataclass (or dict) of parameters -> plain JSON-able dict."""
    d = dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else dict(obj)
    return json.loads(json.dumps(d, default=str))


def write_stl(part, path):
    """STL at the shared resolution (for context/mockup meshes that aren't print targets)."""
    export_stl(part, str(path), tolerance=STL_TOLERANCE, angular_tolerance=STL_ANGULAR)


_stl = write_stl


def is_frozen(out_dir: Path, stem: str) -> bool:
    try:
        return json.loads((out_dir / f"{stem}.params.json").read_text()).get("frozen", False)
    except (OSError, ValueError):
        return False


def write_build(stem: str, b: Build, out_dir: Path, script: str, force=False):
    out_dir.mkdir(parents=True, exist_ok=True)
    if is_frozen(out_dir, stem) and not force:
        raise SystemExit(f"{stem} is frozen (it was printed). Its files are the record of that "
                         f"print. Use a new ID, or --force to overwrite on purpose.")
    if b.part is not None:
        export_step(b.part, str(out_dir / f"{stem}.step"))
        _stl(b.part, out_dir / f"{stem}.stl")
    parts = b.printable if isinstance(b.printable, list) else [b.printable]
    _stl(parts[0] if len(parts) == 1 else Compound(parts), out_dir / f"{stem}_print.stl")
    mesher = Mesher()
    for p in parts:
        mesher.add_shape(p)
    mesher.write(str(out_dir / f"{stem}_print.3mf"))
    if b.settings:
        (out_dir / f"{stem}_print.settings.json").write_text(json.dumps(b.settings, indent=2))
    record = {"stem": stem, "script": script, "describe": b.describe, "params": b.params,
              "built": datetime.date.today().isoformat(), "frozen": False}
    (out_dir / f"{stem}.params.json").write_text(json.dumps(record, indent=2))
    vol = sum(p.volume for p in parts)
    print(f"wrote {stem}: {len(parts)} object(s), {vol / 1000:.2f} cm3")


def freeze(out_dir: Path, stem: str, printed: str):
    p = out_dir / f"{stem}.params.json"
    record = json.loads(p.read_text())
    record.update(frozen=True, printed=printed)
    p.write_text(json.dumps(record, indent=2))
    print(f"froze {stem} ({printed})")


def run(targets: dict, script_file: str, out_dir: Path):
    """CLI: list | <target> [--out DIR] [--force] | freeze <stem> "<when, material>"."""
    args = sys.argv[1:]
    out = Path(args[args.index("--out") + 1]) if "--out" in args else out_dir
    force = "--force" in args
    args = [a for i, a in enumerate(args) if a != "--force" and a != "--out" and
            (i == 0 or args[i - 1] != "--out")]
    script = Path(script_file).resolve().relative_to(Path(__file__).resolve().parent.parent).as_posix()
    if not args or args[0] == "list":
        for name, fn in targets.items():
            tag = " [frozen: printed]" if is_frozen(out_dir, name) else ""
            print(f"  {name:10}{tag}  {(fn.__doc__ or '').strip().splitlines()[0] if fn.__doc__ else ''}")
        return
    if args[0] == "freeze":
        freeze(out, args[1], args[2] if len(args) > 2 else datetime.date.today().isoformat())
        return
    for name in args:
        if name not in targets:
            raise SystemExit(f"unknown target {name!r}; try: list")
        write_build(name, targets[name](), out, script, force=force)
