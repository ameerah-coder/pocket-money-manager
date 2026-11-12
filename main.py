from typing import Literal, Optional
from pydantic import BaseModel, Field
import sqlite3
from fastapi import FastAPI, HTTPException

app = FastAPI()

def get_db():
    conn = sqlite3.connect("pocket.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def home():
    return {"message": "Pocket Money Manager is running"}

@app.get("/transactions")
def list_transactions():
    conn = get_db()
    rows = conn.execute("SELECT * FROM transactions ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]
class TransactionIn(BaseModel):
    user_id: int
    type: Literal["income", "expense"]
    amount: float = Field(gt=0)
    category: Optional[str] = None
    note: Optional[str] = None
    date: str

@app.post("/transactions")
def add_transaction(t: TransactionIn):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO transactions (user_id, type, amount, category, note, date) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (t.user_id, t.type, t.amount, t.category, t.note, t.date),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, "message": "Transaction added"}
@app.delete("/transactions/{transaction_id}")

def delete_transaction(transaction_id: int):
    conn = get_db()
    cur = conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}
@app.put("/transactions/{transaction_id}")
def update_transaction(transaction_id: int, t: TransactionIn):
    conn = get_db()
    cur = conn.execute(
        "UPDATE transactions SET user_id = ?, type = ?, amount = ?, "
        "category = ?, note = ?, date = ? WHERE id = ?",
        (t.user_id, t.type, t.amount, t.category, t.note, t.date, transaction_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction updated"}


