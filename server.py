import socket
import threading
import pythonping
import sys
import ast
from pathlib import Path
import os

# Constants
HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
EXIT_COMMAND = "!EXIT"

# Socket setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# Class to store host information
class Host:
    def __init__(self, name, addr, host, files):
        self.name = name
        self.addr = addr
        self.host = host
        self.files = files

hosts = []

# Function to handle each connected client
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.\n")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            
            if msg == DISCONNECT_MESSAGE:
                connected = False

            if msg.split()[0] == "publish":
                # Handle whitespaces in lname
                # Replace first whitespace in 'publish' command with '#'
                first_whitespace_index = msg.find(' ')
                if first_whitespace_index != -1:
                    msg = msg[:first_whitespace_index] + '#' + msg[first_whitespace_index + 1:]

                # Split 'publish' command into 'lname' and 'fname'
                parts = msg.rsplit(' ', 1)
                if len(parts) == 2:
                    msg = parts[0] + '#' + parts[1]
                lname = msg.split('#')[1]
                fname = msg.split('#')[2]
                publish(lname, fname, addr)
   
            else: 
                if msg.split()[0] == "fetch":
                    fname = msg.split()[1]
                    fetch(fname, conn)
                else:
                    if msg.split('#')[0] == "name":
                        # Handle 'name' command and add the new client
                        for _host in hosts:
                            if _host.name == msg.split('#')[1]:
                                break
                        new_client = Host(msg.split('#')[1], addr, ast.literal_eval(msg.split('#')[2]), eval(msg.split('#')[3]))
                        hosts.append(new_client)
      
    conn.close()

# Function to handle server-side commands
def handle_command():
    while True:
        command = input()
        if command.split()[0] == "discover":
            hostname = command.split()[1]
            discover(hostname)
        else: 
            if command.split()[0] == "ping":
                hostname = command.split()[1]
                ping(hostname)
            else:
                if command == EXIT_COMMAND:
                    print("[EXITING] Server shutting down")
                    sys.exit(0)
                else: 
                    print("[ERROR] Invalid command")

# Function to start the server and listen for connections
def start():
    server.listen()
    command_thread = threading.Thread(target=handle_command)
    command_thread.start()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTING] {threading.active_count() - 2}")

# Function to send messages
def send(msg, conn):
    msg = str(msg).encode(FORMAT)
    msg_length = len(msg)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(msg)

# Function to discover files of a host
def discover(hostname):
    for host in hosts:
        if host.name == hostname:
            for file in host.files.items():
                print(f"{file}")
            return
    print(f"[ERROR] {hostname} does not exist")

# Function to ping a host
def ping(hostname):
    for host in hosts:
        if host.name == hostname:
            pythonping.ping(host.addr[0], verbose=True)
            return

# Function to publish a file
def publish(lname, fname, addr):
    for host in hosts:
        if host.addr == addr:
            host.files[os.path.join(Path(lname))] = fname

# Function to send address of the file client want to fetch
def fetch(fname, conn):
    for host in hosts:
        for file in host.files.items():
            if file[1] == fname:
                send(host.host, conn)

start()
