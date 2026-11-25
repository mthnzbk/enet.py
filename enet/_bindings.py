"""Low-level ctypes bindings for zpl-c/enet native library."""

import ctypes
import ctypes.util
import os
import sys

# ==============================================================================
# Library Loading
# ==============================================================================

def _find_library() -> str:
    """Find the path to the ENet native shared library."""
    # 1. Environment variable
    env_path = os.environ.get("ENET_LIBRARY_PATH")
    if env_path and os.path.isfile(env_path):
        return os.path.abspath(env_path)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = []

    if sys.platform == "win32":
        candidates.extend([
            os.path.join(base_dir, "lib", "enet.dll"),
            os.path.join(base_dir, "enet.dll"),
            os.path.join(os.path.dirname(base_dir), "enet.dll"),
        ])
    elif sys.platform == "darwin":
        candidates.extend([
            os.path.join(base_dir, "lib", "libenet.dylib"),
            os.path.join(base_dir, "libenet.dylib"),
        ])
    else: # Linux / other POSIX
        candidates.extend([
            os.path.join(base_dir, "lib", "libenet.so"),
            os.path.join(base_dir, "libenet.so"),
        ])

    for path in candidates:
        if os.path.isfile(path):
            return path

    # Fallback to system search
    sys_lib = ctypes.util.find_library("enet")
    if sys_lib:
        return sys_lib

    raise FileNotFoundError(
        "Could not find ENet native library (enet.dll / libenet.so / libenet.dylib). "
        "Please compile it or set ENET_LIBRARY_PATH environment variable."
    )

_lib_path = _find_library()
_dll = ctypes.CDLL(_lib_path)

# ==============================================================================
# C Types & Structures
# ==============================================================================

enet_uint8 = ctypes.c_uint8
enet_uint16 = ctypes.c_uint16
enet_uint32 = ctypes.c_uint32
enet_uint64 = ctypes.c_uint64
size_t = ctypes.c_size_t

class C_ENetAddress(ctypes.Structure):
    """C struct _ENetAddress (20 bytes: 16-byte IPv6/IPv4-mapped host, 2-byte port, 2-byte scope)"""
    _fields_ = [
        ("host", ctypes.c_ubyte * 16),
        ("port", enet_uint16),
        ("sin6_scope_id", enet_uint16),
    ]

class C_ENetPacket(ctypes.Structure):
    """C struct _ENetPacket (48 bytes on 64-bit)"""
    _fields_ = [
        ("referenceCount", size_t),
        ("flags", enet_uint32),
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
        ("dataLength", size_t),
        ("freeCallback", ctypes.c_void_p),
        ("userData", ctypes.c_void_p),
    ]

class C_ENetEvent(ctypes.Structure):
    """C struct _ENetEvent (32 bytes on 64-bit)"""
    _fields_ = [
        ("type", ctypes.c_int),
        ("peer", ctypes.c_void_p),
        ("channelID", enet_uint8),
        ("_pad", ctypes.c_ubyte * 3),
        ("data", enet_uint32),
        ("packet", ctypes.POINTER(C_ENetPacket)),
    ]

class C_ENetBuffer(ctypes.Structure):
    """C struct ENetBuffer"""
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("dataLength", size_t),
    ]

# ==============================================================================
# Function Prototypes
# ==============================================================================

# Initialization
_dll.enet_initialize.restype = ctypes.c_int
_dll.enet_initialize.argtypes = []

_dll.enet_deinitialize.restype = None
_dll.enet_deinitialize.argtypes = []

_dll.enet_linked_version.restype = enet_uint32
_dll.enet_linked_version.argtypes = []

_dll.enet_time_get.restype = enet_uint32
_dll.enet_time_get.argtypes = []

# Address functions
_dll.enet_address_set_host_old.restype = ctypes.c_int
_dll.enet_address_set_host_old.argtypes = [ctypes.POINTER(C_ENetAddress), ctypes.c_char_p]

_dll.enet_address_get_host_ip_old.restype = ctypes.c_int
_dll.enet_address_get_host_ip_old.argtypes = [ctypes.POINTER(C_ENetAddress), ctypes.c_char_p, size_t]

_dll.enet_address_get_host_old.restype = ctypes.c_int
_dll.enet_address_get_host_old.argtypes = [ctypes.POINTER(C_ENetAddress), ctypes.c_char_p, size_t]

