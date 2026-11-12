# Pocket-Money Manager

A backend app that helps students record income and expenses, set a
monthly budget, and see where their money goes.

## Features
- Register and log in (passwords stored hashed with a salt)
- Add, view, edit and delete income and expenses
- Set a monthly budget
- Monthly summary by category, with a warning when over budget

## Tech
Python, FastAPI, SQLite. Process model: Agile/Scrum.

## How to run
```
git clone <your repo link>
cd pocket-money-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 create_db.py
uvicorn main:app --reload
```
Then open http://127.0.0.1:8000/docs

## Project documents
- [Requirements and user stories](REQUIREMENTS.md)
- [Use case diagram](USE_CASES.md)
- [Database design](DATABASE.md)

## Endpoints
| Method | Address | What it does |
|---|---|---|
| POST | /register | Create an account |
| POST | /login | Log in and get a token |
| GET | /transactions | List my transactions |
| POST | /transactions | Add a transaction |
| PUT | /transactions/{id} | Edit a transaction |
| DELETE | /transactions/{id} | Delete a transaction |
| PUT | /budgets | Set a monthly budget |
| GET | /budgets/{month} | View a monthly budget |
| GET | /summary/{month} | Spending summary and warning |
