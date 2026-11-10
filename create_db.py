import sqlite3

conn = sqlite3.connect("pocket.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL
)""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  amount REAL NOT NULL,
  category TEXT,
  note TEXT,
  date TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
)""")

cur.execute("""
CREATE TABLE IF NOT EXISTS budgets (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  month TEXT NOT NULL,
  amount REAL NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
)""")

conn.commit()
conn.close()
print("Database created")
