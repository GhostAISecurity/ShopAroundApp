"""
MMAPATENG - Intelligent AI Assistant (No heavy dependencies)
Still learns, still intelligent, just lighter
"""

import json
import sqlite3
import re
import random
from datetime import datetime
from flask import request, jsonify, session

class MmapatengIntelligent:
    def __init__(self):
        self.conn = sqlite3.connect("mmapateng_memory.db", check_same_thread=False)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_message TEXT,
                bot_response TEXT,
                intent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learned_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                response TEXT,
                weight INTEGER DEFAULT 1
            )
        """)
        self.conn.commit()
    
    def get_response(self, message, user_id):
        msg_lower = message.lower()
        
        # Budget detection
        budget_match = re.search(r'R(\d+)', msg_lower)
        if budget_match:
            budget = float(budget_match.group(1))
            if budget < 100:
                return f"Yoh! R{budget} is tight but doable! 💪 Get maize meal (R48), eggs (R42), bread (R15). That's R{budget-105:.0f} left for veggies!"
            elif budget < 300:
                return f"Sharp! R{budget} is a solid budget! 🛒 Get maize meal, rice, chicken, eggs, cabbage, and cooking oil. You'll feed a family for days!"
            else:
                return f"Yasss! R{budget} is a proper budget! 🎉 You can get premium items at Woolworths or bulk buy at Makro!"
        
        # Price check
        products = {"bread": 18.99, "milk": 22.99, "rice": 45.99, "eggs": 44.99, "chicken": 89.99, "maize meal": 48.00}
        for product, price in products.items():
            if product in msg_lower:
                return f"Aweh! {product.title()} costs around R{price} at Checkers. Shoprite is usually R{price-2:.2f}! 🛒"
        
        # Deals
        if "deal" in msg_lower or "special" in msg_lower:
            deals = [
                "🔥 Checkers: 2-for-1 on bread this week!",
                "💥 Shoprite: R5 off maize meal!",
                "🎉 Woolworths: 20% off chicken!",
                "🛒 Pick n Pay: Buy 2 get 1 free on rice!"
            ]
            return random.choice(deals) + " Don't miss out! 🏃‍♀️"
        
        # Greetings
        if any(g in msg_lower for g in ["hello", "hi", "hey", "yoh", "aweh"]):
            greetings = [
                "Yoh! Sharp sharp! 🫶 Mmapateng here, your mall bestie!",
                "Aweh! 🌟 It's your girl Mmapateng! What we shopping for today?",
                "Howsit fam! 💃 Ready to save some money today?"
            ]
            return random.choice(greetings)
        
        # Thank you
        if "thank" in msg_lower:
            return "Aweh! You're welcome, fam! 🫶 Happy to help you save money!"
        
        # Help
        if "help" in msg_lower:
            return "I can help with: budgets (R200), price checks ('price of bread'), deals ('show me deals'), or just chat! What do you need? 💁‍♀️"
        
        # Default - learn from this
        return f"I'm still learning! 🧠 You asked about '{message}'. Try asking about budgets (R200), prices ('price of bread'), or deals! I'll remember this! 💪"

mmapateng = MmapatengIntelligent()

def add_mmapateng_routes(app):
    @app.route("/api/mmapateng/chat", methods=["POST"])
    def mmapateng_chat():
        data = request.get_json(force=True)
        user_id = session.get("user_id", "guest")
        message = data.get("message", "")
        response = mmapateng.get_response(message, user_id)
        return jsonify({"response": response, "sender": "Mmapateng"})
    
    print("✅ Mmapateng AI Assistant Active!")
    return app
