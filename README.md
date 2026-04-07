# 🎓 Student Expense Tracker — Setup Guide

## Files in this project

| File | Purpose |
|------|---------|
| `index.html` | Frontend — open in browser |
| `server.py` | Flask REST API backend |
| `database.py` | SQLite database setup |
| `expense_tracker.db` | SQLite database file (auto-created) |
| `requirements.txt` | Python dependencies |

---

## ⚡ Quick Start (3 steps)

### Step 1 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Start the backend server
```bash
python server.py
```
You should see:
```
🚀 Expense Tracker API running at http://localhost:5000
```

### Step 3 — Open the app
Open your browser and go to `http://localhost:5000`.
If you prefer, you can also open `index.html` directly, but the API works best when the server is running.

---

## 🗄️ Database Schema

The SQLite database (`expense_tracker.db`) has 4 tables:

### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Full name |
| email | TEXT | Unique email/username |
| password | TEXT | SHA-256 hashed password |
| created_at | TEXT | Registration timestamp |

### `sessions`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | FK → users.id |
| token | TEXT | Auth token (hex-32) |
| expires_at | TEXT | Token expiry (7 days) |

### `expenses`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | FK → users.id |
| name | TEXT | Expense description |
| amount | REAL | Amount in ₹ |
| category | TEXT | Food/Rent/Recharge/Transport/Other |
| date | TEXT | Date (YYYY-MM-DD) |

### `budgets`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | FK → users.id (unique) |
| amount | REAL | Monthly budget in ₹ |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | Login, get token |
| POST | `/api/logout` | Logout (invalidate token) |
| GET | `/api/expenses` | Get all expenses |
| POST | `/api/expenses` | Add expense |
| DELETE | `/api/expenses/:id` | Delete one expense |
| DELETE | `/api/expenses` | Delete all expenses |
| GET | `/api/budget` | Get budget |
| PUT | `/api/budget` | Update budget |
| GET | `/api/users` | List all users (dev) |

---

## 🔍 Inspect the Database

You can open `expense_tracker.db` with:
- **DB Browser for SQLite** (free GUI): https://sqlitebrowser.org
- **Command line**: `sqlite3 expense_tracker.db`

```sql
-- Example queries
SELECT * FROM users;
SELECT * FROM expenses ORDER BY date DESC;
SELECT * FROM budgets;
```
