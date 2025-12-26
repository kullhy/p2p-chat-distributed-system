import subprocess
import sys
import time
import os

def main():
    # Path into current python interpreter
    python_executable = sys.executable

    print("Starting 3 P2P Chat GUI instances...")
    
    # Ports to use
    ports = [6000, 6001, 6002]
    
    processes = []
    
    try:
        for port in ports:
            print(f"Launching instance on port {port}...")
            # Launch in background
            p = subprocess.Popen([python_executable, "main.py", str(port)])
            processes.append(p)
            time.sleep(1) # Small delay to avoid binding race conditions if any
            
        print("\nAll instances launched!")
        print("Press Ctrl+C to close all instances.")
        
        # Keep script running to monitor/close processes
        while True:
            time.sleep(1)
            # Check if all closed
            if all(p.poll() is not None for p in processes):
                print("All instances closed.")
                break
                
    except KeyboardInterrupt:
        print("\nStopping all instances...")
        for p in processes:
            p.terminate()
            
if __name__ == "__main__":
    main()
