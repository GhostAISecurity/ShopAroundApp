"""
NEURAL AI MODULE - Fixed version
"""

import sqlite3
import json
import uuid
from datetime import datetime
from flask import request, jsonify

class NeuralMemory:
    def __init__(self):
        self.conn = sqlite3.connect("neural_memory.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # This enables dictionary access
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
        # Convert Row objects to dictionaries properly
        return [{key: row[key] for key in row.keys()} for row in cur.fetchall()]

class StrategyAgent:
    name = "Strategy Agent"
    weight = 0.35
    def evaluate(self, ctx):
        return {"agent": self.name, "recommendation": "EXPAND", "confidence": 0.75, "reason": "Growth opportunity", "weight": self.weight}

class RiskAgent:
    name = "Risk Agent"
    weight = 0.40
    def evaluate(self, ctx):
        risk = ctx.get("risk_score", 0.5)
        rec = "APPROVE" if risk < 0.7 else "REQUIRE_REVIEW"
        return {"agent": self.name, "recommendation": rec, "confidence": 0.85, "reason": f"Risk score: {risk}", "weight": self.weight}

class FinancialAgent:
    name = "Financial Agent"
    weight = 0.30
    def evaluate(self, ctx):
        return {"agent": self.name, "recommendation": "OPTIMIZE", "confidence": 0.80, "reason": "Financial analysis complete", "weight": self.weight}

class OperationsAgent:
    name = "Operations Agent"
    weight = 0.25
    def evaluate(self, ctx):
        return {"agent": self.name, "recommendation": "EXECUTE", "confidence": 0.85, "reason": "Operational capacity available", "weight": self.weight}

class FounderAgent:
    name = "Founder Agent"
    weight = 0.50
    def evaluate(self, ctx):
        return {"agent": self.name, "recommendation": "APPROVE", "confidence": 0.90, "reason": "Aligns with Sediba vision", "weight": self.weight}

class DecisionEngine:
    def decide(self, evals):
        pos = ["APPROVE", "EXECUTE", "EXPAND", "OPTIMIZE"]
        total_w = sum(e["weight"] for e in evals)
        approval = sum(e["weight"] * e["confidence"] for e in evals if e["recommendation"] in pos)
        score = approval / total_w if total_w else 0
        if score >= 0.6:
            return {"verdict": "APPROVED", "approval_score": score}
        elif score >= 0.4:
            return {"verdict": "DEFERRED", "approval_score": score}
        return {"verdict": "REJECTED", "approval_score": score}

class NeuralBrain:
    def __init__(self):
        self.memory = NeuralMemory()
        self.agents = [StrategyAgent(), RiskAgent(), FinancialAgent(), OperationsAgent(), FounderAgent()]
        self.engine = DecisionEngine()
    
    def think(self, context):
        evals = [a.evaluate(context) for a in self.agents]
        decision = self.engine.decide(evals)
        did = str(uuid.uuid4())
        ts = datetime.now().isoformat()
        self.memory.store(did, ts, context, decision["verdict"], decision["approval_score"])
        return {"decision_id": did, "timestamp": ts, "verdict": decision["verdict"], "approval_score": decision["approval_score"], "evaluations": evals}
    
    def status(self):
        return {"name": "Sediba Ghost Neural Mind", "agents": [a.name for a in self.agents], "recent": self.memory.recall(3)}

brain = NeuralBrain()

def register_neural_routes(app):
    """Add neural routes to existing Flask app"""
    
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
    
    print("✅ Neural AI routes added to ShopAround")
    return app

print("🧠 Neural AI Module v2.0 - Ready")
