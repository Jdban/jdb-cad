# Ice maker: parts log

Every printed part has an ID. From I4 on the ID is engraved on the part; earlier
ones were assigned after the fact. Prefix: **I** = full tooth; fit-test plates are
`test-*`, and each piece carries its engraved label. Printed files in `out/` are
frozen (see `out/<ID>.params.json`); never rebuild over them, make a new ID.

| ID | File | Printed | What it is | Result |
|---|---|---|---|---|
| I1 | `out/I1` (rebuild of `older-versions/Ice Maker Fix JDB (4).stl`) | Jul 2025 | Original Tinkercad tooth, 2 mm groove, no keel | Fits; slides sideways into the ejector finger's path and jams |
| I2 | `out/I2_print` | 2026-11-08, colored PETG, standing | 3 mm keel | Snapped at the neck above the wall notch while snapping on (layer lines across the neck) |
| I3 | `out/I3_print` | 2026-11-09, colored PETG, flat | 3 mm keel, slot skin, lead-ins | Too tight to snap on; without the arm it stops a few mm short of the wall |
| test-K: K3 / K5 / K8 | `out/test-K_print` | 2026-11-08, draft | Tops only, keel depth 3 / 5 / 8 mm | All dry after the first (small) fill; retest after a normal fill |
| test-EW: E30 / E26 / W30 | `out/test-EW_print` | 2026-11-09, draft | Tops only, 3 mm keel: keel ends earlier (E30, E26) or slot 5 mm near the wall (W30) | W30 best; E30 tilted; E26 worst. W30's 5 mm still too narrow |
| test-N: N5.6 / N6.1 / N6.6 / N7.1 | `out/test-N_print` | 2026-11-09, draft | I4 top + 12 mm arm stub, notch length to the arm | **N6.6 fits** |
| I5 | `out/I5_print` | 2026-11-09, colored PETG, flat | Slot 7 mm near the wall (blade base 6.37 mm), notch 6.6, arm +0.5, slot skin | **Installed, fits, doesn't slide.** Watching over ice cycles |

Designed but not printed (definitions only, no files): I4 (superseded by I5 before
printing); earlier experiments (5 mm keel, arm +1.5 mm, W6/W7/W8 slot widths: the
blade base was measured instead).
