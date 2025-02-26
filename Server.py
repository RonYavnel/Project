import socket
import threading
from datetime import datetime
from server_constants import *
from server_lib import *
from db_tools import *
from server_UI import ServerUI
from encryption_lib import Encryption

class Server:
    import time
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.mydb = None
        self.list_of_connections = {}  # (ip, port): username
        self.stock_prices_history = {}  # stock_symbol: [list of stock prices]
        self.mutex = threading.Lock()
        self.e = Encryption()
        self.ui = ServerUI(self.stop_server)  # Pass the stop_server callback to the UI

    def update_stock_prices_history(self):
        for stock in get_all_column_values(self.mydb, "stocks", "symbol"):
            self.stock_prices_history[stock] = [get_current_share_price(self.mydb, stock)]  # Initialize the stock prices history with the current share price

    def init_server(self):
        # Initiate a socket
        self.server_socket = socket.socket()
        self.server_socket.bind((self.host, self.port))
        # Wait for connections from clients
        self.server_socket.listen(20)

    def run_server(self):
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
        my_sql_server = init()
        # Create a new database and connect to it
        create_new_database(my_sql_server, "stocktradingdb")
        self.mydb = init_with_db("stocktradingdb")
        # Create the tables in the database
        create_table(self.mydb, "stocks",
                     "(company_name VARCHAR(255), symbol VARCHAR(255), stock_id INT NOT NULL PRIMARY KEY auto_increment, shares_sold INT, num_of_shares INT, current_price INT, highest_price INT, lowest_price INT)")
        create_table(self.mydb, "transactions",
                     "(username VARCHAR(255), client_id VARCHAR(255), side CHAR, stock_symbol VARCHAR(255), share_price INT, amount INT, time_stamp TIMESTAMP)")
        create_table(self.mydb, "users",
                     "(username VARCHAR(255), hashed_password VARCHAR(255), client_id INT NOT NULL PRIMARY KEY auto_increment, ip VARCHAR(255), port INT, last_seen DATETIME, balance INT)")

    def deal_maker(self, conn):
        import time
        
        try:
            # Load the correct keys
            server_private_key = self.e.load_server_private_key()  # Used to decrypt client messages
            client_public_key = self.e.load_client_public_key()    # Used to encrypt messages for the client

            print("in deal_maker")

            # Authenticate user and get username + hashed password
            username, hashed_password = handle_user_connection(self.mydb, conn, server_private_key, client_public_key)
            print("username is: ", username)
            print("hashed_password is: ", hashed_password)

            self.list_of_connections[conn.getpeername()] = username  # Add the connection to the list of connections
            print(self.list_of_connections)

            with self.mutex:
                # Refresh the connected clients table
                connected_clients_list = [(ip, port, user) for (ip, port), user in self.list_of_connections.items()]  
                self.ui.refresh_connected_clients(connected_clients_list)

            # Handle balance
            balance = handle_user_balance(self.mydb, conn, username, hashed_password, server_private_key, client_public_key)

            # Get available stocks and send the list to the client
            list_of_stocks = get_all_column_values(self.mydb, "stocks", "symbol")  
            conn.send(self.e.encrypt_data(str(list_of_stocks), client_public_key))  

            # Receive stock symbol from client
            stock_symbol = self.e.decrypt_data(conn.recv(4096), server_private_key).upper()  
            share_price = get_current_share_price(self.mydb, stock_symbol)  

            # Send the client the updated share price
            conn.send(self.e.encrypt_data(str(share_price), client_public_key))  

            with self.mutex:
                # Initialize stock history if not already present
                if stock_symbol not in self.stock_prices_history:
                    self.stock_prices_history[stock_symbol] = []

            while True:

                print("Waiting for order")

                # Receive order from client
                order = self.e.decrypt_data(conn.recv(4096), server_private_key)

                # Error handling: empty order
                if not order:
                    conn.send(self.e.encrypt_data("Error: the order input is empty", client_public_key))
                    continue

                print("Order is:", order)

                with self.mutex:
                    try:
                        delimiter = "$"
                        param = order.split(delimiter)

                        # Validate format: delimiter and numeric amount check
                        if len(param) != 2:
                            conn.send(self.e.encrypt_data("Error: Incorrect format. Use 'side$amount' format.", client_public_key))
                            continue
                        
                        if not param[1].isdigit():
                            conn.send(self.e.encrypt_data("Error: Amount must be a numeric value.", client_public_key))
                            continue

                        side, amount = param[0].upper(), int(param[1])

                        # Validate the "side" parameter
                        if side.upper() not in ["B", "S"]:
                            conn.send(self.e.encrypt_data("Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.", client_public_key))
                            continue
                        
                        # If all validations pass, send confirmation to the client
                        conn.send(self.e.encrypt_data("Order received", client_public_key))
                        
                        time.sleep(1)
                           
                        # Calculate the whole deal cost
                        deal = share_price * amount

                        # Handle the order
                        if side.upper() == "S":  # Selling
                            balance += deal  # Add the deal cost to the balance of the client

                            # Document transaction in the Transactions table
                            insert_row(
                                self.mydb,
                                "transactions",
                                "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                "(%s, %s, %s, %s, %s, %s, %s)",
                                (username, get_client_id(self.mydb, username, hashed_password), "S", stock_symbol, share_price, amount, datetime.now())
                            )

                            # Adjust the share price based on selling activity
                            adjustment = int((amount * share_price) * 0.01)
                            share_price = max(1, share_price - adjustment)

                            # Send confirmation to the client
                            conn.send(self.e.encrypt_data(f"Sale completed. Your updated balance: {balance}", client_public_key))

                        else:  # Buying
                            if balance >= deal:  # Check if client has enough funds
                                balance -= deal  # Deduct the cost

                                # Document transaction in the Transactions table
                                insert_row(
                                    self.mydb,
                                    "transactions",
                                    "(username, client_id, side, stock_symbol, share_price, amount, time_stamp)", 
                                    "(%s, %s, %s, %s, %s, %s, %s)",
                                    (username, get_client_id(self.mydb, username, hashed_password), "B", stock_symbol, share_price, amount, datetime.now())
                                )        

                                # Adjust the share price based on buying activity
                                adjustment = int((amount * share_price) * 0.01)
                                share_price += adjustment

                                # Send confirmation to the client
                                conn.send(self.e.encrypt_data(f"Purchase successful. New balance: {balance}", client_public_key))

                            else:
                                conn.send(self.e.encrypt_data(f"Error: Insufficient balance for this purchase. Your balance is: {balance}", client_public_key))

                        # Update the stock price history
                        self.stock_prices_history[stock_symbol].append(share_price)

                        # Maintain only the last 10 prices
                        if len(self.stock_prices_history[stock_symbol]) > 15:
                            self.stock_prices_history[stock_symbol].pop(0)

                        print(self.stock_prices_history)

                        self.ui.refresh_transactions_table(self.mydb)
                        self.ui.refresh_stock_graphs({stock_symbol: self.stock_prices_history[stock_symbol]})

                    except ValueError:
                        conn.send(self.e.encrypt_data("Error: Invalid data format.", client_public_key))

                # Update all necessary data
                update_all_data(self.mydb, conn, username, hashed_password, balance, side, amount, stock_symbol, share_price, client_public_key)

        except ConnectionResetError:
            print(f"Connection with {conn} was forcibly aborted")

        finally:
            # Remove connection from list
            self.list_of_connections.pop(conn.getpeername())  
            connected_clients_list = [(ip, port, user) for (ip, port), user in self.list_of_connections.items()]  
            self.ui.refresh_connected_clients(connected_clients_list)  

            print(self.list_of_connections)
            conn.close()
            print(f"Connection with {conn} closed")

    def start_ui(self):
        self.ui.show_combined_ui(self.mydb, self.list_of_connections, get_all_column_values(self.mydb, "stocks", "symbol"), self.stock_prices_history)

    def stop_server(self):
        if self.server_socket:
            self.server_socket.close()

    def run(self):
        print("Server is running")
        self.initialize_database()
        print("Database is ready")

        self.update_stock_prices_history()
        print("Stock prices history is updated")

        # Start the UI in a separate thread
        ui_thread = threading.Thread(target=self.start_ui, daemon=True)
        ui_thread.start()

        # Run the server in the main thread
        self.run_server()

if __name__ == '__main__':
    server = Server(HOST, PORT)
    server.run()