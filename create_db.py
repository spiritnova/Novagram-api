import mysql.connector

mydb = mysql.connector.connect(
    host="160.153.129.209",
    user="bobroot",
    password="zYrpG*q~#E0$",
    port = 3306
)
db = mydb.cursor()

db.execute("SHOW DATABASES")

for dbs in db:
    print(dbs)
