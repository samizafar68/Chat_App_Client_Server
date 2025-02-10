import socket
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk,filedialog,messagebox,scrolledtext
import pickle
from datetime import datetime
import os
import threading
import struct
import base64
import json
from tkinter import Listbox
import io




try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


class FirstScreen(tk.Tk):
    def __init__(self):
        super().__init__()

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        self.x_co = int((screen_width / 2) - (550 / 2))
        self.y_co = int((screen_height / 2) - (400 / 2)) - 80
        self.geometry(f"550x400+{self.x_co}+{self.y_co}")
        self.title("Group Chat Room")

        self.user = None
        self.image_extension = None
        self.image_path = None

        self.first_frame = tk.Frame(self, bg="sky blue")
        self.first_frame.pack(fill="both", expand=True)

        app_icon = Image.open('./images/chat_ca.png')
        app_icon = ImageTk.PhotoImage(app_icon)

        self.iconphoto(False, app_icon)

        #background = Image.open("./images/resizedbackground.png")
        #background = background.resize((550, 400), Image.LANCZOS)
        #background = ImageTk.PhotoImage(background)
        self.first_frame.configure(bg="#000000")

        upload_image = Image.open('./images/upload_ca.png')
        upload_image = upload_image.resize((25, 25), Image.LANCZOS)
        upload_image = ImageTk.PhotoImage(upload_image)

        self.user_image = './images/user.png'

       # tk.Label(self.first_frame, image=background).place(x=0, y=0)

        head = tk.Label(self.first_frame, text="Sign Up", font="lucida 17 bold", bg="grey")
        head.place(relwidth=1, y=24)

        self.profile_label = tk.Label(self.first_frame, bg="grey")
        self.profile_label.place(x=350, y=75, width=150, height=140)

        upload_button = tk.Button(self.first_frame, image=upload_image, compound="left", text="Upload Image",
                                  cursor="hand2", font="lucida 12 bold", padx=2, command=self.add_photo)
        upload_button.place(x=345, y=220)

        self.username = tk.Label(self.first_frame, text="Username", font="lucida 13 bold", bg="#000000",fg="white")
        self.username.place(x=80, y=150)

        self.username_entry = tk.Entry(self.first_frame,  font="lucida 12 bold", width=10,
                                       highlightcolor="blue", highlightthickness=1)
        self.username_entry.place(x=195, y=150)

        self.username_entry.focus_set()

        submit_button = tk.Button(self.first_frame, text="Connect", font="lucida 12 bold", padx=30, cursor="hand2",
                                  command=self.process_data,fg="#000000",bg="#87CEEB", relief="solid", bd=2)

        submit_button.place(x=200, y=275)

        self.mainloop()

    def add_photo(self):
        self.image_path = filedialog.askopenfilename()
        image_name = os.path.basename(self.image_path)
        self.image_extension = image_name[image_name.rfind('.')+1:]

        if self.image_path:
            user_image = Image.open(self.image_path)
            user_image = user_image.resize((150, 140), Image.LANCZOS)
            user_image.save('resized'+image_name)
            user_image.close()

            self.image_path = 'resized'+image_name
            user_image = Image.open(self.image_path)

            user_image = ImageTk.PhotoImage(user_image)
            self.profile_label.image = user_image
            self.profile_label.config(image=user_image)


    def process_data(self):
     if self.username_entry.get():
        self.profile_label.config(image="")

        if len((self.username_entry.get()).strip()) > 6:
            self.user = self.username_entry.get()[:6]+"."
        else:
            self.user = self.username_entry.get()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect(("localhost", 49950))
            status = client_socket.recv(1024).decode()
            if status == 'not_allowed':
                client_socket.close()
                messagebox.showinfo(title="Can't connect !", message='Sorry, server is completely occupied. Try again later')
                return

            client_socket.send(self.user.encode('utf-8'))

            if not self.image_path:
                self.image_path = self.user_image
            with open(self.image_path, 'rb') as image_data:
                image_bytes = image_data.read()

            image_len = len(image_bytes)
            image_len_bytes = struct.pack('i', image_len)
            client_socket.send(image_len_bytes)

            if client_socket.recv(1024).decode() == 'received':
                client_socket.send(str(self.image_extension).strip().encode())

            client_socket.send(image_bytes)

            clients_data_size_bytes = client_socket.recv(1024*8)
            clients_data_size_int = struct.unpack('i', clients_data_size_bytes)[0]
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break

            clients_connected = pickle.loads(b)

            client_socket.send('image_received'.encode())

            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.user} is user no. {user_id}")
            ChatScreen(self, self.first_frame, client_socket, clients_connected, user_id)

        except ConnectionRefusedError:
            messagebox.showinfo(title="Can't connect !", message="Server is offline, try again later.")
            print("Server is offline, try again later.")
        except Exception as e:
            messagebox.showinfo(title="Connection Error", message=f"An error occurred: {e}")
            print(f"An error occurred: {e}")
            client_socket.close()


