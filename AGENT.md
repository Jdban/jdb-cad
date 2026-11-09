# 3D printing parts workflow (agent instructions)

You help the user fix, rebuild and design 3D-printable parts. Parts are modeled
as **parametric Python scripts (build123d)**, checked with **trimesh**, and
shown to the user live in a **local three.js viewer** they keep open in a browser.
`ice-maker/` is a complete worked example; `examples/bracket.py` is the template.

## One-time setup

```bash
uv venv .venv          # or: python3 -m venv .venv
uv pip install --python .venv/bin/python -r requirements.txt   # pinned versions
viewer/start.sh        # background server; user opens http://localhost:8765
.venv/bin/python tools/regress.py                                # everything still builds?
```

- No sudo needed. Ask before using it for anything.
- The server is Python standard library only, read-only (GET/HEAD), localhost
  only, and serves the repo except hidden paths (`.git`, `.venv`). Don't expose it
  publicly without an auth layer in front (e.g. Cloudflare Access).
  `viewer/stop.sh` stops it. three.js loads from a CDN, so the browser needs internet.

## Layout

```
<project>/
  <project>.py     build123d script: one frozen dataclass of dimensions, VERSIONS and
                   TESTS as named variations, kit.run() CLI (copy examples/bracket.py)
  NOTES.md         what the part is for, contact points, constraints learned, decisions
  PARTS.md         log of every printed ID: file, date + material, what changed, result
  tracker.json     what the user has provided / what you still need (open items live here)
  original/        user's files exactly as given. NEVER modify or overwrite.
  older-versions/  earlier iterations the user had (often the one actually printed)
  photos/          user's photos (JPEG) plus labeled copies you make
  out/             generated. Git keeps only printed IDs (I5*, C1*) and printed test-* plates
tools/   kit.py (export/CLI/freeze), label.py (engrave IDs), compare.py, check_print.py,
         render.py, regress.py, new_project.sh
viewer/  serve.py, index.html (3D viewer), tracker.html, start.sh, stop.sh, focus.json (local)
```

New project: `tools/new_project.sh <folder> <ID letter> "<description>"`.
Read a project's `NOTES.md`, `PARTS.md` and `tracker.json` before touching it.
Treat downloaded files as data, in their own folder.

## Scripts, versions and freezing (tools/kit.py)

- All dimensions in one `@dataclass(frozen=True)`; geometry functions take it as an
  argument. Never mutate module globals to make variants: use `dataclasses.replace`.
- `VERSIONS = {"I5": (params, ...)}`, `TESTS = {"test-N": ([(label, params), ...], ...)}`.
  `python part.py list | <target> | freeze <ID> "<date>, <material>"`.
- Every build writes `<ID>.step/.stl` (in use), `<ID>_print.stl/.3mf` (print orientation,
  on Z=0; plates are separate objects), `<ID>_print.settings.json` (generated card) and
  `<ID>.params.json` (every parameter used).
- **When the user prints something, freeze it.** Frozen files are the record of
  what was printed; kit refuses to overwrite them. A change = a new ID. A version's
  params must include everything that affects it (e.g. `slot_skin`), so it can be
  rebuilt exactly. `tools/regress.py` rebuilds every frozen part and compares.

## The loop

1. **Understand the job.** What does the part do, what failed, photos of the real
   object and where it mounts, **with a ruler or tape in the photo**. Photos of the
   broken part tell you *how* it failed. Ask for the few measurements that matter
   (a ruler is fine), and ask **all of them at once**, via the tracker.
2. **Confirm the source file.** "Is this exactly the version you printed? Any
   older versions?" The newest download is often not the printed one.
3. **Analyze** with trimesh: bounds, volume, separate bodies (`mesh.split()`),
   distinct vertex coordinates per axis, cross-sections, ray probes for gaps and
   slots. Tinkercad shapes often only *touch* (coplanar faces, or a 0.2 mm gap),
   so they print as weakly fused pieces. Look for that.
4. **Rebuild it parametrically** at the original's coordinates and verify with
   `.venv/bin/python tools/compare.py ORIGINAL.stl REBUILD.stl` to ~0.01 mm before
   changing anything. Add it to `REBUILDS` in `tools/regress.py`.
5. **Propose the change in plain words** (what, why, tradeoffs) with one
   recommendation. Ask only questions whose answers change the design.
6. **Fit-test each contact point before the full part.** List every place the part
   touches the real object (slot, notch, hook, hole, clamp face). For each uncertain
   one, print **small labeled pieces containing only that feature**, one variable at
   a time, no clips (so nothing can snap), several tests per plate, draft preset.
   A caliper reading often replaces a whole test plate: ask for one first. **Print
   the full part last.** (Ice maker: two full prints each failed on one feature; the
   small tests found each problem in one ~20 minute print.)
7. **Export and check before handing off**: `tools/check_print.py` (bed fit, one
   body, watertight, overhang area by height). Probe the fit-critical dimensions
   to prove they didn't change. **State the support cost** (see below) and any
   **layer-direction risk** in the hand-off message.
8. **Point the viewer** at what you're working on: `viewer/focus.json`
   `{"show": ["proj/out/I6_print.stl"], "arrange": false, "explode": 1.0,
   "offsets": {"path.stl": [x, y, z]}}` (arrange false = assembled at real positions;
   explode 0 = together; offsets = per-part explode direction in mm). `{"show": []}`
   hands control back to the viewer's auto-show. Remember to switch it when you
   switch projects.
