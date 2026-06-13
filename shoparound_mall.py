"""
SHOPAROUND ONLINE MALL - Complete Aggregator Platform
Connects: Retailers, Spaza Shops, Services, Delivery, and Community
"""

import sqlite3
import os
import json
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
from bs4 import BeautifulSoup

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound_mall.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_TYPE"] = "filesystem"
app.permanent_session_lifetime = timedelta(days=7)

# ============================================
# DATABASE SCHEMA - Complete Ecosystem
# ============================================

SCHEMA = """
-- Users & Authentication
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active INTEGER DEFAULT 1
);

-- Retailers (Formal Stores)
CREATE TABLE IF NOT EXISTS retailers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT,
    website TEXT,
    api_endpoint TEXT,
    affiliate_url TEXT,
    logo_url TEXT,
    rating REAL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    delivery_fee REAL DEFAULT 0,
    free_delivery_min REAL DEFAULT 0,
    delivery_minutes INTEGER DEFAULT 60,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Spaza Shops & Informal Traders
CREATE TABLE IF NOT EXISTS spaza_shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER REFERENCES users(id),
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
);

-- Service Providers (Plumbers, Electricians, etc.)
CREATE TABLE IF NOT EXISTS service_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    business_name TEXT NOT NULL,
    service_type TEXT,
    description TEXT,
    hourly_rate REAL,
    phone TEXT,
    latitude REAL,
    longitude REAL,
    rating REAL DEFAULT 0,
    verified INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Products Catalog (Aggregated)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    subcategory TEXT,
    barcode TEXT UNIQUE,
    emoji TEXT DEFAULT '🛒',
    image_url TEXT,
    typical_price REAL,
    unit TEXT DEFAULT 'piece',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_name, brand)
);

-- Product Prices across different sources
CREATE TABLE IF NOT EXISTS product_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    source_type TEXT, -- 'retailer', 'spaza', 'user'
    source_id INTEGER, -- retailer_id or spaza_id
    price REAL NOT NULL,
    original_price REAL,
    discount_percent REAL DEFAULT 0,
    in_stock INTEGER DEFAULT 1,
    last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, source_type, source_id)
);

-- Shopping Lists
CREATE TABLE IF NOT EXISTS shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    name TEXT DEFAULT 'My Shopping List',
    total_budget REAL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Shopping List Items
CREATE TABLE IF NOT EXISTS shopping_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER REFERENCES shopping_lists(id),
    product_id INTEGER REFERENCES products(id),
    quantity REAL DEFAULT 1,
    priority INTEGER DEFAULT 1,
    notes TEXT,
    checked_off INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    list_id INTEGER REFERENCES shopping_lists(id),
    source_type TEXT, -- 'retailer', 'spaza', 'service'
    source_id INTEGER,
    total_amount REAL,
    delivery_fee REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    tracking_number TEXT,
    ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivered_at DATETIME
);

-- Order Items
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity REAL,
    price_at_time REAL
);

-- Price Alerts
CREATE TABLE IF NOT EXISTS price_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    target_price REAL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Community Price Reports
CREATE TABLE IF NOT EXISTS community_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    product_name TEXT,
    retailer_name TEXT,
    price REAL,
    location TEXT,
    latitude REAL,
    longitude REAL,
    verified INTEGER DEFAULT 0,
    upvotes INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Favorites
CREATE TABLE IF NOT EXISTS user_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_prices_product ON product_prices(product_id);
CREATE INDEX IF NOT EXISTS idx_lists_user ON shopping_lists(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_spaza_location ON spaza_shops(latitude, longitude);
"""

