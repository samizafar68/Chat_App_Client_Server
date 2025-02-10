# Chat App Client-Server

A real-time chat application built with a client-server architecture in Python, allowing both **group chats** and **personal (one-on-one) chats**. This project demonstrates the usage of **computer networks** and **socket programming** for real-time communication.

## Project Overview

The project consists of two main components:
- **Client**: The frontend where users can interact with the chat system, sending and receiving messages.
- **Server**: The backend that handles all user connections, message routing, and supports both group and personal chats.

The application allows users to:
- Chat with one or more users in a **group**.
- Chat **personally** with a specific user.
- Send and receive messages in real-time using **socket programming**.

## Features

- **Group Chat**: Users can create or join a group and chat with multiple participants at once.
- **Personal Chat**: Users can send private messages to other users, enabling personal conversations.
- **Real-Time Messaging**: Messages are sent and received instantly, without the need for page refresh.
- **Server-Side Management**: The server handles user connections, message broadcasting (for group chats), and direct message routing (for personal chats).
- **User Authentication**: Basic username system for users to connect and chat.
- **Image and Emoji Support**: Send and receive images and emojis within messages.

## Tools & Technologies

- **Python**: The core language used to implement the client-server chat app.
- **Socket Programming**: For network communication between the client and the server.
- **Threading**: Used for handling multiple client connections simultaneously in the server.
- **Pillow**: Used for image handling and sending images within messages.
- **Pickle**: For serializing objects to send over the network.
- **JSON**: For message formatting and data exchange.
- **Tkinter**: For creating the graphical user interface (GUI).
- **Base64**: For encoding binary data such as images into text format for transmission over the network.
