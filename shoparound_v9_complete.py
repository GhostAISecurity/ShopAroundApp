#!/usr/bin/env python3
"""
SHOPAROUND NEXUS v9.0 - Complete Layered Architecture
ADDITIVE ONLY - No existing features removed
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

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound_v9.db")

# ============================================
# LAYER 1: AUTOMATIC MIGRATIONS (Self-healing)
# ============================================

def run_migrations(db):
    """Automatic database migrations - NEVER manually alter tables again"""
    
    # Users table schema evolution
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
    
    # Get existing columns
    cursor = db.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cursor.fetchall()}
    
    for col, definition in users_columns.items():
        if col not in existing:
            try:
                db.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
                print(f"✅ Added column: {col} to users")
            except:
                pass
    
    # Households table
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
    
    # Receipt scans table
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
    
    # Geo prices table (real-time price observation network)
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
    
    # Spaza shops network
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
    
    # Vendors table (ShopAround Online Mall)
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
    
    # Price predictions table (forecasting engine)
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
# LAYER 2: AUTHENTICATION & SECURITY
# ============================================

def require_auth(f):
    """Authentication decorator for protected routes"""
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
        # Auto-run migrations on each connection
        run_migrations(g.db)
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db:
        db.close()

# ============================================
# LAYER 3: USER MANAGEMENT
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
    
    # Create session token
    token = secrets.token_urlsafe(32)
    db.execute("UPDATE users SET session_token = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?", (token, user["id"]))
    db.commit()
    
    return jsonify({
        "success": True,
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "name": user["name"]}
    })

@app.route("/api/logout", methods=["POST"])
@require_auth
def logout():
    db = get_db()
    db.execute("UPDATE users SET session_token = NULL WHERE id = ?", (request.user["id"],))
    db.commit()
    return jsonify({"success": True})

@app.route("/api/me", methods=["GET"])
@require_auth
def get_me():
    db = get_db()
    user = db.execute("SELECT id, username, email, name, household_size, monthly_budget, language, is_business FROM users WHERE id = ?", (request.user["id"],)).fetchone()
    return jsonify(dict(user))

# ============================================
# LAYER 4: HOUSEHOLD PROFILES
# ============================================

@app.route("/api/households", methods=["POST"])
@require_auth
def create_household():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO households (user_id, name, adults, children, dietary_preferences, allergies, monthly_budget)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (request.user["id"], data.get("name"), data.get("adults", 1), data.get("children", 0),
          data.get("dietary_preferences"), data.get("allergies"), data.get("monthly_budget")))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "success": True})

@app.route("/api/households", methods=["GET"])
@require_auth
def get_households():
    db = get_db()
    households = db.execute("SELECT * FROM households WHERE user_id = ?", (request.user["id"],)).fetchall()
    return jsonify([dict(h) for h in households])

# ============================================
# LAYER 5: RECEIPT OCR & INGESTION
# ============================================

@app.route("/api/receipt/scan", methods=["POST"])
@require_auth
def scan_receipt():
    """Simulate OCR receipt scanning - in production, integrate with actual OCR"""
    data = request.get_json(force=True)
    shop = data.get("shop", "Unknown")
    raw_text = data.get("raw_text", "")
    items = data.get("items", [])
    total = data.get("total", 0)
    
    db = get_db()
    cursor = db.execute("""
        INSERT INTO receipt_scans (user_id, shop, raw_text, parsed_items, total_amount, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (request.user["id"], shop, raw_text, json.dumps(items), total, data.get("confidence", 0.8)))
    db.commit()
    
    # Update price observations
    for item in items:
        db.execute("""
            INSERT INTO geo_prices (item_name, price, shop, location, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item.get("name"), item.get("price"), shop, "User Location", 0.7, "receipt"))
    
    db.commit()
    return jsonify({"scan_id": cursor.lastrowid, "items_found": len(items), "total": total})

# ============================================
# LAYER 6: COMMUNITY PRICE REPORTING
# ============================================

@app.route("/api/community/report", methods=["POST"])
@require_auth
def report_price():
    data = request.get_json(force=True)
    db = get_db()
    
    # Check for existing reports to build consensus
    existing = db.execute("""
        SELECT COUNT(*) as count, AVG(price) as avg_price
        FROM geo_prices
        WHERE item_name = ? AND shop = ? AND location = ?
        AND created_at > datetime('now', '-7 days')
    """, (data.get("item"), data.get("shop"), data.get("location"))).fetchone()
    
    # New report
    cursor = db.execute("""
        INSERT INTO geo_prices (item_name, price, shop, location, latitude, longitude, source, verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get("item"), data.get("price"), data.get("shop"), data.get("location"),
          data.get("latitude"), data.get("longitude"), "community", 0))
    
    # Auto-verify if enough reports
    if existing and existing["count"] >= 2:
        avg_price = existing["avg_price"]
        db.execute("""
            UPDATE geo_prices SET verified = 1, confidence = 0.9
            WHERE item_name = ? AND shop = ? AND location = ?
            AND created_at > datetime('now', '-7 days')
        """, (data.get("item"), data.get("shop"), data.get("location")))
    
    db.commit()
    return jsonify({
        "report_id": cursor.lastrowid,
        "consensus_reports": existing["count"] if existing else 0,
        "verified": existing and existing["count"] >= 2
    })

