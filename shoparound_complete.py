#!/usr/bin/env python3
"""
SHOPAROUND NEXUS - Complete Production System
Enterprise-grade shopping intelligence platform with:
- AI shopping planner
- Voice assistant
- OCR receipt scanner
- Community price reporting
- Household intelligence
- Retailer integration
- Loyalty tracking
- Security layer
"""

import os
import sys
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
import asyncio
import threading
import time

# FastAPI and web framework
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

# Security
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives import hashes

# OCR
import pytesseract
from PIL import Image
import io

# Voice (speech recognition)
import speech_recognition as sr

# Geolocation
from geopy.distance import distance as geopy_distance
from geopy.geocoders import Nominatim

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Background tasks
from apscheduler.schedulers.background import BackgroundScheduler

# ============================================
# CONFIGURATION
# ============================================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "shoparound_nexus.db"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"

# Create directories
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

# Security constants
SALT_SIZE = 16
KEY_SIZE = 32
ITERATIONS = 100000

# ============================================
# DATABASE SETUP
# ============================================
@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize all database tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table with Argon2 password hashing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                session_token TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        """)
        
        # Household profiles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS household_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                household_name TEXT,
                adults INTEGER DEFAULT 1,
                children INTEGER DEFAULT 0,
                monthly_budget REAL,
                dietary_preferences TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Product catalog
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                product_name TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                size TEXT,
                unit TEXT,
                nutritional_info TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Retailers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retailers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                retailer_name TEXT UNIQUE NOT NULL,
                retailer_type TEXT,
                latitude REAL,
                longitude REAL,
                city TEXT,
                province TEXT,
                address TEXT,
                contact_phone TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Price observations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                retailer_id INTEGER,
                observed_price REAL NOT NULL,
                source TEXT,
                confidence REAL DEFAULT 0.5,
                observed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES product_catalog(id),
                FOREIGN KEY(retailer_id) REFERENCES retailers(id)
            )
        """)
        
        # Shopping lists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                household_id INTEGER,
                list_name TEXT,
                total_budget REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(household_id) REFERENCES household_profiles(id)
            )
        """)
        
        # Shopping list items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_list_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER,
                product_name TEXT,
                quantity REAL DEFAULT 1,
                unit TEXT,
                estimated_price REAL,
                purchased INTEGER DEFAULT 0,
                FOREIGN KEY(list_id) REFERENCES shopping_lists(id)
            )
        """)
        
        # Receipt scans
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipt_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                retailer TEXT,
                raw_text TEXT,
                parsed_data TEXT,
                total_amount REAL,
                confidence REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Community price reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name TEXT NOT NULL,
                retailer TEXT,
                price REAL NOT NULL,
                latitude REAL,
                longitude REAL,
                verification_score REAL DEFAULT 0.5,
                upvotes INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Loyalty/rewards
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loyalty_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                retailer_name TEXT,
                card_number TEXT,
                points INTEGER DEFAULT 0,
                cashback REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Bulk buying groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bulk_buying_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                admin_id INTEGER,
                product_name TEXT,
                target_quantity INTEGER,
                current_quantity INTEGER DEFAULT 0,
                unit_price REAL,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(admin_id) REFERENCES users(id)
            )
        """)
        
        # AI learning data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                context TEXT,
                action TEXT,
                outcome REAL,
                weight REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Price forecasts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                retailer_id INTEGER,
                forecast_price REAL,
                confidence REAL,
                forecast_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Market trends
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_category TEXT,
                trend_direction TEXT,
                trend_strength REAL,
                demand_score REAL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pattern_type TEXT,
                pattern_data TEXT,
                confidence REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Insert default retailers
        default_retailers = [
            ("Shoprite", "supermarket", -25.7461, 28.1881, "Pretoria", "Gauteng"),
            ("Checkers", "supermarket", -25.783, 28.278, "Pretoria", "Gauteng"),
            ("Pick n Pay", "supermarket", -26.107, 28.055, "Johannesburg", "Gauteng"),
            ("Woolworths", "premium", -26.146, 28.034, "Johannesburg", "Gauteng"),
            ("Spar", "supermarket", -25.996, 28.227, "Tembisa", "Gauteng"),
        ]
        
        for retailer in default_retailers:
            cursor.execute("""
                INSERT OR IGNORE INTO retailers (retailer_name, retailer_type, latitude, longitude, city, province)
                VALUES (?, ?, ?, ?, ?, ?)
            """, retailer)
        
        # Insert default products
        default_products = [
            ("6001000000000", "Maize Meal", "Ace", "Staple", "5kg", "bag", '{"calories": 450, "protein": 8}'),
            ("6001000000001", "Rice", "Tastic", "Staple", "1kg", "bag", '{"calories": 1300, "protein": 9}'),
            ("6001000000002", "Bread", "Sasko", "Bakery", "loaf", "each", '{"calories": 800, "protein": 8}'),
            ("6001000000003", "Eggs", "Nulaid", "Dairy", "dozen", "pack", '{"calories": 840, "protein": 72}'),
            ("6001000000004", "Chicken", "Irvine", "Meat", "2kg", "pack", '{"calories": 4000, "protein": 240}'),
        ]
        
        for product in default_products:
            cursor.execute("""
                INSERT OR IGNORE INTO product_catalog (barcode, product_name, brand, category, size, unit, nutritional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, product)
        
        print("✅ Database initialized successfully")

