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
class BudgetIn(BaseModel):
    user_id: int
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    amount: float = Field(gt=0)

@app.put("/budgets")
def set_budget(b: BudgetIn):
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM budgets WHERE user_id = ? AND month = ?",
        (b.user_id, b.month),
    ).fetchone()
    if existing:
        conn.execute("UPDATE budgets SET amount = ? WHERE id = ?",
                     (b.amount, existing["id"]))
        message = "Budget updated"
    else:
        conn.execute("INSERT INTO budgets (user_id, month, amount) VALUES (?, ?, ?)",
                     (b.user_id, b.month, b.amount))
        message = "Budget created"
    conn.commit()
    conn.close()
    return {"message": message}

@app.get("/budgets/{user_id}/{month}")
def get_budget(user_id: int, month: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM budgets WHERE user_id = ? AND month = ?",
        (user_id, month),
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="No budget set for that month")
    return dict(row)
@app.get("/summary/{user_id}/{month}")
def summary(user_id: int, month: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) AS total FROM transactions "
        "WHERE user_id = ? AND type = 'expense' AND substr(date, 1, 7) = ? "
        "GROUP BY category",
        (user_id, month),
    ).fetchall()
    income_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
        "WHERE user_id = ? AND type = 'income' AND substr(date, 1, 7) = ?",
        (user_id, month),
    ).fetchone()
    budget_row = conn.execute(
        "SELECT amount FROM budgets WHERE user_id = ? AND month = ?",
        (user_id, month),
    ).fetchone()
    conn.close()

    by_category = {(r["category"] or "uncategorised"): r["total"] for r in rows}
    total_spent = sum(by_category.values())
    budget = budget_row["amount"] if budget_row else None
    over_budget = budget is not None and total_spent > budget

    return {
        "month": month,
        "total_income": income_row["total"],
        "total_spent": total_spent,
        "spent_by_category": by_category,
        "budget": budget,
        "over_budget": over_budget,
        "warning": "You have exceeded your budget!" if over_budget else None,
    }


