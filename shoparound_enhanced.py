"""
ShopAround Online Mall - Enhanced Version
Features:
- User authentication with sessions
- Multiple shopping lists per user
- Advanced basket optimization with mixed-store shopping
- Nutritional tracking
- Price history and alerts
- Household sharing
- Order history
- Wishlists
- Price comparison charts
- Delivery time optimization
- Budget planning
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SESSION_TYPE"] = "filesystem"
app.permanent_session_lifetime = timedelta(days=7)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------------------------------------------------
# Enhanced Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    household_id INTEGER,
    budget_limit REAL DEFAULT 0,
    preferred_store_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS households (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    created_by INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS product_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    emoji TEXT DEFAULT '🛒',
    calories INTEGER,
    protein REAL,
    carbs REAL,
    fat REAL,
    fiber REAL,
    unit TEXT DEFAULT 'piece',
    typical_quantity REAL DEFAULT 1,
    barcode TEXT UNIQUE,
    image_url TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(product_name)
);

CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    location TEXT,
    latitude REAL,
    longitude REAL,
    delivery_fee REAL DEFAULT 0,
    free_delivery_min REAL DEFAULT 0,
    delivery_minutes INTEGER DEFAULT 60,
    rating REAL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    opening_time TEXT DEFAULT '08:00',
    closing_time TEXT DEFAULT '20:00'
);

CREATE TABLE IF NOT EXISTS store_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES product_catalog(id) ON DELETE CASCADE,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    price REAL NOT NULL,
    previous_price REAL,
    discount_percent REAL DEFAULT 0,
    in_stock INTEGER DEFAULT 1,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(product_id, store_id)
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    price REAL NOT NULL,
    recorded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (product_id, store_id) REFERENCES store_prices(product_id, store_id)
);

CREATE TABLE IF NOT EXISTS shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT DEFAULT 'My List',
    is_active INTEGER DEFAULT 1,
    total_budget REAL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shopping_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL REFERENCES shopping_lists(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES product_catalog(id) ON DELETE CASCADE,
    quantity REAL DEFAULT 1,
    unit TEXT DEFAULT 'piece',
    priority INTEGER DEFAULT 1,
    added_by INTEGER REFERENCES users(id),
    checked_off INTEGER DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(list_id, product_id)
);

CREATE TABLE IF NOT EXISTS wishlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT DEFAULT 'My Wishlist',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS wishlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wishlist_id INTEGER NOT NULL REFERENCES wishlists(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES product_catalog(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 1,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    list_id INTEGER REFERENCES shopping_lists(id),
    store_id INTEGER REFERENCES stores(id),
    total_amount REAL NOT NULL,
    delivery_fee REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    ordered_at TEXT DEFAULT (datetime('now')),
    delivered_at TEXT,
    tracking_number TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES product_catalog(id),
    quantity REAL NOT NULL,
    price_at_time REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS price_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES product_catalog(id),
    target_price REAL NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    theme TEXT DEFAULT 'light',
    notifications INTEGER DEFAULT 1,
    preferred_delivery_time TEXT,
    dietary_restrictions TEXT
);

CREATE INDEX idx_prices_product ON store_prices(product_id);
CREATE INDEX idx_prices_store ON store_prices(store_id);
CREATE INDEX idx_list_items_list ON shopping_list_items(list_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_price_history_product ON price_history(product_id, store_id);
"""

# ---------------------------------------------------------------------------
# Enhanced Seed Data
# ---------------------------------------------------------------------------

SEED_PRODUCTS = [
    ("Bread 700g White", "Bakery", "Bread", "🍞", 1750, 9.0, 350, 5.0, 15.0, "loaf", 1),
    ("Milk 1L Full Cream", "Dairy", "Milk", "🥛", 640, 32.0, 48, 34.0, 0, "liter", 1),
    ("Rice 2kg", "Pantry", "Grains", "🍚", 7280, 14.0, 1600, 6.0, 20.0, "kg", 2),
    ("Chicken Breast 1kg", "Meat", "Poultry", "🍗", 1650, 310.0, 0, 37.0, 0, "kg", 1),
    ("Tomatoes 1kg", "Vegetables", "Fresh", "🍅", 180, 9.0, 39, 2.0, 12.0, "kg", 1),
    ("Eggs 12 pack", "Dairy", "Eggs", "🥚", 780, 78.0, 6, 54.0, 0, "pack", 12),
    ("Sugar 2kg", "Pantry", "Sweeteners", "🍬", 7720, 0.0, 1996, 0, 0, "kg", 2),
    ("Cooking Oil 750ml", "Pantry", "Oils", "🛢️", 6750, 0.0, 0, 765, 0, "ml", 750),
    ("Dog Food 2kg", "Pet", "Food", "🐶", 0, 0.0, 400, 120, 80, "kg", 2),
    ("Toothpaste 100ml", "Health", "Oral Care", "🪥", 0, 0.0, 0, 0, 0, "ml", 100),
    ("Apples 1kg", "Fruits", "Fresh", "🍎", 520, 2.6, 138, 1.7, 24, "kg", 1),
    ("Bananas 1kg", "Fruits", "Fresh", "🍌", 890, 10.9, 229, 3.3, 26, "kg", 1),
    ("Coffee 250g", "Beverages", "Hot Drinks", "☕", 25, 3.0, 0, 0, 0, "g", 250),
    ("Tea 100 bags", "Beverages", "Hot Drinks", "🍵", 0, 0, 0, 0, 0, "pack", 100),
]

SEED_STORES = [
    ("Shoprite Pretoria", "Pretoria CBD", -25.746, 28.188, 35.0, 500, 90, 4.2),
    ("Checkers Centurion", "Centurion", -25.861, 28.189, 40.0, 600, 60, 4.5),
    ("Pick n Pay Hatfield", "Hatfield", -25.754, 28.234, 30.0, 400, 75, 4.3),
    ("Makro Silverlakes", "Silverlakes", -25.800, 28.333, 50.0, 750, 120, 4.4),
    ("Woolworths Menlyn", "Menlyn", -25.780, 28.275, 45.0, 500, 45, 4.7),
    ("Food Lovers Market", "Faerie Glen", -25.785, 28.295, 25.0, 300, 35, 4.6),
]

SEED_PRICES = [
    ("Bread 700g White", "Shoprite Pretoria", 18.99, 19.99, 5),
    ("Bread 700g White", "Checkers Centurion", 19.50, 20.50, 2.4),
    ("Bread 700g White", "Pick n Pay Hatfield", 17.99, 18.99, 5.3),
    ("Bread 700g White", "Woolworths Menlyn", 24.99, 26.99, 7.4),
    ("Milk 1L Full Cream", "Shoprite Pretoria", 21.99, 22.50, 2.3),
    ("Milk 1L Full Cream", "Food Lovers Market", 20.99, 21.50, 2.4),
    ("Rice 2kg", "Makro Silverlakes", 44.50, 49.99, 11),
    ("Chicken Breast 1kg", "Food Lovers Market", 85.99, 89.99, 4.4),
    ("Apples 1kg", "Food Lovers Market", 29.99, 34.99, 14.3),
    ("Coffee 250g", "Woolworths Menlyn", 89.99, 95.00, 5.3),
]

# ---------------------------------------------------------------------------
# Advanced Basket Optimization
# ---------------------------------------------------------------------------

