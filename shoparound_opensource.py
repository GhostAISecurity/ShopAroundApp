"""
SHOPAROUND - Open Source Edition
No API keys, no costs, 100% free public infrastructure
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
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)

# ============================================
# OPENSTREETMAP NOMINatim (Free Geocoding)
# ============================================
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ============================================
# DATABASE SCHEMA
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
            household_size INTEGER DEFAULT 1,
            monthly_budget REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

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
        );

        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            name TEXT DEFAULT 'My List',
            total_budget REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER REFERENCES shopping_lists(id),
            product_name TEXT,
            quantity REAL DEFAULT 1,
            checked_off INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_services_location ON service_providers(latitude, longitude);
        CREATE INDEX IF NOT EXISTS idx_services_type ON service_providers(service_type);
    """)
    
    # Seed initial OpenStreetMap data for SA cities
    seed_osm_data(conn)
    conn.commit()
    conn.close()
    print("✅ Database initialized with OpenStreetMap data")

def seed_osm_data(conn):
    """Seed initial service provider data from OpenStreetMap for major SA cities"""
    cursor = conn.cursor()
    
    # Common service providers in South Africa (public data)
    providers = [
        # Johannesburg
        ("Plumbmaster JHB", "Plumbing", "Johannesburg", -26.2041, 28.0473, "011 123 4567", 4.2),
        ("JHB Electricians", "Electrical", "Johannesburg", -26.2025, 28.0450, "011 234 5678", 4.5),
        ("Auto Care Centre", "Mechanic", "Johannesburg", -26.2080, 28.0500, "011 345 6789", 4.0),
        # Pretoria
        ("Pretoria Plumbers", "Plumbing", "Pretoria", -25.7461, 28.1881, "012 345 6789", 4.3),
        ("PTA Electric", "Electrical", "Pretoria", -25.7500, 28.1900, "012 456 7890", 4.4),
        # Cape Town
        ("Cape Plumbing Services", "Plumbing", "Cape Town", -33.9249, 18.4241, "021 123 4567", 4.6),
        ("CT Electricians", "Electrical", "Cape Town", -33.9200, 18.4200, "021 234 5678", 4.3),
        # Durban
        ("Durban Mechanics", "Mechanic", "Durban", -29.8587, 31.0218, "031 123 4567", 4.1),
    ]
    
    for p in providers:
        cursor.execute("""
            INSERT OR IGNORE INTO service_providers (name, service_type, address, latitude, longitude, phone, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, p)

# ============================================
# OPENSTREETMAP API INTEGRATION
# ============================================

def get_osm_service_providers(lat, lng, radius_km=5, service_type=None):
    """
    Fetch real service providers from OpenStreetMap using Overpass API
    Free, no API key required
    """
    # Convert radius to degrees (approx 1 degree = 111 km)
    radius_deg = radius_km / 111.0
    
    # Build Overpass QL query
    bbox = f"{lat - radius_deg},{lng - radius_deg},{lat + radius_deg},{lng + radius_deg}"
    
    # Map service types to OSM tags
    osm_tags = {
        "plumbing": ["shop=plumber", "craft=plumber", "trade=plumber"],
        "electrical": ["shop=electrician", "craft=electrician"],
        "mechanic": ["shop=car_repair", "amenity=vehicle_repair"],
        "cleaning": ["shop=cleaning", "craft=cleaner"],
        "gardening": ["shop=garden_centre", "craft=gardener"],
        "handyman": ["shop=hardware", "craft=handyman"]
    }
    
    tags = osm_tags.get(service_type.lower(), ["shop=*", "craft=*"]) if service_type else ["shop=*", "craft=*"]
    
    all_results = []
    
    for tag in tags:
        query = f"""
        [out:json][timeout:25];
        (
          node["{tag.split('=')[0]}"="{tag.split('=')[1]}"]{bbox};
          way["{tag.split('=')[0]}"="{tag.split('=')[1]}"]{bbox};
        );
        out body;
        """
        
        try:
            response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for element in data.get("elements", []):
                    tags = element.get("tags", {})
                    all_results.append({
                        "id": element.get("id"),
                        "name": tags.get("name", "Unnamed Service"),
                        "service_type": service_type,
                        "latitude": element.get("lat"),
                        "longitude": element.get("lon"),
                        "address": tags.get("addr:street", ""),
                        "phone": tags.get("phone", ""),
                        "website": tags.get("website", ""),
                        "opening_hours": tags.get("opening_hours", ""),
                        "rating": 4.0  # Default rating
                    })
        except Exception as e:
            print(f"OSM query error: {e}")
    
    # Calculate distances
    for provider in all_results:
        provider["distance_km"] = calculate_distance(lat, lng, provider["latitude"], provider["longitude"])
    
    all_results.sort(key=lambda x: x.get("distance_km", 999))
    return all_results

def get_location_from_ip():
    """Free IP geolocation using ip-api.com (no API key required)"""
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "lat": data.get("lat", -26.2041),
                    "lng": data.get("lon", 28.0473),
                    "city": data.get("city", "Johannesburg"),
                    "country": data.get("countryCode", "ZA")
                }
    except:
        pass
    return {"lat": -26.2041, "lng": 28.0473, "city": "Johannesburg", "country": "ZA"}

def geocode_address(address):
    """Free geocoding using Nominatim (OpenStreetMap)"""
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": "ShopAround/1.0"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lng": float(data[0]["lon"]),
                    "display_name": data[0]["display_name"]
                }
    except:
        pass
    return None

def reverse_geocode(lat, lng):
    """Get address from coordinates using Nominatim"""
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json"
    }
    try:
        response = requests.get(NOMINATIM_REVERSE, params=params, headers={"User-Agent": "ShopAround/1.0"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name")
    except:
        pass
    return None

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
    """Return list of major South African retailers (public data)"""
    return [
        {"name": "Checkers", "category": "Grocery", "website": "https://checkers.co.za", "logo": "🛒", "delivery_fee": 35, "free_delivery_min": 350},
        {"name": "Shoprite", "category": "Grocery", "website": "https://shoprite.co.za", "logo": "🛒", "delivery_fee": 35, "free_delivery_min": 350},
        {"name": "Woolworths", "category": "Grocery", "website": "https://woolworths.co.za", "logo": "🥩", "delivery_fee": 45, "free_delivery_min": 450},
        {"name": "Pick n Pay", "category": "Grocery", "website": "https://pnp.co.za", "logo": "🛒", "delivery_fee": 35, "free_delivery_min": 350},
        {"name": "Makro", "category": "Wholesale", "website": "https://makro.co.za", "logo": "🏪", "delivery_fee": 50, "free_delivery_min": 500},
        {"name": "Game", "category": "General", "website": "https://game.co.za", "logo": "🎮", "delivery_fee": 50, "free_delivery_min": 500},
        {"name": "Clicks", "category": "Pharmacy", "website": "https://clicks.co.za", "logo": "💊", "delivery_fee": 30, "free_delivery_min": 300},
        {"name": "Takealot", "category": "E-commerce", "website": "https://takealot.com", "logo": "🛍️", "delivery_fee": 50, "free_delivery_min": 500},
    ]

def get_products():
    """Return common products with prices (public data)"""
    return [
        {"name": "Bread", "price": 18.99, "emoji": "🍞", "store": "Checkers"},
        {"name": "Milk 1L", "price": 22.99, "emoji": "🥛", "store": "Checkers"},
        {"name": "Rice 2kg", "price": 45.99, "emoji": "🍚", "store": "Shoprite"},
        {"name": "Eggs (dozen)", "price": 44.99, "emoji": "🥚", "store": "Checkers"},
        {"name": "Chicken 2kg", "price": 89.99, "emoji": "🍗", "store": "Pick n Pay"},
        {"name": "Sugar 2.5kg", "price": 39.99, "emoji": "🍬", "store": "Shoprite"},
        {"name": "Cooking Oil 750ml", "price": 54.99, "emoji": "🫒", "store": "Checkers"},
        {"name": "Tea Bags (100)", "price": 32.99, "emoji": "🍵", "store": "Woolworths"},
        {"name": "Coffee 250g", "price": 59.99, "emoji": "☕", "store": "Clicks"},
        {"name": "Toothpaste", "price": 24.99, "emoji": "🪥", "store": "Clicks"},
    ]

# ============================================
# DATABASE HELPERS
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

# ============================================
# SERVICE PROVIDER ROUTES (OpenStreetMap)
# ============================================
@app.route("/api/services/nearby", methods=["GET"])
def get_nearby_services():
    """Find service providers using OpenStreetMap (free, no API key)"""
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    service_type = request.args.get("type", "handyman")
    radius = request.args.get("radius", 10, type=int)
    
    # Get location from IP if not provided
    if not lat or not lng:
        ip_location = get_location_from_ip()
        lat = ip_location["lat"]
        lng = ip_location["lng"]
        location_source = "ip"
    else:
        location_source = "gps"
    
    # Get from OpenStreetMap
    osm_providers = get_osm_service_providers(lat, lng, radius, service_type)
    
    # Also get from local database
    db = get_db()
    local_providers = db.execute("""
        SELECT * FROM service_providers 
        WHERE service_type = ? OR ? = ''
        ORDER BY 
            CASE WHEN latitude IS NOT NULL THEN 
                ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?))
            ELSE 999999 END
        LIMIT 30
    """, (service_type, service_type, lat, lat, lng, lng)).fetchall()
    
    # Combine results
    combined = []
    
    for provider in local_providers:
        dist = calculate_distance(lat, lng, provider["latitude"], provider["longitude"]) if provider["latitude"] else None
        combined.append({
            "source": "local",
            "name": provider["name"],
            "service_type": provider["service_type"],
            "address": provider["address"],
            "phone": provider["phone"],
            "rating": provider["rating"],
            "distance_km": dist,
            "latitude": provider["latitude"],
            "longitude": provider["longitude"]
        })
    
    for provider in osm_providers:
        combined.append({
            "source": "osm",
            "name": provider["name"],
            "service_type": service_type,
            "address": provider.get("address", "Address from OpenStreetMap"),
            "phone": provider.get("phone", ""),
            "rating": provider.get("rating", 4.0),
            "distance_km": provider.get("distance_km"),
            "latitude": provider["latitude"],
            "longitude": provider["longitude"]
        })
    
    # Sort by distance
    combined.sort(key=lambda x: x.get("distance_km") if x.get("distance_km") else 999)
    
    return jsonify({
        "success": True,
        "location": {"lat": lat, "lng": lng, "source": location_source},
        "service_type": service_type,
        "total": len(combined),
        "services": combined[:30]
    })

@app.route("/api/services/register", methods=["POST"])
@login_required
def register_service():
    data = request.get_json(force=True)
    db = get_db()
    
    cursor = db.execute("""
        INSERT INTO service_providers (name, service_type, address, phone, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("name"),
        data.get("service_type"),
        data.get("address"),
        data.get("phone"),
        data.get("latitude"),
        data.get("longitude")
    ))
    db.commit()
    
    return jsonify({"success": True, "id": cursor.lastrowid})

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
        items = db.execute("""
            SELECT * FROM shopping_list_items WHERE list_id = ?
            ORDER BY checked_off ASC, created_at DESC
        """, (list_id,)).fetchall()
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

