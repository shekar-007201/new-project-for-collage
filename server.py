"""
server.py — Flask REST API for Student Expense Tracker
Start with: python server.py
API runs on http://localhost:5000
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS

from database import init_db, get_connection

app = Flask(__name__)
CORS(app)  # Allow requests from the HTML file (file:// or any origin)

# ── Helpers ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """SHA-256 hash (simple; swap with bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def make_token() -> str:
    return secrets.token_hex(32)


def get_user_from_token(token: str):
    """Return user row if token is valid and not expired, else None."""
    if not token:
        return None
    conn = get_connection()
    row = conn.execute("""
        SELECT u.* FROM users u
        JOIN sessions s ON s.user_id = u.id
        WHERE s.token = ? AND s.expires_at > datetime('now')
    """, (token,)).fetchone()
    conn.close()
    return row


def auth_required(f):
    """Decorator: inject current_user or return 401."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Auth-Token", "")
        user = get_user_from_token(token)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, user=user, **kwargs)
    return wrapper


# ── Auth endpoints ─────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""

    if not name or not email or not pwd:
        return jsonify({"error": "All fields are required."}), 400
    if len(pwd) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hash_password(pwd))
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        # Create default budget for new user
        conn.execute("INSERT INTO budgets (user_id, amount) VALUES (?, 8000)", (user["id"],))
        conn.commit()

        token = _create_session(conn, user["id"])
        conn.close()
        return jsonify({"token": token, "name": user["name"], "email": user["email"]}), 201

    except Exception as e:
        conn.close()
        if "UNIQUE" in str(e):
            return jsonify({"error": "An account with this email already exists."}), 409
        return jsonify({"error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def login():
    data  = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    pwd   = data.get("password") or ""

    if not email or not pwd:
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not user or user["password"] != hash_password(pwd):
        conn.close()
        return jsonify({"error": "Invalid email or password."}), 401

    token = _create_session(conn, user["id"])
    conn.close()
    return jsonify({"token": token, "name": user["name"], "email": user["email"]}), 200


@app.route("/api/logout", methods=["POST"])
@auth_required
def logout(user):
    token = request.headers.get("X-Auth-Token", "")
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Logged out."}), 200


def _create_session(conn, user_id: int) -> str:
    token   = make_token()
    expires = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires)
    )
    conn.commit()
    return token


# ── Expense endpoints ──────────────────────────────────────────────────────

@app.route("/api/expenses", methods=["GET"])
@auth_required
def get_expenses(user):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user["id"],)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/expenses", methods=["POST"])
@auth_required
def add_expense(user):
    data = request.get_json(force=True)
    name     = (data.get("name") or "").strip()
    amount   = data.get("amount")
    category = data.get("category") or "Other"
    date     = data.get("date") or datetime.utcnow().strftime("%Y-%m-%d")

    if not name or not amount:
        return jsonify({"error": "Name and amount are required."}), 400
    try:
        amount = float(amount)
        assert amount > 0
    except Exception:
        return jsonify({"error": "Amount must be a positive number."}), 400

    conn = get_connection()
    conn.execute(
        "INSERT INTO expenses (user_id, name, amount, category, date) VALUES (?,?,?,?,?)",
        (user["id"], name, amount, category, date)
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (user["id"],)
    ).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
@auth_required
def delete_expense(user, expense_id):
    conn = get_connection()
    result = conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user["id"])
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        return jsonify({"error": "Expense not found."}), 404
    return jsonify({"message": "Deleted."}), 200


@app.route("/api/expenses", methods=["DELETE"])
@auth_required
def delete_all_expenses(user):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()
    return jsonify({"message": "All expenses deleted."}), 200


# ── Budget endpoints ───────────────────────────────────────────────────────

@app.route("/api/budget", methods=["GET"])
@auth_required
def get_budget(user):
    conn = get_connection()
    row = conn.execute(
        "SELECT amount FROM budgets WHERE user_id = ?", (user["id"],)
    ).fetchone()
    conn.close()
    amount = row["amount"] if row else 8000
    return jsonify({"amount": amount})


@app.route("/api/budget", methods=["PUT"])
@auth_required
def update_budget(user):
    data   = request.get_json(force=True)
    amount = data.get("amount")
    try:
        amount = float(amount)
        assert amount > 0
    except Exception:
        return jsonify({"error": "Budget must be a positive number."}), 400

    conn = get_connection()
    conn.execute("""
        INSERT INTO budgets (user_id, amount) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET amount=excluded.amount,
                                           updated_at=datetime('now')
    """, (user["id"], amount))
    conn.commit()
    conn.close()
    return jsonify({"amount": amount})


# ── Users admin (list all users — for dev/inspection) ─────────────────────

@app.route("/api/users", methods=["GET"])
def list_users():
    """Dev endpoint: lists all registered users (no passwords)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, email, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n🚀 Expense Tracker API running at http://localhost:5000")
    print("   Open index.html in your browser after starting this server.\n")
    app.run(debug=True, port=5000)
