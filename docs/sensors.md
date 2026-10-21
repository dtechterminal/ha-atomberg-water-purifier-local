# Additional sensor mapping

The tested W2 sends a 61-field status record. Only fields with a confirmed meaning are currently exposed as named entities. The integration's diagnostic download retains the complete indexed record so more readings can be identified without network captures or a cloud account.

## Confirmed

- Input TDS: field 6, in mg/L. The app may cap its display at ≥1500.
- Output TDS shown in the app: field 41, in mg/L. This matched both 99.78 → 100 and 90.70 → 91 in the app.
- Firmware identifier: field 4, shown in Home Assistant's device information.
- Settings: see the [field table](network.md#measurement-notes).

## Still being investigated

- Filter-health percentages and replacement estimates.
- Water-use totals and water saved.
- RO/UF flow measurements, pump runtime and UV runtime.
- Operating state and fault indicators.

These are not verified mappings. Some values shown by the app may be calculated from several counters or stored history rather than a single local field. For example, fields 38 and 39 were around 97–99 while the app showed 91–92% filter health, so those fields must not be labelled as those filter percentages from that observation.

When comparing diagnostics, record the app reading, units, time and whether the purifier was idle or filling. Compare several states; similar numbers in one snapshot are not enough. Do not induce faults or reset filter counters to identify fields.

Diagnostics include settings and the sleep schedule, but omit the config entry, device ID, MAC and IP address. Keep app screenshots free of account information when sharing evidence.
