# Additional sensor mapping

The tested W2 sends a 61-field status record. Established settings and TDS readings are exposed alongside three explicitly labelled beta analytics sensors. The integration's diagnostic download retains the complete indexed record so more readings can be identified without network captures or a cloud account.

## Confirmed

- Input TDS: field 6, in mg/L. The app may cap its display at ≥1500.
- Output TDS shown in the app: field 41, in mg/L. This matched both 99.78 → 100 and 90.70 → 91 in the app.
- Firmware identifier: field 4, shown in Home Assistant's device information.
- Settings: see the [field table](network.md#measurement-notes).

## Beta analytics (0.2.0)

These readings matched the corresponding W2 app pages. They are provisional until comparison through a full refill cycle is complete. Each entity carries `mapping_status: beta`; the companion card labels its Insights page **Beta**. No filter percentages are inferred from these counters.

| Entity suffix | Local calculation | Unit |
| --- | --- | --- |
| `lifetime_water` | Field 19 / 1000 | L |
| `water_saved` | (Field 24 × 1.5 + field 25 × 3) / 1000 | L |
| `runtime` | Field 26 / 3600 | h |

Water saved uses [Atomberg's published estimate](https://developer.atomberg-iot.com/reference/get-device-analytics), comparing with a 25% recovery purifier. Runtime corresponds to the app's **Runtime** page; the API describes this as UV runtime. Lifetime water is the app's **Lifetime Consumption**, not a directly calibrated dispensing meter.

Negative, non-finite, missing and implausibly large counters become unknown, never a fabricated zero. These sensors intentionally have no statistics state class until counter/reset behavior is validated; ordinary recorder history remains available. Two measured draws did not trigger a refill, so they did not establish dynamic production-counter behavior.

## Still being investigated

- Filter-health percentages and replacement estimates.
- Refill-cycle validation and reset behavior of the beta totals.
- Instantaneous RO/UF flow, pump runtime and tank-level / dispensing flags.
- Operating state and fault indicators.

These are not verified mappings. Some values shown by the app may be calculated from several counters or stored history rather than a single local field. For example, fields 38 and 39 were around 97–99 while the app showed 91–92% filter health, so those fields must not be labelled as those filter percentages from that observation.

When comparing diagnostics, record the app reading, units, time and whether the purifier was idle or filling. Compare several states; similar numbers in one snapshot are not enough. Do not induce faults or reset filter counters to identify fields.

Diagnostics include settings and the sleep schedule, but omit the config entry, device ID, MAC and IP address. Keep app screenshots free of account information when sharing evidence.
