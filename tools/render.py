"""Render PNG views of one or more meshes so an agent can look at them.

Usage: python render.py OUT.png PART.stl [PART2.stl ...] [--section-x X] [--section-y Y] [--section-z Z]
Draws front / top / side / iso views per file (orthographic, shaded), plus
optional 2D cross-section outlines. Read the PNG back to check the shape.
"""
import argparse

import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("files", nargs="+")
ap.add_argument("--section-x", type=float)
ap.add_argument("--section-y", type=float)
ap.add_argument("--section-z", type=float)
args = ap.parse_args()

VIEWS = {"front": (0, -90), "top": (90, -90), "side": (0, 0), "iso": (25, -55)}
sections = [(n, v) for n, v in (("x", args.section_x), ("y", args.section_y), ("z", args.section_z)) if v is not None]
cols = len(VIEWS) + len(sections)
light = np.array([0.4, -0.6, 0.7])
light /= np.linalg.norm(light)

fig = plt.figure(figsize=(4.2 * cols, 4.2 * len(args.files)))
for r, path in enumerate(args.files):
    m = trimesh.load(path, force="mesh")
    b = m.bounds
    c, rad = b.mean(0), (b[1] - b[0]).max() / 2
    for k, (name, (el, az)) in enumerate(VIEWS.items()):
        ax = fig.add_subplot(len(args.files), cols, r * cols + k + 1, projection="3d")
        sh = 0.35 + 0.65 * np.clip(np.abs(m.face_normals @ light), 0, 1)
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=np.c_[0.3 * sh, 0.6 * sh, 0.9 * sh],
                                             edgecolor=(0, 0, 0, 0.15), linewidths=0.2))
        ax.set_xlim(c[0] - rad, c[0] + rad); ax.set_ylim(c[1] - rad, c[1] + rad); ax.set_zlim(c[2] - rad, c[2] + rad)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_proj_type("ortho")
        ax.set_title(f"{path.split('/')[-1]}: {name}", fontsize=8)
    for k, (axis, val) in enumerate(sections):
        ax = fig.add_subplot(len(args.files), cols, r * cols + len(VIEWS) + k + 1)
        n = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[axis]
        keep = {"x": [1, 2], "y": [0, 2], "z": [0, 1]}[axis]
        s = m.section(plane_origin=np.array(n) * val, plane_normal=n)
        if s is not None:
            for e in s.discrete:
                ax.plot(e[:, keep[0]], e[:, keep[1]], "k-", lw=1)
        ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.set_title(f"section {axis}={val}", fontsize=8)
plt.tight_layout()
plt.savefig(args.out, dpi=70)
print(f"wrote {args.out}")
