from tkinter import *
from tkinter import ttk
from db_tools import *

def show_transactions(mydb):
    # Create the main window
    root = Tk()
    root.geometry("800x600")  # Set a smaller window size for demonstration

    transactions_label = Label(root, text="Transactions", font=("Arial", 16))
    transactions_label.pack(anchor="n", pady=10)  # Center the label at the top with padding
    
    # Create a top frame for the Treeview with limited width
    top_frame = Frame(root, width=900, height=200)  # Limit frame size
    top_frame.pack_propagate(False)  # Prevent auto-expansion
    top_frame.place(x=20, y=40)  # Place in the top-left corner

    # Create the Treeview widget with smaller height
    columns = ("Username", "Client ID", "Side", "Stock Symbol", "Share Price", "Amount", "Time Stamp")
    tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=5)  # Reduced height

    # Define column headings and set fixed, smaller column widths
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")  # Shrink column width for compactness

    # Fetch transactions and add data to the table
    list_of_transactions = get_all_rows(mydb, "transactions")
    for transaction in list_of_transactions:
        tree.insert("", "end", values=transaction)

    # Create a vertical scrollbar for the Treeview
    scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Place the Treeview and Scrollbar in the top frame
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    # Run the Tkinter event loop
    root.mainloop()
