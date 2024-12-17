import socket
from DB_Helper import *

HOST = socket.gethostname()
PORT = 5000

stock_symbol = 'AAPL'
DB_CONN = init_with_db("StockTradingDB")
share_price = get_current_share_price(DB_CONN, stock_symbol)
num_of_shares = 50000