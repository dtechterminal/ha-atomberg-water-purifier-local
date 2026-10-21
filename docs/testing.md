# Verification

Tested on a physical Intellon W2 reporting firmware `74`, with Home Assistant on a separate VLAN receiving local broadcast frames. No Atomberg account was used by the integration.

## Hardware checks

Each of the seven setting entities was changed and restored through Home Assistant: purification mode, fallback mode, TDS threshold, display sleep, sleep schedule, sleep start and sleep end. Every change was checked with a separate direct UDP read from the device. Original settings, including the original schedule epoch values, were restored.

The same 14 checks passed after removing the purifier from the router's IPv4/IPv6 internet allow rule. The internet-block policy was read back before and after the tests. The integration was reloaded, and Home Assistant was restarted successfully, while that block remained active. The additional **Refresh readings** button was pressed through HA and returned a confirmed local read; all 11 entities were available after restart.

In this installation, confirmed HA service calls took **44–262 ms**, with a median of **95 ms**, during that run. These are service-call timings measured from the test client, not a measurement of how quickly the water physically changes.

Input and output TDS were compared with the Atomberg app. Output status values of 99.78 and 90.70 matched app displays of 100 and 91 mg/L. All eight original-component capacity estimates were recovered from the compiled app and matched the recorded health screen. Replacement history and flow-based adjustments are outside the current estimates.

Purification-mode testing changed between RO + UV and TasteTune 75–125. It did not physically exercise every offered mode. The remaining choices follow the documented command values. Long-term stability, cold boot of the purifier without internet, other W2 firmware, and other purifier models remain untested.

## Automated checks

40 tests cover malformed status messages, command restrictions, state confirmation, packet and VLAN decoding, real UDP exchanges, timeouts and socket cleanup. Ruff checks the integration and tests. The publishable source was scanned for secrets separately from private deployment helpers and research captures.

## Filter life and automatic polling (0.3.0)

All eight remaining-capacity estimates matched the app with original components:
pre-filter / sediment / pre-carbon 92%, RO 91%, UF / UV 100%, pump 99%, alkaliser 90%.
The user confirmed that no component had been replaced. The installed integration
exposed all eight sensors and kept purification mode and the other controls available.

A passive, 38-second capture on Home Assistant observed four automatic local read
requests, with intervals of 9.993, 9.998 and 10.002 seconds. No Refresh button was
pressed during this check. The companion card's last-read timestamp also advanced
automatically while displaying the live filter readings. This is a short functional
check, not a long-term reliability measurement.

Validation: 58 Python tests and Ruff passed. The companion card passed 14 unit tests
and five browser tests, including Filters at 320, 390, 768 and 1440 px widths.
