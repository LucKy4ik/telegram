import sqlite3
import emoji

user_name = 'Lucky231131'
user_n = 'Lucky23'
user_task = str()

conn = sqlite3.connect("user_telegram.sql")
cur = conn.cursor()
cur.execute('SELECT *FROM users')
users = cur.fetchall()
print(users[0][1])