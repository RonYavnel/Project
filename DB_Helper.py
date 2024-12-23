import mysql.connector
from datetime import *

# Initiate a connection with server without database
def init():
    mydb = mysql.connector.connect(
        host="localhost",
        user="Ron Yavnel",
        password="2612"
    )
    return mydb
  
# Initiate a connection with server and with an existing database  
def init_with_db(dbName):
    mydb = mysql.connector.connect(
        host="localhost",
        user="Ron Yavnel",
        password="2612",
        database=dbName
    )
    return mydb  
    
# Function to show the database
def show_databases(mydb):
    mycursor = mydb.cursor()
    mycursor.execute("SHOW DATABASES")
    databases = []
    for i in  mycursor:
        databases.append(i[0])
    return databases


# Function to create a db in the database
def create_new_database(mydb, dbName):
    
    mycursor = mydb.cursor()
    if dbName not in show_databases(mydb):
        mycursor.execute("CREATE DATABASE " + dbName)


# Function to show tables in the database
def show_tables(mydb):
    
    mycursor = mydb.cursor()
    mycursor.execute("SHOW TABLES")
    tables = []
    for i in  mycursor:
        tables.append(i[0])
    return tables       


# Function to create a table in the database
def create_table(mydb, tableName, params):
    tables = show_tables(mydb)
    mycursor = mydb.cursor()
    query = "CREATE TABLE " + tableName + " " + params
    print(query)
    if tableName not in  tables:
        mycursor.execute(query)

# Function to delete a table in given database
def delete_table(mydb, tableName):
    tables = show_tables(mydb)
    mycursor = mydb.cursor()
    query = "DROP TABLE " + tableName 
    print(query)
    if tableName in tables:
        mycursor.execute(query)

# Function to insert new row to a table in database
def insert_row(mydb, tableName, columnNames, columnTypes, columnValues):
    mycursor = mydb.cursor()
    tables = show_tables(mydb)
    if tableName in tables:
        sql = "INSERT INTO " + tableName + " "+ columnNames +" VALUES " + columnTypes
        mycursor.execute(sql, columnValues)
        mydb.commit()
    else:
        print("No table exists with name "+ tableName)

# Function to delete a row in a table in database
def delete_row(mydb, tableName, columnName, columnValue):
    mycursor = mydb.cursor()
    tables = show_tables(mydb)
    if tableName in tables:
        sql = "DELETE FROM " + tableName + " WHERE "+ columnName + " =  '" + columnValue + "'"
        print(sql)
        mycursor.execute(sql)
        mydb.commit()
    else:
        print("No column name with name "+ tableName)


# Function that returns all the rows of a table in a database
def get_all_rows(mydb, tableName):
    mycursor = mydb.cursor()
    sql = "SELECT * FROM " + tableName
    mycursor.execute(sql)
    rows = []
    print(mycursor)
    for i in mycursor:
        rows.append(i)
    return rows
    
# Function that gets all the rows from a table with condition (name of a column and its value)
def get_rows_from_table_with_value(mydb, tableName, columnName, columnValue):
    mycursor = mydb.cursor()
    tables = show_tables(mydb)
    if tableName in tables:
        sql = "SELECT * FROM " + tableName + " WHERE "+ columnName + " =  '" + columnValue + "'"
        print(sql)
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        return myresult
    else:
        print("No column name with name "+ tableName)
        
        
# Ron's adding 
# Abstract function for handling "fetchone" type sql query functions with one parameter
def fetchone_functions_one_param(mydb, query, param):
    cursor = mydb.cursor()

    cursor.execute(query, (param,))

    result = cursor.fetchone()
    
    cursor.close()

    return result[0]

# Abstract function for handling "fetchone" type sql query functions with two parameters
def fetchone_functions_two_params(mydb, query, param_a, param_b):
    cursor = mydb.cursor()

    cursor.execute(query, (param_a, param_b))

    result = cursor.fetchone()
    
    cursor.close()

    return result[0]

# Abstract function for handling "commit" type sql query functions with one parameter
def commit_functions_one_param(mydb, query, param_a):
    mycursor = mydb.cursor()

    mycursor.execute(query, (param_a, ))
        
    mydb.commit()
                
    mycursor.close()
    
    
# Abstract function for handling "commit" type sql query functions with two parameters
def commit_functions_two_params(mydb, query, param_a, param_b):
    mycursor = mydb.cursor()

    mycursor.execute(query, (param_a, param_b))
        
    mydb.commit()
                
    mycursor.close()
    
    
# Abstract function for handling "commit" type sql query functions with three parameters
def commit_functions_three_params(mydb, query, param_a, param_b, param_c):
    mycursor = mydb.cursor()

    mycursor.execute(query, (param_a, param_b, param_c))
        
    mydb.commit()
                
    mycursor.close()













# Function that checks if username with given name and password exists
def is_username_exists(mydb, username, password):
    
    return fetchone_functions_two_params(mydb,
                                          "SELECT COUNT(*) FROM users WHERE username = %s AND password = %s",
                                          username,
                                          password) > 0


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
                                          "SELECT balance FROM Users WHERE username = %s AND password = %s", 
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
