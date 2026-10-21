"""Confirmed local UDP control, with an optional HA-local VLAN receiver."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import ipaddress
import json
import socket

from .packet import decode_frame, open_receiver, route_interface
from .protocol import COMMAND_PORT, STATE_PORT, State, decode_message, normalize_device_id, validate_command


class CannotConnect(Exception):
    """No confirmed local reply from this purifier."""


class LocalClient:
    def __init__(self, host: str, device_id: str | None = None, *, interface: str | None = None,
                 timeout: float = 2.0) -> None:
        address = ipaddress.IPv4Address(host)
        if address.is_multicast or address.is_unspecified or address == ipaddress.IPv4Address("255.255.255.255"):
            raise ValueError("Enter the purifier's individual IPv4 address")
        self.host = str(address)
        self.device_id = normalize_device_id(device_id) if device_id else None
        self.interface = interface
        self.timeout = timeout
        self.receiver = "udp"
        self._lock = asyncio.Lock()

    async def exchange(self, command: dict) -> State:
        command = validate_command(command)
        expected = {} if command == {"read": 1} else command
        async with self._lock:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[tuple[State, str]] = asyncio.Queue(maxsize=32)
            sockets = []

            def receive(payload: bytes, source: str, via: str) -> None:
                if source != self.host:
                    return
                decoded = decode_message(payload)
                if decoded is None:
                    return
                device_id, state = decoded
                if state is None or (self.device_id and device_id != self.device_id):
                    return
                if queue.full():
                    queue.get_nowait()
                queue.put_nowait((state, via))

            def read_udp(sock: socket.socket) -> None:
                for _ in range(64):
                    try:
                        data, addr = sock.recvfrom(8193)
                    except (BlockingIOError, OSError):
                        return
                    receive(data, addr[0], "udp")

            def read_packet(sock: socket.socket) -> None:
                for _ in range(64):
                    try:
                        data, ancillary, _, _ = sock.recvmsg(65535, 128)
                    except (BlockingIOError, OSError):
                        return
                    decoded = decode_frame(data, ancillary, self.host)
                    if decoded:
                        receive(decoded[1], decoded[0], "local_packet")

            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sockets.append(udp)
            try:
                udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                udp.bind(("0.0.0.0", STATE_PORT))
                udp.setblocking(False)
                loop.add_reader(udp.fileno(), read_udp, udp)
                interface = self.interface or await asyncio.to_thread(route_interface, self.host)
                if interface:
                    try:
                        raw = open_receiver(interface)
                    except OSError:
                        pass  # Standard UDP still works on a normal shared subnet.
                    else:
                        sockets.append(raw)
                        loop.add_reader(raw.fileno(), read_packet, raw)
                payload = json.dumps(command, separators=(",", ":")).encode()
                for _attempt in range(3):
                    # Remove replies queued before this send. Only confirmed values succeed.
                    while not queue.empty():
                        queue.get_nowait()
                    await loop.sock_sendto(udp, payload, (self.host, COMMAND_PORT))
                    end = loop.time() + self.timeout
                    next_read = loop.time() + .3
                    while loop.time() < end:
                        wait = min(end, next_read) - loop.time()
                        try:
                            state, via = await asyncio.wait_for(queue.get(), max(.001, wait))
                        except TimeoutError:
                            if loop.time() >= next_read and expected:
                                await loop.sock_sendto(udp, b'{"read":1}', (self.host, COMMAND_PORT))
                            next_read = loop.time() + .5
                            continue
                        if state.matches(expected):
                            self.device_id = state.device_id
                            self.receiver = via
                            return state
                raise CannotConnect("No confirmed reply. Check the IP address and local network access.")
            except OSError as err:
                raise CannotConnect("Unable to open the local connection") from err
            finally:
                for sock in sockets:
                    with suppress(Exception):
                        loop.remove_reader(sock.fileno())
                    sock.close()

    async def read(self) -> State:
        return await self.exchange({"read": 1})


async def discover(seconds: float = 4.0) -> dict[str, str]:
    """Listen for W2 beacons locally; never contact a cloud or scan unrelated hosts."""
    loop = asyncio.get_running_loop()
    found: dict[str, str] = {}
    sockets = []

    def record(payload: bytes, host: str) -> None:
        decoded = decode_message(payload)
        if decoded:
            found[decoded[0]] = host

    def on_udp(sock: socket.socket) -> None:
        for _ in range(64):
            try:
                data, addr = sock.recvfrom(8193)
            except (BlockingIOError, OSError):
                return
            record(data, addr[0])

    def on_packet(sock: socket.socket) -> None:
        for _ in range(64):
            try:
                data, anc, _, _ = sock.recvmsg(65535, 128)
            except (BlockingIOError, OSError):
                return
            decoded = decode_frame(data, anc)
            if decoded:
                record(decoded[1], decoded[0])

    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sockets.append(udp)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp.bind(("0.0.0.0", STATE_PORT))
        udp.setblocking(False)
        loop.add_reader(udp.fileno(), on_udp, udp)
        for _, interface in await asyncio.to_thread(socket.if_nameindex):
            if interface == "lo":
                continue
            try:
                raw = open_receiver(interface)
            except OSError:
                continue
            sockets.append(raw)
            loop.add_reader(raw.fileno(), on_packet, raw)
        await asyncio.sleep(seconds)
        return found
    except OSError:
        return found
    finally:
        for sock in sockets:
            with suppress(Exception):
                loop.remove_reader(sock.fileno())
            sock.close()