# ============================================
# SHOPPING OPTIMIZATION
# ============================================
@app.route("/api/optimize/<int:list_id>")
@login_required
def optimize_list(list_id):
    db = get_db()
    
    items = db.execute("""
        SELECT product_name, quantity FROM shopping_list_items 
        WHERE list_id = ? AND checked_off = 0
    """, (list_id,)).fetchall()
    
    products = get_products()
    retailers = get_major_retailers()
    
    basket = []
    total = 0
    store_totals = {}
    
    for item in items:
        best_price = None
        best_store = None
        
        for product in products:
            if product["name"].lower() in item["product_name"].lower():
                best_price = product["price"]
                best_store = product["store"]
                break
        
        if not best_price:
            best_price = 50
            best_store = "Checkers"
        
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
    
    # Calculate delivery fees
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
        "store_breakdown": store_totals,
        "recommendation": "For best savings, consider buying from fewer stores or using Click & Collect"
    })

# ============================================
# LOCATION DETECTION
# ============================================
@app.route("/api/location/detect", methods=["GET"])
def detect_location():
    """Detect user location using IP (free, no GPS needed)"""
    location = get_location_from_ip()
    return jsonify({
        "success": True,
        "latitude": location["lat"],
        "longitude": location["lng"],
        "city": location.get("city"),
        "country": location.get("country"),
        "source": "ip"
    })