def optimize_basket_advanced(list_id, max_stores=3, include_delivery=True, optimize_for="price"):
    """
    Advanced optimization supporting:
    - Multi-store shopping (split basket across multiple stores)
    - Delivery fee considerations
    - Time optimization
    - Budget constraints
    - Store ratings
    """
    db = get_db()
    
    items = db.execute("""
        SELECT sli.product_id, sli.quantity, sli.priority,
               pc.product_name, pc.emoji, pc.unit, pc.typical_quantity
        FROM shopping_list_items sli
        JOIN product_catalog pc ON pc.id = sli.product_id
        WHERE sli.list_id = ? AND sli.checked_off = 0
    """, (list_id,)).fetchall()
    
    if not items:
        return {"error": "List is empty", "items": []}
    
    stores = db.execute("""
        SELECT id, name, delivery_fee, free_delivery_min, delivery_minutes, rating
        FROM stores WHERE is_active = 1
    """).fetchall()
    
    # Build price matrix
    price_matrix = {}
    for item in items:
        rows = db.execute("""
            SELECT store_id, price, discount_percent, in_stock
            FROM store_prices WHERE product_id = ? AND in_stock = 1
        """, (item["product_id"],)).fetchall()
        price_matrix[item["product_id"]] = {r["store_id"]: r for r in rows}
    
    # Find optimal multi-store combination
    best_combinations = find_optimal_store_combination(
        items, stores, price_matrix, max_stores, include_delivery, optimize_for
    )
    
    # Get price alerts for user
    user_id = db.execute(
        "SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)
    ).fetchone()
    price_alerts = []
    if user_id:
        price_alerts = db.execute("""
            SELECT pa.*, pc.product_name 
            FROM price_alerts pa
            JOIN product_catalog pc ON pc.id = pa.product_id
            WHERE pa.user_id = ? AND pa.is_active = 1
        """, (user_id[0],)).fetchall()
    
    return {
        "items": [dict(item) for item in items],
        "optimal_combinations": best_combinations,
        "price_alerts": [dict(alert) for alert in price_alerts],
        "recommendation": generate_recommendation(best_combinations),
        "health_metrics": calculate_health_metrics(items, price_matrix)
    }

def find_optimal_store_combination(items, stores, price_matrix, max_stores, include_delivery, optimize_for):
    """Brute-force optimization for small baskets, heuristic for larger ones"""
    if len(items) <= 8:  # Use brute force for small baskets
        return brute_force_optimization(items, stores, price_matrix, max_stores, include_delivery)
    else:
        return heuristic_optimization(items, stores, price_matrix, max_stores, include_delivery)

def brute_force_optimization(items, stores, price_matrix, max_stores, include_delivery):
    combinations = []
    store_ids = [s["id"] for s in stores]
    
    # Try 1 store first
    for store_id in store_ids:
        total = 0
        complete = True
        for item in items:
            if item["product_id"] not in price_matrix or store_id not in price_matrix[item["product_id"]]:
                complete = False
                break
            total += price_matrix[item["product_id"]][store_id]["price"] * item["quantity"]
        if complete:
            delivery_fee = get_delivery_fee(store_id, total, stores) if include_delivery else 0
            combinations.append({
                "stores": [store_id],
                "store_names": [get_store_name(store_id, stores)],
                "subtotal": round(total, 2),
                "delivery_fee": delivery_fee,
                "total": round(total + delivery_fee, 2),
                "store_count": 1
            })
    
    # Try 2 stores for better prices
    if max_stores >= 2 and len(stores) >= 2:
        for i, store1 in enumerate(store_ids):
            for store2 in store_ids[i+1:]:
                total = 0
                assignment = {}
                for item in items:
                    pid = item["product_id"]
                    if pid not in price_matrix:
                        total = float('inf')
                        break
                    price1 = price_matrix[pid].get(store1, {}).get("price", float('inf'))
                    price2 = price_matrix[pid].get(store2, {}).get("price", float('inf'))
                    if price1 == float('inf') and price2 == float('inf'):
                        total = float('inf')
                        break
                    if price1 <= price2:
                        total += price1 * item["quantity"]
                        assignment[pid] = store1
                    else:
                        total += price2 * item["quantity"]
                        assignment[pid] = store2
                if total != float('inf'):
                    delivery_fee1 = get_delivery_fee(store1, total, stores) if include_delivery else 0
                    delivery_fee2 = get_delivery_fee(store2, total, stores) if include_delivery else 0
                    total_delivery = delivery_fee1 + delivery_fee2
                    combinations.append({
                        "stores": [store1, store2],
                        "store_names": [get_store_name(store1, stores), get_store_name(store2, stores)],
                        "subtotal": round(total, 2),
                        "delivery_fee": round(total_delivery, 2),
                        "total": round(total + total_delivery, 2),
                        "store_count": 2,
                        "assignment": {get_product_name(pid, items): get_store_name(store, stores) 
                                      for pid, store in assignment.items()}
                    })
    
    combinations.sort(key=lambda x: x["total"])
    return combinations[:5]  # Return top 5 combinations

def heuristic_optimization(items, stores, price_matrix, max_stores, include_delivery):
    """Greedy heuristic for large baskets"""
    best_stores = {}
    for item in items:
        pid = item["product_id"]
        if pid in price_matrix:
            best_store = min(price_matrix[pid].items(), 
                           key=lambda x: x[1]["price"])[0]
            best_stores[pid] = best_store
    
    # Group by store
    store_items = {}
    for pid, store_id in best_stores.items():
        if store_id not in store_items:
            store_items[store_id] = []
        store_items[store_id].append(pid)
    
    # Calculate totals
    combinations = []
    for store_id, pids in store_items.items():
        total = sum(price_matrix[pid][store_id]["price"] * 
                   next(i["quantity"] for i in items if i["product_id"] == pid) 
                   for pid in pids)
        delivery_fee = get_delivery_fee(store_id, total, stores) if include_delivery else 0
        combinations.append({
            "stores": [store_id],
            "store_names": [get_store_name(store_id, stores)],
            "subtotal": round(total, 2),
            "delivery_fee": delivery_fee,
            "total": round(total + delivery_fee, 2),
            "store_count": 1,
            "items_count": len(pids)
        })
    
    combinations.sort(key=lambda x: x["total"])
    return combinations[:5]

def get_delivery_fee(store_id, subtotal, stores):
    store = next(s for s in stores if s["id"] == store_id)
    if store["free_delivery_min"] > 0 and subtotal >= store["free_delivery_min"]:
        return 0
    return store["delivery_fee"]

def get_store_name(store_id, stores):
    return next(s["name"] for s in stores if s["id"] == store_id)

def get_product_name(product_id, items):
    return next(i["product_name"] for i in items if i["product_id"] == product_id)

def generate_recommendation(combinations):
    if not combinations:
        return "No optimal combination found. Some items may be out of stock."
    
    best = combinations[0]
    if best["store_count"] == 1:
        return f"✨ Best option: Buy everything from {best['store_names'][0]} for R{best['total']:.2f} (including delivery). This is the most convenient one-stop shop."
    else:
        return f"🛒 Best value: Split your shopping between {', '.join(best['store_names'])}. Total: R{best['total']:.2f}. This saves you money by getting the best price for each item."

