#!/usr/bin/env python3

import socket
import sys
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

try:
    serverHost, serverPort = paramMap['server'].split(':')
    serverPort = int(serverPort)
except:
    print(f"Invalid server address format: {paramMap['server']}")
    sys.exit(1)

# Parse file list
fileList = [f.strip() for f in paramMap['files'].split(',') if f.strip()]
if not fileList:
    print("No files provided! Use --files=file1,file2,...")
    sys.exit(1)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((serverHost, serverPort))
print(f"[CLIENT] Connected to {serverHost}:{serverPort}")

#Send PUT command
s.sendall(b"PUT\n")
print(f"[CLIENT] Sent PUT command")

#Send archive data
mytar.archive(fileList, output_fd=s.fileno())
time.sleep(0.05)  # Let socket breathe before shutdown
s.shutdown(socket.SHUT_WR)
print("[CLIENT] Sent archive data and shut down write end")

#Read confirmation
response = s.recv(1024).decode()
if response.strip() == "OK":
    print("[CLIENT] Server confirmed successful transfer!")
else:
    print(f"[CLIENT] Unexpected server response: {response}")

s.close()
