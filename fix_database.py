import sqlite3

DB_PATH = "shoparound.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check existing columns in users table
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Existing columns: {columns}")

# Add missing columns if they don't exist
missing_columns = {
    "last_login": "TEXT",
    "full_name": "TEXT",
    "phone": "TEXT",
    "address": "TEXT",
    "household_size": "INTEGER DEFAULT 1",
    "monthly_budget": "REAL"
}

for col, col_type in missing_columns.items():
    if col not in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            print(f"✅ Added column: {col}")
        except Exception as e:
            print(f"Error adding {col}: {e}")

# Also check service_providers table
cursor.execute("PRAGMA table_info(service_providers)")
sp_columns = [col[1] for col in cursor.fetchall()]
print(f"\nService providers columns: {sp_columns}")

# Add missing service provider columns
sp_missing = {
    "rating": "REAL DEFAULT 0",
    "website": "TEXT",
    "opening_hours": "TEXT",
    "source": "TEXT DEFAULT 'local'",
    "verified": "INTEGER DEFAULT 1"
}

for col, col_type in sp_missing.items():
    if col not in sp_columns:
        try:
            cursor.execute(f"ALTER TABLE service_providers ADD COLUMN {col} {col_type}")
            print(f"✅ Added column: {col}")
        except Exception as e:
            print(f"Error adding {col}: {e}")

conn.commit()
conn.close()
print("\n✅ Database schema fixed!")