def calculate_health_metrics(items, price_matrix):
    """Calculate nutritional information for the basket"""
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    total_fiber = 0
    
    for item in items:
        # Get nutritional info from product catalog
        db = get_db()
        product = db.execute(
            "SELECT calories, protein, carbs, fat, fiber FROM product_catalog WHERE id = ?",
            (item["product_id"],)
        ).fetchone()
        
        if product:
            total_calories += (product["calories"] or 0) * item["quantity"]
            total_protein += (product["protein"] or 0) * item["quantity"]
            total_carbs += (product["carbs"] or 0) * item["quantity"]
            total_fat += (product["fat"] or 0) * item["quantity"]
            total_fiber += (product["fiber"] or 0) * item["quantity"]
    
    return {
        "calories": round(total_calories, 1),
        "protein_g": round(total_protein, 1),
        "carbs_g": round(total_carbs, 1),
        "fat_g": round(total_fat, 1),
        "fiber_g": round(total_fiber, 1),
        "health_score": calculate_health_score(total_calories, total_protein, total_fat, total_fiber)
    }

def calculate_health_score(calories, protein, fat, fiber):
    """Simple health score based on nutritional density"""
    if calories == 0:
        return 50
    protein_ratio = (protein * 4) / calories if calories > 0 else 0
    fiber_ratio = (fiber * 2) / calories if calories > 0 else 0
    fat_ratio = (fat * 9) / calories if calories > 0 else 0
    
    score = (protein_ratio * 30 + fiber_ratio * 30 + (1 - min(fat_ratio, 0.5)) * 40)
    return min(100, max(0, round(score)))

# ---------------------------------------------------------------------------
# User Management Routes
# ---------------------------------------------------------------------------

@app.post("/api/register")
def register():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    
    if not username or not password:
        return jsonify(error="username and password required"), 400
    
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="username or email already exists"), 409
    
    user = db.execute("SELECT id, username, email FROM users WHERE username = ?", (username,)).fetchone()
    return jsonify(dict(user))

@app.post("/api/login")
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
    
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="invalid credentials"), 401
    
    session["user_id"] = user["id"]
    session.permanent = True
    
    db.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user["id"],))
    db.commit()
    
    return jsonify(id=user["id"], username=user["username"], email=user["email"])

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)

@app.get("/api/me")
@login_required
def get_current_user():
    db = get_db()
    user = db.execute("""
        SELECT u.id, u.username, u.email, u.budget_limit, u.household_id,
               h.name as household_name, s.name as preferred_store
        FROM users u
        LEFT JOIN households h ON h.id = u.household_id
        LEFT JOIN stores s ON s.id = u.preferred_store_id
        WHERE u.id = ?
    """, (session["user_id"],)).fetchone()
    
    return jsonify(dict(user))

@app.put("/api/me/preferences")
@login_required
def update_preferences():
    data = request.get_json(force=True)
    db = get_db()
    
    db.execute("""
        INSERT OR REPLACE INTO user_preferences (user_id, theme, notifications, preferred_delivery_time, dietary_restrictions)
        VALUES (?, ?, ?, ?, ?)
    """, (session["user_id"], data.get("theme"), data.get("notifications"), 
          data.get("preferred_delivery_time"), data.get("dietary_restrictions")))
    db.commit()
    
    return jsonify(ok=True)

# ---------------------------------------------------------------------------
# Enhanced Shopping Lists
# ---------------------------------------------------------------------------

@app.post("/api/lists")
@login_required
def create_list():
    data = request.get_json(force=True)
    name = data.get("name", "My List")
    budget = data.get("budget", 0)
    
    db = get_db()
    cur = db.execute(
        "INSERT INTO shopping_lists (user_id, name, total_budget) VALUES (?, ?, ?)",
        (session["user_id"], name, budget)
    )
    db.commit()
    
    return jsonify(id=cur.lastrowid, name=name, budget=budget)

@app.get("/api/lists")
@login_required
def get_user_lists():
    db = get_db()
    rows = db.execute("""
        SELECT sl.*, 
               COUNT(sli.id) as item_count,
               SUM(sli.quantity) as total_items
        FROM shopping_lists sl
        LEFT JOIN shopping_list_items sli ON sli.list_id = sl.id
        WHERE sl.user_id = ? AND sl.is_active = 1
        GROUP BY sl.id
        ORDER BY sl.updated_at DESC
    """, (session["user_id"],)).fetchall()
    
    return jsonify([dict(r) for r in rows])

