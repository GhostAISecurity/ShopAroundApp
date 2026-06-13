#!/usr/bin/env python3
"""
Database Migration - Fix User Table Schema
Safe upgrade that preserves existing data
"""

import sqlite3
import os

DB_PATH = "shoparound.db"

def get_existing_columns(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}

def migrate_users_table():
    print("🔧 Migrating users table...")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    existing = get_existing_columns(conn, "users")
    print(f"   Existing columns: {sorted(existing)}")
    
    # Define the target schema (all possible columns)
    migrations = [
        # Column name, SQL, default
        ("phone_number", "ALTER TABLE users ADD COLUMN phone_number TEXT", None),
        ("household_size", "ALTER TABLE users ADD COLUMN household_size INTEGER DEFAULT 1", 1),
        ("monthly_budget", "ALTER TABLE users ADD COLUMN monthly_budget REAL DEFAULT 0", 0),
        ("language", "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'", 'en'),
        ("total_saved", "ALTER TABLE users ADD COLUMN total_saved REAL DEFAULT 0", 0),
        ("loyalty_points", "ALTER TABLE users ADD COLUMN loyalty_points INTEGER DEFAULT 0", 0),
        ("session_token", "ALTER TABLE users ADD COLUMN session_token TEXT", None),
        ("preferences", "ALTER TABLE users ADD COLUMN preferences TEXT DEFAULT '{}'", '{}'),
        ("last_login", "ALTER TABLE users ADD COLUMN last_login DATETIME", None),
    ]
    
    # Apply migrations
    for col, sql, default in migrations:
        if col not in existing:
            try:
                cursor.execute(sql)
                print(f"   ✅ Added column: {col}")
            except sqlite3.OperationalError as e:
                print(f"   ⚠️ Could not add {col}: {e}")
    
    # Fix registration endpoint - ensure username column exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        # Rename 'name' to 'username' if needed (for compatibility)
        if "name" in existing and "username" not in existing:
            try:
                cursor.execute("ALTER TABLE users RENAME COLUMN name TO username")
                print("   ✅ Renamed 'name' column to 'username'")
            except:
                pass
    
    conn.commit()
    conn.close()
    print("✅ Users table migration complete!")

def fix_service_providers():
    """Fix service_providers table schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    existing = get_existing_columns(conn, "service_providers")
    
    migrations = [
        ("latitude", "ALTER TABLE service_providers ADD COLUMN latitude REAL", None),
        ("longitude", "ALTER TABLE service_providers ADD COLUMN longitude REAL", None),
        ("address", "ALTER TABLE service_providers ADD COLUMN address TEXT", None),
        ("description", "ALTER TABLE service_providers ADD COLUMN description TEXT", None),
        ("hourly_rate", "ALTER TABLE service_providers ADD COLUMN hourly_rate REAL DEFAULT 0", 0),
        ("verified", "ALTER TABLE service_providers ADD COLUMN verified INTEGER DEFAULT 0", 0),
    ]
    
    for col, sql, default in migrations:
        if col not in existing:
            try:
                cursor.execute(sql)
                print(f"   ✅ Added column: {col} to service_providers")
            except:
                pass
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("="*50)
    print("SHOPAROUND Database Migration Tool")
    print("="*50)
    migrate_users_table()
    fix_service_providers()
    print("\n✅ All migrations complete!")
    print("   You can now restart your app.")
