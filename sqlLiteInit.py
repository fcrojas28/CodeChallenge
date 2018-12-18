import sqlite3 as lite

con = lite.connect('users.db')

with con :
    db = con.cursor()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("CREATE TABLE users(username TEXT, auth_req_id TEXT, dt timestamp, access TEXT, webhook_acess_granted_dt timestamp, webhook_acess_denied_dt timestamp)")