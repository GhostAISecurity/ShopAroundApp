"""
SUPABASE INTEGRATION - Graceful fallback
"""

import os
import hashlib
import secrets
from flask import request, jsonify, session

# Try to load config safely
SUPABASE_URL = ""
SUPABASE_ANON_KEY = ""
HAS_CONFIG = False

try:
    from supabase_config import SUPABASE_URL as _URL, SUPABASE_ANON_KEY as _KEY
    if _URL and _KEY and "YOUR_PROJECT_ID" not in _URL:
        SUPABASE_URL = _URL
        SUPABASE_ANON_KEY = _KEY
        HAS_CONFIG = True
except ImportError:
    pass
except Exception:
    pass

# Try to import supabase
SUPABASE_AVAILABLE = False
try:
    from supabase import create_client
    if HAS_CONFIG:
        SUPABASE_AVAILABLE = True
except ImportError:
    pass

class SupabaseAuth:
    def __init__(self):
        self.client = None
        if SUPABASE_AVAILABLE and HAS_CONFIG:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                print("✅ Supabase connected!")
            except Exception as e:
                print(f"⚠️ Supabase connection failed: {e}")
    
    def register_user(self, email, password, metadata=None):
        if self.client:
            try:
                response = self.client.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {"data": metadata or {}}
                })
                return {"success": True, "user": response.user}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Supabase not configured - using local auth"}
    
    def login_user(self, email, password):
        if self.client:
            try:
                response = self.client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                session["supabase_token"] = response.session.access_token
                session["user_id"] = response.user.id
                return {"success": True, "user": response.user}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Supabase not configured"}
    
    def get_current_user(self):
        if self.client and session.get("supabase_token"):
            try:
                self.client.auth.set_session(session["supabase_token"])
                user = self.client.auth.get_user()
                return user.user
            except:
                pass
        return None
    
    def logout_user(self):
        session.clear()
        return {"success": True}

supabase_auth = SupabaseAuth()

def add_supabase_routes(app):
    @app.route("/api/supabase/register", methods=["POST"])
    def supabase_register():
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        result = supabase_auth.register_user(email, password, {"full_name": full_name})
        if result.get("success"):
            return jsonify({"success": True, "message": "User registered!"})
        return jsonify({"error": result.get("error", "Registration failed")}), 400
    
    @app.route("/api/supabase/login", methods=["POST"])
    def supabase_login():
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        result = supabase_auth.login_user(email, password)
        if result.get("success"):
            return jsonify({"success": True, "user": {"email": result["user"].email}})
        return jsonify({"error": result.get("error", "Login failed")}), 401
    
    @app.route("/api/supabase/logout", methods=["POST"])
    def supabase_logout():
        return jsonify(supabase_auth.logout_user())
    
    @app.route("/api/supabase/me", methods=["GET"])
    def supabase_me():
        user = supabase_auth.get_current_user()
        if user:
            return jsonify({"user": {"id": user.id, "email": user.email}})
        return jsonify({"error": "Not logged in"}), 401
    
    print("✅ Supabase routes added (using local fallback)")
    return app
