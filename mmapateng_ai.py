"""
MMAPATENG - The Real Johannah
Intelligent Mall Assistant with continuous learning
Confident voice, positive attitude, human-like interaction
"""

import json
import sqlite3
import random
import re
from datetime import datetime
from flask import request, jsonify, session
from collections import defaultdict

# ============================================
# MMAPATENG'S PERSONALITY DATABASE
# ============================================

MMAPATENG_PERSONALITY = {
    "greetings": [
        "Yoh! Sharp sharp! 🫶 Welcome to ShopAround! I'm Mmapateng, your mall bestie! How can I make your day lekker today?",
        "Aweh! 🌟 It's your girl Mmapateng! Ready to help you find the dopest deals in town! What you looking for?",
        "Howsit fam! 💃 Mmapateng here, your shopping sidekick! Let's make your wallet happy today!",
        "Yebo! 🎉 Welcome to the coolest mall in SA! I'm Mmapateng - ask me anything about shopping, deals, or just chat with me!"
    ],
    "farewells": [
        "Sharp! 🫶 Come back anytime, I'll be here with more lekker deals! Stay blessed!",
        "Aweh! 🎯 Remember, I'm always here to help you save money! Toodles!",
        "Yoh! 💃 You're leaving? Come back soon, I'll have more surprises for you!"
    ],
    "positive_responses": [
        "Yasss! 🎉 That's a smart choice! You're becoming a shopping pro!",
        "Aweh! 💪 That's what I'm talking about! Saving money like a boss!",
        "Sharp sharp! 🫶 You're learning from the best! Keep it up!"
    ],
    "encouragement": [
        "You've got this! 💪 Every rand saved is a step towards your dreams!",
        "I believe in you! 🎯 Smart shopping is a superpower and you're mastering it!",
        "Look at you go! 🎉 Making smart choices like a true budget boss!"
    ]
}

# ============================================
# MMAPATENG'S LEARNING MEMORY
# ============================================

