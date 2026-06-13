#!/usr/bin/env python3
"""
SHOPAROUND NEXUS - Final Working Version
All database columns corrected
"""

import os
import json
import sqlite3
import hashlib
import secrets
import re
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ============================================
# CONFIGURATION
# ============================================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "shoparound_nexus.db"

# ============================================
# DATABASE FUNCTIONS
# ============================================
@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database with correct schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                session_token TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Product catalog (with correct column names)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                size TEXT,
                unit TEXT,
                nutritional_info TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Shopping list
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name TEXT,
                quantity REAL,
                price REAL,
                store TEXT,
                purchased INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Community prices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name TEXT,
                retailer TEXT,
                price REAL,
                verified INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default products
        default_products = [
            ("Maize Meal", "Ace", "Staple", "5kg", "bag", '{"calories": 450, "protein": 8}'),
            ("Rice", "Tastic", "Staple", "1kg", "bag", '{"calories": 1300, "protein": 9}'),
            ("Bread", "Sasko", "Bakery", "loaf", "each", '{"calories": 800, "protein": 8}'),
            ("Eggs", "Nulaid", "Dairy", "dozen", "pack", '{"calories": 840, "protein": 72}'),
            ("Chicken", "Irvine", "Meat", "2kg", "pack", '{"calories": 4000, "protein": 240}'),
            ("Milk", "Clover", "Dairy", "1L", "bottle", '{"calories": 640, "protein": 32}'),
            ("Cabbage", "Fresh", "Vegetable", "each", "each", '{"calories": 200, "protein": 2}'),
            ("Cooking Oil", "Sunfoil", "Pantry", "750ml", "bottle", '{"calories": 6000, "protein": 0}'),
            ("Potatoes", "Fresh", "Vegetable", "5kg", "bag", '{"calories": 3850, "protein": 10}'),
            ("Onions", "Fresh", "Vegetable", "2kg", "bag", '{"calories": 800, "protein": 3}'),
        ]
        
        for product in default_products:
            cursor.execute("""
                INSERT OR IGNORE INTO product_catalog (product_name, brand, category, size, unit, nutritional_info)
                VALUES (?, ?, ?, ?, ?, ?)
            """, product)
        
        print("✅ Database initialized")

# Initialize database
init_database()

# ============================================
# SIMPLE PRODUCT DATA (for UI)
# ============================================
PRODUCTS = [
    {"name": "Maize Meal", "price": 48, "emoji": "🌽", "store": "Shoprite", "calories": 450, "protein": 8},
    {"name": "Rice", "price": 35, "emoji": "🍚", "store": "Checkers", "calories": 1300, "protein": 9},
    {"name": "Bread", "price": 15, "emoji": "🍞", "store": "Checkers", "calories": 800, "protein": 8},
    {"name": "Eggs", "price": 42, "emoji": "🥚", "store": "Checkers", "calories": 840, "protein": 72},
    {"name": "Chicken", "price": 120, "emoji": "🍗", "store": "Pick n Pay", "calories": 4000, "protein": 240},
    {"name": "Milk", "price": 22, "emoji": "🥛", "store": "Checkers", "calories": 640, "protein": 32},
    {"name": "Cabbage", "price": 18, "emoji": "🥬", "store": "Shoprite", "calories": 200, "protein": 2},
    {"name": "Cooking Oil", "price": 45, "emoji": "🫒", "store": "Checkers", "calories": 6000, "protein": 0},
    {"name": "Potatoes", "price": 45, "emoji": "🥔", "store": "Shoprite", "calories": 3850, "protein": 10},
    {"name": "Onions", "price": 30, "emoji": "🧅", "store": "Spaza", "calories": 800, "protein": 3},
]

# ============================================
# SECURITY
# ============================================
def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, 32)
    return base64.b64encode(key).decode(), base64.b64encode(salt).decode()

def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    salt = base64.b64decode(stored_salt.encode())
    key, _ = hash_password(password, salt)
    return key == stored_hash

def create_session_token() -> str:
    return secrets.token_urlsafe(32)

