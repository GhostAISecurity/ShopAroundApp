#!/usr/bin/env python3
"""
SHOPAROUND NEXUS ULTIMATE v9.0
COMPLETE MERGE: Original ShopAround + Neural AI + All v9 Features
NOTHING REMOVED - EVERYTHING ADDED
"""

import sqlite3
import os
import json
import secrets
import math
import requests
import uuid
import hashlib
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=7)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound_ultimate.db")

# ============================================
# PART 1: ORIGINAL SHOPAROUND FEATURES (PRESERVED)
# ============================================

# ========== ORIGINAL RETAILERS DATA ==========
ORIGINAL_RETAILERS = [
    ("Checkers", "Grocery", "https://checkers.co.za", "🛒", 35, 350, 60, 4.2),
    ("Shoprite", "Grocery", "https://shoprite.co.za", "🛒", 35, 350, 60, 4.1),
    ("Woolworths", "Grocery", "https://woolworths.co.za", "🥩", 45, 450, 60, 4.5),
    ("Pick n Pay", "Grocery", "https://pnp.co.za", "🛒", 35, 350, 60, 4.2),
    ("Takealot", "E-commerce", "https://takealot.com", "🛍️", 50, 500, 120, 4.4),
    ("Makro", "E-commerce", "https://makro.co.za", "🏪", 50, 500, 90, 4.0),
    ("Game", "E-commerce", "https://game.co.za", "🎮", 50, 500, 90, 3.9),
    ("Clicks", "Pharmacy", "https://clicks.co.za", "💊", 30, 300, 60, 4.3),
    ("Dischem", "Pharmacy", "https://dischem.co.za", "💊", 30, 300, 60, 4.2),
    ("Builders", "Hardware", "https://builders.co.za", "🔨", 60, 600, 120, 4.0),
]

# ========== ORIGINAL SERVICE PROVIDERS ==========
ORIGINAL_SERVICES = [
    ("Plumbmaster SA", "plumbing", "24/7 Emergency Plumbing", 450, "011 123 4567", -26.2041, 28.0473, "Johannesburg", 4.2),
    ("JHB Electricians", "electrical", "Certified Master Electricians", 400, "011 234 5678", -26.2025, 28.0450, "Braamfontein", 4.5),
    ("Auto Care Centre", "mechanic", "Full Car Repairs & Services", 550, "011 345 6789", -26.2080, 28.0500, "Marshalltown", 4.0),
    ("Rapid Locksmiths", "locksmith", "Lock Installation & Emergency Repairs", 350, "011 456 7890", -26.2000, 28.0400, "Johannesburg", 4.3),
]

# ========== ORIGINAL PRODUCTS ==========
ORIGINAL_PRODUCTS = [
    ("Bread", "Albany", "Grocery", "🍞", 18.99, "loaf"),
    ("Milk 1L", "Clover", "Grocery", "🥛", 22.99, "liter"),
    ("Rice 2kg", "Tastic", "Grocery", "🍚", 45.99, "kg"),
    ("Eggs (dozen)", "Nulaid", "Grocery", "🥚", 44.99, "dozen"),
    ("Chicken 2kg", "Irvine's", "Grocery", "🍗", 89.99, "kg"),
]

# ========== ORIGINAL DELIVERY SERVICES ==========
ORIGINAL_DELIVERY = [
    ("Uber Eats", "Food", 10, 5, "https://ubereats.com", "🚗", 4.3),
    ("Mr D Food", "Food", 10, 4, "https://mrdfood.com", "🍔", 4.2),
    ("Bolt Food", "Food", 8, 4, "https://boltfood.com", "⚡", 4.1),
]

# ============================================
# PART 2: NEURAL AI BRAIN (FROM YOUR FILE)
# ============================================

