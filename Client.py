import socket
from getpass import getpass
from encryption_lib import Encryption
import ast
from client_UI import ClientUI
import tkinter as tk


DEBUG = False

class Client:
        
    def __init__(self, host, port, root):
        self.host = host
        self.port = port
        self.client_socket = None
        self.e = Encryption()
        self.client_private_key = self.e.load_client_private_key()
        self.server_public_key = self.e.load_server_public_key()
        # self.root = root
        # self.ui = ClientUI(self.root, self)


    def general_input(self, msg, default_val):
        if DEBUG:
            print("returning " + default_val)
            return default_val
        return input(msg)

    def general_password_input(self, msg, default_val):
        if DEBUG:
            print("returning " + default_val)
            return default_val
        return getpass(msg)

    def get_and_send_username_and_password(self):
        # Fill in personal details - username and password
        # Send them to the server
        load_status = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
        print("load_status:", load_status)
        if load_status == "Server is busy. Please try again later.":
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)  # Shutdown the connection
            except OSError:
                pass  # Ignore errors during shutdown
            finally:
                self.client_socket.close()  # Close the socket
            raise ConnectionError("Overloading block")  # Raise an exception
        
        ddos_result = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
        print("ddos:", ddos_result)
        
        if ddos_result == "You are blocked due to too many login attempts.":
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)  # Shutdown the connection
            except OSError:
                pass  # Ignore errors during shutdown
            finally:
                self.client_socket.close()  # Close the socket
            raise ConnectionError("DDoS block")  # Raise an exception
        
        
        username = self.general_input("Enter your username: ", "ron")
        self.client_socket.send(self.e.encrypt_data(username, self.server_public_key))  # Encrypt and send username

        password = self.general_password_input("Enter your password: ", "10010")
        self.client_socket.send(self.e.encrypt_data(password, self.server_public_key))  # Encrypt and send password
        
        # Handle new user registration
        while True:
            # Receive the answer from the server
            result = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)  
            if result == '2':
                print("Username already exists. Please enter a new one.")
                username = self.general_input("Enter your username: ", "ron")
                self.client_socket.send(self.e.encrypt_data(username, self.server_public_key))

                password = self.general_password_input("Enter your password: ", "10010")
                self.client_socket.send(self.e.encrypt_data(password, self.server_public_key))
            elif result == '1':
                print(f"Welcome back {username}!")
                break
            else:
                print("Nice to meet you! You are now registered.")
                break

    def initialize_client_balance(self):
        # Check if client with these characteristics exists - the server sends the answer:
        # 1 if registered and 0 if not
        is_registered = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)

        if is_registered == '0':
            while True:
                try:
                    balance = int(self.general_input("Please enter your balance: ", "10000"))
                    break
                except ValueError:
                    print("Invalid balance entered. Please enter a numeric value.")

            self.client_socket.send(self.e.encrypt_data(str(balance), self.server_public_key))
        else:
            current_balance = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
            print(f"Your current balance: {current_balance}")
        
    
    def start_ui(self):
        self.root.mainloop()
    
    def run_whole_client(self):
        try:
            self.client_socket = socket.socket()
            self.client_socket.connect((self.host, self.port))
            
            self.get_and_send_username_and_password()
            self.initialize_client_balance()
            
            while True:
                # Get the list of stocks from the server for client's choice
                stocks_and_prices = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
                stocks_and_prices = ast.literal_eval(stocks_and_prices)
                list_of_stocks = list(stocks_and_prices.keys())
                # Get the wanted stock symbol from the client
                stock_symbol = self.general_input(f"Choose a stock from {list_of_stocks}: ", "AAPL").upper()

                # Check if the stock symbol is valid
                while stock_symbol not in list_of_stocks:
                    stock_symbol = self.general_input(f"Invalid stock. Choose from {list_of_stocks}: ", "AAPL").upper()

                # Send the stock symbol to the server
                self.client_socket.send(self.e.encrypt_data(stock_symbol, self.server_public_key))

                # Receive the current share price from the server
                share_price = stocks_and_prices[stock_symbol]
                print(f"Current share price: {share_price}")

                while True:
                    order = self.general_input("Enter your order (side$amount): ", "")

                    self.client_socket.send(self.e.encrypt_data(order, self.server_public_key))

                    server_response = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
                    print(server_response)

                    if server_response == "Order received":
                        break

                response = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
                print(response)

                share_price = int(self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key))
                print(f"New share price: {share_price}")
        except ConnectionError as e:
            if str(e) == "Overloading block":
                print("Server is currently at maximum capacity. Please try again later.")
                return
            elif str(e) == "DDoS block":
                print("Connection blocked due to too many login attempts. Please try again later.")
                return
            else:
                print(f"Connection error: {e}")
                return
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return
        finally:
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass


if __name__ == '__main__':

    HOST = socket.gethostname()
    PORT = 5000
    #root = tk.Tk()
    client = Client(HOST, PORT, None)

    # Start UI in a separate thread (like server)
    #import threading
    #ui_thread = threading.Thread(target=client.start_ui, daemon=True)
    #ui_thread.start()

    # Run logic (including connecting and trading)
    client.run_whole_client()