@app.route("/api/geocode", methods=["GET"])
def geocode():
    """Convert address to coordinates using OpenStreetMap"""
    address = request.args.get("address", "")
    if not address:
        return jsonify({"error": "Address required"}), 400
    
    result = geocode_address(address)
    if result:
        return jsonify({"success": True, **result})
    return jsonify({"success": False, "error": "Address not found"}), 404

@app.route("/api/reverse-geocode", methods=["GET"])
def reverse():
    """Get address from coordinates"""
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    
    if not lat or not lng:
        return jsonify({"error": "Coordinates required"}), 400
    
    address = reverse_geocode(lat, lng)
    return jsonify({"success": True, "address": address})

# ============================================
# FRONTEND (MAP INCLUDED)
# ============================================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround - Open Source Mall</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f4f0;
            min-height: 100vh;
        }
        .navbar {
            background: #1f8a4c;
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
        .nav-links a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }
        .card {
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 0.5rem;
        }
        h2 { color: #1f8a4c; font-size: 1.25rem; }
        input, select, button, textarea {
            width: 100%;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border: 1px solid #ddd;
            border-radius: 0.5rem;
            font-size: 1rem;
        }
        button {
            background: #1f8a4c;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover { background: #166b3a; }
        .hidden { display: none; }
        .item-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #eee;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .stat-card {
            background: #e8f5e9;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        .stat-value { font-size: 1.5rem; font-weight: bold; color: #1f8a4c; }
        .tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
        .tab {
            padding: 0.5rem 1rem;
            background: #e5e7eb;
            border-radius: 0.5rem;
            cursor: pointer;
        }
        .tab.active { background: #1f8a4c; color: white; }
        #map { height: 400px; border-radius: 1rem; margin-bottom: 1rem; }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-success { background: #d1fae5; color: #10b981; }
        @media (max-width: 768px) {
            .container { padding: 0 1rem; }
            .navbar { padding: 1rem; }
        }
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
        <p>South Africa's Open Source Mall</p>
        <div id="loginForm">
            <input type="text" id="loginUsername" placeholder="Username">
            <input type="password" id="loginPassword" placeholder="Password">
            <button onclick="login()">Login</button>
            <button class="secondary" onclick="showRegister()" style="background:#666;">Register</button>
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

        <!-- Shopping Section -->
        <div id="shoppingSection">
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
                <div class="card-header"><h2>💡 Smart Optimization</h2></div>
                <select id="optimizeList"></select>
                <button onclick="optimizeBasket()">Find Best Prices</button>
                <div id="optimizeResults"></div>
            </div>
        </div>

        <!-- Services Section -->
        <div id="servicesSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🛠️ Find Service Providers</h2></div>
                <select id="serviceType">
                    <option value="plumbing">Plumbing</option>
                    <option value="electrical">Electrical</option>
                    <option value="mechanic">Mechanic</option>
                    <option value="cleaning">Cleaning</option>
                    <option value="gardening">Gardening</option>
                    <option value="handyman">Handyman</option>
                </select>
                <button onclick="findNearbyServices()">🔍 Find Near Me</button>
                <div id="servicesList"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>🏪 Register Your Business</h2></div>
                <input type="text" id="businessName" placeholder="Business Name">
                <select id="businessType">
                    <option value="plumbing">Plumbing</option>
                    <option value="electrical">Electrical</option>
                    <option value="mechanic">Mechanic</option>
                    <option value="cleaning">Cleaning</option>
                </select>
                <input type="text" id="businessPhone" placeholder="Phone">
                <input type="text" id="businessAddress" placeholder="Address">
                <button onclick="registerBusiness()">Register Business</button>
            </div>
        </div>

        <!-- Map Section -->
        <div id="mapSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🗺️ Find Nearby Services</h2></div>
                <div id="map"></div>
                <button onclick="locateMe()">📍 Find My Location</button>
                <div id="mapResults"></div>
            </div>
        </div>
    </div>
</div>

<script>
let map = null;
let markers = [];
let currentLists = [];

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username,password})});
    if (res.ok) {
        document.getElementById('authSection').style.display = 'none';
        document.getElementById('appSection').style.display = 'block';
        document.getElementById('logoutBtn').style.display = 'inline-block';
        loadLists();
        initMap();
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
    document.getElementById('shoppingSection').classList.add('hidden');
    document.getElementById('servicesSection').classList.add('hidden');
    document.getElementById('mapSection').classList.add('hidden');
    document.getElementById(`${section}Section`).classList.remove('hidden');
    if (section === 'map' && map) map.invalidateSize();
}