@app.route("/api/community/verified/<item>", methods=["GET"])
def get_verified_prices(item):
    db = get_db()
    prices = db.execute("""
        SELECT item_name, price, shop, location, confidence, created_at
        FROM geo_prices
        WHERE item_name LIKE ? AND verified = 1
        ORDER BY created_at DESC
        LIMIT 20
    """, (f"%{item}%",)).fetchall()
    return jsonify([dict(p) for p in prices])

# ============================================
# LAYER 7: SPAZA NETWORK
# ============================================

@app.route("/api/spaza/register", methods=["POST"])
@require_auth
def register_spaza():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO spaza_shops (owner_id, owner_name, shop_name, location, latitude, longitude, whatsapp_number, delivery_available)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (request.user["id"], data.get("owner_name"), data.get("shop_name"), data.get("location"),
          data.get("latitude"), data.get("longitude"), data.get("whatsapp_number"), data.get("delivery_available", 0)))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "message": "Spaza shop registered! Pending verification."})

@app.route("/api/spaza/nearby", methods=["GET"])
def get_nearby_spazas():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    db = get_db()
    
    if lat and lng:
        spazas = db.execute("""
            SELECT shop_name, location, whatsapp_number, delivery_available, verified,
                   ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) as distance_sq
            FROM spaza_shops
            WHERE verified = 1
            ORDER BY distance_sq ASC
            LIMIT 20
        """, (lat, lat, lng, lng)).fetchall()
        for s in spazas:
            s["distance_km"] = round((s["distance_sq"] ** 0.5) * 111, 1)
    else:
        spazas = db.execute("SELECT * FROM spaza_shops WHERE verified = 1 LIMIT 20").fetchall()
    
    return jsonify([dict(s) for s in spazas])

# ============================================
# LAYER 8: BASKET OPTIMIZATION ENGINE
# ============================================

