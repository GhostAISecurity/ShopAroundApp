import sqlite3

db = sqlite3.connect("shoparound.db")
cur = db.cursor()

# Fix the shopping_history table structure - add items_json column if needed
try:
    cur.execute("ALTER TABLE shopping_history ADD COLUMN items_json TEXT")
except:
    pass

# Create a better shopping_items table for tracking
cur.execute("""
CREATE TABLE IF NOT EXISTS shopping_items (
    id INTEGER PRIMARY KEY,
    history_id INTEGER,
    item_name TEXT,
    item_price REAL,
    item_shop TEXT,
    FOREIGN KEY(history_id) REFERENCES shopping_history(id)
)
""")

db.commit()
db.close()
print("✅ Database fixed!")