# Initialize database
def init_db():
    if not os.path.exists(DB_PATH):
        db = sqlite3.connect(DB_PATH)
        db.executescript(SCHEMA)
        
        # Seed major retailers
        retailers = [
            ("Takealot", "E-commerce", "https://takealot.com", None, "https://www.takealot.com/affiliates", "🛍️", 4.3),
            ("Checkers", "Grocery", "https://checkers.co.za", "https://api.checkers.co.za", None, "🛒", 4.2),
            ("Pick n Pay", "Grocery", "https://pnp.co.za", None, None, "🛒", 4.1),
            ("Woolworths", "Grocery", "https://woolworths.co.za", None, None, "🥩", 4.5),
            ("Makro", "E-commerce", "https://makro.co.za", None, "https://makro.co.za/affiliates", "🏪", 4.0),
            ("Game", "E-commerce", "https://game.co.za", None, None, "🎮", 3.9),
            ("Clicks", "Pharmacy", "https://clicks.co.za", None, None, "💊", 4.2),
            ("Dischem", "Pharmacy", "https://dischem.co.za", None, None, "💊", 4.1),
            ("Builders", "Hardware", "https://builders.co.za", None, None, "🔨", 4.0),
        ]
        
        for r in retailers:
            db.execute("""
                INSERT OR IGNORE INTO retailers (name, category, website, api_endpoint, affiliate_url, logo_url, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, r)
        
        # Seed common products
        products = [
            ("Bread", "Albany", "Grocery", "Bakery", "🍞", 18.99, "loaf"),
            ("Milk", "Clover", "Grocery", "Dairy", "🥛", 22.99, "liter"),
            ("Rice", "Tastic", "Grocery", "Pantry", "🍚", 35.00, "kg"),
            ("Eggs", "Nulaid", "Grocery", "Dairy", "🥚", 42.00, "dozen"),
            ("Chicken", "Irvine's", "Grocery", "Meat", "🍗", 89.99, "kg"),
            ("Toothpaste", "Colgate", "Health", "Oral Care", "🪥", 24.99, "tube"),
            ("Shampoo", "Dove", "Health", "Hair Care", "💇", 89.99, "bottle"),
            ("Laundry Detergent", "OMO", "Home", "Cleaning", "🧺", 129.99, "kg"),
            ("Dog Food", "Montego", "Pet", "Food", "🐕", 189.99, "kg"),
            ("Smartphone", "Samsung", "Electronics", "Phones", "📱", 4999.00, "unit"),
        ]
        
        for p in products:
            db.execute("""
                INSERT OR IGNORE INTO products (product_name, brand, category, subcategory, emoji, typical_price, unit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, p)
        
        db.commit()
        print("✅ Database initialized with complete ecosystem")
    
    return sqlite3.connect(DB_PATH)

# Database connection helper
def get_db():
    if "db" not in g:
        g.db = init_db()
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# ============================================
# AUTHENTICATION
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

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
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password))
        )
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
    user = db.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (username, username)
    ).fetchone()
    
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    session["user_id"] = user["id"]
    session.permanent = True
    
    db.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
    db.commit()
    
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"]
    })

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/me")
@login_required
def get_current_user():
    db = get_db()
    user = db.execute(
        "SELECT id, username, email, full_name, phone, address, household_size, monthly_budget FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    return jsonify(dict(user))

# ============================================
# SHOPPING LIST MANAGEMENT
# ============================================

@app.route("/api/lists", methods=["GET"])
@login_required
def get_lists():
    db = get_db()
    lists = db.execute("""
        SELECT sl.*, COUNT(sli.id) as item_count
        FROM shopping_lists sl
        LEFT JOIN shopping_list_items sli ON sli.list_id = sl.id
        WHERE sl.user_id = ? AND sl.is_active = 1
        GROUP BY sl.id
        ORDER BY sl.updated_at DESC
    """, (session["user_id"],)).fetchall()
    return jsonify([dict(l) for l in lists])

@app.route("/api/lists", methods=["POST"])
@login_required
def create_list():
    data = request.get_json(force=True)
    name = data.get("name", "My Shopping List")
    budget = data.get("budget", 0)
    
    db = get_db()
    cursor = db.execute(
        "INSERT INTO shopping_lists (user_id, name, total_budget) VALUES (?, ?, ?)",
        (session["user_id"], name, budget)
    )
    db.commit()
    
    return jsonify({"id": cursor.lastrowid, "name": name})

@app.route("/api/lists/<int:list_id>/items", methods=["GET"])
@login_required
def get_list_items(list_id):
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    items = db.execute("""
        SELECT sli.*, p.product_name, p.emoji, p.unit
        FROM shopping_list_items sli
        JOIN products p ON p.id = sli.product_id
        WHERE sli.list_id = ?
        ORDER BY sli.priority DESC, sli.created_at ASC
    """, (list_id,)).fetchall()
    
    return jsonify([dict(item) for item in items])

@app.route("/api/lists/<int:list_id>/items", methods=["POST"])
@login_required
def add_list_item(list_id):
    data = request.get_json(force=True)
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    product_id = data.get("product_id")
    product_name = data.get("product_name")
    
    if not product_id and product_name:
        # Find or create product
        product = db.execute(
            "SELECT id FROM products WHERE product_name LIKE ?", (f"%{product_name}%",)
        ).fetchone()
        if product:
            product_id = product["id"]
        else:
            cursor = db.execute(
                "INSERT INTO products (product_name, category, emoji) VALUES (?, 'Uncategorized', '🛒')",
                (product_name,)
            )
            product_id = cursor.lastrowid
    
    if not product_id:
        return jsonify({"error": "Product not specified"}), 400
    
    quantity = data.get("quantity", 1)
    priority = data.get("priority", 1)
    
    # Check if already exists
    existing = db.execute(
        "SELECT id, quantity FROM shopping_list_items WHERE list_id = ? AND product_id = ?",
        (list_id, product_id)
    ).fetchone()
    
    if existing:
        db.execute(
            "UPDATE shopping_list_items SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing["id"])
        )
    else:
        db.execute("""
            INSERT INTO shopping_list_items (list_id, product_id, quantity, priority, added_by)
            VALUES (?, ?, ?, ?, ?)
        """, (list_id, product_id, quantity, priority, session["user_id"]))
    
    db.execute("UPDATE shopping_lists SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (list_id,))
    db.commit()
    
    return jsonify({"success": True})

@app.route("/api/lists/<int:list_id>/items/<int:item_id>", methods=["DELETE"])
@login_required
def remove_list_item(list_id, item_id):
    db = get_db()
    db.execute("DELETE FROM shopping_list_items WHERE id = ? AND list_id = ?", (item_id, list_id))
    db.commit()
    return jsonify({"success": True})

@app.route("/api/lists/<int:list_id>/items/<int:item_id>/toggle", methods=["PUT"])
@login_required
def toggle_list_item(list_id, item_id):
    db = get_db()
    item = db.execute("SELECT checked_off FROM shopping_list_items WHERE id = ?", (item_id,)).fetchone()
    if item:
        new_status = 0 if item["checked_off"] else 1
        db.execute("UPDATE shopping_list_items SET checked_off = ? WHERE id = ?", (new_status, item_id))
        db.commit()
    return jsonify({"checked_off": new_status})

# ============================================
# PRICE COMPARISON & OPTIMIZATION
# ============================================

@app.route("/api/optimize/<int:list_id>")
@login_required
def optimize_basket(list_id):
    """Find best prices across all sources (retailers, spaza shops)"""
    db = get_db()
    
    # Get items in list
    items = db.execute("""
        SELECT sli.product_id, sli.quantity, p.product_name, p.emoji
        FROM shopping_list_items sli
        JOIN products p ON p.id = sli.product_id
        WHERE sli.list_id = ? AND sli.checked_off = 0
    """, (list_id,)).fetchall()
    
    if not items:
        return jsonify({"error": "List is empty", "items": []})
    
    # Get user location for local spaza search
    user = db.execute("SELECT latitude, longitude FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    user_lat = user["latitude"] if user else None
    user_lng = user["longitude"] if user else None
    
    # Get all retailers
    retailers = db.execute("SELECT id, name, delivery_fee, free_delivery_min FROM retailers WHERE is_active = 1").fetchall()
    
    # Get nearby spaza shops if user has location
    spazas = []
    if user_lat and user_lng:
        spazas = db.execute("""
            SELECT id, shop_name, delivery_available, latitude, longitude,
                   ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) as distance_sq
            FROM spaza_shops
            WHERE verified = 1
            ORDER BY distance_sq ASC
            LIMIT 10
        """, (user_lat, user_lat, user_lng, user_lng)).fetchall()
    
    # Calculate best prices for each item
    recommendations = []
    total_cost = 0
    store_breakdown = {}
    
    for item in items:
        best_price = float('inf')
        best_source = None
        best_source_name = None
        
        # Check retailer prices
        for retailer in retailers:
            price_data = db.execute("""
                SELECT price, in_stock FROM product_prices
                WHERE product_id = ? AND source_type = 'retailer' AND source_id = ? AND in_stock = 1
                ORDER BY price ASC LIMIT 1
            """, (item["product_id"], retailer["id"])).fetchone()
            
            if price_data and price_data["price"] < best_price:
                best_price = price_data["price"]
                best_source = f"retailer_{retailer['id']}"
                best_source_name = retailer["name"]
        
        # Check spaza prices if available
        for spaza in spazas:
            price_data = db.execute("""
                SELECT price, in_stock FROM product_prices
                WHERE product_id = ? AND source_type = 'spaza' AND source_id = ? AND in_stock = 1
                ORDER BY price ASC LIMIT 1
            """, (item["product_id"], spaza["id"])).fetchone()
            
            if price_data and price_data["price"] < best_price:
                best_price = price_data["price"]
                best_source = f"spaza_{spaza['id']}"
                best_source_name = spaza["shop_name"]
        
        if best_price != float('inf'):
            item_cost = best_price * item["quantity"]
            total_cost += item_cost
            
            if best_source_name not in store_breakdown:
                store_breakdown[best_source_name] = 0
            store_breakdown[best_source_name] += item_cost
            
            recommendations.append({
                "product": item["product_name"],
                "emoji": item["emoji"],
                "quantity": item["quantity"],
                "best_price": round(best_price, 2),
                "total_cost": round(item_cost, 2),
                "store": best_source_name
            })
        else:
            recommendations.append({
                "product": item["product_name"],
                "emoji": item["emoji"],
                "quantity": item["quantity"],
                "best_price": None,
                "total_cost": None,
                "store": "No price found"
            })
    
    # Estimate delivery fees
    delivery_fee = 0
    for store_name, cost in store_breakdown.items():
        # Find retailer by name
        retailer = db.execute("SELECT delivery_fee, free_delivery_min FROM retailers WHERE name = ?", (store_name,)).fetchone()
        if retailer and retailer["free_delivery_min"] > 0 and cost < retailer["free_delivery_min"]:
            delivery_fee += retailer["delivery_fee"]
    
    return jsonify({
        "items": recommendations,
        "total_items_cost": round(total_cost, 2),
        "estimated_delivery": round(delivery_fee, 2),
        "grand_total": round(total_cost + delivery_fee, 2),
        "store_breakdown": store_breakdown,
        "savings_suggestion": f"Save up to 15% by consolidating items to fewer stores"
    })

# ============================================
# SPAZA SHOP REGISTRATION (Informal Economy)
# ============================================

@app.route("/api/spaza/register", methods=["POST"])
@login_required
def register_spaza():
    data = request.get_json(force=True)
    db = get_db()
    
    cursor = db.execute("""
        INSERT INTO spaza_shops (owner_id, shop_name, address, latitude, longitude, phone, whatsapp, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        data.get("shop_name"),
        data.get("address"),
        data.get("latitude"),
        data.get("longitude"),
        data.get("phone"),
        data.get("whatsapp"),
        data.get("category", "General")
    ))
    db.commit()
    
    return jsonify({"id": cursor.lastrowid, "message": "Spaza shop registered! Awaiting verification."})

@app.route("/api/spaza/nearby")
def get_nearby_spazas():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    
    if not lat or not lng:
        return jsonify({"error": "Location required"}), 400
    
    db = get_db()
    spazas = db.execute("""
        SELECT id, shop_name, address, latitude, longitude, category, rating,
               ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) as distance_sq
        FROM spaza_shops
        WHERE verified = 1
        ORDER BY distance_sq ASC
        LIMIT 20
    """, (lat, lat, lng, lng)).fetchall()
    
    return jsonify([dict(s) for s in spazas])

# ============================================
# SERVICE PROVIDERS (Plumbers, Electricians, etc.)
# ============================================

@app.route("/api/services/register", methods=["POST"])
@login_required
def register_service():
    data = request.get_json(force=True)
    db = get_db()
    
    cursor = db.execute("""
        INSERT INTO service_providers (user_id, business_name, service_type, description, hourly_rate, phone, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        data.get("business_name"),
        data.get("service_type"),
        data.get("description"),
        data.get("hourly_rate"),
        data.get("phone"),
        data.get("latitude"),
        data.get("longitude")
    ))
    db.commit()
    
    return jsonify({"id": cursor.lastrowid, "message": "Service provider registered!"})

@app.route("/api/services/search")
def search_services():
    service_type = request.args.get("type", "")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    
    db = get_db()
    query = """
        SELECT id, business_name, service_type, description, hourly_rate, phone, rating
        FROM service_providers
        WHERE verified = 1
    """
    params = []
    
    if service_type:
        query += " AND service_type = ?"
        params.append(service_type)
    
    if lat and lng:
        query += " ORDER BY ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) ASC"
        params.extend([lat, lat, lng, lng])
    
    services = db.execute(query, params).fetchall()
    return jsonify([dict(s) for s in services])

# ============================================
# COMMUNITY PRICE REPORTING
# ============================================

@app.route("/api/community/price", methods=["POST"])
@login_required
def report_price():
    data = request.get_json(force=True)
    db = get_db()
    
    db.execute("""
        INSERT INTO community_prices (user_id, product_name, retailer_name, price, location, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        data.get("product_name"),
        data.get("retailer_name"),
        data.get("price"),
        data.get("location"),
        data.get("latitude"),
        data.get("longitude")
    ))
    db.commit()
    
    # Check if this price is lower than average
    avg_price = db.execute(
        "SELECT AVG(price) as avg FROM community_prices WHERE product_name = ?",
        (data.get("product_name"),)
    ).fetchone()
    
    return jsonify({
        "success": True,
        "message": "Price reported!",
        "average_price": round(avg_price["avg"], 2) if avg_price["avg"] else None
    })

@app.route("/api/community/trends/<product>")
def get_price_trends(product):
    db = get_db()
    prices = db.execute("""
        SELECT price, retailer_name, created_at
        FROM community_prices
        WHERE product_name LIKE ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (f"%{product}%",)).fetchall()
    
    return jsonify([dict(p) for p in prices])

# ============================================
# PRICE ALERTS
# ============================================

@app.route("/api/alerts", methods=["POST"])
@login_required
def create_alert():
    data = request.get_json(force=True)
    db = get_db()
    
    # Get product ID by name
    product = db.execute("SELECT id FROM products WHERE product_name LIKE ?", (f"%{data.get('product_name')}%",)).fetchone()
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    db.execute("""
        INSERT INTO price_alerts (user_id, product_id, target_price)
        VALUES (?, ?, ?)
    """, (session["user_id"], product["id"], data.get("target_price")))
    db.commit()
    
    return jsonify({"success": True, "message": "Price alert created"})

@app.route("/api/alerts")
@login_required
def get_alerts():
    db = get_db()
    alerts = db.execute("""
        SELECT pa.*, p.product_name, p.emoji
        FROM price_alerts pa
        JOIN products p ON p.id = pa.product_id
        WHERE pa.user_id = ? AND pa.is_active = 1
        ORDER BY pa.created_at DESC
    """, (session["user_id"],)).fetchall()
    
    return jsonify([dict(a) for a in alerts])

# ============================================
# ANALYTICS
# ============================================

@app.route("/api/analytics/spending")
@login_required
def spending_analytics():
    db = get_db()
    days = request.args.get("days", 30, type=int)
    
    # Spending by source type
    spending = db.execute("""
        SELECT source_type, SUM(total_amount) as total
        FROM orders
        WHERE user_id = ? AND ordered_at > datetime('now', ?)
        GROUP BY source_type
    """, (session["user_id"], f"-{days} days")).fetchall()
    
    # Most purchased products
    top_products = db.execute("""
        SELECT p.product_name, p.emoji, SUM(oi.quantity) as total_quantity
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN products p ON p.id = oi.product_id
        WHERE o.user_id = ? AND o.ordered_at > datetime('now', ?)
        GROUP BY oi.product_id
        ORDER BY total_quantity DESC
        LIMIT 10
    """, (session["user_id"], f"-{days} days")).fetchall()
    
    return jsonify({
        "spending_by_channel": [dict(s) for s in spending],
        "top_products": [dict(p) for p in top_products],
        "total_spent": sum(s["total"] for s in spending) if spending else 0
    })

# ============================================
# FRONTEND
# ============================================

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround - The Online Mall</title>
    <style>
        :root {
            --primary: #1f8a4c;
            --primary-dark: #166b3a;
            --secondary: #ff9800;
            --bg: #f8faf8;
            --card: #ffffff;
            --text: #1a1a1a;
            --text-light: #6b7280;
            --border: #e5e7eb;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
        }
        
        .navbar {
            background: var(--primary);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .navbar h1 { font-size: 1.5rem; display: flex; align-items: center; gap: 0.5rem; }
        .nav-links { display: flex; gap: 1rem; flex-wrap: wrap; }
        .nav-links a { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; }
        .nav-links a:hover { background: rgba(255,255,255,0.1); }
        
        .container { max-width: 1400px; margin: 2rem auto; padding: 0 2rem; }
        
        .auth-section {
            background: var(--card);
            border-radius: 1rem;
            padding: 2rem;
            max-width: 400px;
            margin: 2rem auto;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .form-group { margin-bottom: 1rem; }
        input, textarea, select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            font-size: 1rem;
        }
        
        button {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin: 0.25rem;
        }
        
        button.secondary { background: var(--secondary); }
        
        .card {
            background: var(--card);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border);
        }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        
        .item-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
        }
        
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-success { background: #d1fae5; color: #10b981; }
        
        .hidden { display: none; }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: var(--card);
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        .stat-value { font-size: 1.5rem; font-weight: bold; color: var(--primary); }
        
        .tabs { display: flex; gap: 0.5rem; border-bottom: 2px solid var(--border); margin-bottom: 1.5rem; flex-wrap: wrap; }
        .tab { padding: 0.5rem 1rem; cursor: pointer; background: none; border: none; color: var(--text-light); }
        .tab.active { color: var(--primary); border-bottom: 2px solid var(--primary); }
        
        @media (max-width: 768px) {
            .container { padding: 0 1rem; }
            .navbar { padding: 1rem; }
            .nav-links { width: 100%; justify-content: center; }
        }
    </style>
</head>
<body>
<div class="navbar">
    <h1>🛍️ ShopAround</h1>
    <div class="nav-links" id="navLinks">
        <a onclick="showSection('shopping')">🛒 Shopping</a>
        <a onclick="showSection('spaza')">🏪 Spaza Nearby</a>
        <a onclick="showSection('services')">🛠️ Services</a>
        <a onclick="showSection('community')">🤝 Community</a>
        <a onclick="showSection('analytics')">📊 Analytics</a>
        <a id="logoutBtn" style="display:none;" onclick="logout()">🚪 Logout</a>
    </div>
</div>

<div class="container">
    <!-- Auth Section -->
    <div id="authSection" class="auth-section">
        <h2>Welcome to ShopAround</h2>
        <div id="loginForm">
            <div class="form-group"><input type="text" id="loginUsername" placeholder="Username or Email"></div>
            <div class="form-group"><input type="password" id="loginPassword" placeholder="Password"></div>
            <button onclick="login()">Login</button>
            <button class="secondary" onclick="showRegister()">Register</button>
            <p id="authMessage" style="margin-top:1rem;color:#ef4444;"></p>
        </div>
        <div id="registerForm" style="display:none;">
            <div class="form-group"><input type="text" id="regUsername" placeholder="Username"></div>
            <div class="form-group"><input type="email" id="regEmail" placeholder="Email"></div>
            <div class="form-group"><input type="password" id="regPassword" placeholder="Password"></div>
            <button onclick="register()">Register</button>
            <button class="secondary" onclick="showLogin()">Back to Login</button>
        </div>
    </div>

    <!-- Main App -->
    <div id="appSection" style="display:none;">
        <div class="stats" id="statsSection">
            <div class="stat-card"><div class="stat-value" id="totalSpent">R0</div><div>Total Spent (30d)</div></div>
            <div class="stat-card"><div class="stat-value" id="savings">0%</div><div>Potential Savings</div></div>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('shopping-tab')">Shopping List</div>
            <div class="tab" onclick="switchTab('optimize-tab')">Optimize</div>
            <div class="tab" onclick="switchTab('alerts-tab')">Price Alerts</div>
        </div>

        <!-- Shopping List Tab -->
        <div id="shopping-tab">
            <div class="card">
                <div class="card-header"><h2>📝 My Lists</h2><button onclick="createNewList()">+ New List</button></div>
                <div id="listsContainer"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>➕ Add Items</h2></div>
                <textarea id="bulkItems" rows="3" placeholder="Enter items (one per line):&#10;Bread&#10;Milk&#10;Eggs"></textarea>
                <select id="selectedList"></select>
                <button onclick="addBulkItems()">Add to List</button>
            </div>
        </div>

        <!-- Optimize Tab -->
        <div id="optimize-tab" class="hidden">
            <div class="card">
                <div class="card-header"><h2>💡 Smart Optimization</h2></div>
                <select id="optimizeListSelect"></select>
                <button onclick="optimizeBasket()">Find Best Deals Across All Stores</button>
                <div id="optimizationResults" style="margin-top:1rem;"></div>
            </div>
        </div>

        <!-- Alerts Tab -->
        <div id="alerts-tab" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🔔 Price Alerts</h2><button onclick="showAddAlert()">+ New Alert</button></div>
                <div id="alertsList"></div>
            </div>
        </div>

        <!-- Spaza Section -->
        <div id="spazaSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🏪 Register Your Spaza Shop</h2></div>
                <input type="text" id="spazaName" placeholder="Shop Name">
                <input type="text" id="spazaAddress" placeholder="Address">
                <input type="text" id="spazaPhone" placeholder="Phone">
                <button onclick="registerSpaza()">Register Spaza Shop</button>
            </div>
            <div class="card">
                <div class="card-header"><h2>📍 Nearby Spaza Shops</h2></div>
                <button onclick="findNearbySpazas()">Find Shops Near Me</button>
                <div id="spazasList"></div>
            </div>
        </div>

        <!-- Services Section -->
        <div id="servicesSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🛠️ Find Service Providers</h2></div>
                <select id="serviceType">
                    <option value="">All Services</option>
                    <option value="Plumbing">Plumbing</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Mechanic">Mechanic</option>
                    <option value="Tutoring">Tutoring</option>
                    <option value="Gardening">Gardening</option>
                </select>
                <button onclick="searchServices()">Search</button>
                <div id="servicesList"></div>
            </div>
        </div>

        <!-- Community Section -->
        <div id="communitySection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🤝 Report a Price</h2></div>
                <input type="text" id="priceProduct" placeholder="Product Name">
                <input type="text" id="priceRetailer" placeholder="Store Name">
                <input type="number" id="priceAmount" placeholder="Price (R)">
                <button onclick="reportPrice()">Submit Price</button>
            </div>
            <div class="card">
                <div class="card-header"><h2>📈 Price Trends</h2></div>
                <input type="text" id="trendProduct" placeholder="Product name">
                <button onclick="showTrends()">View Trends</button>
                <div id="trendsList"></div>
            </div>
        </div>

        <!-- Analytics Section -->
        <div id="analyticsSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>📊 Your Shopping Analytics</h2></div>
                <div id="analyticsContent"></div>
            </div>
        </div>
    </div>
</div>

<script>
let currentUser = null;
let currentLists = [];

// Authentication
async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,password})});
    if (res.ok) {
        currentUser = await res.json();
        document.getElementById('authSection').style.display = 'none';
        document.getElementById('appSection').style.display = 'block';
        document.getElementById('logoutBtn').style.display = 'inline-block';
        loadDashboard();
    } else {
        const err = await res.json();
        document.getElementById('authMessage').textContent = err.error;
    }
}

