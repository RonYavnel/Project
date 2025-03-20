import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from client import Client
from PIL import Image, ImageTk
import pygame
import socket
import time
import ast
import ctypes

# Define colors for better aesthetics (matching ServerUI)
BG_COLOR = "#f0f8ff"  # Light blue background
HEADER_BG = "#4682b4"  # Steel blue for headers
HEADER_FG = "#ffffff"  # White text for headers
FONT = ("Helvetica", 12)

class ClientUI:
    def __init__(self, root, client):
        self.root = root
        self.client = client
        self.stock_selected = False

        self.root.title("nExchange Client")
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
        self.root.resizable(False, False)
        self.root.state("zoomed")
        self.root.configure(bg=BG_COLOR)

        # Set window icon (matching ServerUI)
        self.root.iconbitmap("nExchange_logo_icon.png")
        photo = tk.PhotoImage(file="nExchange_logo_icon.png")
        self.root.iconphoto(False, photo)

        # Force taskbar icon change
        icon_path = "nExchange_logo_icon.ico"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("stock_trading_client_app")
        self.root.wm_iconbitmap(icon_path)


        self.configure_styles()
        self.play_intro_sound()
        self.show_logo_and_transition(self.create_login_frame)

    def configure_styles(self):
        """Configure ttk styles for consistent appearance (matching ServerUI)"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, font=FONT)
        style.configure("TButton", 
                       background=HEADER_BG, 
                       foreground=HEADER_FG, 
                       font=FONT, 
                       padding=5)
        style.map("TButton", 
                 background=[("active", "#5294c4")],
                 foreground=[("active", HEADER_FG)])
        style.configure("TEntry", font=FONT)
        style.configure("TCombobox", 
                      font=FONT, 
                      background="white", 
                      fieldbackground="white")
        
        # Configure Treeview for consistent look with ServerUI
        style.configure("Treeview",
                      background="white",
                      foreground="black",
                      rowheight=30,
                      fieldbackground="white",
                      font=FONT)
        style.configure("Treeview.Heading",
                      font=("Helvetica", 13, "bold"),
                      background=HEADER_BG,
                      foreground=HEADER_FG)
        style.map("Treeview.Heading", background=[("active", HEADER_BG)])

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
        logo_frame = tk.Frame(self.root, bg=BG_COLOR)
        logo_frame.pack(fill="both", expand=True)

        original_image = Image.open("nExchange_logo.png").convert("RGBA")
        resized_image = original_image.resize((768, 503), Image.Resampling.LANCZOS)
        logo_image = resized_image.copy()

        tk_image = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(logo_frame, image=tk_image, bg=BG_COLOR)
        logo_label.image = tk_image
        logo_label.pack(expand=True)

        self.root.after(2000, lambda: self.fade_out_logo(logo_image, logo_label, logo_frame, next_screen_callback))

    def create_login_frame(self):
        """Creates the login frame with vertically stacked elements"""
        # Create a container frame
        container = ttk.Frame(self.root, padding=20)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Add logo image
        logo_image = tk.PhotoImage(file="nExchange_logo_icon.png")
        logo_label = tk.Label(container, image=logo_image, bg=BG_COLOR)
        logo_label.image = logo_image  # Keep a reference to prevent garbage collection
        logo_label.pack(pady=(0, 10))
        
        # Add main title
        title_label = tk.Label(container, 
                            text="Welcome to nExchange!", 
                            font=("Helvetica", 24, "bold"), 
                            bg=BG_COLOR)
        title_label.pack(pady=(0, 20))
        
        # Subtitle container frame for vertical subtitles
        subtitle_frame = ttk.Frame(container)
        subtitle_frame.pack(pady=(0, 15))
        
        # Login subtitle (in green) - first line
        login_subtitle = tk.Label(subtitle_frame, 
                                text="Already registered? Log in!", 
                                font=("Helvetica", 16, "bold"), 
                                bg=BG_COLOR, 
                                fg="green")
        login_subtitle.pack(pady=(0, 10))
        
        # Signup subtitle (in green) - second line
        signup_subtitle = tk.Label(subtitle_frame, 
                                text="New to our system? Feel free to sign up!", 
                                font=("Helvetica", 16, "bold"), 
                                bg=BG_COLOR, 
                                fg="green")
        signup_subtitle.pack()
        
        # Login frame and fields
        self.login_frame = ttk.Frame(container, padding=20)
        self.login_frame.pack(pady=20)
        
        # Username field
        username_container = ttk.Frame(self.login_frame)
        username_container.pack(fill="x", pady=10)
        ttk.Label(username_container, text="Username:", font=FONT).pack(side="left")
        self.username_entry = ttk.Entry(username_container, width=30, font=FONT)
        self.username_entry.pack(side="right", padx=10)
        
        # Password field
        password_container = ttk.Frame(self.login_frame)
        password_container.pack(fill="x", pady=10)
        ttk.Label(password_container, text="Password:", font=FONT).pack(side="left")
        self.password_entry = ttk.Entry(password_container, show="*", width=30, font=FONT)
        self.password_entry.pack(side="right", padx=10)
        
        # Login button
        self.login_button = ttk.Button(self.login_frame, 
                                    text="Login", 
                                    command=self.login, 
                                    style="TButton", 
                                    width=20)
        self.login_button.pack(pady=20)
        
        # Bind Enter key to login
        self.login_binding = self.root.bind('<Return>', lambda event: self.login())
    
    
    def create_main_frame(self, balance):
        # Destroy the login frame completely
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create main container for trading platform
        main_container = ttk.Frame(self.root, padding=20)
        main_container.place(x=0, y=0, relwidth=1, relheight=1)

        # Header with title and logo
        header_frame = ttk.Frame(main_container)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        # Add the logo on the left
        try:
            logo_img = Image.open("nExchange_logo.png").resize((150, 100), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(header_frame, image=logo_photo)
            logo_label.image = logo_photo
            logo_label.pack(side=tk.LEFT, padx=10)
        except Exception:
            pass  # Skip if logo file is missing

        # Title and user info
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, expand=True)
        
        title_label = tk.Label(title_frame, text="nExchange Trading Platform", 
                              font=("Helvetica", 24, "bold"), bg=BG_COLOR)
        title_label.pack(anchor=tk.CENTER)

        # Balance display
        balance_frame = ttk.Frame(main_container, padding=10)
        balance_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        balance_label = tk.Label(balance_frame, text="Account Balance:", 
                                font=("Helvetica", 16, "bold"), bg=BG_COLOR)
        balance_label.pack(side=tk.LEFT, padx=10)
        
        self.balance_label = tk.Label(balance_frame, text=f"{balance}$", 
                                     font=("Helvetica", 16), bg=BG_COLOR)
        self.balance_label.pack(side=tk.LEFT)

        # Left panel for stock selection
        left_panel = ttk.Frame(main_container, padding=10)
        left_panel.grid(row=2, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        
        # Stock selection section title
        stock_selection_label = ttk.Label(left_panel, text="Stock Selection", 
                                        font=("Helvetica", 16, "bold"))
        stock_selection_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Stock selection dropdown
        ttk.Label(left_panel, text="Choose Stock:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.stock_combobox = ttk.Combobox(left_panel, state="readonly", width=20, font=FONT)
        self.stock_combobox.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        self.stock_combobox.bind("<<ComboboxSelected>>", self.update_stock_price)
        
        # Stock price display
        ttk.Label(left_panel, text="Current Price:").grid(row=2, column=0, sticky=tk.W, pady=5)
        price_frame = ttk.Frame(left_panel)
        price_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        self.share_price_label = ttk.Label(price_frame, text="Select a stock")
        self.share_price_label.pack(side=tk.LEFT)
        
        # Select button
        self.select_stock_button = ttk.Button(left_panel, text="Select Stock", 
                                            command=self.confirm_stock_selection)
        self.select_stock_button.grid(row=3, column=0, columnspan=2, pady=20)

        # Right panel for order entry
        self.right_panel = ttk.Frame(main_container, padding=10)
        self.right_panel.grid(row=2, column=1, sticky=(tk.N, tk.W, tk.E, tk.S), padx=20)
        
        # Order section title (hidden initially)
        self.order_title_label = ttk.Label(self.right_panel, text="Order Entry", 
                                         font=("Helvetica", 16, "bold"))
        self.order_title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Order input fields
        self.order_label = ttk.Label(self.right_panel, text="Order (side$amount):")
        self.order_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.order_entry = ttk.Entry(self.right_panel, width=30, font=FONT)
        self.order_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Place order button
        self.order_button = ttk.Button(self.right_panel, text="Place Order", 
                                      command=self.place_order)
        self.order_button.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Order help text
        self.help_text = "Format: B$quantity or S$quantity\nExample: B$10"
        self.help_label = ttk.Label(self.right_panel, text=self.help_text, font=("Helvetica", 10, "italic"))
        self.help_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Initially hide order section completely
        self.hide_order_section()
        
        # Update stocks from server
        self.update_stocks()

    def hide_order_section(self):
        """Hide the entire order entry section"""
        self.order_title_label.grid_remove()
        self.order_label.grid_remove()
        self.order_entry.grid_remove()
        self.order_button.grid_remove()
        self.help_label.grid_remove()

    def show_order_section(self):
        """Show the entire order entry section"""
        self.order_title_label.grid()
        self.order_label.grid()
        self.order_entry.grid()
        self.order_button.grid()
        self.help_label.grid()
        self.order_entry.bind('<Return>', lambda event: self.place_order())

    def login(self, event=None):  # Add event parameter to handle both button and key binding
        """Handle login process and transition to main frame"""
        try:
            # Unbind Return key to prevent errors after frame destruction
            if hasattr(self, 'login_binding'):
                self.root.unbind('<Return>', self.login_binding)

            # Get credentials
            username = self.username_entry.get()
            password = self.password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Please enter both username and password")
                return

            # Connect to server
            self.client.client_socket = socket.socket()
            self.client.client_socket.connect((self.client.host, self.client.port))

            # Send credentials
            self.client.client_socket.send(self.client.e.encrypt_data(username, self.client.server_public_key))
            time.sleep(0.1)
            self.client.client_socket.send(self.client.e.encrypt_data(password, self.client.server_public_key))

            # Get server response
            result = self.client.e.decrypt_data(self.client.client_socket.recv(4096), 
                                            self.client.client_private_key)

            if result == '2':
                messagebox.showerror("Error", "Username already exists. Please enter a new one.")
                return

            # Get balance
            balance = self.fetch_balance()

            # Show welcome message
            if result == '1':
                messagebox.showinfo("Welcome", f"Welcome back {username}!")
            else:
                messagebox.showinfo("Welcome", "Nice to meet you! You are now registered.")

            # Create main trading frame
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
                # Create a modal dialog window
                dialog = tk.Toplevel(self.root)
                dialog.title("Set Initial Balance")
                dialog.configure(bg=BG_COLOR)
                
                # Make it modal
                dialog.transient(self.root)
                dialog.grab_set()
                
                # Prevent closing the window
                dialog.protocol("WM_DELETE_WINDOW", lambda: None)
                
                # Center the window
                window_width = 300
                window_height = 200
                screen_width = dialog.winfo_screenwidth()
                screen_height = dialog.winfo_screenheight()
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
                
                # Add widgets
                tk.Label(dialog, text="Enter your starting balance:", font=FONT, bg=BG_COLOR).pack(pady=20)
                entry = ttk.Entry(dialog, font=FONT, justify="center")
                entry.pack(pady=10)
                entry.focus_set()
                
                # Result variable
                result = [None]
                
                def validate():
                    try:
                        value = int(entry.get())
                        if 0 < value <= 1000000:
                            result[0] = value
                            dialog.destroy()
                        else:
                            entry.delete(0, tk.END)
                            messagebox.showerror("Error", "Please enter a value between 1 and 1,000,000")
                    except ValueError:
                        entry.delete(0, tk.END)
                        messagebox.showerror("Error", "Please enter a valid number")
                
                ttk.Button(dialog, text="Confirm", command=validate).pack(pady=10)
                entry.bind('<Return>', lambda e: validate())
                
                # Wait for input
                dialog.wait_window()
                
                if result[0]:
                    self.client.client_socket.send(
                        self.client.e.encrypt_data(str(result[0]), self.client.server_public_key)
                    )
                    return result[0]
                return 0
                
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
        # Only allow stock selection if no stock has been confirmed yet
        if self.stock_selected:
            # Reset the combobox to the previously selected stock
            self.stock_combobox.set(self.selected_stock)
            messagebox.showinfo("Stock Already Selected", 
                             "You've already selected a stock. To select a different stock, place your order first or restart the application.")
            return
        
        try:
            stock_symbol = self.stock_combobox.get().strip()

            # Ignore placeholder selection
            if stock_symbol == "-- Select a Stock --":
                self.share_price_label.config(text="Select a stock")
                return

            # Get price from the cached data
            if stock_symbol in self.stocks_and_prices:
                stock_price = self.stocks_and_prices.get(stock_symbol)
                self.share_price_label.config(text=f"{stock_price}$")
            else:
                self.share_price_label.config(text="Stock price not available")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update stock price: {str(e)}")

    def confirm_stock_selection(self):
        """
        Handles stock selection confirmation.
        Sends the selected stock to the server and enables order input.
        """
        if self.stock_selected:
            messagebox.showinfo("Stock Already Selected", 
                            "You've already selected a stock. To select a different stock, place your order first or restart the application.")
            return
            
        try:
            stock_symbol = self.stock_combobox.get().strip()

            # Prevent selecting the placeholder
            if stock_symbol == "-- Select a Stock --":
                messagebox.showerror("Error", "Please select a valid stock.")
                return

            print(f"Confirming stock selection: {stock_symbol}")

            # Send the selected stock to the server
            self.client.client_socket.send(self.client.e.encrypt_data(stock_symbol, self.client.server_public_key))

            # Set stock as selected and store the symbol
            self.stock_selected = True
            self.selected_stock = stock_symbol
            
            # Disable the combobox and select button to prevent changing stock
            self.stock_combobox.config(state="disabled")
            self.select_stock_button.config(state="disabled")

            # Show order section after successful selection
            self.show_order_section()
                    
            # Focus on the order entry field and flash it
            self.order_entry.focus_set()
            self.flash_widget(self.order_entry, 3)

        except Exception as e:
            self.handle_error(f"Failed to confirm stock: {str(e)}")
            
    def flash_widget(self, widget, times=3):
        """Creates a flashing highlight effect for a widget that stops on focus or click"""
        orig_bg = widget["background"] if "background" in widget.keys() else ""
        orig_fg = widget["foreground"] if "foreground" in widget.keys() else ""
        
        # Flag to track if flashing should continue
        widget.flashing = True
        
        def stop_flashing(event=None):
            if hasattr(widget, 'flashing'):
                widget.flashing = False
                widget.configure(background=orig_bg, foreground=orig_fg)
        
        def flash_cycle(count=0):
            if not hasattr(widget, 'flashing') or not widget.flashing or count >= times * 2:
                widget.configure(background=orig_bg, foreground=orig_fg)
                return
                
            if count % 2 == 0:
                widget.configure(background="#5294c4", foreground="white")
            else:
                widget.configure(background=orig_bg, foreground=orig_fg)
                
            widget.after(300, lambda: flash_cycle(count + 1))
        
        # Bind focus and click events to stop flashing
        widget.bind('<FocusIn>', stop_flashing)
        widget.bind('<Button-1>', stop_flashing)
        
        if isinstance(widget, ttk.Combobox):
            widget.bind('<<ComboboxSelected>>', stop_flashing)
        
        # Start the flashing
        flash_cycle()
    
    def show_loading_bar(self, order):
        """Shows a loading bar for 1 second before completing the order"""
        # Create loading window
        loading_window = tk.Toplevel(self.root)
        loading_window.title("Processing Order")
        loading_window.geometry("300x150")
        loading_window.configure(bg=BG_COLOR)
        
        # Center the window
        window_width = 300
        window_height = 150
        screen_width = loading_window.winfo_screenwidth()
        screen_height = loading_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make it modal
        loading_window.transient(self.root)
        loading_window.grab_set()
        
        # Add loading message
        message = tk.Label(loading_window, 
                        text="Processing your order...", 
                        font=("Helvetica", 12),
                        bg=BG_COLOR)
        message.pack(pady=20)
        
        # Create progressbar
        progress = ttk.Progressbar(loading_window, 
                                length=200, 
                                mode='determinate')
        progress.pack(pady=10)
        
        def update_progress(count=0):
            progress['value'] = count
            if count < 100:
                loading_window.after(20, update_progress, count + 2)
            else:
                loading_window.destroy()
                self.complete_order(order)
        
        # Start progress bar
        update_progress()
    
    
    def place_order(self):
        """Handles placing an order and updates UI accordingly."""
        if not self.stock_selected:
            messagebox.showerror("Error", "Please select a stock first")
            return

        try:
            # Validate order
            order = self.order_entry.get().strip()
            if not order or '$' not in order:
                messagebox.showerror("Error", "Invalid order format. Use 'side$amount' (e.g., B$10 or S$5)")
                return

            side, amount = order.split('$')
            if side.upper() not in ['B', 'S']:
                messagebox.showerror("Error", "Invalid side. Use 'B' for buy or 'S' for sell")
                return

            try:
                amount = int(amount)
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be greater than 0")
                    return
            except ValueError:
                messagebox.showerror("Error", "Amount must be a valid number")
                return

            # Show loading bar and process order
            self.show_loading_bar(order)

        except Exception as e:
            messagebox.showerror("System Error", f"An unexpected error occurred: {str(e)}")
            print(f"Unexpected error in place_order: {str(e)}")
            self.order_entry.delete(0, tk.END)

    def complete_order(self, order):
        """Completes the order process after loading animation"""
        try:
            # Clear any pending messages from the socket
            self.client.client_socket.settimeout(0.1)
            try:
                while True:
                    self.client.client_socket.recv(4096)
            except socket.timeout:
                pass
            self.client.client_socket.settimeout(None)

            # Send the order
            self.client.client_socket.send(self.client.e.encrypt_data(order, self.client.server_public_key))

            # Wait for order confirmation
            order_confirmation = self.client.e.decrypt_data(self.client.client_socket.recv(4096), 
                                                        self.client.client_private_key)
            
            if order_confirmation != "Order received":
                messagebox.showerror("Order Error", order_confirmation)
                return

            # Wait for transaction result
            transaction_result = self.client.e.decrypt_data(self.client.client_socket.recv(4096), 
                                                        self.client.client_private_key)

            if "Error" in transaction_result:
                messagebox.showerror("Transaction Failed", transaction_result)
                return

            # Update balance if transaction successful
            if ":" in transaction_result:
                new_balance = transaction_result.split(":")[-1].strip()
                self.balance_label.config(text=f"{new_balance}$")
                self.flash_widget(self.balance_label, 3)

            # Get updated price
            updated_price = self.client.e.decrypt_data(self.client.client_socket.recv(4096), 
                                                    self.client.client_private_key)

            try:
                if not isinstance(ast.literal_eval(updated_price), dict):
                    price_as_int = int(updated_price)
                    self.stocks_and_prices[self.selected_stock] = price_as_int
                    self.share_price_label.config(text=f"{price_as_int}$")
            except (ValueError, SyntaxError) as e:
                print(f"Error processing updated price: {e}")

            # Clear the order entry
            self.order_entry.delete(0, tk.END)

            # Show confirmation and ask for another order
            self.show_transaction_confirmation(
                self.selected_stock,
                order,
                self.stocks_and_prices.get(self.selected_stock, "N/A"),
                transaction_result
            )
            self.ask_for_another_order()

        except Exception as e:
            messagebox.showerror("System Error", f"An unexpected error occurred: {str(e)}")
            print(f"Unexpected error in complete_order: {str(e)}")
            self.order_entry.delete(0, tk.END)
        
    def show_transaction_confirmation(self, stock_symbol, order, updated_price, transaction_result):
        """
        Shows a modal transaction confirmation dialog.
        """
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("Transaction Complete")
        confirm_window.geometry("400x300")
        confirm_window.configure(bg="#f0f0f0")
        
        # Center the window on screen
        window_width = 400
        window_height = 300
        screen_width = confirm_window.winfo_screenwidth()
        screen_height = confirm_window.winfo_screenheight()
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        confirm_window.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        
        # Make the window modal
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        # Prevent clicking on the main window
        confirm_window.focus_set()
        
        # Add your confirmation content here
        tk.Label(confirm_window, text="Transaction Successful", font=("Helvetica", 16, "bold"), bg="#f0f0f0").pack(pady=20)
        
        # Add transaction details
        details_frame = tk.Frame(confirm_window, bg="#f0f0f0")
        details_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(details_frame, text=f"Stock: {stock_symbol}", font=("Helvetica", 12), bg="#f0f0f0", anchor="w").pack(fill="x", pady=5)
        
        side, quantity = order.split('$')
        tk.Label(details_frame, text=f"Side: {side}", font=("Helvetica", 12), bg="#f0f0f0", anchor="w").pack(fill="x", pady=5)
        tk.Label(details_frame, text=f"Quantity: {quantity}", font=("Helvetica", 12), bg="#f0f0f0", anchor="w").pack(fill="x", pady=5)
        tk.Label(details_frame, text=f"New Price: {updated_price}$", font=("Helvetica", 12), bg="#f0f0f0", anchor="w").pack(fill="x", pady=5)
        
        # Extract new balance from transaction result if available
        if ":" in transaction_result:
            new_balance = transaction_result.split(":")[-1].strip()
            tk.Label(details_frame, text=f"New Balance: {new_balance}$", font=("Helvetica", 12), bg="#f0f0f0", anchor="w").pack(fill="x", pady=5)
        
        # Add an OK button
        ok_button = ttk.Button(confirm_window, text="OK", command=confirm_window.destroy)
        ok_button.pack(pady=20)
        
        # Wait for this window to be closed before continuing
        self.root.wait_window(confirm_window)

    def reset_stock_selection(self):
        """
        Reset the stock selection state to allow selecting a new stock.
        """
        self.stock_selected = False
        self.stock_combobox.config(state="readonly")
        self.stock_combobox.current(0)  # Reset to placeholder
        self.select_stock_button.config(state="normal")
        self.share_price_label.config(text="Select a stock")
        self.hide_order_section()

    def ask_for_another_order(self):
        """
        Ask if the user wants to place another order.
        """
        repeat_order = messagebox.askyesno("Next Order", "Would you like to place another order?")
        if not repeat_order:
            self.fade_out_and_exit()
        else:
            # Reset the stock selection to start the process again
            self.reset_stock_selection()
            # Set focus to combobox without flashing
            self.stock_combobox.focus_set()
        
    def fade_out_and_exit(self):
        """
        Fades out the UI before exiting, ensuring the logo remains centered with a 2-second delay.
        """
        
        self.play_intro_sound()
        
        # Create a fullscreen frame to cover the entire window
        fade_frame = tk.Frame(self.root, bg=BG_COLOR)
        fade_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Load and resize the logo image
        original_image = Image.open("nExchange_logo.png").convert("RGBA")
        resized_image = original_image.resize((768, 503), Image.Resampling.LANCZOS)
        logo_image = resized_image.copy()

        tk_image = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(fade_frame, image=tk_image, bg=BG_COLOR)
        logo_label.image = tk_image

        # Place the label in the center
        logo_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Thank you message
        thank_you_label = tk.Label(fade_frame, text="Thank you for using nExchange!",
                                  font=("Helvetica", 20, "bold"), bg=BG_COLOR)
        thank_you_label.place(relx=0.5, rely=0.2, anchor="center")

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
                    
                    # Also fade out the thank you message
                    fade_color = int(255 - ((255 - alpha) / 255 * 244)) # Background color component
                    text_color = f"#{fade_color:02x}{fade_color:02x}{fade_color:02x}"
                    thank_you_label.config(fg=text_color)
                    
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