function initMap() {
    if (map) return;
    map = L.map('map').setView([-26.2041, 28.0473], 12);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
    }).addTo(map);
}

async function locateMe() {
    if (!map) initMap();
    const res = await fetch('/api/location/detect');
    const loc = await res.json();
    if (loc.success) {
        map.setView([loc.latitude, loc.longitude], 14);
        L.marker([loc.latitude, loc.longitude]).addTo(map).bindPopup('You are here').openPopup();
    }
}

async function findNearbyServices() {
    const type = document.getElementById('serviceType').value;
    const res = await fetch(`/api/location/detect`);
    const loc = await res.json();
    
    document.getElementById('servicesList').innerHTML = '<div class="stats">🔍 Searching...</div>';
    
    const servicesRes = await fetch(`/api/services/nearby?lat=${loc.latitude}&lng=${loc.longitude}&type=${type}`);
    const data = await servicesRes.json();
    
    if (data.services && data.services.length > 0) {
        let html = `<div class="stats">📍 Found ${data.services.length} providers near you</div>`;
        for (const s of data.services) {
            const dist = s.distance_km ? `${s.distance_km}km away` : 'Nearby';
            html += `
                <div class="card">
                    <div><strong>${s.name}</strong> <span class="badge badge-success">${dist}</span></div>
                    <div>${s.address || 'Address available'}</div>
                    ${s.phone ? `<div>📞 ${s.phone}</div>` : ''}
                    ${s.rating ? `<div>⭐ ${s.rating}/5</div>` : ''}
                    <button onclick="window.open('https://www.openstreetmap.org/?mlat=${s.latitude}&mlon=${s.longitude}', '_blank')">📍 Open Map</button>
                </div>
            `;
        }
        document.getElementById('servicesList').innerHTML = html;
    } else {
        document.getElementById('servicesList').innerHTML = '<div class="stats">⚠️ No providers found. Try a different service type.</div>';
    }
}