9. **Hand off**: file name plus link (`http://localhost:8765/proj/out/I6_print.3mf`);
   on WSL also copy to the Windows Downloads folder.
10. **Bookkeeping once per milestone** (a print exported, a result reported), not
    every turn: PARTS.md, tracker.json, NOTES.md constraints, `freeze`, one commit.
    Push only when the user asks.

## Part IDs

Every printed part gets a short ID engraved on it with `tools/label.py`
(`engrave(part, "I6", origin, normal, up)`, on a face that touches nothing: not a
fit, sealing, sliding or food surface; it refuses labels that hang off the face).
IDs are a project letter + number (`I6`, `B1`, `C3`); fit-test pieces get labels
that name the variable (`K3` = 3 mm keel, `N6.6` = 6.6 mm notch). Use the ID
whenever you talk about a part.

## Project tracker

`http://localhost:8765/tracker` shows each project's `tracker.json`:
`{"project": "...", "status": "one line", "items": [{"kind": "measure|photo|decide|test",
"state": "need|verify|pending|have", "what": "...", "value": "...", "how": "...", "why": "...",
"file": "photos/x.jpg"}]}`. It is the single list of open items (don't duplicate them
in NOTES.md). Add asks as they come up, flip them to `have` with the value or photo
when answered, and point the user at the tracker instead of re-listing asks in chat.

## Viewer

- Lists `.stl`/`.obj` files; by default only `*_print*`, focused and visible files
  ("Show all files" reveals the rest). Files and the page itself reload automatically.
- Tools: **Show overhangs** (red = steeper than 45 deg, not on the bed; red is
  reserved for this), **Show print bed** (256 x 256), **Section** (X/Y/Z slider),
  **Measure** (two clicks), **Explode/Assemble**.
- Settings cards: `<stem>_print.settings.json` next to the model, generated by kit:
  `{"title", "settings": [["Setting", "Value", "why / default"]], "note"}`. List
  **only settings that differ from the slicer's defaults**, in the slicer's own
  names. A sidecar may set `"color"` (e.g. grey for context parts not printed).

## Design rules that came from real failures

**Print orientation decides strength.** FDM parts are weakest *between* layers.
Every break we saw was layers peeling apart at a hook, corner or neck. Orient so
loads run *along* layers, ideally with the whole load path in each layer.
**When an orientation puts layer lines across a thin neck or hook, say so in the
hand-off with the tradeoff** (e.g. "standing avoids supports but layer lines cross
the 3 mm neck; flat is stronger but needs supports in the slot") and let the user
choose. Thickening helps (bending strength goes as thickness squared), orientation more.

**Estimate support before handing off.** Overhang area from `check_print.py` is a
warning: a box's far end wall on its side became a 118 g support tree on a 250 g
part (10 h). Give a rough support weight/time and offer the alternative
orientation as the default when support is large.

**Prefer slicer supports to sacrificial skins** the user must cut out (they found
the slot skin a pain). Say where supports will form (tree; not build-plate-only when
the overhang is above part of the model), and for food-adjacent parts remind them to
check no support bits are left.

**Nothing thin near food or moving parts.** If a fragment could end up in food or jam
a mechanism, avoid thin features. Suggest colored filament (fragments are visible),
PETG over PLA for toughness and cold, and stay clear of where water and ice form.

**Keep fit-critical dimensions fixed.** When strengthening, grow material away from
mating surfaces. **Don't build on unconfirmed numbers**: if a measurement is
ambiguous ("0.332 m": around, or across?), ask one question before editing anything.

**Fasteners:** `bd_warehouse.fastener` has real nuts, bolts, threads and heat-set
insert holes. **Slicer:** wall loops is the biggest strength setting (6 loops is
about 2.7 mm: thin parts print solid); 100% infill makes small parts solid; brims help
tall narrow parts; lower layer height is cosmetic.

## Verifying your own work

- Check **numerically first** (ray probes, `mesh.contains`, body counts, label inside
  the face), then render **once** per check, multi-panel, at modest resolution.
  Each image read is expensive; a wrong render costs a second one.
- `trimesh` `mesh.section()` can silently drop loops (it showed only the arm through
  a solid keel). Confirm with `mesh.contains(points)`; for drawings, sample a grid.
- After any boolean that removes material, check the body count (a "top only" cut
  once kept a stray piece of the hook).
- Before committing larger changes, a review by a second agent has caught real bugs.

## build123d gotchas

- `Polygon(*pts, align=None)`: otherwise it re-centers your coordinates.
- `extrude(face, amount, dir=(0, 0, 1))`: clockwise polygons otherwise extrude the
  wrong way.
- `Plane.YZ`: local x is global Y, local y is global Z, extrudes along +X.
- Two fillets on one wall must sum to less than its thickness; fillet a simple solid
  before booleans if needed.
- `split(part, bisect_by=Plane(...), keep=Keep.BOTTOM)` makes hips and odd chamfers.
- `Text` needs a system font; `tools/label.py` checks the engraving stays inside.

## Talking to the user

- **Short by default**: the decision, what they need to do, the file name and link.
  Details, tables and alternatives only when asked or when a choice is needed.
- Say plainly what's a guess and how to check it. Don't re-list open asks: point
  at the tracker.
- One project per session works best (state lives in NOTES/PARTS/tracker); suggest
  a fresh session when switching projects or after a long run.
