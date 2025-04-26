from db_tools import DB_Tools
import datetime

tls = DB_Tools("stocktradingdb")

def insert_to_table_from_list_of_tuples(table_name, list_of_tuples):
    # Create a connection to the database
    mydb = tls.init_with_db("stocktradingdb")
    
    # Create a cursor object to execute SQL queries
    mycursor = mydb.cursor()
    
    # Prepare the SQL query to insert data into the table
    sql = f"INSERT INTO {table_name} (company_name, symbol, stock_id, shares_sold, num_of_shares, current_price, highest_price, lowest_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    
    # Execute the SQL query for each tuple in the list
    for row in list_of_tuples:
        mycursor.execute(sql, row)
    
    # Commit the changes to the database
    mydb.commit()
    
    # Close the cursor and connection
    mycursor.close()
    mydb.close()

insert_to_table_from_list_of_tuples("stocks", [('Apple', 'AAPL', 1, 500, 49500, 340, 4001, 1), ('Google', 'GOOGL', 2, 550, 49880, 116, 450, 63)])