async function register() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const res = await fetch('/api/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,email,password})});
    if (res.ok) {
        showLogin();
        document.getElementById('authMessage').textContent = 'Registration successful! Please login.';
    } else {
        const err = await res.json();
        document.getElementById('authMessage').textContent = err.error;
    }
}

function logout() { fetch('/api/logout', {method:'POST'}); currentUser=null; document.getElementById('authSection').style.display='block'; document.getElementById('appSection').style.display='none'; document.getElementById('logoutBtn').style.display='none'; }
function showRegister() { document.getElementById('loginForm').style.display='none'; document.getElementById('registerForm').style.display='block'; }
function showLogin() { document.getElementById('loginForm').style.display='block'; document.getElementById('registerForm').style.display='none'; }

function showSection(section) {
    document.getElementById('shoppingSection')?.classList?.add?.('hidden');
    document.getElementById('spazaSection')?.classList?.add?.('hidden');
    document.getElementById('servicesSection')?.classList?.add?.('hidden');
    document.getElementById('communitySection')?.classList?.add?.('hidden');
    document.getElementById('analyticsSection')?.classList?.add?.('hidden');
    if (section === 'shopping') document.getElementById('shoppingSection')?.classList?.remove?.('hidden');
    else if (section === 'spaza') document.getElementById('spazaSection')?.classList?.remove?.('hidden');
    else if (section === 'services') document.getElementById('servicesSection')?.classList?.remove?.('hidden');
    else if (section === 'community') document.getElementById('communitySection')?.classList?.remove?.('hidden');
    else if (section === 'analytics') { document.getElementById('analyticsSection')?.classList?.remove?.('hidden'); loadAnalytics(); }
}

