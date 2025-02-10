import socket  # Import the socket module for network communication
import struct  # Import the struct module for packing and unpacking binary data
import pickle  # Import the pickle module for serializing and deserializing Python objects
import threading  # Import the threading module for concurrent execution

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket object
server_socket.bind(('localhost', 49950))  # Bind the socket to the address and port
server_socket.listen(4)  # Enable the server to accept connections with a maximum of 4 queued connections

clients_connected = {}  # Dictionary to store connected clients' socket objects and their information
clients_data = {}  # Dictionary to store image data of connected clients
count = 1  # Counter variable for identifying clients

# Function to handle connection requests from clients
def connection_requests():
    global count  # Access the global count variable
    while True:  # Loop indefinitely to accept multiple connection requests
        print("Waiting for connection...")  # Print a message indicating that the server is waiting for connections
        client_socket, address = server_socket.accept()  # Accept a connection request from a client

        print(f"Connections from {address} has been established")  # Print a message indicating that a connection has been established
        print(len(clients_connected))  # Print the number of currently connected clients
        if len(clients_connected) == 4:  # Check if the maximum number of allowed connections is reached
            client_socket.send('not_allowed'.encode())  # Send a message indicating that the client is not allowed to connect

            client_socket.close()  # Close the connection with the client
            continue  # Continue to the next iteration of the loop
        else:
            client_socket.send('allowed'.encode())  # Send a message indicating that the client is allowed to connect

        try:
            client_name = client_socket.recv(1024).decode('utf-8')  # Receive the client's name
        except:
            print(f"{address} disconnected")  # Print a message indicating that the client has disconnected
            client_socket.close()  # Close the connection with the client
            continue  # Continue to the next iteration of the loop

        print(f"{address} identified itself as {client_name}")  # Print the client's address and name

        clients_connected[client_socket] = (client_name, count)  # Add client's information to the connected clients dictionary

        # Receive the size of the image data in bytes from the client
        image_size_bytes = client_socket.recv(1024)
        image_size_int = struct.unpack('i', image_size_bytes)[0]  # Unpack the received bytes to get the integer size

        client_socket.send('received'.encode())  # Send a confirmation message to the client

        # Receive the image extension from the client
        image_extension = client_socket.recv(1024).decode()

        b = b''  # Initialize an empty byte string to store the image data
        while True:  # Loop until all image data is received
            image_bytes = client_socket.recv(1024)  # Receive image data bytes from the client
            b += image_bytes  # Append the received bytes to the byte string
            if len(b) == image_size_int:  # Check if all image data is received
                break  # Exit the loop if all image data is received

        # Store the client's image data along with its name and extension in the clients_data dictionary
        clients_data[count] = (client_name, b, image_extension)

        # Serialize the clients_data dictionary using pickle
        clients_data_bytes = pickle.dumps(clients_data)
        # Pack the length of the serialized data into a binary format
        clients_data_length = struct.pack('i', len(clients_data_bytes))

        # Send the length of the serialized data to the client
        client_socket.send(clients_data_length)
        # Send the serialized data to the client
        client_socket.send(clients_data_bytes)

        # Receive a confirmation message from the client indicating that it has received the image data
        if client_socket.recv(1024).decode() == 'image_received':
            client_socket.send(struct.pack('i', count))  # Send the client's identifier to the client

            # Notify other connected clients about the new client joining the chat
            for client in clients_connected:
                if client != client_socket:
                    client.send('notification'.encode())  # Send a notification message to the client

                    # Serialize the notification data using pickle
                    data = pickle.dumps(
                        {'message': f"{clients_connected[client_socket][0]} joined the chat", 'extension': image_extension,
                         'image_bytes': b, 'name': clients_connected[client_socket][0], 'n_type': 'joined', 'id': count})
                    # Pack the length of the serialized data into a binary format
                    data_length_bytes = struct.pack('i', len(data))
                    # Send the length of the serialized data to the client
                    client.send(data_length_bytes)
                    # Send the serialized data to the client
                    client.send(data)

        count += 1  # Increment the count variable to assign a unique identifier to the next client
        # Create a new thread to handle receiving data from the client
        t = threading.Thread(target=receive_data, args=(client_socket,))
        t.start()  # Start the thread to receive data from the client

# Function to receive data from a client
def receive_data(client_socket):
    while True:  # Loop indefinitely to receive data from the client
        try:
            data_bytes = client_socket.recv(1024)  # Receive data bytes from the client
        except ConnectionResetError:  # Handle connection reset error
            print(f"{clients_connected[client_socket][0]} disconnected")  # Print a message indicating client disconnection

            # Notify other connected clients about the client leaving the chat
            for client in clients_connected:
                if client != client_socket:
                    client.send('notification'.encode())  # Send a notification message to the client

                    # Serialize the notification data using pickle
                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                         'id': clients_connected[client_socket][1], 'n_type': 'left'})

                    data_length_bytes = struct.pack('i', len(data))  # Pack the length of the data into a binary format
                    client.send(data_length_bytes)  # Send the length of the data to the client
                    client.send(data)  # Send the serialized data to the client

            # Remove the client's data from the dictionaries and close the connection
            del clients_data[clients_connected[client_socket][1]]
            del clients_connected[client_socket]
            client_socket.close()
            break  # Exit the loop
        except ConnectionAbortedError:  # Handle connection aborted error
            print(f"{clients_connected[client_socket][0]} disconnected unexpectedly.")  # Print a message indicating client disconnection

            # Notify other connected clients about the client leaving the chat
            for client in clients_connected:
                if client != client_socket:
                    client.send('notification'.encode())  # Send a notification message to the client

                    # Serialize the notification data using pickle
                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                         'id': clients_connected[client_socket][1], 'n_type': 'left'})

                    data_length_bytes = struct.pack('i', len(data))  # Pack the length of the data into a binary format
                    client.send(data_length_bytes)  # Send the length of the data to the client
                    client.send(data)  # Send the serialized data to the client

            # Remove the client's data from the dictionaries and close the connection
            del clients_data[clients_connected[client_socket][1]]
            del clients_connected[client_socket]
            client_socket.close()
            break  # Exit the loop

        for client in clients_connected:  # Iterate over connected clients
            if client != client_socket:  # Check if the client is not the sender
                client.send('message'.encode())  # Send a message indicator
                client.send(data_bytes)


connection_requests()
