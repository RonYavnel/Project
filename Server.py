import socket
import threading
from datetime import datetime
from configuration import *
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
        self.dict_of_all_clients = {} # (ip, username): ddos_status
        self.dict_of_active_clients = {}  # (ip, port): username
        self.stock_prices_history = {}  # stock_symbol: [list of stock prices]
        self.mutex = threading.Lock()
        self.is_running = True
        self.e = Encryption()
        self.tls = DB_Tools("stocktradingdb")
        self.s_lib = Server_Lib(self)
        self.ui = ServerUI(self.stop_server)  # Pass the stop_server callback to the UI
        self.e.generate_keys()
        self.server_private_key = self.e.load_server_private_key()
        self.client_public_key = self.e.load_client_public_key()

    def setup_stock_prices_history(self):
        for stock in self.tls.get_all_column_values("stocks", "symbol"):
            self.stock_prices_history[stock] = [self.s_lib.get_current_share_price(stock)]  # Initialize the stock prices history with the current share price
            
    def initialize_dict_of_all_clients(self):
        # Initialize the list of all clients with their IP, port, and DDoS status
        for row in self.tls.get_all_rows("users"):
            ip = row[3]
            username = row[0]
            ddos_status = row[7]
            self.dict_of_all_clients[(ip, username)] = ddos_status

    def init_server(self):
        # Initiate a socket
        self.server_socket = socket.socket()
        self.server_socket.bind((self.host, self.port))
        # Wait for connections from clients
        self.server_socket.listen(20)

    def send_data(self, conn, data):
        """Send data to the client."""
        try:
            conn.send(self.e.encrypt_data(data+DATA_DELIMITER, self.client_public_key))
        except Exception as e:
            print(f"Error sending data: {e}")

    def recv_data(self, conn, received_data):
        # Receive data from the server
        if not DATA_DELIMITER in received_data:
            # read more data from the socket
            data = self.e.decrypt_data(conn.recv(4096), self.server_private_key)
            if not data:
                raise ConnectionError("Connection closed by server")
            # add new data to the received data
            received_data += data
            # if still no delimiter - raise an error
            if not DATA_DELIMITER in received_data:
                raise ConnectionError("Missing delimiter in received data")
        data, _, received_data = received_data.partition(DATA_DELIMITER)
        
        return data, received_data

    def handle_connections(self):
        """Handle incoming client connections with proper shutdown support"""
        self.init_server()
        try:
            while self.is_running:
                try:
                    # Set timeout for checking shutdown flag
                    self.server_socket.settimeout(1.0)
                    
                    try:
                        conn, addr = self.server_socket.accept()
                        
                        # Check total connections
                        total_connections = sum(self.ddos_dict.values())
                        print(f"Total number of connections: {total_connections}")
                        
                        # Handle server overload
                        if total_connections >= MAX_CLIENTS:
                            print("Maximum number of clients reached. Connection rejected.")
                            self.send_data(conn, "Server is busy. Please try again later.")
                            conn.close()
                            continue
                            
                        self.send_data(conn, "The server is not overloaded and accepts connections.")

                        # DDoS protection check
                        if not self.ddos_check(conn):
                            print(f"Connection from {addr} rejected due to DDoS protection.")
                            continue

                        print(f"Connection from {addr} accepted")
                        
                        # Start client handler thread
                        client_thread = threading.Thread(
                            target=self.deal_maker,
                            args=(conn,),
                            daemon=True  # Make thread daemon so it exits when main thread exits
                        )
                        client_thread.start()

                    except socket.timeout:
                        # Normal timeout, just continue to check shutdown flag
                        continue
                        
                    except OSError as e:
                        # Handle socket errors
                        if not self.is_running:
                            # Clean shutdown in progress
                            break
                        print(f"Socket error: {e}")
                        continue
                        
                except Exception as e:
                    # Handle any other errors
                    if not self.is_running:
                        break
                    print(f"Error handling connection: {e}")
                    continue

        except Exception as e:
            # Handle fatal errors
            print(f"Fatal server error: {e}")
            
        finally:
            # Final cleanup
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
            print("Server stopped accepting connections")

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
        """Check for DDoS attacks and manage connection limits."""
        try:
            with self.mutex:
                print("self.ddos_dict is: ", self.ddos_dict)
            
            ip = client_socket.getpeername()[0]

            # Check if the IP exists in the database
            if self.s_lib.is_ip_exists(ip):
                ddos_status = self.s_lib.get_ddos_status(ip)
                print(f"IP {ip} has DDoS status: {ddos_status}")

                if ddos_status == "blocked":
                    # If the IP is already blocked, notify the client and close the connection
                    self.send_data(client_socket, "You are blocked due to too many login attempts.")
                    print(f"DDoS attack detected from {ip}. Closing connection.")
                    client_socket.close()
                    return False

            # Update the connection count in ddos_dict
            with self.mutex:
                if ip in self.ddos_dict:
                    self.ddos_dict[ip] += 1
                else:
                    self.ddos_dict[ip] = 1
                current_connections = self.ddos_dict[ip]

            # Check if the number of connections exceeds the allowed limit
            if current_connections > MAX_CONNECTIONS_FROM_CLIENT:
                print(f"IP {ip} exceeded the maximum allowed connections. Blocking IP.")
                
                with self.mutex:
                    # Update the ddos_status in the database to "blocked"
                    self.s_lib.update_ddos_status(ip, "blocked")
                    self.ui.refresh_all_clients_table(self.dict_of_all_clients, 
                                                    self.dict_of_active_clients)

                # Notify the client and close the connection
                self.send_data(client_socket, "You are blocked due to too many login attempts.")
                print(f"DDoS attack detected from {ip}. Closing connection.")
                client_socket.close()
                return False

            # If the IP is not blocked, allow the connection
            self.send_data(client_socket, "Connection accepted")
            print(f"Connection from {ip} accepted.")
            return True
            
        except Exception as e:
            print(f"Error in ddos_check: {e}")
            return False

    def deal_maker(self, conn):
        try:

            received_data = ""  # Initialize received_data to an empty string

            print("in deal_maker")

            ip = conn.getpeername()[0]
            port = conn.getpeername()[1]
            print("ip is: ", ip, "port is: ", port)

            username, hashed_password, received_data = self.s_lib.handle_user_connection(conn, received_data)
            print("username is: ", username)

            if username is None:
                return  # Exit if username is None - means that the user has disconnected


            self.dict_of_active_clients[(ip, port)] = username
            print("dict_of_active_clients: ", self.dict_of_active_clients)

            balance, received_data = self.s_lib.handle_user_balance(conn, username, hashed_password, received_data)

            if (ip, username) not in self.dict_of_all_clients:
                self.dict_of_all_clients[ip, username] = self.s_lib.get_ddos_status(ip)

            print("dict_of_active_clients: ", self.dict_of_active_clients)
            with self.mutex:
                self.ui.refresh_all_clients_table(self.dict_of_all_clients, self.dict_of_active_clients)
                
            while True:
                # Get available stocks and send the list to the client
                stocks_and_prices = {}
                list_of_stocks = self.tls.get_all_column_values( "stocks", "symbol")
                list_of_current_prices = self.tls.get_all_column_values( "stocks", "current_price")
                for i in range(len(list_of_stocks)):
                    stocks_and_prices[list_of_stocks[i]] = list_of_current_prices[i]
                print("stocks_and_prices is: ", stocks_and_prices)

                self.send_data(conn, str(stocks_and_prices))

                # Ask client for a stock symbol before each order
                stock_symbol, received_data = self.recv_data(conn, received_data)
                stock_symbol = stock_symbol.upper()

                share_price = stocks_and_prices[stock_symbol]
                
                with self.mutex:
                    if stock_symbol not in self.stock_prices_history:
                        self.stock_prices_history[stock_symbol] = []

                print("Waiting for order")

                while True:  # Inner loop to handle order retries
                    # Receive order from client
                    order, received_data = self.recv_data(conn, received_data)

                    if not order:
                        self.send_data(conn, "Error: the order input is empty")
                        continue  # Stay in inner loop waiting for corrected order

                    print("Order is:", order)

                    with self.mutex:
                        try:
                            delimiter = "$"
                            param = order.split(delimiter)

                            if len(param) != 2:
                                self.send_data(conn, "Error: Incorrect format. Use 'side$amount' format.")
                                continue  # Stay in inner loop waiting for corrected order

                            if not param[1].isdigit():
                                self.send_data(conn, "Error: Amount must be a numeric value.")
                                continue

                            side, amount = param[0].upper(), int(param[1])

                            if side.upper() not in ["B", "S"]:
                                self.send_data(conn, "Error: Invalid side parameter. Use 'B' for buy or 'S' for sell.")
                                continue  

                            self.send_data(conn, "Order received")

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

                                self.send_data(conn, f"Sale completed. Your updated balance: {balance}")

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

                                    self.send_data(conn, f"Purchase successful. New balance: {balance}")
                                else:
                                    self.send_data(conn, f"Error: Insufficient balance for this purchase. Your balance is: {balance}")
                            self.stock_prices_history[stock_symbol].append(share_price)

                            if len(self.stock_prices_history[stock_symbol]) > 15:
                                self.stock_prices_history[stock_symbol].pop(0)

                            print(self.stock_prices_history)
                            self.ui.refresh_transactions_table()
                            self.ui.refresh_stock_graphs({stock_symbol: self.stock_prices_history[stock_symbol]})

                            # Break inner loop after a successful order
                            break

                        except ValueError as e:
                            self.send_data(conn, "Error: Invalid data format.")
                            print("wrong order format", e)
                            continue  # Stay in inner loop waiting for corrected order

                self.s_lib.update_all_data( conn, username, hashed_password, balance, side, amount, stock_symbol, share_price)

        except ConnectionResetError:
            print(f"Connection with {conn} was forcibly aborted")

        finally:
            peer = conn.getpeername()
            if peer in self.dict_of_active_clients:
                print(f"Removing {peer} from active clients")
                self.dict_of_active_clients.pop(peer)
                dict_of_active_clients = [(ip, port, user) for (ip, port), user in self.dict_of_active_clients.items()]
                self.ui.refresh_all_clients_table(self.dict_of_all_clients, dict_of_active_clients)
            print("dict of active clients: ", self.dict_of_active_clients)

            if ip in self.ddos_dict:
                self.ddos_dict[ip] -= 1
                if self.ddos_dict[ip] == 0:
                    del self.ddos_dict[ip]  # Remove the IP from ddos_dict if no active connections remain

            conn.close()
            print(f"Connection with {conn} closed")

    def start_ui(self):
        self.ui.show_combined_ui(self.dict_of_all_clients, self.dict_of_active_clients, self.tls.get_all_column_values( "stocks", "symbol"), self.stock_prices_history)

    def stop_server(self):
        """Gracefully shutdown the server and all connections"""
        print("Initiating server shutdown...")
        self.is_running = False  # Set flag to stop the server
        
        # Close existing client connections from dict_of_active_clients
        for (ip, port), username in self.dict_of_active_clients.copy().items():
            try:
                conn = socket.socket()
                conn.connect((ip, port))
                self.send_data(conn, "Server is shutting down")
                conn.close()
            except:
                pass
        
        # Clear dictionaries
        self.dict_of_active_clients.clear()
        self.ddos_dict.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        print("Server shutdown completed")
        exit(0)

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
    server = Server(SERVER_IP, PORT)
    server.run_whole_server()