@app.route("/api/optimize/basket", methods=["POST"])
def optimize_basket():
    data = request.get_json(force=True)
    budget = data.get("budget", 100)
    location = data.get("location", "Johannesburg")
    household = data.get("household", {"adults": 2, "children": 0})
    items = data.get("items", ["bread", "milk", "rice", "eggs", "chicken"])
    
    # Simple product database
    product_prices = {
        "bread": 15.99, "milk": 22.99, "rice": 45.99, "eggs": 44.99,
        "chicken": 89.99, "cabbage": 18.99, "potatoes": 45.99, "onions": 30.99,
        "tomatoes": 28.99, "apples": 32.99, "bananas": 25.99, "flour": 24.99,
        "sugar": 39.99, "oil": 54.99, "tea": 32.99, "coffee": 59.99
    }
    
    shops = ["Shoprite", "Checkers", "Pick n Pay", "Woolworths", "Spaza"]
    
    basket = []
    total = 0
    shop_totals = {}
    
    for item in items:
        price = product_prices.get(item.lower(), 35.00)
        if total + price <= budget:
            best_shop = shops[0]
            basket.append({"item": item, "price": price, "shop": best_shop})
            total += price
            shop_totals[best_shop] = shop_totals.get(best_shop, 0) + price
    
    savings = round(budget - total, 2)
    
    return jsonify({
        "basket": basket,
        "total": round(total, 2),
        "savings": savings,
        "shops": list(shop_totals.keys()),
        "household_size": household.get("adults", 1) + household.get("children", 0) * 0.5
    })

# ============================================
# LAYER 9: PRICE FORECASTING ENGINE
# ============================================

@app.route("/api/forecast/<item>", methods=["GET"])
def forecast_price(item):
    db = get_db()
    location = request.args.get("location", "Johannesburg")
    
    # Get historical prices
    history = db.execute("""
        SELECT price, created_at
        FROM geo_prices
        WHERE item_name LIKE ? AND verified = 1
        ORDER BY created_at DESC
        LIMIT 30
    """, (f"%{item}%",)).fetchall()
    
    if len(history) < 3:
        return jsonify({"item": item, "status": "insufficient_data", "message": "Need more price reports"})
    
    prices = [h["price"] for h in history]
    avg_price = sum(prices) / len(prices)
    
    # Simple trend detection
    if len(prices) >= 5:
        recent_avg = sum(prices[:5]) / 5
        older_avg = sum(prices[-5:]) / 5
        trend = "rising" if recent_avg > older_avg else "falling" if recent_avg < older_avg else "stable"
    else:
        trend = "stable"
    
    # Predict next price
    if trend == "rising":
        predicted = prices[0] * 1.05
    elif trend == "falling":
        predicted = prices[0] * 0.95
    else:
        predicted = prices[0]
    
    # Store prediction
    cursor = db.execute("""
        INSERT INTO price_predictions (item, location, predicted_price, confidence, forecast_date)
        VALUES (?, ?, ?, ?, DATE('now', '+7 days'))
    """, (item, location, round(predicted, 2), 0.75))
    db.commit()
    
    return jsonify({
        "item": item,
        "current_price": round(prices[0], 2),
        "predicted_price": round(predicted, 2),
        "trend": trend,
        "confidence": 0.75,
        "data_points": len(history)
    })

# ============================================
# LAYER 10: SHOPAROUND ONLINE MALL (Vendors)
# ============================================

@app.route("/api/mall/vendors", methods=["GET"])
def get_vendors():
    category = request.args.get("category", "")
    db = get_db()
    
    if category:
        vendors = db.execute("SELECT * FROM vendors WHERE category = ? AND verified = 1", (category,)).fetchall()
    else:
        vendors = db.execute("SELECT * FROM vendors WHERE verified = 1 LIMIT 50").fetchall()
    
    return jsonify([dict(v) for v in vendors])

