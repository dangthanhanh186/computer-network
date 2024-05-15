import socket
import threading
import sys
import tqdm
import os
import ast
from pathlib import Path

# Input for server IP address
server = input("[INPUT] Enter server IP ")
name = input("[INPUT] Enter client name ")
client_port = int(input("[INPUT] Enter client port "))

# Constants
HEADER = 64
SERVER_PORT = 5050
SERVER_ADDR = (server, SERVER_PORT)
CLIENT = socket.gethostbyname(socket.gethostname())
CLIENT_ADDR = (CLIENT, client_port)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
EXIT_COMMAND = "!EXIT"

# Socket setup
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(SERVER_ADDR)

host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host.bind(CLIENT_ADDR)

# Function to list all files in a directory
def list_files(startpath):
    files_dict = {}
    for root, dirs, files in os.walk(startpath):
        for file in files:
            filepath = os.path.join(root, file)
            files_dict[filepath] = file
    return files_dict

# Get current directory and list files
current_directory = os.getcwd()
files = list_files(current_directory)

# Function to send messages through socket
def send(msg, conn):
    msg = str(msg).encode(FORMAT)
    msg_length = len(msg)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(msg)

# Function to receive messages through socket
def receive(conn):
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        return msg

# Function to handle commands entered by the user
def handle_command():
    while True:
        command = input()
        if command.split()[0] == "publish":
            # Handle whitespaces in lname
            first_whitespace_index = command.find(' ')
            if first_whitespace_index != -1:
                command = command[:first_whitespace_index] + '#' + command[first_whitespace_index + 1:]
            parts = command.rsplit(' ', 1)
            if len(parts) == 2:
                command = parts[0] + '#' + parts[1]
            lname = command.split('#')[1]
            fname = command.split('#')[2]
            publish(lname, fname)
        else: 
            if command.split()[0] == "fetch":
                fname = command.split()[1]
                fetch(fname)
            else:
                if command == EXIT_COMMAND:
                    print("[EXITING] Exiting")
                    sys.exit(0)
                else: 
                    print("[ERROR] Invalid command")

# Function to handle fetch request
def handle_fetch_request(conn, addr):
    fname = receive(conn)
    send_file(conn, fname)

# Function to send a file through socket
def send_file(conn, fname):
    lname = fname_to_lname(fname)
    file = open(str(lname), "rb")
    file_size = os.path.getsize(lname)
    send(f"{fname}", conn)
    send(str(file_size), conn)
    data = file.read()
    conn.sendall(data)
    conn.send(b"<END>")
    file.close()
    conn.close()

# Function to map filename to local name
def fname_to_lname(fname):
    for file in files.items():
        if file[1] == fname:
            return file[0]

# Function to start the client
def start():
    host.listen()
    send(f"name#{name}#{CLIENT_ADDR}#{files}", client)
    command_thread = threading.Thread(target=handle_command)
    command_thread.start()
    print(f"[LISTENING] Client is listening on {CLIENT}]")
    while True:
        conn, addr = host.accept()
        thread = threading.Thread(target=handle_fetch_request, args=(conn, addr))
        thread.start()

# Function to publish a file
def publish(lname, fname):
    files[os.path.join(Path(lname))] = fname
    send(f"publish {lname} {fname}", client)

# Function to fetch a file
def fetch(fname):
    send(f"fetch {fname}", client)
    addr = receive(client)
    addr = ast.literal_eval(addr)
    thread = threading.Thread(target=handle_fetch, args=(addr, fname))
    thread.start()

# Function to handle file fetching
def handle_fetch(addr, fname):
    requester = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    requester.connect(addr)
    send(f"{fname}", requester)
    receive_file(requester)

# Function to receive a file
def receive_file(conn):
    file_name = receive(conn)
    file_size = receive(conn)
    file = open(f"copy_of_{file_name}", "wb")
    file_bytes = b""
    done = False
    progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=int(file_size))
    while not done:
        data = conn.recv(1024)
        if file_bytes[-5:] == b"<END>":
            done = True
        else:
            file_bytes += data
        progress.update(1024)
    file.write(file_bytes)
    file.close()

start()
