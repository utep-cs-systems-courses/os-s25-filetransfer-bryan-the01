import sys
import os
import time

def archive(files, output_fd):
    for filename in files:
        try:
            fd = os.open(filename, os.O_RDONLY)

            # Write name
            name = f'Name: {filename}\n'.encode()
            os.write(output_fd, name)

            # Calculate size
            size = 0
            while True:
                hunk = os.read(fd, 4096)
                if not hunk:
                    break
                size += len(hunk)
            os.write(output_fd, f'Size: {size}\n'.encode())

            # Send data
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(output_fd, b'Data: ')
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                os.write(output_fd, chunk)
            os.write(output_fd, b'\n')

            os.close(fd)

        except OSError as e:
            print(f"[ERROR] Archiving file {filename}: {e}")


def dearchive(sock):
    reader = BufferedReader(sock.fileno())
    file_num = 1  # Track how many files we’ve processed

    # Initial non-blocking read check
    first_byte = reader.get()
    if first_byte is None:
        print("[SERVER] No data received from client.")
        return
    reader.buf = first_byte + reader.buf  # put byte back

    while True:
        print(f"\n[SERVER] Waiting for file #{file_num}...")

        # Read filename
        name_line = read_line(reader)
        if not name_line:
            print("[SERVER] End of archive stream.")
            break

        if not name_line.startswith("Name: "):
            print(f"[ERROR] Expected 'Name: ...', got: '{name_line}'")
            break

        ogname = name_line[6:].strip()
        filename = "Received_" + ogname
        print(f"[DEBUG] Filename: {filename}")

        # Read file size
        size_line = read_line(reader)
        if not size_line or not size_line.startswith("Size: "):
            print(f"[ERROR] Expected 'Size: ...', got: '{size_line}'")
            break

        try:
            file_size = int(size_line[6:].strip())
        except ValueError:
            print(f"[ERROR] Invalid file size: '{size_line}'")
            break

        print(f"[DEBUG] File size: {file_size} bytes")

        # Read and validate data prefix
        data_prefix = b""
        while len(data_prefix) < 6:
            byte = reader.get()
            if byte is None:
                print("[ERROR] Unexpected end of stream while reading 'Data: ' prefix")
                return
            data_prefix += byte

        if data_prefix != b'Data: ':
            print(f"[ERROR] Invalid data prefix: {data_prefix}")
            return

        # Open output file
        out_fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        bytes_written = 0

        while bytes_written < file_size:
            byte = reader.get()
            if byte is None:
                print("[ERROR] Stream ended early while reading file data.")
                break
            os.write(out_fd, byte)
            bytes_written += 1

        os.close(out_fd)
        print(f"[SERVER] Wrote {bytes_written}/{file_size} bytes to {filename} (file #{file_num})")

        # Consume trailing newline
        newline = reader.get()
        if newline != b'\n':
            print(f"[WARN] Expected newline after file data but got: {newline}")
            return

        file_num += 1



def readline():
    line = b"" #empty byte string
    while True:
        chunk = (os.read, 32) #reading small portion
        if not chunk:
            break
        line += chunk
    

class BufferedReader:
    def __init__(self, fd):
        self.fd = fd
        self.buf = b""
    def get(self):
        if len(self.buf):
            c = self.buf[:1]
            self.buf = self.buf[1:] # return slice, otherwise buf[0] is an int!
            return c
        else:
            self.buf = os.read(self.fd, 1000)
            if len(self.buf) == 0:
                return None 
            else:
                return self.get()

def isPrintable(c):             # checks if character is printable
    if c is None or c == b' ' or c == b'\n' or c == '\r':
        return False 
    return True 
            
def getWord(reader):
    while (c:= reader.get()) and not isPrintable(c): # eat non-printable chars
        pass
    if c is None:
        return None
    buf = c                     # buffer printable chars (as part of a word)
    while (c:= reader.get()) and isPrintable(c):
        buf  += c
    return buf 

# Function will return decoded string of specific line until \n is encountered
def read_line(reader):
    line = b""
    c = reader.get()
    while c and c != b"\n":
        line += c
        c = reader.get()

    return line.decode()
        
def main():
    args = sys.argv
    if len(args) < 2:
        print("Usage: tar [c|x] [file1 file2...]")
        sys.exit(1)
    mode = args[1] # create or execute
    if mode == 'c':
        if len(args) < 3:
            print("No files specified to archive")
            sys.exit(1)
        files = args[2:]
        archive(files)
        
    elif mode == 'x':
        if len(args) > 2:
            dearchive(args[2])
        else:
            dearchive()
    else:
        print("Invalid mode, specify c to create or x to extract")
        sys.exit(1)

if __name__ == "__main__":
    main()
