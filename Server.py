import socket
import threading
from datetime import *
from server_constants import *
# my helper libraries
from server_lib import *
from db_tools import *

stock_symbol = 'AAPL'
share_price = get_current_share_price(DB_CONN, stock_symbol)
num_of_shares = 50000


# When a user connects, its thread referred to deal_maker function
def deal_maker(conn, share_price):
    print("in deal_maker")
    username = conn.recv(6).decode() # Get username
    print ("username is: ", username)
    password = conn.recv(6).decode() # Get his password
    print("password is: ", password)
    conn.send(str(get_current_share_price(DB_CONN, stock_symbol)).encode()) # Send the client the updated share price
    balance = user_handling_and_balance(conn, username, password) # Check if the user exists
    print(f"User's balance is {balance}.")
    # If not - creates it and asks for balance
    # If yes - takes the recent balance
    while True:
        order = conn.recv(1024).decode() # Recieve the order
        if not order: 
            # If the order is empty: update the last_seen time of the user 
            # and terminate the connection
            update_last_seen(DB_CONN, username, password)
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
                    DB_CONN,
                    "transactions",
                    "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                    "(%s, %s, %s, %s, %s, %s, %s)",
                    (username, get_client_id(DB_CONN, username, password), "S", stock_symbol, share_price, amount, datetime.now())
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
                        DB_CONN,
                        "transactions",
                        "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                        "(%s, %s, %s, %s, %s, %s, %s)",
                        (username, get_client_id(DB_CONN, username, password), "B", stock_symbol, share_price, amount, datetime.now())
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
        update_all_data(conn, username, password, balance, side, amount, stock_symbol, share_price)

def init_server():
    # Initiate a socket
    server_socket = socket.socket()
    server_socket.bind((HOST, PORT))
    
    # Wait for connections from clients
    server_socket.listen(10)
    return server_socket

def run_server():

    server_socket = init_server()
    while True:
        # For each connection: accept, and send it to thread
        conn, address = server_socket.accept()
        print("before thread")
        client_thread = threading.Thread(target=deal_maker, args=(conn, share_price))
        client_thread.start()
    

if __name__ == '__main__':
    run_server()
