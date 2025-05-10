import mysql.connector
from datetime import *

class DB_Tools:
    def __init__(self, dbName, host="localhost", user="Ron Yavnel", password="2612"):
        self.host = host
        self.user = user
        self.password = password
        self.mydb = self.init_with_db(dbName) 
        
        
    # Function that gets a username and password and updates this user's current ip and port    
    def update_ip_and_port(self, conn, username, password):
        cursor = self.mydb.cursor()

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

        self.mydb.commit()
        cursor.close()


    # Initiate a connection with server without database
    def init_without_db(self):
        mydb = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )
        return mydb

    # Initiate a connection with server and with an existing database
    def init_with_db(self, dbName):
        mydb = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=dbName
        )
        return mydb

    # Function to show the databases
    def show_databases(self):
        mycursor = self.mydb.cursor()
        mycursor.execute("SHOW DATABASES")
        databases = []
        for i in mycursor:
            databases.append(i[0])
        return databases

    # Function to create a db in the database
    def create_new_database(self, dbName):
        mycursor = self.mydb.cursor()
        if dbName not in self.show_databases(self.mydb):
            mycursor.execute("CREATE DATABASE " + dbName)

    # Function to show tables in the database
    def show_tables(self):
        mycursor = self.mydb.cursor()
        mycursor.execute("SHOW TABLES")
        tables = []
        for i in mycursor:
            tables.append(i[0])
        return tables

    # Function to create a table in the database
    def create_table(self, tableName, params):
        tables = self.show_tables()
        mycursor = self.mydb.cursor()
        query = "CREATE TABLE " + tableName + " " + params
        if tableName not in tables:
            mycursor.execute(query)

    # Function to delete a table in given database
    def delete_table(self, tableName):
        tables = self.show_tables()
        mycursor = self.mydb.cursor()
        query = "DROP TABLE " + tableName
        print(query)
        if tableName in tables:
            mycursor.execute(query)

    # Function to insert new row to a table in database
    def insert_row(self, tableName, columnNames, columnTypes, columnValues):
        mycursor = self.mydb.cursor()
        tables = self.show_tables()
        if tableName in tables:
            sql = "INSERT INTO " + tableName + " " + columnNames + " VALUES " + columnTypes
            mycursor.execute(sql, columnValues)
            self.mydb.commit()
        else:
            print("No table exists with name " + tableName)

    # Function to delete a row in a table in database
    def delete_row(self, tableName, columnName, columnValue):
        mycursor = self.mydb.cursor()
        tables = self.show_tables()
        if tableName in tables:
            sql = "DELETE FROM " + tableName + " WHERE " + columnName + " =  '" + columnValue + "'"
            print(sql)
            mycursor.execute(sql)
            self.mydb.commit()
        else:
            print("No column name with name " + tableName)

    # Function to pull user_id by ip and port
    def get_user_id_by_ip_and_port(self, ip, port):
        mycursor = self.mydb.cursor()
        sql = "SELECT user_id FROM users WHERE ip = %s AND port = %s"
        mycursor.execute(sql, (ip, port))
        result = mycursor.fetchone()
        return result[0]

    # Function that returns all the rows of a table in a database
    def get_all_rows(self, tableName):
        
        # Initiate connections again for refresh
        mydb = self.init_with_db("stocktradingdb")
        
        mycursor = mydb.cursor()
        sql = "SELECT * FROM " + tableName
        mycursor.execute(sql)
        rows = []
        for i in mycursor:
            rows.append(i)
        return rows

    # Function that returns all the values of a specific column in a table
    def get_all_column_values(self, tableName, columnName):
        mycursor = self.mydb.cursor()
        sql = "SELECT " + columnName + " FROM " + tableName
        mycursor.execute(sql)
        rows = []
        for i in mycursor:
            rows.append(i[0])
        return rows

    # Function that gets all the rows from a table with condition (name of a column and its value)
    def get_rows_from_table_with_value(self, tableName, columnName, columnValue):
        mycursor = self.mydb.cursor()
        tables = self.show_tables()
        if tableName in tables:
            sql = "SELECT * FROM " + tableName + " WHERE " + columnName + " =  '" + columnValue + "'"
            print(sql)
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            return myresult
        else:
            print("No column name with name " + tableName)

    def fetchone_functions_tuple(self, query, my_tuple):
        cursor = self.mydb.cursor()
        cursor.execute(query, my_tuple)
        result = cursor.fetchone()
        cursor.close()
        return result[0]

    # Abstract function for handling "fetchone" type sql query functions with one parameter
    def fetchone_functions_one_param(self, query, param):
        return self.fetchone_functions_tuple(query, (param,))

    # Abstract function for handling "fetchone" type sql query functions with two parameters
    def fetchone_functions_two_params(self, query, param_a, param_b):
        return self.fetchone_functions_tuple(query, (param_a, param_b))

    # Abstract function for handling "commit" type sql query functions with three parameters
    def commit_functions_tuple(self, query, my_tuple):
        mycursor = self.mydb.cursor()
        mycursor.execute(query, my_tuple)
        self.mydb.commit()
        mycursor.close()

    # Abstract function for handling "commit" type sql query functions with one parameter
    def commit_functions_one_param(self, query, param_a):
        self.commit_functions_tuple( query, (param_a,))

    # Abstract function for handling "commit" type sql query functions with two parameters
    def commit_functions_two_params(self, query, param_a, param_b):
        self.commit_functions_tuple(query, (param_a, param_b))

    # Abstract function for handling "commit" type sql query functions with three parameters
    def commit_functions_three_params(self, query, param_a, param_b, param_c):
        self.commit_functions_tuple(query, (param_a, param_b, param_c))