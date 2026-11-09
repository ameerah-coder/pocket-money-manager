# Functional requirements
* FR1: A user can register and log in.
* FR2: A user can add an income entry (amount, source, date).
* FR3: A user can add an expense (amount, category, date, note).
* FR4: A user can view, edit, and delete their transactions.
* FR5: A user can set a monthly budget.
* FR6: The app warns the user when spending passes the budget.
* FR7: The app shows a summary of spending by category.
# Non-functional requirements
* NFR1: Pages respond in under 2 seconds.
* NFR2: Passwords are stored hashed, never as plain text.
* NFR3: The interface is simple enough to use without instructions.
# User stories
## US1 (FR1): Register and log in As a student, I want to create an account and log in, so that my records stay private.
* Registering with a new username and password creates an account.
* Logging in with wrong details shows an error.
## US2 (FR2): Add income As a student, I want to record money I receive, so that I know how much I have.
* Amount, source, and date are required.
* The new entry appears in my transaction list.
## US3 (FR3): Add expense As a student, I want to record what I spend, so that I know where my money goes.
* Amount, category, and date are required.
* Amount must be greater than zero.
## US4 (FR4): Manage transactions As a student, I want to view, edit, and delete entries, so that I can fix mistakes.
* All my transactions are listed, newest first.
* Edits and deletions are saved and shown immediately.
## US5 (FR5): Set a budget As a student, I want to set a monthly budget, so that I have a spending limit to follow.
* I can enter one budget amount per month.
* I can change it later.
## US6 (FR6): Budget warning As a student, I want a warning when I pass my budget, so that I can stop overspending.
* The warning appears when total expenses for the month exceed the budget.
* No warning appears while I'm under it.
## US7 (FR7): Spending summary As a student, I want to see spending grouped by category, so that I can see my biggest expenses.
* The summary shows each category's total for the chosen month.
* The totals match my transaction list.
