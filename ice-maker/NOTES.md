# Ice maker: replacement stripper tooth

## What it is
The ice tray's stripper comb has white teeth; the ejector fingers sweep between
them and cubes slide out over them. One tooth broke off, leaving a stub on the
outer wall, so cubes catch in the gap and jam. This part replaces that tooth:
the tooth top sits over the stub, an arm runs down the outside of the outer wall,
and a hook catches under its bottom edge. A groove in the underside rides on a
fixed grey blade. See `photos/stripper-top-view_labeled.png`.

## History
- `older-versions/`: the user's Tinkercad iterations from July 2025. `(4)` is the
  one that was printed and used (long-arm part).
- `original/`: a later download that turned out to be an older, groove-less copy.
- Problem with the printed `(4)`: it slides sideways along the wall into the
  ejector finger's path, and still jams.

## Constraints learned
- Blade slot width **2.2 mm** fits the grey blade well (confirmed on the printed part).
- Tooth width 14 mm; the original teeth are about 14.5 mm at the base.
- **The keel must stay above the water line**, or ice freezes around it.
  The old part had only 2 mm below the tooth and was fine. Water line unknown.
- Nothing thin: a fragment must never end up in the ice. Colored PETG preferred
  (fragments are visible, tougher in the cold).
- Thin spot: the crossbar above the wall notch is about 3 mm at the edges
  (unchanged from the part in use).

## Current design (`ice_maker_clip.py`)
- Rebuild of `(4)` matches the original within 0.003 mm.
- Added a full-width keel (`KEEL_DEPTH`, default 5 mm) with the blade slot
  running through it, so the blade stops sideways sliding.
- Prints standing on the arm's outer face: no supports (flat would put the half
  above the slot over air).

## Open
- Printing `out/ice-tooth_keel3_print` (3 mm keel, `--keel 3`) as the conservative
  overnight part while the ice maker is first switched back on (2026-11-08).
- Ice maker not filling after being switched on; dispenser has always been weak:
  suspect low water pressure (supply valve, kinked line, inlet valve screen).
- Fit tests K3 / K5 / K8 (`out/ice-tooth_fit-test-set_print.3mf`): dip each in a
  filled tray; pick the deepest that comes out dry with a few mm to spare.
