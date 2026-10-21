# Atomberg Water Purifier Local

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/atomberg_purifier_local/brand/dark_logo@2x.png">
  <img src="custom_components/atomberg_purifier_local/brand/logo@2x.png" alt="Atomberg" width="200">
</picture>

Control an Atomberg Intellon water purifier from Home Assistant over your home network. No Atomberg account, API key, subscription or cloud connection is used by this integration.

The purifier must already be connected to your Wi-Fi. First-time Wi-Fi setup is still done with the Atomberg app.

## What you get

- Purification mode: RO + UV, Adaptive, three TasteTune ranges and Vacay.
- Fallback purification mode and input TDS threshold.
- Display sleep and a daily sleep schedule, including start and end times.
- Input and output TDS readings, in mg/L, updated every 30 seconds.
- A **Refresh readings** button to request the device's latest readings immediately.
- A connection sensor showing that Home Assistant is using your local network.

Changes are confirmed by reading the setting back from the purifier. The integration does not assume a command succeeded just because it was sent.

**Tested hardware:** Intellon, local model identifier W2, reported firmware `74`. Other purifier models and firmware versions have not been verified. Atomberg fans use a different integration.

Filter-health percentages, fault explanations and water-use totals are not exposed yet. Their local data has not been mapped reliably. The app's **Skip Flow Check** fault workaround is also not mapped or exposed. The app's cloud history and firmware-update features are outside this integration.

## 1. Install with HACS

You need Home Assistant with [HACS](https://www.hacs.dev/) installed.

1. Open **HACS** in Home Assistant.
2. Open **⋮ → Custom repositories**.
3. Paste this address:

   ```text
   https://github.com/dtechterminal/ha-atomberg-water-purifier-local
   ```

4. Choose **Integration**, then click **Add**.
5. Find **Atomberg Water Purifier Local** in HACS and download it.
6. **Restart Home Assistant.**

You only add the repository once. Future releases can be installed through HACS.

## 2. Add your purifier

1. Open **Settings → Devices & services → Add integration**.
2. Search for **Atomberg Water Purifier Local**.
3. Choose the purifier it finds. If it finds nothing, enter the purifier's IP address from your router's device list.
4. Setup checks the local connection before it finishes. Open the new device to see its controls and readings.

You do not need to edit YAML or enter an Atomberg password.

Home Assistant 2026.3 or newer displays the bundled Atomberg logo locally. See [brand image credits](docs/branding.md).

This is a **HACS custom repository**. It is not in HACS's default catalog.

**Installing without HACS?** Download `atomberg_purifier_local.zip` from the [latest release](https://github.com/dtechterminal/ha-atomberg-water-purifier-local/releases/latest). Extract its contents into `config/custom_components/atomberg_purifier_local`, restart Home Assistant, then follow step 2 above.

## 3. Keep it working without the internet

1. In Home Assistant, turn **Display sleep** on, check the purifier's display, then restore the setting.
2. Open your router's app or website. Block **internet/WAN access for the purifier only**. Keep its Wi-Fi and local access to Home Assistant enabled.
3. Repeat the display test. Make sure the TDS readings keep updating too.
4. Reserve the purifier's IP address in your router so it does not change later.

Some routers call their block option “Pause device” and block the whole network connection. Use an internet-only rule instead. If you use IPv6, the rule should cover that too.

The Atomberg app's cloud features and online updates may stop working while internet access is blocked. Home Assistant controls use the local connection.

## Useful tips

- **Sleep times** use the time zone configured in Home Assistant. Enable **Sleep schedule** before changing its times.
- **TDS readings** show the device's measured value. The Atomberg app may round it or show a limit such as “≥1500”.
- **Changes from the app or purifier** appear in Home Assistant on the next refresh, normally within 30 seconds. Changes made in Home Assistant are read back immediately.
- **IP address changed?** Open the integration's menu and choose **Reconfigure**. Your existing entities are kept.

## If setup cannot find the purifier

Check that the purifier is powered on and connected to Wi-Fi. Try its IP address manually. For the simplest setup, put Home Assistant and the purifier on the same local network.

If you have separate IoT VLANs, see [network details](docs/network.md). Allowing ordinary traffic between VLANs is not sufficient by itself: the purifier sends its replies as broadcasts. The integration can receive these directly on supported Linux hosts when those frames already reach Home Assistant's interface.

## Development

The protocol implementation uses Python's standard library. Tests use synthetic device IDs and packet fixtures; no accounts or recordings are required.

```sh
uv run --with pytest --with pytest-asyncio --with scapy pytest -q
uv run --with ruff ruff check custom_components tests
```

Atomberg's [official command reference](https://developer.atomberg-iot.com/reference/send-command) documents the setting names. Local W2 operation and state-field mappings were verified on physical hardware; this is an independent community integration.

For help, [open an issue](https://github.com/dtechterminal/ha-atomberg-water-purifier-local/issues) with your purifier model, firmware and the error shown. Keep passwords, tokens and private network captures out of issues.

**Want to help add more sensors?** Open **Settings → Devices & services → Atomberg Water Purifier Local → ⋮ → Download diagnostics**. It includes the purifier's local readings, including fields whose meanings are still unknown, without including your IP address or device ID. Compare readings with the app at the same time and note the units. Review the file before sharing: it contains your purifier settings and sleep schedule. See [sensor mapping notes](docs/sensors.md).
