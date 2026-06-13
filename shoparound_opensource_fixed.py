"""
SHOPAROUND - Open Source Edition (Fixed)
No API keys, 100% free, with proper database schema
"""

import sqlite3
import os
import json
import secrets
import re
import math
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)

# ============================================
# DATABASE INITIALIZATION WITH FULL SCHEMA
# ============================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Complete users table with all columns
    cursor.execute("""
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
            last_login DATETIME
        )
    """)
    
    # Service providers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service_type TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            phone TEXT,
            website TEXT,
            rating REAL,
            opening_hours TEXT,
            source TEXT DEFAULT 'osm',
            verified INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Shopping lists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            name TEXT DEFAULT 'My List',
            total_budget REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Shopping list items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER REFERENCES shopping_lists(id),
            product_name TEXT,
            quantity REAL DEFAULT 1,
            checked_off INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample service providers if table is empty
    cursor.execute("SELECT COUNT(*) FROM service_providers")
    if cursor.fetchone()[0] == 0:
        sample_providers = [
            ("Plumbmaster JHB", "plumbing", "Johannesburg", -26.2041, 28.0473, "011 123 4567", 4.2),
            ("JHB Electricians", "electrical", "Johannesburg", -26.2025, 28.0450, "011 234 5678", 4.5),
            ("Auto Care Centre", "mechanic", "Johannesburg", -26.2080, 28.0500, "011 345 6789", 4.0),
            ("Pretoria Plumbers", "plumbing", "Pretoria", -25.7461, 28.1881, "012 345 6789", 4.3),
            ("PTA Electric", "electrical", "Pretoria", -25.7500, 28.1900, "012 456 7890", 4.4),
            ("Cape Plumbing", "plumbing", "Cape Town", -33.9249, 18.4241, "021 123 4567", 4.6),
            ("CT Electricians", "electrical", "Cape Town", -33.9200, 18.4200, "021 234 5678", 4.3),
            ("Durban Mechanics", "mechanic", "Durban", -29.8587, 31.0218, "031 123 4567", 4.1),
        ]
        for p in sample_providers:
            cursor.execute("""
                INSERT INTO service_providers (name, service_type, address, latitude, longitude, phone, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, p)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with complete schema")

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

# ============================================
# OPENSTREETMAP API (Free)
# ============================================
def get_osm_service_providers(lat, lng, radius_km=5, service_type=None):
    """Fetch service providers from OpenStreetMap"""
    radius_deg = radius_km / 111.0
    bbox = f"{lat - radius_deg},{lng - radius_deg},{lat + radius_deg},{lng + radius_deg}"
    
    osm_tags = {
        "plumbing": ["shop=plumber", "craft=plumber"],
        "electrical": ["shop=electrician", "craft=electrician"],
        "mechanic": ["shop=car_repair", "amenity=vehicle_repair"],
        "cleaning": ["shop=cleaning", "craft=cleaner"],
        "gardening": ["shop=garden_centre"],
        "handyman": ["shop=hardware"]
    }
    
    tags = osm_tags.get(service_type, ["shop=*", "craft=*"])
    results = []
    
    for tag in tags:
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:25];
        (
          node["{tag.split('=')[0]}"="{tag.split('=')[1]}"]{bbox};
          way["{tag.split('=')[0]}"="{tag.split('=')[1]}"]{bbox};
        );
        out body;
        """
        try:
            response = requests.post(overpass_url, data={"data": query}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for element in data.get("elements", []):
                    tags = element.get("tags", {})
                    results.append({
                        "name": tags.get("name", "Service Provider"),
                        "latitude": element.get("lat"),
                        "longitude": element.get("lon"),
                        "address": tags.get("addr:street", ""),
                        "phone": tags.get("phone", ""),
                        "rating": 4.0
                    })
        except Exception as e:
            print(f"OSM error: {e}")
    
    # Calculate distances
    for p in results:
        if p["latitude"] and lat:
            p["distance_km"] = calculate_distance(lat, lng, p["latitude"], p["longitude"])
        else:
            p["distance_km"] = None
    
    results.sort(key=lambda x: x.get("distance_km") or 999)
    return results[:20]

def get_location_from_ip():
    """Free IP geolocation"""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "lat": data.get("lat", -26.2041),
                    "lng": data.get("lon", 28.0473),
                    "city": data.get("city", "Johannesburg")
                }
    except:
        pass
    return {"lat": -26.2041, "lng": 28.0473, "city": "Johannesburg"}

def calculate_distance(lat1, lng1, lat2, lng2):
    if not lat1 or not lat2:
        return None
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

def get_major_retailers():
    return [
        {"name": "Checkers", "category": "Grocery", "delivery_fee": 35, "free_delivery_min": 350},
        {"name": "Shoprite", "category": "Grocery", "delivery_fee": 35, "free_delivery_min": 350},
        {"name": "Woolworths", "category": "Grocery", "delivery_fee": 45, "free_delivery_min": 450},
        {"name": "Pick n Pay", "category": "Grocery", "delivery_fee": 35, "free_delivery_min": 350},
        {"name": "Makro", "category": "Wholesale", "delivery_fee": 50, "free_delivery_min": 500},
        {"name": "Game", "category": "General", "delivery_fee": 50, "free_delivery_min": 500},
    ]

def get_products():
    return [
        {"name": "Bread", "price": 18.99, "emoji": "🍞", "store": "Checkers"},
        {"name": "Milk 1L", "price": 22.99, "emoji": "🥛", "store": "Checkers"},
        {"name": "Rice 2kg", "price": 45.99, "emoji": "🍚", "store": "Shoprite"},
        {"name": "Eggs (dozen)", "price": 44.99, "emoji": "🥚", "store": "Checkers"},
        {"name": "Chicken 2kg", "price": 89.99, "emoji": "🍗", "store": "Pick n Pay"},
        {"name": "Sugar 2.5kg", "price": 39.99, "emoji": "🍬", "store": "Shoprite"},
    ]

# ============================================
# AUTHENTICATION ROUTES
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
    
    # Update last_login (column now exists)
    try:
        db.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
        db.commit()
    except:
        pass
    
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"]
    })

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

