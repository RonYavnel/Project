import socket

HOST = socket.gethostname()
PORT = 5000

client_socket = socket.socket()

client_socket.connect((HOST, PORT))

name = input("Enter your name: ")
client_socket.send(name.encode())

user_id = input("Enter your user id: ")
client_socket.send(user_id.encode())

share_price = int(client_socket.recv(1024).decode())
print(f"Current share price: {share_price}")

while True:
    try:
        balance = int(input("enter your balance: "))
        break
    except ValueError:
        print("Invalid balance entered. Please enter a digital value.")
        
client_socket.send(str(balance).encode())
while True:
    order = input("enter your order (side$amount): ")
    client_socket.send(order.encode())
    if order == '':
        client_socket.close()
        break
    
    response = client_socket.recv(1024).decode()
    print(response)
    
    share_price = int(client_socket.recv(1024).decode())
    print(f"Updated share price: {share_price}")    

