import socket
import threading
from datetime import *
from server_constants import *
from server_lib import *
from db_tools import *
from server_UI import *
from encryption_lib import *

list_of_connections = {}  # (ip, port): username
stock_prices_history = {}  # stock_symbol: [list of stock prices]

def update_stock_prices_history():
    for stock in get_all_column_values(mydb, "stocks", "symbol"):
        stock_prices_history[stock] = [get_current_share_price(mydb, stock)] # Initialize the stock prices history with the current share price

# Mutex initialization
mutex = threading.Lock()

# When a user connects, its thread referred to deal_maker function
def deal_maker(mydb, conn):
    try:
        # Load the correct keys
        server_private_key = load_server_private_key()  # Used to decrypt client messages
        client_public_key = load_client_public_key()    # Used to encrypt messages for the client

        print("in deal_maker")

        # Authenticate user and get username + hashed password
        username, hashed_password = handle_user_connection(mydb, conn, server_private_key, client_public_key)
        print("username is: ", username)
        print("hashed_password is: ", hashed_password)

        list_of_connections[conn.getpeername()] = username  # Add the connection to the list of connections
        print(list_of_connections)

        with mutex:
            # Refresh the connected clients table
            connected_clients_list = [(ip, port, user) for (ip, port), user in list_of_connections.items()]  
            refresh_connected_clients(connected_clients_list)

        # Handle balance
        balance = handle_user_balance(mydb, conn, username, hashed_password, server_private_key, client_public_key)

        # Get available stocks and send the list to the client
        list_of_stocks = get_all_column_values(mydb, "stocks", "symbol")  
        conn.send(encrypt_data(str(list_of_stocks), client_public_key))  

        # Receive stock symbol from client
        stock_symbol = decrypt_data(conn.recv(4096), server_private_key).upper()  
        share_price = get_current_share_price(mydb, stock_symbol)  

        # Send the client the updated share price
        conn.send(encrypt_data(str(share_price), client_public_key))  

        with mutex:
            # Initialize stock history if not already present
            if stock_symbol not in stock_prices_history:
                stock_prices_history[stock_symbol] = []

        while True:
            print("Waiting for order")

            # Receive order from client
            order = decrypt_data(conn.recv(4096), server_private_key)

            # Error handling: empty order
            if not order:
                conn.send(encrypt_data("Error: the order input is empty", client_public_key))
                continue

            print("Order is:", order)

            with mutex:
                try:
                    delimiter = "$"
                    param = order.split(delimiter)

                    # Validate format: delimiter and numeric amount check
                    if len(param) != 2:
                        conn.send(encrypt_data("Error: Incorrect format. Use 'side$amount' format.", client_public_key))
                        continue
                    
                    if not param[1].isdigit():
                        conn.send(encrypt_data("Error: Amount must be a numeric value.", client_public_key))
                        continue

                    side, amount = param[0].upper(), int(param[1])

                    # Validate the "side" parameter
                    if side.upper() not in ["B", "S"]:
                        conn.send(encrypt_data("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.", client_public_key))
                        continue

                    # If all validations pass, send confirmation to the client
                    conn.send(encrypt_data("Order recieved", client_public_key))

                    # Calculate the whole deal cost
                    deal = share_price * amount

                    # Handle the order
                    if side.upper() == "S":  # Selling
                        balance += deal  # Add the deal cost to the balance of the client

                        # Document transaction in the Transactions table
                        insert_row(
                            mydb,
                            "transactions",
                            "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                            "(%s, %s, %s, %s, %s, %s, %s)",
                            (username, get_client_id(mydb, username, hashed_password), "S", stock_symbol, share_price, amount, datetime.now())
                        )

                        # Adjust the share price based on selling activity
                        adjustment = int((amount * share_price) * 0.01)
                        share_price = max(1, share_price - adjustment)

                        # Send confirmation to the client
                        conn.send(encrypt_data(f"Sale completed. Your updated balance: {balance}", client_public_key))

                    else:  # Buying
                        if balance >= deal:  # Check if client has enough funds
                            balance -= deal  # Deduct the cost

                            # Document transaction in the Transactions table
                            insert_row(
                                mydb,
                                "transactions",
                                "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                "(%s, %s, %s, %s, %s, %s, %s)",
                                (username, get_client_id(mydb, username, hashed_password), "B", stock_symbol, share_price, amount, datetime.now())
                            )        

                            # Adjust the share price based on buying activity
                            adjustment = int((amount * share_price) * 0.01)
                            share_price += adjustment

                            # Send confirmation to the client
                            conn.send(encrypt_data(f"Purchase successful. New balance: {balance}", client_public_key))

                        else:
                            conn.send(encrypt_data(f"Error: Insufficient balance for this purchase. Your balance is: {balance}", client_public_key))

                    # Update the stock price history
                    stock_prices_history[stock_symbol].append(share_price)

                    # Maintain only the last 10 prices
                    if len(stock_prices_history[stock_symbol]) > 10:
                        stock_prices_history[stock_symbol].pop(0)

                    print(stock_prices_history)

                    refresh_transactions_table(mydb)
                    refresh_stock_graphs({stock_symbol: stock_prices_history[stock_symbol]})

                except ValueError:
                    conn.send(encrypt_data("Error: Invalid data format.", client_public_key))

            # Update all necessary data
            update_all_data(mydb, conn, username, hashed_password, balance, side, amount, stock_symbol, share_price, client_public_key)

    except ConnectionResetError:
        print(f"Connection with {conn} was forcibly aborted")

    finally:
        # Remove connection from list
        list_of_connections.pop(conn.getpeername())  
        connected_clients_list = [(ip, port, user) for (ip, port), user in list_of_connections.items()]  
        refresh_connected_clients(connected_clients_list)  

        print(list_of_connections)
        conn.close()
        print(f"Connection with {conn} closed")



