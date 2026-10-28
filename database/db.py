"""Persistencia SQLite. Los importes se guardan como centavos enteros."""
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime

APP_DIR = Path.home() / "BanderillasCoreanas"
DB_PATH = APP_DIR / "banderillas.sqlite3"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL DEFAULT '', price INTEGER NOT NULL CHECK(price>=0), cost INTEGER NOT NULL DEFAULT 0 CHECK(cost>=0), stock REAL NOT NULL DEFAULT 0 CHECK(stock>=0), min_stock REAL NOT NULL DEFAULT 0 CHECK(min_stock>=0), active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS ingredients(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, unit TEXT NOT NULL, quantity REAL NOT NULL DEFAULT 0 CHECK(quantity>=0), min_stock REAL NOT NULL DEFAULT 0 CHECK(min_stock>=0), unit_cost INTEGER NOT NULL DEFAULT 0 CHECK(unit_cost>=0));
CREATE TABLE IF NOT EXISTS recipes(product_id INTEGER NOT NULL REFERENCES products(id), ingredient_id INTEGER NOT NULL REFERENCES ingredients(id), quantity REAL NOT NULL CHECK(quantity>0), PRIMARY KEY(product_id,ingredient_id));
CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, subtotal INTEGER NOT NULL, discount INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'CONFIRMADA', note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS sale_items(id INTEGER PRIMARY KEY, sale_id INTEGER NOT NULL REFERENCES sales(id), product_id INTEGER NOT NULL REFERENCES products(id), product_name TEXT NOT NULL, quantity REAL NOT NULL, unit_price INTEGER NOT NULL, unit_cost INTEGER NOT NULL, line_total INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY, sale_id INTEGER NOT NULL REFERENCES sales(id), method TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>=0));
CREATE TABLE IF NOT EXISTS inventory_moves(id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, item_type TEXT NOT NULL, item_id INTEGER NOT NULL, item_name TEXT NOT NULL, movement TEXT NOT NULL, quantity REAL NOT NULL, unit_cost INTEGER NOT NULL DEFAULT 0, reference TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>0), method TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cash_sessions(id INTEGER PRIMARY KEY, opened_at TEXT NOT NULL, closed_at TEXT, opening_balance INTEGER NOT NULL, expected_balance INTEGER, counted_balance INTEGER, note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS cash_moves(id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES cash_sessions(id), created_at TEXT NOT NULL, kind TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>=0), method TEXT NOT NULL, note TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS ix_sales_date ON sales(created_at);
CREATE INDEX IF NOT EXISTS ix_moves_date ON inventory_moves(created_at);
"""

def connect():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def initialize():
    with connect() as con:
        con.executescript(SCHEMA)

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def backup(destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with connect() as source, sqlite3.connect(destination) as target:
        source.backup(target)

def restore(source):
    source = Path(source)
    if not source.is_file():
        raise ValueError("No se encontró el archivo de respaldo.")
    with sqlite3.connect(source) as check:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise ValueError("La copia no superó la comprobación de integridad.")
    APP_DIR.mkdir(parents=True, exist_ok=True)
    # La app solicita reiniciarse tras restaurar; respaldo preventivo antes del reemplazo.
    if DB_PATH.exists():
        backup(APP_DIR / f"antes_restauracion_{datetime.now():%Y%m%d_%H%M%S}.sqlite3")
    with sqlite3.connect(source) as src, sqlite3.connect(DB_PATH) as dst:
        src.backup(dst)

