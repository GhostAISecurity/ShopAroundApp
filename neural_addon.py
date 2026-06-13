"""
NEURAL ADDON - Pure addition, no changes to your existing code
"""

import sqlite3
import json
import uuid
from datetime import datetime
from flask import request, jsonify

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
        self.agents = ["Strategy Agent", "Risk Agent", "Financial Agent", "Operations Agent", "Founder Agent"]
    
    def think(self, context):
        risk = context.get("risk_score", 0.5)
        score = 0.85 if risk < 0.3 else 0.65 if risk < 0.6 else 0.45
        verdict = "APPROVED" if score > 0.6 else "DEFERRED" if score > 0.4 else "REJECTED"
        did = str(uuid.uuid4())
        ts = datetime.now().isoformat()
        self.memory.store(did, ts, context, verdict, score)
        return {"verdict": verdict, "approval_score": score, "decision_id": did}
    
    def status(self):
        return {"name": "Sediba Ghost Neural Mind", "agents": self.agents}

brain = NeuralBrain()

def add_neural_routes(app):
    """Adds 3 neural routes - NO changes to existing routes"""
    @app.route("/api/neural/think", methods=["POST"])
    def neural_think():
        data = request.get_json(force=True)
        context = {"objective": data.get("objective", "Decision"), "risk_score": data.get("risk_score", 0.5), "amount": data.get("amount", 0)}
        return jsonify(brain.think(context))
    
    @app.route("/api/neural/status", methods=["GET"])
    def neural_status():
        return jsonify(brain.status())
    
    @app.route("/api/neural/memory", methods=["GET"])
    def neural_memory():
        limit = request.args.get("limit", 10, type=int)
        return jsonify({"memories": brain.memory.recall(limit)})
    
    print("✅ Neural AI integrated (3 new endpoints at /api/neural/*)")
    return app
