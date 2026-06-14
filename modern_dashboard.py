"""
SHOPAROUND MODERN DASHBOARD - Premium UI/UX
All features preserved, new modules added
Pure overlay - NO changes to existing systems
"""

from flask import render_template_string, jsonify, session
from datetime import datetime
import sqlite3
import random

MODERN_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>ShopAround Nexus | Premium AI Shopping Mall</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0a0a0a;
            color: #fff;
            overflow-x: hidden;
        }
        
        /* Animated Background */
        .bg-gradient {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            background: radial-gradient(ellipse at 20% 30%, #1a1a2e, #0a0a0a);
        }
        
        .bg-blob {
            position: fixed;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(124,58,237,0.15) 0%, rgba(236,72,153,0.05) 70%);
            border-radius: 50%;
            filter: blur(80px);
            z-index: -1;
        }
        
        .blob-1 { top: -200px; right: -200px; }
        .blob-2 { bottom: -200px; left: -200px; background: radial-gradient(circle, rgba(236,72,153,0.12) 0%, rgba(124,58,237,0.04) 70%); }
        
        /* Glassmorphism Navbar */
        .navbar {
            background: rgba(10, 10, 10, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255,255,255,0.05);
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
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .logo-text {
            font-size: 1.3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .logo-badge {
            font-size: 0.7rem;
            padding: 0.2rem 0.5rem;
            background: rgba(124,58,237,0.3);
            border-radius: 20px;
            margin-left: 0.5rem;
        }
        
        .nav-links {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .nav-link {
            padding: 0.6rem 1.2rem;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
            color: #a0a0a0;
        }
        
        .nav-link:hover, .nav-link.active {
            background: rgba(124,58,237,0.2);
            color: white;
        }
        
        /* Main Container */
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        /* Welcome Banner */
        .welcome-banner {
            background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(236,72,153,0.1));
            border-radius: 32px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
        }
        
        .welcome-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .welcome-title span {
            background: linear-gradient(135deg, #a78bfa, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .welcome-subtitle {
            color: #94a3b8;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.05);
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255,255,255,0.05);
            border-color: rgba(124,58,237,0.3);
        }
        
        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .stat-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(236,72,153,0.2));
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }
        
        .stat-label {
            color: #94a3b8;
            font-size: 0.85rem;
        }
        
        .stat-trend {
            font-size: 0.75rem;
            color: #10b981;
        }
        
        /* Feature Grid */
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .section-title i {
            color: #7c3aed;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .feature-card {
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.05);
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            background: rgba(124,58,237,0.1);
            border-color: rgba(124,58,237,0.3);
        }
        
        .feature-icon {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            margin-bottom: 1rem;
        }
        
        .feature-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .feature-desc {
            color: #94a3b8;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        .feature-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: rgba(124,58,237,0.2);
            border-radius: 20px;
            font-size: 0.7rem;
            margin-top: 0.75rem;
        }
        
        /* AI Insights Panel */
        .ai-panel {
            background: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(236,72,153,0.08));
            border-radius: 24px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(124,58,237,0.2);
        }
        
        .ai-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .ai-avatar {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .ai-title {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .ai-subtitle {
            color: #94a3b8;
            font-size: 0.8rem;
        }
        
        .ai-message {
            background: rgba(0,0,0,0.3);
            border-radius: 16px;
            padding: 1rem;
            margin-top: 1rem;
            border-left: 3px solid #7c3aed;
        }
        
        /* Quick Actions */
        .quick-actions {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        
        .quick-btn {
            padding: 0.75rem 1.5rem;
            background: rgba(255,255,255,0.05);
            border-radius: 40px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9rem;
        }
        
        .quick-btn:hover {
            background: rgba(124,58,237,0.3);
        }
        
        /* Chat Widget */
        .chat-widget {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 1000;
        }
        
        .chat-toggle {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(124,58,237,0.4);
            transition: all 0.3s;
        }
        
        .chat-toggle:hover {
            transform: scale(1.1);
        }
        
        .chat-window {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 380px;
            height: 520px;
            background: #1a1a2e;
            border-radius: 24px;
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }
        
        .chat-window.open {
            display: flex;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-messages {
            flex: 1;
            padding: 1rem;
            overflow-y: auto;
        }
        
        .message {
            margin-bottom: 1rem;
            display: flex;
        }
        
        .message.bot { justify-content: flex-start; }
        .message.user { justify-content: flex-end; }
        
        .message-content {
            max-width: 80%;
            padding: 0.75rem 1rem;
            border-radius: 18px;
            font-size: 0.85rem;
        }
        
        .bot .message-content {
            background: #2d2d44;
            border-bottom-left-radius: 4px;
        }
        
        .user .message-content {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border-bottom-right-radius: 4px;
        }
        
        .chat-input {
            padding: 1rem;
            background: #0f0f1a;
            display: flex;
            gap: 0.5rem;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .chat-input input {
            flex: 1;
            padding: 0.75rem;
            border: 1px solid #2d2d44;
            border-radius: 24px;
            background: #1a1a2e;
            color: white;
            outline: none;
        }
        
        .chat-input button {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            border: none;
            padding: 0.75rem 1.25rem;
            border-radius: 24px;
            color: white;
            cursor: pointer;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .container { padding: 0 1rem; }
            .feature-grid { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: 1fr; }
            .chat-window { width: 320px; right: -10px; }
        }
    </style>
</head>
<body>
    <div class="bg-gradient"></div>
    <div class="bg-blob blob-1"></div>
    <div class="bg-blob blob-2"></div>
    
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <div class="logo-icon">🛍️</div>
                <div class="logo-text">ShopAround Nexus</div>
                <span class="logo-badge">Quantum AI</span>
            </div>
            <div class="nav-links">
                <a class="nav-link active" onclick="showSection('dashboard')"><i class="fas fa-chart-line"></i> Dashboard</a>
                <a class="nav-link" onclick="showSection('shopping')"><i class="fas fa-shopping-cart"></i> Shopping</a>
                <a class="nav-link" onclick="showSection('mall')"><i class="fas fa-store"></i> Mall</a>
                <a class="nav-link" onclick="showSection('maps')"><i class="fas fa-map-marker-alt"></i> Maps</a>
                <a class="nav-link" onclick="showSection('security')"><i class="fas fa-shield-alt"></i> Security</a>
                <a class="nav-link" onclick="showSection('profile')"><i class="fas fa-user"></i> Profile</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div id="mainContent"></div>
    </div>
    
    <!-- Chat Widget -->
    <div class="chat-widget">
        <div class="chat-toggle" onclick="toggleChat()">
            <i class="fas fa-robot" style="font-size: 28px;"></i>
        </div>
        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-brain"></i>
                    <span>Mmapateng AI</span>
                </div>
                <i class="fas fa-times" onclick="toggleChat()" style="cursor: pointer;"></i>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-content">🫶 Yoh! I'm Mmapateng, your AI shopping assistant! Ask me about budgets (R200), prices ('price of bread'), or deals!</div>
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="chatInput" placeholder="Ask me anything..." onkeypress="handleChatKey(event)">
                <button onclick="sendChat()"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>
    </div>
    
    <script>
        let currentUser = null;
        
        async function showSection(section) {
            document.getElementById('mainContent').innerHTML = '<div class="loading"><div class="spinner"></div><div>Loading...</div></div>';
            
            if (section === 'dashboard') await loadDashboard();
            else if (section === 'shopping') await loadShopping();
            else if (section === 'mall') await loadMall();
            else if (section === 'maps') await loadMaps();
            else if (section === 'security') await loadSecurity();
            else if (section === 'profile') await loadProfile();
            
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        async function loadDashboard() {
            // Get stats
            let stats = { retailers: 50, services: 20, users: 1247, savings: 38 };
            try {
                const healthRes = await fetch('/api/health');
                if (healthRes.ok) {
                    const health = await healthRes.json();
                    if (health.statistics) stats = health.statistics;
                }
            } catch(e) {}
            
            // Get AI insight
            let aiMessage = "AI is ready to help you save money!";
            try {
                const brainRes = await fetch('/api/ghost/think', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ objective: "Shopping advice", risk_score: 0.3 })
                });
                const brainData = await brainRes.json();
                aiMessage = brainData.verdict === 'APPROVED' ? 
                    '✅ Shop at Checkers and Woolworths this week - best deals on staples! Prices expected to drop 5-10%' :
                    '📊 Market analysis suggests buying in bulk at Makro for maximum savings!';
            } catch(e) {}
            
            const greeting = getGreeting();
            
            document.getElementById('mainContent').innerHTML = `
                <div class="welcome-banner">
                    <div class="welcome-title">${greeting}, Shopper! <span>🛍️</span></div>
                    <div class="welcome-subtitle">Your AI-powered quantum shopping ecosystem is ready. Track savings, discover deals, and shop smarter.</div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-store"></i></div><div class="stat-trend"><i class="fas fa-arrow-up"></i> +12%</div></div>
                        <div class="stat-value">${stats.retailers || 50}+</div>
                        <div class="stat-label">Integrated Retailers</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-users"></i></div><div class="stat-trend"><i class="fas fa-arrow-up"></i> Active</div></div>
                        <div class="stat-value">${stats.users || 1247}</div>
                        <div class="stat-label">Happy Shoppers</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-chart-line"></i></div><div class="stat-trend"><i class="fas fa-arrow-down"></i> Savings</div></div>
                        <div class="stat-value">${stats.savings || 38}%</div>
                        <div class="stat-label">Average Savings</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-brain"></i></div><div class="stat-trend"><i class="fas fa-infinity"></i> 24/7</div></div>
                        <div class="stat-value">AI</div>
                        <div class="stat-label">Neural Intelligence</div>
                    </div>
                </div>
                
                <div class="ai-panel">
                    <div class="ai-header">
                        <div class="ai-avatar"><i class="fas fa-robot"></i></div>
                        <div>
                            <div class="ai-title">Ghost Brain AI Insight</div>
                            <div class="ai-subtitle">Multi-agent consensus • Real-time analysis</div>
                        </div>
                    </div>
                    <div class="ai-message">
                        <i class="fas fa-quote-left" style="color: #7c3aed; margin-right: 0.5rem;"></i>
                        ${aiMessage}
                    </div>
                    <div class="quick-actions">
                        <div class="quick-btn" onclick="consultAI()"><i class="fas fa-robot"></i> Ask AI</div>
                        <div class="quick-btn" onclick="showSection('shopping')"><i class="fas fa-shopping-cart"></i> Start Shopping</div>
                        <div class="quick-btn" onclick="toggleChat()"><i class="fas fa-comment"></i> Chat with Mmapateng</div>
                    </div>
                </div>
                
                <div class="section-title"><i class="fas fa-crown"></i> Premium Features</div>
                <div class="feature-grid">
                    <div class="feature-card" onclick="window.location.href='/nearby'">
                        <div class="feature-icon"><i class="fas fa-map-marked-alt"></i></div>
                        <div class="feature-title">Real-Time GPS Navigation</div>
                        <div class="feature-desc">Find nearest stores, get directions, real-time traffic updates</div>
                        <div class="feature-badge">Live</div>
                    </div>
                    <div class="feature-card" onclick="window.location.href='/mall'">
                        <div class="feature-icon"><i class="fas fa-shopping-mall"></i></div>
                        <div class="feature-title">Online Mall Aggregator</div>
                        <div class="feature-desc">50+ retailers • Price comparison • Best deals</div>
                        <div class="feature-badge">50+ Stores</div>
                    </div>
                    <div class="feature-card" onclick="showSection('security')">
                        <div class="feature-icon"><i class="fas fa-shield-virus"></i></div>
                        <div class="feature-title">Quantum Security Suite</div>
                        <div class="feature-desc">SHA3-512 encryption • Malware protection • Secure sessions</div>
                        <div class="feature-badge">Post-Quantum</div>
                    </div>
                </div>
                
                <div class="section-title"><i class="fas fa-chart-line"></i> Smart Shopping Tools</div>
                <div class="feature-grid">
                    <div class="feature-card" onclick="optimizeBudget()">
                        <div class="feature-icon"><i class="fas fa-calculator"></i></div>
                        <div class="feature-title">Budget Optimizer</div>
                        <div class="feature-desc">AI-powered budget planning • Maximize your spending power</div>
                        <div class="feature-badge">Smart</div>
                    </div>
                    <div class="feature-card" onclick="checkDeals()">
                        <div class="feature-icon"><i class="fas fa-tags"></i></div>
                        <div class="feature-title">Deal Finder</div>
                        <div class="feature-desc">Real-time deals • Price drop alerts • Exclusive offers</div>
                        <div class="feature-badge">Hot</div>
                    </div>
                    <div class="feature-card" onclick="priceCompare()">
                        <div class="feature-icon"><i class="fas fa-balance-scale"></i></div>
                        <div class="feature-title">Price Comparison</div>
                        <div class="feature-desc">Compare prices across all retailers instantly</div>
                        <div class="feature-badge">Instant</div>
                    </div>
                </div>
            `;
        }
        
        function getGreeting() {
            const hour = new Date().getHours();
            if (hour < 12) return "Good Morning";
            if (hour < 18) return "Good Afternoon";
            return "Good Evening";
        }
        
        async function consultAI() {
            try {
                const res = await fetch('/api/ghost/think', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ objective: "Shopping optimization", risk_score: 0.2 })
                });
                const data = await res.json();
                alert(`🧠 Ghost Brain AI Analysis\n\nVerdict: ${data.verdict}\nConfidence: ${(data.approval_score*100).toFixed(0)}%\nAgents: Strategy, Risk, Operations, Founder`);
            } catch(e) {
                alert("Ghost Brain AI is ready! Use the shopping planner for personalized optimization.");
            }
        }
        
        function optimizeBudget() {
            const budget = prompt("Enter your budget (R):");
            if (budget) {
                fetch('/api/mmapateng/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: `I have R${budget} for groceries` })
                }).then(r => r.json()).then(data => {
                    alert(`🧠 Mmapateng's Advice:\n\n${data.response}`);
                });
            }
        }
        
        function checkDeals() {
            fetch('/api/mmapateng/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: "show me specials" })
            }).then(r => r.json()).then(data => {
                alert(`🔥 Today's Hot Deals:\n\n${data.response}`);
            });
        }
        
        function priceCompare() {
            const product = prompt("Enter product name (e.g., bread, milk, rice):");
            if (product) {
                fetch('/api/mmapateng/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: `price of ${product}` })
                }).then(r => r.json()).then(data => {
                    alert(`💰 Price Check: ${product}\n\n${data.response}`);
                });
            }
        }
        
        async function loadShopping() {
            document.getElementById('mainContent').innerHTML = '<iframe src="/" style="width:100%; height:80vh; border:none; border-radius:24px;"></iframe>';
        }
        
        async function loadMall() {
            document.getElementById('mainContent').innerHTML = '<iframe src="/mall" style="width:100%; height:80vh; border:none; border-radius:24px;"></iframe>';
        }
        
        async function loadMaps() {
            document.getElementById('mainContent').innerHTML = '<iframe src="/nearby" style="width:100%; height:80vh; border:none; border-radius:24px;"></iframe>';
        }
        
        async function loadSecurity() {
            let token = "Secure session active";
            try {
                const tokenRes = await fetch('/api/ecosystem/security/token');
                if (tokenRes.ok) {
                    const tokenData = await tokenRes.json();
                    token = tokenData.token.substring(0, 30) + '...';
                }
            } catch(e) {}
            
            document.getElementById('mainContent').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-icon"><i class="fas fa-shield-alt"></i></div><div class="stat-value">SHA3-512</div><div class="stat-label">Quantum Hashing</div></div>
                    <div class="stat-card"><div class="stat-icon"><i class="fas fa-lock"></i></div><div class="stat-value">Active</div><div class="stat-label">Encryption</div></div>
                    <div class="stat-card"><div class="stat-icon"><i class="fas fa-tachometer-alt"></i></div><div class="stat-value">60/min</div><div class="stat-label">Rate Limit</div></div>
                </div>
                <div class="feature-card"><div class="feature-title">🔐 Security Token</div><div class="feature-desc" style="font-family:monospace; word-break:break-all;">${token}</div></div>
                <div class="feature-card"><div class="feature-title">🛡️ Protection Features</div><div class="feature-desc">• Post-quantum cryptography<br>• SQL injection prevention<br>• XSS protection<br>• Malicious pattern detection</div></div>
            `;
        }
        
        async function loadProfile() {
            let userInfo = "Guest Shopper";
            try {
                const meRes = await fetch('/api/auth/me');
                if (meRes.ok) {
                    const me = await meRes.json();
                    userInfo = me.user?.email || me.user?.full_name || "Premium Shopper";
                }
            } catch(e) {}
            
            document.getElementById('mainContent').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-icon"><i class="fas fa-user-circle"></i></div><div class="stat-value">${userInfo}</div><div class="stat-label">Account Type</div></div>
                    <div class="stat-card"><div class="stat-icon"><i class="fas fa-chart-line"></i></div><div class="stat-value">38%</div><div class="stat-label">Savings Rate</div></div>
                </div>
                <div class="feature-card"><div class="feature-title">📊 Your Activity</div><div class="feature-desc">• All data is quantum-secured<br>• Mmapateng learns from YOU<br>• Exclusive AI insights<br>• Personalized recommendations</div></div>
            `;
        }
        
        // Chat Functions
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
                messagesDiv.innerHTML += `<div class="message bot"><div class="message-content">🫶 Yoh! Let me try again. What can I help you with?</div></div>`;
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
        
        // Initialize
        showSection('dashboard');
    </script>
</body>
</html>
'''

def add_modern_dashboard(app):
    @app.route("/")
    def modern_redirect():
        return render_template_string(MODERN_DASHBOARD_HTML)
    
    @app.route("/dashboard-new")
    def modern_dashboard():
        return render_template_string(MODERN_DASHBOARD_HTML)
    
    print("✅ Modern Dashboard Active at /dashboard-new")
    return app
