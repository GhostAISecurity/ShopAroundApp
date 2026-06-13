#!/usr/bin/env python3
"""
SHOPAROUND - COMPLETE ONLINE MALL
Fully working version with all features
"""

import sqlite3
import os
import json
import secrets
import math
import requests
import uuid
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ====================================================
# NEURAL BRAIN
# ====================================================

@dataclass(frozen=True)
class Kernel:
    name: str = "SEDIBA GHOST OMNIVERSAL NEURAL MIND"
    version: str = "3.0.0"
    founder: str = "Lukie Sediba"
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class NeuralMemory:
    def __init__(self, db_path: str = "neural_memory.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS neural_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                timestamp TEXT,
                context TEXT,
                evaluations TEXT,
                verdict TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def remember(self, event: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR IGNORE INTO neural_events (event_id, timestamp, context, evaluations, verdict)
            VALUES (?, ?, ?, ?, ?)
        """, (event["id"], event["timestamp"], json.dumps(event["context"]), 
              json.dumps(event["evaluations"]), event["verdict"]))
        conn.commit()
        conn.close()
    
    def recall(self, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM neural_events ORDER BY created_at DESC LIMIT ?", (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

class StrategyAgent:
    name = "Strategy Agent"
    weight = 0.35
    def evaluate(self, context):
        return {"agent": self.name, "recommendation": "EXPAND", "confidence": 0.75, "reason": "Growth opportunity", "weight": self.weight}

class RiskAgent:
    name = "Risk Agent"
    weight = 0.40
    def evaluate(self, context):
        risk = context.get("risk_score", 0.5)
        rec = "APPROVE" if risk < 0.7 else "REQUIRE_REVIEW"
        return {"agent": self.name, "recommendation": rec, "confidence": 0.85, "reason": f"Risk score: {risk}", "weight": self.weight}

class FinancialAgent:
    name = "Financial Agent"
    weight = 0.30
    def evaluate(self, context):
        return {"agent": self.name, "recommendation": "OPTIMIZE", "confidence": 0.80, "reason": "Financial analysis complete", "weight": self.weight}

class OperationsAgent:
    name = "Operations Agent"
    weight = 0.25
    def evaluate(self, context):
        return {"agent": self.name, "recommendation": "EXECUTE", "confidence": 0.85, "reason": "Operational capacity available", "weight": self.weight}

class FounderAgent:
    name = "Founder Agent"
    weight = 0.50
    def evaluate(self, context):
        return {"agent": self.name, "recommendation": "APPROVE", "confidence": 0.90, "reason": "Aligns with Sediba vision", "weight": self.weight}

class DecisionEngine:
    def decide(self, evaluations):
        positive_recs = ["APPROVE", "EXECUTE", "EXPAND", "OPTIMIZE"]
        approval_votes = sum(e["weight"] * e["confidence"] for e in evaluations if e["recommendation"] in positive_recs)
        total_weight = sum(e["weight"] for e in evaluations)
        approval_score = approval_votes / total_weight if total_weight > 0 else 0
        if approval_score >= 0.6:
            return {"verdict": "APPROVED", "action": "PROCEED", "approval_score": approval_score}
        elif approval_score >= 0.4:
            return {"verdict": "DEFERRED", "action": "REQUIRE_REVIEW", "approval_score": approval_score}
        return {"verdict": "REJECTED", "action": "HALT", "approval_score": approval_score}

class GhostBrain:
    def __init__(self):
        self.kernel = Kernel()
        self.memory = NeuralMemory()
        self.agents = [StrategyAgent(), RiskAgent(), FinancialAgent(), OperationsAgent(), FounderAgent()]
        self.engine = DecisionEngine()
    
    def think(self, context):
        evaluations = [agent.evaluate(context) for agent in self.agents]
        decision = self.engine.decide(evaluations)
        event = {"id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(), "context": context, "evaluations": evaluations, "verdict": decision["verdict"], "approval_score": decision["approval_score"]}
        self.memory.remember(event)
        return event
    
    def get_status(self):
        return {"kernel": {"name": self.kernel.name, "version": self.kernel.version}, "agents": [a.name for a in self.agents]}

neural_brain = GhostBrain()

# ====================================================
# FLASK APP
# ====================================================

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound.db")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)

# ====================================================
# DATABASE INITIALIZATION
# ====================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            household_size INTEGER DEFAULT 1,
            monthly_budget REAL,
            is_business INTEGER DEFAULT 0,
            business_name TEXT,
            business_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    
    # Retailers table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS retailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            subcategory TEXT,
            website TEXT,
            logo TEXT,
            delivery_fee REAL DEFAULT 35,
            free_delivery_min REAL DEFAULT 350,
            delivery_minutes INTEGER DEFAULT 60,
            rating REAL DEFAULT 4.0,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Delivery services table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delivery_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            service_type TEXT,
            base_fee REAL,
            per_km_rate REAL,
            website TEXT,
            logo TEXT,
            rating REAL DEFAULT 4.0
        )
    """)
    
    # Pharmacies table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pharmacies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL,
            phone TEXT,
            delivery_available INTEGER DEFAULT 1,
            delivery_fee REAL DEFAULT 30,
            rating REAL DEFAULT 4.2
        )
    """)
    
    # Spaza shops table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spaza_shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            shop_name TEXT NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL,
            phone TEXT,
            whatsapp TEXT,
            category TEXT,
            verified INTEGER DEFAULT 0,
            rating REAL DEFAULT 0,
            opening_time TEXT DEFAULT '08:00',
            closing_time TEXT DEFAULT '20:00',
            delivery_available INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Service providers table (CORRECT column names)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS service_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            service_type TEXT,
            description TEXT,
            hourly_rate REAL,
            phone TEXT,
            latitude REAL,
            longitude REAL,
            address TEXT,
            rating REAL DEFAULT 0,
            verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Products table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            subcategory TEXT,
            barcode TEXT,
            emoji TEXT DEFAULT '🛒',
            typical_price REAL,
            unit TEXT DEFAULT 'piece',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Shopping lists table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT DEFAULT 'My List',
            total_budget REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Shopping list items table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity REAL DEFAULT 1,
            priority INTEGER DEFAULT 1,
            checked_off INTEGER DEFAULT 0,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Community prices table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS community_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            retailer_name TEXT,
            price REAL,
            location TEXT,
            latitude REAL,
            longitude REAL,
            verified INTEGER DEFAULT 0,
            upvotes INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Price alerts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            target_price REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Orders table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            list_id INTEGER,
            retailer_id INTEGER,
            total_amount REAL,
            delivery_fee REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            tracking_number TEXT,
            ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            delivered_at DATETIME
        )
    """)
    
    # Businesses table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            business_name TEXT NOT NULL,
            business_type TEXT,
            registration_number TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ====================================================
    # SEED DATA
    # ====================================================
    
    # Seed retailers
    retailers = [
        ("Checkers", "Grocery", "Supermarket", "https://checkers.co.za", "🛒", 35, 350, 60, 4.2),
        ("Shoprite", "Grocery", "Supermarket", "https://shoprite.co.za", "🛒", 35, 350, 60, 4.1),
        ("Woolworths", "Grocery", "Premium", "https://woolworths.co.za", "🥩", 45, 450, 60, 4.5),
        ("Pick n Pay", "Grocery", "Supermarket", "https://pnp.co.za", "🛒", 35, 350, 60, 4.2),
        ("Takealot", "E-commerce", "General", "https://takealot.com", "🛍️", 50, 500, 120, 4.4),
        ("Makro", "E-commerce", "Wholesale", "https://makro.co.za", "🏪", 50, 500, 90, 4.0),
        ("Game", "E-commerce", "General", "https://game.co.za", "🎮", 50, 500, 90, 3.9),
        ("Clicks", "Pharmacy", "Health", "https://clicks.co.za", "💊", 30, 300, 60, 4.3),
        ("Dischem", "Pharmacy", "Health", "https://dischem.co.za", "💊", 30, 300, 60, 4.2),
        ("Builders", "Hardware", "DIY", "https://builders.co.za", "🔨", 60, 600, 120, 4.0),
        ("Incredible Connection", "Electronics", "Tech", "https://incredible.co.za", "💻", 60, 600, 90, 4.1),
        ("Zando", "Fashion", "Clothing", "https://zando.co.za", "👕", 50, 500, 90, 4.3),
        ("Superbalist", "Fashion", "Clothing", "https://superbalist.com", "👗", 50, 500, 90, 4.4),
        ("Baby City", "Baby", "Toddler", "https://babycity.co.za", "👶", 50, 500, 90, 4.2),
        ("AutoTrader", "Auto", "Cars", "https://autotrader.co.za", "🚗", 0, 0, 0, 4.3),
    ]
    for r in retailers:
        conn.execute("INSERT OR IGNORE INTO retailers (name, category, subcategory, website, logo, delivery_fee, free_delivery_min, delivery_minutes, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", r)
    
    # Seed delivery services
    delivery = [
        ("Uber Eats", "Food", 10, 5, "https://ubereats.com", "🚗", 4.3),
        ("Mr D Food", "Food", 10, 4, "https://mrdfood.com", "🍔", 4.2),
        ("Bolt Food", "Food", 8, 4, "https://boltfood.com", "⚡", 4.1),
    ]
    for d in delivery:
        conn.execute("INSERT OR IGNORE INTO delivery_services (name, service_type, base_fee, per_km_rate, website, logo, rating) VALUES (?, ?, ?, ?, ?, ?, ?)", d)
    
    # Seed service providers (using 'name' column)
    services = [
        ("Plumbmaster SA", "plumbing", "24/7 Emergency Plumbing", 450, "011 123 4567", -26.2041, 28.0473, "Johannesburg", 4.2),
        ("JHB Electricians", "electrical", "Certified Electricians", 400, "011 234 5678", -26.2025, 28.0450, "Johannesburg", 4.5),
        ("Auto Care Centre", "mechanic", "Car Repairs & Services", 550, "011 345 6789", -26.2080, 28.0500, "Johannesburg", 4.0),
        ("Rapid Locksmiths", "locksmith", "Lock Installation & Repair", 350, "011 456 7890", -26.2000, 28.0400, "Johannesburg", 4.3),
        ("Clean Sweep", "cleaning", "Professional Cleaning", 250, "011 567 8901", -26.2100, 28.0550, "Johannesburg", 4.4),
        ("Green Thumb", "gardening", "Garden Services", 300, "011 678 9012", -26.1950, 28.0450, "Johannesburg", 4.3),
    ]
    for s in services:
        conn.execute("INSERT OR IGNORE INTO service_providers (name, service_type, description, hourly_rate, phone, latitude, longitude, address, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", s)
    
    # Seed products
    products = [
        ("Bread", "Albany", "Grocery", "Bakery", None, "🍞", 18.99, "loaf"),
        ("Milk 1L", "Clover", "Grocery", "Dairy", None, "🥛", 22.99, "liter"),
        ("Rice 2kg", "Tastic", "Grocery", "Pantry", None, "🍚", 45.99, "kg"),
        ("Eggs (dozen)", "Nulaid", "Grocery", "Dairy", None, "🥚", 44.99, "dozen"),
        ("Chicken 2kg", "Irvine's", "Grocery", "Meat", None, "🍗", 89.99, "kg"),
        ("Sugar 2.5kg", "Ilovo", "Grocery", "Pantry", None, "🍬", 39.99, "kg"),
        ("Cooking Oil 750ml", "Sunfoil", "Grocery", "Pantry", None, "🫒", 54.99, "bottle"),
        ("Toothpaste", "Colgate", "Health", "Oral Care", None, "🪥", 24.99, "tube"),
    ]
    for p in products:
        conn.execute("INSERT OR IGNORE INTO products (product_name, brand, category, subcategory, barcode, emoji, typical_price, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", p)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with complete schema and data")

