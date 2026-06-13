"""
SEDIBA GHOST OMNIVERSAL NEURAL MIND
Pure add-on - No changes to existing ShopAround code
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List
import uuid
import json
import sqlite3
from flask import request, jsonify

# ====================================================
# KERNEL
# ====================================================

@dataclass(frozen=True)
class Kernel:
    name: str = "SEDIBA GHOST OMNIVERSAL NEURAL MIND"
    version: str = "2.0.0"
    founder: str = "Lukie Sediba"
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ====================================================
# MEMORY LAYER (Persistent)
# ====================================================

class MemoryLayer:
    def __init__(self, db_path="ghost_memory.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ghost_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                timestamp TEXT,
                context TEXT,
                evaluations TEXT,
                verdict TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def remember(self, event: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR IGNORE INTO ghost_events (event_id, timestamp, context, evaluations, verdict)
            VALUES (?, ?, ?, ?, ?)
        """, (event["id"], event["timestamp"], json.dumps(event["context"]), 
              json.dumps(event["evaluations"]), event["verdict"]))
        conn.commit()
        conn.close()
    
    def recent(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM ghost_events ORDER BY created_at DESC LIMIT ?", (limit,))
        results = [dict(row) for row in cur.fetchall()]
        conn.close()
        return results


# ====================================================
# AGENTS
# ====================================================

class Agent:
    name = "Generic Agent"
    def evaluate(self, context: Dict[str, Any]):
        raise NotImplementedError


class StrategyAgent(Agent):
    name = "Strategy Agent"
    def evaluate(self, context):
        return {
            "agent": self.name,
            "recommendation": "EXPAND",
            "confidence": 0.74,
            "reason": "Growth opportunity detected."
        }


class RiskAgent(Agent):
    name = "Risk Agent"
    def evaluate(self, context):
        risk = context.get("risk_score", 0.5)
        return {
            "agent": self.name,
            "recommendation": "APPROVE" if risk < 0.7 else "REJECT",
            "confidence": 0.85,
            "reason": f"Risk score: {risk}"
        }


class OperationsAgent(Agent):
    name = "Operations Agent"
    def evaluate(self, context):
        return {
            "agent": self.name,
            "recommendation": "EXECUTE",
            "confidence": 0.80,
            "reason": "Operational capacity available."
        }


class FounderAgent(Agent):
    name = "Founder Agent"
    def evaluate(self, context):
        return {
            "agent": self.name,
            "recommendation": "ALIGN",
            "confidence": 0.90,
            "reason": "Decision aligns with long-term Sediba vision."
        }


# ====================================================
# DECISION ENGINE
# ====================================================

class DecisionEngine:
    def decide(self, evaluations):
        approvals = 0
        for e in evaluations:
            if e["recommendation"] in ["APPROVE", "EXECUTE", "ALIGN", "EXPAND"]:
                approvals += 1
        if approvals >= 3:
            return "APPROVED"
        return "DEFERRED"


# ====================================================
# GHOST BRAIN ORCHESTRATOR
# ====================================================

class GhostBrain:
    def __init__(self):
        self.kernel = Kernel()
        self.memory = MemoryLayer()
        self.agents = [StrategyAgent(), RiskAgent(), OperationsAgent(), FounderAgent()]
        self.engine = DecisionEngine()
    
    def think(self, context):
        evaluations = [agent.evaluate(context) for agent in self.agents]
        verdict = self.engine.decide(evaluations)
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context,
            "evaluations": evaluations,
            "verdict": verdict
        }
        self.memory.remember(event)
        return event
    
    def status(self):
        return {
            "kernel": {
                "name": self.kernel.name,
                "version": self.kernel.version,
                "founder": self.kernel.founder
            },
            "agents": [a.name for a in self.agents],
            "memory_count": len(self.memory.recent(100))
        }


# ====================================================
# FLASK ROUTES (PURE ADDITION)
# ====================================================

brain = GhostBrain()

def add_ghost_brain(app):
    """Add Ghost Brain routes to existing Flask app - NO CHANGES to existing code"""
    
    @app.route("/api/ghost/think", methods=["POST"])
    def ghost_think():
        data = request.get_json(force=True)
        context = {
            "objective": data.get("objective", "Decision"),
            "risk_score": data.get("risk_score", 0.5),
            "amount": data.get("amount", 0),
            "capital_required": data.get("capital_required", 0)
        }
        result = brain.think(context)
        return jsonify(result)
    
    @app.route("/api/ghost/status", methods=["GET"])
    def ghost_status():
        return jsonify(brain.status())
    
    @app.route("/api/ghost/memory", methods=["GET"])
    def ghost_memory():
        limit = request.args.get("limit", 10, type=int)
        memories = brain.memory.recent(limit)
        return jsonify({"memories": memories})
    
    print("✅ Sediba Ghost Omniversal Neural Mind added at /api/ghost/*")
    return app

print("🧠 Ghost Brain module loaded - Ready to integrate")
