"""
SHOPAROUND ECOSYSTEM MANAGER - Pure Add-on
No changes to existing code. Just adds monitoring and security.
"""

import hashlib
import secrets
import sqlite3
import threading
import time
import os
import subprocess
from datetime import datetime
from flask import request, jsonify

# ============================================
# SHA3 Security Layer
# ============================================

class SecurityLayer:
    def __init__(self):
        self.secret = secrets.token_hex(32)
    
    def sha3_hash(self, data):
        return hashlib.sha3_512(data.encode()).hexdigest()
    
    def secure_token(self):
        return secrets.token_urlsafe(64)

# ============================================
# Database Manager
# ============================================

class DatabaseManager:
    def __init__(self):
        self.db_path = "ecosystem.db"
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT,
                action TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def log(self, module, action, message):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO system_logs (module, action, message) VALUES (?, ?, ?)", 
                        (module, action, message))
            conn.commit()
            conn.close()
        except:
            pass

# ============================================
# Process Monitor
# ============================================

class ProcessMonitor:
    def __init__(self):
        self.running = True
        self.db = DatabaseManager()
    
    def check_app(self):
        result = subprocess.run("pgrep -f 'shoparound_professional'", shell=True, capture_output=True)
        return result.returncode == 0
    
    def start_monitoring(self):
        def monitor():
            while self.running:
                if not self.check_app():
                    self.db.log("monitor", "warning", "Main app not running")
                time.sleep(60)
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        return thread

# ============================================
# Ecosystem API
# ============================================

class EcosystemAPI:
    def __init__(self):
        self.security = SecurityLayer()
        self.db = DatabaseManager()
        self.monitor = ProcessMonitor()
    
    def register(self, app):
        
        @app.route("/api/ecosystem/health", methods=["GET"])
        def eco_health():
            app_running = self.monitor.check_app()
            return jsonify({
                "status": "healthy",
                "app": "running" if app_running else "unknown",
                "security": "SHA3-512 active",
                "timestamp": datetime.now().isoformat()
            })
        
        @app.route("/api/ecosystem/hash", methods=["POST"])
        def eco_hash():
            data = request.get_json(force=True)
            hash_val = self.security.sha3_hash(data.get("data", ""))
            return jsonify({"hash": hash_val, "algorithm": "SHA3-512"})
        
        @app.route("/api/ecosystem/token", methods=["GET"])
        def eco_token():
            return jsonify({"token": self.security.secure_token()})
        
        @app.route("/api/ecosystem/logs", methods=["GET"])
        def eco_logs():
            limit = request.args.get("limit", 20, type=int)
            conn = sqlite3.connect("ecosystem.db")
            conn.row_factory = sqlite3.Row
            logs = conn.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            conn.close()
            return jsonify({"logs": [dict(l) for l in logs]})
        
        print("✅ Ecosystem API added")
        return app

ecosystem = EcosystemAPI()

def add_ecosystem(app):
    """Add ecosystem features to your app - NO CHANGES to existing code"""
    app = ecosystem.register(app)
    ecosystem.monitor.start_monitoring()
    print("🧠 Ecosystem Manager Active")
    print("   ✅ SHA3-512 Security")
    print("   ✅ Health Monitoring")
    print("   ✅ System Logging")
    return app
