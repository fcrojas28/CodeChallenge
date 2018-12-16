import sqlite3 as lite

con = lite.connect('users.db')

with con :
    db = con.cursor()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("CREATE TABLE users(username TEXT, dt timestamp, access TEXT)")