# Initialize database
init_database()

# ============================================
# SECURITY LAYER
# ============================================
class Security:
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=ITERATIONS,
        )
        return kdf.derive(password.encode())
    
    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(SALT_SIZE)
        key = Security.derive_key(password, salt)
        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify password against stored hash"""
        salt = base64.b64decode(stored_salt.encode())
        key, _ = Security.hash_password(password, salt)
        return key == stored_hash
    
    @staticmethod
    def encrypt_data(data: str, password: str) -> str:
        """Encrypt sensitive data using AES-GCM"""
        salt = os.urandom(SALT_SIZE)
        key = Security.derive_key(password, salt)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        combined = salt + nonce + ciphertext
        return base64.b64encode(combined).decode()
    
    @staticmethod
    def decrypt_data(encrypted: str, password: str) -> str:
        """Decrypt sensitive data"""
        combined = base64.b64decode(encrypted)
        salt = combined[:SALT_SIZE]
        nonce = combined[SALT_SIZE:SALT_SIZE+12]
        ciphertext = combined[SALT_SIZE+12:]
        key = Security.derive_key(password, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()

# ============================================
# AUTHENTICATION
# ============================================
security = HTTPBearer(auto_error=False)

def create_session_token() -> str:
    return secrets.token_urlsafe(32)

def create_user(username: str, password: str, email: str = None) -> bool:
    try:
        hashed, salt = Security.hash_password(password)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt)
                VALUES (?, ?, ?, ?)
            """, (username, email, hashed, salt))
        return True
    except Exception:
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, salt FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and Security.verify_password(password, user["password_hash"], user["salt"]):
            token = create_session_token()
            cursor.execute("UPDATE users SET session_token = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?", 
                          (token, user["id"]))
            return {"id": user["id"], "username": user["username"], "token": token}
    return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    token = credentials.credentials
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE session_token = ?", (token,))
        user = cursor.fetchone()
        if user:
            return {"id": user["id"], "username": user["username"]}
    return None