# ============================================
# SERVICE PROVIDER ROUTES
# ============================================
@app.route("/api/services/nearby", methods=["GET"])
def get_nearby_services():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    service_type = request.args.get("type", "handyman")
    
    if not lat or not lng:
        ip_loc = get_location_from_ip()
        lat = ip_loc["lat"]
        lng = ip_loc["lng"]
    
    # Get from local database first
    db = get_db()
    local = db.execute("""
        SELECT * FROM service_providers 
        WHERE service_type = ? OR ? = ''
        LIMIT 20
    """, (service_type, service_type)).fetchall()
    
    # Get from OpenStreetMap
    osm = get_osm_service_providers(lat, lng, 10, service_type)
    
    # Combine results
    services = []
    for p in local:
        dist = calculate_distance(lat, lng, p["latitude"], p["longitude"]) if p["latitude"] else None
        services.append({
            "source": "local",
            "name": p["name"],
            "service_type": p["service_type"],
            "address": p["address"],
            "phone": p["phone"],
            "rating": p["rating"],
            "distance_km": dist,
            "latitude": p["latitude"],
            "longitude": p["longitude"]
        })
    
    for p in osm:
        services.append({
            "source": "osm",
            "name": p["name"],
            "service_type": service_type,
            "address": p.get("address", ""),
            "phone": p.get("phone", ""),
            "rating": p.get("rating", 4.0),
            "distance_km": p.get("distance_km"),
            "latitude": p["latitude"],
            "longitude": p["longitude"]
        })
    
    services.sort(key=lambda x: x.get("distance_km") if x.get("distance_km") else 999)
    
    return jsonify({
        "success": True,
        "location": {"lat": lat, "lng": lng},
        "services": services[:30]
    })

