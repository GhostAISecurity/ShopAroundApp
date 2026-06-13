#!/usr/bin/env python3
"""
SHOPAROUND - COMPLETE ONLINE MALL
=================================
Everything in one place: Retailers, Services, Pharmacy, Deliveries, Spaza Shops, Neural AI
Every user has their own account with access to ALL features
"""

import sqlite3
import os
import json
import secrets
import math
import requests
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ====================================================
# NEURAL BRAIN - SEDIBA GHOST OMNIVERSAL MIND
# ====================================================

@dataclass(frozen=True)
class Kernel:
    name: str = "SEDIBA GHOST OMNIVERSAL NEURAL MIND"
    version: str = "3.0.0"
    founder: str = "Lukie Sediba"
    created: str = field(default_factory=lambda: datetime.now().isoformat())

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
        event = {"id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(), "context": context, "evaluations": evaluations, "verdict": decision["verdict"], "approval_score": decision["approval_score"]}
        self.memory.remember(event)
        return event
    
    def get_status(self):
        return {"kernel": {"name": self.kernel.name, "version": self.kernel.version}, "agents": [a.name for a in self.agents]}

# Initialize Neural Brain
neural_brain = GhostBrain()

# ====================================================
# FLASK APP
# ====================================================

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound.db")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)

# ====================================================
# COMPLETE DATABASE - EVERYTHING
# ====================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        -- USERS TABLE
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
            name TEXT,
            business_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        );
        
        -- RETAILERS (All major online shops)
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
        );
        
        -- DELIVERY SERVICES
        CREATE TABLE IF NOT EXISTS delivery_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            service_type TEXT,
            base_fee REAL,
            per_km_rate REAL,
            website TEXT,
            logo TEXT,
            rating REAL DEFAULT 4.0
        );
        
        -- PHARMACIES
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
        );
        
        -- SPAZA SHOPS (Informal Economy)
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
        );
        
        -- SERVICE PROVIDERS (Plumbers, Electricians, etc.)
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
        );
        
        -- PRODUCTS CATALOG
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
        );
        
        -- SHOPPING LISTS
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT DEFAULT 'My List',
            total_budget REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- SHOPPING LIST ITEMS
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
        );
        
        -- COMMUNITY PRICES
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
        );
        
        -- PRICE ALERTS
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            target_price REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- ORDERS HISTORY
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
        );
        
        -- ORDER ITEMS
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity REAL,
            price_at_time REAL
        );
        
        -- BUSINESS ACCOUNTS
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            name TEXT NOT NULL,
            business_type TEXT,
            registration_number TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- INDEXES
        CREATE INDEX IF NOT EXISTS idx_services_location ON service_providers(latitude, longitude);
        CREATE INDEX IF NOT EXISTS idx_spaza_location ON spaza_shops(latitude, longitude);
        CREATE INDEX IF NOT EXISTS idx_pharmacy_location ON pharmacies(latitude, longitude);
    """)
    
    cursor = conn.cursor()
    
    # ====================================================
    # SEED ALL RETAILERS (Everything online in SA)
    # ====================================================
    retailers = [
        # Grocery
        ("Checkers", "Grocery", "Supermarket", "https://checkers.co.za", "🛒", 35, 350, 60, 4.2),
        ("Shoprite", "Grocery", "Supermarket", "https://shoprite.co.za", "🛒", 35, 350, 60, 4.1),
        ("Woolworths", "Grocery", "Premium", "https://woolworths.co.za", "🥩", 45, 450, 60, 4.5),
        ("Pick n Pay", "Grocery", "Supermarket", "https://pnp.co.za", "🛒", 35, 350, 60, 4.2),
        ("Spar", "Grocery", "Supermarket", "https://spar.co.za", "🛒", 35, 350, 60, 4.0),
        ("Food Lovers Market", "Grocery", "Fresh Produce", "https://foodloversmarket.co.za", "🥬", 30, 300, 45, 4.3),
        
        # E-commerce
        ("Takealot", "E-commerce", "General", "https://takealot.com", "🛍️", 50, 500, 120, 4.4),
        ("Makro", "E-commerce", "Wholesale", "https://makro.co.za", "🏪", 50, 500, 90, 4.0),
        ("Game", "E-commerce", "General", "https://game.co.za", "🎮", 50, 500, 90, 3.9),
        
        # Electronics
        ("Incredible Connection", "Electronics", "Tech", "https://incredible.co.za", "💻", 60, 600, 90, 4.1),
        ("HiFi Corp", "Electronics", "Audio/Tech", "https://hificorp.co.za", "🎧", 60, 600, 90, 4.0),
        ("Vodacom", "Electronics", "Mobile", "https://vodacom.co.za", "📱", 40, 400, 60, 4.2),
        ("MTN", "Electronics", "Mobile", "https://mtn.co.za", "📱", 40, 400, 60, 4.1),
        
        # Fashion
        ("Zando", "Fashion", "Clothing", "https://zando.co.za", "👕", 50, 500, 90, 4.3),
        ("Superbalist", "Fashion", "Clothing", "https://superbalist.com", "👗", 50, 500, 90, 4.4),
        ("Bash", "Fashion", "Clothing", "https://bash.com", "👔", 50, 500, 90, 4.2),
        
        # Home & Hardware
        ("Builders", "Hardware", "DIY", "https://builders.co.za", "🔨", 60, 600, 120, 4.0),
        ("BUCO", "Hardware", "Building", "https://buco.co.za", "🏗️", 60, 600, 120, 3.9),
        ("Leroy Merlin", "Hardware", "DIY", "https://leroymerlin.co.za", "🔧", 60, 600, 120, 4.1),
        
        # Pharmacy
        ("Clicks", "Pharmacy", "Health", "https://clicks.co.za", "💊", 30, 300, 60, 4.3),
        ("Dischem", "Pharmacy", "Health", "https://dischem.co.za", "💊", 30, 300, 60, 4.2),
        
        # Pet
        ("Pet Heaven", "Pet", "Supplies", "https://petheaven.co.za", "🐕", 50, 500, 90, 4.0),
        ("Absolute Pets", "Pet", "Supplies", "https://absolutepets.co.za", "🐈", 50, 500, 90, 4.1),
        
        # Baby & Toddler
        ("Baby City", "Baby", "Toddler", "https://babycity.co.za", "👶", 50, 500, 90, 4.2),
        ("Baby Boom", "Baby", "Toddler", "https://babyboom.co.za", "🍼", 50, 500, 90, 4.1),
        
        # Auto
        ("AutoTrader", "Auto", "Cars", "https://autotrader.co.za", "🚗", 0, 0, 0, 4.3),
        ("WeBuyCars", "Auto", "Cars", "https://webuycars.co.za", "🚙", 0, 0, 0, 4.1),
        ("Cars.co.za", "Auto", "Cars", "https://cars.co.za", "🚘", 0, 0, 0, 4.2),
        
        # Furniture
        ("Decofurn", "Furniture", "Home", "https://decofurn.co.za", "🛋️", 60, 600, 120, 4.1),
        ("Coricraft", "Furniture", "Home", "https://coricraft.co.za", "🪑", 70, 700, 120, 4.3),
        ("Mr Price Home", "Furniture", "Home", "https://mrpricehome.co.za", "🏠", 50, 500, 90, 4.0),
        
        # Sports & Outdoor
        ("Sportsmans Warehouse", "Sports", "Outdoor", "https://sportsmanswarehouse.co.za", "🏃", 50, 500, 90, 4.2),
        ("Totalsports", "Sports", "Apparel", "https://totalsports.co.za", "⚽", 50, 500, 90, 4.1),
        
        # Books & Stationery
        ("Exclusive Books", "Books", "Stationery", "https://exclusivebooks.co.za", "📚", 40, 400, 60, 4.3),
        ("CNA", "Books", "Stationery", "https://cna.co.za", "✏️", 40, 400, 60, 4.0),
    ]
    cursor.executemany("INSERT OR IGNORE INTO retailers (name, category, subcategory, website, logo, delivery_fee, free_delivery_min, delivery_minutes, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", retailers)
    
    # ====================================================
    # SEED DELIVERY SERVICES
    # ====================================================
    delivery_services = [
        ("Uber Eats", "Food", 10, 5, "https://ubereats.com", "🚗", 4.3),
        ("Mr D Food", "Food", 10, 4, "https://mrdfood.com", "🍔", 4.2),
        ("Bolt Food", "Food", 8, 4, "https://boltfood.com", "⚡", 4.1),
        ("Pargo", "Parcel", 25, 3, "https://pargo.co.za", "📦", 4.0),
        ("The Courier Guy", "Parcel", 35, 2, "https://thecourierguy.co.za", "📫", 4.1),
    ]
    cursor.executemany("INSERT OR IGNORE INTO delivery_services (name, service_type, base_fee, per_km_rate, website, logo, rating) VALUES (?, ?, ?, ?, ?, ?, ?)", delivery_services)
    
    # ====================================================
    # SEED PHARMACIES
    # ====================================================
    pharmacies = [
        ("Clicks Pharmacy Sandton", "Sandton City", -26.107, 28.055, "011 123 4567", 1, 30, 4.3),
        ("Dischem Sandton", "Sandton", -26.108, 28.056, "011 123 4568", 1, 30, 4.2),
        ("Clicks Menlyn", "Menlyn", -25.780, 28.275, "012 123 4567", 1, 30, 4.3),
        ("Dischem Menlyn", "Menlyn", -25.781, 28.276, "012 123 4568", 1, 30, 4.2),
        ("Medirite Plus", "Pretoria", -25.746, 28.188, "012 123 4569", 1, 25, 4.0),
    ]
    cursor.executemany("INSERT OR IGNORE INTO pharmacies (name, address, latitude, longitude, phone, delivery_available, delivery_fee, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", pharmacies)
    
    # ====================================================
    # SEED SERVICE PROVIDERS
    # ====================================================
    services = [
        ("Plumbmaster SA", "plumbing", "24/7 Emergency Plumbing", 450, "011 123 4567", -26.2041, 28.0473, "Johannesburg", 4.2),
        ("JHB Electricians", "electrical", "Certified Electricians", 400, "011 234 5678", -26.2025, 28.0450, "Johannesburg", 4.5),
        ("Auto Care Centre", "mechanic", "Car Repairs & Services", 550, "011 345 6789", -26.2080, 28.0500, "Johannesburg", 4.0),
        ("Rapid Locksmiths", "locksmith", "Lock Installation & Repair", 350, "011 456 7890", -26.2000, 28.0400, "Johannesburg", 4.3),
        ("Clean Sweep", "cleaning", "Professional Cleaning", 250, "011 567 8901", -26.2100, 28.0550, "Johannesburg", 4.4),
        ("Green Thumb", "gardening", "Garden Services", 300, "011 678 9012", -26.1950, 28.0450, "Johannesburg", 4.3),
        ("Tutor Connect", "tutoring", "All Subjects", 200, "011 789 0123", -26.2150, 28.0600, "Johannesburg", 4.5),
        ("Pest Control Pro", "pest_control", "Pest Extermination", 500, "011 890 1234", -26.2050, 28.0480, "Johannesburg", 4.2),
        ("Paint Masters", "painting", "House Painting", 400, "011 901 2345", -26.2000, 28.0420, "Johannesburg", 4.1),
        ("Roof Fix SA", "roofing", "Roof Repairs", 600, "011 012 3456", -26.2090, 28.0520, "Johannesburg", 4.0),
        ("Appliance Repair", "appliance", "Fix appliances", 350, "011 123 4560", -26.2070, 28.0490, "Johannesburg", 4.3),
        ("Moving Men", "moving", "Furniture Moving", 800, "011 234 5670", -26.2010, 28.0440, "Johannesburg", 4.2),
    ]
    cursor.executemany("INSERT OR IGNORE INTO service_providers (name, service_type, description, hourly_rate, phone, latitude, longitude, address, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", services)
    
    # ====================================================
    # SEED PRODUCTS
    # ====================================================
    products = [
        ("Bread", "Albany", "Grocery", "Bakery", None, "🍞", 18.99, "loaf"),
        ("Milk 1L", "Clover", "Grocery", "Dairy", None, "🥛", 22.99, "liter"),
        ("Rice 2kg", "Tastic", "Grocery", "Pantry", None, "🍚", 45.99, "kg"),
        ("Eggs (dozen)", "Nulaid", "Grocery", "Dairy", None, "🥚", 44.99, "dozen"),
        ("Chicken 2kg", "Irvine's", "Grocery", "Meat", None, "🍗", 89.99, "kg"),
        ("Sugar 2.5kg", "Ilovo", "Grocery", "Pantry", None, "🍬", 39.99, "kg"),
        ("Cooking Oil 750ml", "Sunfoil", "Grocery", "Pantry", None, "🫒", 54.99, "bottle"),
        ("Toothpaste", "Colgate", "Health", "Oral Care", None, "🪥", 24.99, "tube"),
        ("Shampoo", "Dove", "Health", "Hair", None, "💇", 89.99, "bottle"),
        ("Laundry Detergent", "OMO", "Home", "Cleaning", None, "🧺", 129.99, "kg"),
        ("Dishwashing Liquid", "Sunlight", "Home", "Cleaning", None, "🧼", 35.99, "bottle"),
        ("Coffee 250g", "Jacobs", "Beverage", "Hot Drinks", None, "☕", 59.99, "jar"),
        ("Tea Bags 100", "Five Roses", "Beverage", "Hot Drinks", None, "🍵", 32.99, "box"),
        ("Frozen Chicken", "Irvine's", "Frozen", "Meat", None, "🍗", 79.99, "kg"),
        ("Fish Fillets", "Sea Harvest", "Frozen", "Seafood", None, "🐟", 89.99, "kg"),
        ("Ice Cream", "Ola", "Frozen", "Dessert", None, "🍦", 59.99, "litre"),
        ("Diapers", "Pampers", "Baby", "Nappies", None, "👶", 189.99, "pack"),
        ("Baby Formula", "Aptamil", "Baby", "Food", None, "🍼", 249.99, "tin"),
        ("Car Oil", "Shell", "Auto", "Maintenance", None, "🛢️", 129.99, "litre"),
        ("Car Battery", "Willard", "Auto", "Parts", None, "🔋", 1299.99, "unit"),
        ("Smartphone", "Samsung", "Electronics", "Phones", None, "📱", 4999.99, "unit"),
        ("Laptop", "HP", "Electronics", "Computers", None, "💻", 8999.99, "unit"),
        ("TV 55\"", "Samsung", "Electronics", "TVs", None, "📺", 8999.99, "unit"),
        ("Headphones", "Sony", "Electronics", "Audio", None, "🎧", 899.99, "unit"),
        ("Sofa", "Coricraft", "Furniture", "Living", None, "🛋️", 4999.99, "unit"),
        ("Bed", "Bed Shop", "Furniture", "Bedroom", None, "🛏️", 3999.99, "unit"),
        ("Dog Food", "Montego", "Pet", "Food", None, "🐕", 189.99, "kg"),
        ("Cat Food", "Whiskas", "Pet", "Food", None, "🐈", 89.99, "kg"),
        ("Paint", "Dulux", "Hardware", "Paint", None, "🎨", 299.99, "litre"),
        ("Tools Set", "Stanley", "Hardware", "Tools", None, "🔧", 999.99, "set"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO products (product_name, brand, category, subcategory, barcode, emoji, typical_price, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", products)
    
    conn.commit()
    conn.close()
    print("✅ Complete database initialized with ALL retailers, services, pharmacies, and products")

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
# AUTHENTICATION ROUTES
# ====================================================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    is_business = data.get("is_business", 0)
    name = data.get("name", "")
    business_type = data.get("business_type", "")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    db = get_db()
    try:
        db.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, generate_password_hash(password), is_business, name, business_type))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409
    
    return jsonify({"success": True, "message": "User created successfully"})

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
    
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "is_business": user["is_business"],
        "name": user["name"]
    })

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/me", methods=["GET"])
@login_required
def get_current_user():
    db = get_db()
    user = db.execute("SELECT id, username, email, full_name, phone, address, household_size, monthly_budget, is_business, name FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    return jsonify(dict(user))

# ====================================================
# RETAILER ROUTES
# ====================================================
@app.route("/api/retailers", methods=["GET"])
def get_retailers():
    category = request.args.get("category", "")
    db = get_db()
    if category:
        retailers = db.execute("SELECT * FROM retailers WHERE category = ? AND is_active = 1 ORDER BY rating DESC", (category,)).fetchall()
    else:
        retailers = db.execute("SELECT * FROM retailers WHERE is_active = 1 ORDER BY category, rating DESC").fetchall()
    return jsonify([dict(r) for r in retailers])

@app.route("/api/retailers/categories", methods=["GET"])
def get_retailer_categories():
    db = get_db()
    categories = db.execute("SELECT DISTINCT category FROM retailers ORDER BY category").fetchall()
    return jsonify([c["category"] for c in categories])

# ====================================================
# DELIVERY SERVICES ROUTES
# ====================================================
@app.route("/api/delivery-services", methods=["GET"])
def get_delivery_services():
    db = get_db()
    services = db.execute("SELECT * FROM delivery_services ORDER BY rating DESC").fetchall()
    return jsonify([dict(s) for s in services])

# ====================================================
# PHARMACY ROUTES
# ====================================================
@app.route("/api/pharmacies", methods=["GET"])
def get_pharmacies():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    db = get_db()
    pharmacies = db.execute("SELECT * FROM pharmacies WHERE delivery_available = 1").fetchall()
    
    result = []
    for p in pharmacies:
        dist = None
        if lat and lng and p["latitude"]:
            dist = round(math.sqrt((p["latitude"] - lat)**2 + (p["longitude"] - lng)**2) * 111, 1)
        result.append({"id": p["id"], "name": p["name"], "address": p["address"], "phone": p["phone"], "delivery_fee": p["delivery_fee"], "rating": p["rating"], "distance_km": dist})
    result.sort(key=lambda x: x.get("distance_km") or 999)
    return jsonify({"pharmacies": result[:20]})

# ====================================================
# SERVICE PROVIDER ROUTES
# ====================================================
@app.route("/api/services", methods=["GET"])
def get_services():
    service_type = request.args.get("type", "")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    db = get_db()
    
    query = "SELECT * FROM service_providers WHERE verified = 1"
    params = []
    if service_type:
        query += " AND service_type = ?"
        params.append(service_type)
    
    providers = db.execute(query, params).fetchall()
    result = []
    for p in providers:
        dist = None
        if lat and lng and p["latitude"]:
            dist = round(math.sqrt((p["latitude"] - lat)**2 + (p["longitude"] - lng)**2) * 111, 1)
        result.append({
            "id": p["id"], "name": p["name"], "service_type": p["service_type"],
            "description": p["description"], "hourly_rate": p["hourly_rate"], "phone": p["phone"],
            "address": p["address"], "rating": p["rating"], "distance_km": dist
        })
    result.sort(key=lambda x: x.get("distance_km") or 999)
    return jsonify({"services": result[:30]})

@app.route("/api/services/register", methods=["POST"])
@login_required
def register_service():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO service_providers (user_id, name, service_type, description, hourly_rate, phone, latitude, longitude, address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session["user_id"], data.get("name"), data.get("service_type"), 
          data.get("description"), data.get("hourly_rate"), data.get("phone"),
          data.get("latitude"), data.get("longitude"), data.get("address")))
    db.commit()
    return jsonify({"success": True, "id": cursor.lastrowid, "message": "Service provider registered! Pending verification."})

# ====================================================
# SPAZA SHOP ROUTES
# ====================================================
@app.route("/api/spaza", methods=["GET"])
def get_spaza():
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    db = get_db()
    shops = db.execute("SELECT * FROM spaza_shops WHERE verified = 1 LIMIT 100").fetchall()
    result = []
    for s in shops:
        dist = None
        if lat and lng and s["latitude"]:
            dist = round(math.sqrt((s["latitude"] - lat)**2 + (s["longitude"] - lng)**2) * 111, 1)
        result.append({"id": s["id"], "shop_name": s["shop_name"], "address": s["address"], "phone": s["phone"], "rating": s["rating"], "distance_km": dist})
    result.sort(key=lambda x: x.get("distance_km") or 999)
    return jsonify({"spaza_shops": result[:30]})

@app.route("/api/spaza/register", methods=["POST"])
@login_required
def register_spaza():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO spaza_shops (owner_id, shop_name, address, latitude, longitude, phone, whatsapp, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session["user_id"], data.get("shop_name"), data.get("address"), 
          data.get("latitude"), data.get("longitude"), data.get("phone"), 
          data.get("whatsapp"), data.get("category", "General")))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "message": "Spaza shop registered! Awaiting verification."})

# ====================================================
# BUSINESS REGISTRATION
# ====================================================
@app.route("/api/business/register", methods=["POST"])
@login_required
def register_business():
    data = request.get_json(force=True)
    db = get_db()
    cursor = db.execute("""
        INSERT INTO businesses (owner_id, name, business_type, registration_number, address, phone, email, website)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session["user_id"], data.get("name"), data.get("business_type"),
          data.get("registration_number"), data.get("address"), data.get("phone"),
          data.get("email"), data.get("website")))
    db.commit()
    db.execute("UPDATE users SET is_business = 1, name = ?, business_type = ? WHERE id = ?", 
               (data.get("name"), data.get("business_type"), session["user_id"]))
    db.commit()
    return jsonify({"id": cursor.lastrowid, "message": "Business registered! Awaiting verification."})

