#!/usr/bin/env python3

import socket, sys
import time
sys.path.append("../lib")
import params
import mytar


switchesVarDefaults = (
    (('-s', '--server'), 'server', '127.0.0.1:50001'),
    (('-f', '--files'), 'files', "none"),  # comma-separated list of files
    (('-?', '--usage'), "usage", False),
)
paramMap = params.parseParams(switchesVarDefaults)

if paramMap['usage']:
    params.usage()

serverHost, serverPort = paramMap['server'].split(':')
serverPort = int(serverPort)
fileList = [f.strip() for f in paramMap['files'].split(',') if f.strip()]

if not fileList:
    print("No files provided! Use --files=file1,file2,...")
    sys.exit(1)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((serverHost, serverPort))
print(f"[CLIENT] Connected to {serverHost}:{serverPort}")


s.sendall(b"PUT\n")
print(f"[CLIENT] Sent PUT command")


mytar.archive(fileList, output_fd=s.fileno())
s.sendall(b"")  # force flush
time.sleep(0.05)  # let it breathe
s.shutdown(socket.SHUT_WR)
print("[CLIENT] Sent archive data")


response = s.recv(1024).decode()
if response.strip() == "OK":
    print("[CLIENT] Server confirmed successful transfer!")
else:
    print(f"[CLIENT] Unexpected response from server: {response}")

s.close()
