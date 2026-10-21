# Filter life

Version 0.3.0 adds eight **estimated remaining-capacity** readings. They use
the capacity calculations recovered from Atomberg Home 7.7.2 and the counters
read directly from the W2. No account or internet connection is needed.

They assume the original filters, lamp and pump are still installed. If a
component has been replaced, its reading needs a replacement baseline. This
release does not import the app's replacement records, so that component's
percentage will not be correct after a replacement.

The app also adjusts some percentages using flow performance and its previous
health reading. Those adjustments are not included here. These are capacity
estimates, not a water-safety measurement or an exact copy of every app health
decision. The companion card labels them **Estimated remaining life**.

## Decoded calculation

Fields below are zero-based positions in the local comma-separated W2 status.
Volumes are transmitted in millilitres and converted to litres. Runtime
counters are in seconds. Remaining percentage is `ceil(100 × (1 − used/capacity))`,
bounded to 0–100 for display. Missing or invalid inputs give an unknown reading.

| Component | Used counter | Capacity |
| --- | --- | --- |
| Pre-filter | Scaled total, field 40 / 1000 | 25,000 L |
| Inline sediment | Scaled total, field 40 / 1000 | 25,000 L |
| Pre-carbon | Scaled total, field 40 / 1000 | 25,000 L |
| RO membrane | Scaled RO, field 44 / 1000 | 12,500 L |
| UF membrane | UF total, field 25 / 1000 | 12,000 L |
| UV lamp | UV runtime, field 26 | 21,600,000 seconds (6,000 h) |
| Pump | Pump runtime, field 27 | 7,200,000 seconds (2,000 h) |
| Alkaliser + taste enhancer | Total water, field 19 / 1000 | 12,500 L |

When scaled total is **100 L or less**, the app uses `(2 × field 24 + field 25) / 1000`
for the first three filters and `field 24 / 1000` for RO. An invalid scaled
counter does not trigger this fallback.

## Evidence and limits

The capacity constants and rounding were traced through both
`WaterPurifier._calculateFilterHealths` and
`WpStateProvider._calculateFilterHealths` / `_percentRemaining` in the compiled
7.7.2 ARM64 app. `updateStateFromStateString` confirms the local field positions
and millilitre conversion. The app's filter parser reads replacement baselines
from the separate `filterreplaceliters` record; those baselines are absent from
the local status used here.

All eight capacity results matched the simultaneously recorded app health
screen on the tested W2. The actual counters also changed during a refill.
The check covers the original-component case, not replacement or end-of-life
behavior. Tests use synthetic counters, include the early-life fallback,
separate pump/UV lifetimes, rounding, exhaustion, and invalid input handling.

For future work, the app gates flow-based blending below 85% capacity for the
first three filters and below 50% for RO/UF, then uses historical health for
smoothing. Reconstructing that history from the local status alone is not
possible. No app binaries, decompiled app code or private recordings are
distributed with this integration.
