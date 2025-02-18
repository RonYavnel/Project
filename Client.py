# Import the socket module for communication
import socket 
from getpass import getpass
from encryption_lib import *

DEBUG = False

# Define a function for general input (for debugging purposes - automatically fills in the default value)
def general_input(msg, default_val):
    if DEBUG:
        print("returning " + default_val)
        return default_val
    return input(msg)

# Define a function for general password input (for debugging purposes - automatically fills in the default value)
def general_password_input(msg, default_val):
    if DEBUG:
        print("returning " + default_val)
        return default_val
    return getpass(msg)

# TODO - list of stocks

# Set the host and the port
HOST = socket.gethostname()
PORT = 5000

def get_and_send_username_and_password(client_socket):
    # Fill in personal details - username and password
    # Send them to the server
    server_public_key = load_server_public_key()  # Load the server's public key

    username = general_input("Enter your username: ", "ron")
    client_socket.send(encrypt_data(username, server_public_key))  # Encrypt and send username

    password = general_password_input("Enter your password: ", "10010")
    client_socket.send(encrypt_data(password, server_public_key))  # Encrypt and send password

    # Handle new user registration
    while True:
        # Receive the answer from the server
        result = decrypt_data(client_socket.recv(4096), load_client_private_key())  
        if result == '2':
            print("Username already exists. Please enter a new one.")
            username = general_input("Enter your username: ", "ron")
            client_socket.send(encrypt_data(username, server_public_key))

            password = general_password_input("Enter your password: ", "10010")
            client_socket.send(encrypt_data(password, server_public_key))
        elif result == '1':
            print(f"Welcome back {username}!")
            break
        else:
            print("Nice to meet you! You are now registered.")
            break
        

def initialize_client_balance(client_socket):
    # Check if client with these characteristics exists - the server sends the answer:
    # 1 if registered and 0 if not
    client_private_key = load_client_private_key()
    server_public_key = load_server_public_key()

    is_registered = decrypt_data(client_socket.recv(4096), client_private_key)

    if is_registered == '0':
        while True:
            try:
                balance = int(general_input("Please enter your balance: ", "10000"))
                break
            except ValueError:
                print("Invalid balance entered. Please enter a numeric value.")

        client_socket.send(encrypt_data(str(balance), server_public_key))
    else:
        current_balance = decrypt_data(client_socket.recv(4096), client_private_key)
        print(f"Your current balance: {current_balance}")    
  
def run_client():
    client_socket = socket.socket()
    client_socket.connect((HOST, PORT))

    get_and_send_username_and_password(client_socket)
    
    initialize_client_balance(client_socket)

    client_private_key = load_client_private_key()
    server_public_key = load_server_public_key()

    list_of_stocks = decrypt_data(client_socket.recv(4096), client_private_key)
    
    stock_symbol = general_input(f"Choose a stock from {list_of_stocks}: ", "AAPL").upper()

    while stock_symbol not in list_of_stocks:
        stock_symbol = general_input(f"Invalid stock. Choose from {list_of_stocks}: ", "AAPL").upper()
    
    client_socket.send(encrypt_data(stock_symbol, server_public_key))
    
    share_price = int(decrypt_data(client_socket.recv(4096), client_private_key))
    print(f"Current share price: {share_price}")
        
    # Listen to client's orders until he sends an empty message
    while True:
        while True:
            order = general_input("Enter your order (side$amount): ", "b$10")
            
            # Send the order to the server (even if it is empty)
            client_socket.send(encrypt_data(order, server_public_key) if order else encrypt_data(" ", server_public_key))

            # Receive feedback from the server about the order
            server_response = decrypt_data(client_socket.recv(4096), client_private_key)
            print(server_response)

            # If the server confirms the order is valid, break the loop
            if server_response == "Order recieved":
                break
        
        # Recieve the appropriate response from the server about the order
        response = decrypt_data(client_socket.recv(4096), client_private_key)
        print("im here")
        print(response)
        
        # Recieve the new share price from the server
        share_price = int(decrypt_data(client_socket.recv(4096), client_private_key))
        print(f"New share price: {share_price}")    
        
 
if __name__ == '__main__':
    run_client()