@app.route("/api/location/detect", methods=["GET"])
def detect_location():
    loc = get_location_from_ip()
    return jsonify({
        "success": True,
        "latitude": loc["lat"],
        "longitude": loc["lng"],
        "city": loc.get("city")
    })

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
            ORDER BY sl.created_at DESC
        """, (session["user_id"],)).fetchall()
        return jsonify([dict(l) for l in lists])
    else:
        data = request.get_json(force=True)
        cursor = db.execute(
            "INSERT INTO shopping_lists (user_id, name, total_budget) VALUES (?, ?, ?)",
            (session["user_id"], data.get("name", "My List"), data.get("budget", 0))
        )
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
        items = db.execute("SELECT * FROM shopping_list_items WHERE list_id = ?", (list_id,)).fetchall()
        return jsonify([dict(i) for i in items])
    else:
        data = request.get_json(force=True)
        db.execute("""
            INSERT INTO shopping_list_items (list_id, product_name, quantity)
            VALUES (?, ?, ?)
        """, (list_id, data.get("product_name"), data.get("quantity", 1)))
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
    items = db.execute("SELECT product_name, quantity FROM shopping_list_items WHERE list_id = ? AND checked_off = 0", (list_id,)).fetchall()
    products = get_products()
    retailers = get_major_retailers()
    
    basket = []
    total = 0
    store_totals = {}
    
    for item in items:
        best_price = 50
        best_store = "Checkers"
        for product in products:
            if product["name"].lower() in item["product_name"].lower():
                best_price = product["price"]
                best_store = product["store"]
                break
        item_total = best_price * item["quantity"]
        total += item_total
        store_totals[best_store] = store_totals.get(best_store, 0) + item_total
        basket.append({
            "product": item["product_name"],
            "quantity": item["quantity"],
            "price": round(best_price, 2),
            "total": round(item_total, 2),
            "store": best_store
        })
    
    delivery_fee = 0
    for store, cost in store_totals.items():
        retailer = next((r for r in retailers if r["name"] == store), None)
        if retailer and retailer["free_delivery_min"] > 0 and cost < retailer["free_delivery_min"]:
            delivery_fee += retailer["delivery_fee"]
    
    return jsonify({
        "items": basket,
        "subtotal": round(total, 2),
        "delivery": round(delivery_fee, 2),
        "total": round(total + delivery_fee, 2),
        "store_breakdown": store_totals
    })

# ============================================
# FRONTEND
# ============================================
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround - Open Source Mall</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f0;}
        .navbar{background:#1f8a4c;color:white;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;}
        .navbar h1{font-size:1.5rem;}
        .nav-links{display:flex;gap:1rem;}
        .nav-links a{color:white;text-decoration:none;padding:0.5rem 1rem;border-radius:0.5rem;cursor:pointer;}
        .nav-links a:hover{background:rgba(255,255,255,0.2);}
        .container{max-width:1200px;margin:2rem auto;padding:0 2rem;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;border-bottom:2px solid #e5e7eb;padding-bottom:0.5rem;}
        h2{color:#1f8a4c;font-size:1.25rem;}
        input,select,button,textarea{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #ddd;border-radius:0.5rem;font-size:1rem;}
        button{background:#1f8a4c;color:white;border:none;cursor:pointer;font-weight:600;}
        button:hover{background:#166b3a;}
        .hidden{display:none;}
        .item-row{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 0;border-bottom:1px solid #eee;}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-bottom:1rem;}
        .stat-card{background:#e8f5e9;padding:1rem;border-radius:0.5rem;text-align:center;}
        .stat-value{font-size:1.5rem;font-weight:bold;color:#1f8a4c;}
        .tabs{display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap;}
        .tab{padding:0.5rem 1rem;background:#e5e7eb;border-radius:0.5rem;cursor:pointer;}
        .tab.active{background:#1f8a4c;color:white;}
        #map{height:400px;border-radius:1rem;margin-bottom:1rem;}
        .badge{display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;font-size:0.75rem;font-weight:600;}
        .badge-success{background:#d1fae5;color:#10b981;}
        @media (max-width:768px){.container{padding:0 1rem;}}
    </style>
</head>
<body>
<div class="navbar">
    <h1>🛍️ ShopAround</h1>
    <div class="nav-links">
        <a onclick="showSection('shopping')">Shopping</a>
        <a onclick="showSection('services')">Services</a>
        <a onclick="showSection('map')">Map</a>
        <a id="logoutBtn" style="display:none;" onclick="logout()">Logout</a>
    </div>
</div>

<div class="container">
    <div id="authSection" class="card" style="max-width:400px; margin:2rem auto;">
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
        <p id="authMessage" style="color:#ef4444; margin-top:1rem;"></p>
    </div>

    <div id="appSection" style="display:none;">
        <div class="stats">
            <div class="stat-card"><div class="stat-value" id="totalSpent">R0</div><div>Total Spend</div></div>
            <div class="stat-card"><div class="stat-value" id="savings">0%</div><div>Potential Savings</div></div>
        </div>

        <div id="shoppingSection">
            <div class="card"><div class="card-header"><h2>📝 My Lists</h2><button onclick="createList()">+ New</button></div><div id="listsContainer"></div></div>
            <div class="card"><div class="card-header"><h2>➕ Add Items</h2></div><textarea id="bulkItems" rows="3" placeholder="Bread&#10;Milk&#10;Eggs"></textarea><select id="selectedList"></select><button onclick="addBulkItems()">Add</button></div>
            <div class="card"><div class="card-header"><h2>💡 Optimize</h2></div><select id="optimizeList"></select><button onclick="optimizeBasket()">Find Best Prices</button><div id="optimizeResults"></div></div>
        </div>

        <div id="servicesSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🛠️ Find Services</h2></div>
            <select id="serviceType"><option value="plumbing">Plumbing</option><option value="electrical">Electrical</option><option value="mechanic">Mechanic</option></select>
            <button onclick="findNearbyServices()">🔍 Search</button><div id="servicesList"></div></div>
        </div>

        <div id="mapSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🗺️ Nearby Map</h2></div><div id="map"></div><button onclick="locateMe()">📍 My Location</button><div id="mapResults"></div></div>
        </div>
    </div>
</div>

<script>
let map = null;
let currentLists = [];

async function login(){
    const u=document.getElementById('loginUsername').value, p=document.getElementById('loginPassword').value;
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    if(r.ok){
        document.getElementById('authSection').style.display='none';
        document.getElementById('appSection').style.display='block';
        document.getElementById('logoutBtn').style.display='inline-block';
        loadLists(); initMap();
    }else alert('Login failed');
}

async function register(){
    const u=document.getElementById('regUsername').value, e=document.getElementById('regEmail').value, p=document.getElementById('regPassword').value;
    const r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,email:e,password:p})});
    if(r.ok){ showLogin(); alert('Registered!'); }
    else alert('Failed');
}

function logout(){ fetch('/api/logout',{method:'POST'}); location.reload(); }
function showRegister(){ document.getElementById('loginForm').style.display='none'; document.getElementById('registerForm').style.display='block'; }
function showLogin(){ document.getElementById('loginForm').style.display='block'; document.getElementById('registerForm').style.display='none'; }

function showSection(s){
    document.getElementById('shoppingSection').classList.add('hidden');
    document.getElementById('servicesSection').classList.add('hidden');
    document.getElementById('mapSection').classList.add('hidden');
    document.getElementById(`${s}Section`).classList.remove('hidden');
    if(s==='map' && map) map.invalidateSize();
}

function initMap(){ if(!map){ map=L.map('map').setView([-26.2041,28.0473],12); L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'OSM'}).addTo(map); } }

async function locateMe(){
    initMap();
    const r=await fetch('/api/location/detect');
    const loc=await r.json();
    if(loc.success){
        map.setView([loc.latitude,loc.longitude],14);
        L.marker([loc.latitude,loc.longitude]).addTo(map).bindPopup('You are here').openPopup();
    }
}

async function findNearbyServices(){
    const type=document.getElementById('serviceType').value;
    const loc=await (await fetch('/api/location/detect')).json();
    const r=await fetch(`/api/services/nearby?lat=${loc.latitude}&lng=${loc.longitude}&type=${type}`);
    const data=await r.json();
    if(data.services&&data.services.length){
        let html='';
        for(const s of data.services){
            html+=`<div class="card"><strong>${s.name}</strong><br>📞 ${s.phone||'N/A'}<br>⭐ ${s.rating||'N/A'}<br>${s.distance_km?`📍 ${s.distance_km}km away`:''}<button onclick="window.open('https://www.openstreetmap.org/?mlat=${s.latitude}&mlon=${s.longitude}','_blank')">📍 Map</button></div>`;
        }
        document.getElementById('servicesList').innerHTML=html;
    }else document.getElementById('servicesList').innerHTML='<div class="card">No services found nearby</div>';
}

async function loadLists(){
    const r=await fetch('/api/lists');
    if(r.ok){ currentLists=await r.json(); renderLists(); updateSelectors(); }
}

function renderLists(){
    const c=document.getElementById('listsContainer');
    if(!currentLists.length){ c.innerHTML='<p>No lists</p>'; return; }
    c.innerHTML='';
    for(const l of currentLists){
        const div=document.createElement('div');
        div.className='card';
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
            for(const i of items) html+=`<div class="item-row"><span>🛒 ${i.product_name} x${i.quantity}</span><div><button onclick="toggleItem(${id},${i.id})">${i.checked_off?'✓':'○'}</button><button onclick="removeItem(${id},${i.id})">×</button></div></div>`;
            c.innerHTML=html;
        }
    }
}

function updateSelectors(){
    const s1=document.getElementById('selectedList'), s2=document.getElementById('optimizeList');
    s1.innerHTML='<option value="">Select list</option>'; s2.innerHTML='<option value="">Select list</option>';
    for(const l of currentLists){
        s1.innerHTML+=`<option value="${l.id}">${l.name}</option>`;
        s2.innerHTML+=`<option value="${l.id}">${l.name}</option>`;
    }
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
async function removeItem(lid,iid){ if(confirm('Remove?')){ await fetch(`/api/lists/${lid}/items/${iid}`,{method:'DELETE'}); await loadListItems(lid); await loadLists(); } }

async function optimizeBasket(){
    const lid=document.getElementById('optimizeList').value;
    if(!lid) return alert('Select list');
    const r=await fetch(`/api/optimize/${lid}`);
    const d=await r.json();
    let html=`<div class="stats"><div>Items: R${d.subtotal}</div><div>Delivery: R${d.delivery}</div><div><strong>Total: R${d.total}</strong></div></div><h4>Best Prices</h4>`;
    for(const i of d.items) html+=`<div class="item-row"><span>${i.product} x${i.quantity}</span><span>R${i.price} at ${i.store}</span></div>`;
    document.getElementById('optimizeResults').innerHTML=html;
}

// Auto demo login
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
    return render_template_string(INDEX_HTML)

if __name__ == "__main__":
    print("="*60)
    print("🛍️  SHOPAROUND - Open Source Edition (Fixed)")
    print("="*60)
    print("✅ No API Keys Required")
    print("✅ OpenStreetMap Integration")
    print("✅ IP Geolocation (Free)")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True)
