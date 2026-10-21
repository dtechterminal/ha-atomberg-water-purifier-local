# Verification

Tested on a physical Intellon W2 reporting firmware `74`, with Home Assistant on a separate VLAN receiving local broadcast frames. No Atomberg account was used by the integration.

## Hardware checks

Each of the seven setting entities was changed and restored through Home Assistant: purification mode, fallback mode, TDS threshold, display sleep, sleep schedule, sleep start and sleep end. Every change was checked with a separate direct UDP read from the device. Original settings, including the original schedule epoch values, were restored.

The same 14 checks passed after removing the purifier from the router's IPv4/IPv6 internet allow rule. The internet-block policy was read back before and after the tests. The integration was reloaded, and Home Assistant was restarted successfully, while that block remained active. The additional **Refresh readings** button was pressed through HA and returned a confirmed local read; all 11 entities were available after restart.

In this installation, confirmed HA service calls took **44–262 ms**, with a median of **95 ms**, during that run. These are service-call timings measured from the test client, not a measurement of how quickly the water physically changes.

Input and output TDS were compared with the Atomberg app. Output status values of 99.78 and 90.70 matched app displays of 100 and 91 mg/L. Filter-health percentages have not been decoded sufficiently to expose them.

Purification-mode testing changed between RO + UV and TasteTune 75–125. It did not physically exercise every offered mode. The remaining choices follow the documented command values. Long-term stability, cold boot of the purifier without internet, other W2 firmware, and other purifier models remain untested.

## Automated checks

40 tests cover malformed status messages, command restrictions, state confirmation, packet and VLAN decoding, real UDP exchanges, timeouts and socket cleanup. Ruff checks the integration and tests. The publishable source was scanned for secrets separately from private deployment helpers and research captures.
