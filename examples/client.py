"""ENet Client Example.

Connects to the server, sends several reliable and unsequenced packets,
waits for replies, and disconnects gracefully.
"""

import time
import enet

def run_client(host: str = "127.0.0.1", port: int = 12345):
    print(f"[*] Starting ENet client...")
    with enet.Host(None, peer_count=1, channel_limit=2) as client:
        destination = enet.Address(host, port)
        print(f"[*] Connecting to {destination}...")
        
        peer = client.connect(destination, channel_count=2, data=100)

        # Wait for connection
        connected = False
        start = time.time()
        while time.time() - start < 5.0:
            event = client.service(timeout_ms=50)
            if event.type == enet.EVENT_TYPE_CONNECT:
                connected = True
                print(f"[+] Successfully connected to server! Peer ID: {peer.id}, RTT: {peer.round_trip_time}ms")
                break

        if not connected:
            print("[-] Connection timed out.")
            return

        # Send sample messages
        messages = [
            ("Hello ENet!", enet.PACKET_FLAG_RELIABLE),
            ("Unsequenced position update (x=10, y=20)", enet.PACKET_FLAG_UNSEQUENCED),
            ("Goodbye from client!", enet.PACKET_FLAG_RELIABLE),
        ]

        for text, flags in messages:
            print(f"-> Sending: '{text}' (flags={flags})")
            pkt = enet.Packet(text.encode("utf-8"), flags)
            peer.send(channel_id=0, packet=pkt)
            client.flush()

            # Wait for echo reply
            start_wait = time.time()
            while time.time() - start_wait < 1.0:
                event = client.service(timeout_ms=50)
                if event.type == enet.EVENT_TYPE_RECEIVE:
                    reply = event.packet.data.decode("utf-8", errors="replace")
                    print(f"<- Received from server: '{reply}' (channel {event.channel_id})")
                    break
                time.sleep(0.01)

        print(f"[*] Stats: RTT={peer.round_trip_time}ms, Sent={peer.packets_sent}, Lost={peer.packets_lost}")
        print("[*] Disconnecting...")
        peer.disconnect(data=1)
        client.flush()

        # Wait for disconnect confirmation
        start_dc = time.time()
        while time.time() - start_dc < 1.0:
            event = client.service(timeout_ms=50)
            if event.type == enet.EVENT_TYPE_DISCONNECT:
                print("[+] Disconnected cleanly.")
                break

    print("[*] Done.")


if __name__ == "__main__":
    run_client()
