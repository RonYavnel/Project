import socket
from getpass import getpass
from encryption_lib import Encryption

DEBUG = False

class Client:
        
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.e = Encryption()
        self.client_private_key = self.e.load_client_private_key()
        self.server_public_key = self.e.load_server_public_key()

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

    def run(self):
                
        # Initialize the client socket and connect to the server
        self.client_socket = socket.socket()
        self.client_socket.connect((self.host, self.port))

        # Get the username and password from the client
        self.get_and_send_username_and_password()
        
        # Initialize the client's balance
        self.initialize_client_balance()

        # Get the list of stocks from the server for client's choice
        list_of_stocks = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
        
        # Get the wanted stock symbol from the client
        stock_symbol = self.general_input(f"Choose a stock from {list_of_stocks}: ", "AAPL").upper()

        # Check if the stock symbol is valid
        while stock_symbol not in list_of_stocks:
            stock_symbol = self.general_input(f"Invalid stock. Choose from {list_of_stocks}: ", "AAPL").upper()
        
        # Send a valid stock symbol to the server
        self.client_socket.send(self.e.encrypt_data(stock_symbol, self.server_public_key))
        
        # Receive the current share price from the server
        share_price = int(self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key))
        print(f"Current share price: {share_price}")
            
        # Listen to client's orders until he sends an empty message
        while True:
            while True:
                # Get the client's order
                order = self.general_input("Enter your order (side$amount): ", "b$10")
                
                # Send the order to the server (even if it is empty)
                self.client_socket.send(self.e.encrypt_data(order, self.server_public_key) if order else self.e.encrypt_data(" ", self.server_public_key))

                # Receive feedback from the server about the order
                server_response = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
                print(server_response)
                                
                # If the server confirms the order is valid, break the loop
                if server_response == "Order recieved":
                    break
            
            
            # Receive the appropriate response from the server about the order
            response = self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key)
            print(response)
            
            # Receive the new share price from the server
            share_price = int(self.e.decrypt_data(self.client_socket.recv(4096), self.client_private_key))
            print(f"New share price: {share_price}")


if __name__ == '__main__':
    HOST = socket.gethostname()
    PORT = 5000
    client = Client(HOST, PORT)
    client.run()