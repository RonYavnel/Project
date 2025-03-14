import socket
import threading
from datetime import datetime
from time import sleep
from server_constants import *
from server_lib import Server_Lib
from db_tools import *
from server_UI import ServerUI
from encryption_lib import Encryption

class Server:
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.mydb = None
        self.list_of_connections = {}  # (ip, port): username
        self.stock_prices_history = {}  # stock_symbol: [list of stock prices]
        self.mutex = threading.Lock()
        self.e = Encryption()
        self.tls = DB_Tools()
        self.s_lib = Server_Lib()
        self.ui = ServerUI(self.stop_server)  # Pass the stop_server callback to the UI
        self.e.generate_keys()

    def setup_stock_prices_history(self):
        for stock in self.tls.get_all_column_values(self.mydb, "stocks", "symbol"):
            self.stock_prices_history[stock] = [self.s_lib.get_current_share_price(self.mydb, stock)]  # Initialize the stock prices history with the current share price
            

    def init_server(self):
        # Initiate a socket
        self.server_socket = socket.socket()
        self.server_socket.bind((self.host, self.port))
        # Wait for connections from clients
        self.server_socket.listen(20)

    def handle_connections(self):
        self.init_server()
        # If the server is running - accept connections
        try:
            while True:
                # For each connection: accept, and send it to thread
                conn = self.server_socket.accept()[0]
                client_thread = threading.Thread(target=self.deal_maker, args=(conn,))
                client_thread.start()
        # If the server socket is closed - print a message
        except OSError:
            print("Server socket closed")

    def initialize_database(self):
        # Initiate the connection with the sql server
        my_sql_server = self.tls.init()
        # Create a new database and connect to it
        self.tls.create_new_database(my_sql_server, "stocktradingdb")
        self.mydb = self.tls.init_with_db("stocktradingdb")
        # Create the tables in the database
        self.tls.create_table(self.mydb, "stocks",
                              """(company_name VARCHAR(255), symbol VARCHAR(255), stock_id INT NOT NULL PRIMARY KEY auto_increment, 
                              shares_sold INT, num_of_shares INT, current_price INT, highest_price INT, lowest_price INT)""")
        self.tls.create_table(self.mydb, "transactions",
                              """(username VARCHAR(255), client_id VARCHAR(255), side CHAR, 
                              stock_symbol VARCHAR(255), share_price INT, amount INT, time_stamp TIMESTAMP)""")
        self.tls.create_table(self.mydb, "users",
                              """(username VARCHAR(255), hashed_password VARCHAR(255), client_id INT NOT NULL PRIMARY KEY auto_increment, 
                              ip VARCHAR(255), port INT, last_seen DATETIME, balance INT)""")

    def deal_maker(self, conn):
        try:
            server_private_key = self.e.load_server_private_key()
            client_public_key = self.e.load_client_public_key()

            print("in deal_maker")

            username, hashed_password = self.s_lib.handle_user_connection(self.mydb, conn, server_private_key, client_public_key)
            print("username is: ", username)

            self.list_of_connections[conn.getpeername()] = username
            print(self.list_of_connections)

            with self.mutex:
                connected_clients_list = [(ip, port, user) for (ip, port), user in self.list_of_connections.items()]
                self.ui.refresh_connected_clients(connected_clients_list)

            balance = self.s_lib.handle_user_balance(self.mydb, conn, username, hashed_password, server_private_key, client_public_key)

            while True:
                # Get available stocks and send the list to the client
                stocks_and_prices = {}
                list_of_stocks = self.tls.get_all_column_values(self.mydb, "stocks", "symbol")
                list_of_current_prices = self.tls.get_all_column_values(self.mydb, "stocks", "current_price")
                for i in range(len(list_of_stocks)):
                    stocks_and_prices[list_of_stocks[i]] = list_of_current_prices[i]
                print("stocks_and_prices is: ", stocks_and_prices)

                conn.send(self.e.encrypt_data(str(stocks_and_prices), client_public_key))

                # Ask client for a stock symbol before each order
                stock_symbol = self.e.decrypt_data(conn.recv(4096), server_private_key).upper()

                share_price = stocks_and_prices[stock_symbol]
                
                with self.mutex:
                    if stock_symbol not in self.stock_prices_history:
                        self.stock_prices_history[stock_symbol] = []

                print("Waiting for order")

                # Receive order from client
                order = self.e.decrypt_data(conn.recv(4096), server_private_key)

                if not order:
                    conn.send(self.e.encrypt_data("Error: the order input is empty", client_public_key))
                    continue

                print("Order is:", order)

                with self.mutex:
                    try:
                        delimiter = "$"
                        param = order.split(delimiter)

                        if len(param) != 2:
                            conn.send(self.e.encrypt_data("Error: Incorrect format. Use 'side$amount' format.", client_public_key))
                            continue

                        if not param[1].isdigit():
                            conn.send(self.e.encrypt_data("Error: Amount must be a numeric value.", client_public_key))
                            continue

                        side, amount = param[0].upper(), int(param[1])

                        if side.upper() not in ["B", "S"]:
                            conn.send(self.e.encrypt_data("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.", client_public_key))
                            continue

                        conn.send(self.e.encrypt_data("Order received", client_public_key))

                        sleep(1)

                        deal = share_price * amount

                        if side.upper() == "S":
                            balance += deal

                            self.tls.insert_row(
                                self.mydb,
                                "transactions",
                                "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                "(%s, %s, %s, %s, %s, %s, %s)",
                                (username, self.s_lib.get_client_id(self.mydb, username, hashed_password), "S", stock_symbol, share_price, amount, datetime.now())
                            )

                            adjustment = int((amount * share_price) * 0.01)
                            share_price = max(1, share_price - adjustment)

                            conn.send(self.e.encrypt_data(f"Sale completed. Your updated balance: {balance}", client_public_key))

                        else:
                            if balance >= deal:
                                balance -= deal

                                self.tls.insert_row(
                                    self.mydb,
                                    "transactions",
                                    "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                    "(%s, %s, %s, %s, %s, %s, %s)",
                                    (username, self.s_lib.get_client_id(self.mydb, username, hashed_password), "B", stock_symbol, share_price, amount, datetime.now())
                                )

                                adjustment = int((amount * share_price) * 0.01)
                                share_price += adjustment

                                conn.send(self.e.encrypt_data(f"Purchase successful. New balance: {balance}", client_public_key))
                            else:
                                conn.send(self.e.encrypt_data(f"Error: Insufficient balance for this purchase. Your balance is: {balance}", client_public_key))

                        self.stock_prices_history[stock_symbol].append(share_price)

                        if len(self.stock_prices_history[stock_symbol]) > 15:
                            self.stock_prices_history[stock_symbol].pop(0)

                        print(self.stock_prices_history)

                        self.ui.refresh_transactions_table(self.mydb)
                        self.ui.refresh_stock_graphs({stock_symbol: self.stock_prices_history[stock_symbol]})

                    except ValueError:
                        conn.send(self.e.encrypt_data("Error: Invalid data format.", client_public_key))

                self.s_lib.update_all_data(self.mydb, conn, username, hashed_password, balance, side, amount, stock_symbol, share_price, client_public_key)

        except ConnectionResetError:
            print(f"Connection with {conn} was forcibly aborted")

        finally:
            self.list_of_connections.pop(conn.getpeername())
            connected_clients_list = [(ip, port, user) for (ip, port), user in self.list_of_connections.items()]
            self.ui.refresh_connected_clients(connected_clients_list)

            print(self.list_of_connections)
            conn.close()
            print(f"Connection with {conn} closed")


    def start_ui(self):
        self.ui.show_combined_ui(self.mydb, self.list_of_connections, self.tls.get_all_column_values(self.mydb, "stocks", "symbol"), self.stock_prices_history)

    def stop_server(self):
        if self.server_socket:
            self.server_socket.close()

    def run_whole_server(self):
        print("Server is running")
        self.initialize_database()
        print("Database is ready")

        self.setup_stock_prices_history()
        print("Stock prices history is updated")

        # Start the UI in a separate thread
        ui_thread = threading.Thread(target=self.start_ui, daemon=True)
        ui_thread.start()

        # Run the server in the main thread
        self.handle_connections()

if __name__ == '__main__':
    server = Server(HOST, PORT)
    server.run_whole_server()