# Initialize database
init_db()

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db:
        db.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

# ====================================================
# API ROUTES
# ====================================================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, generate_password_hash(password)))
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
    
    session["user_id"] = user["id"]
    db.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
    db.commit()
    
    return jsonify({"id": user["id"], "username": user["username"]})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

# ====================================================
# RETAILER ROUTES
# ====================================================
@app.route("/api/retailers", methods=["GET"])
def get_retailers():
    db = get_db()
    retailers = db.execute("SELECT * FROM retailers WHERE is_active = 1 ORDER BY rating DESC").fetchall()
    return jsonify([dict(r) for r in retailers])

@app.route("/api/retailers/categories", methods=["GET"])
def get_retailer_categories():
    db = get_db()
    categories = db.execute("SELECT DISTINCT category FROM retailers ORDER BY category").fetchall()
    return jsonify([c["category"] for c in categories])

# ====================================================
# SERVICE PROVIDER ROUTES
# ====================================================
@app.route("/api/services", methods=["GET"])
def get_services():
    service_type = request.args.get("type", "")
    db = get_db()
    if service_type:
        providers = db.execute("SELECT * FROM service_providers WHERE service_type = ? AND verified = 1", (service_type,)).fetchall()
    else:
        providers = db.execute("SELECT * FROM service_providers WHERE verified = 1 LIMIT 30").fetchall()
    return jsonify([dict(p) for p in providers])

