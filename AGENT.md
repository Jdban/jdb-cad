# 3D printing parts workflow (agent instructions)

You help the user fix, rebuild and design 3D-printable parts. Parts are modeled
as **parametric Python scripts (build123d)**, checked with **trimesh**, and
shown to the user live in a **local three.js viewer** they keep open in a browser.
`ice-maker/` is a complete worked example; `examples/bracket.py` is a minimal one.

## One-time setup

```bash
uv venv .venv          # or: python3 -m venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
viewer/start.sh        # background server; user opens http://localhost:8765
```

- No sudo needed. Ask before using it for anything.
- The server is Python standard library only, listens on localhost only, and
  serves the whole repo except hidden paths (`.git`, `.venv`).
  `viewer/stop.sh` stops it. three.js loads from a CDN, so the browser needs internet.
- Smoke test: `.venv/bin/python examples/bracket.py`, then refresh the viewer.

## Folder layout (one folder per project)

```
<project>/
  NOTES.md         what the part is for, constraints learned, decisions, open questions
  original/        user's files exactly as given. NEVER modify or overwrite.
  photos/          user's photos, plus labeled copies you make
  out/             everything generated (STEP, *_print.stl/.3mf, *.settings.json)
  <part>.py        build123d script: key dimensions as named constants at the top
tools/             compare.py, check_print.py, render.py
viewer/            serve.py, index.html, start.sh, stop.sh (focus.json is local state)
```

Put downloaded or extracted files in their own folder and treat them as data.
Read the project's `NOTES.md` before touching a project. Update it whenever you
learn a constraint ("keel must stay above the water line", "2.2 mm slot fits").

## The loop

1. **Understand the job.** Ask what the part does, what failed, and for photos
   of the real object and where it mounts. Ask for **a ruler or tape in the
   photo**, so you can estimate sizes. Photos of the broken part tell you *how*
   it failed (see "Strength" below). Ask only for the few measurements that
   matter, and say a ruler is fine.
2. **Analyze the user's file** with trimesh: bounds, volume, separate bodies
   (`mesh.split()`), distinct vertex coordinates per axis, cross-sections, and
   ray probes to measure gaps and slots. Tinkercad exports are unions of simple
   boxes, so coordinates are usually clean numbers. Tinkercad shapes often only
   *touch* (coplanar faces, or a 0.2 mm gap), so they can print as weakly fused
   pieces. Look for that. Ask whether there are older versions too: the user's
   newest download is not always the one they printed.
3. **Render and look** (`.venv/bin/python tools/render.py OUT.png PART.stl --section-z 5`, then
   read the PNG yourself) before describing anything to the user.
4. **Rebuild it parametrically** in build123d, at the same coordinates as the
   original so it overlays in the viewer. Verify with
   `.venv/bin/python tools/compare.py ORIGINAL.stl REBUILD.stl` until max deviation is roughly
   0.01 mm. Only then change things.
5. **Propose the change in plain words first** (what, why, tradeoffs), with
   one recommendation. Ask only questions whose answers change the design.
6. **Fit-test each contact point before the full part.** List every place the
   part touches the real object (slot, notch, hook, hole, clamp face). For each
   uncertain one, print **small labeled test pieces containing only that
   feature**, varying **one dimension at a time**, with no clips so they can't
   snap (engrave labels with `tools/label.py`). Put independent tests on the same
   plate, use a draft preset, and **print the full part last**, once every
   contact point is settled. (Ice maker: two full prints each failed on a single
   feature; the small tests found each problem in one ~20 minute print.)
7. **Modify, export, check.** Each script exports:
   - `name.step` in the in-use orientation (editable in any CAD tool)
   - `name_print.stl` and `.3mf`, **already rotated to the best print orientation**,
     lying on Z=0
   - `name_print.settings.json`: a settings card shown in the viewer
   Then run `.venv/bin/python tools/check_print.py PART_print.stl` (fits the bed, one body, watertight,
   overhang area by height) and render again. Probe the fit-critical
   dimensions to prove they didn't change.
8. **Point the viewer** at what you're working on by writing
   `viewer/focus.json`: `{"show": ["proj/out/name_print.stl", ...]}`.
   On refresh, and whenever the list changes, the page shows exactly those.
   Add `"arrange": false` to show parts assembled at their real positions
   (true = side by side), and `"explode": 1.0` to pull them apart (0 = assembled).
   `"offsets": {"path.stl": [x, y, z]}` sets each part's explode direction and
   distance in mm (at explode 1); without it parts move away from the average centre.
   The page reloads itself when `viewer/index.html` changes. While a focus list is set, new exports don't auto-appear. Write
   `{"show": []}` to hand control back to the viewer's "Auto-show newest change".
9. **Hand off files.** The user grabs them with the viewer's download button,
   or from a link like `http://localhost:8765/proj/out/name_print.3mf`. On WSL,
   also offer to copy them to the Windows Downloads folder.
10. **Commit** each meaningful step (`git commit`), so "revert that" is one
    command and versions can be compared. Push only when the user asks.

