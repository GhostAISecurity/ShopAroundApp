"""
SHOPAROUND - Complete Neural Integration
With Omniversal Neural Mind & Financial Orchestration Layer
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
# KERNEL - The Core Identity
# ====================================================

@dataclass(frozen=True)
class Kernel:
    name: str = "SEDIBA GHOST OMNIVERSAL NEURAL MIND"
    version: str = "2.0.0"
    founder: str = "Lukie Sediba"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    purpose: str = "Economic Intelligence & Financial Orchestration for Africa"


# ====================================================
# MEMORY LAYER - Persistent Neural Memory
# ====================================================

class MemoryLayer:
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
        """, (
            event["id"],
            event["timestamp"],
            json.dumps(event["context"]),
            json.dumps(event["evaluations"]),
            event["verdict"]
        ))
        conn.commit()
        conn.close()
    
    def recall(self, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM neural_events 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) as total, verdict FROM neural_events GROUP BY verdict")
        stats = {}
        for row in cursor.fetchall():
            stats[row[1]] = row[0]
        conn.close()
        return stats


# ====================================================
# AGENT BASE CLASS
# ====================================================

class Agent:
    name = "Generic Agent"
    weight: float = 1.0
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


# ====================================================
# STRATEGY AGENT - Market Analysis
# ====================================================

class StrategyAgent(Agent):
    name = "Strategy Agent"
    weight = 0.35
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        market_condition = context.get("market_condition", "stable")
        user_growth = context.get("user_growth", 0)
        
        if user_growth > 0.2:
            recommendation = "AGGRESSIVE_EXPAND"
            confidence = 0.85
            reason = "Strong user growth detected"
        elif market_condition == "bullish":
            recommendation = "EXPAND"
            confidence = 0.75
            reason = "Favorable market conditions"
        elif market_condition == "bearish":
            recommendation = "CONSOLIDATE"
            confidence = 0.70
            reason = "Market volatility requires caution"
        else:
            recommendation = "MAINTAIN"
            confidence = 0.65
            reason = "Steady state operations"
        
        return {
            "agent": self.name,
            "recommendation": recommendation,
            "confidence": confidence,
            "reason": reason,
            "weight": self.weight
        }


# ====================================================
# RISK AGENT - Financial Risk Assessment
# ====================================================

class RiskAgent(Agent):
    name = "Risk Agent"
    weight = 0.40
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        risk_score = context.get("risk_score", 0.5)
        transaction_amount = context.get("transaction_amount", 0)
        user_trust = context.get("user_trust_score", 0.5)
        
        # Calculate combined risk
        combined_risk = (risk_score * 0.5 + (1 - user_trust) * 0.3 + min(transaction_amount / 100000, 1) * 0.2)
        
        if combined_risk < 0.3:
            recommendation = "APPROVE"
            confidence = 0.90
            reason = "Low risk transaction"
        elif combined_risk < 0.6:
            recommendation = "REQUIRE_REVIEW"
            confidence = 0.75
            reason = "Moderate risk - additional verification needed"
        else:
            recommendation = "REJECT"
            confidence = 0.85
            reason = "High risk detected"
        
        return {
            "agent": self.name,
            "recommendation": recommendation,
            "confidence": confidence,
            "reason": reason,
            "risk_score": combined_risk,
            "weight": self.weight
        }


# ====================================================
# FINANCIAL AGENT - Treasury & Cash Flow
# ====================================================