@app.route("/api/services/register", methods=["POST"])
@login_required
def register_service():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO service_providers (user_id, name, service_type, description, hourly_rate, phone, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session["user_id"], data.get("name"), data.get("service_type"), data.get("description"), data.get("hourly_rate"), data.get("phone"), data.get("address")))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "message": "Service provider registered"})

# ====================================================
# SHOPPING LISTS
# ====================================================
@app.route("/api/lists", methods=["GET", "POST"])
@login_required
def handle_lists():
    db = get_db()
    if request.method == "GET":
        lists = db.execute("""
            SELECT sl.*, COUNT(sli.id) as item_count
            FROM shopping_lists sl
            LEFT JOIN shopping_list_items sli ON sli.list_id = sl.id
            WHERE sl.user_id = ?
            GROUP BY sl.id
            ORDER BY sl.created_at DESC
        """, (session["user_id"],)).fetchall()
        return jsonify([dict(l) for l in lists])
    else:
        data = request.get_json(force=True)
        cursor = db.execute("INSERT INTO shopping_lists (user_id, name, total_budget) VALUES (?, ?, ?)", (session["user_id"], data.get("name", "My List"), data.get("budget", 0)))
        db.commit()
        return jsonify({"id": cursor.lastrowid})

@app.route("/api/lists/<int:list_id>/items", methods=["GET", "POST"])
@login_required
def handle_list_items(list_id):
    db = get_db()
    owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not owner or owner["user_id"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    if request.method == "GET":
        items = db.execute("SELECT * FROM shopping_list_items WHERE list_id = ? ORDER BY created_at DESC", (list_id,)).fetchall()
        return jsonify([dict(i) for i in items])
    else:
        data = request.get_json(force=True)
        db.execute("INSERT INTO shopping_list_items (list_id, product_name, quantity) VALUES (?, ?, ?)", (list_id, data.get("product_name"), data.get("quantity", 1)))
        db.commit()
        return jsonify({"success": True})

@app.route("/api/lists/<int:list_id>/items/<int:item_id>", methods=["DELETE", "PUT"])
@login_required
def modify_item(list_id, item_id):
    db = get_db()
    if request.method == "DELETE":
        db.execute("DELETE FROM shopping_list_items WHERE id = ?", (item_id,))
        db.commit()
        return jsonify({"success": True})
    else:
        data = request.get_json(force=True)
        db.execute("UPDATE shopping_list_items SET checked_off = ? WHERE id = ?", (data.get("checked_off", 1), item_id))
        db.commit()
        return jsonify({"success": True})

# ====================================================
# PRICE ALERTS
# ====================================================
@app.route("/api/alerts", methods=["GET", "POST"])
@login_required
def handle_alerts():
    db = get_db()
    if request.method == "GET":
        alerts = db.execute("SELECT * FROM price_alerts WHERE user_id = ? AND is_active = 1", (session["user_id"],)).fetchall()
        return jsonify([dict(a) for a in alerts])
    else:
        data = request.get_json(force=True)
        db.execute("INSERT INTO price_alerts (user_id, product_name, target_price) VALUES (?, ?, ?)", (session["user_id"], data.get("product_name"), data.get("target_price")))
        db.commit()
        return jsonify({"success": True})

@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
@login_required
def delete_alert(alert_id):
    db = get_db()
    db.execute("UPDATE price_alerts SET is_active = 0 WHERE id = ? AND user_id = ?", (alert_id, session["user_id"]))
    db.commit()
    return jsonify({"success": True})

# ====================================================
# NEURAL BRAIN ROUTES
# ====================================================
@app.route("/api/brain/think", methods=["POST"])
def brain_think():
    data = request.get_json(force=True)
    context = {"objective": data.get("objective", "Decision"), "risk_score": data.get("risk_score", 0.5), "amount": data.get("amount", 0)}
    result = neural_brain.think(context)
    return jsonify(result)

@app.route("/api/brain/status", methods=["GET"])
def brain_status():
    return jsonify(neural_brain.get_status())

@app.route("/api/brain/memory", methods=["GET"])
def brain_memory():
    limit = request.args.get("limit", 10, type=int)
    memories = neural_brain.memory.recall(limit)
    return jsonify({"memories": memories})

# ====================================================
# DELIVERY SERVICES
# ====================================================
@app.route("/api/delivery-services", methods=["GET"])
def get_delivery_services():
    db = get_db()
    services = db.execute("SELECT * FROM delivery_services ORDER BY rating DESC").fetchall()
    return jsonify([dict(s) for s in services])

# ====================================================
# LOCATION
# ====================================================
@app.route("/api/location/detect", methods=["GET"])
def detect_location():
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({"latitude": data.get("lat", -26.2041), "longitude": data.get("lon", 28.0473), "city": data.get("city", "Johannesburg")})
    except: pass
    return jsonify({"latitude": -26.2041, "longitude": 28.0473, "city": "Johannesburg"})

# ====================================================
# HEALTH CHECK
# ====================================================
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "version": "3.0.0", "neural": "active"})

