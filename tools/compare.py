"""Compare a rebuilt mesh against the matching bodies of an original mesh.

Usage: python compare.py ORIGINAL.stl REBUILD.stl
Takes the original's bodies that fall inside the rebuild's bounding box (1 mm
slack), unions them, then reports bounding box, volume and surface deviation.
"""
import sys

import numpy as np
import trimesh

orig_all = trimesh.load(sys.argv[1], force="mesh")
new = trimesh.load(sys.argv[2], force="mesh")
lo, hi = new.bounds[0] - 1, new.bounds[1] + 1
bodies = [b for b in orig_all.split(only_watertight=False)
          if (b.bounds[0] >= lo).all() and (b.bounds[1] <= hi).all()]
if not bodies:
    sys.exit("No body of ORIGINAL lies inside REBUILD's bounding box (+1 mm). "
             "Are both files in the same position and orientation?")
orig = trimesh.boolean.union(bodies, engine="manifold") if len(bodies) > 1 else bodies[0]

n = 40000
p_new = new.sample(n)
p_orig = orig.sample(n)
d1 = np.abs(trimesh.proximity.signed_distance(orig, p_new))
d2 = np.abs(trimesh.proximity.signed_distance(new, p_orig))
d = np.concatenate([d1, d2])
print(f"bodies matched : {len(bodies)}")
print(f"bbox original  : {orig.bounds.round(2).tolist()}")
print(f"bbox rebuild   : {new.bounds.round(2).tolist()}")
print(f"volume         : original {orig.volume:.1f}  rebuild {new.volume:.1f}  "
      f"diff {100 * (new.volume - orig.volume) / orig.volume:+.3f}%")
print(f"deviation mm   : max {d.max():.4f}  p99 {np.percentile(d, 99):.4f}  mean {d.mean():.4f}")