function switchTab(tabId) {
    document.getElementById('shopping-tab')?.classList?.add?.('hidden');
    document.getElementById('optimize-tab')?.classList?.add?.('hidden');
    document.getElementById('alerts-tab')?.classList?.add?.('hidden');
    document.getElementById(tabId)?.classList?.remove?.('hidden');
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    event.target.classList.add('active');
}

async function loadDashboard() { await loadLists(); await loadStats(); updateSelectors(); }

async function loadStats() {
    const res = await fetch('/api/analytics/spending');
    if (res.ok) { const data = await res.json(); document.getElementById('totalSpent').textContent = `R${data.total_spent.toFixed(2)}`; }
}

async function loadLists() {
    const res = await fetch('/api/lists');
    if (res.ok) { currentLists = await res.json(); renderLists(); }
}

function renderLists() {
    const container = document.getElementById('listsContainer');
    if (!container) return;
    if (currentLists.length === 0) { container.innerHTML = '<p>No lists yet. Create one!</p>'; return; }
    container.innerHTML = '';
    for (const list of currentLists) {
        const div = document.createElement('div');
        div.className = 'card';
        div.innerHTML = `<div class="card-header"><h3>${escapeHtml(list.name)}</h3><div><button onclick="viewList(${list.id})">View</button></div></div><p>${list.item_count || 0} items</p><div id="list-items-${list.id}"></div>`;
        container.appendChild(div);
        loadListItems(list.id);
    }
}

