import sqlite3

conn=sqlite3.connect("notices.db")
cur=conn.cursor()

print("Tables: ")

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())

print("\nSchema:")
cur.execute("PRAGMA table_info(notices);")

for row in cur.fetchall():
    print(row)

print("\nData: ")
cur.execute("SELECT * FROM notices;")
for row in cur.fetchall():
    print(row)

conn.close()