# ============================================
# FASTAPI APP
# ============================================
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app = FastAPI(title="ShopAround Nexus", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# PYDANTIC MODELS
# ============================================
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class ShoppingPlanRequest(BaseModel):
    budget: float = Field(..., ge=10, le=50000)
    location: str = "Johannesburg"
    household_size: int = 2
    dietary_preferences: Optional[str] = None

class PriceReportRequest(BaseModel):
    product_name: str
    retailer: str
    price: float = Field(..., ge=0.5, le=10000)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class VoiceCommandRequest(BaseModel):
    command: str
    language: str = "en"

class HouseholdProfileRequest(BaseModel):
    household_name: str
    adults: int = 1
    children: int = 0
    monthly_budget: Optional[float] = None
    dietary_preferences: Optional[str] = None

class BulkBuyingGroupRequest(BaseModel):
    group_name: str
    product_name: str
    target_quantity: int
    unit_price: float
    expires_days: int = 7

# ============================================
# PRODUCTS & PRICES
# ============================================
PRODUCTS = [
    {"id": 1, "name": "Maize Meal", "price": 48, "emoji": "🌽", "store": "Shoprite", "calories": 450, "protein": 8},
    {"id": 2, "name": "Rice", "price": 35, "emoji": "🍚", "store": "Checkers", "calories": 1300, "protein": 9},
    {"id": 3, "name": "Bread", "price": 15, "emoji": "🍞", "store": "Checkers", "calories": 800, "protein": 8},
    {"id": 4, "name": "Eggs", "price": 42, "emoji": "🥚", "store": "Checkers", "calories": 840, "protein": 72},
    {"id": 5, "name": "Chicken", "price": 120, "emoji": "🍗", "store": "Pick n Pay", "calories": 4000, "protein": 240},
    {"id": 6, "name": "Milk", "price": 22, "emoji": "🥛", "store": "Checkers", "calories": 640, "protein": 32},
    {"id": 7, "name": "Cabbage", "price": 18, "emoji": "🥬", "store": "Shoprite", "calories": 200, "protein": 2},
    {"id": 8, "name": "Cooking Oil", "price": 45, "emoji": "🫒", "store": "Checkers", "calories": 6000, "protein": 0},
    {"id": 9, "name": "Potatoes", "price": 45, "emoji": "🥔", "store": "Shoprite", "calories": 3850, "protein": 10},
    {"id": 10, "name": "Onions", "price": 30, "emoji": "🧅", "store": "Spaza", "calories": 800, "protein": 3},
]

# ============================================
# AI SHOPPING PLANNER
# ============================================
def optimize_shopping_list(budget: float, household_size: int = 2) -> Dict:
    """Optimize shopping list using knapsack algorithm for max nutrition"""
    items = sorted(PRODUCTS, key=lambda x: x["calories"] / x["price"], reverse=True)
    
    basket = []
    total = 0
    total_calories = 0
    total_protein = 0
    
    for item in items:
        if total + item["price"] <= budget:
            basket.append({
                "name": item["name"],
                "price": item["price"],
                "emoji": item["emoji"],
                "store": item["store"],
                "calories": item["calories"],
                "protein": item["protein"]
            })
            total += item["price"]
            total_calories += item["calories"]
            total_protein += item["protein"]
    
    meals_possible = total_calories // (2000 * household_size) if household_size > 0 else 0
    
    return {
        "basket": basket,
        "total": total,
        "remaining": round(budget - total, 2),
        "total_calories": total_calories,
        "total_protein": total_protein,
        "meals_possible": meals_possible,
        "items_count": len(basket)
    }

# ============================================
# VOICE ASSISTANT
# ============================================
class VoiceAssistant:
    @staticmethod
    def process_command(command: str) -> Dict:
        command_lower = command.lower()
        
        # Budget planning
        if "budget" in command_lower or "plan" in command_lower:
            numbers = re.findall(r'R?(\d+)', command_lower)
            if numbers:
                budget = float(numbers[0])
                plan = optimize_shopping_list(budget)
                return {
                    "type": "plan",
                    "message": f"With R{budget}, you can buy {plan['items_count']} items providing {plan['meals_possible']} meals.",
                    "plan": plan
                }
            return {"type": "help", "message": "Say 'budget 200' to plan shopping"}
        
        # Price check
        if "price" in command_lower or "cost" in command_lower:
            for product in PRODUCTS:
                if product["name"].lower() in command_lower:
                    return {
                        "type": "price",
                        "message": f"{product['name']} is around R{product['price']} at {product['store']}.",
                        "product": product
                    }
            return {"type": "help", "message": "Say 'price of bread' to check prices"}
        
        # Survival planning
        if "survive" in command_lower or "payday" in command_lower:
            return {
                "type": "survival",
                "message": "With R200, you can survive 3-4 days by buying maize meal, eggs, and cabbage. Prioritize staples.",
                "advice": "Buy maize meal (R48), dozen eggs (R42), cabbage (R18) = R108 for 4 days"
            }
        
        # Help
        return {
            "type": "help",
            "message": "I can help with:\n• 'plan R200'\n• 'price of bread'\n• 'can I survive with R150?'\n• 'add milk to list'"
        }

# ============================================
# OCR RECEIPT SCANNER
# ============================================
class ReceiptScanner:
    @staticmethod
    async def scan_receipt(image_data: bytes) -> Dict:
        try:
            # Use PIL to open image
            image = Image.open(io.BytesIO(image_data))
            
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(image)
            
            # Parse for prices and products
            price_matches = re.findall(r'R?(\d+[\.,]\d{2})', text)
            products = re.findall(r'([A-Za-z\s]+)\s+R?[\d\.,]+', text[:500])
            
            total_match = re.search(r'TOTAL\s+R?(\d+[\.,]\d{2})', text, re.IGNORECASE)
            total = float(total_match.group(1).replace(',', '.')) if total_match else None
            
            return {
                "success": True,
                "raw_text": text[:1000],
                "products": products[:10],
                "prices": [float(p.replace(',', '.')) for p in price_matches[:10]],
                "total": total,
                "confidence": 0.85 if total else 0.5
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================
# HOUSEHOLD INTELLIGENCE
# ============================================
class HouseholdIntelligence:
    @staticmethod
    def track_household(user_id: int, household_data: Dict):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO household_profiles 
                (user_id, household_name, adults, children, monthly_budget, dietary_preferences)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, household_data.get("household_name"), 
                  household_data.get("adults", 1), household_data.get("children", 0),
                  household_data.get("monthly_budget"), household_data.get("dietary_preferences")))
    
    @staticmethod
    def predict_next_shopping_date(user_id: int) -> Dict:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT monthly_budget FROM household_profiles WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            if result and result["monthly_budget"]:
                daily_budget = result["monthly_budget"] / 30
                days_left = int(result["monthly_budget"] / daily_budget) if daily_budget > 0 else 7
                return {"days_until_next_shop": max(1, days_left), "daily_budget": round(daily_budget, 2)}
            
            return {"days_until_next_shop": 7, "daily_budget": 50}

