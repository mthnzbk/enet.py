"""ENet Host class."""

from __future__ import annotations
import ctypes
from typing import Optional, Iterator, Dict, List
from ._bindings import C_ENetEvent, C_ENetAddress, lib
from .address import Address
from .packet import Packet
from .peer import Peer
from .event import Event
from .constants import EVENT_TYPE_NONE, EVENT_TYPE_RECEIVE, HOST_DEFAULT_MTU


class Host:
    """An ENet host for communicating with one or more peers."""

    def __init__(
        self,
        address: Optional[Address] = None,
        peer_count: int = 32,
        channel_limit: int = 2,
        incoming_bandwidth: int = 0,
        outgoing_bandwidth: int = 0,
    ) -> None:
        """Create a new ENet Host.

        Args:
            address: Local Address to bind server to, or None for client.
            peer_count: Maximum number of peers (clients) to allocate.
            channel_limit: Maximum number of channels per peer (0 = max 255).
            incoming_bandwidth: Downstream bandwidth limit in bytes/sec (0 = unlimited).
            outgoing_bandwidth: Upstream bandwidth limit in bytes/sec (0 = unlimited).
        """
        self._address = address
        self._peer_cache: Dict[int, Peer] = {}
        self._destroyed = False

        if address is not None:
            c_addr = address.to_c_address()
            self._c_host = lib.enet_host_create(
                ctypes.byref(c_addr),
                int(peer_count),
                int(channel_limit),
                int(incoming_bandwidth),
                int(outgoing_bandwidth),
            )
        else:
            self._c_host = lib.enet_host_create(
                None,
                int(peer_count),
                int(channel_limit),
                int(incoming_bandwidth),
                int(outgoing_bandwidth),
            )

        if not self._c_host:
            raise RuntimeError(
                f"Failed to create ENet host (address={address}, peer_count={peer_count})"
            )

    @property
    def address(self) -> Optional[Address]:
        """Local Address this host is bound to, or None."""
        return self._address

    @property
    def peers_count(self) -> int:
        """Number of peers allocated for this host."""
        if self._c_host and hasattr(lib, "enet_host_get_peers_count"):
            return int(lib.enet_host_get_peers_count(self._c_host))
        return 0

    @property
    def packets_sent(self) -> int:
        """Total packets sent by this host."""
        if self._c_host and hasattr(lib, "enet_host_get_packets_sent"):
            return int(lib.enet_host_get_packets_sent(self._c_host))
        return 0

    @property
    def packets_received(self) -> int:
        """Total packets received by this host."""
        if self._c_host and hasattr(lib, "enet_host_get_packets_received"):
            return int(lib.enet_host_get_packets_received(self._c_host))
        return 0

    @property
    def bytes_sent(self) -> int:
        """Total bytes sent by this host."""
        if self._c_host and hasattr(lib, "enet_host_get_bytes_sent"):
            return int(lib.enet_host_get_bytes_sent(self._c_host))
        return 0

    @property
    def bytes_received(self) -> int:
        """Total bytes received by this host."""
        if self._c_host and hasattr(lib, "enet_host_get_bytes_received"):
            return int(lib.enet_host_get_bytes_received(self._c_host))
        return 0

    @property
    def mtu(self) -> int:
        """Maximum Transmission Unit configured for host."""
        if self._c_host and hasattr(lib, "enet_host_get_mtu"):
            return int(lib.enet_host_get_mtu(self._c_host))
        return HOST_DEFAULT_MTU

    @property
    def peers(self) -> List[Peer]:
        """List of active tracked Peer objects."""
        return list(self._peer_cache.values())

    def _get_or_create_peer(self, c_peer_ptr: Optional[ctypes.c_void_p]) -> Optional[Peer]:
        """Retrieve cached Peer instance or create a new wrapper."""
        if not c_peer_ptr:
            return None
        ptr_val = int(c_peer_ptr) if not isinstance(c_peer_ptr, int) else c_peer_ptr
        if ptr_val not in self._peer_cache:
            self._peer_cache[ptr_val] = Peer(c_peer_ptr, self)
        return self._peer_cache[ptr_val]

    def connect(self, address: Address, channel_count: int = 2, data: int = 0) -> Peer:
        """Initiate a connection to a foreign host.

        Args:
            address: Destination Address of the host to connect to.
            channel_count: Number of channels to allocate (minimum 1).
            data: User data to supply to the destination host on connect.

        Returns:
            Peer representing the connection.
        """
        if not self._c_host:
            raise RuntimeError("Host has been destroyed")

        c_addr = address.to_c_address()
        c_peer = lib.enet_host_connect(
            self._c_host,
            ctypes.byref(c_addr),
            int(channel_count),
            int(data),
        )
        if not c_peer:
            raise RuntimeError(f"Failed to initiate connection to {address}")

        peer = self._get_or_create_peer(c_peer)
        assert peer is not None
        return peer

    def service(self, timeout_ms: int = 0) -> Event:
        """Wait for events on the host.

        Args:
            timeout_ms: Milliseconds to wait (0 = non-blocking poll).

        Returns:
            Event object. Check event.type != EVENT_TYPE_NONE.
        """
        if not self._c_host:
            return Event(EVENT_TYPE_NONE)

        c_event = C_ENetEvent()
        ret = lib.enet_host_service(self._c_host, ctypes.byref(c_event), int(timeout_ms))

        if ret > 0:
            peer = self._get_or_create_peer(c_event.peer)
            packet = None
            if c_event.type == EVENT_TYPE_RECEIVE and c_event.packet:
                # Wrap received C packet; Python will own freeing it
                packet = Packet(_c_ptr=c_event.packet, _owned=True)

            return Event(
                event_type=c_event.type,
                peer=peer,
                channel_id=c_event.channelID,
                data=c_event.data,
                packet=packet,
            )
        return Event(EVENT_TYPE_NONE)

    def check_events(self) -> Event:
        """Check for any pending queued events without waiting."""
        if not self._c_host:
            return Event(EVENT_TYPE_NONE)

        c_event = C_ENetEvent()
        ret = lib.enet_host_check_events(self._c_host, ctypes.byref(c_event))
        if ret > 0:
            peer = self._get_or_create_peer(c_event.peer)
            packet = None
            if c_event.type == EVENT_TYPE_RECEIVE and c_event.packet:
                packet = Packet(_c_ptr=c_event.packet, _owned=True)

            return Event(
                event_type=c_event.type,
                peer=peer,
                channel_id=c_event.channelID,
                data=c_event.data,
                packet=packet,
            )
        return Event(EVENT_TYPE_NONE)

    def poll(self, timeout_ms: int = 0) -> Iterator[Event]:
        """Generator yielding all available events in this servicing interval."""
        first = self.service(timeout_ms)
        if first.type != EVENT_TYPE_NONE:
            yield first
            while True:
                nxt = self.check_events()
                if nxt.type == EVENT_TYPE_NONE:
                    break
                yield nxt

    def flush(self) -> None:
        """Send any queued outgoing commands without waiting for service."""
        if self._c_host:
            lib.enet_host_flush(self._c_host)

    def broadcast(self, channel_id: int, packet: Packet) -> None:
        """Broadcast a packet to all connected peers.

        The packet will be sent over the specified channel.
        """
        if not self._c_host:
            raise RuntimeError("Host has been destroyed")
        if not packet._c_packet:
            raise ValueError("Cannot broadcast destroyed packet")

        lib.enet_host_broadcast(self._c_host, int(channel_id), packet._c_packet)
        # ENet takes ownership of the packet reference
        packet._owned = False

    def channel_limit(self, channel_limit: int) -> None:
        """Adjust the maximum number of channels allowed for peers."""
        if self._c_host:
            lib.enet_host_channel_limit(self._c_host, int(channel_limit))

    def bandwidth_limit(self, incoming_bandwidth: int, outgoing_bandwidth: int) -> None:
        """Adjust bandwidth limits in bytes/second."""
        if self._c_host:
            lib.enet_host_bandwidth_limit(
                self._c_host, int(incoming_bandwidth), int(outgoing_bandwidth)
            )

    def bandwidth_throttle(self) -> None:
        """Throttle bandwidth based on limits."""
        if self._c_host:
            lib.enet_host_bandwidth_throttle(self._c_host)

    def destroy(self) -> None:
        """Destroy host and close all sockets and peer connections."""
        if self._c_host and not self._destroyed:
            lib.enet_host_destroy(self._c_host)
            self._c_host = None
            self._destroyed = True
            self._peer_cache.clear()

    def __enter__(self) -> Host:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.destroy()

    def __del__(self) -> None:
        self.destroy()

    def __repr__(self) -> str:
        addr = self.address or "client"
        return f"Host(address={addr}, peers={self.peers_count})"
