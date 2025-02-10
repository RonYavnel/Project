from tkinter import *
from tkinter import ttk
from db_tools import *
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Define colors for better aesthetics
BG_COLOR = "#f0f8ff"  # Light blue background
HEADER_BG = "#4682b4"  # Steel blue for headers
HEADER_FG = "#ffffff"  # White text for headers
FONT = ("Helvetica", 12)

stock_graph_windows = {}  # To store graph windows for each stock


def configure_styles():
    # Define custom styles using ttk.Style
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


def refresh_stock_graphs(stock_prices_dict):
    """
    Updates stock graphs for each stock symbol.
    :param stock_prices_dict: Dictionary in the format {stock_symbol: [list of stock prices]}.
    """
    global stock_graph_windows

    for stock_symbol, prices in stock_prices_dict.items():
        if stock_symbol in stock_graph_windows:
            # Retrieve the graph window, canvas, and axis for this stock symbol
            graph_window, canvas, ax = stock_graph_windows[stock_symbol]

            # Clear the current graph and redraw with the updated prices
            ax.clear()
            ax.plot(prices, marker='o', linestyle='-', color='blue')  # Draw the graph
            ax.set_title(f"Price Changes for {stock_symbol}")
            ax.set_xlabel("Transaction Recency")
            ax.set_ylabel("Price")
            ax.grid(True)

            # Refresh the canvas to display the updated graph
            canvas.draw()



def show_stock_graph(stock_name, prices):
    # Function to handle the closing of the graph window
    def on_close():
        if stock_name in stock_graph_windows:
            stock_graph_windows[stock_name][0].destroy()  # Destroy the window properly
            del stock_graph_windows[stock_name]  # Remove the window reference

    # Check if the stock already has a valid graph window
    if stock_name in stock_graph_windows and stock_graph_windows[stock_name][0].winfo_exists():
        graph_window, canvas, ax = stock_graph_windows[stock_name]
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
        stock_graph_windows[stock_name] = (graph_window, canvas, ax)

    # Update the graph using refresh_stock_graphs
    refresh_stock_graphs({stock_name: prices})

    # Bring the window to the front
    graph_window.deiconify()
    graph_window.lift()


