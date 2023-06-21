import mysql.connector

mydb = mysql.connector.connect(
    host="sql8.freemysqlhosting.net",
    user="sql8627639",
    passwd="2TS2rCxmsT",
)
db = mydb.cursor()

db.execute("SHOW DATABASES")

for dbs in db:
    print(dbs)
