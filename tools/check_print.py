"""Pre-print sanity check for exported STL files (in print orientation, Z up).

Usage: python check_print.py PART.stl [PART2.stl ...]
Reports: size (fits the bed?), separate bodies, watertightness, and
overhang area (faces steeper than 45 deg that aren't on the bed), grouped by
height so you can find what needs support.
"""
import sys

import numpy as np
import trimesh

BED = (256, 256, 256)  # Bambu P1S / X1C; change for your printer

for path in sys.argv[1:]:
    m = trimesh.load(path, force="mesh")
    bodies = m.split(only_watertight=False)
    size = m.extents
    print(f"== {path}")
    print(f"   size {size.round(1).tolist()} mm  fits bed: {all(size <= BED)}")
    print(f"   bodies {len(bodies)}  watertight {m.is_watertight}  volume {m.volume / 1000:.1f} cm3")
    if m.bounds[0][2] < -0.01:
        print(f"   WARNING: part goes below the bed (min z {m.bounds[0][2]:.2f})")
    down = (m.face_normals[:, 2] < -0.71) & (m.triangles_center[:, 2] > m.bounds[0][2] + 0.3)
    if down.any():
        z = m.triangles_center[down][:, 2].round(1)
        a = m.area_faces[down]
        print(f"   overhang area {a.sum():.0f} mm2 (needs support or a redesign if large):")
        for h in sorted(set(z)):
            print(f"     z={h:6.1f}  {a[z == h].sum():8.1f} mm2")
    else:
        print("   no overhangs: prints without support")