class ChatScreen(tk.Canvas):
    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):
        super().__init__(parent, bg="#2b2b2b")

        self.window = 'Group ChatScreen'

        self.first_frame = first_frame
        self.first_frame.pack_forget()

        self.parent = parent
        self.parent.bind('<Return>', lambda e: self.sent_message_format(e))

        self.all_user_image = {}

        self.user_id = user_id


        self.clients_connected = clients_connected

        # self.parent.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(self.first_frame))
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_socket = client_socket
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        x_co = int((screen_width / 2) - (680 / 2))
        y_co = int((screen_height / 2) - (750 / 2)) - 80
        self.parent.geometry(f"680x750+{x_co}+{y_co}")

        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40), Image.LANCZOS)
        self.user_image = ImageTk.PhotoImage(user_image)

        # global background
        # background = Image.open("images/chat_bg_ca.jpg")
        # background = background.resize((1600, 1500), Image.ANTIALIAS)
        # background = ImageTk.PhotoImage(background)

        global group_photo
        group_photo = Image.open('./images/group_ca.png')
        group_photo = group_photo.resize((60, 60), Image.LANCZOS)
        group_photo = ImageTk.PhotoImage(group_photo)

        self.y = 140
        self.clients_online_labels = {}

        # self.create_image(0, 0, image=background)

        self.create_text(545, 120, text="Online", font="lucida 12 bold", fill="#40C961")

        tk.Label(self, text="   ", font="lucida 15 bold", bg="#b5b3b3").place(x=4, y=29)

        tk.Label(self, text="Group Chat", font="lucida 15 bold", padx=20, fg="#000000",
                 bg="#b5b3b3", anchor="w", justify="left").place(x=88, y=29, relwidth=1)

        self.create_image(60, 40, image=group_photo)

        container = tk.Frame(self)
        # 595656
        # d9d5d4
        container.place(x=40, y=120, width=450, height=550)
        self.canvas = tk.Canvas(container, bg="#595656")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#595656")

        scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        def resize_frame(e):
            self.canvas.itemconfig(scrollable_window, width=e.width)

        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.yview_moveto(1.0)

        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame)
        self.canvas.pack(fill="both", expand=True)

        send_button = tk.Button(self, text="Send", fg="#83eaf7", font="lucida 11 bold", bg="#7d7d7d", padx=10,
                                relief="solid", bd=2, command=self.sent_message_format)
        send_button.place(x=400, y=680)

        self.entry = tk.Text(self, font="lucida 10 bold", width=38, height=2,
                             highlightcolor="blue", highlightthickness=1)
        self.entry.place(x=40, y=681)

        self.entry.focus_set()

        # ---------------------------emoji code logic-----------------------------------

        emoji_data = [('emojis/u0001f44a.png', '\U0001F44A'), ('emojis/u0001f44c.png', '\U0001F44C'), ('emojis/u0001f44d.png', '\U0001F44D'),
                      ('emojis/u0001f495.png', '\U0001F495'), ('emojis/u0001f496.png', '\U0001F496'), ('emojis/u0001f4a6.png', '\U0001F4A6'),
                      ('emojis/u0001f4a9.png', '\U0001F4A9'), ('emojis/u0001f4af.png', '\U0001F4AF'), ('emojis/u0001f595.png', '\U0001F595'),
                      ('emojis/u0001f600.png', '\U0001F600'), ('emojis/u0001f602.png', '\U0001F602'), ('emojis/u0001f603.png', '\U0001F603'),
                      ('emojis/u0001f605.png', '\U0001F605'), ('emojis/u0001f606.png', '\U0001F606'), ('emojis/u0001f608.png', '\U0001F608'),
                      ('emojis/u0001f60d.png', '\U0001F60D'), ('emojis/u0001f60e.png', '\U0001F60E'), ('emojis/u0001f60f.png', '\U0001F60F'),
                      ('emojis/u0001f610.png', '\U0001F610'), ('emojis/u0001f618.png', '\U0001F618'), ('emojis/u0001f61b.png', '\U0001F61B'),
                      ('emojis/u0001f61d.png', '\U0001F61D'), ('emojis/u0001f621.png', '\U0001F621'), ('emojis/u0001f624.png', '\U0001F621'),
                      ('emojis/u0001f631.png', '\U0001F631'), ('emojis/u0001f632.png', '\U0001F632'), ('emojis/u0001f634.png', '\U0001F634'),
                      ('emojis/u0001f637.png', '\U0001F637'), ('emojis/u0001f642.png', '\U0001F642'), ('emojis/u0001f64f.png', '\U0001F64F'),
                      ('emojis/u0001f920.png', '\U0001F920'), ('emojis/u0001f923.png', '\U0001F923'), ('emojis/u0001f928.png', '\U0001F928')]

        emoji_x_pos = 490
        emoji_y_pos = 520
        for Emoji in emoji_data:
            global emojis
            emojis = Image.open(Emoji[0])
            emojis = emojis.resize((20, 20), Image.LANCZOS)
            emojis = ImageTk.PhotoImage(emojis)

            emoji_unicode = Emoji[1]
            emoji_label = tk.Label(self, image=emojis, text=emoji_unicode, bg="#194548", cursor="hand2")
            emoji_label.image = emojis
            emoji_label.place(x=emoji_x_pos, y=emoji_y_pos)
            emoji_label.bind('<Button-1>', lambda x: self.insert_emoji(x))

            emoji_x_pos += 25
            cur_index = emoji_data.index(Emoji)
            if (cur_index + 1) % 6 == 0:
                emoji_y_pos += 25
                emoji_x_pos = 490

        # -------------------end of emoji code logic-------------------------------------

        m_frame = tk.Frame(self.scrollable_frame, bg="#d9d5d4")

        t_label = tk.Label(m_frame, bg="#d9d5d4", text=datetime.now().strftime('%H:%M'), font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=f"Happy Chating {self.parent.user}",
                           font="lucida 12 bold", bg="#000000",fg="#FFFFFF")
        m_label.pack(fill="x")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.pack(fill="both", expand=True)

        self.clients_online([])

        t = threading.Thread(target=self.receive_data)
        t.setDaemon(True)
        t.start()

    def receive_data(self):
     while True:
        try:
            data_type = self.client_socket.recv(1024).decode()

            if data_type == 'notification':
                data_size = self.client_socket.recv(2048)
                data_size_int = struct.unpack('i', data_size)[0]

                b = b''
                while True:
                    data_bytes = self.client_socket.recv(1024)
                    b += data_bytes
                    if len(b) == data_size_int:
                        break
                data = pickle.loads(b)
                self.notification_format(data)

            else:
                data_bytes = self.client_socket.recv(1024)
                data = pickle.loads(data_bytes)
                self.received_message_format(data)

        except ConnectionAbortedError:
            print("you disconnected ...")
            self.client_socket.close()
            break
        except ConnectionResetError:
            messagebox.showinfo(title='No Connection !', message="Server offline..try connecting again later")
            self.client_socket.close()
            self.first_screen()
            break

    def on_closing(self):
     if self.window == 'ChatScreen':
        res = messagebox.askokcancel(title='Warning !', message="Do you really want to disconnect ?")
        if res:
            import os
            os.remove(self.all_user_image[self.user_id])
            self.client_socket.close()
            self.first_screen()
     else:
        self.parent.destroy()

    def received_message_format(self, data):

        message = data['message']
        from_ = data['from']

        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        # if not os.path.exists(f"{from_}.{sender_image_extension}"):
        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image)

        im = Image.open(f"{from_}.{sender_image_extension}")
        im = im.resize((40, 40), Image.LANCZOS)
        im = ImageTk.PhotoImage(im)

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        m_frame.columnconfigure(1, weight=1)

        t_label = tk.Label(m_frame, bg="#595656",fg="white", text=datetime.now().strftime('%H:%M'), font="lucida 7 bold",
                           justify="left", anchor="w")
        t_label.grid(row=0, column=1, padx=2, sticky="w")

        m_label = tk.Label(m_frame, wraplength=250,fg="black", bg="#c5c7c9", text=message, font="lucida 9 bold", justify="left",
                           anchor="w")
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        i_label = tk.Label(m_frame, bg="#595656", image=im)
        i_label.image = im
        i_label.grid(row=0, column=0, rowspan=2)

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def sent_message_format(self, event=None):

        message = self.entry.get('1.0', 'end-1c')

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c")

            from_ = self.user_id

            data = {'from': from_, 'message': message}
            data_bytes = pickle.dumps(data)

            self.client_socket.send(data_bytes)

            m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

            m_frame.columnconfigure(0, weight=1)

            t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'),
                               font="lucida 7 bold", justify="right", anchor="e")
            t_label.grid(row=0, column=0, padx=2, sticky="e")

            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="black", bg="#40C961",
                               font="lucida 9 bold", justify="left",
                               anchor="e")
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            i_label = tk.Label(m_frame, bg="#595656", image=self.user_image)
            i_label.image = self.user_image
            i_label.grid(row=0, column=1, rowspan=2, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1.0)

    def notification_format(self, data):
        if data['n_type'] == 'joined':

            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            self.clients_connected[client_id] = (name, image, extension)
            self.clients_online([client_id, name, image, extension])
            # print(self.clients_connected)

        elif data['n_type'] == 'left':
            client_id = data['id']
            message = data['message']
            self.remove_labels(client_id)
            del self.clients_connected[client_id]

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        t_label = tk.Label(m_frame, fg="white", bg="#595656", text=datetime.now().strftime('%H:%M'),
                           font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message, font="lucida 10 bold", justify="left", bg="sky blue")
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.yview_moveto(1.0)

    def clients_online(self, new_added):
        if not new_added:
            pass
            for user_id in self.clients_connected:
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                self.all_user_image[user_id] = f"{user_id}.{extension}"

                user = Image.open(f"{user_id}.{extension}")
                user = user.resize((45, 45), Image.LANCZOS)
                user = ImageTk.PhotoImage(user)

                b = tk.Label(self, image=user, text=name, compound="left",fg="white", bg="#2b2b2b", font="lucida 10 bold", padx=15)
                b.image = user
                self.clients_online_labels[user_id] = (b, self.y)

                b.place(x=500, y=self.y)
                self.y += 60


        else:
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            self.all_user_image[user_id] = f"{user_id}.{extension}"

            user = Image.open(f"{user_id}.{extension}")
            user = user.resize((45, 45), Image.LANCZOS)
            user = ImageTk.PhotoImage(user)

            b = tk.Label(self, image=user, text=name, compound="left", fg="white", bg="#2b2b2b",
                         font="lucida 10 bold", padx=15)
            b.image = user
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=500, y=self.y)
            self.y += 60

    def remove_labels(self, client_id):
        for user_id in self.clients_online_labels.copy():
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]
            if user_id == client_id:
                print("yes")
                b.destroy()
                del self.clients_online_labels[client_id]
                import os
                # os.remove(self.all_user_image[user_id])

            elif user_id > client_id:
                y_co -= 60
                b.place(x=510, y=y_co)
                self.clients_online_labels[user_id] = (b, y_co)
                self.y -= 60

    def insert_emoji(self, x):
        self.entry.insert("end-1c", x.widget['text'])

    def first_screen(self):
        self.destroy()
        self.parent.geometry(f"550x400+{self.parent.x_co}+{self.parent.y_co}")
        self.parent.first_frame.pack(fill="both", expand=True)
        self.window = None
