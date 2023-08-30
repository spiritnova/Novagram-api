import mysql.connector

mydb = mysql.connector.connect(
    host="bfyhrjhms04ghqi87jah-mysql.services.clever-cloud.com",
    user="ui6rpmktcf0dxwqu",
    password="rqAGgYZgfErNY9x43zg7",
    port = 3306
)
db = mydb.cursor()

db.execute("SHOW DATABASES")

for dbs in db:
    print(dbs)
