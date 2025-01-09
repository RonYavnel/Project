# Import the socket module for communication
import socket 
from getpass import getpass
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

# TODO - 2 : save hash of passw and compare to hash of entered
# TODO --- mutex lock for "space"
# TODO - list of stocks


# Set the host and the port
HOST = socket.gethostname()
PORT = 5000

def get_and_send_username_and_password(client_socket):
    # Fill in personal details - username and password
    # Send them to the server
    username = general_input("Enter your username: ", "ron  ")
    client_socket.send(username.encode())

    password = general_password_input("Enter your password: ", "10010")
    client_socket.send(password.encode())
    
    # Handle new user registration
    while True:
        # Recieve the answer from the server:
        result = client_socket.recv(6).decode() 
        if ( result == '2'):
            # 2 if the username already exists
            print("Username already exists. Please enter a new one.")
            username = general_input("Enter your username: ", "ron  ")
            client_socket.send(username.encode())
            password = general_password_input("Enter your password: ", "10010")
            client_socket.send(password.encode())
        elif (result == '1'):
            # 1 if the user is registered
            print(f"Welcome back {username}!")
            break
        else:
            # 0 if the user is not registered
            print("Nice to meet you! You are now registered.")
            break
        

def initialize_client_balance(client_socket):
    
    # Check if client with this characteristics - the server sends the answer:
    # 1 if registered and 0 if not
    is_registered = client_socket.recv(1024).decode()
    # If not registered, try and recieve the balance of the new client until it is valid
    if (is_registered == '0'):
        while True:
            try:
                balance = int(general_input("Please enter your balance: ", "10000"))
                # If valid - break from the loop
                break
            except ValueError:
                print("Invalid balance entered. Please enter a digital value.")
            
        client_socket.send(str(balance).encode())
        
    # If the client exists, present the balance to him and continue
    else:
        current_balance = client_socket.recv(1024).decode()
        print(f"Your current balance: {current_balance}")    
  
  
def run_client():
    # Create a socket
    client_socket = socket.socket()

    # Connect the socket to the server (the server is local)
    client_socket.connect((HOST, PORT))

    get_and_send_username_and_password(client_socket)
    if DEBUG:
        print(f"moooooooooo")

    initialize_client_balance(client_socket)
              
    list_of_stocks = client_socket.recv(1024).decode()
    
    stock_symbol = general_input(f"Choose a stock from the following list: {list_of_stocks}: ", "AAPL")
    while stock_symbol not in list_of_stocks:
        stock_symbol = general_input(f"Invalid stock symbol. Choose a stock from the following list: {list_of_stocks}", "AAPL")
    
    client_socket.send(stock_symbol.encode())
    # Recieve the most updated share price from the server
    share_price = int(client_socket.recv(1024).decode())
    if not DEBUG:
        print(f"Current share price: {share_price}")
        
        
    # Listen to client's orders until he sends an empty message
    while True:
        order = general_input("enter your order (side$amount): ", "b$10")
        client_socket.send(order.encode())
        if order == '':
            client_socket.close()
            break
        
        # Recieve the appropriate response from the server about the order
        response = client_socket.recv(1024).decode()
        print(response)
        
        # Recieve the updated share price from the server
        share_price = int(client_socket.recv(1024).decode())
        print(f"New share price: {share_price}")   
 
if __name__ == '__main__':
    run_client()
