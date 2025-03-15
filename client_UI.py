import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from client import Client
from PIL import Image, ImageTk
import pygame
import socket
import time
import ast

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
        self.balance_label = ttk.Label(self.main_frame, text=balance)
        self.balance_label.grid(row=0, column=1, sticky=(tk.W, tk.E))

        ttk.Label(self.main_frame, text="Stocks:").grid(row=1, column=0, sticky=tk.W)
        
        # Stock selection dropdown
        self.stock_combobox = ttk.Combobox(self.main_frame, state="readonly")
        self.stock_combobox.grid(row=1, column=1, sticky=(tk.W, tk.E))
        # Bind event handler to show price when stock is selected
        self.stock_combobox.bind("<<ComboboxSelected>>", self.update_stock_price)

        # "Select" button to confirm stock selection
        self.select_stock_button = ttk.Button(self.main_frame, text="Select", command=self.confirm_stock_selection)
        self.select_stock_button.grid(row=1, column=2, padx=5)

        # Stock price label (Default: "Select a stock")
        self.share_price_label = ttk.Label(self.main_frame, text="Select a stock")
        self.share_price_label.grid(row=2, column=0, columnspan=2, pady=10)

        self.update_stocks()

        # Order input and button (Initially hidden)
        self.order_label = ttk.Label(self.main_frame, text="Order (side$amount):")
        self.order_entry = ttk.Entry(self.main_frame)
        self.order_button = ttk.Button(self.main_frame, text="Place Order", command=self.place_order)

        # Hide order section until stock is confirmed
        self.order_label.grid(row=3, column=0, sticky=tk.W)
        self.order_entry.grid(row=3, column=1, sticky=(tk.W, tk.E))
        self.order_button.grid(row=4, column=0, columnspan=2, pady=10)

        self.order_label.grid_remove()
        self.order_entry.grid_remove()
        self.order_button.grid_remove()

    def confirm_stock_selection(self):
        """
        Handles stock selection confirmation.
        Sends the selected stock to the server and enables order input.
        """
        try:
            stock_symbol = self.stock_combobox.get().strip()

            # Prevent selecting the placeholder
            if stock_symbol == "-- Select a Stock --":
                messagebox.showerror("Error", "Please select a valid stock.")
                return

            print(f"📢 Confirming stock selection: {stock_symbol}")

            # Send the selected stock to the server
            self.client.client_socket.send(self.client.e.encrypt_data(stock_symbol, self.client.server_public_key))

            # Show order section after successful selection
            self.order_label.grid()
            self.order_entry.grid()
            self.order_button.grid()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to confirm stock: {str(e)}")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        try:
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
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {str(e)}")

    def fetch_balance(self):
        try:
            response = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)
            
            if response == "1":
                balance = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)
                return balance  
            elif response == "0":
                new_balance = simpledialog.askinteger("New User", "Enter your starting balance:")
                if new_balance is not None:
                    self.client.client_socket.send(self.client.e.encrypt_data(str(int(new_balance)), self.client.server_public_key))
                    return new_balance
            return 0  
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch balance: {str(e)}")
            return 0

    def update_stocks(self):
        """
        Fetch the list of stocks from the server and update the dropdown.
        """
        try:
            encrypted_data = self.client.client_socket.recv(4096)
            stock_data = self.client.e.decrypt_data(encrypted_data, self.client.client_private_key)

            self.stocks_and_prices = ast.literal_eval(stock_data)

            stock_list = list(self.stocks_and_prices.keys())

            # Add a placeholder at the start
            placeholder = "-- Select a Stock --"
            stock_list.insert(0, placeholder)

            self.stock_combobox["values"] = stock_list
            self.stock_combobox.current(0)  # Set the placeholder as default

            self.share_price_label.config(text="Select a stock")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update stock list: {str(e)}")

    def update_stock_price(self, event=None):
        """
        Update the displayed stock price when a stock is selected from the dropdown.
        """
        try:
            stock_symbol = self.stock_combobox.get().strip()

            # Ignore placeholder selection
            if stock_symbol == "-- Select a Stock --":
                self.share_price_label.config(text="Select a stock")
                return

            # Get price from the cached data
            if stock_symbol in self.stocks_and_prices:
                stock_price = self.stocks_and_prices.get(stock_symbol)
                self.share_price_label.config(text=f"Current Price: {stock_price}")
            else:
                self.share_price_label.config(text="Stock price not available")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update stock price: {str(e)}")

    def place_order(self):
        """
        Handles placing an order and updates UI accordingly.
        Runs in a loop so the user can place multiple orders.
        """
        try:
            order = self.order_entry.get().strip()
            stock_symbol = self.stock_combobox.get().strip()

            # Prevent placing an order with the placeholder
            if stock_symbol == "-- Select a Stock --":
                messagebox.showerror("Error", "Please select a valid stock before placing an order.")
                return

            if not order:
                messagebox.showerror("Error", "Order cannot be empty")
                return

            print(f"📢 Placing order: {order} for stock: {stock_symbol}")

            # Send the order to the server
            self.client.client_socket.send(self.client.e.encrypt_data(order, self.client.server_public_key))
            
            # Wait for order confirmation
            order_confirmation = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)
            print(f"📢 Order confirmation: {order_confirmation}")
            
            # Wait for transaction result
            transaction_result = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)
            print(f"📢 Transaction result: {transaction_result}")
            
            if "Error" in transaction_result:
                messagebox.showerror("Order Failed", transaction_result)
                return  # Stop if the order fails
            else:                    
                # Get updated share price from server
                updated_price = self.client.e.decrypt_data(self.client.client_socket.recv(4096), self.client.client_private_key)
                print(updated_price)

                self.stocks_and_prices[stock_symbol] = int(updated_price)

                # Show a message window with the updated price
                messagebox.showinfo("Price Update", f"New price for {stock_symbol}: {updated_price}")
                
                # Update the displayed price
                self.share_price_label.config(text=f"Current Price: {updated_price}")
                
                # Clear the order entry field
                self.order_entry.delete(0, tk.END)
                
                # Get and display updated balance
                try:
                    new_balance = transaction_result.split(":")[-1].strip()
                    self.balance_label.config(text=new_balance)
                except Exception as balance_error:
                    print(f"Error updating balance display: {balance_error}")

            # Ask if the user wants to place another order
            repeat_order = messagebox.askyesno("Next Order", "Would you like to place another order?")
            if not repeat_order:
                # User doesn't want to place another order, fade out and exit
                self.fade_out_and_exit()
            else:
                # User wants to place another order, reset to stock selection
                self.reset_to_stock_selection()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to place order: {str(e)}")

    def reset_to_stock_selection(self):
        """
        Reset the UI to the stock selection state.
        Reconnects to server to get fresh stock data.
        """
        try:
            # Hide the order input controls
            self.order_label.grid_remove()
            self.order_entry.grid_remove()
            self.order_button.grid_remove()
            
            # Clear the previous stock selection
            self.stock_combobox.set("-- Select a Stock --")
            self.share_price_label.config(text="Select a stock")
            
            # Instead of trying to reconnect with username/password
            # Just send a special command to the server to reset the stock selection
            try:
                # Get fresh stock data
                self.update_stocks()
            except Exception as conn_error:
                messagebox.showerror("Connection Error", f"Failed to refresh stock data: {str(conn_error)}")
                
        except Exception as e:
            messagebox.showerror("Reset Error", f"Failed to reset stock selection: {str(e)}")
            

    def fade_out_and_exit(self):
        """
        Fades out the UI before exiting, ensuring the logo remains centered with a 2-second delay.
        """
        
        self.play_intro_sound()
        
        # Create a fullscreen frame to cover the entire window
        fade_frame = tk.Frame(self.root, bg="#f0f8ff")
        fade_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Load and resize the logo image
        original_image = Image.open("nExchange_logo.png").convert("RGBA")
        resized_image = original_image.resize((768, 503), Image.Resampling.LANCZOS)
        logo_image = resized_image.copy()

        tk_image = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(fade_frame, image=tk_image, bg="#f0f8ff")
        logo_label.image = tk_image

        # Place the label in the center
        logo_label.place(relx=0.5, rely=0.5, anchor="center")

        def start_fade():
            """Starts the fade-out effect after the delay."""
            alpha = 255  # Start with full opacity

            def step_fade():
                nonlocal alpha
                alpha -= 6
                if alpha <= 0:
                    self.root.quit()  # Exit the application after fade-out
                else:
                    faded_image = logo_image.copy()
                    faded_image.putalpha(alpha)
                    tk_faded = ImageTk.PhotoImage(faded_image)
                    logo_label.config(image=tk_faded)
                    logo_label.image = tk_faded
                    fade_frame.after(50, step_fade)  # Schedule the next fade step

            step_fade()  # Start the fade-out process

        # Delay the fade-out by 2 seconds before starting
        self.root.after(2000, start_fade)



if __name__ == "__main__":
    HOST = socket.gethostname()
    PORT = 5000
    client = Client(HOST, PORT)

    root = tk.Tk()
    app = ClientUI(root, client)
    root.mainloop()