@app.put("/api/lists/<int:list_id>")
@login_required
def update_list(list_id):
    data = request.get_json(force=True)
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify(error="Unauthorized"), 403
    
    updates = []
    params = []
    if "name" in data:
        updates.append("name = ?")
        params.append(data["name"])
    if "is_active" in data:
        updates.append("is_active = ?")
        params.append(data["is_active"])
    if "total_budget" in data:
        updates.append("total_budget = ?")
        params.append(data["total_budget"])
    
    updates.append("updated_at = datetime('now')")
    params.append(list_id)
    
    db.execute(f"UPDATE shopping_lists SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    
    return jsonify(ok=True)

@app.post("/api/lists/<int:list_id>/items")
@login_required
def add_list_item(list_id):
    data = request.get_json(force=True)
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify(error="Unauthorized"), 403
    
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    priority = data.get("priority", 1)
    notes = data.get("notes", "")
    
    if not product_id:
        # Try to find or create product by name
        product_name = data.get("product_name")
        if product_name:
            product = db.execute(
                "SELECT id FROM product_catalog WHERE product_name LIKE ?", (f"%{product_name}%",)
            ).fetchone()
            if product:
                product_id = product["id"]
            else:
                cur = db.execute(
                    "INSERT INTO product_catalog (product_name, category, emoji) VALUES (?, 'Uncategorized', '🛒')",
                    (product_name,)
                )
                product_id = cur.lastrowid
        else:
            return jsonify(error="product_id or product_name required"), 400
    
    # Check if item already exists
    existing = db.execute(
        "SELECT id, quantity FROM shopping_list_items WHERE list_id = ? AND product_id = ?",
        (list_id, product_id)
    ).fetchone()
    
    if existing:
        new_quantity = existing["quantity"] + quantity
        db.execute(
            "UPDATE shopping_list_items SET quantity = ?, notes = ?, priority = ? WHERE id = ?",
            (new_quantity, notes, priority, existing["id"])
        )
    else:
        db.execute("""
            INSERT INTO shopping_list_items (list_id, product_id, quantity, priority, notes, added_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (list_id, product_id, quantity, priority, notes, session["user_id"]))
    
    # Update list timestamp
    db.execute("UPDATE shopping_lists SET updated_at = datetime('now') WHERE id = ?", (list_id,))
    db.commit()
    
    return jsonify(ok=True)

@app.put("/api/lists/<int:list_id>/items/<int:item_id>/toggle")
@login_required
def toggle_list_item(list_id, item_id):
    db = get_db()
    
    # Verify ownership
    item = db.execute("""
        SELECT sli.* FROM shopping_list_items sli
        JOIN shopping_lists sl ON sl.id = sli.list_id
        WHERE sli.id = ? AND sl.user_id = ?
    """, (item_id, session["user_id"])).fetchone()
    
    if not item:
        return jsonify(error="Item not found"), 404
    
    new_status = 0 if item["checked_off"] else 1
    db.execute(
        "UPDATE shopping_list_items SET checked_off = ? WHERE id = ?",
        (new_status, item_id)
    )
    db.commit()
    
    return jsonify(checked_off=new_status)

@app.delete("/api/lists/<int:list_id>/items/<int:item_id>")
@login_required
def remove_list_item(list_id, item_id):
    db = get_db()
    
    # Verify ownership
    item = db.execute("""
        SELECT sli.* FROM shopping_list_items sli
        JOIN shopping_lists sl ON sl.id = sli.list_id
        WHERE sli.id = ? AND sl.user_id = ?
    """, (item_id, session["user_id"])).fetchone()
    
    if not item:
        return jsonify(error="Item not found"), 404
    
    db.execute("DELETE FROM shopping_list_items WHERE id = ?", (item_id,))
    db.execute("UPDATE shopping_lists SET updated_at = datetime('now') WHERE id = ?", (list_id,))
    db.commit()
    
    return jsonify(ok=True)

@app.post("/api/lists/<int:list_id>/duplicate")
@login_required
def duplicate_list(list_id):
    db = get_db()
    
    # Get original list
    original = db.execute(
        "SELECT name, total_budget FROM shopping_lists WHERE id = ? AND user_id = ?",
        (list_id, session["user_id"])
    ).fetchone()
    
    if not original:
        return jsonify(error="List not found"), 404
    
    # Create new list
    cur = db.execute(
        "INSERT INTO shopping_lists (user_id, name, total_budget) VALUES (?, ?, ?)",
        (session["user_id"], f"{original['name']} (Copy)", original['total_budget'])
    )
    new_list_id = cur.lastrowid
    
    # Copy items
    items = db.execute(
        "SELECT product_id, quantity, priority, notes FROM shopping_list_items WHERE list_id = ?",
        (list_id,)
    ).fetchall()
    
    for item in items:
        db.execute("""
            INSERT INTO shopping_list_items (list_id, product_id, quantity, priority, notes, added_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_list_id, item["product_id"], item["quantity"], 
              item["priority"], item["notes"], session["user_id"]))
    
    db.commit()
    
    return jsonify(id=new_list_id, name=f"{original['name']} (Copy)")

# ---------------------------------------------------------------------------
# Enhanced Catalog and Pricing
# ---------------------------------------------------------------------------

@app.get("/api/products")
def list_products():
    db = get_db()
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    limit = request.args.get("limit", 50, type=int)
    
    query = "SELECT * FROM product_catalog WHERE 1=1"
    params = []
    
    if search:
        query += " AND product_name LIKE ?"
        params.append(f"%{search}%")
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY product_name LIMIT ?"
    params.append(limit)
    
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/categories")
def get_categories():
    db = get_db()
    rows = db.execute("""
        SELECT category, COUNT(*) as count 
        FROM product_catalog 
        GROUP BY category 
        ORDER BY count DESC
    """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    db = get_db()
    product = db.execute(
        "SELECT * FROM product_catalog WHERE id = ?", (product_id,)
    ).fetchone()
    
    if not product:
        return jsonify(error="Product not found"), 404
    
    # Get prices from all stores
    prices = db.execute("""
        SELECT s.id, s.name, sp.price, sp.discount_percent, sp.in_stock,
               s.delivery_fee, s.delivery_minutes
        FROM store_prices sp
        JOIN stores s ON s.id = sp.store_id
        WHERE sp.product_id = ?
        ORDER BY sp.price ASC
    """, (product_id,)).fetchall()
    
    # Get price history
    history = db.execute("""
        SELECT price, recorded_at 
        FROM price_history 
        WHERE product_id = ? 
        ORDER BY recorded_at DESC 
        LIMIT 30
    """, (product_id,)).fetchall()
    
    return jsonify({
        "product": dict(product),
        "prices": [dict(p) for p in prices],
        "price_history": [dict(h) for h in history]
    })

@app.post("/api/products")
@login_required
def add_product():
    data = request.get_json(force=True)
    db = get_db()
    
    try:
        cur = db.execute("""
            INSERT INTO product_catalog (
                product_name, category, subcategory, emoji, calories, 
                protein, carbs, fat, fiber, unit, typical_quantity, barcode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["product_name"], data.get("category"), data.get("subcategory"),
            data.get("emoji", "🛒"), data.get("calories"), data.get("protein"),
            data.get("carbs"), data.get("fat"), data.get("fiber"),
            data.get("unit", "piece"), data.get("typical_quantity", 1),
            data.get("barcode")
        ))
        db.commit()
        
        # Add initial price if provided
        if data.get("price") and data.get("store_id"):
            db.execute("""
                INSERT INTO store_prices (product_id, store_id, price)
                VALUES (?, ?, ?)
            """, (cur.lastrowid, data["store_id"], data["price"]))
            db.commit()
        
        return jsonify(id=cur.lastrowid, product_name=data["product_name"])
    except sqlite3.IntegrityError:
        return jsonify(error="Product already exists or barcode duplicate"), 409

@app.post("/api/prices/update")
@login_required
def update_prices():
    """Update price for a product at a store and record history"""
    data = request.get_json(force=True)
    db = get_db()
    
    product_id = data["product_id"]
    store_id = data["store_id"]
    new_price = data["price"]
    
    # Get current price
    current = db.execute(
        "SELECT price FROM store_prices WHERE product_id = ? AND store_id = ?",
        (product_id, store_id)
    ).fetchone()
    
    if current:
        # Record old price in history
        db.execute("""
            INSERT INTO price_history (product_id, store_id, price)
            VALUES (?, ?, ?)
        """, (product_id, store_id, current["price"]))
        
        # Update current price
        discount = ((current["price"] - new_price) / current["price"] * 100) if new_price < current["price"] else 0
        db.execute("""
            UPDATE store_prices 
            SET price = ?, previous_price = ?, discount_percent = ?, updated_at = datetime('now')
            WHERE product_id = ? AND store_id = ?
        """, (new_price, current["price"], discount, product_id, store_id))
    else:
        db.execute("""
            INSERT INTO store_prices (product_id, store_id, price)
            VALUES (?, ?, ?)
        """, (product_id, store_id, new_price))
    
    db.commit()
    
    # Check price alerts
    alerts = db.execute("""
        SELECT pa.*, u.username, u.email
        FROM price_alerts pa
        JOIN users u ON u.id = pa.user_id
        WHERE pa.product_id = ? AND pa.target_price >= ? AND pa.is_active = 1
    """, (product_id, new_price)).fetchall()
    
    triggered_alerts = []
    for alert in alerts:
        db.execute("UPDATE price_alerts SET is_active = 0 WHERE id = ?", (alert["id"],))
        triggered_alerts.append({
            "user": alert["username"],
            "product_id": product_id,
            "target_price": alert["target_price"],
            "current_price": new_price
        })
    
    db.commit()
    
    return jsonify({
        "ok": True,
        "triggered_alerts": triggered_alerts
    })

# ---------------------------------------------------------------------------
# Price Alerts
# ---------------------------------------------------------------------------

@app.post("/api/alerts")
@login_required
def create_price_alert():
    data = request.get_json(force=True)
    db = get_db()
    
    db.execute("""
        INSERT INTO price_alerts (user_id, product_id, target_price)
        VALUES (?, ?, ?)
    """, (session["user_id"], data["product_id"], data["target_price"]))
    db.commit()
    
    return jsonify(ok=True)

@app.get("/api/alerts")
@login_required
def get_price_alerts():
    db = get_db()
    alerts = db.execute("""
        SELECT pa.*, pc.product_name, pc.emoji, sp.price as current_price
        FROM price_alerts pa
        JOIN product_catalog pc ON pc.id = pa.product_id
        LEFT JOIN store_prices sp ON sp.product_id = pa.product_id
        WHERE pa.user_id = ? AND pa.is_active = 1
        ORDER BY pa.created_at DESC
    """, (session["user_id"],)).fetchall()
    
    return jsonify([dict(alert) for alert in alerts])

@app.delete("/api/alerts/<int:alert_id>")
@login_required
def delete_price_alert(alert_id):
    db = get_db()
    db.execute(
        "UPDATE price_alerts SET is_active = 0 WHERE id = ? AND user_id = ?",
        (alert_id, session["user_id"])
    )
    db.commit()
    return jsonify(ok=True)

# ---------------------------------------------------------------------------
# Orders and Checkout
# ---------------------------------------------------------------------------

@app.post("/api/orders")
@login_required
def create_order():
    data = request.get_json(force=True)
    db = get_db()
    
    list_id = data.get("list_id")
    store_id = data.get("store_id")
    
    # Get items from list
    items = db.execute("""
        SELECT sli.product_id, sli.quantity, sp.price
        FROM shopping_list_items sli
        JOIN store_prices sp ON sp.product_id = sli.product_id AND sp.store_id = ?
        WHERE sli.list_id = ? AND sli.checked_off = 0
    """, (store_id, list_id)).fetchall()
    
    if not items:
        return jsonify(error="No items found or store doesn't have all items"), 400
    
    # Calculate total
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    store = db.execute("SELECT delivery_fee FROM stores WHERE id = ?", (store_id,)).fetchone()
    delivery_fee = store["delivery_fee"] if subtotal < 500 else 0  # Free delivery over R500
    total = subtotal + delivery_fee
    
    # Create order
    cur = db.execute("""
        INSERT INTO orders (user_id, list_id, store_id, total_amount, delivery_fee, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session["user_id"], list_id, store_id, total, delivery_fee, "pending"))
    order_id = cur.lastrowid
    
    # Add order items
    for item in items:
        db.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
            VALUES (?, ?, ?, ?)
        """, (order_id, item["product_id"], item["quantity"], item["price"]))
    
    # Mark items as checked off
    db.execute("""
        UPDATE shopping_list_items 
        SET checked_off = 1 
        WHERE list_id = ? AND checked_off = 0
    """, (list_id,))
    
    db.commit()
    
    return jsonify({
        "order_id": order_id,
        "subtotal": round(subtotal, 2),
        "delivery_fee": round(delivery_fee, 2),
        "total": round(total, 2),
        "status": "pending"
    })

@app.get("/api/orders")
@login_required
def get_orders():
    db = get_db()
    orders = db.execute("""
        SELECT o.*, s.name as store_name, sl.name as list_name
        FROM orders o
        LEFT JOIN stores s ON s.id = o.store_id
        LEFT JOIN shopping_lists sl ON sl.id = o.list_id
        WHERE o.user_id = ?
        ORDER BY o.ordered_at DESC
        LIMIT 50
    """, (session["user_id"],)).fetchall()
    
    return jsonify([dict(order) for order in orders])

@app.get("/api/orders/<int:order_id>")
@login_required
def get_order(order_id):
    db = get_db()
    order = db.execute("""
        SELECT o.*, s.name as store_name, s.location, sl.name as list_name
        FROM orders o
        LEFT JOIN stores s ON s.id = o.store_id
        LEFT JOIN shopping_lists sl ON sl.id = o.list_id
        WHERE o.id = ? AND o.user_id = ?
    """, (order_id, session["user_id"])).fetchone()
    
    if not order:
        return jsonify(error="Order not found"), 404
    
    items = db.execute("""
        SELECT oi.*, pc.product_name, pc.emoji
        FROM order_items oi
        JOIN product_catalog pc ON pc.id = oi.product_id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()
    
    return jsonify({
        "order": dict(order),
        "items": [dict(item) for item in items]
    })

# ---------------------------------------------------------------------------
# Household Management
# ---------------------------------------------------------------------------

@app.post("/api/households")
@login_required
def create_household():
    data = request.get_json(force=True)
    db = get_db()
    
    cur = db.execute(
        "INSERT INTO households (name, created_by) VALUES (?, ?)",
        (data["name"], session["user_id"])
    )
    household_id = cur.lastrowid
    
    db.execute(
        "UPDATE users SET household_id = ? WHERE id = ?",
        (household_id, session["user_id"])
    )
    db.commit()
    
    return jsonify(id=household_id, name=data["name"])

@app.post("/api/households/<int:household_id>/invite")
@login_required
def invite_to_household(household_id):
    data = request.get_json(force=True)
    db = get_db()
    
    # Check if user is household admin
    household = db.execute(
        "SELECT created_by FROM households WHERE id = ?",
        (household_id,)
    ).fetchone()
    
    if not household or household["created_by"] != session["user_id"]:
        return jsonify(error="Unauthorized"), 403
    
    # Add user to household
    db.execute(
        "UPDATE users SET household_id = ? WHERE username = ? OR email = ?",
        (household_id, data.get("username"), data.get("email"))
    )
    db.commit()
    
    return jsonify(ok=True)

@app.get("/api/households/<int:household_id>/members")
@login_required
def get_household_members(household_id):
    db = get_db()
    members = db.execute("""
        SELECT id, username, email, created_at, last_login
        FROM users
        WHERE household_id = ?
        ORDER BY username
    """, (household_id,)).fetchall()
    
    return jsonify([dict(member) for member in members])

# ---------------------------------------------------------------------------
# Analytics and Insights
# ---------------------------------------------------------------------------

@app.get("/api/analytics/spending")
@login_required
def get_spending_analytics():
    db = get_db()
    days = request.args.get("days", 30, type=int)
    
    # Get spending by store
    store_spending = db.execute("""
        SELECT s.name, SUM(o.total_amount) as total_spent, COUNT(*) as order_count
        FROM orders o
        JOIN stores s ON s.id = o.store_id
        WHERE o.user_id = ? AND o.ordered_at > datetime('now', ?)
        GROUP BY s.id
        ORDER BY total_spent DESC
    """, (session["user_id"], f"-{days} days")).fetchall()
    
    # Get spending over time
    daily_spending = db.execute("""
        SELECT DATE(o.ordered_at) as date, SUM(o.total_amount) as daily_total
        FROM orders o
        WHERE o.user_id = ? AND o.ordered_at > datetime('now', ?)
        GROUP BY DATE(o.ordered_at)
        ORDER BY date DESC
        LIMIT 30
    """, (session["user_id"], f"-{days} days")).fetchall()
    
    # Get most purchased products
    top_products = db.execute("""
        SELECT pc.product_name, pc.emoji, SUM(oi.quantity) as total_quantity, 
               COUNT(DISTINCT oi.order_id) as times_ordered
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN product_catalog pc ON pc.id = oi.product_id
        WHERE o.user_id = ? AND o.ordered_at > datetime('now', ?)
        GROUP BY oi.product_id
        ORDER BY total_quantity DESC
        LIMIT 10
    """, (session["user_id"], f"-{days} days")).fetchall()
    
    return jsonify({
        "store_spending": [dict(s) for s in store_spending],
        "daily_spending": [dict(d) for d in daily_spending],
        "top_products": [dict(p) for p in top_products],
        "total_spent": sum(s["total_spent"] for s in store_spending),
        "average_order": sum(s["total_spent"] for s in store_spending) / len(store_spending) if store_spending else 0
    })

# ---------------------------------------------------------------------------
# Enhanced Frontend
# ---------------------------------------------------------------------------

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ShopAround - Smart Grocery Shopping</title>
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
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
  }
  
  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
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
  
  .navbar h1 {
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .nav-links {
    display: flex;
    gap: 1rem;
  }
  
  .nav-links a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: background 0.2s;
  }
  
  .nav-links a:hover {
    background: rgba(255,255,255,0.1);
  }
  
  .container {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 2rem;
  }
  
  .auth-section {
    background: var(--card);
    border-radius: 1rem;
    padding: 2rem;
    max-width: 400px;
    margin: 0 auto;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  }
  
  .auth-section h2 {
    margin-bottom: 1.5rem;
    color: var(--primary);
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  input, textarea, select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    font-size: 1rem;
    transition: border-color 0.2s;
  }
  
  input:focus, textarea:focus, select:focus {
    outline: none;
    border-color: var(--primary);
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
    transition: background 0.2s;
  }
  
  button:hover {
    background: var(--primary-dark);
  }
  
  button.secondary {
    background: var(--secondary);
  }
  
  button.danger {
    background: var(--danger);
  }
  
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
  
  .card-header h2 {
    font-size: 1.25rem;
    color: var(--primary);
  }
  
  .items-list {
    list-style: none;
  }
  
  .items-list li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
  }
  
  .items-list li:last-child {
    border-bottom: none;
  }
  
  .item-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
  }
  
  .item-info .emoji {
    font-size: 1.25rem;
  }
  
  .item-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .badge-success {
    background: #d1fae5;
    color: var(--success);
  }
  
  .badge-warning {
    background: #fed7aa;
    color: var(--warning);
  }
  
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
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
  
  .stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary);
  }
  
  .stat-label {
    font-size: 0.875rem;
    color: var(--text-light);
  }
  
  .tabs {
    display: flex;
    gap: 0.5rem;
    border-bottom: 2px solid var(--border);
    margin-bottom: 1.5rem;
  }
  
  .tab {
    padding: 0.5rem 1rem;
    cursor: pointer;
    border: none;
    background: none;
    color: var(--text-light);
  }
  
  .tab.active {
    color: var(--primary);
    border-bottom: 2px solid var(--primary);
  }
  
  .hidden {
    display: none;
  }
  
  @media (max-width: 768px) {
    .container {
      padding: 0 1rem;
    }
    .navbar {
      padding: 1rem;
    }
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
</head>
<body>
<div class="navbar">
  <h1>🛒 ShopAround</h1>
  <div class="nav-links" id="navLinks">
    <a href="#" onclick="showSection('shopping')">Shopping</a>
    <a href="#" onclick="showSection('analytics')">Analytics</a>
    <a href="#" onclick="showSection('alerts')">Price Alerts</a>
    <a href="#" onclick="showSection('orders')">Orders</a>
    <a href="#" id="logoutBtn" style="display:none;" onclick="logout()">Logout</a>
  </div>
</div>

<div class="container">
  <!-- Auth Section -->
  <div id="authSection" class="auth-section">
    <h2>Welcome to ShopAround</h2>
    <div id="loginForm">
      <div class="form-group">
        <input type="text" id="loginUsername" placeholder="Username or Email">
      </div>
      <div class="form-group">
        <input type="password" id="loginPassword" placeholder="Password">
      </div>
      <button onclick="login()">Login</button>
      <button class="secondary" onclick="showRegister()">Register</button>
      <p id="authMessage" style="margin-top: 1rem; color: var(--danger);"></p>
    </div>
    <div id="registerForm" style="display:none;">
      <div class="form-group">
        <input type="text" id="regUsername" placeholder="Username">
      </div>
      <div class="form-group">
        <input type="email" id="regEmail" placeholder="Email">
      </div>
      <div class="form-group">
        <input type="password" id="regPassword" placeholder="Password">
      </div>
      <button onclick="register()">Register</button>
      <button class="secondary" onclick="showLogin()">Back to Login</button>
    </div>
  </div>

  <!-- Main App Section -->
  <div id="appSection" style="display:none;">
    <div class="stats" id="statsSection">
      <div class="stat-card">
        <div class="stat-value" id="totalSpent">R0</div>
        <div class="stat-label">Total Spent (30 days)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" id="avgOrder">R0</div>
        <div class="stat-label">Average Order</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" id="savings">R0</div>
        <div class="stat-label">Potential Savings</div>
      </div>
    </div>

    <div id="shoppingSection">
      <div class="card">
        <div class="card-header">
          <h2>📝 My Shopping List</h2>
          <button onclick="createNewList()">+ New List</button>
        </div>
        <div id="listsContainer"></div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>➕ Add Items</h2>
        </div>
        <textarea id="bulkItems" rows="3" placeholder="Enter items (one per line):&#10;Bread&#10;Milk&#10;Eggs"></textarea>
        <select id="selectedList" style="margin: 0.5rem 0;"></select>
        <button onclick="addBulkItems()">Add to List</button>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>💡 Smart Optimization</h2>
        </div>
        <select id="optimizeListSelect"></select>
        <button onclick="optimizeBasket()">Find Best Deals</button>
        <div id="optimizationResults" style="margin-top: 1rem;"></div>
      </div>
    </div>

    <div id="analyticsSection" style="display:none;">
      <div class="card">
        <h2>📊 Spending by Store</h2>
        <div id="storeSpending"></div>
      </div>
      <div class="card">
        <h2>🏆 Most Purchased Products</h2>
        <div id="topProducts"></div>
      </div>
    </div>

    <div id="alertsSection" style="display:none;">
      <div class="card">
        <div class="card-header">
          <h2>🔔 Price Alerts</h2>
          <button onclick="showAddAlert()">+ New Alert</button>
        </div>
        <div id="alertsList"></div>
      </div>
    </div>

    <div id="ordersSection" style="display:none;">
      <div class="card">
        <h2>📦 Order History</h2>
        <div id="ordersList"></div>
      </div>
    </div>
  </div>
</div>

<script>
let currentUser = null;
let currentLists = [];
let currentListId = null;

// Authentication
async function login() {
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;
  
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
  });
  
  if (res.ok) {
    const user = await res.json();
    currentUser = user;
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('appSection').style.display = 'block';
    document.getElementById('logoutBtn').style.display = 'inline-block';
    loadDashboard();
  } else {
    const error = await res.json();
    document.getElementById('authMessage').textContent = error.error;
  }
}

