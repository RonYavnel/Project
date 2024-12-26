import socket
from db_tools import *

# Saving the constant variables in a dedicated file
HOST = socket.gethostname()
PORT = 5000

DB_CONN = init_with_db("StockTradingDB")