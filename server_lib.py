from db_tools import *
from server_constants import *

# Function that handles a new connection
def handle_user_connection(conn):
    username = conn.recv(6).decode() # Get the username of the client
    password = conn.recv(6).decode() # Get the password of the client
    while True:
        if (not is_user_exists(DB_CONN, username, password) and is_username_exists(DB_CONN, username)): 
            # If the user not exists but there already is a user with such a username
            conn.send("2".encode())
            username = conn.recv(6).decode()
            password = conn.recv(6).decode()
        elif (is_user_exists(DB_CONN, username, password)): # If the user exists
            conn.send("1".encode())
            break
        else:
            conn.send("0".encode())
            break
    return username, password


# If user exists - update his ip, port and last_seen
# If not exists - get balance from him and insert his details
# Eventually, returns the balance of the client
def handle_user_balance(conn, username, password):
    if is_user_exists(DB_CONN, username, password):
        conn.send("1".encode()) # Sends confirmation to the client
        balance = get_user_balance(DB_CONN, username, password) # Gets clients balance
        update_ip_and_port(DB_CONN, conn, username, password) # Updates ip and port
        update_last_seen(DB_CONN, username, password) # Updates last_seen
        conn.send(str(balance).encode()) # Sends the cliet his balance
    else:
        conn.send("0".encode()) # Sends confirmation to the client
        balance = int(conn.recv(1024).decode()) # Gets from the client his balance
        insert_row(    # Inserts the details of the new client to the database
            DB_CONN, 
            "users", 
            "(username, password, ip, port, last_seen, balance)", 
            "(%s, %s, %s, %s, %s, %s)",
            (username, password, conn.getpeername()[0], conn.getpeername()[1], str(datetime.now()), balance)
        )
    return balance # Returns the balance of the client

# Funtion that update all the data about the client and the share after transaction
def update_all_data(conn, username, password, balance, side, amount, stock_symbol, share_price):
    update_last_seen(DB_CONN, username, password) # Updates last_seen time of the client
    update_balance(DB_CONN, username, password, balance) # Updates client's balance
    if side.upper() == "S":
        update_num_of_shares(DB_CONN, stock_symbol, amount) # If shares are sold - add those shares to the num of free shares
    else:
        update_num_of_shares(DB_CONN, stock_symbol, -amount) # If shares are bought - subtract this amount from the num of free shares
        update_shares_sold(DB_CONN, stock_symbol, amount) # Add the new amount of sold shares to database
    update_current_price(DB_CONN, stock_symbol, share_price) # Update the current price of a share after transaction
    if share_price > get_highest_share_price(DB_CONN, stock_symbol): # Update the highest_share_price if needed
        update_highest_price(DB_CONN, stock_symbol, share_price)
    if share_price < get_lowest_share_price(DB_CONN, stock_symbol):  # Update the lowest_share_price if needed
        update_lowest_price(DB_CONN, stock_symbol, share_price)
    conn.send(str(share_price).encode()) # Send the updated share price to the client


# Function that checks if username with given name and password exists
def is_user_exists(mydb, username, password):
    
    return fetchone_functions_two_params(mydb,
                                          "SELECT COUNT(*) FROM users WHERE username = %s AND password = %s",
                                          username,
                                          password) > 0
    
# Function that checks if username with given name exists
def is_username_exists(mydb, username):
    return fetchone_functions_one_param(mydb,
                                        "SELECT COUNT(*) FROM users WHERE username = %s",
                                        username) > 0
    
# Function that updates the "last_seen" value in the users table for now.
def update_last_seen(mydb, username, password):
    
    commit_functions_three_params(mydb,
                                  "UPDATE users SET Last_seen = %s WHERE username = %s AND password = %s",
                                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                  username,
                                  password)
    
    
# Function that gets a username and password and updates his balance  
def update_balance(mydb, username, password, new_balance):

    commit_functions_three_params(mydb,
                                  "UPDATE users SET Balance = %s WHERE username = %s AND password = %s",
                                  new_balance,
                                  username,
                                  password)
    

# Function that gets a username and password and returns this user's balance  
def get_user_balance(mydb, username, password):
    
    return fetchone_functions_two_params(mydb, 
                                          "SELECT balance FROM users WHERE username = %s AND password = %s", 
                                          username, 
                                          password)


# Function that gets a stock symbol and updates the pric of a single share
def update_current_price(mydb, stock_symbol, new_price):

    commit_functions_two_params(mydb,
                                "UPDATE stocks SET current_price = %s WHERE symbol = %s",
                                new_price,
                                stock_symbol)

    
# Function that gets a stock symbol and updates the share's highest_price to the new_highest_price
def update_highest_price(mydb, stock_symbol, new_highest_price):
    
    commit_functions_two_params(mydb,
                                "UPDATE stocks SET highest_price = %s WHERE symbol = %s",
                                new_highest_price,
                                stock_symbol)
    
    
# Function that gets a stock symbol and updates the share's lowest_price to the new_lowest_price
def update_lowest_price(mydb, stock_symbol, new_lowest_price):
    
    commit_functions_two_params(mydb, 
                                "UPDATE stocks SET lowest_price = %s WHERE symbol = %s",
                                new_lowest_price,
                                stock_symbol)

    
# Function that gets a stock symbol and returns the current price of a single share
def get_current_share_price(mydb, stock_symbol):
    
    return fetchone_functions_one_param(mydb,
                                         "SELECT current_price FROM Stocks WHERE symbol = %s",
                                         stock_symbol)
    
    
# Function that gets a stock symbol and returns the highest price of a single share
def get_highest_share_price(mydb, stock_symbol):
    
    return fetchone_functions_one_param(mydb,
                                         "SELECT highest_price FROM Stocks WHERE symbol = %s",
                                         stock_symbol)


# Function that gets a stock symbol and returns the lowest price of a single share
def get_lowest_share_price(mydb, stock_symbol):
    
    return fetchone_functions_one_param(mydb,
                                         "SELECT lowest_price FROM Stocks WHERE symbol = %s",
                                         stock_symbol)



# Function that gets a stock symbol and adds the new amount of sold shares
def update_shares_sold(mydb, stock_symbol, new_amount):
    
    commit_functions_two_params(mydb,
                                """ UPDATE Stocks SET shares_sold = shares_sold + %s WHERE symbol = %s """,
                                new_amount,
                                stock_symbol)
    
    
# Function that get a stock symbol and updates the new number of free shares.
# (new_amount can be positive while selling or negative while buying) 
def update_num_of_shares(mydb, stock_symbol, new_amount):
    
    commit_functions_two_params(mydb,
                                """ UPDATE Stocks SET num_of_shares = num_of_shares + %s WHERE symbol = %s """,
                                new_amount, 
                                stock_symbol)
    

    
# Function that gets a username and password and updates this user's current ip and port
def update_ip_and_port(mydb, conn, username, password):
    
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
def get_client_id(mydb, username, password):
    
    return fetchone_functions_two_params(mydb,
                                          "SELECT client_id FROM Users WHERE username = %s AND password = %s",
                                          username,
                                          password)
