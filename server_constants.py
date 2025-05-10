import socket

# Saving the constant variables in a dedicated file
HOST = socket.gethostname()
PORT = 5000

MAX_CLIENTS = 10
MAX_CONNECTIONS_FROM_CLIENT = 3

DATA_DELIMITER = "$$$"