def show_stock_table(root, stocks, stock_prices_history):
    stock_frame = Frame(root, width=600, height=300, bg=BG_COLOR)
    stock_frame.pack_propagate(False)
    stock_frame.place(relx=0.74, rely=0.41, anchor="n")

    stock_label = Label(root, text="Stocks", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
    stock_label.place(relx=0.765, rely=0.36, anchor="ne")

    columns = ("Stock Name",)
    stock_tree = ttk.Treeview(stock_frame, columns=columns, show="headings", height=5)
    stock_tree.heading("Stock Name", text="Stock Name")
    stock_tree.column("Stock Name", width=180, anchor="center")

    for stock_name in stocks:
        stock_tree.insert("", "end", values=(stock_name,))

    def on_stock_select(event):
        selected_item = stock_tree.selection()[0]
        stock_name = stock_tree.item(selected_item, "values")[0]
        prices = stock_prices_history.get(stock_name, [100] * 10)  # Default to 10 prices if not available
        show_stock_graph(stock_name, prices)

    stock_tree.bind("<Double-1>", on_stock_select)

    scrollbar = ttk.Scrollbar(stock_frame, orient="vertical", command=stock_tree.yview)
    stock_tree.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    stock_tree.pack(side="left", fill="both", expand=True)


def show_transactions(root, mydb):
    transactions_label = Label(root, text="Transactions", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
    transactions_label.pack(anchor="n", pady=10)

    top_frame = Frame(root, width=1250, height=200, bg=BG_COLOR)
    top_frame.pack_propagate(False)
    top_frame.place(x=15, rely=0.07)

    columns = ("Username", "Client ID", "Side", "Stock Symbol", "Share Price", "Amount", "Time Stamp")
    tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=5)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    # Fetch transactions and add data to the table
    list_of_transactions = get_all_rows(mydb, "transactions")
    for transaction in list_of_transactions:
        tree.insert("", "end", values=transaction)
        tree.see(tree.get_children()[-1])

    scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    return tree


def show_connected_people(root, dict_of_connected_people):
    top_frame = Frame(root, width=600, height=300, bg=BG_COLOR)
    top_frame.pack_propagate(False)
    top_frame.place(relx=0.26, rely=0.41, anchor="n")

    connected_people_label = Label(root, text="Connected People", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
    connected_people_label.place(relx=0.34, rely=0.36, anchor="ne")

    columns = ("IP Address", "Port", "Username")
    tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=5)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    for ip_and_port, username in dict_of_connected_people.items():
        ip, port = ip_and_port
        tree.insert("", "end", values=(ip, port, username))

    scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    return tree


def fade_out_logo(logo_image, logo_label, logo_frame, next_screen_callback):
    alpha = 255  # Start fully opaque

    def step_fade():
        nonlocal alpha
        alpha -= 10  # Gradually decrease opacity
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


def show_logo_and_transition(root, next_screen_callback):
    # Create a frame for the full-screen logo display
    logo_frame = Frame(root, bg="#f0f8ff")
    logo_frame.pack(fill="both", expand=True)

    # Load and resize the image
    original_image = Image.open("nExchange_logo.png").convert("RGBA")
    resized_image = original_image.resize((768, 503), Image.Resampling.LANCZOS)  # Resize with high-quality resampling
    logo_image = resized_image.copy()


    # Create a copy of the resized image to preserve transparency
    logo_image = resized_image.copy()

    # Display the image in a label
    tk_image = ImageTk.PhotoImage(logo_image)
    logo_label = Label(logo_frame, image=tk_image, bg="#f0f8ff")
    logo_label.image = tk_image  # Keep reference to avoid garbage collection
    logo_label.pack(expand=True)

    # Start fading out the logo after 3 seconds
    root.after(2000, lambda: fade_out_logo(logo_image, logo_label, logo_frame, next_screen_callback))



# Global references to Treeview widgets and stock graph windows
connected_clients_tree = None
transactions_tree = None
stock_graph_windows = {}  # {stock_symbol: (graph_window, canvas, ax)}


def initialize_ui_references(connected_clients_widget, transactions_widget):
    """
    Initializes the global references to the Treeview widgets.
    """
    global connected_clients_tree, transactions_tree
    connected_clients_tree = connected_clients_widget
    transactions_tree = transactions_widget


def refresh_connected_clients(connected_clients_list):
    """
    Refreshes the connected clients table.
    :param connected_clients_list: List of connected clients in the format [(IP, Port, Username), ...].
    """
    global connected_clients_tree
    # Clear the table
    for item in connected_clients_tree.get_children():
        connected_clients_tree.delete(item)

    # Insert updated data
    for ip, port, username in connected_clients_list:
        connected_clients_tree.insert("", "end", values=(ip, port, username))


def refresh_transactions_table(mydb):
    """
    Refreshes the transactions table.
    :param mydb: Database connection to fetch the updated transactions.
    """
    global transactions_tree
    from db_tools import get_all_rows  # Importing here to prevent circular imports

    # Clear the existing rows
    for item in transactions_tree.get_children():
        transactions_tree.delete(item)

    # Fetch updated transactions from the database
    updated_transactions = get_all_rows(mydb, "transactions")

    # Populate the table with updated transactions
    for transaction in updated_transactions:
        transactions_tree.insert("", "end", values=transaction)


def show_combined_ui(mydb, dict_of_connected_people, stocks, stock_prices_history):
    
    global connected_clients_tree, transactions_tree

    root = Tk("nExchange Dashboard") 
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
    root.configure(bg="#f0f8ff")
    root.resizable(False, False)
    root.state("zoomed")
    
    configure_styles()

    # Function to initialize and show all UI components after the logo fades out
    def initialize_ui():
        # Create the connected clients and transactions tables
        connected_clients_tree = show_connected_people(root, dict_of_connected_people)
        transactions_tree = show_transactions(root, mydb)

        # Initialize references
        initialize_ui_references(connected_clients_tree, transactions_tree)

        # Show the stock table
        show_stock_table(root, stocks, stock_prices_history)

    # Show the logo and transition to the main UI
    show_logo_and_transition(root, initialize_ui)

    root.mainloop()

    return transactions_tree, connected_clients_tree


# Example inputs
mydb = init_with_db("stocktradingdb")

dict_of_connected_people = {("192.168.1.1", 8080): "Alice", ("192.168.1.2", 9090): "Bob"}
stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
stock_prices_history = {
    "AAPL": [150, 152, 149, 153, 155, 158, 160, 162, 165, 168],
    "GOOGL": [2800, 2810, 2820, 2830, 2840, 2850, 2860, 2875, 2885, 2890],
    "MSFT": [290, 292, 295, 298, 300, 302, 304, 306, 308, 310],
    "AMZN": [3400, 3410, 3425, 3430, 3440, 3450, 3460, 3470, 3485, 3490],
    "TSLA": [720, 725, 730, 735, 740, 745, 750, 755, 760, 765]
}

show_combined_ui(mydb, dict_of_connected_people, stocks, stock_prices_history)