from core.network_engine import P2PEngine
import threading
import time
import sys

def main():
    username = input("Enter username: ").strip()
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

    engine = P2PEngine(username, callbacks=callbacks)
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
                for ip, info in engine.peers.items():
                    print(f"{ip}: {info['username']} ({info['status']})")
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
                # Parse "IP content"
                parts = cmd.split(" ", 1)
                if len(parts) < 2:
                    print("Invalid format. Use: IP CONTENT")
                    continue
                
                target_ip, content = parts
                # Find port
                peer = engine.peers.get(target_ip)
                port = peer["port"] if peer else 6000
                
                if engine.send_message(target_ip, port, content):
                    print("Sent.")
                else:
                    print("Failed to send.")

        except KeyboardInterrupt:
            engine.running = False
            break

if __name__ == "__main__":
    main()
