import os
import sqlite3

# Use a separate database so your real data is never touched
os.environ["POCKET_DB"] = "test_pocket.db"
if os.path.exists("test_pocket.db"):
    os.remove("test_pocket.db")

from fastapi.testclient import TestClient

import main

SCHEMA = """
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL
);
CREATE TABLE transactions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  amount REAL NOT NULL,
  category TEXT,
  note TEXT,
  date TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE budgets (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  month TEXT NOT NULL,
  amount REAL NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

conn = sqlite3.connect("test_pocket.db")
conn.executescript(SCHEMA)
conn.close()

client = TestClient(main.app)


def make_user(name):
    """Register and log in a user, return the login header."""
    client.post("/register", json={"username": name, "password": "secret123"})
    r = client.post("/login", json={"username": name, "password": "secret123"})
    return {"Authorization": "Bearer " + r.json()["token"]}


def test_duplicate_username_rejected():
    client.post("/register", json={"username": "dupuser", "password": "secret123"})
    r = client.post("/register", json={"username": "dupuser", "password": "secret123"})
    assert r.status_code == 400


def test_wrong_password_rejected():
    client.post("/register", json={"username": "wrongpw", "password": "secret123"})
    r = client.post("/login", json={"username": "wrongpw", "password": "badpass1"})
    assert r.status_code == 401


def test_login_required():
    r = client.get("/transactions")
    assert r.status_code in (401, 403)


def test_add_and_list_transaction():
    headers = make_user("lister")
    new = {"type": "expense", "amount": 500, "category": "food",
           "note": "lunch", "date": "2026-11-12"}
    assert client.post("/transactions", json=new, headers=headers).status_code == 200
    rows = client.get("/transactions", headers=headers).json()
    assert len(rows) == 1
    assert rows[0]["amount"] == 500


def test_negative_amount_rejected():
    headers = make_user("negative")
    bad = {"type": "expense", "amount": -5, "date": "2026-11-12"}
    r = client.post("/transactions", json=bad, headers=headers)
    assert r.status_code == 422


def test_budget_warning():
    headers = make_user("budgeter")
    spend = {"type": "expense", "amount": 1100, "category": "food",
             "date": "2026-11-12"}
    client.post("/transactions", json=spend, headers=headers)

    client.put("/budgets", json={"month": "2026-11", "amount": 1000}, headers=headers)
    over = client.get("/summary/2026-11", headers=headers).json()
    assert over["over_budget"] is True

    client.put("/budgets", json={"month": "2026-11", "amount": 3000}, headers=headers)
    ok = client.get("/summary/2026-11", headers=headers).json()
    assert ok["over_budget"] is False


def test_cannot_delete_another_users_transaction():
    owner = make_user("owner")
    other = make_user("intruder")
    new = {"type": "income", "amount": 100, "date": "2026-11-12"}
    tid = client.post("/transactions", json=new, headers=owner).json()["id"]
    r = client.delete("/transactions/" + str(tid), headers=other)
    assert r.status_code == 404