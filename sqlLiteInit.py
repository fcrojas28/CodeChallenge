import sqlite3 as lite
import datetime

usersList = (
    ('fcrojas28',datetime.datetime.now(), "granted"),
    ('limemodo',datetime.datetime.now(), "denied")
)

con = lite.connect('users.db')

with con :
    db = con.cursor()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("CREATE TABLE users(username TEXT, dt timestamp, access TEXT)")
    db.executemany("INSERT INTO users VALUES(?,?,?)",usersList)