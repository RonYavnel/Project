from tkinter import *
from tkinter import ttk
from db_tools import *
from PIL import Image, ImageTk

# Define colors for better aesthetics
BG_COLOR = "#f0f8ff"  # Light blue background
HEADER_BG = "#4682b4"  # Steel blue for headers
HEADER_FG = "#ffffff"  # White text for headers
FONT = ("Helvetica", 12)

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
    logo_frame = Frame(root, bg=BG_COLOR)
    logo_frame.pack(fill="both", expand=True)

    # Load the image with transparency enabled
    original_image = Image.open("nExchange_logo.png").convert("RGBA")  # Enable alpha channel
    logo_image = original_image.copy()  # Copy the original image

    # Display the image in a label
    tk_image = ImageTk.PhotoImage(logo_image)
    logo_label = Label(logo_frame, image=tk_image, bg=BG_COLOR)
    logo_label.image = tk_image  # Keep reference to avoid garbage collection
    logo_label.pack(expand=True)

    # Start fading out the logo after 3 seconds
    root.after(2000, lambda: fade_out_logo(logo_image, logo_label, logo_frame, next_screen_callback))


def show_transactions(root, mydb):
    transactions_label = Label(root, text="Transactions", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
    transactions_label.pack(anchor="n", pady=10)

    # Create a top frame for the Treeview with limited width
    top_frame = Frame(root, width=1250, height=200, bg=BG_COLOR)
    top_frame.pack_propagate(False)
    top_frame.place(x=15, rely=0.07)

    # Create the Treeview widget with smaller height
    columns = ("Username", "Client ID", "Side", "Stock Symbol", "Share Price", "Amount", "Time Stamp")
    tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=5)

    # Define column headings and set fixed, smaller column widths
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    # Fetch transactions and add data to the table
    list_of_transactions = get_all_rows(mydb, "transactions")
    for transaction in list_of_transactions:
        tree.insert("", "end", values=transaction)
        tree.see(tree.get_children()[-1])

    # Create a vertical scrollbar for the Treeview
    scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Place the Treeview and Scrollbar in the top frame
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)


def show_connected_people(root, dict_of_connected_people):
    top_frame = Frame(root, width=600, height=300, bg=BG_COLOR)
    top_frame.pack_propagate(False)
    top_frame.place(relx=0.26, rely=0.41, anchor="n")

    connected_people_label = Label(root, text="Connected People", font=("Helvetica", 18, "bold"), bg=BG_COLOR)
    connected_people_label.place(relx=0.34, rely=0.36, anchor="ne")

    # Create the Treeview widget with smaller height
    columns = ("IP Address", "Port", "Username")
    tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=5)

    # Define column headings and set fixed, smaller column widths
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    # Add data to the table
    for ip_and_port, username in dict_of_connected_people.items():
        ip, port = ip_and_port
        tree.insert("", "end", values=(ip, port, username))

    # Create a vertical scrollbar for the Treeview
    scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Place the Treeview and Scrollbar in the top frame
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)


def show_combined_ui(mydb, dict_of_connected_people):
    root = Tk()
    root.geometry("1200x800")
    root.configure(bg=BG_COLOR)

    configure_styles()

    show_logo_and_transition(root, lambda: (show_transactions(root, mydb), show_connected_people(root, dict_of_connected_people)))

    root.mainloop()


mydb = init_with_db("stocktradingdb")
dict_of_connected_people = {("192.168.1.1", 8080): "Alice", ("192.168.1.2", 9090): "Bob"}
show_combined_ui(mydb, dict_of_connected_people)
