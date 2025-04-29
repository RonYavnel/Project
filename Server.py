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
        self.ddos_dict = {} # ip: number of connections
        self.dict_of_all_clients = {} # (ip, port, username): ddos_status
        self.dict_of_live_connections = {}  # (ip, port): username
        self.stock_prices_history = {}  # stock_symbol: [list of stock prices]
        self.mutex = threading.Lock()
        self.e = Encryption()
        self.tls = DB_Tools("stocktradingdb")
        self.s_lib = Server_Lib()
        self.ui = ServerUI(self.stop_server)  # Pass the stop_server callback to the UI
        self.e.generate_keys()

    def setup_stock_prices_history(self):
        for stock in self.tls.get_all_column_values("stocks", "symbol"):
            self.stock_prices_history[stock] = [self.s_lib.get_current_share_price(stock)]  # Initialize the stock prices history with the current share price
            
    def initialize_dict_of_all_clients(self):
        # Initialize the list of all clients with their IP, port, and DDoS status
        for row in self.tls.get_all_rows("users"):
            ip = row[3]
            port = row[4]
            username = row[0]
            ddos_status = row[7]
            self.dict_of_all_clients[(ip, port, username)] = ddos_status

    def init_server(self):
        # Initiate a socket
        self.server_socket = socket.socket()
        self.server_socket.bind((self.host, self.port))
        # Wait for connections from clients
        self.server_socket.listen(20)

    def handle_connections(self):
        self.init_server()
        try:
            while True:
                try:
                    # For each connection: accept it and start checking for overload and DDoS attacks
                    conn, addr = self.server_socket.accept()
                    total_num_of_connections = sum(self.ddos_dict.values())                    
                    print(f"Total number of connections: {total_num_of_connections}")
                    if total_num_of_connections >= MAX_CLIENTS:
                        print("Maximum number of clients reached. Connection rejected.")
                        conn.send(self.e.encrypt_data("Server is busy. Please try again later.", self.e.load_client_public_key()))
                        conn.close()
                        continue
                    else:
                        conn.send(self.e.encrypt_data("The server is not overloaded and accepts connections.", self.e.load_client_public_key()))

                    # Check for DDoS attacks
                    if not self.ddos_check(conn):
                        print(f"Connection from {addr} rejected due to DDoS protection.")
                        # Don't need to close conn here as ddos_check already closes it
                        continue
                    
                    print(f"Connection from {addr} accepted")
                    # Start a new thread for each client connection
                    client_thread = threading.Thread(target=self.deal_maker, args=(conn,))
                    client_thread.start()
                except OSError as e:
                    if e.errno != socket.EBADF:  # If it's not a "bad file descriptor" error
                        print(f"Connection error: {e}")
                        continue
                    else:
                        raise  # Re-raise if it's a server socket error
        except OSError as e:
            print(f"Server socket closed: {e}")

    def initialize_database_tables(self):
    
        # Create the tables in the database
        self.tls.create_table("stocks",
                              """(company_name VARCHAR(255), symbol VARCHAR(255), stock_id INT NOT NULL PRIMARY KEY auto_increment, 
                              shares_sold INT, num_of_shares INT, current_price INT, highest_price INT, lowest_price INT)""")
        self.tls.create_table("transactions",
                              """(username VARCHAR(255), client_id VARCHAR(255), side CHAR, 
                              stock_symbol VARCHAR(255), share_price INT, amount INT, time_stamp TIMESTAMP)""")
        self.tls.create_table("users",
                              """(username VARCHAR(255), hashed_password VARCHAR(255), client_id INT NOT NULL PRIMARY KEY auto_increment, 
                              ip VARCHAR(255), port INT, last_seen DATETIME, balance INT, ddos_status VARCHAR(255))""")

    def ddos_check(self, client_socket):
        # Function to check for DDoS attacks
        ip = client_socket.getpeername()[0]
        if ip in self.ddos_dict:
            if self.ddos_dict[ip] >= MAX_CONNECTIONS_FROM_CLIENT:
                # Check if the IP is registered in the users table
                if self.s_lib.is_ip_exists(ip):
                    ddos_status = self.s_lib.get_ddos_status(ip)
                    print("ddos status:", ddos_status)
                    if ddos_status == "blocked":
                        # Update the ddos_status to "accepted" for this IP
                        print(f"IP {ip} is registered in DB. DDoS status is already 'blocked'.")

                    else:
                        # Update the ddos_status to "blocked" for this IP
                        self.s_lib.update_ddos_status(ip, "blocked")
                        self.ui.refresh_all_clients_table(self.dict_of_all_clients)
                        print(f"IP {ip} is registered in DB. DDoS status updated to 'blocked'.")
                
                # Send the blocked message to the client
                client_socket.send(self.e.encrypt_data("You are blocked due to too many login attempts.", self.e.load_client_public_key()))
                print(f"DDoS attack detected from {ip}. Closing connection.")
                sleep(1)  # Give the client time to process the message
                client_socket.close()  # Close the connection after sending the message
                return False
            else:
                self.ddos_dict[ip] += 1
                client_socket.send(self.e.encrypt_data("Connection accepted", self.e.load_client_public_key()))
        else:
            # First connection from this IP
            self.ddos_dict[ip] = 1
            client_socket.send(self.e.encrypt_data("Connection accepted", self.e.load_client_public_key()))  # Send acknowledgment
        return True

    def deal_maker(self, conn):
        try:
            server_private_key = self.e.load_server_private_key()
            client_public_key = self.e.load_client_public_key()

            print("in deal_maker")

            username, hashed_password = self.s_lib.handle_user_connection(conn, server_private_key, client_public_key)
            print("username is: ", username)

            if username not in self.dict_of_all_clients:
                self.dict_of_all_clients[conn.getpeername()[0], conn.getpeername()[1], username] = self.s_lib.get_ddos_status(conn.getpeername()[0])


            self.dict_of_live_connections[conn.getpeername()] = username
            print(self.dict_of_live_connections)

            balance = self.s_lib.handle_user_balance(conn, username, hashed_password, server_private_key, client_public_key)

            with self.mutex:
                self.ui.refresh_all_clients_table(self.dict_of_all_clients)
                
            while True:
                # Get available stocks and send the list to the client
                stocks_and_prices = {}
                list_of_stocks = self.tls.get_all_column_values( "stocks", "symbol")
                list_of_current_prices = self.tls.get_all_column_values( "stocks", "current_price")
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

                while True:  # Inner loop to handle order retries
                    # Receive order from client
                    order = self.e.decrypt_data(conn.recv(4096), server_private_key)

                    if not order:
                        conn.send(self.e.encrypt_data("Error: the order input is empty", client_public_key))
                        continue  # Stay in inner loop waiting for corrected order

                    print("Order is:", order)

                    with self.mutex:
                        try:
                            delimiter = "$"
                            param = order.split(delimiter)

                            if len(param) != 2:
                                conn.send(self.e.encrypt_data("Error: Incorrect format. Use 'side$amount' format.", client_public_key))
                                continue  # Stay in inner loop waiting for corrected order

                            if not param[1].isdigit():
                                conn.send(self.e.encrypt_data("Error: Amount must be a numeric value.", client_public_key))
                                continue  # Stay in inner loop waiting for corrected order

                            side, amount = param[0].upper(), int(param[1])

                            if side.upper() not in ["B", "S"]:
                                conn.send(self.e.encrypt_data("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.", client_public_key))
                                continue  # Stay in inner loop waiting for corrected order
                            
                            # Simulate a delay in processing the order
                            sleep(0.5)
                            
                            conn.send(self.e.encrypt_data("Order received", client_public_key))
                            
                            # Simulate a delay in processing the order
                            sleep(1)

                            deal = share_price * amount

                            if side.upper() == "S":
                                balance += deal

                                self.tls.insert_row(
                                    "transactions",
                                    "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                    "(%s, %s, %s, %s, %s, %s, %s)",
                                    (username, self.s_lib.get_client_id(username, hashed_password), "S", stock_symbol, share_price, amount, datetime.now())
                                )

                                adjustment = int((amount * share_price) * 0.01)
                                share_price = max(1, share_price - adjustment)

                                conn.send(self.e.encrypt_data(f"Sale completed. Your updated balance: {balance}", client_public_key))

                            else:
                                if balance >= deal:
                                    balance -= deal

                                    self.tls.insert_row(
                                        "transactions",
                                        "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                        "(%s, %s, %s, %s, %s, %s, %s)",
                                        (username, self.s_lib.get_client_id(username, hashed_password), "B", stock_symbol, share_price, amount, datetime.now())
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
                            sleep(1)
                            self.ui.refresh_transactions_table()
                            self.ui.refresh_stock_graphs({stock_symbol: self.stock_prices_history[stock_symbol]})

                            # Break inner loop after a successful order
                            break

                        except ValueError:
                            conn.send(self.e.encrypt_data("Error: Invalid data format.", client_public_key))
                            continue  # Stay in inner loop waiting for corrected order

                self.s_lib.update_all_data( conn, username, hashed_password, balance, side, amount, stock_symbol, share_price, client_public_key)

        except ConnectionResetError:
            print(f"Connection with {conn} was forcibly aborted")
            self.ddos_dict[conn.getpeername()[0]] -= 1

        finally:
            self.dict_of_live_connections.pop(conn.getpeername())
            dict_of_live_connections = [(ip, port, user) for (ip, port), user in self.dict_of_live_connections.items()]
            self.ui.refresh_all_clients_table(self.dict_of_all_clients)
            print(self.dict_of_live_connections)
            self.ddos_dict[conn.getpeername()[0]] -= 1
            conn.close()
            print(f"Connection with {conn} closed")

    def start_ui(self):
        self.ui.show_combined_ui(self.dict_of_all_clients, self.tls.get_all_column_values( "stocks", "symbol"), self.stock_prices_history)

    def stop_server(self):
        if self.server_socket:
            self.server_socket.close()

    def run_whole_server(self):
        print("Server is running")
        self.initialize_database_tables()
        print("Database is ready")

        self.setup_stock_prices_history()
        print("Stock prices history is updated")

        self.initialize_dict_of_all_clients()
        print("List of all clients is updated")

        # Start the UI in a separate thread
        ui_thread = threading.Thread(target=self.start_ui, daemon=True)
        ui_thread.start()

        # Run the server in the main thread
        self.handle_connections()

if __name__ == '__main__':
    server = Server(HOST, PORT)
    server.run_whole_server()