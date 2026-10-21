import struct

import pytest
from scapy.all import Dot1Q, Ether, IP, UDP, Raw

from purifier.packet import decode_frame, SOL_PACKET, PACKET_AUXDATA, TP_STATUS_VLAN_VALID

HOST = "192.0.2.10"


def frame(*, vlan=False, source=HOST, port=5625, fragment=False):
    ethernet = Ether()
    if vlan:
        ethernet /= Dot1Q(vlan=7)
    return bytes(ethernet / IP(src=source, dst="255.255.255.255", flags="MF" if fragment else 0)
                 / UDP(sport=45001, dport=port) / Raw(b"020000000001_W2"))


def test_independently_encoded_frames_and_vlan_offload():
    assert decode_frame(frame(), [], HOST) == (HOST, b"020000000001_W2")
    assert decode_frame(frame(vlan=True), [], HOST, vlan_id=7) == (HOST, b"020000000001_W2")
    aux = [(SOL_PACKET, PACKET_AUXDATA, struct.pack("=IIIHHHH", TP_STATUS_VLAN_VALID, 0, 0, 0, 0, 7, 0x8100))]
    assert decode_frame(frame(), aux, HOST, vlan_id=7) == (HOST, b"020000000001_W2")
    assert decode_frame(frame(vlan=True), [], HOST, vlan_id=8) is None


@pytest.mark.parametrize("data", [b"", frame()[:35], frame()[:-1], frame(port=5002),
                                   frame(source="192.0.2.11"), frame(fragment=True)])
def test_ignores_unrelated_and_broken_packets(data):
    assert decode_frame(data, [], HOST) is None


def test_checks_actual_ip_and_udp_checksums():
    corrupt = bytearray(frame())
    corrupt[-1] ^= 1
    assert decode_frame(bytes(corrupt), [], HOST) is None
    corrupt = bytearray(frame())
    corrupt[24] ^= 1
    assert decode_frame(bytes(corrupt), [], HOST) is None
