import mysql.connector
from datetime import *

def init():
    mydb = mysql.connector.connect(
        host="localhost",
        user="Ron Yavnel",
        password="2612"
    )
    return mydb
  
  
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
# Pay Attention: expected format of params is :
#               (name VARCHAR(255), address VARCHAR(255))")
# also NOTICE that you need to have a COUPLE of () around params
def create_table(mydb, tableName, params):
    tables = show_tables(mydb)
    mycursor = mydb.cursor()
    query = "CREATE TABLE " + tableName + " " + params
    print(query)
    if tableName not in  tables:
        mycursor.execute(query)

def delete_table(mydb, tableName):
    tables = show_tables(mydb)
    mycursor = mydb.cursor()
    query = "DROP TABLE " + tableName 
    print(query)
    if tableName in tables:
        mycursor.execute(query)


def insert_row(mydb, tableName, columnNames, columnTypes, columnValues):
    mycursor = mydb.cursor()
    tables = show_tables(mydb)
    if tableName in tables:
        sql = "INSERT INTO " + tableName + " "+ columnNames +" VALUES " + columnTypes
        mycursor.execute(sql, columnValues)
        mydb.commit()
    else:
        print("No table exists with name "+ tableName)

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



def get_all_rows(mydb, tableName):
    mycursor = mydb.cursor()
    sql = "SELECT * FROM " + tableName
    mycursor.execute(sql)
    rows = []
    print(mycursor)
    for i in mycursor:
        rows.append(i)
    return rows
    
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
        
        
# ron's adding 

def is_username_exists(mydb, username, password):
    cursor = mydb.cursor()
    
    query = "SELECT COUNT(*) FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    
    result = cursor.fetchone()
    
    cursor.close()
    
    return result[0] > 0


def update_last_seen(mydb, username, password):
    mycursor = mydb.cursor()

    last_seen = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    query = "UPDATE users SET Last_seen = %s WHERE username = %s AND password = %s"

    mycursor.execute(query, (last_seen, username, password))
        
    mydb.commit()
                
    mycursor.close()
    
    
    
def update_balance(mydb, username, password, new_balance):

    mycursor = mydb.cursor()

    query = "UPDATE users SET Balance = %s WHERE username = %s AND password = %s"

    mycursor.execute(query, (new_balance, username, password))
    
    mydb.commit()

    mycursor.close()
    
    
def get_user_balance(mydb, username, password):
    cursor = mydb.cursor()

    query = "SELECT Balance FROM Users WHERE username = %s AND password = %s"

    cursor.execute(query, (username, password))

    result = cursor.fetchone()
    
    cursor.close()

    return result[0]


def update_current_price(mydb, stock_symbol, new_price):

    mycursor = mydb.cursor()

    query = "UPDATE stocks SET current_price = %s WHERE symbol = %s"

    mycursor.execute(query, (new_price, stock_symbol))
    
    mydb.commit()

    mycursor.close()
    
def update_highest_price(mydb, stock_symbol, new_highest_price):

    mycursor = mydb.cursor()

    query = "UPDATE stocks SET highest_price = %s WHERE symbol = %s"

    mycursor.execute(query, (new_highest_price, stock_symbol))
    
    mydb.commit()

    mycursor.close()
    
    
def update_lowest_price(mydb, stock_symbol, new_lowest_price):

    mycursor = mydb.cursor()

    query = "UPDATE stocks SET lowest_price = %s WHERE symbol = %s"

    mycursor.execute(query, (new_lowest_price, stock_symbol))
    
    mydb.commit()

    mycursor.close()
    
def get_current_share_price(db_conn, stock_symbol):
    
    cursor = db_conn.cursor()

    query = "SELECT current_price FROM Stocks WHERE symbol = %s"

    cursor.execute(query, (stock_symbol,))

    result = cursor.fetchone()
    
    cursor.close()

    return result[0]
    
def get_highest_share_price(mydb, stock_symbol):
    
    cursor = mydb.cursor()

    query = "SELECT highest_price FROM Stocks WHERE symbol = %s"

    cursor.execute(query, (stock_symbol,))

    result = cursor.fetchone()
    
    cursor.close()

    return result[0]


def get_lowest_share_price(mydb, stock_symbol):
    
    cursor = mydb.cursor()

    query = "SELECT lowest_price FROM Stocks WHERE symbol = %s"

    cursor.execute(query, (stock_symbol,))

    result = cursor.fetchone()
    
    cursor.close()

    return result[0]



def update_shares_sold(db_conn, stock_symbol, new_amount):
    
    cursor = db_conn.cursor()

    query = """
        UPDATE Stocks
        SET shares_sold = shares_sold + %s
        WHERE symbol = %s
    """

    cursor.execute(query, (new_amount, stock_symbol))

    db_conn.commit()

    cursor.close()
    

def update_num_of_shares(db_conn, stock_symbol, new_amount):
    
    cursor = db_conn.cursor()

    query = """
        UPDATE Stocks
        SET num_of_shares = num_of_shares + %s
        WHERE symbol = %s
    """

    cursor.execute(query, (new_amount, stock_symbol))

    db_conn.commit()

    cursor.close()
    

def update_ip_and_port(db_conn, conn, username, password):
    
    cursor = db_conn.cursor()

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

    db_conn.commit()

    cursor.close()
    
def get_client_id(db_conn, username, password):
    
    cursor = db_conn.cursor()

    query = "SELECT client_id FROM Users WHERE username = %s AND password = %s"

    cursor.execute(query, (username, password))

    result = cursor.fetchone()
    
    cursor.close()

    return result[0]