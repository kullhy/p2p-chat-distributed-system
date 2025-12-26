from core.network_engine import P2PEngine
import threading
import time
import sys

def main():
    if len(sys.argv) >= 2:
        username = sys.argv[1]
    else:
        username = input("Enter username: ").strip()
    
    tcp_port = 6000
    if len(sys.argv) >= 3:
        tcp_port = int(sys.argv[2])

    if not username:
        print("Username required.")
        return

    # Callbacks for CLI
    def on_log(msg):
        # Avoid printing over input prompt? A bit hard in simple CLI
        # We'll just print with a prefix
        pass # print(f"\r[LOG] {msg}\n> ", end="")

    def on_peer_update(peers):
        print(f"\n[SYSTEM] Peers updated: {len(peers)} online")
        for ip, info in peers.items():
            print(f" - {info['username']} ({ip}) [{info['status']}]")
        print("> ", end="", flush=True)

    def on_message(msg):
        sender = msg.get('sender', 'Unknown')
        content = msg.get('content', '')
        if sender != username: # proper check needed or source_ip check
            print(f"\n[{sender}]: {content}\n> ", end="", flush=True)

    callbacks = {
        "on_log": on_log,
        "on_peer_update": on_peer_update,
        "on_message": on_message
    }

    # Auto-assign UDP port based on TCP port for local testing
    # If TCP is 6000, UDP is 7000. If TCP is 6001, UDP is 7001.
    udp_port = 7000 + (tcp_port - 6000)
    
    engine = P2PEngine(username, tcp_port=tcp_port, udp_port=udp_port, callbacks=callbacks)
    engine.start()

    print(f"P2P Chat Started as {username}. Type '/peers' to list, or 'ip message' to chat.")
    print("Example: 192.168.1.5 Hello there")
    
    time.sleep(1) # Let startup logs flush

    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue
            
            if cmd == "/peers":
                print("--- Peers ---")
                for key, info in engine.peers.items():
                    print(f"{key}: {info['username']} ({info['status']})")
                print("-------------")
            elif cmd == "/exit":
                print("Exiting...")
                engine.running = False
                sys.exit(0)
            elif cmd.startswith("/group "):
                content = cmd[7:].strip()
                if content:
                    count = engine.send_group_message(content)
                    print(f"Sent to {count} peers.")
            else:
                # Parse "IP content" or "IP:Port content"
                parts = cmd.split(" ", 1)
                if len(parts) < 2:
                    print("Invalid format. Use: IP CONTENT or IP:PORT CONTENT")
                    continue
                
                target, content = parts
                
                # Check if target is in peers (using key)
                peer = engine.peers.get(target)
                if peer:
                     target_ip = peer.get("ip", target.split(":")[0])
                     port = peer["port"]
                elif ":" in target:
                     target_ip, p = target.split(":")
                     port = int(p)
                else:
                     target_ip = target
                     port = 6000 # Default fallback
                
                if engine.send_message(target_ip, port, content):
                    print("Sent.")
                else:
                    print("Failed to send.")

        except KeyboardInterrupt:
            engine.running = False
            break

if __name__ == "__main__":
    main()