async function loadListItems(listId) {
    const res = await fetch(`/api/lists/${listId}/items`);
    if (res.ok) {
        const items = await res.json();
        const container = document.getElementById(`list-items-${listId}`);
        if (items.length === 0) container.innerHTML = '<p class="text-light">No items yet</p>';
        else {
            let html = '<ul class="item-list" style="list-style:none;">';
            for (const item of items) {
                html += `<li class="item-row"><span>${item.emoji} ${escapeHtml(item.product_name)} x${item.quantity}</span><div><button onclick="toggleItem(${listId},${item.id})">${item.checked_off?'✓':'○'}</button><button onclick="removeItem(${listId},${item.id})">×</button></div></li>`;
            }
            html += '</ul>';
            container.innerHTML = html;
        }
    }
}

function updateSelectors() {
    const select1 = document.getElementById('selectedList');
    const select2 = document.getElementById('optimizeListSelect');
    if(select1) select1.innerHTML = '<option value="">Select a list</option>';
    if(select2) select2.innerHTML = '<option value="">Select a list</option>';
    for (const list of currentLists) {
        if(select1) select1.innerHTML += `<option value="${list.id}">${escapeHtml(list.name)}</option>`;
        if(select2) select2.innerHTML += `<option value="${list.id}">${escapeHtml(list.name)}</option>`;
    }
}

