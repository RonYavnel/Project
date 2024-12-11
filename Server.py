import socket
import threading
from time import sleep
import mysql.connector
from DB_Helper import *
from datetime import *

share_price = 220
lock = threading.Lock()

DB_CONN = init_with_db("StockTradingDB")

def deal_maker(conn, share_price):
    username = conn.recv(1024).decode()
    user_id = conn.recv(1024).decode()
    conn.send(str(share_price).encode())
    balance = int(conn.recv(1024).decode())
    if is_username_exists(DB_CONN, username):
       update_last_seen(DB_CONN, username)
    else: 
        insert_row(
            DB_CONN, 
            "users", 
            "(Username, IP, PORT, Last_seen, Balance)", 
            "(%s, %s, %s, %s, %s)",
            (username, conn.getpeername()[0], conn.getpeername()[1], str(datetime.now()), balance)
        )
    while True:
        order = conn.recv(1024).decode()
        if not order:
            update_last_seen(DB_CONN, username)
            conn.close()
            break

        try:
            delimiter = "$"
            param = order.split(delimiter)
            if len(param) < 2:
                conn.send("Error: not enough parameters provided.".encode())
                continue
            
            side, amount = param[0], int(param[1])
            deal = share_price * amount

            if side.upper() == "S":
                balance += deal
                insert_row(
                    DB_CONN,
                    "transactions",
                    "(username, userID, side, stock_symbol, share_price, amount, time_stamp)", 
                    "(%s, %s, %s, %s, %s, %s, %s)",
                    (username, user_id, "S", "AAPL", share_price, amount, datetime.now())
                )
                adjustment = int((amount * share_price) * 0.01)
                share_price = max(1, share_price - adjustment)
                update_balance(DB_CONN, username, balance)
                conn.send(f"Sale completed. New balance: {balance}".encode())
            elif side.upper() == "B":
                if balance >= deal:
                    balance -= deal
                    insert_row(
                    DB_CONN,
                    "transactions",
                    "(username, userID, side, stock_symbol, share_price, amount, time_stamp)", 
                    "(%s, %s, %s, %s, %s, %s, %s)",
                    (username, user_id, "B", "AAPL", share_price, amount, datetime.now())
                    )                    
                    adjustment = int((amount * share_price) * 0.01)
                    share_price += adjustment
                    update_balance(DB_CONN, username, balance)
                    conn.send(f"Purchase successful. New balance: {balance}".encode())
                elif balance < deal:
                    conn.send(f"Error: Insufficient balance for this purchase. Your balance is: {balance}".encode())
                else:
                    conn.send("Error: Not enough shares available.".encode())
            else:
                conn.send("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.".encode())
        except ValueError:
            conn.send("Error: Invalid data format.".encode())

        conn.send(str(share_price).encode())

HOST = socket.gethostname()
PORT = 5000

server_socket = socket.socket()
server_socket.bind((HOST, PORT))
server_socket.listen(10)

while True:
    conn, address = server_socket.accept()
    client_thread = threading.Thread(target=deal_maker, args=(conn, share_price))
    client_thread.start()
