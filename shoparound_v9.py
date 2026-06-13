#!/usr/bin/env python3
"""
SHOPAROUND NEXUS v9.0
Complete Mall + Neural AI Brain
"""

import sqlite3
import os
import json
import secrets
import math
import requests
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ============================================
# NEURAL AI BRAIN
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
            {"name": "Strategy Agent", "weight": 0.35},
            {"name": "Risk Agent", "weight": 0.40},
            {"name": "Financial Agent", "weight": 0.30},
            {"name": "Operations Agent", "weight": 0.25},
            {"name": "Founder Agent", "weight": 0.50}
        ]
    
    def think(self, context):
        risk = context.get("risk_score", 0.5)
        score = 0.8 if risk < 0.3 else 0.6 if risk < 0.6 else 0.4
        verdict = "APPROVED" if score > 0.6 else "DEFERRED" if score > 0.4 else "REJECTED"
        did = str(uuid.uuid4())
        ts = datetime.now().isoformat()
        self.memory.store(did, ts, context, verdict, score)
        return {"verdict": verdict, "approval_score": score, "decision_id": did}
    
    def status(self):
        return {"name": "Sediba Ghost Neural Mind", "agents": [a["name"] for a in self.agents], "recent": self.memory.recall(3)}

brain = NeuralBrain()

# ============================================
# FLASK APP
# ============================================

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)
app.permanent_session_lifetime = 86400 * 7  # 7 days

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound.db")

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
        db.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                   (username, email, generate_password_hash(password)))
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
    return jsonify({"id": user["id"], "username": user["username"]})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

# ============================================
# NEURAL AI ROUTES
# ============================================

@app.route("/api/neural/think", methods=["POST"])
def neural_think():
    data = request.get_json(force=True)
    context = {
        "objective": data.get("objective", "Decision"),
        "risk_score": data.get("risk_score", 0.5),
        "amount": data.get("amount", 0)
    }
    return jsonify(brain.think(context))

@app.route("/api/neural/status", methods=["GET"])
def neural_status():
    return jsonify(brain.status())

@app.route("/api/neural/memory", methods=["GET"])
def neural_memory():
    limit = request.args.get("limit", 10, type=int)
    return jsonify({"memories": brain.memory.recall(limit)})

# ============================================
# RETAILERS ROUTES
# ============================================

@app.route("/api/retailers", methods=["GET"])
def get_retailers():
    db = get_db()
    retailers = db.execute("SELECT * FROM retailers WHERE is_active = 1 LIMIT 50").fetchall()
    return jsonify([dict(r) for r in retailers])

@app.route("/api/retailers/categories", methods=["GET"])
def get_retailer_categories():
    db = get_db()
    categories = db.execute("SELECT DISTINCT category FROM retailers").fetchall()
    return jsonify([c["category"] for c in categories])

# ============================================
# SERVICE ROUTES
# ============================================

@app.route("/api/services", methods=["GET"])
def get_services():
    service_type = request.args.get("type", "")
    db = get_db()
    if service_type:
        services = db.execute("SELECT * FROM service_providers WHERE service_type = ? LIMIT 30", (service_type,)).fetchall()
    else:
        services = db.execute("SELECT * FROM service_providers LIMIT 30").fetchall()
    return jsonify([dict(s) for s in services])

# ============================================
# SHOPPING LISTS
# ============================================

@app.route("/api/lists", methods=["GET", "POST"])
@login_required
def handle_lists():
    db = get_db()
    if request.method == "GET":
        lists = db.execute("SELECT * FROM shopping_lists WHERE user_id = ?", (session["user_id"],)).fetchall()
        return jsonify([dict(l) for l in lists])
    else:
        data = request.get_json(force=True)
        cursor = db.execute("INSERT INTO shopping_lists (user_id, name) VALUES (?, ?)", 
                           (session["user_id"], data.get("name", "My List")))
        db.commit()
        return jsonify({"id": cursor.lastrowid})

@app.route("/api/lists/<int:list_id>/items", methods=["GET", "POST"])
@login_required
def handle_items(list_id):
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
# PRICE ALERTS
# ============================================

