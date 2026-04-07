"""
database.py — SQLite database setup for Student Expense Tracker
Run this once to initialize the database: python database.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "expense_tracker.db")


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Rows behave like dicts
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users table ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,       -- stored as bcrypt hash
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Sessions table ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token       TEXT    NOT NULL UNIQUE,
            created_at  TEXT    DEFAULT (datetime('now')),
            expires_at  TEXT    NOT NULL
        )
    """)

    # ── Expenses table ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount > 0),
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Budget table ──────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            amount      REAL    NOT NULL DEFAULT 8000,
            updated_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")
    print("   Tables created: users, sessions, expenses, budgets")


if __name__ == "__main__":
    init_db()
