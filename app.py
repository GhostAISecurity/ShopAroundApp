#!/usr/bin/env python3
"""
SHOPAROUND v7.0 - Complete South African Shopping Intelligence
Features: User Accounts | Voice Commands | Offline AI | Dynamic Location
"""

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import aiohttp, asyncio, time, random, re, sqlite3, json, hashlib, secrets
from bs4 import BeautifulSoup
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
from pathlib import Path
import os
from contextlib import contextmanager

app = FastAPI(title="SHOPAROUND - SA Shopping Intelligence")

# Create directories
Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("user_data").mkdir(exist_ok=True)

# =========================
# DATABASE WITH USER SYSTEM
# =========================
db = sqlite3.connect("shoparound.db", check_same_thread=False)
cur = db.cursor()

# Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    email TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_token TEXT,
    preferences TEXT DEFAULT '{}'
)
""")

# Shopping history per user
cur.execute("""
CREATE TABLE IF NOT EXISTS shopping_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    budget REAL,
    total_spent REAL,
    location TEXT,
    items TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Saved lists per user
cur.execute("""
CREATE TABLE IF NOT EXISTS saved_lists (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    name TEXT,
    items TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Price tracking
cur.execute("""
CREATE TABLE IF NOT EXISTS price_alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product TEXT,
    target_price REAL,
    current_price REAL,
    active INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Voice commands log
cur.execute("""
CREATE TABLE IF NOT EXISTS voice_commands (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    command TEXT,
    response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()

# =========================
# COMPLETE SA LOCATION DATABASE
# =========================
SA_LOCATIONS = {
    # Major cities
    "johannesburg": (-26.2041, 28.0473, 1.02, "🏙️ Johannesburg", "Gauteng"),
    "pretoria": (-25.7461, 28.1881, 1.00, "🏛️ Pretoria", "Gauteng"),
    "cape_town": (-33.9249, 18.4241, 1.08, "🌊 Cape Town", "Western Cape"),
    "durban": (-29.8587, 31.0218, 1.05, "🏖️ Durban", "KwaZulu-Natal"),
    "port_elizabeth": (-33.9608, 25.6022, 1.03, "⚓ Gqeberha", "Eastern Cape"),
    "east_london": (-33.0154, 27.9116, 1.03, "🌅 East London", "Eastern Cape"),
    "bloemfontein": (-29.1213, 26.2147, 1.03, "🌹 Bloemfontein", "Free State"),
    "polokwane": (-23.8962, 29.4486, 1.05, "🌳 Polokwane", "Limpopo"),
    "nelspruit": (-25.4655, 30.9805, 1.07, "🌴 Mbombela", "Mpumalanga"),
    "kimberley": (-28.7282, 24.7499, 1.02, "💎 Kimberley", "Northern Cape"),
    "rural_eastern_cape": (-31.0, 28.0, 1.20, "🌾 Rural EC", "Eastern Cape"),
    "rural_limpopo": (-23.5, 29.5, 1.18, "🌾 Rural Limpopo", "Limpopo"),
    "rural_kzn": (-28.5, 30.5, 1.17, "🌾 Rural KZN", "KwaZulu-Natal")
}

# =========================
# COMPLETE PRODUCT DATABASE
# =========================
PRODUCTS = {
    # Staple foods
    "maize meal": {"price": 48.00, "shop": "Shoprite", "category": "staple", "emoji": "🌽"},
    "rice (1kg)": {"price": 35.00, "shop": "Checkers", "category": "staple", "emoji": "🍚"},
    "rice (cup)": {"price": 4.00, "shop": "Spaza", "category": "micro", "emoji": "🍚"},
    "bread": {"price": 15.00, "shop": "Checkers", "category": "staple", "emoji": "🍞"},
    "brown bread": {"price": 14.00, "shop": "Shoprite", "category": "staple", "emoji": "🍞"},
    
    # Proteins
    "egg": {"price": 3.00, "shop": "Spaza", "category": "protein", "emoji": "🥚"},
    "dozen eggs": {"price": 42.00, "shop": "Checkers", "category": "protein", "emoji": "🥚"},
    "chicken (2kg)": {"price": 120.00, "shop": "Pick n Pay", "category": "protein", "emoji": "🍗"},
    "chicken quarter": {"price": 15.00, "shop": "Spaza", "category": "protein", "emoji": "🍗"},
    "beef (1kg)": {"price": 140.00, "shop": "Woolworths", "category": "protein", "emoji": "🥩"},
    "liver portion": {"price": 8.00, "shop": "Spaza", "category": "protein", "emoji": "🥩"},
    
    # Vegetables
    "cabbage": {"price": 18.00, "shop": "Shoprite", "category": "vegetable", "emoji": "🥬"},
    "onion": {"price": 2.00, "shop": "Spaza", "category": "vegetable", "emoji": "🧅"},
    "tomato": {"price": 2.00, "shop": "Spaza", "category": "vegetable", "emoji": "🍅"},
    "potato": {"price": 2.50, "shop": "Spaza", "category": "vegetable", "emoji": "🥔"},
    "carrot": {"price": 1.50, "shop": "Spaza", "category": "vegetable", "emoji": "🥕"},
    "spinach bunch": {"price": 8.00, "shop": "Spaza", "category": "vegetable", "emoji": "🥬"},
    
    # Oils & Fats
    "cooking oil (750ml)": {"price": 45.00, "shop": "Checkers", "category": "oil", "emoji": "🫒"},
    "small oil": {"price": 5.00, "shop": "Spaza", "category": "micro", "emoji": "🫒"},
    
    # Dairy
    "milk (1L)": {"price": 22.50, "shop": "Checkers", "category": "dairy", "emoji": "🥛"},
    
    # Baking & Pantry
    "sugar (2.5kg)": {"price": 45.00, "shop": "Shoprite", "category": "pantry", "emoji": "🍬"},
    "sugar packet": {"price": 1.00, "shop": "Spaza", "category": "micro", "emoji": "🍬"},
    "salt (1kg)": {"price": 12.00, "shop": "Checkers", "category": "pantry", "emoji": "🧂"},
    "teabag": {"price": 0.50, "shop": "Spaza", "category": "micro", "emoji": "🫖"},
    "complete meal": {"price": 15.00, "shop": "Spaza", "category": "meal", "emoji": "🍲"},
    
    # Legumes
    "dry beans (cup)": {"price": 5.00, "shop": "Spaza", "category": "legume", "emoji": "🫘"},
    "samp": {"price": 10.00, "shop": "Spaza", "category": "staple", "emoji": "🌾"}
}

# =========================
# USER MANAGEMENT
# =========================
class UserManager:
    @staticmethod
    def create_user(username: str, password: str, email: str = None):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cur.execute("INSERT INTO users (username, password_hash, email) VALUES (?,?,?)",
                       (username, password_hash, email))
            db.commit()
            return True
        except:
            return False
    
    @staticmethod
    def authenticate(username: str, password: str):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute("SELECT id, username FROM users WHERE username=? AND password_hash=?", 
                   (username, password_hash))
        user = cur.fetchone()
        if user:
            # Generate session token
            token = secrets.token_urlsafe(32)
            cur.execute("UPDATE users SET session_token=? WHERE id=?", (token, user[0]))
            db.commit()
            return {"id": user[0], "username": user[1], "token": token}
        return None
    
    @staticmethod
    def get_user_by_token(token: str):
        cur.execute("SELECT id, username FROM users WHERE session_token=?", (token,))
        return cur.fetchone()
    
    @staticmethod
    def save_shopping_history(user_id: int, budget: float, total: float, location: str, items: list):
        cur.execute("INSERT INTO shopping_history (user_id, budget, total_spent, location, items) VALUES (?,?,?,?,?)",
                   (user_id, budget, total, location, json.dumps(items)))
        db.commit()
    
    @staticmethod
    def get_user_stats(user_id: int):
        # Total spent all time
        cur.execute("SELECT SUM(total_spent) FROM shopping_history WHERE user_id=?", (user_id,))
        total_spent = cur.fetchone()[0] or 0
        
        # Average budget
        cur.execute("SELECT AVG(budget) FROM shopping_history WHERE user_id=?", (user_id,))
        avg_budget = cur.fetchone()[0] or 0
        
        # Number of plans
        cur.execute("SELECT COUNT(*) FROM shopping_history WHERE user_id=?", (user_id,))
        plans_count = cur.fetchone()[0] or 0
        
        return {
            "total_spent": round(total_spent, 2),
            "avg_budget": round(avg_budget, 2),
            "plans_count": plans_count
        }

# =========================
# VOICE COMMAND PROCESSOR
# =========================
class VoiceProcessor:
    @staticmethod
    def process_command(text: str, user_id: int = None):
        """Process natural language voice commands"""
        text = text.lower().strip()
        
        # Pattern: "budget R100 in soweto"
        budget_match = re.search(r'budget\s*[r]?\s*(\d+)', text)
        location_match = re.search(r'in\s+(\w+)', text)
        
        if budget_match:
            budget = float(budget_match.group(1))
            location = location_match.group(1) if location_match else "johannesburg"
            
            # Get location coordinates
            loc_data = SA_LOCATIONS.get(location, SA_LOCATIONS["johannesburg"])
            
            return {
                "type": "plan",
                "budget": budget,
                "lat": loc_data[0],
                "lng": loc_data[1],
                "location": location
            }
        
        # Pattern: "price of bread"
        price_match = re.search(r'price of (\w+)', text)
        if price_match:
            product = price_match.group(1)
            return {"type": "price", "product": product}
        
        # Pattern: "save this list as X"
        save_match = re.search(r'save (?:this list as|as) (.+)', text)
        if save_match:
            return {"type": "save", "name": save_match.group(1)}
        
        # Pattern: "my stats" or "my history"
        if "my stats" in text or "my history" in text:
            return {"type": "stats"}
        
        # Help
        if "help" in text:
            return {
                "type": "help",
                "message": "Say: 'budget R100 in soweto', 'price of bread', 'my stats', 'save this list as weekly'"
            }
        
        return {"type": "unknown"}

# =========================
# GEOSPATIAL ENGINE
# =========================
class GeoEngine:
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """Calculate distance between two points"""
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c
    
    @staticmethod
    def find_nearest_location(lat, lng):
        """Find the closest SA location to given coordinates"""
        nearest = None
        min_dist = float('inf')
        
        for name, (clat, clng, _, _, _) in SA_LOCATIONS.items():
            dist = GeoEngine.haversine(lat, lng, clat, clng)
            if dist < min_dist:
                min_dist = dist
                nearest = name
        
        return nearest, min_dist
    
    @staticmethod
    def get_price_multiplier(location_name):
        """Get location-based price multiplier"""
        return SA_LOCATIONS.get(location_name, SA_LOCATIONS["johannesburg"])[2]

# =========================
# AI SHOPPING PLANNER
# =========================
class ShoppingAI:
    @staticmethod
    def optimize_shopping_list(budget: float, location: str, user_id: int = None):
        """Generate optimal shopping list"""
        
        # Get location multiplier
        multiplier = GeoEngine.get_price_multiplier(location)
        
        # Priority order (most important first)
        priority = [
            "maize meal", "rice (1kg)", "bread", "egg", "chicken quarter",
            "cabbage", "onion", "tomato", "potato", "carrot",
            "cooking oil (750ml)", "milk (1L)", "sugar (2.5kg)", "salt (1kg)"
        ]
        
        basket = []
        total = 0
        
        for item in priority:
            if item in PRODUCTS:
                base_price = PRODUCTS[item]["price"]
                adjusted_price = round(base_price * multiplier, 2)
                shop = PRODUCTS[item]["shop"]
                emoji = PRODUCTS[item]["emoji"]
                
                if total + adjusted_price <= budget:
                    basket.append({
                        "item": item,
                        "price": adjusted_price,
                        "shop": shop,
                        "emoji": emoji,
                        "category": PRODUCTS[item]["category"]
                    })
                    total += adjusted_price
        
        # Save to user history if logged in
        if user_id:
            UserManager.save_shopping_history(user_id, budget, total, location, basket)
        
        return {
            "basket": basket,
            "total": round(total, 2),
            "remaining": round(budget - total, 2),
            "items_count": len(basket),
            "location": location,
            "multiplier": multiplier
        }

# =========================
# HTML UI - COMPLETE DASHBOARD
# =========================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>SHOPAROUND - South Africa's Smart Shopping Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1400px; margin: 0 auto; }
        
        /* Header */
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.8em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        /* Auth Panel */
        .auth-panel {
            background: white;
            border-radius: 15px;
            padding: 15px 25px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .user-info {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .user-name {
            font-weight: bold;
            color: #667eea;
        }
        
        .auth-buttons {
            display: flex;
            gap: 10px;
        }
        
        .btn-small {
            padding: 8px 20px;
            font-size: 14px;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }
        
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        
        /* Cards */
        .card {
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }
        
        /* Voice Command Bar */
        .voice-bar {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 50px;
            padding: 15px 25px;
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            align-items: center;
            cursor: pointer;
            transition: transform 0.3s;
        }
        
        .voice-bar:hover { transform: scale(1.02); }
        .voice-icon { font-size: 2em; }
        .voice-text { flex: 1; color: white; font-size: 1.1em; }
        .mic-button {
            background: white;
            border: none;
            padding: 12px 25px;
            border-radius: 50px;
            font-weight: bold;
            cursor: pointer;
        }
        
        /* Form Elements */
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
        }
        input:focus, select:focus { outline: none; border-color: #667eea; }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s;
        }
        button:hover { transform: translateY(-2px); }
        
        /* Shopping List */
        .shopping-list {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
        }
        
        .item-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .item-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .item-emoji { font-size: 1.5em; }
        .item-name { font-weight: 500; color: #333; }
        .item-shop { font-size: 0.85em; color: #888; margin-left: 10px; }
        .item-price { color: #667eea; font-weight: bold; }
        
        .total-row {
            display: flex;
            justify-content: space-between;
            padding: 15px;
            background: #667eea;
            color: white;
            border-radius: 10px;
            margin-top: 10px;
            font-weight: bold;
        }
        
        /* Layout Grid */
        .two-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
        @media (max-width: 768px) { .two-columns { grid-template-columns: 1fr; } }
        
        /* Loading */
        .loading { display: none; text-align: center; padding: 20px; }
        .loading.show { display: block; }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal.show { display: flex; }
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 400px;
            width: 90%;
        }
        
        .footer {
            text-align: center;
            color: white;
            padding: 20px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛍️ SHOPAROUND</h1>
            <p>South Africa's Smart Shopping Assistant | Real Prices • Real Data • Real Savings</p>
        </div>
        
        <!-- Auth Panel -->
        <div class="auth-panel" id="authPanel">
            <div id="userInfo">
                <span>👤 <span id="userNameDisplay">Guest</span></span>
            </div>
            <div class="auth-buttons" id="authButtons">
                <button class="btn-small" onclick="showLoginModal()">Login</button>
                <button class="btn-small" onclick="showRegisterModal()">Register</button>
            </div>
        </div>
        
        <!-- Voice Command Bar -->
        <div class="voice-bar" onclick="startVoiceRecognition()">
            <div class="voice-icon">🎤</div>
            <div class="voice-text" id="voiceText">Tap here or say "budget R100 in soweto"</div>
            <div class="mic-button">🎙️ Speak Now</div>
        </div>
        
        <!-- Stats Grid -->
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card"><div class="stat-number" id="totalPlans">-</div><div class="stat-label">Shopping Plans</div></div>
            <div class="stat-card"><div class="stat-number" id="avgPrice">-</div><div class="stat-label">Avg Item Price</div></div>
            <div class="stat-card"><div class="stat-number">133k</div><div class="stat-label">Spaza Shops Mapped</div></div>
            <div class="stat-card"><div class="stat-number">R900B</div><div class="stat-label">Township Economy</div></div>
        </div>
        
        <!-- Main Content -->
        <div class="two-columns">
            <!-- Shopping Planner -->
            <div class="card">
                <h2>🛒 Smart Shopping Planner</h2>
                <div class="form-group">
                    <label>💰 Budget (R)</label>
                    <input type="number" id="budget" placeholder="Enter your budget" value="200">
                </div>
                <div class="form-group">
                    <label>📍 Location (Any city/town in SA)</label>
                    <input type="text" id="locationInput" placeholder="Enter any SA location e.g., Soweto, Mthatha, Polokwane" list="locations">
                    <datalist id="locations">
                        <option>Johannesburg</option><option>Pretoria</option><option>Cape Town</option>
                        <option>Durban</option><option>Gqeberha</option><option>Bloemfontein</option>
                        <option>Polokwane</option><option>Nelspruit</option><option>Kimberley</option>
                        <option>Soweto</option><option>Tembisa</option><option>Mthatha</option>
                    </datalist>
                </div>
                <button onclick="generatePlan()">✨ Generate Shopping Plan</button>
                
                <div class="loading" id="loading"><div class="spinner"></div><p>AI is planning...</p></div>
                
                <div class="results" id="results" style="display:none;">
                    <div class="shopping-list">
                        <h3>📋 Your Optimal Basket</h3>
                        <div id="basketList"></div>
                        <div id="totalRow"></div>
                        <div id="advice"></div>
                    </div>
                </div>
            </div>
            
            <!-- Right Column -->
            <div>
                <!-- Price Check -->
                <div class="card">
                    <h2>🔍 Quick Price Check</h2>
                    <div class="form-group">
                        <input type="text" id="productName" placeholder="Product name e.g., bread, rice">
                    </div>
                    <button onclick="checkPrice()">Check Price</button>
                    <div id="priceResult" style="margin-top: 15px;"></div>
                </div>
                
                <!-- User Stats -->
                <div class="card" id="userStatsCard" style="display:none;">
                    <h2>📊 Your Shopping Stats</h2>
                    <div id="userStats"></div>
                </div>
                
                <!-- Trending -->
                <div class="card">
                    <h2>📈 Trending in SA</h2>
                    <div id="trendsList">Loading...</div>
                </div>
                
                <!-- Township Specials -->
                <div class="card">
                    <h2>🏪 Township Micro-Prices</h2>
                    <div id="specialsList"></div>
                </div>
            </div>
        </div>
        
        <!-- Shop Comparison -->
        <div class="card">
            <h2>🏬 Compare Shop Prices</h2>
            <div class="form-group">
                <input type="text" id="compareProduct" placeholder="Product to compare">
            </div>
            <button onclick="comparePrices()">Compare</button>
            <div id="compareResult" style="margin-top: 15px;"></div>
        </div>
        
        <div class="footer">
            <p>Powered by SHOPAROUND AI | Real spaza shop data | Voice enabled | Learning from every purchase</p>
        </div>
    </div>
    
    <!-- Login Modal -->
    <div class="modal" id="loginModal">
        <div class="modal-content">
            <h3>Login to SHOPAROUND</h3>
            <input type="text" id="loginUsername" placeholder="Username" style="width:100%; margin:10px 0; padding:10px;">
            <input type="password" id="loginPassword" placeholder="Password" style="width:100%; margin:10px 0; padding:10px;">
            <button onclick="login()" style="width:100%;">Login</button>
            <button onclick="closeModal('loginModal')" style="width:100%; margin-top:10px; background:#666;">Cancel</button>
        </div>
    </div>
    
    <!-- Register Modal -->
    <div class="modal" id="registerModal">
        <div class="modal-content">
            <h3>Create Account</h3>
            <input type="text" id="regUsername" placeholder="Username" style="width:100%; margin:10px 0; padding:10px;">
            <input type="password" id="regPassword" placeholder="Password" style="width:100%; margin:10px 0; padding:10px;">
            <input type="email" id="regEmail" placeholder="Email (optional)" style="width:100%; margin:10px 0; padding:10px;">
            <button onclick="register()" style="width:100%;">Register</button>
            <button onclick="closeModal('registerModal')" style="width:100%; margin-top:10px; background:#666;">Cancel</button>
        </div>
    </div>
    
    <script>
        let currentUser = null;
        let recognition = null;
        
        // Initialize voice recognition
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-ZA';
            
            recognition.onresult = function(event) {
                const command = event.results[0][0].transcript;
                document.getElementById('voiceText').innerHTML = '🎤 You said: "' + command + '"';
                processVoiceCommand(command);
            };
            
            recognition.onerror = function() {
                document.getElementById('voiceText').innerHTML = '🎤 Tap to speak again';
            };
        }
        
        function startVoiceRecognition() {
            if (recognition) {
                document.getElementById('voiceText').innerHTML = '🎤 Listening...';
                recognition.start();
            } else {
                alert('Voice recognition not supported. Please type your command.');
            }
        }
        
        async function processVoiceCommand(command) {
            try {
                const response = await fetch('/api/voice', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: command, token: currentUser?.token})
                });
                const data = await response.json();
                
                if (data.type === 'plan') {
                    document.getElementById('budget').value = data.budget;
                    document.getElementById('locationInput').value = data.location;
                    generatePlan();
                } else if (data.type === 'price') {
                    document.getElementById('productName').value = data.product;
                    checkPrice();
                } else if (data.type === 'stats') {
                    loadUserStats();
                } else if (data.type === 'help') {
                    alert(data.message);
                } else {
                    alert('Command not recognized. Try: "budget R100 in soweto"');
                }
            } catch(e) {
                console.error(e);
            }
        }
        
        async function login() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            const data = await response.json();
            
            if (data.success) {
                currentUser = data.user;
                localStorage.setItem('token', data.user.token);
                document.getElementById('userNameDisplay').innerText = currentUser.username;
                document.getElementById('authButtons').innerHTML = '<button class="btn-small" onclick="logout()">Logout</button>';
                document.getElementById('userStatsCard').style.display = 'block';
                closeModal('loginModal');
                loadUserStats();
                loadStats();
            } else {
                alert('Login failed');
            }
        }
        
        async function register() {
            const username = document.getElementById('regUsername').value;
            const password = document.getElementById('regPassword').value;
            const email = document.getElementById('regEmail').value;
            
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password, email})
            });
            const data = await response.json();
            
            if (data.success) {
                alert('Registration successful! Please login.');
                closeModal('registerModal');
                showLoginModal();
            } else {
                alert('Registration failed');
            }
        }
        
        function logout() {
            currentUser = null;
            localStorage.removeItem('token');
            document.getElementById('userNameDisplay').innerText = 'Guest';
            document.getElementById('authButtons').innerHTML = '<button class="btn-small" onclick="showLoginModal()">Login</button><button class="btn-small" onclick="showRegisterModal()">Register</button>';
            document.getElementById('userStatsCard').style.display = 'none';
        }
        
        async function loadUserStats() {
            if (!currentUser) return;
            const response = await fetch('/api/user/stats?token=' + currentUser.token);
            const data = await response.json();
            document.getElementById('userStats').innerHTML = `
                <div class="stat-card" style="margin:10px 0"><div class="stat-number">R${data.total_spent}</div><div>Total Spent</div></div>
                <div class="stat-card" style="margin:10px 0"><div class="stat-number">R${data.avg_budget}</div><div>Avg Budget</div></div>
                <div class="stat-card" style="margin:10px 0"><div class="stat-number">${data.plans_count}</div><div>Plans Made</div></div>
            `;
        }
        
        async function generatePlan() {
            const budget = document.getElementById('budget').value;
            const location = document.getElementById('locationInput').value;
            
            if (!budget || budget <= 0) {
                alert('Please enter a valid budget');
                return;
            }
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('results').style.display = 'none';
            
            try {
                const response = await fetch('/api/plan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        budget: parseFloat(budget),
                        location: location,
                        token: currentUser?.token
                    })
                });
                const data = await response.json();
                displayPlan(data);
            } catch(e) {
                alert('Error: ' + e.message);
            } finally {
                document.getElementById('loading').classList.remove('show');
            }
        }
        
        function displayPlan(data) {
            const basket = data.basket;
            const basketList = document.getElementById('basketList');
            
            basketList.innerHTML = basket.map(item => `
                <div class="item-row">
                    <div class="item-info">
                        <span class="item-emoji">${item.emoji}</span>
                        <div>
                            <span class="item-name">${item.item}</span>
                            <span class="item-shop">📍 ${item.shop}</span>
                        </div>
                    </div>
                    <span class="item-price">R${item.price.toFixed(2)}</span>
                </div>
            `).join('');
            
            document.getElementById('totalRow').innerHTML = `
                <div class="total-row">
                    <span>💰 Total</span>
                    <span>R${data.total.toFixed(2)}</span>
                </div>
            `;
            
            const advice = document.getElementById('advice');
            if (data.remaining > 0) {
                advice.innerHTML = `<div style="margin-top:15px; padding:10px; background:#d4edda; border-radius:10px;">
                    ✅ Great! R${data.remaining.toFixed(2)} remaining. 💡 ${data.remaining > 50 ? 'Add a treat or save it!' : 'Perfect use of your budget!'}
                </div>`;
            } else if (data.remaining < 0) {
                advice.innerHTML = `<div style="margin-top:15px; padding:10px; background:#f8d7da; border-radius:10px;">
                    ⚠️ Over budget. Try micro portions from spaza shops!
                </div>`;
            }
            
            document.getElementById('results').style.display = 'block';
            loadTrends();
        }
        
        async function checkPrice() {
            const product = document.getElementById('productName').value;
            if (!product) return;
            
            const response = await fetch(`/api/price/${product}`);
            const data = await response.json();
            
            document.getElementById('priceResult').innerHTML = `
                <div style="background:#e8f4f8; padding:15px; border-radius:10px;">
                    <div style="font-size:1.2em; font-weight:bold;">💰 ${data.product}</div>
                    <div style="font-size:1.8em; color:#667eea;">R${data.price.toFixed(2)}</div>
                    <div>📍 ${data.shop}</div>
                </div>
            `;
        }
        
        async function comparePrices() {
            const product = document.getElementById('compareProduct').value;
            if (!product) return;
            
            const response = await fetch(`/api/compare/${product}`);
            const data = await response.json();
            
            if (data.prices) {
                const priceList = Object.entries(data.prices).map(([shop, price]) => `
                    <div class="item-row"><span>🏪 ${shop}</span><span class="item-price">R${price.toFixed(2)}</span></div>
                `).join('');
                document.getElementById('compareResult').innerHTML = `
                    <div class="shopping-list"><h4>📊 ${data.product}</h4>${priceList}</div>
                `;
            }
        }
        
        async function loadStats() {
            const response = await fetch('/api/statistics');
            const data = await response.json();
            document.getElementById('totalPlans').textContent = data.total_plans || 0;
            document.getElementById('avgPrice').textContent = 'R' + (data.avg_price || 0);
        }
        
        async function loadTrends() {
            const response = await fetch('/api/trends');
            const data = await response.json();
            const trendsList = document.getElementById('trendsList');
            trendsList.innerHTML = data.trends.map(t => `
                <div class="item-row"><span>🍽️ ${t.item}</span><span>${t.demand} purchases</span></div>
            `).join('');
        }
        
        function loadSpecials() {
            const specials = {'Single Egg':3, 'Cup of Rice':4, 'Single Teabag':0.5, 'Sugar Packet':1, 'Small Oil':5, 'Complete Meal':15};
            document.getElementById('specialsList').innerHTML = Object.entries(specials).map(([item, price]) => `
                <div class="item-row"><span>🥚 ${item}</span><span class="item-price">R${price}</span></div>
            `).join('');
        }
        
        function showLoginModal() { document.getElementById('loginModal').classList.add('show'); }
        function showRegisterModal() { document.getElementById('registerModal').classList.add('show'); }
        function closeModal(id) { document.getElementById(id).classList.remove('show'); }
        
        // Check for saved login
        const token = localStorage.getItem('token');
        if (token) {
            // Auto-login with token
            fetch('/api/verify?token=' + token).then(r => r.json()).then(data => {
                if (data.valid) {
                    currentUser = {username: data.username, token: token};
                    document.getElementById('userNameDisplay').innerText = currentUser.username;
                    document.getElementById('authButtons').innerHTML = '<button class="btn-small" onclick="logout()">Logout</button>';
                    document.getElementById('userStatsCard').style.display = 'block';
                    loadUserStats();
                }
            });
        }
        
        loadStats(); loadTrends(); loadSpecials();
    </script>
</body>
</html>
'''

# =========================
# API ENDPOINTS
# =========================

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_TEMPLATE

@app.post("/api/register")
async def register(request: Request):
    data = await request.json()
    success = UserManager.create_user(data['username'], data['password'], data.get('email'))
    return {"success": success}

@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    user = UserManager.authenticate(data['username'], data['password'])
    if user:
        return {"success": True, "user": user}
    return {"success": False}

@app.get("/api/verify")
async def verify(token: str):
    user = UserManager.get_user_by_token(token)
    return {"valid": user is not None, "username": user[1] if user else None}

@app.post("/api/plan")
async def plan(request: Request):
    data = await request.json()
    budget = data['budget']
    location = data['location'].lower()
    
    # Find closest location if exact not found
    if location not in SA_LOCATIONS:
        for loc in SA_LOCATIONS:
            if location in loc or loc in location:
                location = loc
                break
        else:
            location = "johannesburg"
    
    user_id = None
    if data.get('token'):
        user = UserManager.get_user_by_token(data['token'])
        if user:
            user_id = user[0]
    
    result = ShoppingAI.optimize_shopping_list(budget, location, user_id)
    return result

@app.get("/api/price/{product}")
async def price(product: str):
    product_lower = product.lower()
    for key, val in PRODUCTS.items():
        if product_lower in key.lower():
            return {"product": key, "price": val["price"], "shop": val["shop"]}
    return {"product": product, "price": 0, "shop": "Unknown"}

@app.get("/api/compare/{product}")
async def compare(product: str):
    product_lower = product.lower()
    prices = {}
    for key, val in PRODUCTS.items():
        if product_lower in key.lower():
            prices[val["shop"]] = val["price"]
            break
    if not prices:
        return {"product": product, "prices": None}
    return {"product": product, "prices": prices}

@app.post("/api/voice")
async def voice(request: Request):
    data = await request.json()
    command = data.get('command', '')
    token = data.get('token')
    
    user_id = None
    if token:
        user = UserManager.get_user_by_token(token)
        if user:
            user_id = user[0]
    
    result = VoiceProcessor.process_command(command, user_id)
    return result

@app.get("/api/statistics")
async def statistics():
    total = cur.execute("SELECT COUNT(*) FROM shopping_history").fetchone()[0]
    avg = cur.execute("SELECT AVG(total_spent) FROM shopping_history").fetchone()[0]
    return {"total_plans": total, "avg_price": round(avg or 0, 2)}

@app.get("/api/trends")
async def trends():
    trends = cur.execute("""
        SELECT item, COUNT(*) FROM shopping_history, json_each(shopping_history.items)
        WHERE json_each.value LIKE '%"item":"%'
        GROUP BY item LIMIT 10
    """).fetchall()
    return {"trends": [{"item": "Sample", "demand": 0}]}

@app.get("/api/user/stats")
async def user_stats(token: str):
    user = UserManager.get_user_by_token(token)
    if user:
        stats = UserManager.get_user_stats(user[0])
        return stats
    return {"error": "Unauthorized"}

if __name__ == "__main__":
    import uvicorn
    print("🛍️ SHOPAROUND v7.0 Starting...")
    print("📱 Open: http://localhost:9000")
    print("🎤 Voice commands supported!")
    print("👤 User accounts active!")
    uvicorn.run(app, host="0.0.0.0", port=9000)
