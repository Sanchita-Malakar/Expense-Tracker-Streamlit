import sqlite3
import pandas as pd
import os

DB_PATH = 'data/expenses.db'

INCOME_SOURCES = ['Salary', 'Freelance', 'Business', 'Investment', 'Rental', 'Gift', 'Other']


def _get_conn():
    return sqlite3.connect(DB_PATH)


def _migrate_schema(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(expenses)")
    cols = {row[1]: row for row in cursor.fetchall()}
    if 'id' not in cols or cols['id'][5] != 1:
        print("[database] Migrating expenses schema...")
        cursor.executescript('''
            ALTER TABLE expenses RENAME TO expenses_old;
            CREATE TABLE expenses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                date           TEXT    NOT NULL,
                category       TEXT    NOT NULL,
                amount         REAL    NOT NULL,
                payment_method TEXT    NOT NULL,
                note           TEXT    DEFAULT "",
                source         TEXT    DEFAULT "manual"
            );
            INSERT INTO expenses (date, category, amount, payment_method, note, source)
            SELECT date, category, amount, payment_method,
                   COALESCE(note, ""), COALESCE(source, "manual")
            FROM   expenses_old;
            DROP TABLE expenses_old;
        ''')
        conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# INIT
# ══════════════════════════════════════════════════════════════════════════════
def init_db():
    os.makedirs('data', exist_ok=True)
    conn   = _get_conn()
    cursor = conn.cursor()

    # ── expenses ──────────────────────────────────────────────────────────────
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'")
    if cursor.fetchone():
        _migrate_schema(conn)
        cursor.execute("PRAGMA table_info(expenses)")
        existing = {r[1] for r in cursor.fetchall()}
        if 'source' not in existing:
            cursor.execute("ALTER TABLE expenses ADD COLUMN source TEXT DEFAULT 'manual'")
            conn.commit()
    else:
        cursor.execute('''
            CREATE TABLE expenses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                date           TEXT    NOT NULL,
                category       TEXT    NOT NULL,
                amount         REAL    NOT NULL,
                payment_method TEXT    NOT NULL,
                note           TEXT    DEFAULT "",
                source         TEXT    DEFAULT "manual"
            )
        ''')
        conn.commit()

    # ── income ────────────────────────────────────────────────────────────────
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='income'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE income (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                date   TEXT    NOT NULL,
                source TEXT    NOT NULL,
                amount REAL    NOT NULL,
                note   TEXT    DEFAULT ""
            )
        ''')
        conn.commit()

    # ── indexes ───────────────────────────────────────────────────────────────
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_date     ON expenses(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_category ON expenses(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inc_date     ON income(date)")
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# EXPENSES
# ══════════════════════════════════════════════════════════════════════════════
def insert_expense(date, category, amount, payment_method, note='', source='manual'):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO expenses (date,category,amount,payment_method,note,source) VALUES(?,?,?,?,?,?)",
        (date, category, float(amount), payment_method, note or '', source)
    )
    conn.commit(); conn.close()


def bulk_insert_expenses(df: pd.DataFrame, source: str = 'csv_upload'):
    REQUIRED = {'date', 'category', 'amount', 'payment_method'}
    errors   = []
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()
    missing = REQUIRED - set(df.columns)
    if missing:
        return 0, [f"Missing columns: {', '.join(missing)}"]
    if 'note' not in df.columns:
        df['note'] = ''
    df['note']   = df['note'].fillna('').astype(str)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    bad = df['amount'].isna()
    if bad.any():
        errors.append(f"{bad.sum()} rows had non-numeric amounts and were skipped.")
        df = df[~bad]
    try:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    except Exception:
        return 0, ["Could not parse 'date' column."]
    if df.empty:
        return 0, errors + ["No valid rows."]
    rows = [list(r) + [source] for r in df[['date','category','amount','payment_method','note']].values]
    conn = _get_conn(); cur = conn.cursor()
    cur.executemany(
        "INSERT INTO expenses (date,category,amount,payment_method,note,source) VALUES(?,?,?,?,?,?)", rows
    )
    conn.commit(); inserted = cur.rowcount; conn.close()
    return inserted, errors


def get_all_expenses_as_df():
    conn = _get_conn()
    df   = pd.read_sql_query(
        "SELECT id,date,category,amount,payment_method,note,source FROM expenses ORDER BY date DESC", conn
    )
    conn.close(); return df


def update_expense(exp_id, date, category, amount, payment_method, note=''):
    conn = _get_conn()
    conn.execute(
        "UPDATE expenses SET date=?,category=?,amount=?,payment_method=?,note=? WHERE id=?",
        (date, category, float(amount), payment_method, note or '', int(exp_id))
    )
    conn.commit(); conn.close()


def delete_expense(exp_id):
    conn = _get_conn()
    conn.execute("DELETE FROM expenses WHERE id=?", (int(exp_id),))
    conn.commit(); conn.close()


def seed_synthetic_data(df_synthetic):
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM expenses")
    if cur.fetchone()[0] == 0:
        rows = [list(r) + ['synthetic']
                for r in df_synthetic[['date','category','amount','payment_method','note']].values]
        cur.executemany(
            "INSERT INTO expenses (date,category,amount,payment_method,note,source) VALUES(?,?,?,?,?,?)", rows
        )
        conn.commit()
        print(f"Seeded {len(rows)} synthetic records.")
    conn.close()


def get_budget_vs_actual(budgets: dict, month: str = None):
    conn      = _get_conn()
    cur_month = month or pd.Timestamp.today().strftime('%Y-%m')
    df = pd.read_sql_query(
        f"SELECT category, SUM(amount) AS actual FROM expenses "
        f"WHERE strftime('%Y-%m',date)='{cur_month}' GROUP BY category", conn
    )
    conn.close()
    df['budget']    = df['category'].map(budgets).fillna(0)
    df['remaining'] = df['budget'] - df['actual']
    df['pct_used']  = (df['actual'] / df['budget'].replace(0, float('nan'))) * 100
    return df


def get_monthly_summary():
    conn = _get_conn()
    df   = pd.read_sql_query(
        """SELECT strftime('%Y-%m',date) AS month, category,
                  SUM(amount) AS total, COUNT(*) AS txn_count
           FROM expenses GROUP BY month, category ORDER BY month""", conn
    )
    conn.close(); return df


# ══════════════════════════════════════════════════════════════════════════════
# INCOME
# ══════════════════════════════════════════════════════════════════════════════
def insert_income(date, source, amount, note=''):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO income (date,source,amount,note) VALUES(?,?,?,?)",
        (date, source, float(amount), note or '')
    )
    conn.commit(); conn.close()


def get_all_income_as_df():
    conn = _get_conn()
    df   = pd.read_sql_query(
        "SELECT id,date,source,amount,note FROM income ORDER BY date DESC", conn
    )
    conn.close(); return df


def update_income(inc_id, date, source, amount, note=''):
    conn = _get_conn()
    conn.execute(
        "UPDATE income SET date=?,source=?,amount=?,note=? WHERE id=?",
        (date, source, float(amount), note or '', int(inc_id))
    )
    conn.commit(); conn.close()


def delete_income(inc_id):
    conn = _get_conn()
    conn.execute("DELETE FROM income WHERE id=?", (int(inc_id),))
    conn.commit(); conn.close()


def get_monthly_income_summary():
    conn = _get_conn()
    df   = pd.read_sql_query(
        """SELECT strftime('%Y-%m',date) AS month, source,
                  SUM(amount) AS total
           FROM income GROUP BY month, source ORDER BY month""", conn
    )
    conn.close(); return df