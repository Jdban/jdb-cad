"""Regression check: do the scripts still produce what was printed?

    .venv/bin/python tools/regress.py

1. Every frozen part (out/*.params.json with "frozen": true) is rebuilt from its
   script into a temp folder and compared with the printed record.
2. Each project's rebuild of the user's original file is compared with original/.
3. Every out/*_print.stl is checked: watertight, on the bed, fits the printer,
   expected number of objects.
Projects that aren't present (e.g. private ones on a friend's machine) are skipped.
Exit code 1 if anything fails.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
BED = (256, 256, 256)
TOL = 0.02          # mm: allowed deviation from the printed record (mesh resolution)
REBUILDS = [        # (script, target, original file): rebuild must match the user's original
    ("ice-maker/ice_maker_clip.py", "rebuild", "ice-maker/older-versions/Ice Maker Fix JDB (4).stl"),
    ("changing-table/changing_table.py", "rebuild-tray", "changing-table/original/Baby Wipes to Changing Table.stl"),
    ("changing-table/changing_table.py", "rebuild-bin", "changing-table/original/Baby Wipes to Changing Table.stl"),
]
failures = []


def deviation(a, b):
    d1 = np.abs(trimesh.proximity.signed_distance(a, b.sample(15000)))
    d2 = np.abs(trimesh.proximity.signed_distance(b, a.sample(15000)))
    return float(max(d1.max(), d2.max()))


def build(script, target, out):
    r = subprocess.run([PY, str(ROOT / script), target, "--out", str(out)], cwd=ROOT / Path(script).parent,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "build failed")


def check(name, ok, detail):
    print(f"  {'ok  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        failures.append(name)


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    print("Frozen parts reproduce what was printed:")
    for rec_path in sorted(ROOT.glob("*/out/*.params.json")):
        rec = json.loads(rec_path.read_text())
        if not rec.get("frozen"):
            continue
        stem, out = rec["stem"], tmp / rec_path.parent.parent.name
        try:
            build(rec["script"], stem, out)
            dev = deviation(trimesh.load(rec_path.parent / f"{stem}_print.stl", force="mesh"),
                            trimesh.load(out / f"{stem}_print.stl", force="mesh"))
            check(f"{rec_path.parent.parent.name}/{stem}", dev < TOL, f"max deviation {dev:.4f} mm")
        except Exception as e:  # noqa: BLE001
            check(f"{rec_path.parent.parent.name}/{stem}", False, str(e))

    print("Rebuilds match the user's original files:")
    for script, target, original in REBUILDS:
        if not (ROOT / script).exists() or not (ROOT / original).exists():
            continue
        out = tmp / "rebuilds"
        try:
            build(script, target, out)
            r = subprocess.run([PY, str(ROOT / "tools/compare.py"), str(ROOT / original), str(out / f"{target}.stl")],
                               capture_output=True, text=True)
            line = next(l for l in r.stdout.splitlines() if l.startswith("deviation"))
            dev = float(line.split("max")[1].split()[0])
            check(f"{script} {target}", dev < 0.03, f"max deviation {dev:.4f} mm vs original")
        except Exception as e:  # noqa: BLE001
            check(f"{script} {target}", False, str(e))

print("Print files are printable:")
for f in sorted(ROOT.glob("*/out/*_print.stl")):
    m = trimesh.load(f, force="mesh")
    rec = f.with_name(f.name.replace("_print.stl", ".params.json"))
    expected = 1
    if rec.exists():
        p = json.loads(rec.read_text())["params"]
        expected = sum(1 for v in p.values() if isinstance(v, dict)) or 1
    bodies = len(m.split(only_watertight=False))
    problems = []
    if not m.is_watertight:
        problems.append("not watertight")
    if abs(m.bounds[0][2]) > 0.01:
        problems.append(f"not on the bed (min z {m.bounds[0][2]:.2f})")
    if not all(m.extents <= BED):
        problems.append(f"too big {m.extents.round(0)}")
    if bodies != expected:
        problems.append(f"{bodies} objects, expected {expected}")
    check(f.relative_to(ROOT).as_posix(), not problems, ", ".join(problems) or f"{bodies} object(s), fits")

print(f"\n{'ALL GOOD' if not failures else f'{len(failures)} FAILED: ' + ', '.join(failures)}")
sys.exit(1 if failures else 0)
