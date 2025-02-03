from db_tools import *

def delete_all_rows_in_table(mydb, tableName):
    mycursor = mydb.cursor()
    sql = "DELETE FROM " + tableName
    mycursor.execute(sql)
    mydb.commit()
    
mydb = init_with_db("stocktradingdb")
delete_all_rows_in_table(mydb, "users")