# ====================================================
# PRODUCT ROUTES
# ====================================================
@app.route("/api/products", methods=["GET"])
def get_products():
    category = request.args.get("category", "")
    search = request.args.get("search", "")
    db = get_db()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND product_name LIKE ?"
        params.append(f"%{search}%")
    products = db.execute(query, params).fetchall()
    return jsonify([dict(p) for p in products])

@app.route("/api/products/categories", methods=["GET"])
def get_product_categories():
    db = get_db()
    categories = db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    return jsonify([c["category"] for c in categories])

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
        cursor = db.execute("INSERT INTO shopping_lists (user_id, name, total_budget) VALUES (?, ?, ?)", 
                           (session["user_id"], data.get("name", "My List"), data.get("budget", 0)))
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
            SELECT sli.*, p.emoji, p.typical_price
            FROM shopping_list_items sli
            LEFT JOIN products p ON p.id = sli.product_id
            WHERE sli.list_id = ?
            ORDER BY sli.priority DESC, sli.created_at DESC
        """, (list_id,)).fetchall()
        return jsonify([dict(i) for i in items])
    else:
        data = request.get_json(force=True)
        product_name = data.get("product_name")
        product = db.execute("SELECT id FROM products WHERE product_name LIKE ?", (f"%{product_name}%",)).fetchone()
        product_id = product["id"] if product else None
        db.execute("""
            INSERT INTO shopping_list_items (list_id, product_id, product_name, quantity, priority, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (list_id, product_id, product_name, data.get("quantity", 1), data.get("priority", 1), data.get("notes", "")))
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
# SHOPPING OPTIMIZATION
# ====================================================
@app.route("/api/optimize/<int:list_id>")
@login_required
def optimize_list(list_id):
    db = get_db()
    items = db.execute("SELECT product_name, quantity FROM shopping_list_items WHERE list_id = ? AND checked_off = 0", (list_id,)).fetchall()
    retailers = db.execute("SELECT name, delivery_fee, free_delivery_min FROM retailers WHERE is_active = 1").fetchall()
    products = db.execute("SELECT product_name, typical_price FROM products").fetchall()
    
    basket = []
    total = 0
    store_totals = {}
    
    for item in items:
        best_price = 50
        best_store = "Checkers"
        for p in products:
            if p["product_name"].lower() in item["product_name"].lower():
                best_price = p["typical_price"] or 50
                break
        item_total = best_price * item["quantity"]
        total += item_total
        store_totals[best_store] = store_totals.get(best_store, 0) + item_total
        basket.append({"product": item["product_name"], "quantity": item["quantity"], "price": round(best_price, 2), "total": round(item_total, 2), "store": best_store})
    
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
        "recommendation": "💡 You can save by consolidating items to fewer stores or using store pickup"
    })

