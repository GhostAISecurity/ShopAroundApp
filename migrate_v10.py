import sqlite3

conn = sqlite3.connect("shoparound.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS geo_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT,
    price REAL,
    shop TEXT,
    location TEXT,
    latitude REAL,
    longitude REAL,
    confidence REAL DEFAULT 0.7,
    source TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS receipt_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    shop TEXT,
    raw_text TEXT,
    parsed_items TEXT,
    confidence REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS economic_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT,
    location TEXT,
    item_name TEXT,
    severity REAL,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS product_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE,
    aliases TEXT,
    category TEXT
)
""")

conn.commit()
conn.close()

print("Migration complete")