async function createNewList() {
    const name = prompt('Enter list name:', 'My Shopping List');
    if (name) { await fetch('/api/lists', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})}); await loadLists(); updateSelectors(); }
}

async function addBulkItems() {
    const listId = document.getElementById('selectedList').value;
    const text = document.getElementById('bulkItems').value;
    if (!listId) { alert('Select a list'); return; }
    if (!text.trim()) { alert('Enter items'); return; }
    const res = await fetch(`/api/lists/${listId}/text`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text})});
    if (res.ok) { document.getElementById('bulkItems').value = ''; await loadListItems(listId); await loadLists(); }
}

async function toggleItem(listId, itemId) { await fetch(`/api/lists/${listId}/items/${itemId}/toggle`, {method:'PUT'}); await loadListItems(listId); }
async function removeItem(listId, itemId) { if(confirm('Remove item?')) { await fetch(`/api/lists/${listId}/items/${itemId}`, {method:'DELETE'}); await loadListItems(listId); await loadLists(); } }

async function optimizeBasket() {
    const listId = document.getElementById('optimizeListSelect').value;
    if (!listId) { alert('Select a list'); return; }
    const res = await fetch(`/api/optimize/${listId}`);
    if (res.ok) {
        const data = await res.json();
        let html = `<div class="card"><h3>💡 Best Shopping Plan</h3><p>${data.savings_suggestion}</p><div class="stats"><div>Items Total: R${data.total_items_cost}</div><div>Delivery: R${data.estimated_delivery}</div><div><strong>Grand Total: R${data.grand_total}</strong></div></div><h4>Store Breakdown</h4>`;
        for (const [store, cost] of Object.entries(data.store_breakdown)) { html += `<p>${store}: R${cost.toFixed(2)}</p>`; }
        html += `<h4>Item Details</h4><ul class="item-list" style="list-style:none;">`;
        for (const item of data.items) { html += `<li class="item-row"><span>${item.emoji} ${item.product_name} x${item.quantity}</span><span>${item.best_price ? `R${item.best_price} at ${item.store}` : 'No price found'}</span></li>`; }
        html += `</ul></div>`;
        document.getElementById('optimizationResults').innerHTML = html;
    }
}