# ====================================================
# FRONTEND
# ====================================================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround - Complete Online Mall</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;}
        .navbar{background:#1f8a4c;color:white;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;}
        .navbar h1{font-size:1.5rem;}
        .nav-links{display:flex;gap:1rem;flex-wrap:wrap;}
        .nav-links a{color:white;text-decoration:none;padding:0.5rem 1rem;border-radius:0.5rem;cursor:pointer;}
        .nav-links a:hover{background:rgba(255,255,255,0.2);}
        .container{max-width:1200px;margin:2rem auto;padding:0 2rem;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;border-bottom:2px solid #e0e0e0;padding-bottom:0.5rem;}
        h2{color:#1f8a4c;}
        input,select,button,textarea{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #ddd;border-radius:0.5rem;font-size:1rem;}
        button{background:#1f8a4c;color:white;border:none;cursor:pointer;font-weight:600;}
        button:hover{background:#166b3a;}
        .hidden{display:none;}
        .item-row{display:flex;justify-content:space-between;padding:0.75rem 0;border-bottom:1px solid #eee;}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:1rem;}
        .stat-card{background:#e8f5e9;padding:1rem;border-radius:0.5rem;text-align:center;}
        .stat-value{font-size:1.8rem;font-weight:bold;color:#1f8a4c;}
        .tabs{display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap;}
        .tab{padding:0.5rem 1rem;background:#e0e0e0;border-radius:0.5rem;cursor:pointer;}
        .tab.active{background:#1f8a4c;color:white;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;}
        .retailer-card{background:#f8f9fa;padding:1rem;border-radius:0.5rem;text-align:center;cursor:pointer;}
        .retailer-card:hover{background:#e8f5e9;}
        @media (max-width:768px){.container{padding:0 1rem;}}
    </style>
</head>
<body>
<div class="navbar">
    <h1>🛍️ ShopAround Complete Mall</h1>
    <div class="nav-links">
        <a onclick="showSection('shopping')">Shopping</a>
        <a onclick="showSection('retailers')">Retailers</a>
        <a onclick="showSection('services')">Services</a>
        <a onclick="showSection('delivery')">Delivery</a>
        <a onclick="showSection('brain')">AI Brain</a>
        <a id="logoutBtn" style="display:none;" onclick="logout()">Logout</a>
    </div>
</div>

<div class="container">
    <div id="authSection" class="card" style="max-width:400px; margin:2rem auto; text-align:center;">
        <h2>Welcome to ShopAround</h2>
        <div id="loginForm">
            <input type="text" id="loginUsername" placeholder="Username">
            <input type="password" id="loginPassword" placeholder="Password">
            <button onclick="login()">Login</button>
            <button onclick="showRegister()" style="background:#666;">Register</button>
        </div>
        <div id="registerForm" style="display:none;">
            <input type="text" id="regUsername" placeholder="Username">
            <input type="email" id="regEmail" placeholder="Email">
            <input type="password" id="regPassword" placeholder="Password">
            <button onclick="register()">Register</button>
            <button onclick="showLogin()" style="background:#666;">Back</button>
        </div>
    </div>

    <div id="appSection" style="display:none;">
        <div class="stats">
            <div class="stat-card"><div class="stat-value">15+</div><div>Retailers</div></div>
            <div class="stat-card"><div class="stat-value" id="brainStatus">Active</div><div>Neural AI</div></div>
        </div>

        <div id="shoppingSection">
            <div class="card"><div class="card-header"><h2>📝 My Lists</h2><button onclick="createList()">+ New</button></div><div id="listsContainer"></div></div>
            <div class="card"><div class="card-header"><h2>➕ Add Items</h2></div><textarea id="bulkItems" rows="3" placeholder="Bread&#10;Milk&#10;Eggs"></textarea><select id="selectedList"></select><button onclick="addBulkItems()">Add</button></div>
            <div class="card"><div class="card-header"><h2>🔔 Price Alerts</h2><button onclick="showAddAlert()">+ New</button></div><div id="alertsList"></div></div>
        </div>

        <div id="retailersSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🏬 All Retailers</h2></div><div id="retailersGrid" class="grid"></div></div>
        </div>

        <div id="servicesSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🛠️ Service Providers</h2></div><select id="serviceType"><option value="">All</option><option value="plumbing">Plumbing</option><option value="electrical">Electrical</option><option value="mechanic">Mechanic</option></select><button onclick="loadServices()">Search</button><div id="servicesList"></div></div>
        </div>

        <div id="deliverySection" class="hidden">
            <div class="card"><div class="card-header"><h2>🚚 Delivery Services</h2></div><div id="deliveryList"></div></div>
        </div>

        <div id="brainSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🧠 Consult Neural AI</h2></div>
            <input type="text" id="brainObjective" placeholder="What decision?">
            <input type="number" id="brainAmount" placeholder="Amount (R)" value="5000">
            <input type="number" id="brainRisk" placeholder="Risk (0-1)" value="0.3" step="0.1">
            <button onclick="consultBrain()">Get AI Decision</button>
            <div id="brainResult"></div></div>
        </div>
    </div>
</div>

<script>
let currentUser = null;
let currentLists = [];

async function login(){
    const u=document.getElementById('loginUsername').value;
    const p=document.getElementById('loginPassword').value;
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    if(r.ok){
        currentUser=await r.json();
        document.getElementById('authSection').style.display='none';
        document.getElementById('appSection').style.display='block';
        document.getElementById('logoutBtn').style.display='inline-block';
        loadLists(); loadRetailers(); loadDelivery();
    }else alert('Login failed');
}

async function register(){
    const u=document.getElementById('regUsername').value;
    const e=document.getElementById('regEmail').value;
    const p=document.getElementById('regPassword').value;
    const r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,email:e,password:p})});
    if(r.ok){ showLogin(); alert('Registered!'); }
    else alert('Failed');
}

function logout(){ fetch('/api/logout',{method:'POST'}); location.reload(); }
function showRegister(){ document.getElementById('loginForm').style.display='none'; document.getElementById('registerForm').style.display='block'; }
function showLogin(){ document.getElementById('loginForm').style.display='block'; document.getElementById('registerForm').style.display='none'; }

function showSection(s){
    document.getElementById('shoppingSection').classList.add('hidden');
    document.getElementById('retailersSection').classList.add('hidden');
    document.getElementById('servicesSection').classList.add('hidden');
    document.getElementById('deliverySection').classList.add('hidden');
    document.getElementById('brainSection').classList.add('hidden');
    document.getElementById(s+'Section').classList.remove('hidden');
    if(s=='retailers') loadRetailers();
    if(s=='delivery') loadDelivery();
}

async function loadRetailers(){
    const r=await fetch('/api/retailers');
    const retailers=await r.json();
    document.getElementById('retailersGrid').innerHTML=retailers.map(r=>`<div class="retailer-card" onclick="window.open('${r.website}','_blank')"><div>${r.logo||'🏪'}</div><div><strong>${r.name}</strong></div><div>⭐ ${r.rating}</div><div><small>R${r.delivery_fee}</small></div></div>`).join('');
}

async function loadServices(){
    const type=document.getElementById('serviceType').value;
    const r=await fetch(`/api/services${type?`?type=${type}`:''}`);
    const services=await r.json();
    document.getElementById('servicesList').innerHTML=services.map(s=>`<div class="card"><strong>${s.name}</strong><br>${s.service_type} • R${s.hourly_rate}/hr<br>📞 ${s.phone}</div>`).join('');
}

async function loadDelivery(){
    const r=await fetch('/api/delivery-services');
    const services=await r.json();
    document.getElementById('deliveryList').innerHTML=services.map(s=>`<div class="card"><div class="item-row"><span>${s.logo||'🚚'} ${s.name}</span><span>⭐ ${s.rating}</span></div><div>Base: R${s.base_fee} + R${s.per_km_rate}/km</div><button onclick="window.open('${s.website}','_blank')">Go</button></div>`).join('');
}

async function loadLists(){
    const r=await fetch('/api/lists');
    if(r.ok){ currentLists=await r.json(); renderLists(); updateSelectors(); }
}

function renderLists(){
    const c=document.getElementById('listsContainer');
    if(!currentLists.length){ c.innerHTML='<div class="card"><p>No lists</p></div>'; return; }
    c.innerHTML='';
    for(const l of currentLists){
        const div=document.createElement('div'); div.className='card';
        div.innerHTML=`<div class="card-header"><h3>📋 ${l.name}</h3><button onclick="viewList(${l.id})">View</button></div><p>${l.item_count||0} items</p><div id="items-${l.id}"></div>`;
        c.appendChild(div);
        loadListItems(l.id);
    }
}

async function loadListItems(id){
    const r=await fetch(`/api/lists/${id}/items`);
    if(r.ok){
        const items=await r.json();
        const c=document.getElementById(`items-${id}`);
        if(!items.length) c.innerHTML='<p>Empty</p>';
        else{
            let html='';
            for(const i of items) html+=`<div class="item-row"><span>🛒 ${i.product_name} x${i.quantity}</span><button onclick="toggleItem(${id},${i.id})">${i.checked_off?'✓':'○'}</button></div>`;
            c.innerHTML=html;
        }
    }
}

function updateSelectors(){
    const s=document.getElementById('selectedList');
    s.innerHTML='<option value="">Select list</option>';
    for(const l of currentLists) s.innerHTML+=`<option value="${l.id}">${l.name}</option>`;
}

async function createList(){
    const n=prompt('List name:','My List');
    if(n){ await fetch('/api/lists',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n})}); await loadLists(); }
}

function viewList(id){ loadListItems(id); }

async function addBulkItems(){
    const lid=document.getElementById('selectedList').value;
    const text=document.getElementById('bulkItems').value;
    if(!lid) return alert('Select list');
    const lines=text.split('\\n').filter(l=>l.trim());
    for(const line of lines) await fetch(`/api/lists/${lid}/items`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_name:line.trim(),quantity:1})});
    document.getElementById('bulkItems').value='';
    await loadListItems(lid); await loadLists();
}

async function toggleItem(lid,iid){ await fetch(`/api/lists/${lid}/items/${iid}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({checked_off:1})}); await loadListItems(lid); }

async function showAddAlert(){
    const product=prompt('Product:');
    if(!product) return;
    const target=parseFloat(prompt('Target price:'));
    if(isNaN(target)) return;
    await fetch('/api/alerts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_name:product,target_price:target})});
    loadAlerts();
}

async function loadAlerts(){
    const r=await fetch('/api/alerts');
    if(r.ok){
        const alerts=await r.json();
        const c=document.getElementById('alertsList');
        if(!alerts.length) c.innerHTML='<p>No alerts</p>';
        else c.innerHTML=alerts.map(a=>`<div class="item-row"><span>🔔 ${a.product_name}</span><span>When ≤ R${a.target_price}</span><button onclick="deleteAlert(${a.id})">Delete</button></div>`).join('');
    }
}

async function deleteAlert(id){ await fetch(`/api/alerts/${id}`,{method:'DELETE'}); loadAlerts(); }

async function consultBrain(){
    const obj=document.getElementById('brainObjective').value;
    const amt=parseFloat(document.getElementById('brainAmount').value);
    const risk=parseFloat(document.getElementById('brainRisk').value);
    if(!obj){ alert('Enter question'); return; }
    const r=await fetch('/api/brain/think',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({objective:obj,amount:amt,risk_score:risk})});
    const data=await r.json();
    document.getElementById('brainResult').innerHTML=`<div class="card"><strong>🧠 Decision:</strong> ${data.verdict}<br>Confidence: ${(data.approval_score*100).toFixed(0)}%<br>${data.evaluations?.map(e=>`<div>${e.agent}: ${e.recommendation} (${(e.confidence*100).toFixed(0)}%)</div>`).join('')||''}</div>`;
}

// Auto demo
async function autoDemo(){
    await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'demo',password:'demo123'})});
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'demo',password:'demo123'})});
    if(r.ok) login();
}
autoDemo();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    print("="*70)
    print("🏆 SHOPAROUND - COMPLETE ONLINE MALL")
    print("="*70)
    print("✅ 15+ Retailers (Checkers, Shoprite, Woolworths, Takealot, etc)")
    print("✅ Delivery Services (Uber Eats, Mr D, Bolt Food)")
    print("✅ Service Providers (Plumbing, Electrical, Mechanic, etc)")
    print("✅ Neural AI Brain with 5 Agents")
    print("✅ Shopping Lists & Price Alerts")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=True)
