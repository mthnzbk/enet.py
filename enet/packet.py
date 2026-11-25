"""ENet Packet class."""

from __future__ import annotations
import ctypes
from typing import Union, Optional
from ._bindings import C_ENetPacket, lib
from .constants import PACKET_FLAG_RELIABLE


class Packet:
    """An ENet data packet sent to or received from a peer."""

    def __init__(
        self,
        data: Union[bytes, bytearray, memoryview, str] = b"",
        flags: int = PACKET_FLAG_RELIABLE,
        _c_ptr: Optional[ctypes.POINTER(C_ENetPacket)] = None,
        _owned: bool = True,
    ) -> None:
        """Create a new Packet or wrap an existing C packet.

        Args:
            data: Binary payload (or string encoded to UTF-8).
            flags: Bitwise OR of PACKET_FLAG_* constants (default: PACKET_FLAG_RELIABLE).
            _c_ptr: Internal pointer to C struct (for packets from events).
            _owned: Whether Python is responsible for freeing this packet.
        """
        self._owned = _owned

        if _c_ptr is not None:
            self._c_packet = _c_ptr
        else:
            if isinstance(data, str):
                raw = data.encode("utf-8")
            elif isinstance(data, (bytes, bytearray, memoryview)):
                raw = bytes(data)
            else:
                raise TypeError(f"Packet data must be bytes, bytearray, memoryview or str, not {type(data)}")

            self._c_packet = lib.enet_packet_create(raw, len(raw), int(flags))
            if not self._c_packet:
                raise MemoryError("Failed to allocate ENetPacket")

    @property
    def data(self) -> bytes:
        """Packet payload as bytes."""
        if not self._c_packet:
            return b""
        c_pkt = self._c_packet.contents
        if not c_pkt.data or c_pkt.dataLength == 0:
            return b""
        return ctypes.string_at(c_pkt.data, c_pkt.dataLength)

    @property
    def dataLength(self) -> int:
        """Length of payload in bytes (pyenet alias)."""
        return self.data_length

    @property
    def data_length(self) -> int:
        """Length of payload in bytes."""
        if not self._c_packet:
            return 0
        return int(self._c_packet.contents.dataLength)

    @property
    def flags(self) -> int:
        """Packet flags bitfield."""
        if not self._c_packet:
            return 0
        return int(self._c_packet.contents.flags)

    @property
    def sent(self) -> bool:
        """Whether the packet has been sent from queues."""
        return bool(self.flags & (1 << 8))

    @property
    def reliable(self) -> bool:
        """Whether this packet is marked as reliable."""
        return bool(self.flags & PACKET_FLAG_RELIABLE)

    def destroy(self) -> None:
        """Explicitly destroy the native packet buffer."""
        if self._c_packet and self._owned:
            lib.enet_packet_destroy(self._c_packet)
            self._c_packet = None
            self._owned = False

    def __del__(self) -> None:
        self.destroy()

    def __len__(self) -> int:
        return self.data_length

    def __bytes__(self) -> bytes:
        return self.data

    def __repr__(self) -> str:
        data_preview = self.data[:32]
        if len(self.data) > 32:
            data_preview += b"..."
        return f"Packet({data_preview!r}, flags={self.flags}, len={self.data_length})"
