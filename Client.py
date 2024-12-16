# Import the socket module for communication
import socket 

# Set the host and the port
HOST = socket.gethostname()
PORT = 5000

# Create a socket
client_socket = socket.socket()

# Connect the socket to the server (the server is local)
client_socket.connect((HOST, PORT))

# Fill in personal details - username and password
# Send them to the server
username = input("Enter your username: ")
client_socket.send(username.encode())

password = input("Enter your password: ")
client_socket.send(password.encode())

# Recieve the most updated
share_price = int(client_socket.recv(1024).decode())
print(f"Current share price: {share_price}")

# Check if client with this characteristics - the server sends the answer:
# 1 if registered and 0 if not
is_registered = client_socket.recv(1024).decode()

# If not registered, try and recieve the balance of the new client until it is valid
if (is_registered == '0'):
    while True:
        try:
            balance = int(input("Enter your balance: "))
            # If valid - break from the loop
            break
        except ValueError:
            print("Invalid balance entered. Please enter a digital value.")
        
    client_socket.send(str(balance).encode())
    
# If the client exists, present the balance to him and continue
else:
    current_balance = client_socket.recv(1024).decode()
    print(f"Your current balance: {current_balance}")    
    
# Listen to client's orders until he sends an empty message
while True:
    order = input("enter your order (side$amount): ")
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