# ====================================================
# COMMUNITY PRICES
# ====================================================
@app.route("/api/community/price", methods=["POST"])
@login_required
def report_price():
    data = request.get_json(force=True)
    db = get_db()
    db.execute("""
        INSERT INTO community_prices (user_id, product_name, retailer_name, price, location, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session["user_id"], data.get("product_name"), data.get("retailer_name"),
          data.get("price"), data.get("location"), data.get("latitude"), data.get("longitude")))
    db.commit()
    avg = db.execute("SELECT AVG(price) as avg FROM community_prices WHERE product_name = ?", (data.get("product_name"),)).fetchone()
    return jsonify({"success": True, "message": "Price reported!", "average_price": round(avg["avg"], 2) if avg["avg"] else None})

@app.route("/api/community/trends/<product>", methods=["GET"])
def get_community_trends(product):
    db = get_db()
    trends = db.execute("""
        SELECT price, retailer_name, created_at, latitude, longitude
        FROM community_prices
        WHERE product_name LIKE ?
        ORDER BY created_at DESC
        LIMIT 30
    """, (f"%{product}%",)).fetchall()
    return jsonify([dict(t) for t in trends])

# ====================================================
# PRICE ALERTS
# ====================================================
@app.route("/api/alerts", methods=["GET", "POST"])
@login_required
def handle_alerts():
    db = get_db()
    if request.method == "GET":
        alerts = db.execute("""
            SELECT pa.*, p.emoji
            FROM price_alerts pa
            LEFT JOIN products p ON p.id = pa.product_id
            WHERE pa.user_id = ? AND pa.is_active = 1
            ORDER BY pa.created_at DESC
        """, (session["user_id"],)).fetchall()
        return jsonify([dict(a) for a in alerts])
    else:
        data = request.get_json(force=True)
        product_name = data.get("product_name")
        target_price = data.get("target_price")
        product = db.execute("SELECT id FROM products WHERE product_name LIKE ?", (f"%{product_name}%",)).fetchone()
        if not product:
            return jsonify({"error": "Product not found"}), 404
        db.execute("""
            INSERT INTO price_alerts (user_id, product_id, product_name, target_price)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], product["id"], product_name, target_price))
        db.commit()
        return jsonify({"success": True, "message": f"Alert set for {product_name} at R{target_price}"})

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
    context = {
        "objective": data.get("objective", "Business decision"),
        "risk_score": data.get("risk_score", 0.5),
        "amount": data.get("amount", 0),
        "strategic_alignment": data.get("strategic_alignment", 0.8)
    }
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
# LOCATION DETECTION
# ====================================================
@app.route("/api/location/detect", methods=["GET"])
def detect_location():
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return jsonify({"success": True, "latitude": data.get("lat", -26.2041), "longitude": data.get("lon", 28.0473), "city": data.get("city", "Johannesburg")})
    except: pass
    return jsonify({"success": True, "latitude": -26.2041, "longitude": 28.0473, "city": "Johannesburg"})

