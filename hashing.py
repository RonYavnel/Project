import bcrypt
from db_tools import DB_Tools

tls = DB_Tools("stocktradingdb")

# Function to hash a password
def hash_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(str(password).encode(), salt)
    return hashed_password

def delete_row_in_table_with_specific_value(mydb, tableName, columnName, value):
    mycursor = mydb.cursor()
    sql = "DELETE FROM " + tableName + " WHERE " + columnName + " = %s"
    mycursor.execute(sql, (value,))
    mydb.commit()
    
def delete_all_rows_in_table(mydb, tableName):
    mycursor = mydb.cursor()
    sql = "DELETE FROM " + tableName
    mycursor.execute(sql)
    mydb.commit()
    
def insert_value_to_all_rows_in_table(mydb, tableName, columnName, value):
    mycursor = mydb.cursor()
    sql = "UPDATE " + tableName + " SET " + columnName + " = %s"
    mycursor.execute(sql, (value,))
    mydb.commit()

def change_ddos_status(mydb, ip, status):
    mycursor = mydb.cursor()
    sql = "UPDATE users SET ddos_status = %s WHERE username = %s"
    mycursor.execute(sql, (status, ip))
    mydb.commit()

def change_hashed_password(mydb, username, password):
    mycursor = mydb.cursor()
    hashed_password = tls.hash_data(username+password)
    sql = "UPDATE users SET hashed_password = %s WHERE username = %s"
    mycursor.execute(sql, (hashed_password, username))
    mydb.commit()

# change_ddos_status(tls.mydb, "slava", "accepted")
change_hashed_password(tls.mydb, "tal", "1234")