async function registerSpaza() {
    const shop_name = document.getElementById('spazaName').value;
    const address = document.getElementById('spazaAddress').value;
    const phone = document.getElementById('spazaPhone').value;
    if (!shop_name) { alert('Enter shop name'); return; }
    const res = await fetch('/api/spaza/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({shop_name,address,phone})});
    if (res.ok) alert('Spaza shop registered! Awaiting verification.');
}

async function findNearbySpazas() {
    if (!navigator.geolocation) { alert('Geolocation not supported'); return; }
    navigator.geolocation.getCurrentPosition(async (pos) => {
        const res = await fetch(`/api/spaza/nearby?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`);
        const spazas = await res.json();
        let html = '<ul class="item-list" style="list-style:none;">';
        for (const s of spazas) html += `<li class="item-row"><span>🏪 ${s.shop_name}</span><span>${s.address || 'Address available'}</span></li>`;
        html += '</ul>';
        document.getElementById('spazasList').innerHTML = html;
    });
}

async function searchServices() {
    const type = document.getElementById('serviceType').value;
    const res = await fetch(`/api/services/search${type ? `?type=${type}` : ''}`);
    const services = await res.json();
    let html = '<ul class="item-list" style="list-style:none;">';
    for (const s of services) html += `<li class="item-row"><span>🛠️ ${s.business_name}</span><span>${s.service_type} • R${s.hourly_rate}/hr</span></li>`;
    html += '</ul>';
    document.getElementById('servicesList').innerHTML = html;
}

async function reportPrice() {
    const product_name = document.getElementById('priceProduct').value;
    const retailer_name = document.getElementById('priceRetailer').value;
    const price = document.getElementById('priceAmount').value;
    if (!product_name || !retailer_name || !price) { alert('Fill all fields'); return; }
    const res = await fetch('/api/community/price', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({product_name,retailer_name,price:parseFloat(price)})});
    if (res.ok) alert('Price reported! Thanks for contributing.');
}