class MmapatengMemory:
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
                sentiment TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learned_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                response TEXT,
                usage_count INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                preferred_store TEXT,
                budget REAL,
                favorite_categories TEXT,
                    last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        self.conn.commit()
    
    def store_conversation(self, user_id, user_msg, bot_resp, sentiment="neutral"):
        self.conn.execute(
            "INSERT INTO conversations (user_id, user_message, bot_response, sentiment) VALUES (?, ?, ?, ?)",
            (user_id, user_msg, bot_resp, sentiment)
        )
        self.conn.commit()
    
    def learn_response(self, keyword, response):
        existing = self.conn.execute(
            "SELECT id, usage_count FROM learned_responses WHERE keyword = ?", (keyword,)
        ).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE learned_responses SET usage_count = usage_count + 1 WHERE id = ?",
                (existing[0],)
            )
        else:
            self.conn.execute(
                "INSERT INTO learned_responses (keyword, response) VALUES (?, ?)",
                (keyword, response)
            )
        self.conn.commit()
    
    def get_learned_response(self, keyword):
        results = self.conn.execute(
            "SELECT response FROM learned_responses WHERE keyword LIKE ? ORDER BY usage_count DESC LIMIT 3",
            (f"%{keyword}%",)
        ).fetchall()
        return [r[0] for r in results] if results else []
    
    def get_user_pref(self, user_id, key):
        row = self.conn.execute(
            "SELECT value FROM user_preferences WHERE user_id = ? AND key = ?",
            (user_id, key)
        ).fetchone()
        return row[0] if row else None
    
    def set_user_pref(self, user_id, key, value):
        self.conn.execute("""
            INSERT OR REPLACE INTO user_preferences (user_id, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, key, value))
        self.conn.commit()

# ============================================
# MMAPATENG'S INTELLIGENCE ENGINE
# ============================================

class MmapatengAI:
    def __init__(self):
        self.memory = MmapatengMemory()
        self.name = "Mmapateng"
        self.nickname = "The Real Johannah"
        
    def get_greeting(self):
        return random.choice(MMAPATENG_PERSONALITY["greetings"])
    
    def get_farewell(self):
        return random.choice(MMAPATENG_PERSONALITY["farewells"])
    
    def get_encouragement(self):
        return random.choice(MMAPATENG_PERSONALITY["encouragement"])
    
    def analyze_sentiment(self, text):
        positive_words = ["love", "great", "awesome", "lekker", "sharp", "nice", "good", "happy", "excited"]
        negative_words = ["sad", "bad", "terrible", "awful", "hate", "angry", "frustrated"]
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
    
    def extract_intent(self, text):
        text_lower = text.lower()
        
        intents = {
            "budget": ["budget", "money", "spend", "cost", "price", "expensive", "cheap", "save"],
            "food": ["food", "eat", "hungry", "meal", "cook", "restaurant", "grocery"],
            "clothing": ["clothes", "fashion", "wear", "dress", "shirt", "pants", "shoes"],
            "electronics": ["phone", "laptop", "tv", "computer", "gadget", "electronics"],
            "help": ["help", "how to", "what is", "tell me", "explain", "guide"],
            "greeting": ["hello", "hi", "hey", "yoh", "aweh", "howzit", "sup", "good morning", "good afternoon"],
            "farewell": ["bye", "goodbye", "see you", "later", "tata", "peace", "exit"],
            "deal": ["deal", "discount", "sale", "special", "promo", "offer"],
            "store": ["shop", "store", "mall", "retailer", "where to buy"],
            "price_check": ["price of", "how much", "cost of", "what does"]
        }
        
        for intent, keywords in intents.items():
            if any(k in text_lower for k in keywords):
                return intent
        return "general"
    
    def get_store_info(self, store_name=None):
        # Get from your database
        import sqlite3
        conn = sqlite3.connect("shoparound.db")
        conn.row_factory = sqlite3.Row
        if store_name:
            stores = conn.execute(
                "SELECT name, category, rating, delivery_fee FROM retailers WHERE name LIKE ? LIMIT 3",
                (f"%{store_name}%",)
            ).fetchall()
        else:
            stores = conn.execute("SELECT name, category, rating FROM retailers LIMIT 5").fetchall()
        conn.close()
        return stores
    
    def get_budget_advice(self, budget):
        if budget < 100:
            return f"Yoh! R{budget} is tight but possible! 💪 Focus on essentials: maize meal (R48), eggs (R42), and bread (R15). You'll have R{budget-105} left for veggies!",
        elif budget < 300:
            return f"Sharp! R{budget} can get you a solid shop! 🛒 Get maize meal, rice, chicken, eggs, and fresh veggies. You might even have some change for treats!"
        else:
            return f"Yasss! R{budget} is a proper budget! 🎉 You can get premium items at Woolworths or bulk buy at Makro. Consider getting some nice-to-haves!"
    
    def get_price_check(self, product):
        import sqlite3
        conn = sqlite3.connect("shoparound.db")
        conn.row_factory = sqlite3.Row
        # Get typical price from products table
        product_data = conn.execute(
            "SELECT product_name, typical_price FROM products WHERE product_name LIKE ? LIMIT 1",
            (f"%{product}%",)
        ).fetchone()
        conn.close()
        
        if product_data:
            return f"Aweh! {product_data['product_name']} typically costs around R{product_data['typical_price']:.2f}. Check Checkers or Shoprite for the best deals! 🛒"
        return f"Lemme check... I don't have exact price for {product} right now, but I'll learn for next time! Try Checkers or Shoprite for best prices! 💪"
    
    def chat(self, user_id, message):
        intent = self.extract_intent(message)
        sentiment = self.analyze_sentiment(message)
        
        # Check for budget
        budget_match = re.search(r'R(\d+)', message)
        if budget_match:
            budget = float(budget_match.group(1))
            response = self.get_budget_advice(budget)
            self.memory.store_conversation(user_id, message, response, sentiment)
            return response
        
        # Check for price check
        if intent == "price_check":
            product = message.lower().replace("price of", "").replace("how much is", "").replace("cost of", "").strip()
            response = self.get_price_check(product)
            self.memory.store_conversation(user_id, message, response, sentiment)
            return response
        
        # Handle intents
        if intent == "greeting":
            response = self.get_greeting()
        elif intent == "farewell":
            response = self.get_farewell()
        elif intent == "deal":
            response = "Yoh! 🔥 Hot deals right now: Checkers has 2-for-1 on bread, Shoprite has R5 off maize meal, and Woolworths has 20% off chicken! Don't miss out!"
        elif intent == "store":
            stores = self.get_store_info()
            response = f"Here are some popular stores: {', '.join([s['name'] for s in stores[:3]])}. Want details about any specific store? 🛒"
        elif intent == "budget":
            response = "I can help you budget! Just tell me your amount like 'R200' and I'll plan your shopping! 💰"
        else:
            # Check learned responses
            learned = self.memory.get_learned_response(message[:20])
            if learned:
                response = random.choice(learned)
            else:
                response = f"I hear you saying: '{message}'. Let me help! 💁‍♀️ You can ask me about budgets, prices, stores, or just chat with me! What would you like to know?"
                self.memory.learn_response(message[:20], response)
        
        self.memory.store_conversation(user_id, message, response, sentiment)
        return response

# Initialize Mmapateng
mmapateng = MmapatengAI()

def add_mmapateng_routes(app):
    """Add Mmapateng AI assistant to your app"""
    
    @app.route("/api/mmapateng/chat", methods=["POST"])
    def mmapateng_chat():
        data = request.get_json(force=True)
        user_id = session.get("user_id", "guest_" + request.remote_addr or "anonymous")
        message = data.get("message", "")
        
        if not message:
            return jsonify({"error": "Say something to Mmapateng!"}), 400
        
        response = mmapateng.chat(user_id, message)
        
        return jsonify({
            "response": response,
            "sender": "Mmapateng",
            "nickname": "The Real Johannah",
            "personality": "confident, positive, engaging"
        })
    
    @app.route("/api/mmapateng/info", methods=["GET"])
    def mmapateng_info():
        return jsonify({
            "name": "Mmapateng",
            "nickname": "The Real Johannah",
            "personality": "Confident, positive, helpful, engaging",
            "skills": ["Budget planning", "Price checking", "Store recommendations", "Deal finding", "Shopping advice"],
            "languages": ["English", "South African Slang", "Tsonga", "Zulu"],
            "motto": "Save money, live better! 🫶"
        })
    
    @app.route("/api/mmapateng/encourage", methods=["GET"])
    def mmapateng_encourage():
        return jsonify({"message": mmapateng.get_encouragement()})
    
    print("🧠 Mmapateng 'The Real Johannah' AI Assistant Active!")
    print("   💬 Intelligent Mall Info Office")
    print("   🎯 Continuous Learning Enabled")
    print("   💪 Confident, Positive Personality")
    return app

# HTML Chat Widget for embedding
MMAPATENG_WIDGET = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        .mmapateng-chat {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            font-family: 'Inter', system-ui, sans-serif;
        }
        
        .chat-button {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s;
        }
        
        .chat-button:hover {
            transform: scale(1.1);
        }
        
        .chat-window {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: none;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-window.open {
            display: flex;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-header h3 {
            margin: 0;
            font-size: 1rem;
        }
        
        .close-chat {
            cursor: pointer;
            font-size: 1.2rem;
        }
        
        .chat-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 10px;
            display: flex;
        }
        
        .message.bot {
            justify-content: flex-start;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        
        .bot .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 5px;
        }
        
        .user .message-content {
            background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .chat-input {
            padding: 15px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 25px;
            outline: none;
        }
        
        .chat-input button {
            background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
        }
        
        .typing {
            display: none;
            padding: 10px;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
<div class="mmapateng-chat">
    <div class="chat-button" onclick="toggleChat()">
        <span style="font-size: 28px;">💬</span>
    </div>
    <div class="chat-window" id="chatWindow">
        <div class="chat-header">
            <h3>💬 Mmapateng - The Real Johannah</h3>
            <span class="close-chat" onclick="toggleChat()">✕</span>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div class="message-content">
                    🫶 Yoh! Sharp sharp! I'm Mmapateng, your mall bestie! Ask me anything about shopping, budgets, or just chat with me!
                </div>
            </div>
        </div>
        <div class="typing" id="typing">Mmapateng is typing...</div>
        <div class="chat-input">
            <input type="text" id="chatInput" placeholder="Ask Mmapateng..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>
</div>

<script>
    function toggleChat() {
        const window = document.getElementById('chatWindow');
        window.classList.toggle('open');
    }
    
    async function sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        if (!message) return;
        
        // Add user message
        const messagesDiv = document.getElementById('chatMessages');
        messagesDiv.innerHTML += `
            <div class="message user">
                <div class="message-content">${escapeHtml(message)}</div>
            </div>
        `;
        input.value = '';
        
        // Show typing indicator
        document.getElementById('typing').style.display = 'block';
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        // Send to API
        try {
            const response = await fetch('/api/mmapateng/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            const data = await response.json();
            
            // Hide typing indicator
            document.getElementById('typing').style.display = 'none';
            
            // Add bot response
            messagesDiv.innerHTML += `
                <div class="message bot">
                    <div class="message-content">${escapeHtml(data.response)}</div>
                </div>
            `;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        } catch (error) {
            document.getElementById('typing').style.display = 'none';
            messagesDiv.innerHTML += `
                <div class="message bot">
                    <div class="message-content">🫶 Oops! Let me try again. What can I help you with?</div>
                </div>
            `;
        }
    }
    
    function handleKeyPress(event) {
        if (event.key === 'Enter') {
            sendMessage();
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
'''

def add_mmapateng_widget(app):
    @app.route("/mmapateng-widget")
    def mmapateng_widget():
        return MMAPATENG_WIDGET
    
    print("✅ Mmapateng chat widget available at /mmapateng-widget")
    return app