_dll.enet_address_set_host_ip_old.restype = ctypes.c_int
_dll.enet_address_set_host_ip_old.argtypes = [ctypes.POINTER(C_ENetAddress), ctypes.c_char_p]

if hasattr(_dll, "enet_address_set_host_new"):
    _dll.enet_address_set_host_new.restype = ctypes.c_int
    _dll.enet_address_set_host_new.argtypes = [ctypes.POINTER(C_ENetAddress), ctypes.c_char_p]

if hasattr(_dll, "enet_address_get_host_ip_new"):
    _dll.enet_address_get_host_ip_new.restype = ctypes.c_int
    _dll.enet_address_get_host_ip_new.argtypes = [ctypes.POINTER(C_ENetAddress), ctypes.c_char_p, size_t]

# Packet functions
_dll.enet_packet_create.restype = ctypes.POINTER(C_ENetPacket)
_dll.enet_packet_create.argtypes = [ctypes.c_char_p, size_t, enet_uint32]

_dll.enet_packet_destroy.restype = None
_dll.enet_packet_destroy.argtypes = [ctypes.POINTER(C_ENetPacket)]

_dll.enet_packet_resize.restype = ctypes.POINTER(C_ENetPacket)
_dll.enet_packet_resize.argtypes = [ctypes.POINTER(C_ENetPacket), size_t]

_dll.enet_packet_copy.restype = ctypes.POINTER(C_ENetPacket)
_dll.enet_packet_copy.argtypes = [ctypes.POINTER(C_ENetPacket)]

if hasattr(_dll, "enet_packet_get_data"):
    _dll.enet_packet_get_data.restype = ctypes.c_void_p
    _dll.enet_packet_get_data.argtypes = [ctypes.POINTER(C_ENetPacket)]

if hasattr(_dll, "enet_packet_get_length"):
    _dll.enet_packet_get_length.restype = enet_uint32
    _dll.enet_packet_get_length.argtypes = [ctypes.POINTER(C_ENetPacket)]

# Host functions
_dll.enet_host_create.restype = ctypes.c_void_p
_dll.enet_host_create.argtypes = [ctypes.POINTER(C_ENetAddress), size_t, size_t, enet_uint32, enet_uint32]

_dll.enet_host_destroy.restype = None
_dll.enet_host_destroy.argtypes = [ctypes.c_void_p]

_dll.enet_host_connect.restype = ctypes.c_void_p
_dll.enet_host_connect.argtypes = [ctypes.c_void_p, ctypes.POINTER(C_ENetAddress), size_t, enet_uint32]

_dll.enet_host_check_events.restype = ctypes.c_int
_dll.enet_host_check_events.argtypes = [ctypes.c_void_p, ctypes.POINTER(C_ENetEvent)]

_dll.enet_host_service.restype = ctypes.c_int
_dll.enet_host_service.argtypes = [ctypes.c_void_p, ctypes.POINTER(C_ENetEvent), enet_uint32]

_dll.enet_host_flush.restype = None
_dll.enet_host_flush.argtypes = [ctypes.c_void_p]

_dll.enet_host_broadcast.restype = None
_dll.enet_host_broadcast.argtypes = [ctypes.c_void_p, enet_uint8, ctypes.POINTER(C_ENetPacket)]

_dll.enet_host_channel_limit.restype = None
_dll.enet_host_channel_limit.argtypes = [ctypes.c_void_p, size_t]

_dll.enet_host_bandwidth_limit.restype = None
_dll.enet_host_bandwidth_limit.argtypes = [ctypes.c_void_p, enet_uint32, enet_uint32]

_dll.enet_host_bandwidth_throttle.restype = None
_dll.enet_host_bandwidth_throttle.argtypes = [ctypes.c_void_p]

_dll.enet_host_send_raw.restype = ctypes.c_int
_dll.enet_host_send_raw.argtypes = [ctypes.c_void_p, ctypes.POINTER(C_ENetAddress), ctypes.POINTER(enet_uint8), size_t]

