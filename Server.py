import socket
import threading
from time import sleep
import mysql.connector
from DB_Helper import *
from datetime import *

lock = threading.Lock()
stock_symbol = 'AAPL'
DB_CONN = init_with_db("StockTradingDB")
share_price = get_current_share_price(DB_CONN, stock_symbol)
num_of_shares = 50000

def deal_maker(conn, share_price):
    username = conn.recv(1024).decode()
    password = conn.recv(1024).decode()
    conn.send(str(get_current_share_price(DB_CONN, stock_symbol)).encode())
    if is_username_exists(DB_CONN, username, password):
        conn.send("1".encode())
        balance = get_user_balance(DB_CONN, username, password)
        update_ip_and_port(DB_CONN, conn, username, password)
        update_last_seen(DB_CONN, username, password)
        conn.send(str(balance).encode())
    else:
        conn.send("0".encode()) 
        balance = int(conn.recv(1024).decode())
        insert_row(
            DB_CONN, 
            "users", 
            "(username, password, ip, port, last_seen, balance)", 
            "(%s, %s, %s, %s, %s, %s)",
            (username, password, conn.getpeername()[0], conn.getpeername()[1], str(datetime.now()), balance)
        )
    while True:
        order = conn.recv(1024).decode()
        if not order:
            update_last_seen(DB_CONN, username, password)
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
                    "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                    "(%s, %s, %s, %s, %s, %s, %s)",
                    (username, get_client_id(DB_CONN, username, password), "S", stock_symbol, share_price, amount, datetime.now())
                )
                adjustment = int((amount * share_price) * 0.01)
                share_price = max(1, share_price - adjustment)
                conn.send(f"Sale completed. New balance: {balance}".encode())
            elif side.upper() == "B":
                if balance >= deal:
                    balance -= deal
                    insert_row(
                        DB_CONN,
                        "transactions",
                        "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                        "(%s, %s, %s, %s, %s, %s, %s)",
                        (username, get_client_id(DB_CONN, username, password), "B", stock_symbol, share_price, amount, datetime.now())
                    )                    
                    adjustment = int((amount * share_price) * 0.01)
                    share_price += adjustment
                    conn.send(f"Purchase successful. New balance: {balance}".encode())
                elif balance < deal:
                    conn.send(f"Error: Insufficient balance for this purchase. Your balance is: {balance}".encode())
                else:
                    conn.send("Error: Not enough shares available.".encode())
            else:
                conn.send("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.".encode())
        except ValueError:
            conn.send("Error: Invalid data format.".encode())
        
        update_last_seen(DB_CONN, username, password)
        update_balance(DB_CONN, username, password, balance)
        if side.upper() == "S":
            update_num_of_shares(DB_CONN, stock_symbol, amount)
        else:
            update_num_of_shares(DB_CONN, stock_symbol, -amount)
        update_current_price(DB_CONN, stock_symbol, share_price)
        update_shares_sold(DB_CONN, stock_symbol, amount)
        if share_price > get_highest_share_price(DB_CONN, stock_symbol):
            update_highest_price(DB_CONN, stock_symbol, share_price)
        if share_price < get_lowest_share_price(DB_CONN, stock_symbol):
            update_lowest_price(DB_CONN, stock_symbol, share_price)
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
