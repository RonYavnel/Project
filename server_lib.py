from db_tools import DB_Tools
from server_constants import *
from encryption_lib import Encryption
import time
from datetime import datetime

class Server_Lib:
    def __init__(self):
        # Initialize the Encryption class
        self.e = Encryption()
        # Initialize the DB_Tools class
        self.tls = DB_Tools()

    # Function that handles a new connection
    def handle_user_connection(self, mydb, conn, server_private_key, client_public_key):
        # Receive and decrypt the username
        username = self.e.decrypt_data(conn.recv(4096), server_private_key)
        
        # Receive and decrypt the password, then hash it
        hashed_password = self.e.hash_data(self.e.decrypt_data(conn.recv(4096), server_private_key))

        while True:
            if (not self.is_user_exists(mydb, username, hashed_password) and self.is_username_exists(mydb, username)): 
                # If the user does not exist but there is a user with the same username
                conn.send(self.e.encrypt_data("2", client_public_key))
                
                # Receive and decrypt the new username and password
                username = self.e.decrypt_data(conn.recv(4096), server_private_key)
                hashed_password = self.e.hash_data(self.e.decrypt_data(conn.recv(4096), server_private_key))
            
            elif (self.is_user_exists(mydb, username, hashed_password)):  # If the user exists
                conn.send(self.e.encrypt_data("1", client_public_key))
                break
            else:
                conn.send(self.e.encrypt_data("0", client_public_key))
                break
        
        return username, hashed_password

    # If user exists - update his ip, port and last_seen
    # If not exists - get balance from him and insert his details
    # Eventually, returns the balance of the client
    def handle_user_balance(self, mydb, conn, username, password, server_private_key, client_public_key):
        if self.is_user_exists(mydb, username, password):
            conn.send(self.e.encrypt_data("1", client_public_key))
            
            # Sends confirmation to the client
            balance = self.get_user_balance(mydb, username, password)  # Gets client's balance
            print(balance)
            self.update_ip_and_port(mydb, conn, username, password)  # Updates IP and port
            self.update_last_seen(mydb, username, password)  # Updates last_seen
            time.sleep(0.1)
            conn.send(self.e.encrypt_data(str(balance), client_public_key))  # Sends the client his balance

        else:
            conn.send(self.e.encrypt_data("0", client_public_key))
            # Sends confirmation to the client
            balance = int(self.e.decrypt_data(conn.recv(4096), server_private_key))  # Gets balance from the client
            self.tls.insert_row(    # Inserts the details of the new client into the database
                mydb, 
                "users", 
                "(username, password, ip, port, last_seen, balance)", 
                "(%s, %s, %s, %s, %s, %s)",
                (username, password, conn.getpeername()[0], conn.getpeername()[1], str(datetime.now()), balance)
            )
        return balance  # Returns the balance of the client

    # Funtion that update all the data about the client and the share after transaction
    def update_all_data(self, mydb, conn, username, password, balance, side, amount, stock_symbol, share_price, client_public_key):
        self.update_last_seen(mydb, username, password) # Updates last_seen time of the client
        self.update_balance(mydb, username, password, balance) # Updates client's balance
        if side.upper() == "S":
            self.update_num_of_shares(mydb, stock_symbol, amount) # If shares are sold - add those shares to the num of free shares
        else:
            self.update_num_of_shares(mydb, stock_symbol, -amount) # If shares are bought - subtract this amount from the num of free shares
            self.update_shares_sold(mydb, stock_symbol, amount) # Add the new amount of sold shares to database
        self.update_current_price(mydb, stock_symbol, share_price) # Update the current price of a share after transaction
        if share_price > self.get_highest_share_price(mydb, stock_symbol): # Update the highest_share_price if needed
            self.update_highest_price(mydb, stock_symbol, share_price)
        if share_price < self.get_lowest_share_price(mydb, stock_symbol):  # Update the lowest_share_price if needed
            self.update_lowest_price(mydb, stock_symbol, share_price)
        conn.send(self.e.encrypt_data(str(share_price), client_public_key)) # Send the updated share price to the client

    # Function that checks if username with given name and password exists
    def is_user_exists(self, mydb, username, password):
        return self.tls.fetchone_functions_two_params(mydb,
                                              "SELECT COUNT(*) FROM users WHERE username = %s AND password = %s",
                                              username,
                                              password) > 0
        
    # Function that checks if username with given name exists
    def is_username_exists(self, mydb, username):
        return self.tls.fetchone_functions_one_param(mydb,
                                            "SELECT COUNT(*) FROM users WHERE username = %s",
                                            username) > 0
        
    # Function that updates the "last_seen" value in the users table for now.
    def update_last_seen(self, mydb, username, password):
        self.tls.commit_functions_three_params(mydb,
                                      "UPDATE users SET Last_seen = %s WHERE username = %s AND password = %s",
                                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                      username,
                                      password)
        
    # Function that gets a username and password and updates his balance  
    def update_balance(self, mydb, username, password, new_balance):
        self.tls.commit_functions_three_params(mydb,
                                      "UPDATE users SET Balance = %s WHERE username = %s AND password = %s",
                                      new_balance,
                                      username,
                                      password)
        
    # Function that gets a username and password and returns this user's balance  
    def get_user_balance(self, mydb, username, password):
        return self.tls.fetchone_functions_two_params(mydb, 
                                              "SELECT balance FROM users WHERE username = %s AND password = %s", 
                                              username, 
                                              password)

    # Function that gets a stock symbol and updates the pric of a single share
    def update_current_price(self, mydb, stock_symbol, new_price):
        self.tls.commit_functions_two_params(mydb,
                                    "UPDATE stocks SET current_price = %s WHERE symbol = %s",
                                    new_price,
                                    stock_symbol)
        
    # Function that gets a stock symbol and updates the share's highest_price to the new_highest_price
    def update_highest_price(self, mydb, stock_symbol, new_highest_price):
        self.tls.commit_functions_two_params(mydb,
                                    "UPDATE stocks SET highest_price = %s WHERE symbol = %s",
                                    new_highest_price,
                                    stock_symbol)
        
    # Function that gets a stock symbol and updates the share's lowest_price to the new_lowest_price
    def update_lowest_price(self, mydb, stock_symbol, new_lowest_price):
        self.tls.commit_functions_two_params(mydb, 
                                    "UPDATE stocks SET lowest_price = %s WHERE symbol = %s",
                                    new_lowest_price,
                                    stock_symbol)
        
    # Function that gets a stock symbol and returns the current price of a single share
    def get_current_share_price(self, mydb, stock_symbol):
        return self.tls.fetchone_functions_one_param(mydb,
                                             "SELECT current_price FROM Stocks WHERE symbol = %s",
                                             stock_symbol)
        
    # Function that gets a stock symbol and returns the highest price of a single share
    def get_highest_share_price(self, mydb, stock_symbol):
        return self.tls.fetchone_functions_one_param(mydb,
                                             "SELECT highest_price FROM Stocks WHERE symbol = %s",
                                             stock_symbol)

    # Function that gets a stock symbol and returns the lowest price of a single share
    def get_lowest_share_price(self, mydb, stock_symbol):
        return self.tls.fetchone_functions_one_param(mydb,
                                             "SELECT lowest_price FROM Stocks WHERE symbol = %s",
                                             stock_symbol)

    # Function that gets a stock symbol and adds the new amount of sold shares
    def update_shares_sold(self, mydb, stock_symbol, new_amount):
        self.tls.commit_functions_two_params(mydb,
                                    """ UPDATE Stocks SET shares_sold = shares_sold + %s WHERE symbol = %s """,
                                    new_amount,
                                    stock_symbol)
        
    # Function that get a stock symbol and updates the new number of free shares.
    # (new_amount can be positive while selling or negative while buying) 
    def update_num_of_shares(self, mydb, stock_symbol, new_amount):
        self.tls.commit_functions_two_params(mydb,
                                    """ UPDATE Stocks SET num_of_shares = num_of_shares + %s WHERE symbol = %s """,
                                    new_amount, 
                                    stock_symbol)
        
    # Function that gets a username and password and updates this user's current ip and port
    def update_ip_and_port(self, mydb, conn, username, password):
        cursor = mydb.cursor()

        query = """
            UPDATE Users
            SET ip = %s
            WHERE username = %s AND password = %s
        """
        cursor.execute(query, (conn.getpeername()[0], username, password))

        query = """
            UPDATE Users
            SET port = %s
            WHERE username = %s AND password = %s
        """
        cursor.execute(query, (conn.getpeername()[1], username, password))

        mydb.commit()
        cursor.close()
    
    # Function that gets a username and password and returns the client_id of the user  
    def get_client_id(self, mydb, username, password):
        return self.tls.fetchone_functions_two_params(mydb,
                                              "SELECT client_id FROM Users WHERE username = %s AND password = %s",
                                              username,
                                              password)
