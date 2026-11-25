"""Python bindings for zpl-c/enet reliable UDP networking library.

Features:
- Single-header C99 ENet (zpl-c/enet) with integrated IPv6 support
- Reliable, ordered, and fragmented UDP packet delivery
- High-level, pythonic Host, Peer, Packet, Address, and Event classes
- Zero external build dependencies for end users (bundled native binaries)
- Drop-in compatibility with classic pyenet API patterns
"""

from __future__ import annotations
import atexit
from typing import Optional

from ._bindings import lib
from .constants import (
    ENET_VERSION_MAJOR,
    ENET_VERSION_MINOR,
    ENET_VERSION_PATCH,
    ENET_VERSION,
    # Packet flags
    PACKET_FLAG_RELIABLE,
    PACKET_FLAG_UNSEQUENCED,
    PACKET_FLAG_NO_ALLOCATE,
    PACKET_FLAG_UNRELIABLE_FRAGMENT,
    PACKET_FLAG_UNTHROTTLED,
    PACKET_FLAG_SENT,
    # pyenet aliases
    ENET_PACKET_FLAG_RELIABLE,
    ENET_PACKET_FLAG_UNSEQUENCED,
    ENET_PACKET_FLAG_NO_ALLOCATE,
    ENET_PACKET_FLAG_UNRELIABLE_FRAGMENT,
    ENET_PACKET_FLAG_UNTHROTTLED,
    ENET_PACKET_FLAG_SENT,
    # Event types
    EVENT_TYPE_NONE,
    EVENT_TYPE_CONNECT,
    EVENT_TYPE_DISCONNECT,
    EVENT_TYPE_RECEIVE,
    EVENT_TYPE_DISCONNECT_TIMEOUT,
    # pyenet aliases
    ENET_EVENT_TYPE_NONE,
    ENET_EVENT_TYPE_CONNECT,
    ENET_EVENT_TYPE_DISCONNECT,
    ENET_EVENT_TYPE_RECEIVE,
    ENET_EVENT_TYPE_DISCONNECT_TIMEOUT,
    # Peer states
    PEER_STATE_DISCONNECTED,
    PEER_STATE_CONNECTING,
    PEER_STATE_ACKNOWLEDGING_CONNECT,
    PEER_STATE_CONNECTION_PENDING,
    PEER_STATE_CONNECTION_SUCCEEDED,
    PEER_STATE_CONNECTED,
    PEER_STATE_DISCONNECT_LATER,
    PEER_STATE_DISCONNECTING,
    PEER_STATE_ACKNOWLEDGING_DISCONNECT,
    PEER_STATE_ZOMBIE,
    # pyenet aliases
    ENET_PEER_STATE_DISCONNECTED,
    ENET_PEER_STATE_CONNECTING,
    ENET_PEER_STATE_ACKNOWLEDGING_CONNECT,
    ENET_PEER_STATE_CONNECTION_PENDING,
    ENET_PEER_STATE_CONNECTION_SUCCEEDED,
    ENET_PEER_STATE_CONNECTED,
    ENET_PEER_STATE_DISCONNECT_LATER,
    ENET_PEER_STATE_DISCONNECTING,
    ENET_PEER_STATE_ACKNOWLEDGING_DISCONNECT,
    ENET_PEER_STATE_ZOMBIE,
    # Other constants
    HOST_ANY,
    PORT_ANY,
    PEER_PACKET_LOSS_SCALE,
)
from .address import Address
from .packet import Packet
from .peer import Peer
from .event import Event
from .host import Host

__version__ = f"{ENET_VERSION_MAJOR}.{ENET_VERSION_MINOR}.{ENET_VERSION_PATCH}"
__all__ = [
    "Address",
    "Packet",
    "Peer",
    "Host",
    "Event",
    "initialize",
    "deinitialize",
    "time_get",
    "linked_version",
    # Constants
    "PACKET_FLAG_RELIABLE",
    "PACKET_FLAG_UNSEQUENCED",
    "PACKET_FLAG_NO_ALLOCATE",
    "PACKET_FLAG_UNRELIABLE_FRAGMENT",
    "PACKET_FLAG_UNTHROTTLED",
    "PACKET_FLAG_SENT",
    "ENET_PACKET_FLAG_RELIABLE",
    "ENET_PACKET_FLAG_UNSEQUENCED",
    "ENET_PACKET_FLAG_NO_ALLOCATE",
    "ENET_PACKET_FLAG_UNRELIABLE_FRAGMENT",
    "ENET_PACKET_FLAG_UNTHROTTLED",
    "ENET_PACKET_FLAG_SENT",
    "EVENT_TYPE_NONE",
    "EVENT_TYPE_CONNECT",
    "EVENT_TYPE_DISCONNECT",
    "EVENT_TYPE_RECEIVE",
    "EVENT_TYPE_DISCONNECT_TIMEOUT",
    "ENET_EVENT_TYPE_NONE",
    "ENET_EVENT_TYPE_CONNECT",
    "ENET_EVENT_TYPE_DISCONNECT",
    "ENET_EVENT_TYPE_RECEIVE",
    "ENET_EVENT_TYPE_DISCONNECT_TIMEOUT",
    "PEER_STATE_DISCONNECTED",
    "PEER_STATE_CONNECTING",
    "PEER_STATE_ACKNOWLEDGING_CONNECT",
    "PEER_STATE_CONNECTION_PENDING",
    "PEER_STATE_CONNECTION_SUCCEEDED",
    "PEER_STATE_CONNECTED",
    "PEER_STATE_DISCONNECT_LATER",
    "PEER_STATE_DISCONNECTING",
    "PEER_STATE_ACKNOWLEDGING_DISCONNECT",
    "PEER_STATE_ZOMBIE",
    "ENET_PEER_STATE_DISCONNECTED",
    "ENET_PEER_STATE_CONNECTING",
    "ENET_PEER_STATE_ACKNOWLEDGING_CONNECT",
    "ENET_PEER_STATE_CONNECTION_PENDING",
    "ENET_PEER_STATE_CONNECTION_SUCCEEDED",
    "ENET_PEER_STATE_CONNECTED",
    "ENET_PEER_STATE_DISCONNECT_LATER",
    "ENET_PEER_STATE_DISCONNECTING",
    "ENET_PEER_STATE_ACKNOWLEDGING_DISCONNECT",
    "ENET_PEER_STATE_ZOMBIE",
    "HOST_ANY",
    "PORT_ANY",
    "PEER_PACKET_LOSS_SCALE",
]

_initialized = False


def initialize() -> int:
    """Initialize ENet subsystem globally.

    Automatically called on import; can be called again safely.
    """
    global _initialized
    if not _initialized:
        res = lib.enet_initialize()
        if res != 0:
            raise RuntimeError(f"Failed to initialize ENet (error code {res})")
        _initialized = True
        return 0
    return 0


def deinitialize() -> None:
    """Deinitialize ENet subsystem globally.

    Registered with atexit to be called upon Python termination.
    """
    global _initialized
    if _initialized:
        lib.enet_deinitialize()
        _initialized = False


def time_get() -> int:
    """Return the monotonic time in milliseconds."""
    return int(lib.enet_time_get())


def linked_version() -> int:
    """Return the version integer of the linked ENet library."""
    return int(lib.enet_linked_version())


# Auto-initialize on import
initialize()
atexit.register(deinitialize)
