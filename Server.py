import socket
import threading
from datetime import *
from server_constants import *
# my helper libraries
from server_lib import *
from db_tools import *
from server_UI import *

list_of_connections = {} # (ip, port): username
stock_prices_history = {} # stock_symbol: [list of stock prices]

def update_stock_prices_history():
    for stock in get_all_column_values(mydb, "stocks", "symbol"):
        stock_prices_history[stock] = [get_current_share_price(mydb, stock)] # Initialize the stock prices history with the current share price


# Mutex initialization
mutex = threading.Lock()

# When a user connects, its thread referred to deal_maker function
def deal_maker(mydb, conn):
    try:
        print("in deal_maker")
        username, hashed_password = handle_user_connection(mydb, conn) # Get username and hashed password
        print("username is: ", username)
        print("hashed_password is: ", hashed_password)
        list_of_connections[conn.getpeername()] = username # Add the connection to the list of connections
        print(list_of_connections)
        
        with mutex:
            # Refresh the connected clients table
            connected_clients_list = [(ip, port, user) for (ip, port), user in list_of_connections.items()] # list of tuples (ip, port, username)
            refresh_connected_clients(connected_clients_list)
        
        balance = handle_user_balance(mydb, conn, username, hashed_password) # Check if the user exists
        # If not - creates it and asks for balance
        # If yes - takes the recent balance
        list_of_stocks = get_all_column_values(mydb, "stocks", "symbol") # Get the stocks from the database
        conn.send(str(list_of_stocks).encode()) # Send the client the list of stocks
        stock_symbol = conn.recv(1024).decode().upper() # Recieve the stock symbol from the client
        share_price = get_current_share_price(mydb, stock_symbol) # Get the current share price
        conn.send(str(share_price).encode()) # Send the client the updated share price

        with mutex:
            # Initialize stock history if not already present
            if stock_symbol not in stock_prices_history:
                stock_prices_history[stock_symbol] = []
            
        while True:
            print("Waiting for order")
            order = conn.recv(1024).decode() # Recieve the order from the client

            # Error handling: empty order
            if not order:
                conn.send("Error: the order input is empty".encode())
                continue

            print("Order is:", order)

            with mutex:
                try:
                    delimiter = "$"
                    param = order.split(delimiter)

                    # Validate format: delimiter and numeric amount check
                    # If the order is not in the format 'side$amount' - send error and ask for order again
                    if len(param) != 2:
                        conn.send("Error: Incorrect format. Use 'side$amount format.".encode())
                        continue
                    
                    # If the amount is not a numeric value - send error and ask for order again
                    if not param[1].isdigit():
                        conn.send("Error: Amount must be a numeric value.".encode())
                        continue

                    side, amount = param[0].upper(), int(param[1])

                    # Validate the "side" parameter
                    if side.upper() not in ["B", "S"]:
                        conn.send("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.".encode())
                        continue

                    # If all validations pass
                    conn.send("Order recieved".encode())

                    # Calculate the whole deal cost
                    deal = share_price * amount
                    
                    # Handle the order
                    
                    # If the side is "sell":
                    if side.upper() == "S":
                        # Add the deal cost to the balance of the client
                        balance += deal
                        # Document the transaction in the Transactions table
                        insert_row(
                            mydb,
                            "transactions",
                            "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                            "(%s, %s, %s, %s, %s, %s, %s)",
                            (username, get_client_id(mydb, username, hashed_password), "S", stock_symbol, share_price, amount, datetime.now())
                        )
                        # Adjust the share price according to the amount of shares that have been sold.
                        adjustment = int((amount * share_price) * 0.01)
                        share_price = max(1, share_price - adjustment)
                        # Send confirmation to the client with his updated balance
                        conn.send(f"Sale completed. Your updated balance: {balance}".encode())
                    
                    # If the side is "buy":
                    else:
                        # Check the deal cost is less than user's balance,
                        # if not - send error and ask for order again
                        if balance >= deal:
                            # Subtract the deal cost from the user's balance
                            balance -= deal
                            # Document the transaction in the Transactions table
                            insert_row(
                                mydb,
                                "transactions",
                                "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                "(%s, %s, %s, %s, %s, %s, %s)",
                                (username, get_client_id(mydb, username, hashed_password), "B", stock_symbol, share_price, amount, datetime.now())
                            )        
                            # Adjust the share price according to the amount of shares that have been bought.            
                            adjustment = int((amount * share_price) * 0.01)
                            share_price += adjustment
                            # Send confirmation to the client with his updated balance
                            conn.send(f"Purchase successful. New balance: {balance}".encode())
                        elif balance < deal:
                            # Error handling: insufficient balance for order
                            conn.send(f"Error: Insufficient balance for this purchase. Your balance is: {balance}".encode())
                        else:
                            # Error handling: amount of shares bigger than the number of available shares.
                            conn.send("Error: Not enough shares available.".encode())
                    
                    # Update the stock price history
                    stock_prices_history[stock_symbol].append(share_price)
                    
                    # Maintain only the last 10 prices
                    if len(stock_prices_history[stock_symbol]) > 10:
                        stock_prices_history[stock_symbol].pop(0)
                        
                    print(stock_prices_history)
                    
                    refresh_transactions_table(mydb)
                    refresh_stock_graphs({stock_symbol: stock_prices_history[stock_symbol]})

                except ValueError:
                    conn.send("Error: Invalid data format.".encode())
            update_all_data(mydb, conn, username, hashed_password, balance, side, amount, stock_symbol, share_price)

    except ConnectionResetError as e:
        # Error handling: connection forcibly aborted by the client (process killed)
        print(f"Connection with {conn} was forcibly aborted")
    finally:
        list_of_connections.pop(conn.getpeername()) # Remove the connection from the list of connections
        connected_clients_list = [(ip, port, user) for (ip, port), user in list_of_connections.items()] # refresh the connected clients list after removing the connection
        refresh_connected_clients(connected_clients_list) # Refresh the connected clients table
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