# Server and UI initialization
def init_server():
    # Initiate a socket
    server_socket = socket.socket()
    server_socket.bind((HOST, PORT))
    
    # Wait for connections from clients
    server_socket.listen(10)
    return server_socket

def run_server(mydb):
    server_socket = init_server()
    while True:
        # For each connection: accept, and send it to thread
        conn = server_socket.accept()[0]
        client_thread = threading.Thread(target=deal_maker, args=(mydb, conn))
        client_thread.start()


def initialize_database():
    # Initiate the connection with the sql server
    my_sql_server = init()
    # Create a new database and connect to it
    create_new_database(my_sql_server, "stocktradingdb")
    mydb = init_with_db("stocktradingdb")
    # Create the tables in the database
    create_table(mydb, "stocks",
                 "(company_name VARCHAR(255), symbol VARCHAR(255), stock_id INT NOT NULL PRIMARY KEY auto_increment, shares_sold INT, num_of_shares INT, current_price INT, highest_price INT, lowest_price INT)")
    create_table(mydb, "transactions",
                 "(username VARCHAR(255), client_id VARCHAR(255), side CHAR, stock_symbol VARCHAR(255), share_price INT, amount INT, time_stamp TIMESTAMP)")
    create_table(mydb, "users",
                 "(username VARCHAR(255), hashed_password VARCHAR(255), client_id INT NOT NULL PRIMARY KEY auto_increment, ip VARCHAR(255), port INT, last_seen DATETIME, balance INT)")
    return mydb

if __name__ == '__main__':
    print("Server is running")
    mydb = initialize_database()
    print("Database is ready")

    update_stock_prices_history()
    print("Stock prices history is updated")

    # Retrieve the UI components (Treeviews) from the UI thread
    def start_ui():
        global transactions_tree, connected_clients_tree
        transactions_tree, connected_clients_tree = show_combined_ui(mydb, list_of_connections, get_all_column_values(mydb, "stocks", "symbol"), stock_prices_history)

    # Start the UI in a separate thread
    ui_thread = threading.Thread(target=start_ui, daemon=True)
    ui_thread.start()

    # Run the server in the main thread
    run_server(mydb)