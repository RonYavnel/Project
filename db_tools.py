import mysql.connector
from datetime import *

class DB_Tools:
    def __init__(self, host="localhost", user="Ron Yavnel", password="2612"):
        self.host = host
        self.user = user
        self.password = password

    # Initiate a connection with server without database
    def init(self):
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
    def show_databases(self, mydb):
        mycursor = mydb.cursor()
        mycursor.execute("SHOW DATABASES")
        databases = []
        for i in mycursor:
            databases.append(i[0])
        return databases

    # Function to create a db in the database
    def create_new_database(self, mydb, dbName):
        mycursor = mydb.cursor()
        if dbName not in self.show_databases(mydb):
            mycursor.execute("CREATE DATABASE " + dbName)

    # Function to show tables in the database
    def show_tables(self, mydb):
        mycursor = mydb.cursor()
        mycursor.execute("SHOW TABLES")
        tables = []
        for i in mycursor:
            tables.append(i[0])
        return tables

    # Function to create a table in the database
    def create_table(self, mydb, tableName, params):
        tables = self.show_tables(mydb)
        mycursor = mydb.cursor()
        query = "CREATE TABLE " + tableName + " " + params
        if tableName not in tables:
            mycursor.execute(query)

    # Function to delete a table in given database
    def delete_table(self, mydb, tableName):
        tables = self.show_tables(mydb)
        mycursor = mydb.cursor()
        query = "DROP TABLE " + tableName
        print(query)
        if tableName in tables:
            mycursor.execute(query)

    # Function to insert new row to a table in database
    def insert_row(self, mydb, tableName, columnNames, columnTypes, columnValues):
        mycursor = mydb.cursor()
        tables = self.show_tables(mydb)
        if tableName in tables:
            sql = "INSERT INTO " + tableName + " " + columnNames + " VALUES " + columnTypes
            mycursor.execute(sql, columnValues)
            mydb.commit()
        else:
            print("No table exists with name " + tableName)

    # Function to delete a row in a table in database
    def delete_row(self, mydb, tableName, columnName, columnValue):
        mycursor = mydb.cursor()
        tables = self.show_tables(mydb)
        if tableName in tables:
            sql = "DELETE FROM " + tableName + " WHERE " + columnName + " =  '" + columnValue + "'"
            print(sql)
            mycursor.execute(sql)
            mydb.commit()
        else:
            print("No column name with name " + tableName)

    def get_user_id_by_ip_and_port(self, mydb, ip, port):
        mycursor = mydb.cursor()
        sql = "SELECT user_id FROM users WHERE ip = %s AND port = %s"
        mycursor.execute(sql, (ip, port))
        result = mycursor.fetchone()
        return result[0]

    # Function that returns all the rows of a table in a database
    def get_all_rows(self, mydb, tableName):
        mycursor = mydb.cursor()
        sql = "SELECT * FROM " + tableName
        mycursor.execute(sql)
        rows = []
        for i in mycursor:
            rows.append(i)
        return rows

    def get_all_column_values(self, mydb, tableName, columnName):
        mycursor = mydb.cursor()
        sql = "SELECT " + columnName + " FROM " + tableName
        mycursor.execute(sql)
        rows = []
        for i in mycursor:
            rows.append(i[0])
        return rows

    # Function that gets all the rows from a table with condition (name of a column and its value)
    def get_rows_from_table_with_value(self, mydb, tableName, columnName, columnValue):
        mycursor = mydb.cursor()
        tables = self.show_tables(mydb)
        if tableName in tables:
            sql = "SELECT * FROM " + tableName + " WHERE " + columnName + " =  '" + columnValue + "'"
            print(sql)
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            return myresult
        else:
            print("No column name with name " + tableName)

    def fetchone_functions_tuple(self, mydb, query, my_tuple):
        cursor = mydb.cursor()
        cursor.execute(query, my_tuple)
        result = cursor.fetchone()
        cursor.close()
        return result[0]

    # Ron's adding
    # Abstract function for handling "fetchone" type sql query functions with one parameter
    def fetchone_functions_one_param(self, mydb, query, param):
        return self.fetchone_functions_tuple(mydb, query, (param,))

    # Abstract function for handling "fetchone" type sql query functions with two parameters
    def fetchone_functions_two_params(self, mydb, query, param_a, param_b):
        return self.fetchone_functions_tuple(mydb, query, (param_a, param_b))

    # Abstract function for handling "commit" type sql query functions with three parameters
    def commit_functions_tuple(self, mydb, query, my_tuple):
        mycursor = mydb.cursor()
        mycursor.execute(query, my_tuple)
        mydb.commit()
        mycursor.close()

    # Abstract function for handling "commit" type sql query functions with one parameter
    def commit_functions_one_param(self, mydb, query, param_a):
        self.commit_functions_tuple(mydb, query, (param_a,))

    # Abstract function for handling "commit" type sql query functions with two parameters
    def commit_functions_two_params(self, mydb, query, param_a, param_b):
        self.commit_functions_tuple(mydb, query, (param_a, param_b))

    # Abstract function for handling "commit" type sql query functions with three parameters
    def commit_functions_three_params(self, mydb, query, param_a, param_b, param_c):
        self.commit_functions_tuple(mydb, query, (param_a, param_b, param_c))