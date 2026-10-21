# Network details

The purifier receives JSON commands on UDP port **5600** and broadcasts replies to **255.255.255.255:5625**. A local read command is `{"read":1}`. No account credentials are involved.

On a shared subnet, the integration uses a normal UDP listener. On Linux it also listens for matching Ethernet frames using `AF_PACKET`, when the existing Home Assistant environment permits it. This handles broadcast replies that arrive on an interface but are not delivered to the normal UDP socket, including supported VLAN-tagged frames.

The packet receiver does not route, bridge or relay traffic between networks. It only sees frames that already reach Home Assistant. It does not log into the router, create SSH keys or change firewall rules. An ordinary routed VLAN configuration does not forward limited broadcasts. If those replies cannot reach Home Assistant, use a shared subnet or arrange an appropriate network design separately.

Permit commands from Home Assistant to the purifier on UDP 5600 and the purifier's replies to UDP 5625. The receiver checks source IP, device ID, W2 model and packet validity. It does not enable promiscuous mode. Its sockets and readers are closed after each exchange.

The protocol has no application-level authentication. Keep it on trusted local networks and do not forward these UDP ports from the internet.

## Measurement notes

The W2 status is a comma-separated record inside a hex-encoded JSON response. Settings were mapped by changing one setting, checking the resulting state and restoring the original value. Input and output TDS were compared with the Atomberg app.

| Setting or reading | Zero-based field |
| --- | --- |
| Input TDS | 6 |
| Purification mode | 17 |
| Fallback mode | 28 |
| Display sleep | 30 |
| Input TDS threshold | 32 |
| Output TDS shown by the app | 41 |
| Sleep schedule enabled | 53 |
| Sleep start UTC epoch | 54 |
| Sleep end UTC epoch | 55 |

Sleep schedule confirmation compares the time of day. The device can retain old dates in its epoch values. Unmapped fields are not assigned sensor names.