@app.route("/api/alerts", methods=["GET"])
@login_required
def get_alerts():
    db = get_db()
    alerts = db.execute("SELECT * FROM price_alerts WHERE user_id = ?", (session["user_id"],)).fetchall()
    return jsonify([dict(a) for a in alerts])

# ============================================
# DELIVERY SERVICES
# ============================================

@app.route("/api/delivery-services", methods=["GET"])
def get_delivery_services():
    db = get_db()
    services = db.execute("SELECT * FROM delivery_services").fetchall()
    return jsonify([dict(s) for s in services])

# ============================================
# LOCATION
# ============================================

@app.route("/api/location/detect", methods=["GET"])
def detect_location():
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({"latitude": data.get("lat", -26.2041), "longitude": data.get("lon", 28.0473)})
    except:
        pass
    return jsonify({"latitude": -26.2041, "longitude": 28.0473})

# ============================================
# HEALTH CHECK
# ============================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "version": "9.0", "neural": "active"})

# ============================================
# FRONTEND
# ============================================

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Nexus v9 - AI Mall</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:system-ui,sans-serif;background:#f0f4f0;padding:20px;}
        .navbar{background:#1f8a4c;color:white;padding:1rem;border-radius:1rem;margin-bottom:1rem;display:flex;justify-content:space-between;align-items:center;}
        .navbar h1{font-size:1.3rem;}
        .nav-links{display:flex;gap:0.5rem;flex-wrap:wrap;}
        .nav-links a{color:white;text-decoration:none;padding:0.3rem 0.8rem;border-radius:0.5rem;cursor:pointer;}
        .nav-links a:hover{background:rgba(255,255,255,0.2);}
        .container{max-width:1200px;margin:0 auto;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;border-bottom:2px solid #e5e7eb;padding-bottom:0.5rem;}
        h2{color:#1f8a4c;}
        input,select,button{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #ddd;border-radius:0.5rem;}
        button{background:#1f8a4c;color:white;border:none;cursor:pointer;font-weight:bold;}
        button:hover{background:#166b3a;}
        .hidden{display:none;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem;}
        .item-row{display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid #eee;}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-bottom:1rem;}
        .stat-card{background:#e8f5e9;padding:1rem;border-radius:0.5rem;text-align:center;}
        .stat-value{font-size:1.8rem;font-weight:bold;color:#1f8a4c;}
        .tabs{display:flex;gap:0.5rem;margin-bottom:1rem;}
        .tab{padding:0.5rem 1rem;background:#e5e7eb;border-radius:2rem;cursor:pointer;}
        .tab.active{background:#1f8a4c;color:white;}
        .badge-success{background:#d1fae5;color:#10b981;padding:0.25rem 0.75rem;border-radius:999px;font-size:0.75rem;}
        @media (max-width:768px){.grid{grid-template-columns:1fr;}}
    </style>
</head>
<body>
<div class="navbar">
    <h1>🛍️ ShopAround Nexus v9</h1>
    <div class="nav-links">
        <a onclick="showSection('shopping')">Shopping</a>
        <a onclick="showSection('retailers')">Retailers</a>
        <a onclick="showSection('services')">Services</a>
        <a onclick="showSection('neural')">AI Brain</a>
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
    </div>

    <div id="appSection" style="display:none;">
        <div class="stats">
            <div class="stat-card"><div class="stat-value" id="welcome">-</div><div>Welcome</div></div>
            <div class="stat-card"><div class="stat-value" id="neuralStatus">Active</div><div>Neural AI</div></div>
        </div>

        <div id="shoppingSection">
            <div class="card"><div class="card-header"><h2>📝 My Lists</h2><button onclick="createList()">+ New</button></div><div id="lists"></div></div>
            <div class="card"><div class="card-header"><h2>➕ Add Items</h2></div><textarea id="bulkItems" rows="3" placeholder="Bread&#10;Milk&#10;Eggs"></textarea><select id="listSelect"></select><button onclick="addItems()">Add</button></div>
        </div>

        <div id="retailersSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🏬 Retailers</h2></div><div id="retailersGrid" class="grid"></div></div>
        </div>

        <div id="servicesSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🛠️ Services</h2></div><select id="serviceType"><option value="">All</option><option value="plumbing">Plumbing</option><option value="electrical">Electrical</option><option value="mechanic">Mechanic</option></select><button onclick="loadServices()">Search</button><div id="servicesList"></div></div>
        </div>

        <div id="neuralSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🧠 Consult AI</h2></div>
            <input type="text" id="aiQuestion" placeholder="What decision?">
            <input type="number" id="aiAmount" placeholder="Amount (R)" value="5000">
            <input type="number" id="aiRisk" placeholder="Risk (0-1)" value="0.3" step="0.1">
            <button onclick="consultAI()">Get AI Decision</button>
            <div id="aiResult"></div></div>
        </div>
    </div>
</div>

<script>
let currentUser = null;
let lists = [];

async function login(){
    const u=document.getElementById('loginUsername').value;
    const p=document.getElementById('loginPassword').value;
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
    if(r.ok){
        currentUser=await r.json();
        document.getElementById('authSection').style.display='none';
        document.getElementById('appSection').style.display='block';
        document.getElementById('logoutBtn').style.display='inline-block';
        document.getElementById('welcome').innerHTML=`Hello ${currentUser.username}`;
        loadLists();
        loadRetailers();
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
    document.getElementById('shoppingSection').classList.add('hidden');
    document.getElementById('retailersSection').classList.add('hidden');
    document.getElementById('servicesSection').classList.add('hidden');
    document.getElementById('neuralSection').classList.add('hidden');
    document.getElementById(s+'Section').classList.remove('hidden');
    if(s=='retailers') loadRetailers();
}

async function loadRetailers(){
    const r=await fetch('/api/retailers');
    const retailers=await r.json();
    document.getElementById('retailersGrid').innerHTML=retailers.map(r=>`<div class="card"><strong>${r.name}</strong><br>⭐ ${r.rating}<br>🚚 R${r.delivery_fee}</div>`).join('');
}

async function loadServices(){
    const type=document.getElementById('serviceType').value;
    const r=await fetch(`/api/services${type?`?type=${type}`:''}`);
    const services=await r.json();
    document.getElementById('servicesList').innerHTML=services.map(s=>`<div class="card"><strong>🔧 ${s.name}</strong><br>${s.service_type}<br>📞 ${s.phone}</div>`).join('');
}

async function loadLists(){
    const r=await fetch('/api/lists');
    if(r.ok){
        lists=await r.json();
        const container=document.getElementById('lists');
        if(!lists.length) container.innerHTML='<p>No lists. Create one!</p>';
        else{
            container.innerHTML=lists.map(l=>`<div class="card"><div class="item-row"><span>📋 ${l.name}</span><button onclick="viewList(${l.id})">View</button></div><div id="items-${l.id}"></div></div>`).join('');
            lists.forEach(l=>loadListItems(l.id));
        }
        const select=document.getElementById('listSelect');
        select.innerHTML='<option value="">Select list</option>'+lists.map(l=>`<option value="${l.id}">${l.name}</option>`).join('');
    }
}

async function loadListItems(id){
    const r=await fetch(`/api/lists/${id}/items`);
    if(r.ok){
        const items=await r.json();
        const container=document.getElementById(`items-${id}`);
        if(!items.length) container.innerHTML='<p>Empty</p>';
        else container.innerHTML=items.map(i=>`<div class="item-row"><span>🛒 ${i.product_name} x${i.quantity}</span></div>`).join('');
    }
}

async function createList(){
    const n=prompt('List name:');
    if(n){ await fetch('/api/lists',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n})}); await loadLists(); }
}

function viewList(id){ loadListItems(id); }

async function addItems(){
    const lid=document.getElementById('listSelect').value;
    const text=document.getElementById('bulkItems').value;
    if(!lid){ alert('Select list'); return; }
    const lines=text.split('\\n').filter(l=>l.trim());
    for(const line of lines){
        await fetch(`/api/lists/${lid}/items`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_name:line.trim()})});
    }
    document.getElementById('bulkItems').value='';
    await loadListItems(lid);
}

async function consultAI(){
    const q=document.getElementById('aiQuestion').value;
    const amt=parseFloat(document.getElementById('aiAmount').value);
    const risk=parseFloat(document.getElementById('aiRisk').value);
    if(!q){ alert('Enter a question'); return; }
    const r=await fetch('/api/neural/think',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({objective:q,amount:amt,risk_score:risk})});
    const d=await r.json();
    const badge=d.verdict==='APPROVED'?'badge-success':'';
    document.getElementById('aiResult').innerHTML=`<div class="card"><strong>🧠 AI Decision:</strong> <span class="${badge}">${d.verdict}</span><br>Approval: ${(d.approval_score*100).toFixed(0)}%</div>`;
}

autoDemo();
async function autoDemo(){
    await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'demo',password:'demo123'})});
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'demo',password:'demo123'})});
    if(r.ok) login();
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