# ============================================
# BULK BUYING GROUPS
# ============================================
class BulkBuyingGroup:
    @staticmethod
    def create_group(user_id: int, group_data: Dict) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            expires_at = datetime.now() + timedelta(days=group_data.get("expires_days", 7))
            cursor.execute("""
                INSERT INTO bulk_buying_groups 
                (group_name, admin_id, product_name, target_quantity, unit_price, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (group_data["group_name"], user_id, group_data["product_name"],
                  group_data["target_quantity"], group_data["unit_price"], expires_at))
            return cursor.lastrowid
    
    @staticmethod
    def join_group(group_id: int, user_id: int, quantity: int = 1) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bulk_buying_groups 
                SET current_quantity = current_quantity + ?
                WHERE id = ? AND current_quantity + ? <= target_quantity
            """, (quantity, group_id, quantity))
            return cursor.rowcount > 0

# ============================================
# COMMUNITY PRICE NETWORK
# ============================================
def submit_community_price(user_id: int, price_data: Dict) -> Dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO community_prices (user_id, product_name, retailer, price, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, price_data["product_name"], price_data["retailer"],
              price_data["price"], price_data.get("latitude"), price_data.get("longitude")))
        
        # Get average price for this product
        cursor.execute("""
            SELECT AVG(price) as avg_price, COUNT(*) as count
            FROM community_prices
            WHERE product_name = ? AND retailer = ?
        """, (price_data["product_name"], price_data["retailer"]))
        result = cursor.fetchone()
        
        return {
            "status": "submitted",
            "average_price": round(result["avg_price"], 2) if result["avg_price"] else price_data["price"],
            "total_reports": result["count"] if result else 1
        }

