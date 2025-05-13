import socket


SERVER_IP = socket.gethostname()  
PORT = 5000

MAX_CLIENTS = 10
MAX_CONNECTIONS_FROM_CLIENT = 3

# Delimiter for data packets
DATA_DELIMITER = "$$$"
