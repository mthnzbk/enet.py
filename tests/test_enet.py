"""Comprehensive unit tests for enet Python package."""

import time
import pytest
import enet


def test_version_and_time():
    assert enet.ENET_VERSION_MAJOR == 2
    assert enet.ENET_VERSION_MINOR == 7
    assert enet.linked_version() >= 0x020700
    t1 = enet.time_get()
    time.sleep(0.01)
    t2 = enet.time_get()
    assert t2 >= t1


def test_address_ipv4():
    addr = enet.Address("127.0.0.1", 9999)
    assert addr.port == 9999
    assert addr.ip == "127.0.0.1"
    assert not addr.is_ipv6
    assert not addr.is_any
    assert str(addr) == "127.0.0.1:9999"

    addr2 = enet.Address("127.0.0.1", 9999)
    assert addr == addr2
    assert hash(addr) == hash(addr2)

    addr3 = enet.Address("127.0.0.1", 10000)
    assert addr != addr3


def test_address_ipv6():
    addr = enet.Address("::1", 8080)
    assert addr.port == 8080
    assert addr.is_ipv6
    assert str(addr) == "[::1]:8080"


def test_address_any():
    addr = enet.Address(None, 7777)
    assert addr.port == 7777
    assert addr.is_any
    assert addr.host == "*"


def test_packet_create():
    payload = b"Hello world networking"
    pkt = enet.Packet(payload, enet.PACKET_FLAG_RELIABLE)
    assert pkt.data == payload
    assert len(pkt) == len(payload)
    assert bytes(pkt) == payload
    assert pkt.reliable
    assert pkt.flags & enet.PACKET_FLAG_RELIABLE

    # String input
    str_pkt = enet.Packet("UTF-8 text test")
    assert str_pkt.data == b"UTF-8 text test"
    assert len(str_pkt) == len(b"UTF-8 text test")


def test_host_lifecycle():
    with enet.Host(None, peer_count=10, channel_limit=4) as client_host:
        assert client_host.peers_count >= 0
        assert client_host.mtu > 0

    with enet.Host(enet.Address(None, 49721), peer_count=16, channel_limit=2) as server_host:
        assert server_host.address is not None
        assert server_host.address.port == 49721


def test_loopback_client_server():
    port = 49725
    server_addr = enet.Address(None, port)

    with enet.Host(server_addr, peer_count=8, channel_limit=2) as server, \
         enet.Host(None, peer_count=1, channel_limit=2) as client:

        # Client connects to server
        connect_addr = enet.Address("127.0.0.1", port)
        client_peer = client.connect(connect_addr, channel_count=2, data=42)
        assert client_peer is not None

        # Custom data attribute test
        client_peer.data = {"role": "player1"}
        assert client_peer.data["role"] == "player1"

        # Drive handshake
        server_connected = False
        client_connected = False
        server_peer = None

        start = time.time()
        while time.time() - start < 3.0:
            for event in server.poll():
                if event.type == enet.EVENT_TYPE_CONNECT:
                    server_connected = True
                    server_peer = event.peer
                    assert event.data == 42
            for event in client.poll():
                if event.type == enet.EVENT_TYPE_CONNECT:
                    client_connected = True
            if server_connected and client_connected:
                break
            time.sleep(0.01)

        assert server_connected, "Server failed to register connect event"
        assert client_connected, "Client failed to register connect event"
        assert server_peer is not None

        # Client sends packet to server
        test_msg = b"Reliable packet data from client"
        pkt = enet.Packet(test_msg, enet.PACKET_FLAG_RELIABLE)
        ret = client_peer.send(0, pkt)
        assert ret == 0
        client.flush()

        # Server receives packet
        received_msg = None
        start = time.time()
        while time.time() - start < 3.0:
            client.service(0)
            for event in server.poll():
                if event.type == enet.EVENT_TYPE_RECEIVE:
                    received_msg = event.packet.data
                    assert event.channel_id == 0
                    break
            if received_msg is not None:
                break
            time.sleep(0.01)

        assert received_msg == test_msg, f"Expected {test_msg!r}, got {received_msg!r}"

        # Server sends response packet to client
        reply_msg = b"PONG from server"
        server_peer.send(1, enet.Packet(reply_msg, enet.PACKET_FLAG_RELIABLE))
        server.flush()

        # Client receives response
        client_received = None
        start = time.time()
        while time.time() - start < 3.0:
            server.service(0)
            for event in client.poll():
                if event.type == enet.EVENT_TYPE_RECEIVE:
                    client_received = event.packet.data
                    assert event.channel_id == 1
                    break
            if client_received is not None:
                break
            time.sleep(0.01)

        assert client_received == reply_msg

        # Graceful disconnect
        client_peer.disconnect(data=99)
        client.flush()

        server_disconnected = False
        start = time.time()
        while time.time() - start < 3.0:
            client.service(0)
            for event in server.poll():
                if event.type in (enet.EVENT_TYPE_DISCONNECT, enet.EVENT_TYPE_DISCONNECT_TIMEOUT):
                    server_disconnected = True
                    assert event.data == 99
                    break
            if server_disconnected:
                break
            time.sleep(0.01)

        assert server_disconnected, "Server did not receive disconnect event"


def test_broadcast():
    port = 49730
    server_addr = enet.Address(None, port)

    with enet.Host(server_addr, peer_count=4, channel_limit=2) as server, \
         enet.Host(None, peer_count=1, channel_limit=2) as client:

        peer = client.connect(enet.Address("127.0.0.1", port), 2)
        server_connected = False
        client_connected = False

        start = time.time()
        while time.time() - start < 3.0:
            for event in server.poll():
                if event.type == enet.EVENT_TYPE_CONNECT:
                    server_connected = True
            for event in client.poll():
                if event.type == enet.EVENT_TYPE_CONNECT:
                    client_connected = True
            if server_connected and client_connected:
                break
            time.sleep(0.01)

        assert server_connected and client_connected

        bcast_msg = b"Broadcast to all"
        server.broadcast(0, enet.Packet(bcast_msg, enet.PACKET_FLAG_RELIABLE))
        server.flush()

        received = False
        start = time.time()
        while time.time() - start < 3.0:
            server.service(0)
            for event in client.poll():
                if event.type == enet.EVENT_TYPE_RECEIVE and event.packet.data == bcast_msg:
                    received = True
                    break
            if received:
                break
            time.sleep(0.01)

        assert received, "Client did not receive broadcast message"