class FinancialAgent(Agent):
    name = "Financial Agent"
    weight = 0.30
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        available_capital = context.get("available_capital", 0)
        monthly_revenue = context.get("monthly_revenue", 0)
        monthly_expenses = context.get("monthly_expenses", 0)
        
        net_cash_flow = monthly_revenue - monthly_expenses
        burn_rate = monthly_expenses if monthly_expenses > 0 else 1
        runway_months = available_capital / burn_rate if burn_rate > 0 else 0
        
        if runway_months < 3:
            recommendation = "CONSERVE_CASH"
            confidence = 0.90
            reason = f"Critical runway: {runway_months:.1f} months"
        elif runway_months < 6:
            recommendation = "OPTIMIZE_SPENDING"
            confidence = 0.80
            reason = f"Limited runway: {runway_months:.1f} months"
        elif net_cash_flow > 0:
            recommendation = "INVEST_GROWTH"
            confidence = 0.85
            reason = f"Positive cash flow of R{net_cash_flow:,.0f}"
        else:
            recommendation = "MAINTAIN"
            confidence = 0.70
            reason = "Stable financial position"
        
        return {
            "agent": self.name,
            "recommendation": recommendation,
            "confidence": confidence,
            "reason": reason,
            "runway_months": round(runway_months, 1),
            "net_cash_flow": net_cash_flow,
            "weight": self.weight
        }


# ====================================================
# OPERATIONS AGENT - System Health
# ====================================================

class OperationsAgent(Agent):
    name = "Operations Agent"
    weight = 0.25
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        system_load = context.get("system_load", 0.5)
        active_users = context.get("active_users", 0)
        error_rate = context.get("error_rate", 0.05)
        
        if error_rate > 0.1:
            recommendation = "INVESTIGATE"
            confidence = 0.90
            reason = f"High error rate: {error_rate*100:.1f}%"
        elif system_load > 0.8:
            recommendation = "SCALE_UP"
            confidence = 0.85
            reason = "System near capacity"
        elif active_users > 0:
            recommendation = "OPTIMIZE"
            confidence = 0.75
            reason = f"Supporting {active_users} active users"
        else:
            recommendation = "READY"
            confidence = 0.70
            reason = "System operational"
        
        return {
            "agent": self.name,
            "recommendation": recommendation,
            "confidence": confidence,
            "reason": reason,
            "weight": self.weight
        }


# ====================================================
# FOUNDER AGENT - Strategic Alignment
# ====================================================

class FounderAgent(Agent):
    name = "Founder Agent"
    weight = 0.50
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        alignment_score = context.get("strategic_alignment", 0.8)
        long_term_value = context.get("long_term_value", 0.5)
        
        combined_score = (alignment_score + long_term_value) / 2
        
        if combined_score > 0.7:
            recommendation = "APPROVE"
            confidence = 0.95
            reason = "Strong alignment with Sediba vision"
        elif combined_score > 0.4:
            recommendation = "REVIEW"
            confidence = 0.75
            reason = "Partial alignment - further evaluation needed"
        else:
            recommendation = "REJECT"
            confidence = 0.85
            reason = "Does not align with long-term strategy"
        
        return {
            "agent": self.name,
            "recommendation": recommendation,
            "confidence": confidence,
            "reason": reason,
            "alignment_score": combined_score,
            "weight": self.weight
        }


# ====================================================
# DECISION ENGINE - Consensus Mechanism
# ====================================================