def create_user(username: str, password: str, email: str = None) -> bool:
    try:
        hashed, salt = hash_password(password)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            """, (username, email, hashed, salt))
        return True
    except:
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, salt FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and verify_password(password, user["password_hash"], user["salt"]):
            token = create_session_token()
            cursor.execute("UPDATE users SET session_token = ? WHERE id = ?", (token, user["id"]))
            return {"id": user["id"], "username": user["username"], "token": token}
    return None

def get_user_by_token(token: str) -> Optional[Dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE session_token = ?", (token,))
        user = cursor.fetchone()
        return dict(user) if user else None

# ============================================
# FASTAPI APP
# ============================================
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app = FastAPI(title="ShopAround Nexus", version="4.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# ============================================
# MODELS
# ============================================
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class PlanRequest(BaseModel):
    budget: float = Field(..., ge=10, le=50000)
    household_size: int = 2

class PriceReportRequest(BaseModel):
    product_name: str
    retailer: str
    price: float

class VoiceRequest(BaseModel):
    command: str

# ============================================
# AI PLANNER
# ============================================
def optimize_shopping_list(budget: float, household_size: int = 2) -> Dict:
    products = sorted(PRODUCTS, key=lambda x: x["calories"] / x["price"] if x["price"] > 0 else 0, reverse=True)
    
    basket = []
    total = 0
    total_calories = 0
    total_protein = 0
    
    for p in products:
        if total + p["price"] <= budget:
            basket.append({
                "name": p["name"],
                "price": p["price"],
                "emoji": p["emoji"],
                "store": p["store"],
                "calories": p["calories"],
                "protein": p["protein"]
            })
            total += p["price"]
            total_calories += p["calories"]
            total_protein += p["protein"]
    
    meals = total_calories // (2000 * max(1, household_size)) if total_calories > 0 else 0
    
    return {
        "basket": basket,
        "total": round(total, 2),
        "remaining": round(budget - total, 2),
        "total_calories": total_calories,
        "total_protein": total_protein,
        "meals_possible": meals,
        "items_count": len(basket)
    }

# ============================================
# VOICE ASSISTANT
# ============================================
def process_voice(command: str) -> Dict:
    cmd_lower = command.lower()
    
    # Budget command
    numbers = re.findall(r'R?(\d+)', cmd_lower)
    if numbers:
        budget = float(numbers[0])
        plan = optimize_shopping_list(budget)
        return {
            "type": "plan",
            "message": f"With R{budget}, you can buy {plan['items_count']} items for {plan['meals_possible']} meals.",
            "plan": plan
        }
    
    # Price check
    for p in PRODUCTS:
        if p["name"].lower() in cmd_lower:
            return {
                "type": "price",
                "message": f"{p['name']} is about R{p['price']} at {p['store']}.",
                "product": p
            }
    
    return {"type": "help", "message": "Try: '200' for budget plan, or 'price of bread'"}

# ============================================
# COMMUNITY PRICES
# ============================================
def submit_community_price(user_id: int, product: str, retailer: str, price: float) -> Dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO community_prices (user_id, product_name, retailer, price)
            VALUES (?, ?, ?, ?)
        """, (user_id, product, retailer, price))
        
        cursor.execute("SELECT AVG(price) as avg_price, COUNT(*) as count FROM community_prices WHERE product_name = ?", (product,))
        result = cursor.fetchone()
        
        return {
            "average": round(result["avg_price"], 2) if result["avg_price"] else price,
            "count": result["count"] if result else 1
        }

# ============================================
# API ENDPOINTS
# ============================================
@app.get("/")
async def root():
    return HTMLResponse(UI_HTML)

@app.post("/api/register")
async def register(req: RegisterRequest):
    success = create_user(req.username, req.password, req.email)
    if success:
        return {"success": True, "message": "User created"}
    return {"success": False, "message": "Username exists"}

@app.post("/api/login")
async def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if user:
        return {"success": True, "user": user}
    return {"success": False, "message": "Invalid credentials"}

@app.post("/api/plan")
async def plan(req: PlanRequest):
    result = optimize_shopping_list(req.budget, req.household_size)
    return JSONResponse(result)

@app.post("/api/voice")
async def voice(req: VoiceRequest):
    result = process_voice(req.command)
    return JSONResponse(result)

@app.post("/api/report-price")
async def report_price(req: PriceReportRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return JSONResponse({"success": False, "message": "Login required"}, status_code=401)
    
    user = get_user_by_token(credentials.credentials)
    if not user:
        return JSONResponse({"success": False, "message": "Invalid session"}, status_code=401)
    
    result = submit_community_price(user["id"], req.product_name, req.retailer, req.price)
    return JSONResponse({
        "success": True,
        "message": f"Price reported! Avg: R{result['average']} from {result['count']} reports"
    })

@app.get("/api/products")
async def products_list():
    return JSONResponse({"products": PRODUCTS})

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "4.0.0", "features": ["planner", "voice", "community"]}

