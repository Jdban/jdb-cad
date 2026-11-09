# jdb-cad

Parametric 3D-printing parts, built with an AI coding agent.

- Parts are Python scripts using [build123d](https://github.com/gumyr/build123d) (OpenCascade CAD kernel).
- Meshes are checked with [trimesh](https://trimesh.org): compare a rebuild to the original, overhangs, bed fit.
- A small local viewer ([three.js](https://threejs.org)) shows models live as they change, with print-settings cards, section, measure and overhang tools.

The workflow the agent follows is in [AGENT.md](AGENT.md). `ice-maker/` is a worked example
(a replacement stripper tooth for an ice maker, with a fit-test set), and `examples/bracket.py` is a minimal part.

## Quick start

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
viewer/start.sh                      # http://localhost:8765
.venv/bin/python examples/bracket.py
```