class DecisionEngine:
    
    def __init__(self):
        self.decision_threshold = 0.6
    
    def decide(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Weighted voting system
        weighted_scores = {}
        approval_votes = 0
        total_weight = 0
        
        # Define positive recommendations
        positive_recs = ["APPROVE", "EXECUTE", "ALIGN", "EXPAND", "INVEST_GROWTH", "OPTIMIZE", "MAINTAIN", "READY"]
        
        for eval in evaluations:
            weight = eval.get("weight", 1.0)
            total_weight += weight
            
            if eval["recommendation"] in positive_recs:
                approval_votes += weight * eval["confidence"]
            
            weighted_scores[eval["agent"]] = {
                "vote": eval["recommendation"],
                "confidence": eval["confidence"],
                "weight": weight,
                "reason": eval["reason"]
            }
        
        # Calculate weighted approval score
        approval_score = approval_votes / total_weight if total_weight > 0 else 0
        
        if approval_score >= self.decision_threshold:
            verdict = "APPROVED"
            action = "PROCEED"
        elif approval_score >= 0.4:
            verdict = "DEFERRED"
            action = "REQUIRE_REVIEW"
        else:
            verdict = "REJECTED"
            action = "HALT"
        
        return {
            "verdict": verdict,
            "action": action,
            "approval_score": round(approval_score, 3),
            "threshold": self.decision_threshold,
            "agent_votes": weighted_scores
        }


# ====================================================
# FINANCIAL ORCHESTRATION LAYER
# ====================================================

class FinancialOrchestrator:
    """Treasury AI Brain - Central Financial Nervous System"""
    
    def __init__(self):
        self.transactions = []
        self.budgets = {}
        self.revenue_streams = {}
    
    def record_transaction(self, transaction: Dict) -> Dict:
        transaction["id"] = str(uuid.uuid4())
        transaction["timestamp"] = datetime.utcnow().isoformat()
        self.transactions.append(transaction)
        return transaction
    
    def get_cash_position(self) -> Dict:
        total_inflow = sum(t["amount"] for t in self.transactions if t["type"] == "inflow")
        total_outflow = sum(t["amount"] for t in self.transactions if t["type"] == "outflow")
        return {
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "net_position": total_inflow - total_outflow,
            "transaction_count": len(self.transactions)
        }
    
    def analyze_revenue_health(self) -> Dict:
        daily_revenue = {}
        for t in self.transactions:
            if t["type"] == "inflow":
                date = t["timestamp"][:10]
                daily_revenue[date] = daily_revenue.get(date, 0) + t["amount"]
        
        if daily_revenue:
            daily_values = list(daily_revenue.values())
            avg_daily = sum(daily_values) / len(daily_values)
            return {
                "average_daily_revenue": avg_daily,
                "revenue_volatility": max(daily_values) - min(daily_values) if len(daily_values) > 1 else 0,
                "days_with_revenue": len(daily_revenue)
            }
        return {"average_daily_revenue": 0, "revenue_volatility": 0, "days_with_revenue": 0}
    
    def recommend_budget_allocation(self, total_budget: float) -> Dict:
        # Smart budget allocation based on business priorities
        allocation = {
            "technology_development": total_budget * 0.35,
            "marketing_sales": total_budget * 0.25,
            "operations_support": total_budget * 0.20,
            "compliance_legal": total_budget * 0.10,
            "reserve_contingency": total_budget * 0.10
        }
        return {
            "total_budget": total_budget,
            "allocation": allocation,
            "recommendation": "Prioritize technology and marketing for growth phase"
        }


# ====================================================
# OMNIVERSAL BRAIN - Main Orchestrator
# ====================================================

class GhostBrain:
    
    def __init__(self):
        self.kernel = Kernel()
        self.memory = MemoryLayer()
        self.agents = [
            StrategyAgent(),
            RiskAgent(),
            FinancialAgent(),
            OperationsAgent(),
            FounderAgent()
        ]
        self.engine = DecisionEngine()
        self.financial = FinancialOrchestrator()
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main thinking method - evaluates context and produces decision"""
        
        evaluations = []
        for agent in self.agents:
            try:
                evaluation = agent.evaluate(context)
                evaluations.append(evaluation)
            except Exception as e:
                evaluations.append({
                    "agent": agent.name,
                    "recommendation": "ERROR",
                    "confidence": 0,
                    "reason": f"Evaluation failed: {str(e)}",
                    "weight": agent.weight
                })
        
        decision = self.engine.decide(evaluations)
        
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
            "evaluations": evaluations,
            "verdict": decision["verdict"],
            "action": decision["action"],
            "approval_score": decision["approval_score"]
        }
        
        self.memory.remember(event)
        
        return event
    
    def get_system_status(self) -> Dict:
        memory_stats = self.memory.get_statistics()
        cash_position = self.financial.get_cash_position()
        revenue_health = self.financial.analyze_revenue_health()
        
        return {
            "kernel": {
                "name": self.kernel.name,
                "version": self.kernel.version,
                "founder": self.kernel.founder,
                "created": self.kernel.created
            },
            "agents": [{"name": a.name, "weight": a.weight} for a in self.agents],
            "memory": memory_stats,
            "financial": cash_position,
            "revenue": revenue_health,
            "timestamp": datetime.utcnow().isoformat()
        }


# ====================================================
# FLASK APP INTEGRATION
# ====================================================

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shoparound.db")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=7)

# Initialize the Ghost Brain
ghost_brain = GhostBrain()

# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
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
            rating REAL,
            verified INTEGER DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS shopping_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT DEFAULT 'My List',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER,
            product_name TEXT,
            quantity REAL DEFAULT 1,
            checked_off INTEGER DEFAULT 0
        );
    """)
    
    # Seed sample service providers
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM service_providers")
    if cursor.fetchone()[0] == 0:
        sample = [
            ("Plumbmaster JHB", "plumbing", "Johannesburg", -26.2041, 28.0473, "011 123 4567", 4.2),
            ("JHB Electricians", "electrical", "Johannesburg", -26.2025, 28.0450, "011 234 5678", 4.5),
            ("Auto Care Centre", "mechanic", "Johannesburg", -26.2080, 28.0500, "011 345 6789", 4.0),
            ("Pretoria Plumbers", "plumbing", "Pretoria", -25.7461, 28.1881, "012 345 6789", 4.3),
        ]
        cursor.executemany("INSERT INTO service_providers (name, service_type, address, latitude, longitude, phone, rating) VALUES (?, ?, ?, ?, ?, ?, ?)", sample)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

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
# API ROUTES
# ====================================================

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
    return jsonify({"id": user["id"], "username": user["username"]})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

