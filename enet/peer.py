"""ENet Peer class."""

from __future__ import annotations
import ctypes
from typing import Optional, Tuple, Any, TYPE_CHECKING
from ._bindings import lib, enet_uint8
from .packet import Packet
from .address import Address

if TYPE_CHECKING:
    from .host import Host


class Peer:
    """An ENet peer with which data packets may be exchanged."""

    def __init__(self, c_peer_ptr: ctypes.c_void_p, host: Host) -> None:
        if not c_peer_ptr:
            raise ValueError("Invalid NULL peer pointer")
        self._c_peer = c_peer_ptr
        self._host = host
        self.data: Any = None  # User-assignable Python data

    @property
    def host(self) -> Host:
        """The Host managing this peer."""
        return self._host

    @property
    def id(self) -> int:
        """Outgoing peer ID assigned by host."""
        if hasattr(lib, "enet_peer_get_id"):
            return int(lib.enet_peer_get_id(self._c_peer))
        return 0

    @property
    def state(self) -> int:
        """Current ENetPeerState enum value."""
        if hasattr(lib, "enet_peer_get_state"):
            return int(lib.enet_peer_get_state(self._c_peer))
        return 0

    @property
    def address(self) -> Address:
        """Internet address of the peer."""
        ip_buf = ctypes.create_string_buffer(64)
        if hasattr(lib, "enet_peer_get_ip") and hasattr(lib, "enet_peer_get_port"):
            lib.enet_peer_get_ip(self._c_peer, ip_buf, 64)
            port = int(lib.enet_peer_get_port(self._c_peer))
            ip_str = ip_buf.value.decode("utf-8", errors="replace")
            addr = Address(ip_str if ip_str else None, port)
            return addr
        return Address(None, 0)

    @property
    def roundTripTime(self) -> int:
        """Mean round trip time in milliseconds (pyenet alias)."""
        return self.round_trip_time

    @property
    def round_trip_time(self) -> int:
        """Mean round trip time in milliseconds (RTT)."""
        if hasattr(lib, "enet_peer_get_rtt"):
            return int(lib.enet_peer_get_rtt(self._c_peer))
        return 0

    @property
    def packets_sent(self) -> int:
        """Total packets sent to this peer."""
        if hasattr(lib, "enet_peer_get_packets_sent"):
            return int(lib.enet_peer_get_packets_sent(self._c_peer))
        return 0

    @property
    def packets_lost(self) -> int:
        """Total packets lost in transmission to this peer."""
        if hasattr(lib, "enet_peer_get_packets_lost"):
            return int(lib.enet_peer_get_packets_lost(self._c_peer))
        return 0

    @property
    def packet_loss(self) -> float:
        """Packet loss ratio between 0.0 and 1.0."""
        # 65536 is ENET_PEER_PACKET_LOSS_SCALE
        return self.packets_lost / max(1, self.packets_sent)

    @property
    def bytes_sent(self) -> int:
        """Total bytes sent to this peer."""
        if hasattr(lib, "enet_peer_get_bytes_sent"):
            return int(lib.enet_peer_get_bytes_sent(self._c_peer))
        return 0

    @property
    def bytes_received(self) -> int:
        """Total bytes received from this peer."""
        if hasattr(lib, "enet_peer_get_bytes_received"):
            return int(lib.enet_peer_get_bytes_received(self._c_peer))
        return 0

    def send(self, channel_id: int, packet: Packet) -> int:
        """Queue a packet to be sent on the given channel.

        Returns 0 on success, < 0 on failure.
        """
        if not packet._c_packet:
            raise ValueError("Cannot send a destroyed packet")
        ret = lib.enet_peer_send(self._c_peer, int(channel_id), packet._c_packet)
        if ret == 0:
            # Transfer ownership of packet memory to ENet
            packet._owned = False
        return int(ret)

    def receive(self) -> Optional[Tuple[int, Packet]]:
        """Attempt to receive a queued packet from this peer.

        Returns (channel_id, Packet) if available, or None.
        """
        chan = enet_uint8(0)
        c_pkt = lib.enet_peer_receive(self._c_peer, ctypes.byref(chan))
        if not c_pkt:
            return None
        return (int(chan.value), Packet(_c_ptr=c_pkt, _owned=True))

    def ping(self) -> None:
        """Send a ping to the peer to measure RTT and keep connection alive."""
        lib.enet_peer_ping(self._c_peer)

    def ping_interval(self, interval_ms: int) -> None:
        """Set ping interval in milliseconds."""
        lib.enet_peer_ping_interval(self._c_peer, int(interval_ms))

    def timeout(self, limit: int, minimum_ms: int, maximum_ms: int) -> None:
        """Configure timeout limits for this peer."""
        lib.enet_peer_timeout(self._c_peer, int(limit), int(minimum_ms), int(maximum_ms))

    def throttle_configure(self, interval: int, acceleration: int, deceleration: int) -> None:
        """Configure packet throttle behavior."""
        lib.enet_peer_throttle_configure(self._c_peer, int(interval), int(acceleration), int(deceleration))

    def reset(self) -> None:
        """Forcefully reset peer connection without notifying remote end."""
        lib.enet_peer_reset(self._c_peer)

    def disconnect(self, data: int = 0) -> None:
        """Politely request a graceful disconnect from peer."""
        lib.enet_peer_disconnect(self._c_peer, int(data))

    def disconnect_now(self, data: int = 0) -> None:
        """Immediately disconnect from peer without awaiting acknowledgments."""
        lib.enet_peer_disconnect_now(self._c_peer, int(data))

    def disconnect_later(self, data: int = 0) -> None:
        """Disconnect after all currently queued packets are sent."""
        lib.enet_peer_disconnect_later(self._c_peer, int(data))

    def __repr__(self) -> str:
        return f"Peer(id={self.id}, address={self.address}, state={self.state}, rtt={self.round_trip_time}ms)"