class Client:
    def __init__(self, host, port, user, first):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = user
        self.client_listbox = None
        self.firstframe = first
        self.latest_messages = {}  # Dictionary to store the latest message from each sender
        self.connected_clients = set()  # Set to store the names of connected clients
        self.statuses = {}  # Dictionary to store the status of each client
        self.connect()

    def connect(self):
        self.client_socket.connect((self.host, self.port))
        self.start()

    def send_message(self, message_data):
        self.client_socket.send(json.dumps(message_data).encode())

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(4096).decode()
                if not message:
                    break
                self.update_chat_log(message)  # Update the GUI with received message
                self.update_client_listbox()  # Update the client listbox with all connected clients
            except Exception as e:
                print("Error receiving message:", e)
                break

    def start(self):
        join_message = {
            'type': 'join',
            'username': self.username
        }
        self.send_message(join_message)
        threading.Thread(target=self.receive_messages).start()
        self.update_client_listbox()  # Update the client listbox with all connected clients
        self.create_gui()

    def update_client_listbox(self, new_client=None):
        # Clear the listbox
        if self.client_listbox:
            self.client_listbox.delete(0, tk.END)

        # Populate the listbox with all connected clients
        for client_name in self.connected_clients:
            self.client_listbox.insert(tk.END, client_name)

        # If a new client is provided, add it to the listbox
        if new_client:
            self.client_listbox.insert(tk.END, new_client)

    def update_chat_log(self, message):
        message_data = json.loads(message)
        sender = message_data.get('sender', 'Unknown')
        content = message_data.get('content', '')
        file_name = message_data.get('file_name')

        # Add sender to the set of connected clients if not already present
        self.connected_clients.add(sender)

        # Append the new message to the chat log
        self.log_text.config(state=tk.NORMAL)  # Enable editing of the chat log

        # Check if the current sender is the same as the last sender
        if sender!= getattr(self, 'last_sender', None):
            self.log_text.insert(tk.END, f"{sender}:\n", "sender_name")  # Add sender's name
            # Apply formatting to the sender's name
            self.log_text.tag_config("sender_name", justify="center", font=("Arial", 14, "bold"), foreground="#000000")

        # Add message content
        if file_name:
            # If the message contains an image file
            image_data = base64.b64decode(content)
            # Convert the image data to bytes
            image_bytes = io.BytesIO(image_data)
            # Open the image
            image = Image.open(image_bytes)
            # Resize the image
            image.thumbnail((200, 200))
            # Convert the image to PhotoImage
            photo = ImageTk.PhotoImage(image)
            # Insert the image into the chat log
            self.log_text.image_create(tk.END, image=photo)
            self.log_text.insert(tk.END, '\n')
        else:
            self.log_text.insert(tk.END, f"{content}\n", "message")

        # Apply formatting to the message content
        self.log_text.tag_config("message", foreground="white", font=("Arial", 12, "bold"))

        # Scroll to the bottom of the chat log
        self.log_text.see(tk.END)

        # Disable editing of the chat log
        self.log_text.config(state=tk.DISABLED)

        # Update the last sender
        self.last_sender = sender

    def create_gui(self):
        self.firstframe.destroy()
        self.root = tk.Tk()
        tk.Label(self.root, text=f"Client {self.username} Chat",fg="white", font=("Arial", 18, "bold"),bg="#000000").pack(pady=10)
        self.root.title("Client Chat")
        self.root.geometry("480x820")
        self.root.configure(bg="black")

        self.nav_frame = tk.Frame(self.root, bg="#000000")
        self.nav_frame.pack(fill="x")

        self.title_label = tk.Label(self.nav_frame, text="Notifications", font=("Arial", 12, "bold"), fg="white",
                                    bg="#000000")
        self.title_label.pack(side="left", padx=10, pady=5)

        self.client_listbox = Listbox(self.nav_frame, font=("Arial", 12,"bold"), bg="grey", fg="white",
                                      selectbackground="#075E54")
        self.client_listbox.pack(side="left", padx=(0, 10), pady=5)
        self.client_listbox.bind("<<ListboxSelect>>", self.on_client_select)  # Bind on_client_select to ListboxSelect event

        self.log_text = scrolledtext.ScrolledText(self.root, width=40, height=20, font=("Arial", 10), bg="grey")
        self.log_text.pack(pady=10)

        # Disable the text log initially
        self.log_text.config(state=tk.DISABLED)

        self.input_frame = tk.Frame(self.root, bg="#000000")
        self.input_frame.pack()

        self.recipient_label = tk.Label(self.input_frame, text="Recipient:", font=("Arial", 12, "bold"),
                                        fg="#FFFFFF", bg="#000000")
        self.recipient_label.grid(row=0, column=0)

        self.recipient_entry = tk.Entry(self.input_frame, font=("Arial", 11, "bold"))
        self.recipient_entry.grid(row=0, column=1)

        self.message_label = tk.Label(self.input_frame, text="Message:", font=("Arial", 12, "bold"),
                                      fg="#FFFFFF", bg="#000000")
        self.message_label.grid(row=1, column=0)

        self.message_entry = tk.Entry(self.input_frame, font=("Arial", 11, "bold"))
        self.message_entry.grid(row=1, column=1)

        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message_gui,
                                     bg="#3498DB", fg="white", font=("Arial", 12, "bold"), relief="solid", bd=2)
        self.send_button.grid(row=2, column=1)
        self.select_file_button = tk.Button(self.input_frame, text="Select Image", command=self.select_image)
        self.select_file_button.grid(row=2, column=0)
        self.message_entry.bind('<Return>', lambda event: self.send_message_gui())

        self.populate_client_list()  # Populate the listbox with connected clients

        self.root.mainloop()

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.gif")])
        if file_path:
            self.send_message_with_image(file_path)

    def send_message_with_image(self, file_path):
        file_path = file_path.replace('\0', '')  # Strip null characters from file path
        chunk_size = 1024
        file_size = os.path.getsize(file_path)
        total_chunks = file_size // chunk_size + 1

        # Prepare the initial message to send file metadata
        initial_message = {
            'type': 'image',
            'file_name': os.path.basename(file_path),
            'total_chunks': total_chunks,
            'sender': self.username,
            'recipient': 'Ali'
        }

        # Send the initial metadata message
        self.send_message(initial_message)

        # Read and send file chunks
        with open(file_path, 'rb') as file:
            for chunk in range(total_chunks):
                chunk_data = file.read(chunk_size)
                # Convert the chunk data to base64
                base64_data = base64.b64encode(chunk_data).decode('utf-8')
                # Prepare the chunk message
                chunk_message = {
                    'type': 'image_chunk',
                    'chunk': chunk,
                    'total_chunks': total_chunks,
                    'file_name': os.path.basename(file_path),
                    'content': base64_data
                }
                # Send the chunk message
                self.send_message(chunk_message)

    def populate_client_list(self):
        for client_name in self.connected_clients:
            self.client_listbox.insert(tk.END, client_name)

    def on_client_select(self, event):
        # Get the selected client's name from the listbox
        selected_index = self.client_listbox.curselection()
        if selected_index:
            selected_client = self.client_listbox.get(selected_index)
            # Update the recipient entry with the selected client's name
            self.recipient_entry.delete(0, tk.END)
            self.recipient_entry.insert(0, selected_client)
            # Enable the log text widget to display messages for the selected client
            self.log_text.config(state=tk.NORMAL)

    def send_message_gui(self):
        recipient = self.recipient_entry.get()
        message = self.message_entry.get()
        if recipient and message:
            message_data = {
                'type': 'message',
                'sender': self.username,
                'recipient': recipient,
                'content': message
            }
            self.send_message(message_data)
            self.message_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "Recipient and message cannot be empty!")

    def receive_image(self):
        while True:
            try:
                message = self.client_socket.recv(4096).decode()
                if not message:
                    break
                self.update_chat_log(message)  # Update the GUI with received message
            except Exception as e:
                print("Error receiving image:", e)
                break