# ====================================================
# NEURAL BRAIN API ENDPOINTS
# ====================================================

@app.route("/api/brain/think", methods=["POST"])
def brain_think():
    """Let the AI brain analyze and decide"""
    data = request.get_json(force=True)
    context = {
        "objective": data.get("objective", "Business decision"),
        "risk_score": data.get("risk_score", 0.5),
        "transaction_amount": data.get("amount", 0),
        "user_trust_score": data.get("trust_score", 0.5),
        "market_condition": data.get("market_condition", "stable"),
        "user_growth": data.get("user_growth", 0),
        "available_capital": data.get("available_capital", 10000),
        "monthly_revenue": data.get("monthly_revenue", 5000),
        "monthly_expenses": data.get("monthly_expenses", 3000),
        "strategic_alignment": data.get("strategic_alignment", 0.8),
        "long_term_value": data.get("long_term_value", 0.6)
    }
    
    result = ghost_brain.think(context)
    return jsonify(result)

@app.route("/api/brain/status", methods=["GET"])
def brain_status():
    """Get the current status of the AI brain"""
    status = ghost_brain.get_system_status()
    return jsonify(status)

@app.route("/api/brain/memory", methods=["GET"])
def brain_memory():
    """Recall recent AI decisions"""
    limit = request.args.get("limit", 10, type=int)
    memories = ghost_brain.memory.recall(limit)
    return jsonify({"memories": memories})

@app.route("/api/financial/transaction", methods=["POST"])
def record_transaction():
    """Record a financial transaction"""
    data = request.get_json(force=True)
    transaction = ghost_brain.financial.record_transaction({
        "type": data.get("type", "inflow"),
        "amount": data.get("amount", 0),
        "category": data.get("category", "uncategorized"),
        "description": data.get("description", "")
    })
    return jsonify(transaction)

@app.route("/api/financial/cash-position", methods=["GET"])
def get_cash_position():
    """Get current cash position"""
    return jsonify(ghost_brain.financial.get_cash_position())

@app.route("/api/financial/budget", methods=["POST"])
def recommend_budget():
    """Get budget recommendation"""
    data = request.get_json(force=True)
    total_budget = data.get("total_budget", 10000)
    return jsonify(ghost_brain.financial.recommend_budget_allocation(total_budget))

# ====================================================
# SERVICE PROVIDER ROUTES
# ====================================================

