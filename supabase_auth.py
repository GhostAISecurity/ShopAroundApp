"""
SUPABASE AUTHENTICATION MODULE
User account isolation - Each user only accesses their own data
Pure add-on - No changes to existing code
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import request, jsonify, session, g

# Try to import supabase (optional - will work with local fallback)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not installed. Using local SQLite fallback.")

# Supabase configuration (set these in environment)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

# Local fallback database for user isolation
import sqlite3

class UserAuth:
    def __init__(self):
        self.supabase = None
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✅ Supabase connected")
        else:
            print("⚠️ Using local SQLite for authentication")
            self._init_local_db()
    
    def _init_local_db(self):
        conn = sqlite3.connect("users_local.db")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_token TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                data_key TEXT,
                data_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, data_key)
            )
        """)
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, email, password, full_name=None):
        """Register a new user - each user gets isolated account"""
        password_hash = self.hash_password(password)
        
        if self.supabase:
            try:
                response = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {"data": {"full_name": full_name}}
                })
                return {"success": True, "user": response.user, "id": response.user.id}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            # Local fallback
            conn = sqlite3.connect("users_local.db")
            try:
                cursor = conn.execute(
                    "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
                    (email, password_hash, full_name)
                )
                conn.commit()
                user_id = cursor.lastrowid
                token = secrets.token_urlsafe(32)
                conn.execute("UPDATE users SET session_token = ? WHERE id = ?", (token, user_id))
                conn.commit()
                return {"success": True, "id": user_id, "token": token}
            except sqlite3.IntegrityError:
                return {"success": False, "error": "Email already exists"}
            finally:
                conn.close()
    
    def login_user(self, email, password):
        """Login user - creates isolated session"""
        password_hash = self.hash_password(password)
        
        if self.supabase:
            try:
                response = self.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                session["user_id"] = response.user.id
                session["user_email"] = response.user.email
                session["session_token"] = response.session.access_token
                return {"success": True, "user": response.user}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            conn = sqlite3.connect("users_local.db")
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT id, email, full_name FROM users WHERE email = ? AND password_hash = ?",
                (email, password_hash)
            ).fetchone()
            conn.close()
            
            if user:
                token = secrets.token_urlsafe(32)
                conn = sqlite3.connect("users_local.db")
                conn.execute("UPDATE users SET session_token = ? WHERE id = ?", (token, user["id"]))
                conn.commit()
                conn.close()
                
                session["user_id"] = user["id"]
                session["user_email"] = user["email"]
                session["session_token"] = token
                return {"success": True, "user": dict(user)}
            return {"success": False, "error": "Invalid credentials"}
    
    def get_current_user(self):
        """Get currently logged in user"""
        user_id = session.get("user_id")
        if not user_id:
            return None
        
        if self.supabase:
            try:
                user = self.supabase.auth.get_user()
                return {"id": user.user.id, "email": user.user.email}
            except:
                return None
        else:
            conn = sqlite3.connect("users_local.db")
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT id, email, full_name FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            conn.close()
            return dict(user) if user else None
    
    def logout_user(self):
        """Logout current user"""
        session.clear()
        return {"success": True}
    
    def save_user_data(self, key, value):
        """Save user-specific data (isolated per user)"""
        user_id = session.get("user_id")
        if not user_id:
            return {"success": False, "error": "Not logged in"}
        
        conn = sqlite3.connect("users_local.db")
        conn.execute("""
            INSERT OR REPLACE INTO user_data (user_id, data_key, data_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, key, json.dumps(value)))
        conn.commit()
        conn.close()
        return {"success": True}
    
    def get_user_data(self, key):
        """Get user-specific data (isolated per user)"""
        user_id = session.get("user_id")
        if not user_id:
            return None
        
        conn = sqlite3.connect("users_local.db")
        row = conn.execute(
            "SELECT data_value FROM user_data WHERE user_id = ? AND data_key = ?",
            (user_id, key)
        ).fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None

# Global instance
user_auth = UserAuth()

def require_auth(f):
    """Decorator to require authentication - isolates user access"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Authentication required", "message": "Please login first"}), 401
        return f(*args, **kwargs)
    return decorated

def add_supabase_auth(app):
    """Add authentication routes to existing app"""
    
    @app.route("/api/auth/register", methods=["POST"])
    def auth_register():
        data = request.get_json(force=True)
        email = data.get("email", "").strip()
        password = data.get("password", "")
        full_name = data.get("full_name", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        result = user_auth.register_user(email, password, full_name)
        if result["success"]:
            return jsonify({"success": True, "message": "User registered successfully"})
        return jsonify({"error": result.get("error", "Registration failed")}), 400
    
    @app.route("/api/auth/login", methods=["POST"])
    def auth_login():
        data = request.get_json(force=True)
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        result = user_auth.login_user(email, password)
        if result["success"]:
            return jsonify({
                "success": True,
                "user": result["user"],
                "message": "Logged in successfully"
            })
        return jsonify({"error": result.get("error", "Invalid credentials")}), 401
    
    @app.route("/api/auth/logout", methods=["POST"])
    def auth_logout():
        result = user_auth.logout_user()
        return jsonify(result)
    
    @app.route("/api/auth/me", methods=["GET"])
    @require_auth
    def auth_me():
        user = user_auth.get_current_user()
        if user:
            return jsonify({"user": user})
        return jsonify({"error": "Not logged in"}), 401
    
    @app.route("/api/auth/data/<key>", methods=["GET", "POST"])
    @require_auth
    def user_data(key):
        if request.method == "GET":
            data = user_auth.get_user_data(key)
            return jsonify({"key": key, "data": data})
        else:
            value = request.get_json(force=True)
            result = user_auth.save_user_data(key, value)
            return jsonify(result)
    
    print("✅ Supabase Auth added - User isolation active")
    return app