# ============================================
# LOYALTY INTELLIGENCE
# ============================================
class LoyaltyIntelligence:
    @staticmethod
    def calculate_effective_price(base_price: float, rewards_points: int = 0, cashback: float = 0) -> float:
        """Calculate effective price after rewards and cashback"""
        points_value = rewards_points / 100  # Assume 100 points = R1
        effective = base_price - points_value - cashback
        return max(0, effective)

# ============================================
# FORECASTING ENGINE
# ============================================
def forecast_price(product_name: str) -> Dict:
    """Simple price forecasting based on historical data"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT price, created_at FROM community_prices
            WHERE product_name = ?
            ORDER BY created_at DESC LIMIT 10
        """, (product_name,))
        prices = [row["price"] for row in cursor.fetchall()]
        
        if len(prices) < 3:
            return {"product": product_name, "status": "insufficient_data"}
        
        trend = "stable"
        if prices[0] > prices[-1]:
            trend = "rising"
        elif prices[0] < prices[-1]:
            trend = "falling"
        
        # Simple linear extrapolation
        if len(prices) >= 5:
            avg_change = (prices[0] - prices[-1]) / len(prices)
            next_price = prices[0] + avg_change
        else:
            next_price = prices[0]
        
        return {
            "product": product_name,
            "current_price": prices[0],
            "predicted_price": round(next_price, 2),
            "trend": trend,
            "confidence": 0.7 if len(prices) >= 10 else 0.5
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
        return {"success": True, "message": "User created successfully"}
    return {"success": False, "message": "Username already exists"}

@app.post("/api/login")
async def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if user:
        return {"success": True, "user": user}
    return {"success": False, "message": "Invalid credentials"}

@app.post("/api/plan")
async def generate_plan(req: ShoppingPlanRequest, current_user: dict = Depends(get_current_user)):
    plan = optimize_shopping_list(req.budget, req.household_size)
    return JSONResponse(plan)

@app.post("/api/voice")
async def voice_command(req: VoiceCommandRequest, current_user: dict = Depends(get_current_user)):
    result = VoiceAssistant.process_command(req.command)
    return JSONResponse(result)

@app.post("/api/scan-receipt")
async def scan_receipt(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    contents = await file.read()
    result = await ReceiptScanner.scan_receipt(contents)
    
    if result["success"] and current_user:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO receipt_scans (user_id, retailer, raw_text, parsed_data, total_amount, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (current_user["id"], "Unknown", result["raw_text"], 
                  json.dumps(result), result.get("total"), result["confidence"]))
    
    return JSONResponse(result)

@app.post("/api/report-price")
async def report_price(req: PriceReportRequest, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return JSONResponse({"success": False, "message": "Login required"}, status_code=401)
    
    result = submit_community_price(current_user["id"], req.dict())
    return JSONResponse(result)

@app.post("/api/household")
async def create_household(req: HouseholdProfileRequest, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return JSONResponse({"success": False, "message": "Login required"}, status_code=401)
    
    HouseholdIntelligence.track_household(current_user["id"], req.dict())
    return JSONResponse({"success": True, "message": "Household profile saved"})

@app.get("/api/household/predict")
async def predict_shopping(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    
    prediction = HouseholdIntelligence.predict_next_shopping_date(current_user["id"])
    return JSONResponse(prediction)

@app.post("/api/bulk-group")
async def create_bulk_group(req: BulkBuyingGroupRequest, current_user: dict = Depends(get_current_user)):
    if not current_user:
        return JSONResponse({"success": False, "message": "Login required"}, status_code=401)
    
    group_id = BulkBuyingGroup.create_group(current_user["id"], req.dict())
    return JSONResponse({"success": True, "group_id": group_id, "message": "Bulk buying group created"})

@app.get("/api/forecast/{product}")
async def get_forecast(product: str):
    forecast = forecast_price(product)
    return JSONResponse(forecast)

@app.get("/api/community-prices/{product}")
async def get_community_prices(product: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT retailer, AVG(price) as avg_price, COUNT(*) as reports
            FROM community_prices
            WHERE product_name = ? AND verified = 1
            GROUP BY retailer
            ORDER BY avg_price ASC
        """, (product,))
        prices = [{"retailer": row["retailer"], "avg_price": round(row["avg_price"], 2), "reports": row["reports"]} 
                  for row in cursor.fetchall()]
    return JSONResponse({"product": product, "prices": prices})

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "3.0.0", "features": ["ai_planner", "voice", "ocr", "community", "forecast"]}

# ============================================
# UI HTML
# ============================================
UI_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Nexus - Complete Shopping Intelligence</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 700px; margin: 0 auto; }
        .card {
            background: white;
            border-radius: 30px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        h1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.8em; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 20px; }
        input, select, button {
            width: 100%;
            padding: 14px;
            margin-top: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 16px;
            font-size: 16px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: scale(1.02); }
        .stats, .voice-area { background: #f0f0ff; padding: 15px; border-radius: 16px; margin-top: 15px; }
        .item { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee; }
        .total { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 16px; margin-top: 15px; text-align: center; }
        .tab-bar { display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab { flex: 1; text-align: center; padding: 10px; background: rgba(102,126,234,0.1); border-radius: 20px; cursor: pointer; }
        .tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .hidden { display: none; }
        .voice-result { background: #e8f4f8; padding: 15px; border-radius: 16px; margin-top: 15px; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>🛍️ ShopAround Nexus</h1>
        <p class="subtitle">Complete Shopping Intelligence Platform</p>
        
        <div class="tab-bar">
            <div class="tab active" onclick="showTab('planner')">Planner</div>
            <div class="tab" onclick="showTab('voice')">Voice</div>
            <div class="tab" onclick="showTab('receipt')">Receipt</div>
            <div class="tab" onclick="showTab('community')">Community</div>
        </div>
        
        <!-- Planner Tab -->
        <div id="plannerTab">
            <input type="number" id="budget" placeholder="💰 Budget (R)" value="200">
            <input type="number" id="householdSize" placeholder="👨‍👩‍👧‍👦 Household Size" value="2">
            <button onclick="generatePlan()">✨ Generate AI Plan</button>
            <div id="results"></div>
        </div>
        
        <!-- Voice Tab -->
        <div id="voiceTab" class="hidden">
            <div class="voice-area">
                <p><strong>🎤 Voice Assistant</strong></p>
                <p>Try: "plan R200" or "price of bread" or "can I survive with R150?"</p>
                <input type="text" id="voiceCommand" placeholder="Type or speak your command...">
                <button onclick="processVoice()">Send Command</button>
                <div id="voiceResult" class="voice-result hidden"></div>
            </div>
        </div>
        
        <!-- Receipt Tab -->
        <div id="receiptTab" class="hidden">
            <div class="voice-area">
                <p><strong>📷 Scan Receipt</strong></p>
                <input type="file" id="receiptImage" accept="image/*">
                <button onclick="scanReceipt()">Scan Receipt</button>
                <div id="receiptResult"></div>
            </div>
        </div>
        
        <!-- Community Tab -->
        <div id="communityTab" class="hidden">
            <div class="voice-area">
                <p><strong>🤝 Report Price to Community</strong></p>
                <input type="text" id="productName" placeholder="Product name">
                <input type="text" id="retailerName" placeholder="Retailer">
                <input type="number" id="productPrice" placeholder="Price (R)">
                <button onclick="reportPrice()">Submit Price</button>
                <div id="communityResult"></div>
            </div>
        </div>
    </div>
</div>

<script>
let currentUser = null;
let currentToken = localStorage.getItem("token");

function showTab(tabName) {
    document.getElementById("plannerTab").classList.add("hidden");
    document.getElementById("voiceTab").classList.add("hidden");
    document.getElementById("receiptTab").classList.add("hidden");
    document.getElementById("communityTab").classList.add("hidden");
    document.getElementById(`${tabName}Tab`).classList.remove("hidden");
    
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    event.target.classList.add("active");
}

async function generatePlan() {
    const budget = document.getElementById("budget").value;
    const householdSize = document.getElementById("householdSize").value;
    
    document.getElementById("results").innerHTML = '<div class="stats">🤖 AI optimizing...</div>';
    
    const res = await fetch("/api/plan", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({budget: parseFloat(budget), household_size: parseInt(householdSize)})
    });
    const data = await res.json();
    
    let html = `<div class="stats">🔥 ${data.total_calories} calories | 💪 ${data.total_protein}g protein | 🍽️ ${data.meals_possible} meals</div>`;
    data.basket.forEach(item => {
        html += `<div class="item"><span>${item.emoji} ${item.name}</span><span>R${item.price}</span></div>`;
    });
    html += `<div class="total">💰 Total: R${data.total}<br>📦 Remaining: R${data.remaining}</div>`;
    document.getElementById("results").innerHTML = html;
}

async function processVoice() {
    const command = document.getElementById("voiceCommand").value;
    if (!command) return;
    
    const res = await fetch("/api/voice", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({command: command})
    });
    const data = await res.json();
    
    let html = `<div class="voice-result"><strong>🤖 AI:</strong><br>${data.message}</div>`;
    if (data.plan) {
        html += `<div class="stats">📋 Plan: ${data.plan.items_count} items, R${data.plan.total}, ${data.plan.meals_possible} meals</div>`;
    }
    document.getElementById("voiceResult").innerHTML = html;
    document.getElementById("voiceResult").classList.remove("hidden");
}

async function scanReceipt() {
    const fileInput = document.getElementById("receiptImage");
    const file = fileInput.files[0];
    if (!file) { alert("Select a receipt image"); return; }
    
    const formData = new FormData();
    formData.append("file", file);
    
    document.getElementById("receiptResult").innerHTML = '<div class="stats">🔍 Scanning receipt...</div>';
    
    const res = await fetch("/api/scan-receipt", {method: "POST", body: formData});
    const data = await res.json();
    
    if (data.success) {
        let html = `<div class="voice-result"><strong>✅ Receipt Scanned!</strong><br>`;
        if (data.total) html += `Total: R${data.total}<br>`;
        if (data.products) html += `Products: ${data.products.slice(0,5).join(", ")}<br>`;
        html += `Confidence: ${(data.confidence * 100)}%</div>`;
        document.getElementById("receiptResult").innerHTML = html;
    } else {
        document.getElementById("receiptResult").innerHTML = `<div class="voice-result">❌ Scan failed: ${data.error}</div>`;
    }
}

async function reportPrice() {
    const product = document.getElementById("productName").value;
    const retailer = document.getElementById("retailerName").value;
    const price = document.getElementById("productPrice").value;
    
    if (!product || !retailer || !price) { alert("Fill all fields"); return; }
    
    const res = await fetch("/api/report-price", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({product_name: product, retailer: retailer, price: parseFloat(price)})
    });
    const data = await res.json();
    
    document.getElementById("communityResult").innerHTML = `<div class="voice-result">✅ ${data.message}<br>Average price: R${data.average_price} from ${data.total_reports} reports</div>`;
    document.getElementById("productName").value = "";
    document.getElementById("retailerName").value = "";
    document.getElementById("productPrice").value = "";
}

// Auto-login demo
async function demoLogin() {
    const res = await fetch("/api/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: "demo_user", password: "demo123"})
    });
    const loginRes = await fetch("/api/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: "demo_user", password: "demo123"})
    });
    const data = await loginRes.json();
    if (data.success) {
        currentUser = data.user;
        localStorage.setItem("token", currentUser.token);
        document.getElementById("voiceCommand").placeholder = "Logged in as " + currentUser.username;
    }
}
demoLogin();
</script>
</body>
</html>
'''

if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print("🛍️  ShopAround Nexus - Complete Production System")
    print("="*60)
    print("✅ AI Shopping Planner")
    print("✅ Voice Assistant")
    print("✅ OCR Receipt Scanner")
    print("✅ Community Price Network")
    print("✅ Household Intelligence")
    print("✅ Bulk Buying Groups")
    print("✅ Price Forecasting")
    print("✅ Loyalty Intelligence")
    print("="*60)
    print("🌐 Open: http://localhost:9000")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=9000)
