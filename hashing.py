import bcrypt
from db_tools import DB_Tools

tls = DB_Tools()

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
    
mydb = tls.init_with_db("stocktradingdb")
delete_all_rows_in_table(mydb, "users")
