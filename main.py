import hashlib
import hmac
import os
import secrets
import sqlite3
from typing import Literal, Optional
from fastapi.responses import FileResponse
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

app = FastAPI()
bearer = HTTPBearer()
sessions = {}  # token -> user_id
DB_PATH = os.environ.get("POCKET_DB", "pocket.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    if ":" not in stored:
        return False
    salt_hex, digest_hex = stored.split(":")
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), 200_000
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    user_id = sessions.get(creds.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Please log in first")
    return user_id


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=6)


class TransactionIn(BaseModel):
    type: Literal["income", "expense"]
    amount: float = Field(gt=0)
    category: Optional[str] = None
    note: Optional[str] = None
    date: str


class BudgetIn(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    amount: float = Field(gt=0)


@app.get("/")
def home():
    return {"message": "Pocket Money Manager is running"}


@app.post("/register")
def register(u: UserIn):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (u.username, hash_password(u.password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already taken")
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, "message": "Account created"}


@app.post("/login")
def login(u: UserIn):
    conn = get_db()
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (u.username,),
    ).fetchone()
    conn.close()
    if row is None or not verify_password(u.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    token = secrets.token_hex(16)
    sessions[token] = row["id"]
    return {"token": token, "message": "Login successful"}


@app.get("/transactions")
def list_transactions(user_id: int = Depends(current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/transactions")
def add_transaction(t: TransactionIn, user_id: int = Depends(current_user)):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO transactions (user_id, type, amount, category, note, date) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, t.type, t.amount, t.category, t.note, t.date),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, "message": "Transaction added"}


@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int, t: TransactionIn, user_id: int = Depends(current_user)
):
    conn = get_db()
    cur = conn.execute(
        "UPDATE transactions SET type = ?, amount = ?, category = ?, "
        "note = ?, date = ? WHERE id = ? AND user_id = ?",
        (t.type, t.amount, t.category, t.note, t.date, transaction_id, user_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction updated"}


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, user_id: int = Depends(current_user)):
    conn = get_db()
    cur = conn.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}


@app.put("/budgets")
def set_budget(b: BudgetIn, user_id: int = Depends(current_user)):
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM budgets WHERE user_id = ? AND month = ?",
        (user_id, b.month),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE budgets SET amount = ? WHERE id = ?", (b.amount, existing["id"])
        )
        message = "Budget updated"
    else:
        conn.execute(
            "INSERT INTO budgets (user_id, month, amount) VALUES (?, ?, ?)",
            (user_id, b.month, b.amount),
        )
        message = "Budget created"
    conn.commit()
    conn.close()
    return {"message": message}


@app.get("/budgets/{month}")
def get_budget(month: str, user_id: int = Depends(current_user)):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM budgets WHERE user_id = ? AND month = ?",
        (user_id, month),
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="No budget set for that month")
    return dict(row)


@app.get("/summary/{month}")
def summary(month: str, user_id: int = Depends(current_user)):
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
@app.get("/app")
def frontend():
    return FileResponse("static/index.html")