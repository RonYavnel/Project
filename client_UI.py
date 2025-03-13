import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from client import Client
from PIL import Image, ImageTk
import pygame
import socket
import time

class ClientUI:
    def __init__(self, root, client):
        self.root = root
        self.client = client

        self.root.title("Stock Trading Client")
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
        self.root.resizable(False, False)
        self.root.state("zoomed")

        self.play_intro_sound()
        self.show_logo_and_transition(self.create_login_frame)

    def play_intro_sound(self):
        pygame.mixer.init()
        pygame.mixer.music.load("intro.mp3")
        pygame.mixer.music.play()

    def fade_out_logo(self, logo_image, logo_label, logo_frame, next_screen_callback):
        alpha = 255  

        def step_fade():
            nonlocal alpha
            alpha -= 6  
            if alpha <= 0:
                logo_frame.destroy()  
                next_screen_callback()  
            else:
                faded_image = logo_image.copy()
                faded_image.putalpha(alpha)
                tk_image = ImageTk.PhotoImage(faded_image)
                logo_label.config(image=tk_image)
                logo_label.image = tk_image  
                logo_frame.after(50, step_fade)  

        step_fade()  

    def show_logo_and_transition(self, next_screen_callback):
        logo_frame = tk.Frame(self.root, bg="#f0f8ff")
        logo_frame.pack(fill="both", expand=True)

        original_image = Image.open("nExchange_logo.png").convert("RGBA")
        resized_image = original_image.resize((768, 503), Image.Resampling.LANCZOS)
        logo_image = resized_image.copy()

        tk_image = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(logo_frame, image=tk_image, bg="#f0f8ff")
        logo_label.image = tk_image
        logo_label.pack(expand=True)

        self.root.after(2000, lambda: self.fade_out_logo(logo_image, logo_label, logo_frame, next_screen_callback))

    def create_login_frame(self):
        self.login_frame = ttk.Frame(self.root, padding="10")
        self.login_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))

        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))

        self.login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)

    def create_main_frame(self, balance):
        self.login_frame.destroy()

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.main_frame, text="Balance: ").grid(row=0, column=0, sticky=tk.W)
        self.balance_label = ttk.Label(self.main_frame, text=f"Balance: {balance:.2f}")
        self.balance_label.grid(row=0, column=1, sticky=(tk.W, tk.E))

        ttk.Label(self.main_frame, text="Stocks:").grid(row=1, column=0, sticky=tk.W)
        self.stock_combobox = ttk.Combobox(self.main_frame)
        self.stock_combobox.grid(row=1, column=1, sticky=(tk.W, tk.E))

        # Bind stock selection to update the price
        self.stock_combobox.bind("<<ComboboxSelected>>", self.update_stock_price)

        self.update_stocks()

        ttk.Label(self.main_frame, text="Order (side$amount):").grid(row=2, column=0, sticky=tk.W)
        self.order_entry = ttk.Entry(self.main_frame)
        self.order_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))

        self.order_button = ttk.Button(self.main_frame, text="Place Order", command=self.place_order)
        self.order_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.share_price_label = ttk.Label(self.main_frame, text="Loading Price...")
        self.share_price_label.grid(row=4, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        self.client.client_socket = socket.socket()
        self.client.client_socket.connect((self.client.host, self.client.port))

        self.client.client_socket.send(self.client.e.encrypt_data(username, self.client.server_public_key))
        time.sleep(0.1)
        self.client.client_socket.send(self.client.e.encrypt_data(password, self.client.server_public_key))

        result = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)

        if result == '2':
            messagebox.showerror("Error", "Username already exists. Please enter a new one.")
            return

        balance = self.fetch_balance()

        if result == '1':
            messagebox.showinfo("Welcome", f"Welcome back {username}!")
        else:
            messagebox.showinfo("Welcome", "Nice to meet you! You are now registered.")

        self.create_main_frame(balance)

    def fetch_balance(self):
        try:
            response = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)
            
            if response == "1":
                balance = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)
                return float(balance)  
            elif response == "0":
                new_balance = simpledialog.askfloat("New User", "Enter your starting balance:")
                if new_balance is not None:
                    self.client.client_socket.send(self.client.e.encrypt_data(str(int(new_balance)), self.client.server_public_key))
                    return new_balance
            return 0.0  
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch balance: {str(e)}")
            return 0.0  

    def update_stocks(self):
        try:
            encrypted_data = self.client.client_socket.recv(4096)
            stock_data = self.client.e.decrypt_data(encrypted_data, self.client.client_private_key)
            stock_list = stock_data.strip("[]").replace("'", "").split(", ")
            self.stock_combobox["values"] = stock_list
            if stock_list:
                self.stock_combobox.current(0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update stock list: {str(e)}")

    def update_stock_price(self, event=None):
        """
        Fetch and display the latest stock price when a stock is selected.
        Ensures stock price requests are not confused with orders.
        """
        try:
            stock_symbol = self.stock_combobox.get().strip()

            if not stock_symbol:
                self.share_price_label.config(text="Select a stock to view price")
                return

            # Send the stock symbol inside a structured request
            request_message = f"{stock_symbol}"

            print(f"📢 Requesting price for stock: {stock_symbol}")

            self.client.client_socket.send(self.client.e.encrypt_data(request_message, self.client.server_public_key))

            stock_price = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)

            print(f"📢 Received stock price for {stock_symbol}: {stock_price}")

            if "Error" in stock_price:
                messagebox.showwarning("Stock Not Found", f"Stock '{stock_symbol}' not found!")
                self.share_price_label.config(text="Stock Not Found")
            else:
                self.share_price_label.config(text=f"Current Price: {stock_price}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch stock price: {str(e)}")


    def place_order(self):
        """
        Handles placing an order and updates UI accordingly.
        """
        try:
            order = self.order_entry.get().strip()
            stock_symbol = self.stock_combobox.get().strip()
            if not order or not stock_symbol:
                messagebox.showerror("Error", "Order and stock symbol cannot be empty")
                return

            print(f"📢 Placing order: {order} for stock: {stock_symbol}")

            self.client.client_socket.send(self.client.e.encrypt_data(order, self.client.server_public_key))
            response = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)

            print(f"📢 Server response for order: {response}")

            if "Error" in response:
                messagebox.showerror("Order Failed", response)
            else:
                messagebox.showinfo("Order Success", response)
                self.balance_label.config(text=f"Balance: {self.fetch_balance():.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to place order: {str(e)}")


if __name__ == "__main__":
    HOST = socket.gethostname()
    PORT = 5000
    client = Client(HOST, PORT)

    root = tk.Tk()
    app = ClientUI(root, client)
    root.mainloop()
