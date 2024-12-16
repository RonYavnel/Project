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
name = input("Enter your name: ")
client_socket.send(name.encode())

password = input("Enter your password: ")
client_socket.send(password.encode())

share_price = int(client_socket.recv(1024).decode())
print(f"Current share price: {share_price}")

is_registered = client_socket.recv(1024).decode()
if (is_registered == '0'):
    while True:
        try:
            balance = int(input("Enter your balance: "))
            break
        except ValueError:
            print("Invalid balance entered. Please enter a digital value.")
        
    client_socket.send(str(balance).encode())
    
else:
    current_balance = client_socket.recv(1024).decode()
    print(f"Your current balance: {current_balance}")    
    
while True:
    order = input("enter your order (side$amount): ")
    client_socket.send(order.encode())
    if order == '':
        client_socket.close()
        break
    
    response = client_socket.recv(1024).decode()
    print(response)
    
    share_price = int(client_socket.recv(1024).decode())
    print(f"New share price: {share_price}")    

