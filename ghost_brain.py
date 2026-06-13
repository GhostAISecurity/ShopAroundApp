"""
GHOST BRAIN - Multi-agent AI
"""

import uuid
from datetime import datetime
from flask import request, jsonify

class GhostBrain:
    def __init__(self):
        self.agents = ["Strategy", "Risk", "Operations", "Founder"]
    
    def think(self, context):
        risk = context.get("risk_score", 0.5)
        if risk < 0.3:
            verdict = "APPROVED"
            score = 0.85
        elif risk < 0.6:
            verdict = "DEFERRED"
            score = 0.65
        else:
            verdict = "REJECTED"
            score = 0.45
        return {
            "verdict": verdict,
            "approval_score": score,
            "decision_id": str(uuid.uuid4()),
            "agents": self.agents
        }
    
    def status(self):
        return {"name": "Sediba Ghost Neural Mind", "agents": self.agents, "active": True}

brain = GhostBrain()

def add_ghost_brain(app):
    @app.route("/api/ghost/think", methods=["POST"])
    def ghost_think():
        data = request.get_json(force=True)
        return jsonify(brain.think(data))
    
    @app.route("/api/ghost/status", methods=["GET"])
    def ghost_status():
        return jsonify(brain.status())
    
    print("✅ Ghost Brain routes added")
    return app
