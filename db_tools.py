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
    for i in mycursor:
        rows.append(i)
    return rows
    
def get_all_column_values(mydb, tableName, columnName):
    mycursor = mydb.cursor()
    sql = "SELECT " + columnName + " FROM " + tableName
    mycursor.execute(sql)
    rows = []
    for i in mycursor:
        rows.append(i[0])
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
        
def fetchone_functions_tuple(mydb, query, my_tuple):
    cursor = mydb.cursor()
    cursor.execute(query,my_tuple)
    result = cursor.fetchone()
    cursor.close()
    return result[0]
       
# Ron's adding 
# Abstract function for handling "fetchone" type sql query functions with one parameter
def fetchone_functions_one_param(mydb, query, param):
    return fetchone_functions_tuple(mydb, query, (param,))

# Abstract function for handling "fetchone" type sql query functions with two parameters
def fetchone_functions_two_params(mydb, query, param_a, param_b):
    return fetchone_functions_tuple(mydb, query, (param_a, param_b))

# Abstract function for handling "commit" type sql query functions with three parameters
def commit_functions_tuple(mydb, query, my_tuple):
    mycursor = mydb.cursor()
    mycursor.execute(query, my_tuple)
    mydb.commit()           
    mycursor.close()

# Abstract function for handling "commit" type sql query functions with one parameter
def commit_functions_one_param(mydb, query, param_a):
    commit_functions_tuple(mydb, query, (param_a, ))
    
    
# Abstract function for handling "commit" type sql query functions with two parameters
def commit_functions_two_params(mydb, query, param_a, param_b):
    commit_functions_tuple(mydb, query, (param_a, param_b))
    
    
# Abstract function for handling "commit" type sql query functions with three parameters
def commit_functions_three_params(mydb, query, param_a, param_b, param_c):
    commit_functions_tuple(mydb, query, (param_a, param_b, param_c))