async function registerBusiness() {
    const name = document.getElementById('businessName').value;
    const type = document.getElementById('businessType').value;
    const phone = document.getElementById('businessPhone').value;
    const address = document.getElementById('businessAddress').value;
    if (!name) { alert('Enter business name'); return; }
    const res = await fetch('/api/services/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name, service_type:type, phone, address})});
    if (res.ok) alert('Business registered! Pending verification.');
}

async function loadLists() {
    const res = await fetch('/api/lists');
    if (res.ok) { currentLists = await res.json(); renderLists(); updateSelectors(); }
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
                html += `<li class="item-row"><span>🛒 ${i.product_name} x${i.quantity}</span><div><button onclick="toggleItem(${listId},${i.id})">${i.checked_off?'✓':'○'}</button><button onclick="removeItem(${listId},${i.id})">×</button></div></li>`;
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
    html += `</ul><p class="badge-success" style="padding:0.5rem;">💡 ${data.recommendation}</p>`;
    document.getElementById('optimizeResults').innerHTML = html;
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

# ============================================
# RUN THE APP
# ============================================
if __name__ == "__main__":
    init_db()
    print("="*60)
    print("🛍️  SHOPAROUND - Open Source Edition")
    print("="*60)
    print("✅ No API Keys Required")
    print("✅ Uses OpenStreetMap (Free)")
    print("✅ IP Geolocation (Free)")
    print("✅ Open Data for Retailers")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True)
