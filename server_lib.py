from db_tools import DB_Tools
from server_constants import *
from encryption_lib import Encryption
import time
from datetime import datetime

class Server_Lib:
    def __init__(self, server):
        self.server = server
        # Initialize the Encryption class
        self.e = Encryption()
        # Initialize the DB_Tools class
        self.tls = DB_Tools("stocktradingdb")

    # Function that handles a new connection
    def handle_user_connection(self, conn, received_data):
        try:
            # Receive and decrypt the username
            username, received_data = self.server.recv_data(conn, received_data)
            
            # Receive and decrypt the password, then hash it
            password, received_data = self.server.recv_data(conn, received_data)
            hashed_password = self.tls.hash_data(username+password)

            while True:
                if (not self.is_user_exists(username, hashed_password) and self.is_username_exists(username)): 
                    # If the user does not exist but there is a user with the same username
                    self.server.send_data(conn, "2")
                    
                    # Receive and decrypt the new username and password
                    username, received_data = self.server.recv_data(conn, received_data)
                    password, received_data = self.server.recv_data(conn, received_data)
                    hashed_password = self.tls.hash_data(password)
                
                elif (self.is_user_exists(username, hashed_password)):  # If the user exists
                    self.server.send_data(conn, "1")
                    break
                else:
                    self.server.send_data(conn, "0")
                    break
            
            return username, hashed_password, received_data

        except (ConnectionResetError, ConnectionAbortedError, ValueError, OSError):
            print("Client disconnected unexpectedly during user connection handling.")
            return None, None, ""

    # If user exists - update his ip, port and last_seen
    # If not exists - get balance from him and insert his details
    # Eventually, returns the balance of the client
    def handle_user_balance(self, conn, username, hashed_password, received_data):
        try:
            if self.is_user_exists(username, hashed_password):
                self.server.send_data(conn, "1")
                
                # Sends confirmation to the client
                balance = self.get_user_balance(username, hashed_password)  # Gets client's balance
                print(balance)
                self.tls.update_ip_and_port(conn, username, hashed_password)  # Updates IP and port
                self.update_last_seen(username, hashed_password)  # Updates last_seen
                time.sleep(0.1)
                self.server.send_data(conn, str(balance))  # Sends the client his balance

            else:
                self.server.send_data(conn, "0")
                # Sends confirmation to the client
                balance, received_data = self.server.recv_data(conn, received_data)  # Gets balance from the client
                balance = int(balance)  # Converts the balance to an integer
                self.tls.insert_row(    # Inserts the details of the new client into the database
                    "users", 
                    "(username, hashed_password, ip, port, last_seen, balance, ddos_status)", 
                    "(%s, %s, %s, %s, %s, %s, %s)",
                    (username, hashed_password, conn.getpeername()[0], conn.getpeername()[1], str(datetime.now()), balance, "accepted")
                )
            return balance, received_data  # Returns the balance of the client

        except (ConnectionResetError, ConnectionAbortedError, ValueError, OSError):
            print("Client disconnected unexpectedly during balance handling.")
            return None


    # Funtion that update all the data about the client and the share after transaction
    def update_all_data(self, conn, username, hashed_password, balance, side, amount, stock_symbol, share_price):
        self.update_last_seen(username, hashed_password) # Updates last_seen time of the client
        self.update_balance(username, hashed_password, balance) # Updates client's balance
        if side.upper() == "S":
            self.update_num_of_shares(stock_symbol, amount) # If shares are sold - add those shares to the num of free shares
        else:
            self.update_num_of_shares(stock_symbol, -amount) # If shares are bought - subtract this amount from the num of free shares
            self.update_shares_sold(stock_symbol, amount) # Add the new amount of sold shares to database
        self.update_current_price(stock_symbol, share_price) # Update the current price of a share after transaction
        if share_price > self.get_highest_share_price(stock_symbol): # Update the highest_share_price if needed
            self.update_highest_price(stock_symbol, share_price)
        if share_price < self.get_lowest_share_price(stock_symbol):  # Update the lowest_share_price if needed
            self.update_lowest_price(stock_symbol, share_price)
        self.server.send_data(conn, str(share_price)) # Send the updated share price to the client
        
                
    # Function that checks if username with given name and password exists
    def is_user_exists(self, username, hashed_password):
        return self.tls.fetchone_functions_two_params(
                                              "SELECT COUNT(*) FROM users WHERE username = %s AND hashed_password = %s",
                                              username,
                                              hashed_password) > 0
        
    # Function that checks if username with given name exists
    def is_username_exists(self, username):
        return self.tls.fetchone_functions_one_param(
                                            "SELECT COUNT(*) FROM users WHERE username = %s",
                                            username) > 0
        
    # Function that updates the "last_seen" value in the users table for now.
    def update_last_seen(self, username, hashed_password):
        self.tls.commit_functions_three_params(
                                      "UPDATE users SET Last_seen = %s WHERE username = %s AND hashed_password = %s",
                                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                      username,
                                      hashed_password)
        
    # Function that gets a username and hashed_password and updates his balance  
    def update_balance(self, username, hashed_password, new_balance):
        self.tls.commit_functions_three_params(
                                      "UPDATE users SET Balance = %s WHERE username = %s AND hashed_password = %s",
                                      new_balance,
                                      username,
                                      hashed_password)
        
    # Function that gets a username and hashed_password and returns this user's balance  
    def get_user_balance(self,  username, hashed_password):
        return self.tls.fetchone_functions_two_params( 
                                              "SELECT balance FROM users WHERE username = %s AND hashed_password = %s", 
                                              username, 
                                              hashed_password)

    # Function that gets a stock symbol and updates the pric of a single share
    def update_current_price(self, stock_symbol, new_price):
        self.tls.commit_functions_two_params(
                                    "UPDATE stocks SET current_price = %s WHERE symbol = %s",
                                    new_price,
                                    stock_symbol)
        
    # Function that gets a stock symbol and updates the share's highest_price to the new_highest_price
    def update_highest_price(self, stock_symbol, new_highest_price):
        self.tls.commit_functions_two_params(
                                    "UPDATE stocks SET highest_price = %s WHERE symbol = %s",
                                    new_highest_price,
                                    stock_symbol)
        
    # Function that gets a stock symbol and updates the share's lowest_price to the new_lowest_price
    def update_lowest_price(self, stock_symbol, new_lowest_price):
        self.tls.commit_functions_two_params( 
                                    "UPDATE stocks SET lowest_price = %s WHERE symbol = %s",
                                    new_lowest_price,
                                    stock_symbol)
        
    # Function that gets a stock symbol and returns the current price of a single share
    def get_current_share_price(self, stock_symbol):
        price = self.tls.fetchone_functions_one_param(
                                             "SELECT current_price FROM Stocks WHERE symbol = %s",
                                             stock_symbol)
        return int(price)
        
    # Function that gets a stock symbol and returns the highest price of a single share
    def get_highest_share_price(self, stock_symbol):
        return self.tls.fetchone_functions_one_param(
                                             "SELECT highest_price FROM Stocks WHERE symbol = %s",
                                             stock_symbol)

    # Function that gets a stock symbol and returns the lowest price of a single share
    def get_lowest_share_price(self, stock_symbol):
        return self.tls.fetchone_functions_one_param(
                                             "SELECT lowest_price FROM Stocks WHERE symbol = %s",
                                             stock_symbol)

    # Function that gets a stock symbol and adds the new amount of sold shares
    def update_shares_sold(self, stock_symbol, new_amount):
        self.tls.commit_functions_two_params(
                                    """ UPDATE Stocks SET shares_sold = shares_sold + %s WHERE symbol = %s """,
                                    new_amount,
                                    stock_symbol)
        
    # Function that get a stock symbol and updates the new number of free shares.
    # (new_amount can be positive while selling or negative while buying) 
    def update_num_of_shares(self, stock_symbol, new_amount):
        self.tls.commit_functions_two_params(
                                    """ UPDATE Stocks SET num_of_shares = num_of_shares + %s WHERE symbol = %s """,
                                    new_amount, 
                                    stock_symbol)
        

    # Function that gets a username and hashed_password and returns the client_id of the user  
    def get_client_id(self, username, hashed_password):
        return self.tls.fetchone_functions_two_params(
                                              "SELECT client_id FROM Users WHERE username = %s AND hashed_password = %s",
                                              username,
                                              hashed_password)

    def get_ddos_status(self, ip):
        return self.tls.fetchone_functions_one_param(
                                            "SELECT ddos_status FROM Users WHERE ip = %s",
                                            ip)
    
    def update_ddos_status(self, ip, status):
        self.tls.commit_functions_two_params(
                                              "UPDATE Users SET ddos_status = %s WHERE ip = %s",
                                              status,
                                              ip)
        
    def is_ip_exists(self, ip):
        return self.tls.fetchone_functions_one_param(
                                              "SELECT COUNT(*) FROM Users WHERE ip = %s",
                                              ip) > 0