class Start:
    def __init__(self):
        image_path = None
        image_extension=None
        pass
    def show_chat_options(self):
        root = tk.Tk()
        root.title("Chatting App")
        root.geometry("600x480")
        root.configure(bg="#000000")

        def open_group_chat():
            open_first_screen()

        def open_client_chat():
            root.destroy()
            create_signup_ui()
            
        def open_first_screen():           
            root.destroy()
            first_screen = FirstScreen()
            first_screen.mainloop()
        
        tk.Label(root, text="Welcome to My Chatt App",fg="white", font=("Arial", 18, "bold"),bg="#000000").pack(pady=10)
        group_chat_button = tk.Button(root, text="Group Chat", font="lucida 12 bold", cursor="hand2", command=open_group_chat, bg="#3498DB", fg="white", padx=30, pady=20, relief="solid", bd=2)
        group_chat_button.pack(pady=80)

        client_chat_button = tk.Button(root, text="Client Chat", font="lucida 12 bold", cursor="hand2", command=open_client_chat, bg="#3498DB", fg="white", padx=30, pady=20, relief="solid", bd=2)
        client_chat_button.pack(pady=0)

        root.mainloop()

def create_signup_ui():
    def add_photo():
        image_path = filedialog.askopenfilename()
        if image_path:
            image_name = os.path.basename(image_path)
            image_extension = image_name[image_name.rfind('.') + 1:]

            user_image = Image.open(image_path)
            user_image = user_image.resize((150, 140), Image.LANCZOS)
            user_image.save('resized' + image_name)
            user_image.close()

            resized_image_path = 'resized' + image_name
            user_image = Image.open(resized_image_path)
            user_image = ImageTk.PhotoImage(user_image)

            profile_label.image = user_image
            profile_label.config(image=user_image)

    def process_data():
        username = username_entry.get()  # Retrieve the username from the entry widget
        client = Client("localhost", 8000, username,first_frame)  
    root = tk.Tk()
    root.title("Client Chat")

    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    x_co = int((screen_width / 2) - (550 / 2))
    y_co = int((screen_height / 2) - (400 / 2)) - 80
    root.geometry(f"550x400+{x_co}+{y_co}")

    first_frame = tk.Frame(root, bg="sky blue")
    first_frame.pack(fill="both", expand=True)

    root.app_icon = Image.open('./images/chat_ca.png')
    root.app_icon = ImageTk.PhotoImage(root.app_icon)
    root.iconphoto(False, root.app_icon)

   # root.background = Image.open("./images/login_bg_ca.jpg")
    #root.background = root.background.resize((550, 400), Image.LANCZOS)
    #root.background = ImageTk.PhotoImage(root.background)
    #tk.Label(first_frame, image=root.background).place(x=0, y=0)
    first_frame.configure(bg="#000000")
    head = tk.Label(first_frame, text="Sign Up", font="lucida 17 bold", bg="grey")
    head.place(relwidth=1, y=24)

    profile_label = tk.Label(first_frame, bg="#000000")
    profile_label.place(x=350, y=75, width=150, height=140)

    upload_image = Image.open('./images/upload_ca.png')
    upload_image = upload_image.resize((25, 25), Image.LANCZOS)
    upload_image = ImageTk.PhotoImage(upload_image)

    username = tk.Label(first_frame, text="Username", font="lucida 12 bold", bg="#000000",fg="#FFFFFF")
    username.place(x=80, y=150)

    username_entry = tk.Entry(first_frame, font="lucida 12 bold", width=10, highlightcolor="blue", highlightthickness=1)
    username_entry.place(x=195, y=150)
    username_entry.focus_set()
    username_entry.get()
    #print(user)

    upload_button = tk.Button(first_frame, image=upload_image, compound="left", text="Upload Image",
                              cursor="hand2", font="lucida 12 bold", padx=2, command=add_photo)
    upload_button.place(x=345, y=220)

    submit_button = tk.Button(first_frame, text="Connect", font="lucida 12 bold", padx=30, cursor="hand2",
                              bg="#87CEEB", relief="solid", bd=2,command=process_data)
    submit_button.place(x=200, y=275)


    root.mainloop()

start = Start()
start.show_chat_options()


