import sys
import os
import socket

def archive(files, output_fd=1):  # Default is stdout if not specified
    for filename in files:
        try:
            fd = os.open(filename, os.O_RDONLY)

            # Encode and write filename length (4 bytes) + filename
            name_bytes = filename.encode()
            name_length = f"{len(name_bytes):04}".encode()
            os.write(output_fd, name_length)
            os.write(output_fd, name_bytes)

            # Read file contents
            file_data = b""
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                file_data += chunk

            # Write content length (4 bytes) + file data
            data_length = f"{len(file_data):04}".encode()
            os.write(output_fd, data_length)
            os.write(output_fd, file_data)

            os.close(fd)

        except OSError as e:
            print(f"[ERROR] Archiving {filename}: {e}")


def dearchive(sock):
    reader = BufferedReader(sock.fileno())

    while True:
        # Read filename length (4 bytes)
        filename_length_bytes = reader.read_exact(4)
        if filename_length_bytes is None:
            break  # End of stream
        filename_length = int(filename_length_bytes.decode())

        # Read filename
        filename_bytes = reader.read_exact(filename_length)
        filename = filename_bytes.decode()

        # Read file content length
        content_length_bytes = reader.read_exact(4)
        content_length = int(content_length_bytes.decode())

        # Read file content
        content_bytes = reader.read_exact(content_length)

        # Save the file
        out_fd = os.open("Received_" + filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        os.write(out_fd, content_bytes)
        os.close(out_fd)

        print(f"[SERVER] Saved file: Received_{filename} ({content_length} bytes)")


class BufferedReader:
    def __init__(self, fd):
        self.fd = fd
        self.buf = b""

    def get(self):
        if self.buf:
            c = self.buf[:1]
            self.buf = self.buf[1:]
            return c
        else:
            self.buf = os.read(self.fd, 1000)
            if not self.buf:
                return None
            return self.get()

    def read_exact(self, n):
        data = b""
        while len(data) < n:
            c = self.get()
            if c is None:
                return data if data else None
            data += c
        return data


def main():
    args = sys.argv
    if len(args) < 2:
        print("Usage: tar [c|x] [file1 file2...]")
        sys.exit(1)

    mode = args[1]
    if mode == 'c':
        if len(args) < 3:
            print("No files specified to archive")
            sys.exit(1)
        archive(args[2:])

    elif mode == 'x':
        dearchive(sys.stdin)  # use stdin
    else:
        print("Invalid mode, use 'c' for create or 'x' for extract")
        sys.exit(1)


if __name__ == "__main__":
    main()