# ============================================
# INITIALIZE DATABASE
# ============================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    
    # Users table with correct schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            session_token TEXT,
            preferences TEXT DEFAULT '{}',
            total_saved REAL DEFAULT 0,
            loyalty_points INTEGER DEFAULT 0,
            household_size INTEGER DEFAULT 1,
            monthly_budget REAL DEFAULT 0,
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Retailers table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS retailers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            website TEXT,
            logo TEXT,
            delivery_fee REAL DEFAULT 35,
            rating REAL DEFAULT 4.0,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Service providers
    conn.execute("""
        CREATE TABLE IF NOT EXISTS service_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service_type TEXT,
            phone TEXT,
            address TEXT,
            rating REAL DEFAULT 4.0
        )
    """)
    
    # Shopping lists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT DEFAULT 'My List',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Shopping list items
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER,
            product_name TEXT,
            quantity REAL DEFAULT 1,
            checked_off INTEGER DEFAULT 0
        )
    """)
    
    # Price alerts
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            target_price REAL,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Delivery services
    conn.execute("""
        CREATE TABLE IF NOT EXISTS delivery_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service_type TEXT,
            base_fee REAL,
            per_km_rate REAL,
            website TEXT,
            rating REAL DEFAULT 4.0
        )
    """)
    
    # Seed data
    cursor = conn.cursor()
    
    # Seed retailers
    retailers = [
        ("Checkers", "Grocery", "https://checkers.co.za", "🛒", 35, 4.2),
        ("Shoprite", "Grocery", "https://shoprite.co.za", "🛒", 35, 4.1),
        ("Woolworths", "Grocery", "https://woolworths.co.za", "🥩", 45, 4.5),
        ("Takealot", "E-commerce", "https://takealot.com", "🛍️", 50, 4.4),
        ("Clicks", "Pharmacy", "https://clicks.co.za", "💊", 30, 4.3),
    ]
    for r in retailers:
        cursor.execute("INSERT OR IGNORE INTO retailers (name, category, website, logo, delivery_fee, rating) VALUES (?, ?, ?, ?, ?, ?)", r)
    
    # Seed services
    services = [
        ("Plumbmaster", "plumbing", "011 123 4567", "Johannesburg", 4.2),
        ("JHB Electricians", "electrical", "011 234 5678", "Johannesburg", 4.5),
        ("Auto Care", "mechanic", "011 345 6789", "Johannesburg", 4.0),
    ]
    for s in services:
        cursor.execute("INSERT OR IGNORE INTO service_providers (name, service_type, phone, address, rating) VALUES (?, ?, ?, ?, ?)", s)
    
    # Seed delivery services
    delivery = [
        ("Uber Eats", "Food", 10, 5, "https://ubereats.com", 4.3),
        ("Mr D Food", "Food", 10, 4, "https://mrdfood.com", 4.2),
    ]
    for d in delivery:
        cursor.execute("INSERT OR IGNORE INTO delivery_services (name, service_type, base_fee, per_km_rate, website, rating) VALUES (?, ?, ?, ?, ?, ?)", d)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

init_db()

if __name__ == "__main__":
    print("="*60)
    print("🛍️  SHOPAROUND NEXUS v9.0")
    print("="*60)
    print("✅ Neural AI Brain Active")
    print("✅ 5 AI Agents Running")
    print("✅ Retailers, Services, Shopping Lists Ready")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=True)
