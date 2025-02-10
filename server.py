import socket  # Import the socket module for network communication
import json  # Import the json module for encoding/decoding JSON data
import threading  # Import the threading module for concurrent execution
import os  # Import the os module for operating system-related functions
import tkinter as tk  # Import the tkinter module for GUI
from tkinter import scrolledtext  # Import scrolledtext widget from tkinter

class ChatServer:
    def __init__(self, host, port):
        # Initialize the ChatServer instance with the specified host and port
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP socket
        self.clients = {}  # Dictionary to store connected clients and their socket objects
        self.statuses = {}  # Dictionary to store user statuses
        self.is_running = False  # Flag to indicate whether the server is running
        self.root = None  # Tkinter root window
        self.log_text = None  # Text widget for logging server activities
        self.server_thread = None  # Thread for running the server

    def start_server(self):
        # Start the server if it's not already running
        if not self.is_running:
            self.server_thread = threading.Thread(target=self.run_server)
            self.server_thread.start()

    def stop_server(self):
        # Stop the server
        if self.is_running:
            self.is_running = False
            self.server_socket.close()
            self.server_thread.join()

    def run_server(self):
        # Start the server and handle client connections
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.log(f"Server listening on port {self.port}")
        self.is_running = True
        while self.is_running:
            client_socket, client_address = self.server_socket.accept()
            self.log(f"Connected to client: {client_address}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_handler.start()

    def handle_client(self, client_socket, client_address):
        # Handle messages from a client
        while True:
            try:
                message = client_socket.recv(4096).decode()
                if not message:
                    break
                message_data = json.loads(message)
                if message_data['type'] == 'join':
                    self.handle_join_request(message_data, client_socket)
                elif message_data['type'] == 'message':
                    self.route_message(message_data, client_socket)
                elif message_data['type'] == 'status':
                    self.update_status(message_data, client_socket)
                elif message_data['type'] == 'multimedia':
                    self.route_multimedia(message_data, client_socket)
                elif message_data['type'] == 'voice_message':
                    self.route_voice_message(message_data, client_socket)
                elif message_data['type'] == 'group_message':
                    self.route_group_message(message_data, client_socket)
            except Exception as e:
                self.log(f"Error receiving message: {e}")
                break
        client_socket.close()
        if client_socket in self.clients.values():
            del self.clients[client_socket]

    def handle_join_request(self, message_data, client_socket):
        # Handle a join request from a client
        username = message_data['username']
        self.clients[username] = client_socket
        self.log(f"Client {username} joined the server")

    def update_status(self, message_data, client_socket):
        # Update the status of a client
        username = message_data['username']
        status = message_data['status']
        self.statuses[username] = status
        self.broadcast_status_updates()

    def broadcast_status_updates(self):
        # Broadcast status updates to all clients
        for client_socket in self.clients.values():
            for username, status in self.statuses.items():
                message = json.dumps({"type": "status_update", "username": username, "status": status})
                client_socket.send(message.encode())

    def route_message(self, message_data, sender_socket):
        # Route a message to the intended recipient
        recipient_username = message_data['recipient']
        if recipient_username in self.clients:
            recipient_socket = self.clients[recipient_username]
            recipient_socket.send(json.dumps(message_data).encode())
            self.log(f"Message from {message_data['sender']} to {recipient_username}: {message_data['content']}")
        else:
            self.log(f"Recipient {recipient_username} not found")

    def route_multimedia(self, message_data, sender_socket):
        # Route multimedia content to the intended recipient
        recipient_username = message_data['recipient']
        if recipient_username in self.clients:
            recipient_socket = self.clients[recipient_username]
            file_name = message_data['file_name']
            file_path = os.path.join("documents", file_name)  # Path to the document file
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    file_content = file.read()
                message_data['content'] = file_content
                recipient_socket.send(json.dumps(message_data).encode())
                self.log(f"Document '{file_name}' sent from {message_data['sender']} to {recipient_username}")
            else:
                self.log(f"Document '{file_name}' not found")
        else:
            self.log(f"Recipient {recipient_username} not found")

    def route_voice_message(self, message_data, sender_socket):
        # Route a voice message to the intended recipient
        recipient_username = message_data['recipient']
        if recipient_username in self.clients:
            recipient_socket = self.clients[recipient_username]
            recipient_socket.send(json.dumps(message_data).encode())
            self.log(f"Voice message from {message_data['sender']} to {recipient_username}")
        else:
            self.log(f"Recipient {recipient_username} not found")

    def route_group_message(self, message_data, sender_socket):
        # Route a group message to the intended recipients
        sender_username = message_data['sender']
        for recipient_username in message_data['recipients']:
            if recipient_username in self.clients and recipient_username != sender_username:
                recipient_socket = self.clients[recipient_username]
                recipient_socket.send(json.dumps(message_data).encode())
        self.log(f"Group message from {sender_username} to {message_data['recipients']}: {message_data['content']}")

    def log(self, message):
        # Log messages to the text widget
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def create_gui(self):
        # Create the GUI for the server
        self.root = tk.Tk()  # Create the root window
        self.root.title("Chat Server")  # Set the title of the window
        self.root.geometry("400x300")  # Set the dimensions of the window
        self.root.configure(bg="black")  # Set the background color of the window

        # Create a scrolled text widget for logging server activities
        self.log_text = scrolledtext.ScrolledText(self.root, width=40, height=15, bg="grey", fg="#000000")
        self.log_text.pack(pady=10)  # Pack the text widget into the window

        # Create a frame for buttons
        self.button_frame = tk.Frame(self.root, bg="#000000")
        self.button_frame.pack()  # Pack the frame into the window

        # Create buttons for starting, stopping, and quitting the server
        self.start_button = tk.Button(self.button_frame, text="Start Server", command=self.start_server,
                                      bg="sky blue", fg="white", font=("Arial", 10, "bold"))
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(self.button_frame, text="Stop Server", command=self.stop_server,
                                     bg="sky blue", fg="white", font=("Arial", 10, "bold"))
        self.stop_button.grid(row=0, column=1, padx=5)

        self.quit_button = tk.Button(self.button_frame, text="Quit", command=self.quit_server,
                                     bg="sky blue", fg="white", font=("Arial", 10, "bold"))
        self.quit_button.grid(row=0, column=2, padx=5)

        self.root.mainloop()  # Start the GUI event loop

    def quit_server(self):
        # Quit the server
        self.stop_server()  # Stop the server
        self.root.destroy()  # Destroy the root window

if __name__ == "__main__":
    # Create an instance of the ChatServer class and start the GUI
    server = ChatServer("localhost", 8000)
    server.create_gui()