async function register() {
  const username = document.getElementById('regUsername').value;
  const email = document.getElementById('regEmail').value;
  const password = document.getElementById('regPassword').value;
  
  const res = await fetch('/api/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, email, password})
  });
  
  if (res.ok) {
    showLogin();
    document.getElementById('authMessage').textContent = 'Registration successful! Please login.';
  } else {
    const error = await res.json();
    document.getElementById('authMessage').textContent = error.error;
  }
}

function logout() {
  fetch('/api/logout', {method: 'POST'});
  currentUser = null;
  document.getElementById('authSection').style.display = 'block';
  document.getElementById('appSection').style.display = 'none';
  document.getElementById('logoutBtn').style.display = 'none';
}

function showRegister() {
  document.getElementById('loginForm').style.display = 'none';
  document.getElementById('registerForm').style.display = 'block';
}

function showLogin() {
  document.getElementById('loginForm').style.display = 'block';
  document.getElementById('registerForm').style.display = 'none';
}

function showSection(section) {
  document.getElementById('shoppingSection').style.display = section === 'shopping' ? 'block' : 'none';
  document.getElementById('analyticsSection').style.display = section === 'analytics' ? 'block' : 'none';
  document.getElementById('alertsSection').style.display = section === 'alerts' ? 'block' : 'none';
  document.getElementById('ordersSection').style.display = section === 'orders' ? 'block' : 'none';
  
  if (section === 'analytics') loadAnalytics();
  if (section === 'alerts') loadAlerts();
  if (section === 'orders') loadOrders();
}

