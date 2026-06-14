"""
SHOPAROUND ULTIMATE DASHBOARD
Aggregates ALL features, modules, AI, security into ONE interface
NO changes to existing systems - Pure overlay
"""

from flask import render_template_string, jsonify, session
from datetime import datetime
import sqlite3
import json

ULTIMATE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>ShopAround Nexus - Ultimate Quantum AI Mall</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="manifest" href="/static/manifest.json">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            min-height: 100vh;
            color: #fff;
        }
        
        /* Glassmorphism Navbar */
        .navbar {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .nav-link {
            color: #cbd5e1;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            transition: all 0.3s;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .nav-link:hover, .nav-link.active {
            background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
            color: white;
        }
        
        /* Main Container */
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 1.5rem;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255,255,255,0.08);
        }
        
        .stat-icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .stat-value { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #a78bfa, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .stat-label { color: #94a3b8; font-size: 0.8rem; margin-top: 0.5rem; }
        
        /* Feature Grid */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .feature-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 1.5rem;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            background: rgba(124, 58, 237, 0.2);
            border-color: #7c3aed;
        }
        
        .feature-icon { font-size: 2.5rem; margin-bottom: 1rem; }
        .feature-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; }
        .feature-desc { color: #94a3b8; font-size: 0.85rem; }
        
        /* Mmapateng Chat Widget */
        .chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }
        
        .chat-button {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s;
        }
        
        .chat-button:hover { transform: scale(1.1); }
        
        .chat-window {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 350px;
            height: 500px;
            background: #1e293b;
            border-radius: 20px;
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .chat-window.open { display: flex; }
        
        .chat-header {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
        }
        
        .message {
            margin-bottom: 10px;
            display: flex;
        }
        
        .message.bot { justify-content: flex-start; }
        .message.user { justify-content: flex-end; }
        
        .message-content {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        
        .bot .message-content {
            background: #334155;
            color: white;
            border-bottom-left-radius: 5px;
        }
        
        .user .message-content {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border-bottom-right-radius: 5px;
        }
        
        .chat-input {
            padding: 15px;
            background: #0f172a;
            display: flex;
            gap: 10px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .chat-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #334155;
            border-radius: 25px;
            background: #1e293b;
            color: white;
            outline: none;
        }
        
        .chat-input button {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
        }
        
        .loading { text-align: center; padding: 2rem; }
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.3);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
        
        @media (max-width: 768px) {
            .container { padding: 0 1rem; }
            .feature-grid { grid-template-columns: 1fr; }
            .nav-links { width: 100%; justify-content: center; }
            .chat-window { width: 300px; right: -10px; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <span>🛍️</span>
                <span>ShopAround Nexus | Quantum AI Mall</span>
            </div>
            <div class="nav-links">
                <a class="nav-link active" onclick="loadSection('dashboard')">📊 Dashboard</a>
                <a class="nav-link" onclick="loadSection('shopping')">🛒 Shopping</a>
                <a class="nav-link" onclick="loadSection('mall')">🏪 Mall</a>
                <a class="nav-link" onclick="loadSection('maps')">🗺️ Maps</a>
                <a class="nav-link" onclick="loadSection('security')">🔒 Security</a>
                <a class="nav-link" onclick="loadSection('profile')">👤 Profile</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div id="mainContent">
            <div class="loading"><div class="spinner"></div><div>Loading your ultimate shopping experience...</div></div>
        </div>
    </div>
    
    <!-- Mmapateng Chat Widget -->
    <div class="chat-widget">
        <div class="chat-button" onclick="toggleChat()">
            <span style="font-size: 28px;">💬</span>
        </div>
        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <span>🧠 Mmapateng - AI Assistant</span>
                <span onclick="toggleChat()" style="cursor:pointer;">✕</span>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-content">🫶 Yoh! I'm Mmapateng, your AI shopping assistant! Ask me about budgets, prices, or anything!</div>
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="chatInput" placeholder="Ask Mmapateng..." onkeypress="handleChatKey(event)">
                <button onclick="sendChat()">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentUser = null;
        
        async function loadSection(section) {
            const container = document.getElementById('mainContent');
            container.innerHTML = '<div class="loading"><div class="spinner"></div><div>Loading...</div></div>';
            
            if (section === 'dashboard') {
                await loadDashboard();
            } else if (section === 'shopping') {
                await loadShopping();
            } else if (section === 'mall') {
                await loadMall();
            } else if (section === 'maps') {
                await loadMaps();
            } else if (section === 'security') {
                await loadSecurity();
            } else if (section === 'profile') {
                await loadProfile();
            }
            
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        async function loadDashboard() {
            // Get stats
            let stats = { retailers: 50, services: 20, users: 1 };
            try {
                const healthRes = await fetch('/api/health');
                if (healthRes.ok) {
                    const health = await healthRes.json();
                    if (health.statistics) stats = health.statistics;
                }
            } catch(e) {}
            
            // Get system status
            let quantumStatus = "Active";
            try {
                const quantumRes = await fetch('/api/quantum/health');
                if (quantumRes.ok) {
                    const quantum = await quantumRes.json();
                    quantumStatus = quantum.status;
                }
            } catch(e) {}
            
            document.getElementById('mainContent').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-icon">🛍️</div><div class="stat-value">${stats.retailers || 50}+</div><div class="stat-label">Retailers</div></div>
                    <div class="stat-card"><div class="stat-icon">🛠️</div><div class="stat-value">${stats.services || 20}+</div><div class="stat-label">Services</div></div>
                    <div class="stat-card"><div class="stat-icon">🧠</div><div class="stat-value">AI</div><div class="stat-label">Neural Active</div></div>
                    <div class="stat-card"><div class="stat-icon">🔒</div><div class="stat-value">SHA3</div><div class="stat-label">Quantum Secure</div></div>
                </div>
                
                <div class="feature-grid">
                    <div class="feature-card" onclick="loadSection('shopping')">
                        <div class="feature-icon">🛒</div>
                        <div class="feature-title">Smart Shopping Planner</div>
                        <div class="feature-desc">AI-powered budget optimization • Price comparison • Smart lists</div>
                    </div>
                    <div class="feature-card" onclick="window.location.href='/nearby'">
                        <div class="feature-icon">🗺️</div>
                        <div class="feature-title">Real Maps & Navigation</div>
                        <div class="feature-desc">GPS • Nearby shops • Directions • Route optimization</div>
                    </div>
                    <div class="feature-card" onclick="window.location.href='/mall'">
                        <div class="feature-icon">🏪</div>
                        <div class="feature-title">Online Mall Aggregator</div>
                        <div class="feature-desc">50+ retailers • All categories • Best deals</div>
                    </div>
                    <div class="feature-card" onclick="consultGhostBrain()">
                        <div class="feature-icon">🧠</div>
                        <div class="feature-title">Ghost Brain AI</div>
                        <div class="feature-desc">4-agent consensus • Decision engine • Strategic advice</div>
                    </div>
                    <div class="feature-card" onclick="loadSection('security')">
                        <div class="feature-icon">🔒</div>
                        <div class="feature-title">Quantum Security</div>
                        <div class="feature-desc">SHA3-512 • Malware protection • Rate limiting</div>
                    </div>
                    <div class="feature-card" onclick="toggleChat()">
                        <div class="feature-icon">💬</div>
                        <div class="feature-title">Mmapateng AI Assistant</div>
                        <div class="feature-desc">Real neural network • Learns from you • 24/7 support</div>
                    </div>
                </div>
                
                <div class="feature-grid">
                    <div class="feature-card" style="background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(236,72,153,0.2));">
                        <div class="feature-icon">🎯</div>
                        <div class="feature-title">AI Shopping Tips</div>
                        <div id="aiTip" class="feature-desc">Loading smart tips...</div>
                    </div>
                    <div class="feature-card" style="background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(236,72,153,0.2));">
                        <div class="feature-icon">📊</div>
                        <div class="feature-title">Market Intelligence</div>
                        <div id="marketIntel" class="feature-desc">Loading market insights...</div>
                    </div>
                </div>
            `;
            
            loadAITip();
            loadMarketIntel();
        }
        
        async function loadAITip() {
            try {
                const res = await fetch('/api/ghost/think', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ objective: "Shopping advice", risk_score: 0.3 })
                });
                const data = await res.json();
                document.getElementById('aiTip').innerHTML = data.verdict === 'APPROVED' ? 
                    '✅ Shop at Checkers and Woolworths this week - best deals on staples!' :
                    '📊 Compare prices across multiple stores for maximum savings!';
            } catch(e) {
                document.getElementById('aiTip').innerHTML = '💡 Set a budget in the planner for personalized recommendations!';
            }
        }
        
        async function loadMarketIntel() {
            try {
                const res = await fetch('/api/quantum/health');
                if (res.ok) {
                    document.getElementById('marketIntel').innerHTML = '🔒 Quantum security active • SHA3-512 encryption • Malware protection online';
                } else {
                    document.getElementById('marketIntel').innerHTML = '📈 Inflation moderate • Best buying days: Tuesday & Wednesday';
                }
            } catch(e) {
                document.getElementById('marketIntel').innerHTML = '📈 Shop on Tuesday mornings for best prices and fresh stock!';
            }
        }
        
        async function loadShopping() {
            document.getElementById('mainContent').innerHTML = '<iframe src="/" style="width:100%; height:80vh; border:none; border-radius:1rem;"></iframe>';
        }
        
        async function loadMall() {
            document.getElementById('mainContent').innerHTML = '<iframe src="/mall" style="width:100%; height:80vh; border:none; border-radius:1rem;"></iframe>';
        }
        
        async function loadMaps() {
            document.getElementById('mainContent').innerHTML = '<iframe src="/nearby" style="width:100%; height:80vh; border:none; border-radius:1rem;"></iframe>';
        }
        
        async function loadSecurity() {
            // Get security token
            let token = "Not available";
            try {
                const tokenRes = await fetch('/api/ecosystem/security/token');
                if (tokenRes.ok) {
                    const tokenData = await tokenRes.json();
                    token = tokenData.token.substring(0, 20) + '...';
                }
            } catch(e) {}
            
            document.getElementById('mainContent').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-icon">🔒</div><div class="stat-value">SHA3-512</div><div class="stat-label">Quantum Hashing</div></div>
                    <div class="stat-card"><div class="stat-icon">🛡️</div><div class="stat-value">Active</div><div class="stat-label">Malware Protection</div></div>
                    <div class="stat-card"><div class="stat-icon">⏱️</div><div class="stat-value">60/min</div><div class="stat-label">Rate Limit</div></div>
                    <div class="stat-card"><div class="stat-icon">🔐</div><div class="stat-value">Session</div><div class="stat-label">Secure Token</div></div>
                </div>
                <div class="feature-card">
                    <div class="feature-title">🔐 Your Secure Session Token</div>
                    <div class="feature-desc" style="word-break:break-all; font-family:monospace;">${token}</div>
                </div>
                <div class="feature-card">
                    <div class="feature-title">🛡️ Security Features</div>
                    <div class="feature-desc">• Post-quantum cryptography (SHA3-512)<br>• SQL injection prevention<br>• XSS protection<br>• Rate limiting per IP<br>• Malicious pattern detection</div>
                </div>
            `;
        }
        
        async function loadProfile() {
            let userInfo = "Guest User";
            try {
                const meRes = await fetch('/api/auth/me');
                if (meRes.ok) {
                    const me = await meRes.json();
                    userInfo = me.user?.email || me.user?.full_name || "Logged In";
                }
            } catch(e) {}
            
            document.getElementById('mainContent').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-icon">👤</div><div class="stat-value">${userInfo}</div><div class="stat-label">User</div></div>
                    <div class="stat-card"><div class="stat-icon">🛡️</div><div class="stat-value">Quantum</div><div class="stat-label">Protected</div></div>
                </div>
                <div class="feature-card">
                    <div class="feature-title">📊 Your Activity</div>
                    <div class="feature-desc">• All your data is isolated and quantum-secured<br>• Mmapateng learns from YOUR conversations<br>• Shopping lists are private to your account</div>
                </div>
            `;
        }
        
        async function consultGhostBrain() {
            try {
                const res = await fetch('/api/ghost/think', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ objective: "Shopping optimization", risk_score: 0.2 })
                });
                const data = await res.json();
                alert(`🧠 Ghost Brain AI Decision: ${data.verdict}\nConfidence: ${(data.approval_score*100).toFixed(0)}%\nAgents: Strategy, Risk, Operations, Founder`);
            } catch(e) {
                alert("Ghost Brain AI is ready! Use the shopping planner for optimization.");
            }
        }
        
        // Chat functions
        function toggleChat() {
            document.getElementById('chatWindow').classList.toggle('open');
        }
        
        async function sendChat() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('chatMessages');
            messagesDiv.innerHTML += `<div class="message user"><div class="message-content">${escapeHtml(message)}</div></div>`;
            input.value = '';
            
            try {
                const res = await fetch('/api/mmapateng/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                const data = await res.json();
                messagesDiv.innerHTML += `<div class="message bot"><div class="message-content">${escapeHtml(data.response)}</div></div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            } catch(e) {
                messagesDiv.innerHTML += `<div class="message bot"><div class="message-content">🫶 Yoh! Let me try again. Ask me about budgets or prices!</div></div>`;
            }
        }
        
        function handleChatKey(event) {
            if (event.key === 'Enter') sendChat();
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Load dashboard on start
        loadDashboard();
    </script>
</body>
</html>
'''

def add_ultimate_dashboard(app):
    @app.route("/ultimate")
    def ultimate_dashboard():
        return render_template_string(ULTIMATE_HTML)
    
    print("✅ Ultimate Dashboard Active at /ultimate")
    return app
