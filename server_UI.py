from tkinter import *
from tkinter import ttk
from db_tools import DB_Tools
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import pygame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Define colors for better aesthetics
BG_COLOR = "#f0f8ff"  # Light blue background
HEADER_BG = "#4682b4"  # Steel blue for headers
HEADER_FG = "#ffffff"  # White text for headers
FONT = ("Helvetica", 12)

class ServerUI:
    # initialize the ServerUI class
    def __init__(self, on_close_callback):
        self.stock_graph_windows = {}  # To store graph windows for each stock
        self.connected_clients_tree = None # To store the connected clients table
        self.transactions_tree = None # To store the transactions table
        self.tls = DB_Tools("stocktradingdb")  # Initialize the database tools
        self.on_close_callback = on_close_callback  # Callback to stop the server

    def show_logo_and_transition(self, root, next_screen_callback):
        # Create a frame for the full-screen logo display
        logo_frame = Frame(root, bg="#f0f8ff")
        logo_frame.pack(fill="both", expand=True)

        # Load and resize the image
        original_image = Image.open("C:\\Users\\ronya\\OneDrive\\Project\\FirstMVP\\nExchange_logo.png").convert("RGBA")
        resized_image = original_image.resize((768, 503), Image.Resampling.LANCZOS)  # Resize with high-quality resampling
        logo_image = resized_image.copy()

        # Create a copy of the resized image to preserve transparency
        logo_image = resized_image.copy()

        # Display the image in a label
        tk_image = ImageTk.PhotoImage(logo_image)
        logo_label = Label(logo_frame, image=tk_image, bg="#f0f8ff")
        logo_label.image = tk_image  # Keep reference to avoid garbage collection
        logo_label.pack(expand=True)

        # Start fading out the logo after 2 seconds
        root.after(2000, lambda: self.fade_out_logo(logo_image, logo_label, logo_frame, next_screen_callback))

    def fade_out_logo(self, logo_image, logo_label, logo_frame, next_screen_callback):
        alpha = 255  # Start fully opaque

        def step_fade():
            nonlocal alpha
            alpha -= 6  # Gradually decrease opacity
            if alpha <= 0:
                logo_frame.destroy()  # Remove the logo frame completely
                next_screen_callback()  # Show the main UI
            else:
                # Create a new image with reduced opacity
                faded_image = logo_image.copy()
                faded_image.putalpha(alpha)  # Update alpha channel
                tk_image = ImageTk.PhotoImage(faded_image)
                logo_label.config(image=tk_image)
                logo_label.image = tk_image  # Keep a reference to avoid garbage collection
                logo_frame.after(50, step_fade)  # Schedule the next step

        step_fade()  # Start the fade animation
        
    # Function to play the intro sound
    def play_intro_sound(self):
        pygame.mixer.init()
        pygame.mixer.music.load("intro.mp3")
        pygame.mixer.music.play()

    # Function to configure the styles of the UI
    def configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
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
    
    def show_stock_graph(self, stock_name, prices):
        # Function to handle the closing of the graph window
        def on_close():
            if stock_name in self.stock_graph_windows:
                self.stock_graph_windows[stock_name][0].destroy()  # Destroy the window properly
                del self.stock_graph_windows[stock_name]  # Remove the window reference

        # Check if the stock already has a valid graph window
        if stock_name in self.stock_graph_windows and self.stock_graph_windows[stock_name][0].winfo_exists():
            graph_window, canvas, ax = self.stock_graph_windows[stock_name]
        else:
            # Create a new graph window if not already opened or if it was destroyed
            graph_window = Toplevel()
            graph_window.title(f"Price Changes for {stock_name}")
            graph_window.geometry("600x400")

            # Add a handler to clean up and close the window properly when it is closed
            graph_window.protocol("WM_DELETE_WINDOW", on_close)

            # Create a figure and plot the graph
            fig, ax = plt.subplots(figsize=(6, 4))
            canvas = FigureCanvasTkAgg(fig, master=graph_window)
            canvas.get_tk_widget().pack(fill=BOTH, expand=True)

            # Store the new window reference
            self.stock_graph_windows[stock_name] = (graph_window, canvas, ax)

        # Update the graph using refresh_stock_graphs
        self.refresh_stock_graphs({stock_name: prices})

        # Bring the window to the front
        graph_window.deiconify()
        graph_window.lift()

    def show_stocks_table(self, root, stocks, stock_prices_history):
        # Creates a space (a Frame) to hold the stock table.
        stock_frame = Frame(root, width=600, height=300, bg=BG_COLOR)
        stock_frame.pack_propagate(False) # Prevents the frame from resizing to fit its contents.
        stock_frame.place(relx=0.74, rely=0.41, anchor="n") # Positions the frame on the right side of the window.

        # Adds a title "Stocks" above the table.
        stock_label = Label(root, text="Stocks", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
        stock_label.place(relx=0.76, rely=0.36, anchor="ne") # Positions the label above the frame.

        # Defines the column name for the table.
        columns = ("Stock Name",)
        # Creates the table (a Treeview widget) to display the stock names.
        stock_tree = ttk.Treeview(stock_frame, columns=columns, show="headings", height=5)
        stock_tree.heading("Stock Name", text="Stock Name") # Sets the column heading.
        stock_tree.column("Stock Name", width=180, anchor="center") # Sets the column width and alignment.

        # Adds each stock name to the table.
        for stock_name in stocks:
            stock_tree.insert("", "end", values=(stock_name,))

        # Defines what happens when you double-click a stock in the table.
        def on_stock_select(event):
            selected_item = stock_tree.selection()[0] # Gets the selected stock.
            stock_name = stock_tree.item(selected_item, "values")[0] # Gets the name of the selected stock.
            prices = stock_prices_history.get(stock_name, [100] * 10)  # Gets the price history for the stock, or defaults to a list of 100s if not found.
            self.show_stock_graph(stock_name, prices) # Calls another function to display a graph of the stock's price history.

        stock_tree.bind("<Double-1>", on_stock_select) # Makes the `on_stock_select` function run when you double-click a stock.

        # Adds a scrollbar to the table, in case there are too many stocks to fit.
        scrollbar = ttk.Scrollbar(stock_frame, orient="vertical", command=stock_tree.yview)
        stock_tree.configure(yscrollcommand=scrollbar.set)

        # Positions the scrollbar and the table within the frame.
        scrollbar.pack(side="right", fill="y")
        stock_tree.pack(side="left", fill="both", expand=True)

    def show_transactions_table(self, root):
        # Add a title "Transactions" above the table.
        transactions_label = Label(root, text="Transactions", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
        transactions_label.pack(anchor="n", pady=10)

        # Create a space (a Frame) to hold the transactions table.
        top_frame = Frame(root, width=1250, height=200, bg=BG_COLOR)
        top_frame.pack_propagate(False)
        top_frame.place(x=150, rely=0.07) # Position the frame at the top of the window.

        # Define the column names for the table.
        columns = ("Username", "Client ID", "Side", "Stock Symbol", "Share Price", "Amount", "Time Stamp")
        # Create the table (a Treeview widget) to display the transactions.
        tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=5)

        # Set up the headings for each column.
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        # Fetch transactions from the database and add them to the table.
        list_of_transactions = self.tls.get_all_rows("transactions")
        for transaction in list_of_transactions:
            tree.insert("", "end", values=transaction)
            tree.see(tree.get_children()[-1])  # Auto-scroll to the latest transaction.

        # Add a scrollbar to the table, in case there are too many transactions to fit.
        scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Positions the scrollbar and the table within the frame.
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        return tree  # Return the table so it can be updated later.

    def show_all_clients_table(self, root, dict_of_all_clients, dict_of_active_clients):
        # Ensure dict_of_active_clients is a dictionary
        if not isinstance(dict_of_active_clients, dict):
            dict_of_active_clients = {}

        # Create a space (a Frame) to hold the connected people table.
        top_frame = Frame(root, width=800, height=300, bg=BG_COLOR)
        top_frame.pack_propagate(False)  # Keep the frame from resizing.
        top_frame.place(relx=0.27, rely=0.41, anchor="n")  # Position the frame.

        # Add a title "Connected People" above the table.
        connected_people_label = Label(root, text="All Connected Clients", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
        connected_people_label.place(relx=0.34, rely=0.36, anchor="ne")  # Position the title.

        # Define the column names for the table.
        columns = ("IP Address", "Username", "DDoS Status", "Connection Status")
        # Create the table (a Treeview widget) to display the connected people.
        tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=5)

        # Set up the headings for each column.
        for col in columns:
            tree.heading(col, text=col)  # Set the text for the heading.
            tree.column(col, width=100, anchor="center")  # Set the width and alignment.

        # Define tags for coloring rows
        tree.tag_configure("accepted", background="#d4edda")  # Light green for accepted
        tree.tag_configure("blocked", background="#f8d7da")  # Light red for blocked

        # Add each connected person to the table.
        for (ip, username), ddos_status in dict_of_all_clients.items():
            tag = "accepted" if ddos_status.lower() == "accepted" else "blocked"
            
            if any(ip == key[0] for key in dict_of_active_clients.keys()):
                # If the IP is in the active clients, set the connection status to "Active"
                connection_status = "Online"
            else:
                # If the IP is not in the active clients, set the connection status to "Offline"
                connection_status = "Offline"
                
            tree.insert("", "end", values=(ip, username, ddos_status, connection_status), tags=(tag,))  # Add the data with the appropriate tag.

        # Add a scrollbar to the table, in case there are too many connected people to fit.
        scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)  # Link the scrollbar to the table.

        # Positions the scrollbar and the table within the frame.
        scrollbar.pack(side="right", fill="y")  # Place the scrollbar on the right.
        tree.pack(side="left", fill="both", expand=True)  # Place the table and make it fill the space.

        return tree  # Give back the table so we can use it later.
    
    def initialize_ui_references(self, connected_clients_widget, transactions_widget):
        # Initializes the global references to the Treeview widgets.
        self.connected_clients_tree = connected_clients_widget
        self.transactions_tree = transactions_widget

    def refresh_all_clients_table(self, dict_of_all_clients, dict_of_active_clients):
        # Ensure dict_of_active_clients is a dictionary
        if not isinstance(dict_of_active_clients, dict):
            dict_of_active_clients = {}

        # Refreshes the connected clients table.

        # Clears the table
        for item in self.connected_clients_tree.get_children():
            self.connected_clients_tree.delete(item)

        # Define tags for coloring rows
        self.connected_clients_tree.tag_configure("accepted", background="#d4edda")  # Light green
        self.connected_clients_tree.tag_configure("blocked", background="#f8d7da")  # Light red

        # Inserts updated data
        for (ip, username), ddos_status in dict_of_all_clients.items():
            tag = "accepted" if ddos_status.lower() == "accepted" else "blocked"
            
            if any(ip == key[0] for key in dict_of_active_clients.keys()):
                # If the IP is in the active clients, set the connection status to "Active"
                connection_status = "Online"
            else:
                # If the IP is not in the active clients, set the connection status to "Offline"
                connection_status = "Offline"
                
            self.connected_clients_tree.insert("", "end", values=(ip, username, ddos_status, connection_status), tags=(tag,))
    
    def refresh_transactions_table(self):
        # Refreshes the transactions table.
        
        # Clear the existing rows
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)

        # Fetch updated transactions from the database
        updated_transactions = self.tls.get_all_rows("transactions")

        # Populate the table with updated transactions
        for transaction in updated_transactions:
            self.transactions_tree.insert("", "end", values=transaction)

    def refresh_stock_graphs(self, stock_prices_dict):
        # Updates stock graphs for each stock symbol.
        
        for stock_symbol, prices in stock_prices_dict.items():
            if stock_symbol in self.stock_graph_windows:
                # Retrieve the graph window, canvas, and axis for this stock symbol
                graph_window, canvas, ax = self.stock_graph_windows[stock_symbol]

                # Clear the current graph and redraw with the updated prices
                ax.clear()
                ax.plot(prices, marker='o', linestyle='-', color='blue')  # Draw the graph
                ax.set_title(f"Price Changes for {stock_symbol}")
                ax.set_xlabel("Transaction Recency")
                ax.set_ylabel("Price")
                ax.grid(True)

                # Refresh the canvas to display the updated graph
                canvas.draw()
    
    # Function to show the combined UI            
    def show_combined_ui(self, dict_of_all_clients, dict_of_active_clients, stocks, stock_prices_history):
        import ctypes # For changing the taskbar icon

        root = Tk("nExchange Dashboard")
        root.title("nExchange Dashboard")

        root.iconbitmap("C:\\Users\\ronya\\OneDrive\\Project\\FirstMVP\\nExchange_logo_icon.png")  # Sets the window icon

        # Force taskbar icon change
        icon_path = "C:\\Users\\ronya\\OneDrive\\Project\\FirstMVP\\nExchange_logo_icon.ico"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("my_custom_python_app")
        root.wm_iconbitmap(icon_path)

        photo = PhotoImage(file="C:\\Users\\ronya\\OneDrive\\Project\\FirstMVP\\nExchange_logo_icon.png")
        root.iconphoto(True, photo)

        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
        root.configure(bg="#f0f8ff")
        root.resizable(False, False)
        root.state("zoomed")

        self.configure_styles()

        # Function to initialize and show all UI components after the logo fades out
        def initialize_ui(container=None):
            # If no container is provided, use root
            target = container if container else root
            
            # Create the connected clients and transactions tables
            self.connected_clients_tree = self.show_all_clients_table(target, dict_of_all_clients, dict_of_active_clients)
            self.transactions_tree = self.show_transactions_table(target)

            # Initialize references
            self.initialize_ui_references(self.connected_clients_tree, self.transactions_tree)

            # Show the stock table
            self.show_stocks_table(target, stocks, stock_prices_history)

        # Show the logo and transition to the main UI
        self.show_logo_and_transition(root, initialize_ui)
        self.play_intro_sound()

        # Add a protocol handler to stop the server when the window is closed
        root.protocol("WM_DELETE_WINDOW", self.on_close_callback)

        root.mainloop()

        return self.transactions_tree, self.connected_clients_tree


# Example usage
if __name__ == "__main__":
    tls = DB_Tools()
    
    mydb = tls.init_with_db("stocktradingdb")

    dict_of_connected_people = {("192.168.1.1", 8080): "Alice", ("192.168.1.2", 9090): "Bob"}
    stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    stock_prices_history = {
        "AAPL": [150, 152, 149, 153, 155, 158, 160, 162, 165, 168],
        "GOOGL": [2800, 2810, 2820, 2830, 2840, 2850, 2860, 2875, 2885, 2890],
        "MSFT": [290, 292, 295, 298, 300, 302, 304, 306, 308, 310],
        "AMZN": [3400, 3410, 3425, 3430, 3440, 3450, 3460, 3470, 3485, 3490],
        "TSLA": [720, 725, 730, 735, 740, 745, 750, 755, 760, 765]
    }

    server_ui = ServerUI(lambda: None)
    server_ui.show_combined_ui(dict_of_connected_people, stocks, stock_prices_history)