// Dashboard
async function loadDashboard() {
  await loadLists();
  await loadStats();
  updateListSelectors();
}

async function loadStats() {
  const res = await fetch('/api/analytics/spending');
  if (res.ok) {
    const data = await res.json();
    document.getElementById('totalSpent').textContent = `R${data.total_spent.toFixed(2)}`;
    document.getElementById('avgOrder').textContent = `R${data.average_order.toFixed(2)}`;
  }
}

async function loadLists() {
  const res = await fetch('/api/lists');
  if (res.ok) {
    currentLists = await res.json();
    renderLists();
  }
}

function renderLists() {
  const container = document.getElementById('listsContainer');
  if (currentLists.length === 0) {
    container.innerHTML = '<p>No lists yet. Create one!</p>';
    return;
  }
  
  container.innerHTML = '';
  for (const list of currentLists) {
    const listDiv = document.createElement('div');
    listDiv.className = 'card';
    listDiv.innerHTML = `
      <div class="card-header">
        <h3>${escapeHtml(list.name)}</h3>
        <div>
          <button onclick="viewList(${list.id})">View</button>
          <button onclick="duplicateList(${list.id})">Duplicate</button>
        </div>
      </div>
      <p>${list.item_count || 0} items • ${list.total_items || 0} units</p>
      ${list.total_budget ? `<p>Budget: R${list.total_budget}</p>` : ''}
      <div id="list-items-${list.id}"></div>
    `;
    container.appendChild(listDiv);
    loadListItems(list.id);
  }
}

