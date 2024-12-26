import socket
import threading
import time
import mysql.connector
from db_tools import *
from datetime import *

host = '127.0.0.1'

db_conn = init_with_db("StockTradingDB")
print(show_databases(db_conn))   
print(show_tables(db_conn))
""" insert_row(
    db_conn, 
    "transactions", 
    "(username, userID, side, stock_symbol, share_price, amount)", 
    "(%s, %s, %s, %s, %s, %s)",
    ("Ron", "10010", "B", "AAPL", 220, 100) 
)
print(get_all_rows(db_conn, "transactions"))
delete_row(db_conn, "transactions", "username", "ron")
print(get_all_rows(db_conn, "transactions")) """
