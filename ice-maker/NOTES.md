# Ice maker: replacement stripper tooth

## What it is
The ice tray's stripper comb has white teeth; the ejector fingers sweep between
them and cubes slide out over them. One tooth broke off, leaving a stub on the
outer wall, so cubes catch in the gap and jam. This part replaces that tooth:
the tooth top sits over the stub, an arm runs down the outside of the outer wall,
and a hook catches under its bottom edge. A groove in the underside rides on a
fixed grey blade. See `photos/stripper-top-view_labeled.jpg`.

## History
- `older-versions/`: the user's Tinkercad iterations from July 2025. `(4)` is the
  one that was printed and used (long-arm part).
- `original/`: a later download that turned out to be an older, groove-less copy.
- Problem with the printed `(4)`: it slides sideways along the wall into the
  ejector finger's path, and still jams.

## Constraints learned
- Measured values (slot, blade base, tooth width, water flow) are in `tracker.json`
  under Answered; test results are in `PARTS.md`.
- **The keel must stay above the water line**, or ice freezes around it.
  The old part had only 2 mm below the tooth and was fine. Water line unknown.
- Nothing thin: a fragment must never end up in the ice. Colored PETG preferred
  (fragments are visible, tougher in the cold).
- Thin spot: the crossbar above the wall notch is about 3 mm at the edges
  (unchanged from the part in use).

## Current design (`ice_maker_clip.py`, version I5, installed)
- All dimensions live in the `Tooth` dataclass; versions I1-I5 and the fit-test
  sets are named variations of it. `python ice_maker_clip.py list` shows them.
- Rebuild of `(4)` (I1) matches the original within 0.004 mm.
- Full-width keel, 3 mm deep, with the blade slot through it (2.2 mm on the thin
  part of the blade, 7 mm near the wall for the 6.37 mm blade base), so the blade
  stops the tooth sliding sideways. Notch 6.6 mm to the arm (N6.6 test), arm +0.5 mm,
  1 mm lead-in chamfers, ID engraved on the arm.
- Prints FLAT (each layer holds the whole J). I5 used a 0.6 mm slot skin; the next
  version uses slicer supports in the slot instead (`slot_skin=0`).
- Open items live in `tracker.json` (http://localhost:8765/tracker), not here.

## Lessons
- Printed STANDING (arm face down) the 3 mm keel part snapped at the thin neck
  above the wall notch while snapping it on: layer lines ran across the neck.
  Now prints FLAT (each layer holds the whole J), with a 0.6 mm sacrificial skin
  closing the slot bottom so the slot ceiling is a short bridge. Cut the skin off
  before installing. Added 1 mm lead-in chamfers on the hook tip and notch mouth.

- With the arm removed, the 3 mm keel tooth sat down but would not slide all the
  way out to the wall (stopped a few mm short). Likely the keel's narrow slot
  hitting the blade's thicker base near the hub (the old 2 mm groove rode above it).
  Wall-end fit test printed: E30 / E26 (keel ends earlier), W30 (slot 5 mm near wall).

- The 0.6 mm slot skin (I3-I5) was a pain to cut out. From I6 on: no skin, slicer
  supports in the slot instead (tree, not build-plate-only); pull with pliers, check for bits.

- Ideas only if needed later: skirts over the stub's sides (I5 doesn't slide, so not
  needed); a tapered tip like the original teeth (only matters if cubes catch or the
  fingers rub).

## Water supply (slow flow)
- Fridge dispenser: 1 cup in ~90 s (normal is 7-10 s). The previous fridge was slow
  too, so the cause is the supply, not the fridge.
- Supply is a **saddle valve** spliced into a line under the house. Cycling it fully
  closed then fully open improved flow to ~40 s per cup (2026-11-08). Still ~4x slow.
- Next, cheap: cycle the saddle valve again; replace the fridge filter (in ~9 months).
- Bucket test (disconnect at the back of the fridge into a bucket) to confirm supply vs fridge.
- **Renovation (planned soon): have the plumber add a dedicated fridge line with a
  quarter-turn shutoff (no saddle valve) and a braided stainless supply hose.**
- Ice maker had zero water when first switched back on (off ~9 months): first fills
  are small until the flow is fixed. Throw out the first few batches of ice.
