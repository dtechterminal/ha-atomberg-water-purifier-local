"""Synthetic W2 packet; no real identifiers or account data."""
import json

DEVICE = "020000000001"
WIRE_STATE = (
    "0,B,W2,0,74,3,800.0,25.0,90.0,0,8,0.6,0.6,0,0,2000,300000,"
    "3,0,1000000,0.6,0.6,0,0,1000000,100000,100000,100000,"
    "2,1000,0,0,250,2,0.4,0.5,0.4,0.4,97,98,2000000,99,0,90,1000000,"
    "0,0,1.6,1.6,0.2,0,1,0,1,1767304800,1767330000,0,0,0,30,END"
)


def wire(*, device=DEVICE, changes=None):
    fields = WIRE_STATE.split(",")
    for index, value in (changes or {}).items():
        fields[index] = str(value)
    return json.dumps({"device_id": device, "message_id": "synthetic",
                       "state_string": ",".join(fields)}).encode().hex().encode()