# ============================================
# UI HTML
# ============================================
UI_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Nexus - Smart Shopping</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}
        .container{max-width:600px;margin:0 auto;}
        .card{background:white;border-radius:30px;padding:25px;margin-bottom:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);}
        h1{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
        input,button{width:100%;padding:14px;margin-top:12px;border:2px solid #e0e0e0;border-radius:16px;font-size:16px;}
        button{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;font-weight:bold;cursor:pointer;}
        .stats{background:#f0f0ff;padding:15px;border-radius:16px;margin-top:15px;}
        .item{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #eee;}
        .total{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:15px;border-radius:16px;margin-top:15px;}
        .tab-bar{display:flex;gap:5px;margin-bottom:20px;}
        .tab{flex:1;text-align:center;padding:10px;background:rgba(102,126,234,0.1);border-radius:20px;cursor:pointer;}
        .tab.active{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;}
        .hidden{display:none;}
        .voice-result{background:#e8f4f8;padding:15px;border-radius:16px;margin-top:15px;}
        .auth-section{display:flex;gap:10px;margin-bottom:15px;}
        .auth-section input{margin-top:0;}
        .auth-section button{margin-top:0;width:auto;padding:10px 20px;}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>🛍️ ShopAround Nexus</h1>
        <p>Complete Shopping Intelligence Platform</p>
        
        <div class="auth-section">
            <input type="text" id="loginUsername" placeholder="Username">
            <input type="password" id="loginPassword" placeholder="Password">
            <button onclick="login()">Login</button>
            <button onclick="showRegister()" style="background:#666;">Register</button>
        </div>
        
        <div class="tab-bar">
            <div class="tab active" onclick="showTab('planner')">Planner</div>
            <div class="tab" onclick="showTab('voice')">Voice</div>
            <div class="tab" onclick="showTab('community')">Community</div>
        </div>
        
        <div id="plannerTab">
            <input type="number" id="budget" placeholder="Budget (R)" value="200">
            <input type="number" id="householdSize" placeholder="Household Size" value="2">
            <button onclick="generatePlan()">Generate AI Plan</button>
            <div id="results"></div>
        </div>
        
        <div id="voiceTab" class="hidden">
            <div class="stats">
                <p><strong>Voice Assistant</strong></p>
                <p>Try: "200" or "price of bread"</p>
                <input type="text" id="voiceCommand" placeholder="Type command...">
                <button onclick="processVoice()">Send</button>
                <div id="voiceResult" class="voice-result hidden"></div>
            </div>
        </div>
        
        <div id="communityTab" class="hidden">
            <div class="stats">
                <p><strong>Report Price to Community</strong></p>
                <input type="text" id="productName" placeholder="Product name">
                <input type="text" id="retailerName" placeholder="Retailer">
                <input type="number" id="productPrice" placeholder="Price (R)">
                <button onclick="reportPrice()">Submit</button>
                <div id="communityResult"></div>
            </div>
        </div>
    </div>
</div>

<script>
let token = localStorage.getItem("token");

async function login() {
    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;
    const res = await fetch("/api/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username, password})
    });
    const data = await res.json();
    if (data.success) {
        token = data.user.token;
        localStorage.setItem("token", token);
        alert("Logged in!");
    } else {
        alert("Login failed");
    }
}

async function showRegister() {
    const username = prompt("Username:");
    const password = prompt("Password:");
    if (username && password) {
        const res = await fetch("/api/register", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        alert(data.message);
    }
}

function showTab(tabName) {
    document.getElementById("plannerTab").classList.add("hidden");
    document.getElementById("voiceTab").classList.add("hidden");
    document.getElementById("communityTab").classList.add("hidden");
    document.getElementById(`${tabName}Tab`).classList.remove("hidden");
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    event.target.classList.add("active");
}

async function generatePlan() {
    const budget = document.getElementById("budget").value;
    const household = document.getElementById("householdSize").value;
    const res = await fetch("/api/plan", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({budget: parseFloat(budget), household_size: parseInt(household)})
    });
    const data = await res.json();
    
    let html = `<div class="stats">Calories: ${data.total_calories} | Protein: ${data.total_protein}g | ${data.meals_possible} meals</div>`;
    data.basket.forEach(i => {
        html += `<div class="item"><span>${i.emoji} ${i.name}</span><span>R${i.price}</span></div>`;
    });
    html += `<div class="total">Total: R${data.total} | Remaining: R${data.remaining}</div>`;
    document.getElementById("results").innerHTML = html;
}

async function processVoice() {
    const command = document.getElementById("voiceCommand").value;
    if (!command) return;
    const res = await fetch("/api/voice", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({command})
    });
    const data = await res.json();
    let html = `<div class="voice-result">${data.message}</div>`;
    document.getElementById("voiceResult").innerHTML = html;
    document.getElementById("voiceResult").classList.remove("hidden");
}

async function reportPrice() {
    const product = document.getElementById("productName").value;
    const retailer = document.getElementById("retailerName").value;
    const price = document.getElementById("productPrice").value;
    if (!product || !retailer || !price) { alert("Fill all fields"); return; }
    if (!token) { alert("Please login first"); return; }
    
    const res = await fetch("/api/report-price", {
        method: "POST",
        headers: {"Content-Type": "application/json", "Authorization": `Bearer ${token}`},
        body: JSON.stringify({product_name: product, retailer: retailer, price: parseFloat(price)})
    });
    const data = await res.json();
    if (data.success) {
        document.getElementById("communityResult").innerHTML = `<div class="voice-result">${data.message}</div>`;
        document.getElementById("productName").value = "";
        document.getElementById("retailerName").value = "";
        document.getElementById("productPrice").value = "";
    } else {
        alert(data.message);
    }
}
</script>
</body>
</html>
'''

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("🛍️  ShopAround Nexus - Final Working Version")
    print("="*60)
    print("✅ AI Shopping Planner")
    print("✅ Voice Assistant")
    print("✅ Community Price Network")
    print("✅ User Authentication")
    print("="*60)
    print("🌐 Open: http://localhost:9000")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=9000)
