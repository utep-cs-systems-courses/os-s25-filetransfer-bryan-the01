#!/usr/bin/env python3

import socket
import sys
import threading
import mytar
sys.path.append("../lib")
import params

switchesVarDefaults = (
    (('-l', '--listenPort'), 'listenPort', 50001),
    (('-?', '--usage'), "usage", False),
)
paramMap = params.parseParams(switchesVarDefaults)

if paramMap['usage']:
    params.usage()

listenPort = paramMap['listenPort']
listenAddr = ''  # Bind to all interfaces

listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listenSock.bind((listenAddr, listenPort))
listenSock.listen(5)

print(f"[SERVER] Listening on port {listenPort}")


def handle_client(sock, addr):
    print(f"[SERVER] Thread started for {addr}")
    try:
        # Step 1: Receive initial command line (e.g., "PUT\n")
        line = b""
        while not line.endswith(b"\n"):
            chunk = sock.recv(1)
            if not chunk:
                print(f"[SERVER] {addr} disconnected before sending command.")
                sock.close()
                return
            line += chunk

        command = line.decode().strip()
        if command != "PUT":
            sock.sendall(b"ERROR: Unknown command\n")
            print(f"[SERVER] Invalid command from {addr}: {command}")
            sock.close()
            return

        print(f"[SERVER] Starting dearchive from {addr}")
        mytar.dearchive(sock)  # Use new socket-based dearchiver
        sock.sendall(b"OK\n")
        print(f"[SERVER] Transfer complete for {addr}")

    except Exception as e:
        print(f"[SERVER] Error with {addr}: {e}")
    finally:
        sock.close()
        print(f"[SERVER] Closed connection with {addr}")


#Main server loop
try:
    while True:
        conn, addr = listenSock.accept()
        print(f"[SERVER] Accepted connection from {addr}")
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()
except KeyboardInterrupt:
    print("\n[SERVER] Shutting down.")
    listenSock.close()
    sys.exit(0)
