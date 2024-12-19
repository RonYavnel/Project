import socket
import threading
from time import sleep
import mysql.connector
from DB_Helper import *
from datetime import *
from server_constants import *

stock_symbol = 'AAPL'
share_price = get_current_share_price(DB_CONN, stock_symbol)
num_of_shares = 50000

# Function that handles a new connection
# If user exists - update his ip, port and last_seen
# If not exists - get balance from him and insert his details
# Eventually, returns the balance of the client
def user_handling_and_balance(conn, username, password):
    if is_username_exists(DB_CONN, username, password):
        conn.send("1".encode()) # Sends confirmation to the client
        balance = get_user_balance(DB_CONN, username, password) # Gets clients balance
        update_ip_and_port(DB_CONN, conn, username, password) # Updates ip and port
        update_last_seen(DB_CONN, username, password) # Updates last_seen
        conn.send(str(balance).encode()) # Sends the cliet his balance
    else:
        conn.send("0".encode()) # Sends confirmation to the client
        balance = int(conn.recv(1024).decode()) # Gets from the client his balance
        insert_row(    # Inserts the details of the new client to the database
            DB_CONN, 
            "users", 
            "(username, password, ip, port, last_seen, balance)", 
            "(%s, %s, %s, %s, %s, %s)",
            (username, password, conn.getpeername()[0], conn.getpeername()[1], str(datetime.now()), balance)
        )
    return balance # Returns the balance of the client

# Funtion that update all the data about the client and the share after transaction
def update_all_data(conn, username, password, balance, side, amount, stock_symbol, share_price):
    update_last_seen(DB_CONN, username, password) # Updates last_seen time of the client
    update_balance(DB_CONN, username, password, balance) # Updates client's balance
    if side.upper() == "S":
        update_num_of_shares(DB_CONN, stock_symbol, amount) # If shares are sold - add those shares to the num of free shares
    else:
        update_num_of_shares(DB_CONN, stock_symbol, -amount) # If shares are bought - subtract this amount from the num of free shares
        update_shares_sold(DB_CONN, stock_symbol, amount) # Add the new amount of sold shares to database
    update_current_price(DB_CONN, stock_symbol, share_price) # Update the current price of a share after transaction
    if share_price > get_highest_share_price(DB_CONN, stock_symbol): # Update the highest_share_price if needed
        update_highest_price(DB_CONN, stock_symbol, share_price)
    if share_price < get_lowest_share_price(DB_CONN, stock_symbol):  # Update the lowest_share_price if needed
        update_lowest_price(DB_CONN, stock_symbol, share_price)
    conn.send(str(share_price).encode()) # Send the updated share price to the client


# When a user connects, its thread referred to deal_maker function
def deal_maker(conn, share_price):
    username = conn.recv(1024).decode() # Get username
    password = conn.recv(1024).decode() # Get his password
    conn.send(str(get_current_share_price(DB_CONN, stock_symbol)).encode()) # Send the client the updated share price
    balance = user_handling_and_balance(conn, username, password) # Check if the user exists
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


def run_server():
    
    # Initiate a socket
    server_socket = socket.socket()
    server_socket.bind((HOST, PORT))
    
    # Wait for connections from clients
    server_socket.listen(10)

    while True:
        # For each connection: accept, and send it to thread
        conn, address = server_socket.accept()
        client_thread = threading.Thread(target=deal_maker, args=(conn, share_price))
        client_thread.start()
    

if __name__ == '__main__':
    run_server()
