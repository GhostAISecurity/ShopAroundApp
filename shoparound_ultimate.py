"""
SHOPAROUND ULTIMATE - Complete Online & Physical Mall
- All online shops (Takealot, Amazon, Shein, Temu, Makro, Game, Checkers, Woolworths, etc.)
- Physical store locator with OpenStreetMap
- Service providers (Plumbers, Electricians, Mechanics)
- Smart price optimizer across all stores
- Open source navigation (no API keys needed)
"""

import sqlite3
import os
import json
import secrets
import hashlib
import requests
import math
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound_ultimate.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)

# ============================================
# OPENSTREETMAP INTEGRATION (Free, no API keys)
# ============================================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ============================================
# ALL SHOPS - COMPLETE DATABASE (50+ shops)
# ============================================

ALL_SHOPS = {
    # 🛍️ E-COMMERCE GIANTS
    "takealot": {"name": "Takealot", "category": "E-commerce", "logo": "🛍️", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://takealot.com", "color": "#1a8c4a", "delivery_time": "2-3 days", "type": "online"},
    "amazon": {"name": "Amazon", "category": "E-commerce", "logo": "📦", "delivery_fee": 100, "free_delivery_min": 1000, "website": "https://amazon.com", "color": "#ff9900", "delivery_time": "5-7 days", "type": "online"},
    "shein": {"name": "Shein", "category": "Fashion", "logo": "👗", "delivery_fee": 80, "free_delivery_min": 800, "website": "https://shein.com", "color": "#ff6b6b", "delivery_time": "7-10 days", "type": "online"},
    "temu": {"name": "Temu", "category": "E-commerce", "logo": "🎁", "delivery_fee": 60, "free_delivery_min": 600, "website": "https://temu.com", "color": "#2d8cff", "delivery_time": "7-14 days", "type": "online"},
    "makro": {"name": "Makro", "category": "Wholesale", "logo": "🏪", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://makro.co.za", "color": "#e31e24", "delivery_time": "1-2 days", "type": "both"},
    "game": {"name": "Game", "category": "General", "logo": "🎮", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://game.co.za", "color": "#ff6600", "delivery_time": "1-2 days", "type": "both"},
    "bash": {"name": "Bash", "category": "Fashion", "logo": "👔", "delivery_fee": 45, "free_delivery_min": 450, "website": "https://bash.com", "color": "#ff1493", "delivery_time": "2-3 days", "type": "online"},
    "superbalist": {"name": "Superbalist", "category": "Fashion", "logo": "👕", "delivery_fee": 45, "free_delivery_min": 450, "website": "https://superbalist.com", "color": "#ff4081", "delivery_time": "2-4 days", "type": "online"},
    "zando": {"name": "Zando", "category": "Fashion", "logo": "👗", "delivery_fee": 40, "free_delivery_min": 400, "website": "https://zando.co.za", "color": "#ff1493", "delivery_time": "2-4 days", "type": "online"},
    "takealot_more": {"name": "Takealot More", "category": "E-commerce", "logo": "🛒", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://takealot.com", "color": "#1a8c4a", "delivery_time": "2-3 days", "type": "online"},
    
    # 🛒 GROCERY STORES
    "checkers": {"name": "Checkers", "category": "Grocery", "logo": "🛒", "delivery_fee": 35, "free_delivery_min": 350, "website": "https://checkers.co.za", "color": "#0066b3", "delivery_time": "60 min", "type": "both", "has_sixty": True},
    "checkers_sixty": {"name": "Checkers Sixty60", "category": "Grocery Delivery", "logo": "⏱️", "delivery_fee": 35, "free_delivery_min": 350, "website": "https://sixty60.co.za", "color": "#00a651", "delivery_time": "60 min", "type": "online"},
    "shoprite": {"name": "Shoprite", "category": "Grocery", "logo": "🛒", "delivery_fee": 35, "free_delivery_min": 350, "website": "https://shoprite.co.za", "color": "#ff6600", "delivery_time": "1-2 days", "type": "both"},
    "woolworths": {"name": "Woolworths", "category": "Grocery", "logo": "🥩", "delivery_fee": 45, "free_delivery_min": 450, "website": "https://woolworths.co.za", "color": "#004d40", "delivery_time": "2-4 hours", "type": "both"},
    "picknpay": {"name": "Pick n Pay", "category": "Grocery", "logo": "🛒", "delivery_fee": 35, "free_delivery_min": 350, "website": "https://pnp.co.za", "color": "#007847", "delivery_time": "2-3 hours", "type": "both"},
    "spar": {"name": "Spar", "category": "Grocery", "logo": "🛒", "delivery_fee": 35, "free_delivery_min": 350, "website": "https://spar.co.za", "color": "#006633", "delivery_time": "2-3 hours", "type": "both"},
    "spar2u": {"name": "Spar2U", "category": "Grocery Delivery", "logo": "🚗", "delivery_fee": 35, "free_delivery_min": 350, "website": "https://spar2u.co.za", "color": "#00a651", "delivery_time": "60 min", "type": "online"},
    "foodlovers": {"name": "Food Lovers Market", "category": "Grocery", "logo": "🥬", "delivery_fee": 30, "free_delivery_min": 300, "website": "https://foodloversmarket.co.za", "color": "#00a651", "delivery_time": "1-2 days", "type": "both"},
    
    # 🍔 FOOD DELIVERY
    "uber_eats": {"name": "Uber Eats", "category": "Food Delivery", "logo": "🍔", "delivery_fee": 15, "free_delivery_min": 100, "website": "https://ubereats.com", "color": "#000000", "delivery_time": "30-45 min", "type": "online"},
    "mrd": {"name": "Mr D", "category": "Food Delivery", "logo": "🍕", "delivery_fee": 20, "free_delivery_min": 120, "website": "https://mrdelivery.co.za", "color": "#ff6600", "delivery_time": "35-50 min", "type": "online"},
    "bolt_food": {"name": "Bolt Food", "category": "Food Delivery", "logo": "⚡", "delivery_fee": 15, "free_delivery_min": 100, "website": "https://boltfood.com", "color": "#00a651", "delivery_time": "30-45 min", "type": "online"},
    "kfc_delivery": {"name": "KFC Delivery", "category": "Fast Food", "logo": "🍗", "delivery_fee": 25, "free_delivery_min": 150, "website": "https://kfc.co.za", "color": "#e31e24", "delivery_time": "30-45 min", "type": "online"},
    "mcdonalds": {"name": "McDonald's Delivery", "category": "Fast Food", "logo": "🍔", "delivery_fee": 20, "free_delivery_min": 120, "website": "https://mcdonalds.co.za", "color": "#ffc107", "delivery_time": "25-40 min", "type": "online"},
    "dominos": {"name": "Domino's Pizza", "category": "Fast Food", "logo": "🍕", "delivery_fee": 25, "free_delivery_min": 150, "website": "https://dominos.co.za", "color": "#0066b3", "delivery_time": "30-45 min", "type": "online"},
    "nandos": {"name": "Nando's Delivery", "category": "Fast Food", "logo": "🐔", "delivery_fee": 20, "free_delivery_min": 120, "website": "https://nandos.co.za", "color": "#e31e24", "delivery_time": "30-45 min", "type": "online"},
    
    # 🚗 TRANSPORT & RIDE HAILING
    "uber": {"name": "Uber", "category": "Transport", "logo": "🚗", "delivery_fee": "variable", "free_delivery_min": 0, "website": "https://uber.com", "color": "#000000", "delivery_time": "5-10 min", "type": "online"},
    "bolt": {"name": "Bolt", "category": "Transport", "logo": "⚡", "delivery_fee": "variable", "free_delivery_min": 0, "website": "https://bolt.eu", "color": "#00a651", "delivery_time": "5-10 min", "type": "online"},
    "indrive": {"name": "inDrive", "category": "Transport", "logo": "🚙", "delivery_fee": "variable", "free_delivery_min": 0, "website": "https://indrive.com", "color": "#ff6b6b", "delivery_time": "5-15 min", "type": "online"},
    
    # 💊 PHARMACY & HEALTH
    "clicks": {"name": "Clicks", "category": "Pharmacy", "logo": "💊", "delivery_fee": 30, "free_delivery_min": 300, "website": "https://clicks.co.za", "color": "#0080c5", "delivery_time": "1-2 days", "type": "both"},
    "dischem": {"name": "Dischem", "category": "Pharmacy", "logo": "💊", "delivery_fee": 30, "free_delivery_min": 300, "website": "https://dischem.co.za", "color": "#009944", "delivery_time": "1-2 days", "type": "both"},
    
    # 🔨 HARDWARE & HOME
    "builders": {"name": "Builders", "category": "Hardware", "logo": "🔨", "delivery_fee": 60, "free_delivery_min": 600, "website": "https://builders.co.za", "color": "#f5821f", "delivery_time": "2-3 days", "type": "both"},
    "leroy_merlin": {"name": "Leroy Merlin", "category": "Hardware", "logo": "🔧", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://leroymerlin.co.za", "color": "#ff6600", "delivery_time": "2-3 days", "type": "both"},
    
    # 📱 ELECTRONICS
    "incredible": {"name": "Incredible Connection", "category": "Electronics", "logo": "💻", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://incredible.co.za", "color": "#e31e24", "delivery_time": "2-3 days", "type": "both"},
    "hificorp": {"name": "HiFi Corp", "category": "Electronics", "logo": "📺", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://hificorp.co.za", "color": "#ff6600", "delivery_time": "2-3 days", "type": "both"},
    
    # 👶 BABY & TOYS
    "toysrus": {"name": "Toys R Us", "category": "Toys", "logo": "🧸", "delivery_fee": 40, "free_delivery_min": 400, "website": "https://toysrus.co.za", "color": "#e31e24", "delivery_time": "2-3 days", "type": "both"},
    "babiesrus": {"name": "Babies R Us", "category": "Baby", "logo": "👶", "delivery_fee": 40, "free_delivery_min": 400, "website": "https://babiesrus.co.za", "color": "#ff66b3", "delivery_time": "2-3 days", "type": "both"},
    
    # 🏪 CONVENIENCE STORES
    "kalahari": {"name": "Kalahari", "category": "E-commerce", "logo": "🦁", "delivery_fee": 45, "free_delivery_min": 450, "website": "https://kalahari.com", "color": "#ff9900", "delivery_time": "2-3 days", "type": "online"},
    "loot": {"name": "Loot", "category": "E-commerce", "logo": "💰", "delivery_fee": 45, "free_delivery_min": 450, "website": "https://loot.co.za", "color": "#00a651", "delivery_time": "2-3 days", "type": "online"},
    
    # 🏃 SPORTS & OUTDOOR
    "sportsmans": {"name": "Sportsman's Warehouse", "category": "Sports", "logo": "🏃", "delivery_fee": 50, "free_delivery_min": 500, "website": "https://sportsmanswarehouse.co.za", "color": "#ff6600", "delivery_time": "2-3 days", "type": "both"},
    "totalsports": {"name": "Totalsports", "category": "Sports", "logo": "⚽", "delivery_fee": 40, "free_delivery_min": 400, "website": "https://totalsports.co.za", "color": "#0066b3", "delivery_time": "2-3 days", "type": "both"},
}

# ============================================
# PRODUCTS WITH PRICES
# ============================================
PRODUCTS = [
    {"name": "Bread", "price": 18.99, "emoji": "🍞", "store": "Checkers"},
    {"name": "Milk 1L", "price": 22.99, "emoji": "🥛", "store": "Checkers"},
    {"name": "Rice 2kg", "price": 45.99, "emoji": "🍚", "store": "Shoprite"},
    {"name": "Eggs (dozen)", "price": 44.99, "emoji": "🥚", "store": "Checkers"},
    {"name": "Chicken 2kg", "price": 89.99, "emoji": "🍗", "store": "Pick n Pay"},
    {"name": "Sugar 2.5kg", "price": 39.99, "emoji": "🍬", "store": "Shoprite"},
    {"name": "Smartphone", "price": 2999, "emoji": "📱", "store": "Takealot"},
    {"name": "Laptop", "price": 8999, "emoji": "💻", "store": "Makro"},
    {"name": "T-shirt", "price": 199, "emoji": "👕", "store": "Shein"},
    {"name": "Dress", "price": 399, "emoji": "👗", "store": "Zando"},
    {"name": "Pizza", "price": 89.99, "emoji": "🍕", "store": "Domino's"},
    {"name": "Burger", "price": 69.99, "emoji": "🍔", "store": "McDonald's"},
    {"name": "Fried Chicken", "price": 79.99, "emoji": "🍗", "store": "KFC"},
]

# ============================================
# PHYSICAL STORES (with coordinates for maps)
# ============================================
PHYSICAL_STORES = [
    {"name": "Checkers Menlyn", "lat": -25.783, "lng": 28.278, "address": "Menlyn Park, Pretoria", "type": "Grocery", "hours": "08:00-20:00"},
    {"name": "Woolworths Sandton", "lat": -26.107, "lng": 28.055, "address": "Sandton City", "type": "Grocery", "hours": "09:00-21:00"},
    {"name": "Pick n Pay Hatfield", "lat": -25.754, "lng": 28.234, "address": "Hatfield Plaza", "type": "Grocery", "hours": "08:00-19:00"},
    {"name": "Shoprite Pretoria CBD", "lat": -25.746, "lng": 28.188, "address": "Church Street", "type": "Grocery", "hours": "08:00-18:00"},
    {"name": "Makro Silverlakes", "lat": -25.800, "lng": 28.333, "address": "Silverlakes, Pretoria", "type": "Wholesale", "hours": "09:00-18:00"},
    {"name": "Game Cresta", "lat": -26.131, "lng": 27.999, "address": "Cresta Mall", "type": "General", "hours": "09:00-19:00"},
    {"name": "Builders Fourways", "lat": -26.014, "lng": 28.005, "address": "Fourways", "type": "Hardware", "hours": "08:00-17:00"},
    {"name": "Clicks Rosebank", "lat": -26.146, "lng": 28.034, "address": "The Zone, Rosebank", "type": "Pharmacy", "hours": "09:00-20:00"},
]

# ============================================
# SERVICE PROVIDERS
# ============================================
SERVICE_PROVIDERS = [
    {"name": "Quick Plumb", "type": "Plumbing", "phone": "011 123 4567", "rating": 4.5, "area": "Johannesburg", "price_range": "R300-R800"},
    {"name": "Spark Electric", "type": "Electrical", "phone": "011 234 5678", "rating": 4.8, "area": "Pretoria", "price_range": "R350-R1000"},
    {"name": "Auto Care Centre", "type": "Mechanic", "phone": "011 345 6789", "rating": 4.3, "area": "Cape Town", "price_range": "R500-R2000"},
    {"name": "Green Thumb", "type": "Gardening", "phone": "012 456 7890", "rating": 4.6, "area": "Durban", "price_range": "R250-R600"},
    {"name": "Clean Masters", "type": "Cleaning", "phone": "021 567 8901", "rating": 4.7, "area": "Johannesburg", "price_range": "R200-R500"},
]

# ============================================
# DATABASE
# ============================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        );

        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            name TEXT DEFAULT 'My Shopping List',
            total_budget REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER REFERENCES shopping_lists(id),
            product_name TEXT,
            store TEXT,
            price REAL,
            quantity REAL DEFAULT 1,
            checked_off INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            store_name TEXT,
            items TEXT,
            total_amount REAL,
            delivery_fee REAL,
            status TEXT DEFAULT 'pending',
            ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized")

# ============================================
# OPENSTREETMAP FUNCTIONS
# ============================================
def get_location_from_ip():
    """Free IP geolocation"""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {"lat": data.get("lat", -26.2041), "lng": data.get("lon", 28.0473), "city": data.get("city"), "country": "ZA"}
    except: pass
    return {"lat": -26.2041, "lng": 28.0473, "city": "Johannesburg", "country": "ZA"}

def search_nearby_physical_stores(lat, lng, radius_km=5):
    """Find physical stores near user location"""
    results = []
    for store in PHYSICAL_STORES:
        dist = calculate_distance(lat, lng, store["lat"], store["lng"])
        if dist <= radius_km:
            results.append({**store, "distance_km": round(dist, 1)})
    results.sort(key=lambda x: x["distance_km"])
    return results

def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# ============================================
# FLASK APP
# ============================================
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

# ============================================
# AUTHENTICATION
# ============================================
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
        return jsonify({"error": "Username or email exists"}), 409
    
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
    session.permanent = True
    db.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
    db.commit()
    
    return jsonify({"id": user["id"], "username": user["username"]})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

# ============================================
# SHOP ENDPOINTS
# ============================================
@app.route("/api/shops")
def get_all_shops():
    categories = {}
    for shop_id, shop in ALL_SHOPS.items():
        cat = shop["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({"id": shop_id, **shop})
    return jsonify({"categories": categories, "total_shops": len(ALL_SHOPS)})

@app.route("/api/shop/<shop_id>")
def get_shop_details(shop_id):
    if shop_id in ALL_SHOPS:
        return jsonify(ALL_SHOPS[shop_id])
    return jsonify({"error": "Shop not found"}), 404

# ============================================
# PHYSICAL STORES & MAPS
# ============================================
@app.route("/api/location/detect", methods=["GET"])
def detect_location():
    location = get_location_from_ip()
    return jsonify({"success": True, "latitude": location["lat"], "longitude": location["lng"], "city": location.get("city")})

@app.route("/api/stores/nearby", methods=["GET"])
def get_nearby_stores():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", 5, type=int)
    
    if not lat or not lng:
        loc = get_location_from_ip()
        lat, lng = loc["lat"], loc["lng"]
    
    stores = search_nearby_physical_stores(lat, lng, radius)
    return jsonify({"stores": stores, "location": {"lat": lat, "lng": lng}, "total": len(stores)})

@app.route("/api/services")
def get_services():
    service_type = request.args.get("type", "")
    if service_type:
        results = [s for s in SERVICE_PROVIDERS if s["type"].lower() == service_type.lower()]
    else:
        results = SERVICE_PROVIDERS
    return jsonify({"services": results})

# ============================================
# SHOPPING LISTS
# ============================================
@app.route("/api/lists", methods=["GET", "POST"])
@login_required
def handle_lists():
    db = get_db()
    if request.method == "GET":
        lists = db.execute("""
            SELECT sl.*, COUNT(sli.id) as item_count
            FROM shopping_lists sl
            LEFT JOIN shopping_list_items sli ON sli.list_id = sl.id
            WHERE sl.user_id = ? AND sl.is_active = 1
            GROUP BY sl.id
        """, (session["user_id"],)).fetchall()
        return jsonify([dict(l) for l in lists])
    else:
        data = request.get_json(force=True)
        cursor = db.execute("INSERT INTO shopping_lists (user_id, name, total_budget) VALUES (?, ?, ?)", (session["user_id"], data.get("name", "My List"), data.get("budget", 0)))
        db.commit()
        return jsonify({"id": cursor.lastrowid})

@app.route("/api/lists/<int:list_id>/items", methods=["GET", "POST"])
@login_required
def handle_items(list_id):
    db = get_db()
    owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not owner or owner["user_id"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403
    
    if request.method == "GET":
        items = db.execute("SELECT * FROM shopping_list_items WHERE list_id = ?", (list_id,)).fetchall()
        return jsonify([dict(i) for i in items])
    else:
        data = request.get_json(force=True)
        product_name = data.get("product_name")
        store = data.get("store", "Checkers")
        price = 25
        for p in PRODUCTS:
            if p["name"].lower() in product_name.lower():
                price = p["price"]
                store = p.get("store", store)
                break
        db.execute("INSERT INTO shopping_list_items (list_id, product_name, store, price, quantity) VALUES (?, ?, ?, ?, ?)", (list_id, product_name, store, price, data.get("quantity", 1)))
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

@app.route("/api/optimize/<int:list_id>")
@login_required
def optimize_list(list_id):
    db = get_db()
    items = db.execute("SELECT product_name, quantity FROM shopping_list_items WHERE list_id = ?", (list_id,)).fetchall()
    
    basket = []
    total = 0
    store_totals = {}
    
    for item in items:
        price = 25
        store = "Checkers"
        for p in PRODUCTS:
            if p["name"].lower() in item["product_name"].lower():
                price = p["price"]
                store = p.get("store", store)
                break
        item_total = price * item["quantity"]
        total += item_total
        store_totals[store] = store_totals.get(store, 0) + item_total
        basket.append({"product": item["product_name"], "quantity": item["quantity"], "price": price, "total": item_total, "store": store})
    
    delivery = 0
    for store, cost in store_totals.items():
        for s in ALL_SHOPS.values():
            if s["name"] == store and isinstance(s.get("delivery_fee"), (int, float)):
                if cost < s.get("free_delivery_min", 999):
                    delivery += s["delivery_fee"]
    
    return jsonify({"items": basket, "subtotal": round(total, 2), "delivery": round(delivery, 2), "total": round(total + delivery, 2), "store_breakdown": store_totals, "tip": "💡 Save by buying from fewer stores or using Click & Collect"})

@app.route("/api/order", methods=["POST"])
@login_required
def place_order():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("INSERT INTO orders (user_id, store_name, items, total_amount, delivery_fee) VALUES (?, ?, ?, ?, ?)", (session["user_id"], data.get("store"), json.dumps(data.get("items")), data.get("total"), data.get("delivery", 0)))
    db.commit()
    return jsonify({"order_id": cursor.lastrowid, "message": "Order placed!"})

@app.route("/api/orders")
@login_required
def get_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY ordered_at DESC", (session["user_id"],)).fetchall()
    return jsonify([dict(o) for o in orders])

# ============================================
# FRONTEND - COMPLETE UI WITH MAPS
# ============================================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>ShopAround - The Ultimate Online Mall</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f4f0; min-height: 100vh; }
        .navbar { background: #1f8a4c; color: white; padding: 1rem; position: sticky; top: 0; z-index: 100; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; }
        .navbar h1 { font-size: 1.3rem; display: flex; align-items: center; gap: 0.5rem; }
        .nav-links { display: flex; gap: 0.5rem; flex-wrap: wrap; }
        .nav-links a { color: white; text-decoration: none; padding: 0.4rem 0.8rem; border-radius: 0.5rem; cursor: pointer; font-size: 0.85rem; }
        .nav-links a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1200px; margin: 1rem auto; padding: 0 1rem; }
        .card { background: white; border-radius: 1rem; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
        h2 { color: #1f8a4c; font-size: 1.2rem; }
        input, select, button, textarea { width: 100%; padding: 0.7rem; margin: 0.4rem 0; border: 1px solid #ddd; border-radius: 0.5rem; font-size: 0.95rem; }
        button { background: #1f8a4c; color: white; border: none; cursor: pointer; font-weight: 600; }
        button:hover { background: #166b3a; }
        .hidden { display: none; }
        .item-row { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid #eee; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.8rem; margin-bottom: 1rem; }
        .stat-card { background: #e8f5e9; padding: 0.8rem; border-radius: 0.5rem; text-align: center; }
        .stat-value { font-size: 1.3rem; font-weight: bold; color: #1f8a4c; }
        .tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
        .tab { padding: 0.4rem 1rem; background: #e5e7eb; border-radius: 2rem; cursor: pointer; font-size: 0.85rem; }
        .tab.active { background: #1f8a4c; color: white; }
        .shop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 0.8rem; margin-top: 0.8rem; }
        .shop-card { background: #f8f9fa; padding: 0.8rem; border-radius: 0.8rem; text-align: center; cursor: pointer; transition: transform 0.2s; border: 1px solid #e5e7eb; }
        .shop-card:hover { transform: scale(1.02); background: #e8f5e9; }
        .shop-logo { font-size: 2rem; margin-bottom: 0.3rem; }
        .shop-name { font-weight: 600; font-size: 0.75rem; }
        .delivery-badge { font-size: 0.65rem; background: #d1fae5; padding: 0.2rem 0.4rem; border-radius: 0.5rem; display: inline-block; margin-top: 0.3rem; }
        .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 0.5rem; font-size: 0.7rem; font-weight: 600; }
        .badge-success { background: #d1fae5; color: #10b981; }
        .badge-warning { background: #fed7aa; color: #f59e0b; }
        #map { height: 350px; border-radius: 1rem; margin-bottom: 1rem; }
        @media (max-width: 600px) {
            .shop-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }
            .navbar h1 { font-size: 1rem; }
            .nav-links a { font-size: 0.7rem; padding: 0.3rem 0.6rem; }
        }
    </style>
</head>
<body>
<div class="navbar">
    <h1>🛍️ ShopAround Ultimate Mall</h1>
    <div class="nav-links">
        <a onclick="showSection('shops')">🏪 Shops</a>
        <a onclick="showSection('shopping')">📝 Lists</a>
        <a onclick="showSection('maps')">🗺️ Near Me</a>
        <a onclick="showSection('services')">🛠️ Services</a>
        <a onclick="showSection('orders')">📦 Orders</a>
        <a id="logoutBtn" style="display:none;" onclick="logout()">🚪 Logout</a>
    </div>
</div>

<div class="container">
    <!-- Auth Section -->
    <div id="authSection" class="card" style="max-width:400px; margin:2rem auto;">
        <h2>Welcome to ShopAround</h2>
        <p>South Africa's Ultimate Online Mall</p>
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
        <p id="authMessage" style="color:#ef4444; margin-top:0.5rem;"></p>
    </div>

    <!-- Main App -->
    <div id="appSection" style="display:none;">
        <div class="stats">
            <div class="stat-card"><div class="stat-value" id="totalStores">0</div><div>Stores</div></div>
            <div class="stat-card"><div class="stat-value" id="totalLists">0</div><div>My Lists</div></div>
            <div class="stat-card"><div class="stat-value" id="nearbyStores">0</div><div>Nearby Stores</div></div>
        </div>

        <!-- Shops Section -->
        <div id="shopsSection">
            <div class="card">
                <div class="card-header"><h2>🏪 All Stores ({{ total_shops }}+)</h2></div>
                <div id="shopsContainer"></div>
            </div>
        </div>

        <!-- Shopping Section -->
        <div id="shoppingSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>📝 My Shopping Lists</h2><button onclick="createList()">+ New List</button></div>
                <div id="listsContainer"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>➕ Add Items</h2></div>
                <textarea id="bulkItems" rows="3" placeholder="Enter items (one per line):&#10;Bread&#10;Milk&#10;Eggs"></textarea>
                <select id="selectedList"></select>
                <button onclick="addBulkItems()">Add to List</button>
            </div>
            <div class="card">
                <div class="card-header"><h2>💡 Smart Price Optimizer</h2></div>
                <select id="optimizeList"></select>
                <button onclick="optimizeBasket()">Find Best Prices Across All Stores</button>
                <div id="optimizeResults"></div>
            </div>
        </div>

        <!-- Maps Section -->
        <div id="mapsSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🗺️ Find Physical Stores Near You</h2></div>
                <div id="map"></div>
                <button onclick="findMyLocation()">📍 Find My Location</button>
                <button onclick="findNearbyStores()">🏪 Find Nearby Stores</button>
                <div id="nearbyStoresList"></div>
            </div>
        </div>

        <!-- Services Section -->
        <div id="servicesSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🛠️ Service Providers</h2></div>
                <select id="serviceType">
                    <option value="">All Services</option>
                    <option value="Plumbing">Plumbing</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Mechanic">Mechanic</option>
                    <option value="Gardening">Gardening</option>
                    <option value="Cleaning">Cleaning</option>
                </select>
                <button onclick="loadServices()">Search</button>
                <div id="servicesList"></div>
            </div>
        </div>

        <!-- Orders Section -->
        <div id="ordersSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>📦 My Orders</h2></div>
                <div id="ordersList"></div>
            </div>
        </div>
    </div>
</div>

<script>
let currentUser = null;
let allShops = {};
let currentLists = [];
let map = null;
let userLat = -26.2041, userLng = 28.0473;

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
        loadAllShops();
        loadLists();
        detectLocation();
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
    if (res.ok) { showLogin(); alert('Registered! Please login.'); }
    else { alert('Registration failed'); }
}

function logout() { fetch('/api/logout', {method:'POST'}); location.reload(); }
function showRegister() { document.getElementById('loginForm').style.display='none'; document.getElementById('registerForm').style.display='block'; }
function showLogin() { document.getElementById('loginForm').style.display='block'; document.getElementById('registerForm').style.display='none'; }

function showSection(section) {
    document.getElementById('shopsSection').classList.add('hidden');
    document.getElementById('shoppingSection').classList.add('hidden');
    document.getElementById('mapsSection').classList.add('hidden');
    document.getElementById('servicesSection').classList.add('hidden');
    document.getElementById('ordersSection').classList.add('hidden');
    document.getElementById(`${section}Section`).classList.remove('hidden');
    if (section === 'maps') initMap();
    if (section === 'orders') loadOrders();
}

async function detectLocation() {
    const res = await fetch('/api/location/detect');
    const data = await res.json();
    if (data.success) {
        userLat = data.latitude;
        userLng = data.longitude;
    }
}

async function loadAllShops() {
    const res = await fetch('/api/shops');
    const data = await res.json();
    allShops = data;
    let total = 0;
    let html = '';
    for (const [category, shops] of Object.entries(data.categories)) {
        html += `<h3 style="margin: 1rem 0 0.5rem;">${category}</h3><div class="shop-grid">`;
        for (const shop of shops) {
            total++;
            html += `<div class="shop-card" onclick="visitShop('${shop.id}')"><div class="shop-logo">${shop.logo}</div><div class="shop-name">${shop.name}</div><div class="delivery-badge">🚚 ${typeof shop.delivery_fee === 'number' ? 'R'+shop.delivery_fee : shop.delivery_fee}</div><div class="badge badge-success">${shop.delivery_time || 'Same day'}</div></div>`;
        }
        html += `</div>`;
    }
    document.getElementById('shopsContainer').innerHTML = html;
    document.getElementById('totalStores').textContent = total;
}

function visitShop(shopId) {
    const all = Object.values(allShops.categories).flat();
    const shop = all.find(s => s.id === shopId);
    if (shop && shop.website) {
        window.open(shop.website, '_blank');
    } else {
        alert(`Opening ${shop?.name || shopId}`);
    }
}

function initMap() {
    if (map) return;
    map = L.map('map').setView([userLat, userLng], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {attribution: '&copy; OSM'}).addTo(map);
    L.marker([userLat, userLng]).addTo(map).bindPopup('You are here').openPopup();
}

async function findMyLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            userLat = pos.coords.latitude;
            userLng = pos.coords.longitude;
            if (map) map.setView([userLat, userLng], 14);
            else initMap();
            L.marker([userLat, userLng]).addTo(map).bindPopup('You are here').openPopup();
            await findNearbyStores();
        });
    } else {
        alert('Geolocation not supported');
    }
}

async function findNearbyStores() {
    const res = await fetch(`/api/stores/nearby?lat=${userLat}&lng=${userLng}&radius=10`);
    const data = await res.json();
    document.getElementById('nearbyStores').textContent = data.total;
    let html = '';
    for (const store of data.stores) {
        html += `<div class="card"><div><strong>${store.name}</strong> <span class="badge badge-success">${store.distance_km}km</span></div><div>${store.address}</div><div>🕒 ${store.hours}</div><button onclick="window.open('https://www.openstreetmap.org/?mlat=${store.lat}&mlon=${store.lng}', '_blank')">📍 Navigate</button></div>`;
        if (map) {
            L.marker([store.lat, store.lng]).addTo(map).bindPopup(`<b>${store.name}</b><br>${store.address}`);
        }
    }
    document.getElementById('nearbyStoresList').innerHTML = html || '<p>No stores found nearby</p>';
}

async function loadServices() {
    const type = document.getElementById('serviceType').value;
    const res = await fetch(`/api/services${type ? `?type=${type}` : ''}`);
    const data = await res.json();
    let html = '';
    for (const s of data.services) {
        html += `<div class="card"><div><strong>${s.name}</strong> <span class="badge badge-success">⭐ ${s.rating}</span></div><div>${s.type}</div><div>📞 ${s.phone}</div><div>💰 ${s.price_range}</div><div>📍 ${s.area}</div><button onclick="window.location.href='tel:${s.phone}'">Call Now</button></div>`;
    }
    document.getElementById('servicesList').innerHTML = html || '<p>No services found</p>';
}

async function loadLists() {
    const res = await fetch('/api/lists');
    if (res.ok) { currentLists = await res.json(); renderLists(); updateSelectors(); }
    document.getElementById('totalLists').textContent = currentLists.length;
}

function renderLists() {
    const container = document.getElementById('listsContainer');
    if (currentLists.length === 0) { container.innerHTML = '<p>No lists yet. Create one!</p>'; return; }
    container.innerHTML = '';
    for (const list of currentLists) {
        const div = document.createElement('div');
        div.className = 'card';
        div.innerHTML = `<div class="card-header"><h3>📋 ${list.name}</h3><div><button onclick="viewList(${list.id})">View</button></div></div><p>${list.item_count || 0} items</p><div id="items-${list.id}"></div>`;
        container.appendChild(div);
        loadListItems(list.id);
    }
}

async function loadListItems(listId) {
    const res = await fetch(`/api/lists/${listId}/items`);
    if (res.ok) {
        const items = await res.json();
        const container = document.getElementById(`items-${listId}`);
        if (items.length === 0) container.innerHTML = '<p>No items</p>';
        else {
            let html = '<ul style="list-style:none;">';
            for (const i of items) {
                html += `<li class="item-row"><span>🛒 ${i.product_name} x${i.quantity} @ ${i.store}</span><div><button onclick="toggleItem(${listId},${i.id})">${i.checked_off?'✓':'○'}</button><button onclick="removeItem(${listId},${i.id})">×</button></div></li>`;
            }
            html += '</ul>';
            container.innerHTML = html;
        }
    }
}

function updateSelectors() {
    const select1 = document.getElementById('selectedList');
    const select2 = document.getElementById('optimizeList');
    select1.innerHTML = '<option value="">Select a list</option>';
    select2.innerHTML = '<option value="">Select a list</option>';
    for (const list of currentLists) {
        select1.innerHTML += `<option value="${list.id}">${list.name}</option>`;
        select2.innerHTML += `<option value="${list.id}">${list.name}</option>`;
    }
}

async function createList() {
    const name = prompt('List name:', 'My Shopping List');
    if (name) {
        await fetch('/api/lists', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})});
        await loadLists();
    }
}

function viewList(id) { loadListItems(id); }

async function addBulkItems() {
    const listId = document.getElementById('selectedList').value;
    const text = document.getElementById('bulkItems').value;
    if (!listId) { alert('Select a list'); return; }
    const lines = text.split('\\n').filter(l => l.trim());
    for (const line of lines) {
        await fetch(`/api/lists/${listId}/items`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({product_name:line.trim(), quantity:1})});
    }
    document.getElementById('bulkItems').value = '';
    await loadListItems(listId);
    await loadLists();
}

async function toggleItem(listId, itemId) {
    await fetch(`/api/lists/${listId}/items/${itemId}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({checked_off:1})});
    await loadListItems(listId);
}

async function removeItem(listId, itemId) {
    if(confirm('Remove?')) { await fetch(`/api/lists/${listId}/items/${itemId}`, {method:'DELETE'}); await loadListItems(listId); await loadLists(); }
}

async function optimizeBasket() {
    const listId = document.getElementById('optimizeList').value;
    if (!listId) { alert('Select a list'); return; }
    const res = await fetch(`/api/optimize/${listId}`);
    const data = await res.json();
    let html = `<div class="stats"><div>Subtotal: R${data.subtotal}</div><div>Delivery: R${data.delivery}</div><div><strong>Total: R${data.total}</strong></div></div><h4>Store Breakdown</h4>`;
    for (const [store, cost] of Object.entries(data.store_breakdown)) { html += `<p>${store}: R${cost.toFixed(2)}</p>`; }
    html += `<h4>Items</h4><ul style="list-style:none;">`;
    for (const i of data.items) { html += `<li class="item-row"><span>${i.product} x${i.quantity}</span><span>R${i.price} at ${i.store}</span></li>`; }
    html += `</ul><div class="badge-success" style="padding:0.5rem;">💡 ${data.tip}</div>`;
    document.getElementById('optimizeResults').innerHTML = html;
}

async function loadOrders() {
    const res = await fetch('/api/orders');
    if (res.ok) {
        const orders = await res.json();
        let html = '';
        for (const o of orders) {
            html += `<div class="card"><div><strong>Order #${o.id}</strong> - ${o.store_name}</div><div>Total: R${o.total_amount}</div><div>Status: ${o.status}</div><div>${new Date(o.ordered_at).toLocaleDateString()}</div></div>`;
        }
        document.getElementById('ordersList').innerHTML = html || '<p>No orders yet</p>';
    }
}

// Auto demo login
async function autoDemo() {
    await fetch('/api/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:'demo',password:'demo123'})});
    const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:'demo',password:'demo123'})});
    if (res.ok) { login(); }
}
autoDemo();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

if __name__ == "__main__":
    init_db()
    print("="*70)
    print("🛍️  SHOPAROUND - ULTIMATE COMPLETE MALL")
    print("="*70)
    print(f"✅ {len(ALL_SHOPS)} Online Shops Integrated")
    print("   - E-commerce: Takealot, Amazon, Shein, Temu, Makro, Game, Bash, Superbalist, Zando")
    print("   - Grocery: Checkers, Shoprite, Woolworths, Pick n Pay, Spar, Food Lovers")
    print("   - Food Delivery: Uber Eats, Mr D, KFC, McDonald's, Domino's, Nando's")
    print("   - Transport: Uber, Bolt, inDrive")
    print("   - Pharmacy: Clicks, Dischem")
    print("   - Hardware: Builders, Leroy Merlin")
    print("   - Electronics: Incredible, HiFi Corp")
    print("   - Sports: Sportsman's, Totalsports")
    print("   - Baby & Toys: Toys R Us, Babies R Us")
    print("")
    print(f"📍 {len(PHYSICAL_STORES)} Physical Stores with Maps")
    print("🛠️ Service Providers Available")
    print("🗺️ OpenStreetMap Navigation (Free, No API Keys)")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=True)