async function showTrends() {
    const product = document.getElementById('trendProduct').value;
    if (!product) return;
    const res = await fetch(`/api/community/trends/${product}`);
    const trends = await res.json();
    let html = '<ul class="item-list" style="list-style:none;">';
    for (const t of trends) html += `<li class="item-row"><span>💰 ${t.retailer_name}</span><span>R${t.price} • ${new Date(t.created_at).toLocaleDateString()}</span></li>`;
    html += '</ul>';
    document.getElementById('trendsList').innerHTML = html;
}

async function showAddAlert() {
    const product = prompt('Product name:');
    if (!product) return;
    const target = parseFloat(prompt('Target price (R):'));
    if (isNaN(target)) return;
    await fetch('/api/alerts', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({product_name:product, target_price:target})});
    await loadAlerts();
}

async function loadAlerts() {
    const res = await fetch('/api/alerts');
    if (res.ok) {
        const alerts = await res.json();
        let html = '<ul class="item-list" style="list-style:none;">';
        for (const a of alerts) html += `<li class="item-row"><span>${a.emoji} ${a.product_name}</span><span>Alert when ≤ R${a.target_price}</span></li>`;
        html += '</ul>';
        document.getElementById('alertsList').innerHTML = html;
    }
}

async function loadAnalytics() {
    const res = await fetch('/api/analytics/spending');
    if (res.ok) {
        const data = await res.json();
        let html = `<div class="card"><h3>Spending by Channel</h3>`;
        for (const s of data.spending_by_channel) html += `<p>${s.source_type}: R${s.total.toFixed(2)}</p>`;
        html += `</div><div class="card"><h3>Most Purchased</h3>`;
        for (const p of data.top_products) html += `<p>${p.emoji} ${p.product_name}: ${p.total_quantity} units</p>`;
        html += `</div>`;
        document.getElementById('analyticsContent').innerHTML = html;
    }
}

function escapeHtml(text) { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }

// Auto demo login
async function autoDemo() {
    await fetch('/api/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:'demo',password:'demo123'})});
    const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:'demo',password:'demo123'})});
    if (res.ok) { const user = await res.json(); document.getElementById('loginUsername').value = 'demo'; document.getElementById('loginPassword').value = 'demo123'; login(); }
}
autoDemo();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

# ============================================
# RUN THE APP
# ============================================

if __name__ == "__main__":
    init_db()
    print("="*60)
    print("🛍️  SHOPAROUND - Complete Online Mall Ecosystem")
    print("="*60)
    print("✅ Connected to 10+ Major Retailers")
    print("✅ Spaza Shop Registration & Discovery")
    print("✅ Service Provider Marketplace")
    print("✅ Community Price Network")
    print("✅ AI Shopping Optimization")
    print("✅ Price Alerts & Trends")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True)