# ====================================================
# ANALYTICS
# ====================================================
@app.route("/api/analytics/spending", methods=["GET"])
@login_required
def get_spending_analytics():
    db = get_db()
    days = request.args.get("days", 30, type=int)
    orders = db.execute("""
        SELECT strftime('%Y-%m-%d', ordered_at) as date, SUM(total_amount) as daily_total
        FROM orders
        WHERE user_id = ? AND ordered_at > datetime('now', ?)
        GROUP BY date
        ORDER BY date DESC
    """, (session["user_id"], f"-{days} days")).fetchall()
    return jsonify({"daily_spending": [dict(o) for o in orders], "total": sum(o["daily_total"] for o in orders)})

# ====================================================
# COMPLETE FRONTEND - ALL FEATURES
# ====================================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround - Complete Online Mall</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;}
        .navbar{background:#1f8a4c;color:white;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;}
        .navbar h1{font-size:1.5rem;}
        .nav-links{display:flex;gap:1rem;flex-wrap:wrap;}
        .nav-links a{color:white;text-decoration:none;padding:0.5rem 1rem;border-radius:0.5rem;cursor:pointer;}
        .nav-links a:hover{background:rgba(255,255,255,0.2);}
        .container{max-width:1400px;margin:2rem auto;padding:0 2rem;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;border-bottom:2px solid #e0e0e0;padding-bottom:0.5rem;}
        h2{color:#1f8a4c;font-size:1.25rem;}
        h3{color:#333;margin-bottom:0.5rem;}
        input,select,button,textarea{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #ddd;border-radius:0.5rem;font-size:1rem;}
        button{background:#1f8a4c;color:white;border:none;cursor:pointer;font-weight:600;}
        button:hover{background:#166b3a;}
        button.secondary{background:#666;}
        .hidden{display:none;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem;}
        .item-row{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 0;border-bottom:1px solid #eee;}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:1rem;}
        .stat-card{background:#e8f5e9;padding:1rem;border-radius:0.5rem;text-align:center;}
        .stat-value{font-size:1.8rem;font-weight:bold;color:#1f8a4c;}
        .tabs{display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap;}
        .tab{padding:0.5rem 1rem;background:#e0e0e0;border-radius:0.5rem;cursor:pointer;}
        .tab.active{background:#1f8a4c;color:white;}
        .badge{display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;font-size:0.75rem;font-weight:600;}
        .badge-success{background:#d1fae5;color:#10b981;}
        .badge-warning{background:#fed7aa;color:#f59e0b;}
        .badge-info{background:#dbeafe;color:#3b82f6;}
        .retailer-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1rem;margin-top:1rem;}
        .retailer-card{background:#f8f9fa;padding:1rem;border-radius:0.5rem;text-align:center;cursor:pointer;transition:transform 0.2s;}
        .retailer-card:hover{transform:scale(1.05);background:#e8f5e9;}
        .retailer-logo{font-size:2rem;}
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
        <a onclick="showSection('spaza')">Spaza Shops</a>
        <a onclick="showSection('pharmacy')">Pharmacy</a>
        <a onclick="showSection('delivery')">Delivery</a>
        <a onclick="showSection('community')">Community</a>
        <a onclick="showSection('brain')">AI Brain</a>
        <a id="logoutBtn" style="display:none;" onclick="logout()">Logout</a>
    </div>
</div>

<div class="container">
    <!-- Auth Section -->
    <div id="authSection" class="card" style="max-width:500px; margin:2rem auto;">
        <h2>Welcome to ShopAround</h2>
        <p>South Africa's Complete Online Mall</p>
        <div id="loginForm">
            <input type="text" id="loginUsername" placeholder="Username">
            <input type="password" id="loginPassword" placeholder="Password">
            <button onclick="login()">Login</button>
            <button class="secondary" onclick="showRegister()">Register</button>
        </div>
        <div id="registerForm" style="display:none;">
            <input type="text" id="regUsername" placeholder="Username">
            <input type="email" id="regEmail" placeholder="Email">
            <input type="password" id="regPassword" placeholder="Password">
            <button onclick="register()">Register</button>
            <button onclick="showLogin()">Back</button>
        </div>
        <p id="authMessage" style="color:#ef4444; margin-top:1rem;"></p>
    </div>

    <!-- Main App -->
    <div id="appSection" style="display:none;">
        <div class="stats">
            <div class="stat-card"><div class="stat-value" id="userWelcome">-</div><div>Welcome</div></div>
            <div class="stat-card"><div class="stat-value" id="brainStatus">Active</div><div>Neural AI</div></div>
            <div class="stat-card"><div class="stat-value" id="totalStores">32+</div><div>Stores & Services</div></div>
        </div>

        <!-- Shopping Section -->
        <div id="shoppingSection">
            <div class="card">
                <div class="card-header"><h2>📝 My Shopping Lists</h2><button onclick="createList()">+ New List</button></div>
                <div id="listsContainer"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>➕ Add Items</h2></div>
                <textarea id="bulkItems" rows="3" placeholder="Enter items (one per line):&#10;Bread&#10;Milk&#10;Eggs&#10;Chicken"></textarea>
                <select id="selectedList"></select>
                <button onclick="addBulkItems()">Add to List</button>
            </div>
            <div class="card">
                <div class="card-header"><h2>💡 Smart Optimization</h2></div>
                <select id="optimizeList"></select>
                <button onclick="optimizeBasket()">Find Best Prices</button>
                <div id="optimizeResults"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>🔔 Price Alerts</h2><button onclick="showAddAlert()">+ New Alert</button></div>
                <div id="alertsList"></div>
            </div>
        </div>

        <!-- Retailers Section -->
        <div id="retailersSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🏬 All Retailers</h2></div>
                <select id="retailerCategoryFilter">
                    <option value="">All Categories</option>
                </select>
                <div id="retailersGrid" class="retailer-grid"></div>
            </div>
        </div>

        <!-- Services Section -->
        <div id="servicesSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🛠️ Service Providers</h2></div>
                <select id="serviceTypeFilter">
                    <option value="">All Services</option>
                    <option value="plumbing">Plumbing</option>
                    <option value="electrical">Electrical</option>
                    <option value="mechanic">Mechanic</option>
                    <option value="cleaning">Cleaning</option>
                    <option value="gardening">Gardening</option>
                    <option value="tutoring">Tutoring</option>
                    <option value="locksmith">Locksmith</option>
                    <option value="painting">Painting</option>
                    <option value="moving">Moving</option>
                </select>
                <button onclick="loadServices()">🔍 Find Services</button>
                <div id="servicesList"></div>
            </div>
            <div class="card">
                <div class="card-header"><h2>🏪 Register Your Business</h2></div>
                <input type="text" id="serviceName" placeholder="Business Name">
                <select id="serviceTypeReg"><option value="plumbing">Plumbing</option><option value="electrical">Electrical</option><option value="mechanic">Mechanic</option><option value="cleaning">Cleaning</option></select>
                <input type="text" id="servicePhone" placeholder="Phone">
                <input type="text" id="serviceAddress" placeholder="Address">
                <button onclick="registerService()">Register Business</button>
            </div>
        </div>

        <!-- Spaza Shops Section -->
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

        <!-- Pharmacy Section -->
        <div id="pharmacySection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>💊 Pharmacies Near You</h2></div>
                <button onclick="findNearbyPharmacies()">Find Pharmacies</button>
                <div id="pharmaciesList"></div>
            </div>
        </div>

        <!-- Delivery Services Section -->
        <div id="deliverySection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🚚 Delivery Services</h2></div>
                <div id="deliveryServicesList"></div>
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

        <!-- Neural Brain Section -->
        <div id="brainSection" class="hidden">
            <div class="card">
                <div class="card-header"><h2>🧠 Consult the Neural AI</h2></div>
                <input type="text" id="brainObjective" placeholder="What decision do you need help with?">
                <input type="number" id="brainAmount" placeholder="Amount (R)" value="5000">
                <input type="number" id="brainRisk" placeholder="Risk Score (0-1)" value="0.3" step="0.1">
                <button onclick="consultBrain()">🧠 Get AI Decision</button>
                <div id="brainResult"></div>
            </div>
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
        document.getElementById('userWelcome').innerHTML=`Hello ${currentUser.username}`;
        loadLists(); loadRetailers();
    }else alert('Login failed');
}

async function register(){
    const u=document.getElementById('regUsername').value;
    const e=document.getElementById('regEmail').value;
    const p=document.getElementById('regPassword').value;
    const r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,email:e,password:p})});
    if(r.ok){ showLogin(); alert('Registered! Please login.'); }
    else alert('Registration failed');
}

function logout(){ fetch('/api/logout',{method:'POST'}); location.reload(); }
function showRegister(){ document.getElementById('loginForm').style.display='none'; document.getElementById('registerForm').style.display='block'; }
function showLogin(){ document.getElementById('loginForm').style.display='block'; document.getElementById('registerForm').style.display='none'; }

function showSection(s){
    const sections=['shopping','retailers','services','spaza','pharmacy','delivery','community','brain'];
    sections.forEach(sec=>document.getElementById(sec+'Section').classList.add('hidden'));
    document.getElementById(s+'Section').classList.remove('hidden');
    if(s=='retailers') loadRetailers();
    if(s=='delivery') loadDeliveryServices();
}

async function loadRetailers(){
    const cat=document.getElementById('retailerCategoryFilter').value;
    const r=await fetch(`/api/retailers${cat?`?category=${cat}`:''}`);
    const retailers=await r.json();
    const categories=await (await fetch('/api/retailers/categories')).json();
    const catSelect=document.getElementById('retailerCategoryFilter');
    if(catSelect.options.length<=1){
        catSelect.innerHTML='<option value="">All Categories</option>';
        categories.forEach(c=>catSelect.innerHTML+=`<option value="${c}">${c}</option>`);
    }
    const grid=document.getElementById('retailersGrid');
    grid.innerHTML=retailers.map(r=>`<div class="retailer-card" onclick="window.open('${r.website}','_blank')"><div class="retailer-logo">${r.logo||'🏪'}</div><div><strong>${r.name}</strong></div><div>⭐ ${r.rating}</div><div><small>Delivery: R${r.delivery_fee}</small></div></div>`).join('');
}

async function loadServices(){
    const type=document.getElementById('serviceTypeFilter').value;
    const loc=await (await fetch('/api/location/detect')).json();
    const r=await fetch(`/api/services?type=${type}&lat=${loc.latitude}&lng=${loc.longitude}`);
    const data=await r.json();
    const list=document.getElementById('servicesList');
    if(data.services.length){
        list.innerHTML=data.services.map(s=>`<div class="card"><strong>🔧 ${s.name}</strong><br>${s.service_type} • R${s.hourly_rate}/hr<br>📞 ${s.phone}<br>${s.distance_km?`📍 ${s.distance_km}km away`:''}<br><button onclick="window.open('https://www.openstreetmap.org/?mlat=${s.latitude}&mlon=${s.longitude}','_blank')">📍 Map</button></div>`).join('');
    }else list.innerHTML='<div class="card">No services found nearby</div>';
}

async function loadDeliveryServices(){
    const r=await fetch('/api/delivery-services');
    const services=await r.json();
    document.getElementById('deliveryServicesList').innerHTML=services.map(s=>`<div class="card"><div class="item-row"><span>${s.logo||'🚚'} ${s.name}</span><span>⭐ ${s.rating}</span></div><div>Base: R${s.base_fee} + R${s.per_km_rate}/km</div><button onclick="window.open('${s.website}','_blank')">Go to ${s.name}</button></div>`).join('');
}

async function loadLists(){
    const r=await fetch('/api/lists');
    if(r.ok){ currentLists=await r.json(); renderLists(); updateSelectors(); }
}

function renderLists(){
    const c=document.getElementById('listsContainer');
    if(!currentLists.length){ c.innerHTML='<div class="card"><p>No lists yet. Create one!</p></div>'; return; }
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
            for(const i of items) html+=`<div class="item-row"><span>${i.emoji||'🛒'} ${i.product_name} x${i.quantity}</span><div><button onclick="toggleItem(${id},${i.id})">${i.checked_off?'✓':'○'}</button></div></div>`;
            c.innerHTML=html;
        }
    }
}

function updateSelectors(){
    const s=document.getElementById('selectedList'), o=document.getElementById('optimizeList');
    s.innerHTML='<option value="">Select list</option>'; o.innerHTML='<option value="">Select list</option>';
    for(const l of currentLists){
        s.innerHTML+=`<option value="${l.id}">${l.name}</option>`;
        o.innerHTML+=`<option value="${l.id}">${l.name}</option>`;
    }
}

async function createList(){
    const n=prompt('List name:','My Shopping List');
    if(n){ await fetch('/api/lists',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n})}); await loadLists(); }
}

function viewList(id){ loadListItems(id); }

async function addBulkItems(){
    const lid=document.getElementById('selectedList').value;
    const text=document.getElementById('bulkItems').value;
    if(!lid){ alert('Select a list'); return; }
    const lines=text.split('\\n').filter(l=>l.trim());
    for(const line of lines) await fetch(`/api/lists/${lid}/items`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_name:line.trim(),quantity:1})});
    document.getElementById('bulkItems').value='';
    await loadListItems(lid); await loadLists();
}

async function toggleItem(lid,iid){ await fetch(`/api/lists/${lid}/items/${iid}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({checked_off:1})}); await loadListItems(lid); }

async function optimizeBasket(){
    const lid=document.getElementById('optimizeList').value;
    if(!lid){ alert('Select a list'); return; }
    const r=await fetch(`/api/optimize/${lid}`);
    const d=await r.json();
    let html=`<div class="stats"><div>Subtotal: R${d.subtotal}</div><div>Delivery: R${d.delivery}</div><div><strong>Total: R${d.total}</strong></div></div><p>💡 ${d.recommendation}</p><h4>Items</h4>`;
    for(const i of d.items) html+=`<div class="item-row"><span>${i.product} x${i.quantity}</span><span>R${i.price} at ${i.store}</span></div>`;
    document.getElementById('optimizeResults').innerHTML=html;
}

async function showAddAlert(){
    const product=prompt('Product name:');
    if(!product) return;
    const target=parseFloat(prompt('Target price (R):'));
    if(isNaN(target)) return;
    await fetch('/api/alerts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_name:product,target_price:target})});
    loadAlerts();
}

async function loadAlerts(){
    const r=await fetch('/api/alerts');
    if(r.ok){
        const alerts=await r.json();
        const c=document.getElementById('alertsList');
        if(!alerts.length) c.innerHTML='<p>No alerts yet</p>';
        else c.innerHTML=alerts.map(a=>`<div class="item-row"><span>${a.emoji||'🔔'} ${a.product_name}</span><span>Alert when ≤ R${a.target_price}</span><button onclick="deleteAlert(${a.id})">Delete</button></div>`).join('');
    }
}

async function deleteAlert(id){ await fetch(`/api/alerts/${id}`,{method:'DELETE'}); loadAlerts(); }

async function registerService(){
    const name=document.getElementById('serviceName').value;
    const type=document.getElementById('serviceTypeReg').value;
    const phone=document.getElementById('servicePhone').value;
    const addr=document.getElementById('serviceAddress').value;
    if(!name){ alert('Enter business name'); return; }
    await fetch('/api/services/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name,service_type:type,phone:phone,address:addr})});
    alert('Registered! Pending verification.');
}

async function registerSpaza(){
    const name=document.getElementById('spazaName').value;
    const addr=document.getElementById('spazaAddress').value;
    const phone=document.getElementById('spazaPhone').value;
    if(!name){ alert('Enter shop name'); return; }
    await fetch('/api/spaza/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({shop_name:name,address:addr,phone:phone})});
    alert('Spaza shop registered! Awaiting verification.');
}

async function findNearbySpazas(){
    const loc=await (await fetch('/api/location/detect')).json();
    const r=await fetch(`/api/spaza?lat=${loc.latitude}&lng=${loc.longitude}`);
    const data=await r.json();
    const list=document.getElementById('spazasList');
    if(data.spaza_shops.length){
        list.innerHTML=data.spaza_shops.map(s=>`<div class="card"><strong>🏪 ${s.shop_name}</strong><br>${s.address||'Address available'}<br>📞 ${s.phone||'N/A'}<br>${s.distance_km?`📍 ${s.distance_km}km away`:''}</div>`).join('');
    }else list.innerHTML='<div class="card">No spaza shops found nearby</div>';
}

async function findNearbyPharmacies(){
    const loc=await (await fetch('/api/location/detect')).json();
    const r=await fetch(`/api/pharmacies?lat=${loc.latitude}&lng=${loc.longitude}`);
    const data=await r.json();
    const list=document.getElementById('pharmaciesList');
    if(data.pharmacies.length){
        list.innerHTML=data.pharmacies.map(p=>`<div class="card"><strong>💊 ${p.name}</strong><br>${p.address}<br>📞 ${p.phone}<br>Delivery: R${p.delivery_fee}<br>${p.distance_km?`📍 ${p.distance_km}km away`:''}</div>`).join('');
    }else list.innerHTML='<div class="card">No pharmacies found nearby</div>';
}

async function reportPrice(){
    const product=document.getElementById('priceProduct').value;
    const retailer=document.getElementById('priceRetailer').value;
    const price=document.getElementById('priceAmount').value;
    if(!product||!retailer||!price){ alert('Fill all fields'); return; }
    const r=await fetch('/api/community/price',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_name:product,retailer_name:retailer,price:parseFloat(price)})});
    const data=await r.json();
    alert(data.message);
}

async function showTrends(){
    const product=document.getElementById('trendProduct').value;
    if(!product) return;
    const r=await fetch(`/api/community/trends/${product}`);
    const trends=await r.json();
    const list=document.getElementById('trendsList');
    if(trends.length){
        list.innerHTML=trends.map(t=>`<div class="item-row"><span>💰 ${t.retailer_name}</span><span>R${t.price}</span><span>${new Date(t.created_at).toLocaleDateString()}</span></div>`).join('');
    }else list.innerHTML='<div class="card">No price trends found</div>';
}

async function consultBrain(){
    const objective=document.getElementById('brainObjective').value;
    const amount=parseFloat(document.getElementById('brainAmount').value);
    const risk=parseFloat(document.getElementById('brainRisk').value);
    if(!objective){ alert('Enter what you need help with'); return; }
    const r=await fetch('/api/brain/think',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({objective,amount,risk_score:risk})});
    const data=await r.json();
    const verdictClass=data.verdict==='APPROVED'?'badge-success':'badge-warning';
    document.getElementById('brainResult').innerHTML=`
        <div class="stats"><div class="stat-card"><div class="stat-value">${data.verdict}</div><div>Verdict</div></div>
        <div class="stat-card"><div class="stat-value">${(data.approval_score*100).toFixed(0)}%</div><div>Approval Score</div></div></div>
        <div class="card"><strong>🤖 AI Decision:</strong> ${data.verdict}<br>${data.evaluations?data.evaluations.map(e=>`<div class="item-row"><span>${e.agent}</span><span class="${verdictClass}">${e.recommendation}</span><span>${(e.confidence*100).toFixed(0)}%</span></div>`).join(''):''}</div>
    `;
}

async function loadAlertsList(){ await loadAlerts(); }
setInterval(()=>{if(document.getElementById('alertsList'))loadAlerts();},30000);
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    print("="*70)
    print("🏆 SHOPAROUND - COMPLETE ONLINE MALL")
    print("="*70)
    print("✅ Retailers: Checkers, Shoprite, Woolworths, Takealot, Makro, Game, Clicks, Dischem, Builders, +30 more")
    print("✅ Delivery Services: Uber Eats, Mr D, Bolt Food, Pargo, The Courier Guy")
    print("✅ Pharmacies: Clicks, Dischem, Medirite")
    print("✅ Service Providers: Plumbing, Electrical, Mechanic, Cleaning, Gardening, Tutoring")
    print("✅ Spaza Shops: Register & Find Nearby")
    print("✅ Neural Brain: 5 AI Agents with Consensus Decision Engine")
    print("✅ Shopping Lists, Price Alerts, Community Prices, Business Registration")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=True)
