# jdb-cad

Parametric 3D-printing parts, built with an AI coding agent.

- Parts are Python scripts using [build123d](https://github.com/gumyr/build123d) (OpenCascade CAD kernel):
  one dataclass of dimensions per part, versions and fit tests as named variations.
- Meshes are checked with [trimesh](https://trimesh.org): rebuild vs original, overhangs, bed fit,
  and a regression check that every printed part still rebuilds exactly.
- A small local viewer ([three.js](https://threejs.org)) shows models live as they change, with
  print-settings cards, section / measure / overhang tools, and a project tracker page.

The workflow the agent follows is in [AGENTS.md](AGENTS.md). `ice-maker/` is a worked example
(a replacement stripper tooth for an ice maker, with its fit-test plates and parts log), and
`examples/bracket.py` is the template for new parts.

## Quick start

```bash
docker compose build && docker compose up -d viewer   # http://localhost:8765 (tracker: /tracker)
tools/cad tools/regress.py                            # everything rebuilds and checks out
tools/new_project.sh my-part M "What my part is"      # start a project from the template
cd my-part && ../tools/cad my_part.py list            # run a part script in the container
```

Without Docker: `uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt`,
then `viewer/start.sh` and `.venv/bin/python` wherever `tools/cad` appears.