## Part IDs and parts logs

**Every printed part gets a short ID engraved on it**, and each project keeps a
`PARTS.md` log: ID, file, date and material, what changed, and the result. Then
"re-test I5" is unambiguous for both of you.
- IDs: a project letter plus a number (`I4`, `B1`, `C3`). Fit-test pieces get
  labels that name the variable (`K3` = 3 mm keel, `E30` = keel ends at 30).
- Engrave with `tools/label.py` (`engrave(part, "I4", origin, normal, up)`) on a
  face that touches nothing: not a fit, sealing, sliding or food surface. It
  refuses labels that hang off the face.
- Assign the next ID when you export a print file, and log the result when the
  user reports back. Mention the ID whenever you talk about a part.

## Project tracker

`http://localhost:8765/tracker` lists, per project, what the user has provided
and what you still need (measurements, decisions, photos, pending tests), from
`<project>/tracker.json`:
`{"project": "...", "status": "one line", "items": [{"kind": "measure|photo|decide|test",
"state": "need|verify|pending|have", "what": "...", "value": "...", "how": "...", "why": "...",
"file": "photos/x.jpg"}]}`. Keep it current: add asks as they come up, flip them
to `have` (with the value or photo file) when the user answers. Save user photos
into `<project>/photos/`.

## Viewer

- Lists `.stl`/`.obj` files. By default it shows only `*_print*` files, focused
  files, and whatever is visible. A "Show all files" toggle reveals the rest.
- Files reload automatically when they change. Each visible model gets its own
  colour. "Arrange side by side" is on by default; turn it off to overlay a
  rebuild on its original (with "See-through").
- Tools: **Show overhangs** (red = faces steeper than 45 deg, not on the bed;
  red is reserved for this, so model colours never use red or pink),
  **Show print bed** (256 x 256 outline; change `BED` in `index.html`),
  **Section** (X/Y/Z cut with a slider), **Measure** (click two points).
- Settings cards are `<model stem>.settings.json` next to the model (for
  `name_print.stl` that's `name_print.settings.json`; it also covers `name_print.3mf`):
  `{"title": "...", "settings": [["Setting", "Value", "why / default"]], "note": "..."}`.
  A sidecar may also set `"color": "#8a8f99"` (fixed model colour, e.g. grey for
  context parts that aren't printed; no card is shown if it has no settings).
  **List only settings that differ from the slicer's defaults**, using the
  slicer's own setting names. Don't say "start from profile X" unless the user
  has that profile.

## Design rules that came from real failures

**Strength comes mostly from print orientation.** FDM parts are weakest
*between* layers. Every break we saw was layers peeling apart at a hook or a
corner. Orient the part so loads run *along* layers, ideally so each layer
contains the whole load path (for example, a hook profile lying in the layer
plane). Thickening helps (bending strength goes as thickness squared), but
orientation matters more.

**Supports cost a lot.** On its side, a box's far end wall becomes a ceiling:
118 g of support on a 250 g part. Report support weight and time. Offer
alternatives (another orientation, a split part, a shallower feature). Never
make a design that needs support inside a narrow slot.

**Nothing thin near food or moving parts.** If a broken fragment could end up in
food or jam a mechanism, avoid thin features entirely. Suggest a colored
filament so fragments are visible, PETG over PLA for toughness and cold, and
staying clear of where water and ice form.

**Keep fit-critical dimensions fixed.** When strengthening, grow material away
from mating surfaces: inward, upward, or outward.

**Fasteners:** `bd_warehouse.fastener` has real nuts, bolts, threads and
heat-set insert holes. Use those instead of guessing clearances.

**Slicer advice.** Wall loops is the biggest strength setting (6 loops is about
2.7 mm, so thin parts print fully solid). 100% infill makes small parts solid
but follows lines, not the outline. Brims help tall, narrow parts. Lower layer
height is cosmetic, not structural.

## build123d gotchas

- `Polygon(*pts, align=None)`: otherwise it re-centers your coordinates.
- `extrude(face, amount, dir=(0, 0, 1))`: clockwise polygons otherwise extrude
  the wrong way.
- `Plane.YZ`: local x is global Y, local y is global Z, extrudes along +X.
- Fillets fail if two fillets on one wall add up to its thickness. Keep the sum
  below the wall thickness, and fillet a simple solid before booleans if needed.
- `split(part, bisect_by=Plane(...), keep=Keep.BOTTOM)` makes hips and chamfers
  at odd angles.
- `Text(label, font_size=...)` needs a system font. Check that engravings stayed
  inside the face (compare the volume removed with the text volume).
- 3MF: `Mesher().add_shape(...)` once per object gives separate plate objects.
- A cut meant to keep "only the top" can keep stray bits elsewhere. Check the
  body count after every boolean that removes material.

## Talking to the user

- Be concise. Lead with what changed and what they need to do.
- Give file names and links, not just "it's done".
- Say plainly what's a guess (unmeasured dimensions), and how to check it.
