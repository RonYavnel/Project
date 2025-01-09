import socket
import threading
from datetime import *
from server_constants import *
# my helper libraries
from server_lib import *
from db_tools import *


# When a user connects, its thread referred to deal_maker function
def deal_maker(mydb, conn):
    print("in deal_maker")
    username, password = handle_user_connection(mydb, conn) # Get username and password
    # print ("username is: ", username)
    # print("password is: ", password)
    balance = handle_user_balance(mydb, conn, username, password) # Check if the user exists
    # If not - creates it and asks for balance
    # If yes - takes the recent balance
    list_of_stocks = get_all_column_values(mydb, "stocks", "symbol") # Get the stocks from the database
    conn.send(str(list_of_stocks).encode()) # Send the client the list of stocks
    stock_symbol = conn.recv(1024).decode() # Recieve the stock symbol from the client
    share_price = get_current_share_price(mydb, stock_symbol) # Get the current share price
    conn.send(str(share_price).encode()) # Send the client the updated share price

    while True:
        order = conn.recv(1024).decode() # Recieve the order
        if not order: 
            # If the order is empty: update the last_seen time of the user 
            # and terminate the connection
            update_last_seen(mydb, username, password)
            conn.close()
            break

        try:
            # Try to split the order by the delimiter, format: (side$amount)
            delimiter = "$"
            param = order.split(delimiter)
            if len(param) < 2:
                conn.send("Error: not enough parameters provided.".encode())
                continue
            
            # Put the side and the amount to the right variables
            side, amount = param[0], int(param[1])
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
                    (username, get_client_id(mydb, username, password), "S", stock_symbol, share_price, amount, datetime.now())
                )
                # Adjust the share price according to the amount of shares that have been sold.
                adjustment = int((amount * share_price) * 0.01)
                share_price = max(1, share_price - adjustment)
                # Send confirmation to the client with his updated balance
                conn.send(f"Sale completed. Your updated balance: {balance}".encode())
            
            # If the side is "buy":
            elif side.upper() == "B":
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
                        (username, get_client_id(mydb, username, password), "B", stock_symbol, share_price, amount, datetime.now())
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
            else:
                # Error handling: invalid side parameter
                conn.send("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.".encode())
        except ValueError:
            conn.send("Error: Invalid data format.".encode())
        
        # If the transactions is completed successfully - update all user's and share's data
        update_all_data(mydb, conn, username, password, balance, side, amount, stock_symbol, share_price)

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
                 "(company_name VARCHAR(255), symbol VARCHAR(255), stock_id INT, shares_sold INT, num_of_shares INT, current_price INT, highest_price INT, lowest_price INT)")
    create_table(mydb, "transactions",
                 "(username VARCHAR(255), client_id VARCHAR(255), side CHAR, stock_symbol VARCHAR(255), share_price INT, amount INT, time_stamp TIMESTAMP)")
    create_table(mydb, "users",
                 "(username VARCHAR(255), password VARCHAR(255), client_id INT, ip VARCHAR(255), port INT, last_seen DATETIME, balance INT)")
    return mydb

if __name__ == '__main__':
    print("Server is running")
    mydb = initialize_database()
    print("Database is ready")
    run_server(mydb)