async function loadListItems(listId) {
  const res = await fetch(`/api/lists/${listId}/items`);
  if (res.ok) {
    const items = await res.json();
    const container = document.getElementById(`list-items-${listId}`);
    if (items.length === 0) {
      container.innerHTML = '<p class="text-light">No items yet</p>';
    } else {
      const ul = document.createElement('ul');
      ul.className = 'items-list';
      for (const item of items) {
        const li = document.createElement('li');
        li.innerHTML = `
          <div class="item-info">
            <span class="emoji">${item.emoji}</span>
            <span>${escapeHtml(item.product_name)}</span>
            <span class="badge badge-success">x${item.quantity}</span>
          </div>
          <div class="item-actions">
            <button class="small" onclick="toggleItem(${listId}, ${item.id})">
              ${item.checked_off ? '✓' : '○'}
            </button>
            <button class="small danger" onclick="removeItem(${listId}, ${item.id})">×</button>
          </div>
        `;
        ul.appendChild(li);
      }
      container.innerHTML = '';
      container.appendChild(ul);
    }
  }
}

function updateListSelectors() {
  const select1 = document.getElementById('selectedList');
  const select2 = document.getElementById('optimizeListSelect');
  
  select1.innerHTML = '<option value="">Select a list</option>';
  select2.innerHTML = '<option value="">Select a list</option>';
  
  for (const list of currentLists) {
    select1.innerHTML += `<option value="${list.id}">${escapeHtml(list.name)}</option>`;
    select2.innerHTML += `<option value="${list.id}">${escapeHtml(list.name)}</option>`;
  }
}

async function createNewList() {
  const name = prompt('Enter list name:', 'My Shopping List');
  if (name) {
    const res = await fetch('/api/lists', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name})
    });
    if (res.ok) {
      await loadLists();
      updateListSelectors();
    }
  }
}

async function addBulkItems() {
  const listId = document.getElementById('selectedList').value;
  const text = document.getElementById('bulkItems').value;
  
  if (!listId) {
    alert('Please select a list');
    return;
  }
  
  if (!text.trim()) {
    alert('Please enter items');
    return;
  }
  
  const res = await fetch(`/api/lists/${listId}/text`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text})
  });
  
  if (res.ok) {
    document.getElementById('bulkItems').value = '';
    await loadListItems(listId);
    await loadLists();
  }
}

async function toggleItem(listId, itemId) {
  await fetch(`/api/lists/${listId}/items/${itemId}/toggle`, {method: 'PUT'});
  await loadListItems(listId);
}

async function removeItem(listId, itemId) {
  if (confirm('Remove this item?')) {
    await fetch(`/api/lists/${listId}/items/${itemId}`, {method: 'DELETE'});
    await loadListItems(listId);
    await loadLists();
  }
}

async function duplicateList(listId) {
  await fetch(`/api/lists/${listId}/duplicate`, {method: 'POST'});
  await loadLists();
  updateListSelectors();
}

async function optimizeBasket() {
  const listId = document.getElementById('optimizeListSelect').value;
  if (!listId) {
    alert('Please select a list');
    return;
  }
  
  const res = await fetch(`/api/lists/${listId}/optimize`);
  if (res.ok) {
    const data = await res.json();
    displayOptimization(data);
  }
}

function displayOptimization(data) {
  const container = document.getElementById('optimizationResults');
  
  if (data.error) {
    container.innerHTML = `<p class="text-light">${data.error}</p>`;
    return;
  }
  
  let html = '<h3>Recommendation</h3>';
  html += `<p class="badge badge-success">${data.recommendation}</p>`;
  
  if (data.optimal_combinations && data.optimal_combinations.length > 0) {
    html += '<h3>Best Options</h3>';
    for (const opt of data.optimal_combinations) {
      html += `
        <div style="margin: 1rem 0; padding: 1rem; background: var(--bg); border-radius: 0.5rem;">
          <strong>${opt.store_names.join(' + ')}</strong><br>
          Subtotal: R${opt.subtotal} | Delivery: R${opt.delivery_fee} | Total: R${opt.total}
          ${opt.assignment ? `<br><small>${JSON.stringify(opt.assignment)}</small>` : ''}
        </div>
      `;
    }
  }
  
  if (data.health_metrics) {
    html += '<h3>Health Metrics</h3>';
    html += `<div class="grid">
      <div>🔥 Calories: ${data.health_metrics.calories}</div>
      <div>💪 Protein: ${data.health_metrics.protein_g}g</div>
      <div>🍚 Carbs: ${data.health_metrics.carbs_g}g</div>
      <div>🥑 Fat: ${data.health_metrics.fat_g}g</div>
      <div>🌾 Fiber: ${data.health_metrics.fiber_g}g</div>
      <div>⭐ Health Score: ${data.health_metrics.health_score}/100</div>
    </div>`;
  }
  
  container.innerHTML = html;
}

async function loadAnalytics() {
  const res = await fetch('/api/analytics/spending');
  if (res.ok) {
    const data = await res.json();
    
    // Store spending
    let storeHtml = '<ul class="items-list">';
    for (const store of data.store_spending) {
      storeHtml += `<li>
        <span>${escapeHtml(store.name)}</span>
        <span>R${store.total_spent.toFixed(2)} (${store.order_count} orders)</span>
      </li>`;
    }
    storeHtml += '</ul>';
    document.getElementById('storeSpending').innerHTML = storeHtml;
    
    // Top products
    let productsHtml = '<ul class="items-list">';
    for (const product of data.top_products) {
      productsHtml += `<li>
        <span>${product.emoji} ${escapeHtml(product.product_name)}</span>
        <span>${product.total_quantity} units (${product.times_ordered} orders)</span>
      </li>`;
    }
    productsHtml += '</ul>';
    document.getElementById('topProducts').innerHTML = productsHtml;
  }
}

async function loadAlerts() {
  const res = await fetch('/api/alerts');
  if (res.ok) {
    const alerts = await res.json();
    const container = document.getElementById('alertsList');
    
    if (alerts.length === 0) {
      container.innerHTML = '<p>No price alerts set</p>';
    } else {
      let html = '<ul class="items-list">';
      for (const alert of alerts) {
        html += `<li>
          <span>${alert.emoji} ${escapeHtml(alert.product_name)}</span>
          <span>Alert when price ≤ R${alert.target_price}</span>
          <span>Current: R${alert.current_price || 'N/A'}</span>
          <button class="small" onclick="deleteAlert(${alert.id})">×</button>
        </li>`;
      }
      html += '</ul>';
      container.innerHTML = html;
    }
  }
}

