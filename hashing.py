import bcrypt
from db_tools import *

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
    
mydb = init_with_db("stocktradingdb")
delete_row_in_table_with_specific_value(mydb, "users", "username", "ron")
