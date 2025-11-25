import sqlite3
import hashlib
import datetime
import os

# === CONFIG ===
USE_MYSQL = False  # set True if you want MySQL (you'll need mysql-connector)
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "bankdb"
}

SQLITE_DB = "bank.db"

# helper: password hashing
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

# DB connection abstraction
def get_conn():
    if USE_MYSQL:
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"]
        )
        return conn
    else:
        return sqlite3.connect(SQLITE_DB)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # Admins table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        fullname TEXT
    );
    """)
    # Customers / Accounts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_no TEXT UNIQUE,
        name TEXT,
        email TEXT,
        phone TEXT,
        balance REAL DEFAULT 0,
        created_at TEXT
    );
    """)
    # Transactions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_no TEXT,
        type TEXT, -- deposit/withdraw/transfer
        amount REAL,
        timestamp TEXT,
        note TEXT
    );
    """)
    # Loans
    cur.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_no TEXT,
        amount REAL,
        status TEXT, -- pending/approved/paid
        created_at TEXT,
        updated_at TEXT
    );
    """)
    # Audit logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin TEXT,
        action TEXT,
        timestamp TEXT
    );
    """)
    conn.commit()

    # create default admin if not exists
    cur.execute("SELECT COUNT(*) FROM admins;")
    count = cur.fetchone()[0]
    if count == 0:
        pw = hash_password("Admin123")
        cur.execute("INSERT INTO admins (username, password_hash, fullname) VALUES (?, ?, ?)",
                    ("Admin", pw, "Charles Admin"))
        conn.commit()

    conn.close()

# Authentication
def authenticate_admin(username: str, password: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM admins WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    stored = row[0]
    return stored == hash_password(password)

# Admin creation (optional)
def create_admin(username: str, password: str, fullname: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO admins (username, password_hash, fullname) VALUES (?, ?, ?)",
                    (username, hash_password(password), fullname))
        conn.commit()
        return True
    except Exception as e:
        print("create_admin error:", e)
        return False
    finally:
        conn.close()

# Accounts functions
def create_account(account_no, name, email="", phone="", initial_balance=0.0):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO accounts (account_no, name, email, phone, balance, created_at)
                       VALUES (?, ?, ?, ?, ?, ?);""",
                    (account_no, name, email, phone, initial_balance, datetime.datetime.utcnow().isoformat()))
        conn.commit()
        log_action("system", f"Create account {account_no}")
        return True
    except Exception as e:
        print("create_account error:", e)
        return False
    finally:
        conn.close()

def get_accounts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, account_no, name, email, phone, balance, created_at FROM accounts;")
    rows = cur.fetchall()
    conn.close()
    return rows

def update_account(acc_id, name=None, email=None, phone=None):
    conn = get_conn()
    cur = conn.cursor()
    # fetch current
    cur.execute("SELECT account_no, name, email, phone FROM accounts WHERE id = ?;", (acc_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False
    account_no = r[0]
    new_name = name if name is not None else r[1]
    new_email = email if email is not None else r[2]
    new_phone = phone if phone is not None else r[3]
    cur.execute("UPDATE accounts SET name=?, email=?, phone=? WHERE id=?",
                (new_name, new_email, new_phone, acc_id))
    conn.commit()
    log_action("system", f"Update account {account_no}")
    conn.close()
    return True

def delete_account(acc_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT account_no FROM accounts WHERE id=?;", (acc_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False
    account_no = r[0]
    cur.execute("DELETE FROM accounts WHERE id=?", (acc_id,))
    conn.commit()
    log_action("system", f"Delete account {account_no}")
    conn.close()
    return True

# Transactions (deposit/withdraw)
def add_transaction(account_no, ttype, amount, note=""):
    conn = get_conn()
    cur = conn.cursor()
    # update balance
    cur.execute("SELECT balance FROM accounts WHERE account_no = ?;", (account_no,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False, "Account not found"
    balance = r[0]
    if ttype == "withdraw" and balance < amount:
        conn.close()
        return False, "Insufficient funds"
    new_balance = balance + amount if ttype == "deposit" else balance - amount
    cur.execute("UPDATE accounts SET balance = ? WHERE account_no = ?;", (new_balance, account_no))
    cur.execute("INSERT INTO transactions (account_no, type, amount, timestamp, note) VALUES (?, ?, ?, ?, ?)",
                (account_no, ttype, amount, datetime.datetime.utcnow().isoformat(), note))
    conn.commit()
    log_action("system", f"{ttype} {amount} on {account_no}")
    conn.close()
    return True, "OK"

def get_transactions(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, account_no, type, amount, timestamp, note FROM transactions ORDER BY id DESC LIMIT ?;", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Loans
def create_loan(account_no, amount):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO loans (account_no, amount, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (account_no, amount, "pending", now, now))
    conn.commit()
    log_action("system", f"Loan request {amount} for {account_no}")
    conn.close()
    return True

def update_loan_status(loan_id, status):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("UPDATE loans SET status=?, updated_at=? WHERE id=?", (status, now, loan_id))
    conn.commit()
    log_action("system", f"Loan {loan_id} status -> {status}")
    conn.close()
    return True

def get_loans():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, account_no, amount, status, created_at, updated_at FROM loans ORDER BY id DESC;")
    rows = cur.fetchall()
    conn.close()
    return rows

# Reporting
def total_deposits():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='deposit';")
    s = cur.fetchone()[0] or 0
    conn.close()
    return s

def total_withdraws():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='withdraw';")
    s = cur.fetchone()[0] or 0
    conn.close()
    return s

# Audit logs
def log_action(admin, action):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO audit_logs (admin, action, timestamp) VALUES (?, ?, ?)",
                (admin, action, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_audit_logs(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, admin, action, timestamp FROM audit_logs ORDER BY id DESC LIMIT ?;", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Helper: generate a simple account number
def generate_account_no():
    import random
    return "AC" + str(random.randint(100000, 999999))

if __name__ == "__main__":
    # Create DB and default admin/account for quick testing
    init_db()
    print("Database initialized (default admin: Admin / Admin123)")