class NeuralMemory:
    def __init__(self):
        self.conn = sqlite3.connect("neural_memory.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS neural_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT UNIQUE,
                timestamp TEXT,
                context TEXT,
                verdict TEXT,
                approval_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def store(self, decision_id, timestamp, context, verdict, approval_score):
        self.conn.execute("""
            INSERT OR IGNORE INTO neural_decisions (decision_id, timestamp, context, verdict, approval_score)
            VALUES (?, ?, ?, ?, ?)
        """, (decision_id, timestamp, json.dumps(context), verdict, approval_score))
        self.conn.commit()
    
    def recall(self, limit=10):
        cur = self.conn.execute("SELECT * FROM neural_decisions ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

class NeuralBrain:
    def __init__(self):
        self.memory = NeuralMemory()
        self.agents = [
            {"name": "Strategy Agent", "weight": 0.35, "confidence": 0.75},
            {"name": "Risk Agent", "weight": 0.40, "confidence": 0.85},
            {"name": "Financial Agent", "weight": 0.30, "confidence": 0.80},
            {"name": "Operations Agent", "weight": 0.25, "confidence": 0.85},
            {"name": "Founder Agent", "weight": 0.50, "confidence": 0.90}
        ]
    
    def think(self, context):
        risk = context.get("risk_score", 0.5)
        total_weight = sum(a["weight"] for a in self.agents)
        approval = sum(a["weight"] * a["confidence"] for a in self.agents)
        score = approval / total_weight
        if risk > 0.7:
            score = score * 0.5
        elif risk > 0.4:
            score = score * 0.8
        
        verdict = "APPROVED" if score > 0.6 else "DEFERRED" if score > 0.4 else "REJECTED"
        did = str(uuid.uuid4())
        ts = datetime.now().isoformat()
        self.memory.store(did, ts, context, verdict, score)
        return {
            "verdict": verdict,
            "approval_score": round(score, 3),
            "decision_id": did,
            "timestamp": ts,
            "risk_adjusted": risk > 0.4,
            "agents": [{"name": a["name"], "weight": a["weight"], "confidence": a["confidence"]} for a in self.agents]
        }
    
    def status(self):
        return {
            "name": "Sediba Ghost Neural Mind",
            "version": "2.0",
            "agents": [a["name"] for a in self.agents],
            "memory_size": len(self.memory.recall(100))
        }

neural_brain = NeuralBrain()

# ============================================
# PART 3: V9 LAYERED ARCHITECTURE (ADDITIONS)
# ============================================

def run_migrations(db):
    """Automatic database migrations - Self-healing"""
    users_columns = {
        "name": "TEXT",
        "phone_number": "TEXT",
        "is_business": "INTEGER DEFAULT 0",
        "business_type": "TEXT",
        "household_size": "INTEGER DEFAULT 1",
        "monthly_budget": "REAL DEFAULT 0",
        "language": "TEXT DEFAULT 'en'",
        "session_token": "TEXT",
        "preferences": "TEXT DEFAULT '{}'",
        "total_saved": "REAL DEFAULT 0",
        "loyalty_points": "INTEGER DEFAULT 0",
        "last_login": "DATETIME"
    }
    
    cursor = db.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cursor.fetchall()}
    
    for col, definition in users_columns.items():
        if col not in existing:
            try:
                db.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
                print(f"✅ Added column: {col}")
            except:
                pass
    
    # Additional tables
    db.execute("""
        CREATE TABLE IF NOT EXISTS households (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            adults INTEGER DEFAULT 1,
            children INTEGER DEFAULT 0,
            dietary_preferences TEXT,
            allergies TEXT,
            monthly_budget REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS receipt_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shop TEXT,
            raw_text TEXT,
            parsed_items TEXT,
            total_amount REAL,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS geo_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            price REAL,
            shop TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            confidence REAL DEFAULT 0.5,
            source TEXT,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS spaza_shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            owner_name TEXT,
            shop_name TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            whatsapp_number TEXT,
            delivery_available INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner_id) REFERENCES users(id)
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            verified INTEGER DEFAULT 0,
            api_endpoint TEXT,
            website TEXT,
            logo TEXT,
            contact_info TEXT,
            rating REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS price_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            location TEXT,
            predicted_price REAL,
            confidence REAL,
            forecast_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.commit()
    print("✅ Automatic migrations complete")

# ============================================
# PART 4: AUTHENTICATION & SECURITY
# ============================================

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized", "message": "Bearer token required"}), 401
        
        token = auth.split(" ")[1]
        db = get_db()
        user = db.execute("SELECT id, username FROM users WHERE session_token = ?", (token,)).fetchone()
        
        if not user:
            return jsonify({"error": "Unauthorized", "message": "Invalid or expired token"}), 401
        
        request.user = dict(user)
        return f(*args, **kwargs)
    return wrapper

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        run_migrations(g.db)
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db:
        db.close()

# ============================================
# PART 5: USER MANAGEMENT (Enhanced)
# ============================================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    name = data.get("name", username)
    is_business = data.get("is_business", 0)
    business_type = data.get("business_type", "")
    household_size = data.get("household_size", 1)
    language = data.get("language", "en")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    db = get_db()
    try:
        db.execute("""
            INSERT INTO users (username, email, password_hash, name, is_business, business_type, household_size, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, email, generate_password_hash(password), name, is_business, business_type, household_size, language))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409
    
    return jsonify({"success": True, "message": "User created"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
    
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    token = secrets.token_urlsafe(32)
    db.execute("UPDATE users SET session_token = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?", (token, user["id"]))
    db.commit()
    
    return jsonify({
        "success": True,
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "name": user["name"] if "name" in user.keys() else user["username"]}
    })

@app.route("/api/logout", methods=["POST"])
@require_auth
def logout():
    db = get_db()
    db.execute("UPDATE users SET session_token = NULL WHERE id = ?", (request.user["id"],))
    db.commit()
    return jsonify({"success": True})

# ============================================
# PART 6: NEURAL AI ROUTES (From your file)
# ============================================

@app.route("/api/neural/think", methods=["POST"])
def neural_think():
    data = request.get_json(force=True)
    context = {
        "objective": data.get("objective", "Decision"),
        "risk_score": data.get("risk_score", 0.5),
        "amount": data.get("amount", 0)
    }
    return jsonify(neural_brain.think(context))

@app.route("/api/neural/status", methods=["GET"])
def neural_status():
    return jsonify(neural_brain.status())

@app.route("/api/neural/memory", methods=["GET"])
def neural_memory():
    limit = request.args.get("limit", 10, type=int)
    return jsonify({"memories": neural_brain.memory.recall(limit)})

# ============================================
# PART 7: ORIGINAL SHOPAROUND ENDPOINTS (Preserved)
# ============================================

@app.route("/api/retailers", methods=["GET"])
def get_retailers():
    db = get_db()
    retailers = db.execute("SELECT * FROM retailers WHERE is_active = 1").fetchall()
    return jsonify([dict(r) for r in retailers])

@app.route("/api/services", methods=["GET"])
def get_services():
    service_type = request.args.get("type", "")
    db = get_db()
    if service_type:
        services = db.execute("SELECT * FROM service_providers WHERE service_type = ?", (service_type,)).fetchall()
    else:
        services = db.execute("SELECT * FROM service_providers LIMIT 30").fetchall()
    return jsonify([dict(s) for s in services])

@app.route("/api/delivery-services", methods=["GET"])
def get_delivery_services():
    db = get_db()
    services = db.execute("SELECT * FROM delivery_services ORDER BY rating DESC").fetchall()
    return jsonify([dict(s) for s in services])

# ============================================
# PART 8: SHOPPING LISTS (Original preserved)
# ============================================

@app.route("/api/lists", methods=["GET", "POST"])
@require_auth
def shopping_lists():
    db = get_db()
    if request.method == "GET":
        lists = db.execute("SELECT * FROM shopping_lists WHERE user_id = ?", (request.user["id"],)).fetchall()
        return jsonify([dict(l) for l in lists])
    else:
        data = request.get_json(force=True)
        cursor = db.execute("INSERT INTO shopping_lists (user_id, name) VALUES (?, ?)", 
                           (request.user["id"], data.get("name", "My List")))
        db.commit()
        return jsonify({"id": cursor.lastrowid})

@app.route("/api/lists/<int:list_id>/items", methods=["GET", "POST"])
@require_auth
def list_items(list_id):
    db = get_db()
    if request.method == "GET":
        items = db.execute("SELECT * FROM shopping_list_items WHERE list_id = ?", (list_id,)).fetchall()
        return jsonify([dict(i) for i in items])
    else:
        data = request.get_json(force=True)
        db.execute("INSERT INTO shopping_list_items (list_id, product_name, quantity) VALUES (?, ?, ?)",
                  (list_id, data.get("product_name"), data.get("quantity", 1)))
        db.commit()
        return jsonify({"success": True})

# ============================================
# PART 9: V9 ENHANCED FEATURES
# ============================================

@app.route("/api/optimize/basket", methods=["POST"])
def optimize_basket():
    data = request.get_json(force=True)
    budget = data.get("budget", 100)
    items = data.get("items", ["bread", "milk", "rice"])
    
    product_prices = {"bread": 15.99, "milk": 22.99, "rice": 45.99, "eggs": 44.99, "chicken": 89.99}
    basket = []
    total = 0
    
    for item in items:
        price = product_prices.get(item.lower(), 35.00)
        if total + price <= budget:
            basket.append({"item": item, "price": price, "shop": "Checkers"})
            total += price
    
    return jsonify({"basket": basket, "total": round(total, 2), "savings": round(budget - total, 2)})

@app.route("/api/community/report", methods=["POST"])
@require_auth
def report_price():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO geo_prices (item_name, price, shop, location, source, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.get("item"), data.get("price"), data.get("shop"), data.get("location", "User"), "community", request.user["id"]))
    db.commit()
    return jsonify({"report_id": cursor.lastrowid, "message": "Price reported! Thanks for contributing."})

@app.route("/api/community/verified/<item>", methods=["GET"])
def get_verified_prices(item):
    db = get_db()
    prices = db.execute("""
        SELECT item_name, price, shop, location, created_at
        FROM geo_prices
        WHERE item_name LIKE ? AND verified = 1
        ORDER BY created_at DESC LIMIT 20
    """, (f"%{item}%",)).fetchall()
    return jsonify([dict(p) for p in prices])

@app.route("/api/spaza/register", methods=["POST"])
@require_auth
def register_spaza():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO spaza_shops (owner_id, owner_name, shop_name, location, whatsapp_number)
        VALUES (?, ?, ?, ?, ?)
    """, (request.user["id"], data.get("owner_name"), data.get("shop_name"), data.get("location"), data.get("whatsapp_number")))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "message": "Spaza shop registered!"})

@app.route("/api/spaza/nearby", methods=["GET"])
def get_nearby_spazas():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    db = get_db()
    
    if lat and lng:
        spazas = db.execute("""
            SELECT shop_name, location, whatsapp_number, delivery_available,
                   ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) as distance_sq
            FROM spaza_shops WHERE verified = 1
            ORDER BY distance_sq ASC LIMIT 20
        """, (lat, lat, lng, lng)).fetchall()
        for s in spazas:
            s["distance_km"] = round((s["distance_sq"] ** 0.5) * 111, 1) if s["distance_sq"] else None
    else:
        spazas = db.execute("SELECT * FROM spaza_shops WHERE verified = 1 LIMIT 20").fetchall()
    
    return jsonify([dict(s) for s in spazas])

@app.route("/api/forecast/<item>", methods=["GET"])
def forecast_price(item):
    db = get_db()
    history = db.execute("""
        SELECT price, created_at FROM geo_prices
        WHERE item_name LIKE ? ORDER BY created_at DESC LIMIT 30
    """, (f"%{item}%",)).fetchall()
    
    if len(history) < 3:
        return jsonify({"item": item, "status": "insufficient_data"})
    
    prices = [h["price"] for h in history]
    current = prices[0]
    trend = "rising" if len(prices) >= 2 and prices[0] > prices[-1] else "falling" if len(prices) >= 2 and prices[0] < prices[-1] else "stable"
    
    return jsonify({"item": item, "current_price": round(current, 2), "trend": trend, "data_points": len(history)})

@app.route("/api/alerts", methods=["GET", "POST"])
@require_auth
def alerts():
    db = get_db()
    if request.method == "GET":
        alerts_data = db.execute("SELECT * FROM price_alerts WHERE user_id = ? AND is_active = 1", (request.user["id"],)).fetchall()
        return jsonify([dict(a) for a in alerts_data])
    else:
        data = request.get_json(force=True)
        db.execute("INSERT INTO price_alerts (user_id, product_name, target_price) VALUES (?, ?, ?)",
                  (request.user["id"], data.get("product_name"), data.get("target_price")))
        db.commit()
        return jsonify({"success": True})

@app.route("/api/health", methods=["GET"])
def health():
    db = get_db()
    stats = {
        "users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "retailers": db.execute("SELECT COUNT(*) FROM retailers").fetchone()[0],
        "services": db.execute("SELECT COUNT(*) FROM service_providers").fetchone()[0],
        "price_reports": db.execute("SELECT COUNT(*) FROM geo_prices").fetchone()[0],
        "neural_active": True
    }
    return jsonify({"status": "healthy", "version": "ULTIMATE v9.0", "statistics": stats})

# ============================================
# PART 10: INITIALIZE DATABASE WITH ORIGINAL DATA
# ============================================

def init_database():
    db = sqlite3.connect(DB_PATH)
    
    # Users table
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Retailers table
    db.execute("""
        CREATE TABLE IF NOT EXISTS retailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            website TEXT,
            logo TEXT,
            delivery_fee REAL DEFAULT 35,
            free_delivery_min REAL DEFAULT 350,
            delivery_minutes INTEGER DEFAULT 60,
            rating REAL DEFAULT 4.0,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Service providers
    db.execute("""
        CREATE TABLE IF NOT EXISTS service_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service_type TEXT,
            description TEXT,
            hourly_rate REAL,
            phone TEXT,
            latitude REAL,
            longitude REAL,
            address TEXT,
            rating REAL DEFAULT 0,
            verified INTEGER DEFAULT 0
        )
    """)
    
    # Products
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            emoji TEXT DEFAULT '🛒',
            typical_price REAL,
            unit TEXT DEFAULT 'piece'
        )
    """)
    
    # Delivery services
    db.execute("""
        CREATE TABLE IF NOT EXISTS delivery_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service_type TEXT,
            base_fee REAL,
            per_km_rate REAL,
            website TEXT,
            logo TEXT,
            rating REAL DEFAULT 4.0
        )
    """)
    
    # Shopping lists (original)
    db.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT DEFAULT 'My List',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER,
            product_name TEXT,
            quantity REAL DEFAULT 1,
            checked_off INTEGER DEFAULT 0
        )
    """)
    
    # Price alerts
    db.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            target_price REAL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed original retailers
    for r in ORIGINAL_RETAILERS:
        db.execute("INSERT OR IGNORE INTO retailers (name, category, website, logo, delivery_fee, free_delivery_min, delivery_minutes, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", r)
    
    # Seed original services
    for s in ORIGINAL_SERVICES:
        db.execute("INSERT OR IGNORE INTO service_providers (name, service_type, description, hourly_rate, phone, latitude, longitude, address, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", s)
    
    # Seed original products
    for p in ORIGINAL_PRODUCTS:
        db.execute("INSERT OR IGNORE INTO products (product_name, brand, category, emoji, typical_price, unit) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # Seed original delivery services
    for d in ORIGINAL_DELIVERY:
        db.execute("INSERT OR IGNORE INTO delivery_services (name, service_type, base_fee, per_km_rate, website, logo, rating) VALUES (?, ?, ?, ?, ?, ?, ?)", d)
    
    db.commit()
    db.close()
    print("✅ Original ShopAround data seeded")

# Run migrations and init
run_migrations(sqlite3.connect(DB_PATH))
init_database()

# ============================================
# PART 11: BEAUTIFUL FRONTEND
# ============================================

FRONTEND_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Ultimate v9 - Complete Ecosystem</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:system-ui,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}
        .container{max-width:1200px;margin:0 auto;}
        .navbar{background:white;border-radius:1rem;padding:1rem 2rem;margin-bottom:1rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;}
        .navbar h1{color:#1f8a4c;}
        .nav-links{display:flex;gap:1rem;flex-wrap:wrap;}
        .nav-links a{color:#666;text-decoration:none;cursor:pointer;padding:0.5rem 1rem;border-radius:0.5rem;}
        .nav-links a:hover{background:#f0f0f0;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;border-bottom:2px solid #e5e7eb;padding-bottom:0.5rem;flex-wrap:wrap;}
        h2{color:#1f8a4c;}
        input,select,button,textarea{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #ddd;border-radius:0.5rem;}
        button{background:#1f8a4c;color:white;border:none;cursor:pointer;font-weight:bold;}
        button:hover{background:#166b3a;}
        .hidden{display:none;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem;}
        .item-row{display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid #eee;}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-bottom:1rem;}
        .stat-card{background:#e8f5e9;padding:1rem;border-radius:0.5rem;text-align:center;}
        .stat-value{font-size:1.8rem;font-weight:bold;color:#1f8a4c;}
        .tabs{display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap;}
        .tab{padding:0.5rem 1rem;background:#e5e7eb;border-radius:2rem;cursor:pointer;}
        .tab.active{background:#1f8a4c;color:white;}
        .badge{display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;font-size:0.75rem;}
        .badge-success{background:#d1fae5;color:#10b981;}
        .badge-warning{background:#fed7aa;color:#f59e0b;}
        .auth-container{max-width:450px;margin:2rem auto;}
        @media (max-width:768px){.grid{grid-template-columns:1fr;}}
    </style>
</head>
<body>
<div class="container">
    <div id="authContainer" class="auth-container">
        <div class="card" id="loginCard">
            <h2>🛍️ ShopAround Ultimate v9</h2>
            <p style="color:#666; margin-bottom:1rem;">Complete Shopping Intelligence Ecosystem</p>
            <input type="text" id="loginUsername" placeholder="Username">
            <input type="password" id="loginPassword" placeholder="Password">
            <button onclick="login()">Login</button>
            <button onclick="showRegister()" style="background:#666; margin-top:0.5rem;">Create Account</button>
        </div>
        <div class="card hidden" id="registerCard">
            <h2>Create Account</h2>
            <input type="text" id="regUsername" placeholder="Username">
            <input type="email" id="regEmail" placeholder="Email">
            <input type="password" id="regPassword" placeholder="Password">
            <input type="text" id="regName" placeholder="Full Name">
            <button onclick="register()">Register</button>
            <button onclick="showLogin()" style="background:#666; margin-top:0.5rem;">Back</button>
        </div>
    </div>

    <div id="mainApp" class="hidden">
        <div class="navbar">
            <h1>🛍️ ShopAround Ultimate v9</h1>
            <div class="nav-links">
                <a onclick="showSection('planner')">Planner</a>
                <a onclick="showSection('retailers')">Retailers</a>
                <a onclick="showSection('services')">Services</a>
                <a onclick="showSection('spaza')">Spaza</a>
                <a onclick="showSection('neural')">Neural AI</a>
                <a onclick="logout()" style="color:#dc2626;">Logout</a>
            </div>
        </div>

        <div class="stats" id="statsPanel"></div>

        <div id="plannerSection">
            <div class="card">
                <div class="card-header"><h2>🛒 Smart Shopping Planner</h2></div>
                <input type="number" id="budget" placeholder="Budget (R)" value="200">
                <textarea id="itemsList" rows="3" placeholder="Items (one per line)&#10;bread&#10;milk&#10;rice"></textarea>
                <button onclick="optimizeBasket()">✨ Optimize Shopping</button>
                <div id="optimizeResult"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>🧠 Neural AI Decision</h2></div>
                <input type="text" id="aiQuestion" placeholder="What decision?">
                <input type="number" id="aiAmount" placeholder="Amount (R)" value="5000">
                <input type="number" id="aiRisk" placeholder="Risk (0-1)" value="0.3" step="0.1">
                <button onclick="consultAI()">Get AI Decision</button>
                <div id="aiResult"></div>
            </div>
        </div>

        <div id="retailersSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🏪 Major Retailers</h2></div><div id="retailersGrid" class="grid"></div></div>
            <div class="card"><div class="card-header"><h2>🚚 Delivery Services</h2></div><div id="deliveryGrid" class="grid"></div></div>
        </div>

        <div id="servicesSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🛠️ Service Providers</h2></div><select id="serviceFilter"><option value="">All</option><option value="plumbing">Plumbing</option><option value="electrical">Electrical</option><option value="mechanic">Mechanic</option></select><button onclick="loadServices()">Search</button><div id="servicesList"></div></div>
        </div>

        <div id="spazaSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🏪 Register Spaza Shop</h2></div><input type="text" id="spazaName" placeholder="Shop Name"><input type="text" id="spazaLocation" placeholder="Location"><input type="text" id="spazaWhatsapp" placeholder="WhatsApp"><button onclick="registerSpaza()">Register</button></div>
            <div class="card"><div class="card-header"><h2>📍 Nearby Spazas</h2></div><button onclick="findNearbySpazas()">Find Nearby</button><div id="nearbySpazas"></div></div>
        </div>

        <div id="neuralSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🧠 Neural Brain Status</h2></div><div id="neuralStatus"></div></div>
            <div class="card"><div class="card-header"><h2>📜 Decision Memory</h2></div><div id="neuralMemory"></div></div>
        </div>
    </div>
</div>

<script>
let authToken = null;

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,password})});
    const data = await res.json();
    if (data.success) {
        authToken = data.token;
        localStorage.setItem('token', authToken);
        document.getElementById('authContainer').classList.add('hidden');
        document.getElementById('mainApp').classList.remove('hidden');
        loadStats(); loadRetailers(); loadDelivery();
    } else alert('Login failed');
}

async function register() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const name = document.getElementById('regName').value;
    const res = await fetch('/api/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,email,password,name})});
    const data = await res.json();
    if (data.success) { alert('Registered! Please login.'); showLogin(); }
    else alert('Registration failed');
}

function logout() { localStorage.removeItem('token'); location.reload(); }
function showRegister() { document.getElementById('loginCard').classList.add('hidden'); document.getElementById('registerCard').classList.remove('hidden'); }
function showLogin() { document.getElementById('registerCard').classList.add('hidden'); document.getElementById('loginCard').classList.remove('hidden'); }

function showSection(s) {
    const sections = ['planner', 'retailers', 'services', 'spaza', 'neural'];
    sections.forEach(sec => document.getElementById(sec+'Section').classList.add('hidden'));
    document.getElementById(s+'Section').classList.remove('hidden');
    if (s === 'neural') { loadNeuralStatus(); loadNeuralMemory(); }
}

async function loadStats() {
    const res = await fetch('/api/health');
    const data = await res.json();
    document.getElementById('statsPanel').innerHTML = `
        <div class="stat-card"><div class="stat-value">${data.statistics.users||0}</div><div>Users</div></div>
        <div class="stat-card"><div class="stat-value">${data.statistics.retailers||0}</div><div>Retailers</div></div>
        <div class="stat-card"><div class="stat-value">${data.statistics.price_reports||0}</div><div>Price Reports</div></div>
    `;
}

async function loadRetailers() {
    const res = await fetch('/api/retailers');
    const retailers = await res.json();
    document.getElementById('retailersGrid').innerHTML = retailers.map(r => `<div class="card"><strong>${r.logo||'🏪'} ${r.name}</strong><br>⭐ ${r.rating}<br>🚚 R${r.delivery_fee}</div>`).join('');
}

async function loadDelivery() {
    const res = await fetch('/api/delivery-services');
    const services = await res.json();
    document.getElementById('deliveryGrid').innerHTML = services.map(s => `<div class="card"><strong>${s.logo||'🚚'} ${s.name}</strong><br>Base: R${s.base_fee} + R${s.per_km_rate}/km<br>⭐ ${s.rating}</div>`).join('');
}

async function loadServices() {
    const type = document.getElementById('serviceFilter').value;
    const res = await fetch(`/api/services${type?`?type=${type}`:''}`);
    const services = await res.json();
    document.getElementById('servicesList').innerHTML = services.map(s => `<div class="card"><strong>🔧 ${s.name}</strong><br>${s.service_type}<br>📞 ${s.phone}</div>`).join('');
}

async function optimizeBasket() {
    const budget = document.getElementById('budget').value;
    const itemsText = document.getElementById('itemsList').value;
    const items = itemsText.split('\\n').filter(i => i.trim());
    const res = await fetch('/api/optimize/basket', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({budget:parseFloat(budget), items})});
    const data = await res.json();
    let html = `<div class="stats"><div class="stat-card">Total: R${data.total}</div><div class="stat-card">Savings: R${data.savings}</div></div>`;
    data.basket.forEach(i => html += `<div class="item-row"><span>${i.item}</span><span>R${i.price}</span><span>${i.shop}</span></div>`);
    document.getElementById('optimizeResult').innerHTML = html;
}

async function consultAI() {
    const objective = document.getElementById('aiQuestion').value || "Business decision";
    const amount = parseFloat(document.getElementById('aiAmount').value);
    const risk = parseFloat(document.getElementById('aiRisk').value);
    const res = await fetch('/api/neural/think', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({objective, amount, risk_score: risk})});
    const data = await res.json();
    const badge = data.verdict === 'APPROVED' ? 'badge-success' : (data.verdict === 'DEFERRED' ? 'badge-warning' : 'badge');
    document.getElementById('aiResult').innerHTML = `<div class="card"><strong>🧠 AI Decision:</strong> <span class="${badge}">${data.verdict}</span><br>Approval: ${(data.approval_score*100).toFixed(0)}%<br>Risk Adjusted: ${data.risk_adjusted ? 'Yes' : 'No'}</div>`;
}

async function registerSpaza() {
    const shop_name = document.getElementById('spazaName').value;
    const location = document.getElementById('spazaLocation').value;
    const whatsapp = document.getElementById('spazaWhatsapp').value;
    const res = await fetch('/api/spaza/register', {method:'POST', headers:{'Content-Type':'application/json', 'Authorization': `Bearer ${authToken}`}, body:JSON.stringify({shop_name, location, whatsapp_number: whatsapp})});
    const data = await res.json();
    alert(data.message);
}

async function findNearbySpazas() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const res = await fetch(`/api/spaza/nearby?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`);
            const spazas = await res.json();
            document.getElementById('nearbySpazas').innerHTML = spazas.map(s => `<div class="item-row"><span>🏪 ${s.shop_name}</span><span>${s.distance_km ? s.distance_km+'km' : s.location}</span></div>`).join('');
        });
    } else alert('Geolocation not supported');
}

async function loadNeuralStatus() {
    const res = await fetch('/api/neural/status');
    const data = await res.json();
    document.getElementById('neuralStatus').innerHTML = `<div class="stats"><div class="stat-card"><div class="stat-value">${data.name}</div><div>Neural Brain</div></div><div class="stat-card"><div class="stat-value">${data.agents.length}</div><div>AI Agents</div></div><div class="stat-card"><div class="stat-value">${data.memory_size||0}</div><div>Decisions Made</div></div></div>`;
}

async function loadNeuralMemory() {
    const res = await fetch('/api/neural/memory?limit=5');
    const data = await res.json();
    document.getElementById('neuralMemory').innerHTML = (data.memories||[]).map(m => `<div class="item-row"><span>${m.verdict}</span><span>${(m.approval_score*100).toFixed(0)}%</span><span>${new Date(m.created_at).toLocaleString()}</span></div>`).join('');
}

// Auto login from stored token
const token = localStorage.getItem('token');
if (token) {
    authToken = token;
    document.getElementById('authContainer').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    loadStats(); loadRetailers(); loadDelivery();
}
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(FRONTEND_HTML)

if __name__ == "__main__":
    print("="*70)
    print("🏆 SHOPAROUND ULTIMATE v9.0 - COMPLETE MERGE")
    print("="*70)
    print("✅ Original ShopAround Features (Retailers, Services, Products, Delivery)")
    print("✅ Neural AI Brain (5 Agents, Memory, Decision Engine)")
    print("✅ V9 Layered Architecture (Migrations, Auth, Households, Receipts, Spaza, Forecasting)")
    print("✅ ALL ORIGINAL FUNCTIONALITY PRESERVED")
    print("✅ NOTHING REMOVED - EVERYTHING ADDED")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=False)
