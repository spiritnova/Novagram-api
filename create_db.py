import mysql.connector

mydb = mysql.connector.connect(
    host="sql7.freemysqlhosting.net",
    user="sql7600856",
    passwd="2KGKqCNgfD",
)
db = mydb.cursor()

db.execute("SHOW DATABASES")

for dbs in db:
    print(dbs)