async function deleteAlert(alertId) {
  await fetch(`/api/alerts/${alertId}`, {method: 'DELETE'});
  await loadAlerts();
}

function showAddAlert() {
  const productName = prompt('Enter product name:');
  if (!productName) return;
  
  const targetPrice = parseFloat(prompt('Enter target price (R):'));
  if (isNaN(targetPrice)) return;
  
  // Search for product
  fetch(`/api/products?q=${encodeURIComponent(productName)}`)
    .then(res => res.json())
    .then(products => {
      if (products.length === 0) {
        alert('Product not found');
        return;
      }
      
      const product = products[0];
      fetch('/api/alerts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: product.id, target_price: targetPrice})
      }).then(() => {
        loadAlerts();
      });
    });
}

async function loadOrders() {
  const res = await fetch('/api/orders');
  if (res.ok) {
    const orders = await res.json();
    const container = document.getElementById('ordersList');
    
    if (orders.length === 0) {
      container.innerHTML = '<p>No orders yet</p>';
    } else {
      let html = '<ul class="items-list">';
      for (const order of orders) {
        html += `<li>
          <div>
            <strong>Order #${order.id}</strong><br>
            ${order.store_name || 'Unknown Store'} • ${new Date(order.ordered_at).toLocaleDateString()}
          </div>
          <div>
            R${order.total_amount.toFixed(2)}<br>
            <span class="badge badge-${order.status === 'delivered' ? 'success' : 'warning'}">${order.status}</span>
          </div>
        </li>`;
      }
      html += '</ul>';
      container.innerHTML = html;
    }
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
</script>
</body>
</html>
"""

@app.get("/")
def index():
    return render_template_string(INDEX_HTML)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Initialize database
    if not os.path.exists(DB_PATH):
        db = sqlite3.connect(DB_PATH)
        db.executescript(SCHEMA)
        
        # Seed products
        for product in SEED_PRODUCTS:
            db.execute("""
                INSERT OR IGNORE INTO product_catalog 
                (product_name, category, subcategory, emoji, calories, protein, carbs, fat, fiber, unit, typical_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, product)
        
        # Seed stores
        for store in SEED_STORES:
            db.execute("""
                INSERT OR IGNORE INTO stores 
                (name, location, latitude, longitude, delivery_fee, free_delivery_min, delivery_minutes, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, store)
        
        db.commit()
        
        # Seed prices
        for price_data in SEED_PRICES:
            product = db.execute("SELECT id FROM product_catalog WHERE product_name = ?", (price_data[0],)).fetchone()
            store = db.execute("SELECT id FROM stores WHERE name = ?", (price_data[1],)).fetchone()
            if product and store:
                db.execute("""
                    INSERT OR IGNORE INTO store_prices (product_id, store_id, price, previous_price, discount_percent)
                    VALUES (?, ?, ?, ?, ?)
                """, (product[0], store[0], price_data[2], price_data[3], price_data[4]))
        
        db.commit()
        db.close()
    
    app.run(host="0.0.0.0", port=5000, debug=True)

@app.get("/api/lists/<int:list_id>/items")
@login_required
def get_list_items(list_id):
    """Get items in a shopping list"""
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify(error="Unauthorized"), 403
    
    items = db.execute("""
        SELECT sli.*, pc.product_name, pc.emoji, pc.unit, pc.typical_quantity
        FROM shopping_list_items sli
        JOIN product_catalog pc ON pc.id = sli.product_id
        WHERE sli.list_id = ?
        ORDER BY sli.priority DESC, sli.created_at ASC
    """, (list_id,)).fetchall()
    
    return jsonify([dict(item) for item in items])

@app.post("/api/lists/<int:list_id>/text")
@login_required
def add_bulk_items_text(list_id):
    """Add multiple items from text input"""
    data = request.get_json(force=True)
    text = data.get("text", "")
    
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify(error="Unauthorized"), 403
    
    # Parse items (one per line)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    added = 0
    for line in lines:
        # Check if line has quantity (e.g., "2 bread" or "milk 2L")
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            quantity = float(parts[0])
            product_name = ' '.join(parts[1:])
        else:
            quantity = 1
            product_name = line
        
        # Find or create product
        product = db.execute(
            "SELECT id FROM product_catalog WHERE product_name LIKE ?", (f"%{product_name}%",)
        ).fetchone()
        
        if not product:
            cur = db.execute(
                "INSERT INTO product_catalog (product_name, category, emoji) VALUES (?, 'Uncategorized', '🛒')",
                (product_name,)
            )
            product_id = cur.lastrowid
        else:
            product_id = product["id"]
        
        # Check if already in list
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
                INSERT INTO shopping_list_items (list_id, product_id, quantity, added_by)
                VALUES (?, ?, ?, ?)
            """, (list_id, product_id, quantity, session["user_id"]))
        
        added += 1
    
    db.execute("UPDATE shopping_lists SET updated_at = datetime('now') WHERE id = ?", (list_id,))
    db.commit()
    
    return jsonify(added=added, message=f"Added {added} items")

@app.get("/api/lists/<int:list_id>/items")
@login_required
def get_list_items(list_id):
    """Get items in a shopping list"""
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify(error="Unauthorized"), 403
    
    items = db.execute("""
        SELECT sli.*, pc.product_name, pc.emoji, pc.unit, pc.typical_quantity
        FROM shopping_list_items sli
        JOIN product_catalog pc ON pc.id = sli.product_id
        WHERE sli.list_id = ?
        ORDER BY sli.priority DESC, sli.created_at ASC
    """, (list_id,)).fetchall()
    
    return jsonify([dict(item) for item in items])

@app.post("/api/lists/<int:list_id>/text")
@login_required
def add_bulk_items_text(list_id):
    """Add multiple items from text input"""
    data = request.get_json(force=True)
    text = data.get("text", "")
    
    db = get_db()
    
    # Verify ownership
    list_owner = db.execute("SELECT user_id FROM shopping_lists WHERE id = ?", (list_id,)).fetchone()
    if not list_owner or list_owner["user_id"] != session["user_id"]:
        return jsonify(error="Unauthorized"), 403
    
    # Parse items (one per line)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    added = 0
    for line in lines:
        # Check if line has quantity (e.g., "2 bread" or "milk 2L")
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            quantity = float(parts[0])
            product_name = ' '.join(parts[1:])
        else:
            quantity = 1
            product_name = line
        
        # Find or create product
        product = db.execute(
            "SELECT id FROM product_catalog WHERE product_name LIKE ?", (f"%{product_name}%",)
        ).fetchone()
        
        if not product:
            cur = db.execute(
                "INSERT INTO product_catalog (product_name, category, emoji) VALUES (?, 'Uncategorized', '🛒')",
                (product_name,)
            )
            product_id = cur.lastrowid
        else:
            product_id = product["id"]
        
        # Check if already in list
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
                INSERT INTO shopping_list_items (list_id, product_id, quantity, added_by)
                VALUES (?, ?, ?, ?)
            """, (list_id, product_id, quantity, session["user_id"]))
        
        added += 1
    
    db.execute("UPDATE shopping_lists SET updated_at = datetime('now') WHERE id = ?", (list_id,))
    db.commit()
    
    return jsonify(added=added, message=f"Added {added} items")