@app.route("/api/services/nearby", methods=["GET"])
def get_nearby_services():
    lat = request.args.get("lat", type=float, default=-26.2041)
    lng = request.args.get("lng", type=float, default=28.0473)
    service_type = request.args.get("type", "plumbing")
    
    db = get_db()
    providers = db.execute("""
        SELECT * FROM service_providers 
        WHERE service_type = ? OR ? = ''
        LIMIT 20
    """, (service_type, service_type)).fetchall()
    
    # Calculate distances
    result = []
    for p in providers:
        dist = None
        if p["latitude"]:
            dist = math.sqrt((p["latitude"] - lat)**2 + (p["longitude"] - lng)**2) * 111
        result.append({
            "name": p["name"],
            "service_type": p["service_type"],
            "address": p["address"],
            "phone": p["phone"],
            "rating": p["rating"],
            "distance_km": round(dist, 1) if dist else None,
            "latitude": p["latitude"],
            "longitude": p["longitude"]
        })
    
    result.sort(key=lambda x: x.get("distance_km") or 999)
    
    return jsonify({
        "success": True,
        "services": result[:20]
    })

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
        cursor = db.execute(
            "INSERT INTO shopping_lists (user_id, name) VALUES (?, ?)",
            (session["user_id"], data.get("name", "My List"))
        )
        db.commit()
        return jsonify({"id": cursor.lastrowid})

@app.route("/api/lists/<int:list_id>/items", methods=["POST"])
@login_required
def add_list_item(list_id):
    data = request.get_json(force=True)
    db = get_db()
    db.execute("""
        INSERT INTO shopping_list_items (list_id, product_name, quantity)
        VALUES (?, ?, ?)
    """, (list_id, data.get("product_name"), data.get("quantity", 1)))
    db.commit()
    return jsonify({"success": True})

@app.route("/api/lists/<int:list_id>/items", methods=["GET"])
@login_required
def get_list_items(list_id):
    db = get_db()
    items = db.execute("SELECT * FROM shopping_list_items WHERE list_id = ?", (list_id,)).fetchall()
    return jsonify([dict(i) for i in items])

