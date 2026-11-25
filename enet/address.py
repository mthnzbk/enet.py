"""ENet Address class."""

from __future__ import annotations
import ctypes
from typing import Optional
from ._bindings import C_ENetAddress, lib


class Address:
    """Represents an internet address (host IP/name and port).

    Supports both IPv4 (including IPv4-mapped) and IPv6 addresses.
    """

    def __init__(self, host: Optional[str] = None, port: int = 0) -> None:
        """Create an Address.

        Args:
            host: Hostname (e.g. "localhost", "example.com") or IP string
                  (e.g. "127.0.0.1", "::1"). If None, binds to ENET_HOST_ANY.
            port: Port number (0-65535).
        """
        self._c_addr = C_ENetAddress()
        self._c_addr.port = int(port)
        self._original_host = host

        if host is not None:
            self.set_host(host)

    @property
    def host(self) -> str:
        """Return the host string or resolved IP string."""
        if self.is_any:
            return "*"
        return self.ip

    @host.setter
    def host(self, value: Optional[str]) -> None:
        if value is None:
            for i in range(16):
                self._c_addr.host[i] = 0
            self._original_host = None
        else:
            self.set_host(value)

    @property
    def ip(self) -> str:
        """Printable IP address string (normalizes ::ffff:x.x.x.x to x.x.x.x)."""
        raw = self.get_host_ip()
        if raw.startswith("::ffff:"):
            return raw[7:]
        return raw

    @property
    def raw_ip(self) -> str:
        """Exact raw IP string returned by ENet (e.g. ::ffff:127.0.0.1)."""
        return self.get_host_ip()

    @property
    def port(self) -> int:
        """Port number."""
        return int(self._c_addr.port)

    @port.setter
    def port(self, value: int) -> None:
        self._c_addr.port = int(value)

    @property
    def is_any(self) -> bool:
        """Check if address is set to wildcard/ANY."""
        return all(b == 0 for b in self._c_addr.host)

    @property
    def is_ipv6(self) -> bool:
        """Check if address is a native IPv6 address (not IPv4-mapped)."""
        raw = self.get_host_ip()
        return ":" in raw and not raw.startswith("::ffff:")

    def set_host(self, host: str) -> None:
        """Resolve and set the host from hostname or IP string."""
        self._original_host = host
        host_bytes = host.encode("utf-8")
        ret = lib.enet_address_set_host_old(ctypes.byref(self._c_addr), host_bytes)
        if ret != 0:
            raise ValueError(f"Could not resolve host: '{host}'")

    def get_host_ip(self) -> str:
        """Return the printable IP address string as reported by ENet."""
        buf = ctypes.create_string_buffer(64)
        ret = lib.enet_address_get_host_ip_old(ctypes.byref(self._c_addr), buf, 64)
        if ret != 0:
            return "0.0.0.0"
        return buf.value.decode("utf-8", errors="replace")

    def get_host(self) -> str:
        """Attempt reverse DNS lookup for hostname, falling back to IP."""
        buf = ctypes.create_string_buffer(256)
        ret = lib.enet_address_get_host_old(ctypes.byref(self._c_addr), buf, 256)
        if ret != 0:
            return self.ip
        return buf.value.decode("utf-8", errors="replace")

    def to_c_address(self) -> C_ENetAddress:
        """Return underlying C structure copy."""
        addr = C_ENetAddress()
        addr.port = self._c_addr.port
        addr.sin6_scope_id = self._c_addr.sin6_scope_id
        for i in range(16):
            addr.host[i] = self._c_addr.host[i]
        return addr

    @classmethod
    def from_c_address(cls, c_addr: C_ENetAddress) -> Address:
        """Create Address instance from a C struct."""
        addr = cls()
        addr._c_addr.port = c_addr.port
        addr._c_addr.sin6_scope_id = c_addr.sin6_scope_id
        for i in range(16):
            addr._c_addr.host[i] = c_addr.host[i]
        return addr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Address):
            return False
        if self.port != other.port:
            return False
        return bytes(self._c_addr.host) == bytes(other._c_addr.host)

    def __hash__(self) -> int:
        return hash((bytes(self._c_addr.host), self.port))

    def __repr__(self) -> str:
        return f"Address({self.host!r}, {self.port})"

    def __str__(self) -> str:
        if self.is_ipv6:
            return f"[{self.ip}]:{self.port}"
        return f"{self.ip}:{self.port}"