# Safe getters for Host (added in zpl-c/enet)
if hasattr(_dll, "enet_host_get_peers_count"):
    _dll.enet_host_get_peers_count.restype = enet_uint32
    _dll.enet_host_get_peers_count.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_host_get_packets_sent"):
    _dll.enet_host_get_packets_sent.restype = enet_uint32
    _dll.enet_host_get_packets_sent.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_host_get_packets_received"):
    _dll.enet_host_get_packets_received.restype = enet_uint32
    _dll.enet_host_get_packets_received.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_host_get_bytes_sent"):
    _dll.enet_host_get_bytes_sent.restype = enet_uint32
    _dll.enet_host_get_bytes_sent.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_host_get_bytes_received"):
    _dll.enet_host_get_bytes_received.restype = enet_uint32
    _dll.enet_host_get_bytes_received.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_host_get_mtu"):
    _dll.enet_host_get_mtu.restype = enet_uint32
    _dll.enet_host_get_mtu.argtypes = [ctypes.c_void_p]

# Peer functions
_dll.enet_peer_send.restype = ctypes.c_int
_dll.enet_peer_send.argtypes = [ctypes.c_void_p, enet_uint8, ctypes.POINTER(C_ENetPacket)]

_dll.enet_peer_receive.restype = ctypes.POINTER(C_ENetPacket)
_dll.enet_peer_receive.argtypes = [ctypes.c_void_p, ctypes.POINTER(enet_uint8)]

_dll.enet_peer_ping.restype = None
_dll.enet_peer_ping.argtypes = [ctypes.c_void_p]

_dll.enet_peer_ping_interval.restype = None
_dll.enet_peer_ping_interval.argtypes = [ctypes.c_void_p, enet_uint32]

_dll.enet_peer_timeout.restype = None
_dll.enet_peer_timeout.argtypes = [ctypes.c_void_p, enet_uint32, enet_uint32, enet_uint32]

_dll.enet_peer_reset.restype = None
_dll.enet_peer_reset.argtypes = [ctypes.c_void_p]

_dll.enet_peer_disconnect.restype = None
_dll.enet_peer_disconnect.argtypes = [ctypes.c_void_p, enet_uint32]

_dll.enet_peer_disconnect_now.restype = None
_dll.enet_peer_disconnect_now.argtypes = [ctypes.c_void_p, enet_uint32]

_dll.enet_peer_disconnect_later.restype = None
_dll.enet_peer_disconnect_later.argtypes = [ctypes.c_void_p, enet_uint32]

_dll.enet_peer_throttle_configure.restype = None
_dll.enet_peer_throttle_configure.argtypes = [ctypes.c_void_p, enet_uint32, enet_uint32, enet_uint32]

# Safe getters for Peer (added in zpl-c/enet)
if hasattr(_dll, "enet_peer_get_id"):
    _dll.enet_peer_get_id.restype = enet_uint32
    _dll.enet_peer_get_id.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_peer_get_ip"):
    _dll.enet_peer_get_ip.restype = enet_uint32
    _dll.enet_peer_get_ip.argtypes = [ctypes.c_void_p, ctypes.c_char_p, size_t]

if hasattr(_dll, "enet_peer_get_port"):
    _dll.enet_peer_get_port.restype = enet_uint16
    _dll.enet_peer_get_port.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_peer_get_rtt"):
    _dll.enet_peer_get_rtt.restype = enet_uint32
    _dll.enet_peer_get_rtt.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_peer_get_packets_sent"):
    _dll.enet_peer_get_packets_sent.restype = enet_uint64
    _dll.enet_peer_get_packets_sent.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_peer_get_packets_lost"):
    _dll.enet_peer_get_packets_lost.restype = enet_uint32
    _dll.enet_peer_get_packets_lost.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_peer_get_bytes_sent"):
    _dll.enet_peer_get_bytes_sent.restype = enet_uint64
    _dll.enet_peer_get_bytes_sent.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_peer_get_bytes_received"):
    _dll.enet_peer_get_bytes_received.restype = enet_uint64
    _dll.enet_peer_get_bytes_received.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_peer_get_state"):
    _dll.enet_peer_get_state.restype = ctypes.c_int
    _dll.enet_peer_get_state.argtypes = [ctypes.c_void_p]

if hasattr(_dll, "enet_crc32"):
    _dll.enet_crc32.restype = enet_uint32
    _dll.enet_crc32.argtypes = [ctypes.POINTER(C_ENetBuffer), size_t]

# Expose C library handle
lib = _dll