# ====================================================
# FRONTEND
# ====================================================

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sediba Ghost - ShopAround Neural Platform</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 100%);min-height:100vh;}
        .navbar{background:#1f8a4c;color:white;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;}
        .navbar h1{font-size:1.5rem;}
        .nav-links{display:flex;gap:1rem;}
        .nav-links a{color:white;text-decoration:none;padding:0.5rem 1rem;border-radius:0.5rem;cursor:pointer;}
        .nav-links a:hover{background:rgba(255,255,255,0.2);}
        .container{max-width:1200px;margin:2rem auto;padding:0 2rem;}
        .card{background:rgba(17,24,39,0.95);border-radius:1rem;padding:1.5rem;margin-bottom:1.5rem;border:1px solid rgba(255,255,255,0.1);}
        .card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;border-bottom:2px solid #334155;padding-bottom:0.5rem;}
        h2{color:#a78bfa;font-size:1.25rem;}
        input,select,button,textarea{width:100%;padding:0.75rem;margin:0.5rem 0;border:1px solid #334155;border-radius:0.5rem;background:#1e293b;color:white;}
        button{background:#7c3aed;color:white;border:none;cursor:pointer;font-weight:600;}
        button:hover{background:#6d28d9;}
        .hidden{display:none;}
        .item-row{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 0;border-bottom:1px solid #334155;}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:1rem;}
        .stat-card{background:#1e293b;padding:1rem;border-radius:0.5rem;text-align:center;}
        .stat-value{font-size:1.8rem;font-weight:bold;color:#a78bfa;}
        .tabs{display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap;}
        .tab{padding:0.5rem 1rem;background:#1e293b;border-radius:0.5rem;cursor:pointer;color:#94a3b8;}
        .tab.active{background:#7c3aed;color:white;}
        .badge{display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;font-size:0.75rem;}
        .badge-success{background:#10b981;color:white;}
        .badge-warning{background:#f59e0b;color:white;}
        .badge-danger{background:#ef4444;color:white;}
        @media (max-width:768px){.container{padding:0 1rem;}}
    </style>
</head>
<body>
<div class="navbar">
    <h1>🧠 Sediba Ghost Omniversal Mind</h1>
    <div class="nav-links">
        <a onclick="showSection('shopping')">Shopping</a>
        <a onclick="showSection('services')">Services</a>
        <a onclick="showSection('brain')">AI Brain</a>
        <a id="logoutBtn" style="display:none;" onclick="logout()">Logout</a>
    </div>
</div>

<div class="container">
    <div id="authSection" class="card" style="max-width:400px; margin:2rem auto; text-align:center;">
        <h2 style="color:white;">Welcome to ShopAround</h2>
        <p style="color:#94a3b8;">Powered by Sediba Ghost Neural Intelligence</p>
        <div id="loginForm">
            <input type="text" id="loginUsername" placeholder="Username">
            <input type="password" id="loginPassword" placeholder="Password">
            <button onclick="login()">Login</button>
            <button onclick="showRegister()" style="background:#334155;">Register</button>
        </div>
        <div id="registerForm" style="display:none;">
            <input type="text" id="regUsername" placeholder="Username">
            <input type="email" id="regEmail" placeholder="Email">
            <input type="password" id="regPassword" placeholder="Password">
            <button onclick="register()">Register</button>
            <button onclick="showLogin()" style="background:#334155;">Back</button>
        </div>
        <p id="authMessage" style="color:#ef4444; margin-top:1rem;"></p>
    </div>

    <div id="appSection" style="display:none;">
        <div class="stats">
            <div class="stat-card"><div class="stat-value" id="neuralStatus">Active</div><div>Neural Status</div></div>
            <div class="stat-card"><div class="stat-value" id="brainConfidence">-</div><div>AI Confidence</div></div>
        </div>

        <div id="shoppingSection">
            <div class="card"><div class="card-header"><h2>🛒 My Shopping Lists</h2><button onclick="createList()">+ New</button></div><div id="listsContainer"></div></div>
            <div class="card"><div class="card-header"><h2>➕ Add Items</h2></div><textarea id="bulkItems" rows="3" placeholder="Bread&#10;Milk&#10;Eggs"></textarea><select id="selectedList"></select><button onclick="addBulkItems()">Add</button></div>
        </div>

        <div id="servicesSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🛠️ Find Services</h2></div>
            <select id="serviceType"><option value="plumbing">Plumbing</option><option value="electrical">Electrical</option><option value="mechanic">Mechanic</option></select>
            <button onclick="findServices()">🔍 Search</button><div id="servicesList"></div></div>
        </div>

        <div id="brainSection" class="hidden">
            <div class="card"><div class="card-header"><h2>🧠 AI Decision Engine</h2></div>
            <input type="text" id="brainObjective" placeholder="Decision Objective" value="Approve transaction?">
            <input type="number" id="brainAmount" placeholder="Amount (R)" value="5000">
            <input type="number" id="brainRisk" placeholder="Risk Score (0-1)" value="0.3" step="0.1">
            <button onclick="consultBrain()">🧠 Consult the Neural Mind</button>
            <div id="brainResult"></div></div>
            
            <div class="card"><div class="card-header"><h2>📊 Financial Orchestration</h2></div>
            <input type="number" id="budgetAmount" placeholder="Total Budget (R)" value="50000">
            <button onclick="getBudgetRecommendation()">💰 Get Budget Recommendation</button>
            <div id="budgetResult"></div></div>
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
        document.getElementById('authSection').style.display='none';
        document.getElementById('appSection').style.display='block';
        document.getElementById('logoutBtn').style.display='inline-block';
        loadLists();
        updateBrainStatus();
    }else alert('Login failed');
}

async function register(){
    const u=document.getElementById('regUsername').value;
    const e=document.getElementById('regEmail').value;
    const p=document.getElementById('regPassword').value;
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
    document.getElementById('brainSection').classList.add('hidden');
    document.getElementById(`${s}Section`).classList.remove('hidden');
}

async function updateBrainStatus(){
    const r=await fetch('/api/brain/status');
    const data=await r.json();
    if(data.kernel) document.getElementById('neuralStatus').innerHTML=data.kernel.name.split(' ')[0];
}

async function consultBrain(){
    const objective=document.getElementById('brainObjective').value;
    const amount=parseFloat(document.getElementById('brainAmount').value);
    const risk=parseFloat(document.getElementById('brainRisk').value);
    
    const r=await fetch('/api/brain/think',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({objective,amount,risk_score:risk})});
    const data=await r.json();
    
    const verdictClass=data.verdict==='APPROVED'?'badge-success':data.verdict==='DEFERRED'?'badge-warning':'badge-danger';
    document.getElementById('brainResult').innerHTML=`
        <div class="stats"><div class="stat-card"><div class="stat-value">${data.verdict}</div><div>Verdict</div></div>
        <div class="stat-card"><div class="stat-value">${(data.approval_score*100).toFixed(0)}%</div><div>Approval Score</div></div></div>
        <div class="card"><strong>Agent Evaluations:</strong><br>
        ${data.evaluations.map(e=>`<div class="item-row"><span>🧠 ${e.agent}</span><span class="${e.recommendation.includes('APPROVE')?'badge-success':'badge-warning'}">${e.recommendation}</span><span>${e.confidence*100}%</span></div>`).join('')}
        </div>
        <div class="card"><strong>Reason:</strong> ${data.evaluations[0]?.reason || 'Decision processed by neural consensus'}</div>
    `;
}

async function getBudgetRecommendation(){
    const budget=parseFloat(document.getElementById('budgetAmount').value);
    const r=await fetch('/api/financial/budget',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({total_budget:budget})});
    const data=await r.json();
    document.getElementById('budgetResult').innerHTML=`
        <div class="card"><h3>💰 Budget Allocation Recommendation</h3>
        ${Object.entries(data.allocation).map(([k,v])=>`<div class="item-row"><span>${k.replace('_',' ').toUpperCase()}</span><span>R${v.toLocaleString()}</span></div>`).join('')}
        <div class="stats"><div class="stat-card"><div class="stat-value">R${data.total_budget.toLocaleString()}</div><div>Total Budget</div></div></div>
        <p>💡 ${data.recommendation}</p></div>
    `;
}

async function findServices(){
    const type=document.getElementById('serviceType').value;
    const r=await fetch(`/api/services/nearby?type=${type}`);
    const data=await r.json();
    if(data.services&&data.services.length){
        let html='';
        for(const s of data.services){
            html+=`<div class="card"><strong>${s.name}</strong><br>📞 ${s.phone||'N/A'}<br>⭐ ${s.rating||'N/A'}<br>${s.distance_km?`📍 ${s.distance_km}km away`:''}</div>`;
        }
        document.getElementById('servicesList').innerHTML=html;
    }else document.getElementById('servicesList').innerHTML='<div class="card">No services found</div>';
}

async function loadLists(){
    const r=await fetch('/api/lists');
    if(r.ok){ currentLists=await r.json(); renderLists(); updateSelectors(); }
}

function renderLists(){
    const c=document.getElementById('listsContainer');
    if(!currentLists.length){ c.innerHTML='<div class="card"><p>No lists yet</p></div>'; return; }
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
            for(const i of items) html+=`<div class="item-row"><span>🛒 ${i.product_name} x${i.quantity}</span><button onclick="toggleItem(${id},${i.id})">${i.checked_off?'✓':'○'}</button></div>`;
            c.innerHTML=html;
        }
    }
}

function updateSelectors(){
    const s=document.getElementById('selectedList');
    s.innerHTML='<option value="">Select list</option>';
    for(const l of currentLists) s.innerHTML+=`<option value="${l.id}">${l.name}</option>`;
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

// Auto demo
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
    init_db()
    print("="*70)
    print("🧠 SEDIBA GHOST - OMNIVERSAL NEURAL MIND")
    print("="*70)
    print(f"Kernel: {ghost_brain.kernel.name}")
    print(f"Version: {ghost_brain.kernel.version}")
    print(f"Founder: {ghost_brain.kernel.founder}")
    print("="*70)
    print("✅ Neural Agents: Strategy, Risk, Financial, Operations, Founder")
    print("✅ Financial Orchestration Layer Active")
    print("✅ Multi-Agent Consensus Engine Running")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=True)