@app.route("/api/mall/vendors/register", methods=["POST"])
@require_auth
def register_vendor():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO vendors (name, category, website, logo, contact_info)
        VALUES (?, ?, ?, ?, ?)
    """, (data.get("name"), data.get("category"), data.get("website"), data.get("logo"), data.get("contact_info")))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "message": "Vendor registered! Pending verification."})

# ============================================
# LAYER 11: AUTHENTICATED ALERTS
# ============================================

@app.route("/api/alerts", methods=["GET", "POST"])
@require_auth
def alerts():
    db = get_db()
    
    if request.method == "GET":
        alerts_data = db.execute("""
            SELECT * FROM price_alerts WHERE user_id = ? AND is_active = 1
        """, (request.user["id"],)).fetchall()
        return jsonify([dict(a) for a in alerts_data])
    else:
        data = request.get_json(force=True)
        db.execute("""
            INSERT INTO price_alerts (user_id, product_name, target_price)
            VALUES (?, ?, ?)
        """, (request.user["id"], data.get("product_name"), data.get("target_price")))
        db.commit()
        return jsonify({"success": True, "message": "Alert created"})

# ============================================
# LAYER 12: SHOPPING LISTS (Original preserved)
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
# LAYER 13: HEALTH & STATUS
# ============================================

@app.route("/api/health", methods=["GET"])
def health():
    db = get_db()
    stats = {
        "users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "households": db.execute("SELECT COUNT(*) FROM households").fetchone()[0],
        "spaza_shops": db.execute("SELECT COUNT(*) FROM spaza_shops").fetchone()[0],
        "price_observations": db.execute("SELECT COUNT(*) FROM geo_prices").fetchone()[0],
        "receipts": db.execute("SELECT COUNT(*) FROM receipt_scans").fetchone()[0]
    }
    return jsonify({
        "status": "healthy",
        "version": "9.0",
        "timestamp": datetime.now().isoformat(),
        "statistics": stats
    })

# ============================================
# FRONTEND - BEAUTIFUL DASHBOARD
# ============================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Nexus v9 - Complete Ecosystem</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:system-ui,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}
        .container{max-width:1200px;margin:0 auto;}
        .navbar{background:white;border-radius:1rem;padding:1rem 2rem;margin-bottom:1rem;display:flex;justify-content:space-between;align-items:center;box-shadow:0 4px 6px rgba(0,0,0,0.1);}
        .navbar h1{color:#1f8a4c;}
        .nav-links{display:flex;gap:1rem;}
        .nav-links a{color:#666;text-decoration:none;cursor:pointer;padding:0.5rem 1rem;border-radius:0.5rem;}
        .nav-links a:hover{background:#f0f0f0;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;border-bottom:2px solid #e5e7eb;padding-bottom:0.5rem;}
        h2{color:#1f8a4c;}
        input,select,button{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #ddd;border-radius:0.5rem;}
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
        .auth-container{max-width:400px;margin:2rem auto;}
        @media (max-width:768px){.grid{grid-template-columns:1fr;}}
    </style>
</head>
<body>
<div class="container">
    <!-- Auth Section -->
    <div id="authContainer" class="auth-container">
        <div class="card" id="loginCard">
            <h2>Welcome to ShopAround Nexus v9</h2>
            <p style="color:#666; margin-bottom:1rem;">Complete Economic Ecosystem</p>
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
            <button onclick="showLogin()" style="background:#666; margin-top:0.5rem;">Back to Login</button>
        </div>
    </div>

    <!-- Main App -->
    <div id="mainApp" class="hidden">
        <div class="navbar">
            <h1>🛍️ ShopAround Nexus v9</h1>
            <div class="nav-links">
                <a onclick="showSection('planner')">Planner</a>
                <a onclick="showSection('market')">Marketplace</a>
                <a onclick="showSection('community')">Community</a>
                <a onclick="showSection('spaza')">Spaza Network</a>
                <a onclick="logout()" style="color:#dc2626;">Logout</a>
            </div>
        </div>

        <div class="stats" id="statsPanel"></div>

        <!-- Planner Section -->
        <div id="plannerSection">
            <div class="card">
                <div class="card-header"><h2>🛒 Smart Shopping Planner</h2></div>
                <input type="number" id="budget" placeholder="Budget (R)" value="500">
                <input type="text" id="location" placeholder="Location" value="Johannesburg">
                <textarea id="itemsList" rows="3" placeholder="Items (one per line)&#10;bread&#10;milk&#10;rice&#10;eggs&#10;chicken"></textarea>
                <button onclick="optimizeBasket()">✨ Optimize Shopping</button>
                <div id="optimizeResult"></div>
            </div>
        </div>

        <!-- Marketplace Section -->
        <div id="marketSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🏪 ShopAround Mall</h2></div>
                <div id="mallVendors" class="grid"></div>
            </div>
        </div>

        <!-- Community Section -->
        <div id="communitySection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🤝 Community Price Reporting</h2></div>
                <input type="text" id="priceItem" placeholder="Item name">
                <input type="number" id="priceAmount" placeholder="Price (R)">
                <input type="text" id="priceShop" placeholder="Shop name">
                <button onclick="reportPrice()">Report Price</button>
                <div id="priceReportResult"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>📈 Verified Prices</h2></div>
                <input type="text" id="searchItem" placeholder="Search item">
                <button onclick="searchVerifiedPrices()">Search</button>
                <div id="verifiedPrices"></div>
            </div>
        </div>

        <!-- Spaza Section -->
        <div id="spazaSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🏪 Register Your Spaza Shop</h2></div>
                <input type="text" id="spazaName" placeholder="Shop Name">
                <input type="text" id="spazaLocation" placeholder="Location">
                <input type="text" id="spazaWhatsapp" placeholder="WhatsApp Number">
                <button onclick="registerSpaza()">Register Shop</button>
            </div>
            <div class="card">
                <div class="card-header"><h2>📍 Nearby Spaza Shops</h2></div>
                <button onclick="findNearbySpazas()">Find Nearby</button>
                <div id="nearbySpazas"></div>
            </div>
        </div>
    </div>
</div>

<script>
let authToken = null;

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    const res = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    const data = await res.json();
    
    if (data.success) {
        authToken = data.token;
        localStorage.setItem('token', authToken);
        document.getElementById('authContainer').classList.add('hidden');
        document.getElementById('mainApp').classList.remove('hidden');
        loadStats();
        loadMall();
    } else {
        alert('Login failed');
    }
}

async function register() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const name = document.getElementById('regName').value;
    
    const res = await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, email, password, name})
    });
    const data = await res.json();
    
    if (data.success) {
        alert('Registration successful! Please login.');
        showLogin();
    } else {
        alert('Registration failed');
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('token');
    document.getElementById('authContainer').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

function showRegister() {
    document.getElementById('loginCard').classList.add('hidden');
    document.getElementById('registerCard').classList.remove('hidden');
}

function showLogin() {
    document.getElementById('registerCard').classList.add('hidden');
    document.getElementById('loginCard').classList.remove('hidden');
}

function showSection(section) {
    const sections = ['planner', 'market', 'community', 'spaza'];
    sections.forEach(s => document.getElementById(s + 'Section').classList.add('hidden'));
    document.getElementById(section + 'Section').classList.remove('hidden');
}

async function loadStats() {
    const res = await fetch('/api/health');
    const data = await res.json();
    document.getElementById('statsPanel').innerHTML = `
        <div class="stat-card"><div class="stat-value">${data.statistics.users || 0}</div><div>Users</div></div>
        <div class="stat-card"><div class="stat-value">${data.statistics.spaza_shops || 0}</div><div>Spaza Shops</div></div>
        <div class="stat-card"><div class="stat-value">${data.statistics.price_observations || 0}</div><div>Price Reports</div></div>
    `;
}

async function loadMall() {
    const res = await fetch('/api/mall/vendors');
    const vendors = await res.json();
    document.getElementById('mallVendors').innerHTML = vendors.map(v => `
        <div class="card"><strong>${v.name}</strong><br>${v.category}<br>⭐ ${v.rating || 'New'}</div>
    `).join('');
}

async function optimizeBasket() {
    const budget = document.getElementById('budget').value;
    const location = document.getElementById('location').value;
    const itemsText = document.getElementById('itemsList').value;
    const items = itemsText.split('\\n').filter(i => i.trim());
    
    const res = await fetch('/api/optimize/basket', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({budget: parseFloat(budget), location, items})
    });
    const data = await res.json();
    
    let html = `<div class="stats"><div class="stat-card">Total: R${data.total}</div><div class="stat-card">Savings: R${data.savings}</div></div>`;
    data.basket.forEach(item => {
        html += `<div class="item-row"><span>${item.item}</span><span>R${item.price}</span><span>${item.shop}</span></div>`;
    });
    document.getElementById('optimizeResult').innerHTML = html;
}

async function reportPrice() {
    const item = document.getElementById('priceItem').value;
    const price = document.getElementById('priceAmount').value;
    const shop = document.getElementById('priceShop').value;
    
    if (!authToken) { alert('Please login'); return; }
    
    const res = await fetch('/api/community/report', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({item, price, shop, location: 'User Location'})
    });
    const data = await res.json();
    document.getElementById('priceReportResult').innerHTML = `<div class="badge-success" style="padding:0.5rem;">✅ Reported! ${data.consensus_reports} reports total</div>`;
}

async function searchVerifiedPrices() {
    const item = document.getElementById('searchItem').value;
    const res = await fetch(`/api/community/verified/${item}`);
    const prices = await res.json();
    document.getElementById('verifiedPrices').innerHTML = prices.map(p => `
        <div class="item-row"><span>${p.item_name}</span><span>R${p.price}</span><span>${p.shop}</span></div>
    `).join('');
}

async function registerSpaza() {
    const shop_name = document.getElementById('spazaName').value;
    const location = document.getElementById('spazaLocation').value;
    const whatsapp = document.getElementById('spazaWhatsapp').value;
    
    const res = await fetch('/api/spaza/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({shop_name, location, whatsapp_number: whatsapp})
    });
    const data = await res.json();
    alert(data.message);
}

async function findNearbySpazas() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const res = await fetch(`/api/spaza/nearby?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`);
            const spazas = await res.json();
            document.getElementById('nearbySpazas').innerHTML = spazas.map(s => `
                <div class="item-row"><span>🏪 ${s.shop_name}</span><span>${s.distance_km ? s.distance_km + 'km' : s.location}</span></div>
            `).join('');
        });
    } else {
        alert('Geolocation not supported');
    }
}

// Auto login from stored token
const token = localStorage.getItem('token');
if (token) {
    authToken = token;
    document.getElementById('authContainer').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    loadStats();
    loadMall();
}
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

# ============================================
# INITIALIZE DATABASE
# ============================================

def init_db():
    db = sqlite3.connect(DB_PATH)
    
    # Create base users table if not exists
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create shopping lists (original compatibility)
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
    
    # Price alerts table
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
    
    db.commit()
    
    # Run migrations
    run_migrations(db)
    db.close()

init_db()

if __name__ == "__main__":
    print("="*70)
    print("🏆 SHOPAROUND NEXUS v9.0 - Complete Layered Architecture")
    print("="*70)
    print("✅ Layer 1: Automatic Migrations (Self-healing)")
    print("✅ Layer 2: Authentication & Security (Bearer Tokens)")
    print("✅ Layer 3: User Management (Registration, Login)")
    print("✅ Layer 4: Household Profiles")
    print("✅ Layer 5: Receipt OCR & Ingestion")
    print("✅ Layer 6: Community Price Reporting (Consensus)")
    print("✅ Layer 7: Spaza Network (Township Economy)")
    print("✅ Layer 8: Basket Optimization Engine")
    print("✅ Layer 9: Price Forecasting Engine")
    print("✅ Layer 10: ShopAround Online Mall (Vendors)")
    print("✅ Layer 11: Authenticated Alerts")
    print("✅ Layer 12: Shopping Lists (Original Preserved)")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=False)
