"""ENet Echo Server Example.

Listens on port 12345, accepts clients, echoes back received messages,
and handles disconnects.
"""

import time
import enet

def run_server(port: int = 12345):
    # Bind to wildcard address (dual-stack IPv4/IPv6)
    server_address = enet.Address(None, port)
    
    print(f"[*] Starting ENet server on port {port}...")
    with enet.Host(server_address, peer_count=32, channel_limit=2) as server:
        print(f"[+] Server listening on {server_address}")
        print("[*] Press Ctrl+C to stop.")

        running = True
        while running:
            try:
                # Service host with 50ms timeout
                event = server.service(timeout_ms=50)

                if event.type == enet.EVENT_TYPE_CONNECT:
                    print(f"[+] Client connected from {event.peer.address} (Peer ID: {event.peer.id})")
                    event.peer.data = {"joined_at": time.time(), "messages": 0}

                elif event.type == enet.EVENT_TYPE_RECEIVE:
                    event.peer.data["messages"] += 1
                    msg = event.packet.data.decode("utf-8", errors="replace")
                    print(f"<- Received from {event.peer.address} on channel {event.channel_id}: '{msg}'")

                    # Echo message back
                    reply = f"Echo: {msg}".encode("utf-8")
                    reply_packet = enet.Packet(reply, enet.PACKET_FLAG_RELIABLE)
                    event.peer.send(event.channel_id, reply_packet)
                    server.flush()

                elif event.type in (enet.EVENT_TYPE_DISCONNECT, enet.EVENT_TYPE_DISCONNECT_TIMEOUT):
                    print(f"[-] Client {event.peer.address} disconnected (data: {event.data})")

            except KeyboardInterrupt:
                print("\n[*] Server stopping...")
                running = False


if __name__ == "__main__":
    run_server()
