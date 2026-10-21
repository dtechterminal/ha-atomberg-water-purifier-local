import asyncio
import json
import socket

import pytest

from purifier import client
from helpers import DEVICE, wire


@pytest.fixture
def network(monkeypatch):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    server.setblocking(False)
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    listener_port = probe.getsockname()[1]
    probe.close()
    monkeypatch.setattr(client, "COMMAND_PORT", server.getsockname()[1])
    monkeypatch.setattr(client, "STATE_PORT", listener_port)
    monkeypatch.setattr(client, "route_interface", lambda _: None)
    yield server, listener_port
    server.close()


async def test_real_udp_confirms_actual_setting_and_ignores_other_device(network):
    server, _ = network
    loop = asyncio.get_running_loop()
    api = client.LocalClient("127.0.0.1", DEVICE, timeout=.4)

    async def appliance():
        data, addr = await loop.sock_recvfrom(server, 8192)
        assert json.loads(data) == {"mode": 0}
        await loop.sock_sendto(server, wire(device="020000000099", changes={17: 0}), addr)
        await loop.sock_sendto(server, wire(), addr)  # Device has not applied it yet.
        await asyncio.sleep(.02)
        await loop.sock_sendto(server, wire(changes={17: 0}), addr)

    task = asyncio.create_task(appliance())
    try:
        state = await api.exchange({"mode": 0})
        assert state.settings["mode"] == 0
        assert api.device_id == DEVICE and api.receiver == "udp"
        await task
    finally:
        task.cancel()


async def test_requeries_after_error_ack_and_confirms_readback(network):
    server, _ = network
    loop = asyncio.get_running_loop()
    api = client.LocalClient("127.0.0.1", DEVICE, timeout=.8)

    async def appliance():
        _, addr = await loop.sock_recvfrom(server, 8192)
        error = json.dumps({"device_id": DEVICE, "state_string": "No command detected in the message"}).encode().hex().encode()
        await loop.sock_sendto(server, error, addr)
        query, addr = await loop.sock_recvfrom(server, 8192)
        assert json.loads(query) == {"read": 1}
        await loop.sock_sendto(server, wire(changes={30: 1}), addr)

    task = asyncio.create_task(appliance())
    try:
        result = await api.exchange({"idle_sleep": 1})
        assert result.settings["idle_sleep"] == 1
        await task
    finally:
        task.cancel()


async def test_missing_raw_permission_preserves_udp(network, monkeypatch):
    server, _ = network
    loop = asyncio.get_running_loop()
    monkeypatch.setattr(client, "route_interface", lambda _: "test0")
    def denied(_):
        raise PermissionError("no raw permission")
    monkeypatch.setattr(client, "open_receiver", denied)

    async def appliance():
        _, addr = await loop.sock_recvfrom(server, 8192)
        await loop.sock_sendto(server, wire(), addr)

    task = asyncio.create_task(appliance())
    try:
        result = await client.LocalClient("127.0.0.1", timeout=.2).read()
        assert result.settings["fallback_mode"] == 2
        await task
    finally:
        task.cancel()


async def test_timeout_does_not_claim_success_and_releases_port(network):
    _, port = network
    with pytest.raises(client.CannotConnect):
        await client.LocalClient("127.0.0.1", timeout=.02).exchange({"mode": 0})
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as check:
        check.bind(("0.0.0.0", port))
        assert check.getsockname()[1] == port


async def test_cancellation_releases_listener(network):
    _, port = network
    api = client.LocalClient("127.0.0.1", timeout=5)
    task = asyncio.create_task(api.read())
    await asyncio.sleep(.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as check:
        check.bind(("0.0.0.0", port))
        assert check.getsockname()[1] == port
