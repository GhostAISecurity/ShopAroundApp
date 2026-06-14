"""
BEAUTIFUL DASHBOARD OVERLAY
Pure addition - No changes to your existing system
Adds a modern dashboard at /dashboard
"""

from flask import render_template_string, jsonify, session
from datetime import datetime
import sqlite3

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>ShopAround Dashboard - AI Shopping Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
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
        
        /* Modern Glassmorphism Navbar */
        .navbar {
            background: rgba(15, 23, 42, 0.8);
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
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
        }
        
        .nav-link {
            color: #cbd5e1;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .nav-link:hover {
            background: rgba(255,255,255,0.1);
            color: white;
        }
        
        .nav-link.active {
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
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 1.5rem;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            background: rgba(255,255,255,0.08);
        }
        
        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-label {
            color: #94a3b8;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        
        /* Main Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        /* Cards */
        .card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 1.5rem;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Activity List */
        .activity-list {
            list-style: none;
        }
        
        .activity-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .activity-icon {
            width: 40px;
            height: 40px;
            background: rgba(124, 58, 237, 0.2);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }
        
        .activity-details {
            flex: 1;
        }
        
        .activity-title {
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .activity-time {
            font-size: 0.75rem;
            color: #94a3b8;
        }
        
        /* Quick Actions */
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .action-btn {
            background: rgba(124, 58, 237, 0.2);
            border: 1px solid rgba(124, 58, 237, 0.4);
            padding: 1rem;
            border-radius: 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .action-btn:hover {
            background: rgba(124, 58, 237, 0.4);
            transform: translateY(-3px);
        }
        
        .action-emoji {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }
        
        .action-text {
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        /* Shopping List */
        .shopping-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .shopping-name {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .shopping-price {
            font-weight: 600;
            color: #a78bfa;
        }
        
        .progress-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 1rem;
            height: 8px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #7c3aed, #ec4899);
            height: 100%;
            border-radius: 1rem;
            transition: width 0.5s ease;
        }
        
        /* AI Insight */
        .ai-insight {
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2));
            border-radius: 1rem;
            padding: 1rem;
            margin-top: 1rem;
            border-left: 3px solid #7c3aed;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 0 1rem;
            }
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            .stats-grid {
                grid-template-columns: 1fr;
            }
            .nav-links {
                width: 100%;
                justify-content: center;
            }
        }
        
        /* Loading Animation */
        .loading {
            text-align: center;
            padding: 2rem;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.3);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Welcome Banner */
        .welcome-banner {
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(236, 72, 153, 0.3));
            border-radius: 1.5rem;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .welcome-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .welcome-subtitle {
            color: #cbd5e1;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <span>🛍️</span>
                <span>ShopAround Nexus</span>
            </div>
            <div class="nav-links">
                <a class="nav-link active" onclick="loadSection('dashboard')">📊 Dashboard</a>
                <a class="nav-link" onclick="loadSection('shopping')">🛒 Shopping</a>
                <a class="nav-link" onclick="loadSection('mall')">🏪 Mall</a>
                <a class="nav-link" onclick="loadSection('profile')">👤 Profile</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div id="dashboardContent">
            <!-- Dashboard content loads here -->
        </div>
    </div>
    
    <script>
        let currentUser = null;
        
        async function loadDashboard() {
            const container = document.getElementById('dashboardContent');
            container.innerHTML = '<div class="loading"><div class="spinner"></div><div>Loading your dashboard...</div></div>';
            
            // Try to get user info
            try {
                const userRes = await fetch('/api/auth/me');
                if (userRes.ok) {
                    currentUser = await userRes.json();
                }
            } catch(e) {}
            
            // Get system stats
            let stats = { retailers: 50, services: 20, users: 1 };
            try {
                const healthRes = await fetch('/api/health');
                if (healthRes.ok) {
                    const health = await healthRes.json();
                    if (health.statistics) stats = health.statistics;
                }
            } catch(e) {}
            
            const userName = currentUser?.user?.full_name || currentUser?.user?.email || 'Guest';
            const currentHour = new Date().getHours();
            const greeting = currentHour < 12 ? 'Good Morning' : currentHour < 18 ? 'Good Afternoon' : 'Good Evening';
            
            container.innerHTML = `
                <div class="welcome-banner">
                    <div class="welcome-title">${greeting}, ${userName.split('@')[0]}! 👋</div>
                    <div class="welcome-subtitle">Welcome to your AI-powered shopping ecosystem. Track your savings, discover deals, and shop smarter.</div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon">🛍️</div>
                        <div class="stat-value">${stats.retailers || 50}+</div>
                        <div class="stat-label">Retailers & Shops</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">🛠️</div>
                        <div class="stat-value">${stats.services || 20}+</div>
                        <div class="stat-label">Service Providers</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">👥</div>
                        <div class="stat-value">${stats.users || 1}</div>
                        <div class="stat-label">Active Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">💰</div>
                        <div class="stat-value">Up to 40%</div>
                        <div class="stat-label">Potential Savings</div>
                    </div>
                </div>
                
                <div class="dashboard-grid">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">🎯 Quick Actions</div>
                        </div>
                        <div class="quick-actions">
                            <div class="action-btn" onclick="window.location.href='/nearby'">
                                <div class="action-emoji">📍</div>
                                <div class="action-text">Find Nearby</div>
                            </div>
                            <div class="action-btn" onclick="window.location.href='/mall'">
                                <div class="action-emoji">🛍️</div>
                                <div class="action-text">Online Mall</div>
                            </div>
                            <div class="action-btn" onclick="consultAI()">
                                <div class="action-emoji">🧠</div>
                                <div class="action-text">Ask AI</div>
                            </div>
                            <div class="action-btn" onclick="window.location.href='/nearby'">
                                <div class="action-emoji">🗺️</div>
                                <div class="action-text">Maps</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">🧠 AI Insight</div>
                        </div>
                        <div class="ai-insight" id="aiInsight">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                <span>🤖</span>
                                <strong>Ghost Brain AI</strong>
                            </div>
                            <div id="aiMessage">Click "Ask AI" for shopping recommendations</div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-grid">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">🏪 Top Retailers</div>
                        </div>
                        <div id="topRetailers" class="activity-list">Loading...</div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">📈 Your Shopping Activity</div>
                        </div>
                        <div id="activityList" class="activity-list">
                            <div class="activity-item">
                                <div class="activity-icon">🛒</div>
                                <div class="activity-details">
                                    <div class="activity-title">Start shopping to see activity</div>
                                    <div class="activity-time">Create a shopping list to begin</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">🛒 Smart Shopping Tips</div>
                    </div>
                    <div class="activity-list">
                        <div class="activity-item">
                            <div class="activity-icon">💡</div>
                            <div class="activity-details">
                                <div class="activity-title">Buy in bulk for staples like rice and maize meal</div>
                                <div class="activity-time">Save up to 30% on bulk purchases</div>
                            </div>
                        </div>
                        <div class="activity-item">
                            <div class="activity-icon">📍</div>
                            <div class="activity-details">
                                <div class="activity-title">Use location services to find nearest spaza shops</div>
                                <div class="activity-time">Spaza shops offer micro-pricing on essentials</div>
                            </div>
                        </div>
                        <div class="activity-item">
                            <div class="activity-icon">🧠</div>
                            <div class="activity-details">
                                <div class="activity-title">Let AI optimize your shopping list</div>
                                <div class="activity-time">Click "Ask AI" for personalized recommendations</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            loadTopRetailers();
        }
        
        async function loadTopRetailers() {
            try {
                const res = await fetch('/api/retailers');
                if (res.ok) {
                    const retailers = await res.json();
                    const topRetailers = retailers.slice(0, 5);
                    document.getElementById('topRetailers').innerHTML = topRetailers.map(r => `
                        <div class="activity-item">
                            <div class="activity-icon">${r.logo || '🏪'}</div>
                            <div class="activity-details">
                                <div class="activity-title">${r.name}</div>
                                <div class="activity-time">⭐ ${r.rating || 4.0} • Delivery: R${r.delivery_fee || 35}</div>
                            </div>
                        </div>
                    `).join('');
                }
            } catch(e) {
                document.getElementById('topRetailers').innerHTML = '<div class="activity-item">Unable to load retailers</div>';
            }
        }
        
        async function consultAI() {
            const aiDiv = document.getElementById('aiMessage');
            aiDiv.innerHTML = '<div class="spinner" style="width:20px;height:20px;"></div> Thinking...';
            
            try {
                const res = await fetch('/api/ghost/think', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ objective: "Shopping advice", risk_score: 0.3 })
                });
                const data = await res.json();
                aiDiv.innerHTML = data.verdict === 'APPROVED' ? 
                    '✅ AI recommends shopping at Checkers and Woolworths for best deals this week.' :
                    '📊 AI suggests comparing prices across multiple stores for maximum savings.';
            } catch(e) {
                aiDiv.innerHTML = '💡 Try setting a budget in the planner for personalized recommendations!';
            }
        }
        
        function loadSection(section) {
            if (section === 'dashboard') {
                loadDashboard();
            } else if (section === 'shopping') {
                window.location.href = '/';
            } else if (section === 'mall') {
                window.location.href = '/mall';
            } else if (section === 'profile') {
                window.location.href = '/api/auth/me';
            }
            
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        // Load dashboard on page load
        loadDashboard();
    </script>
</body>
</html>
'''

def add_dashboard(app):
    @app.route("/dashboard")
    def dashboard():
        return render_template_string(DASHBOARD_HTML)
    
    print("✅ Beautiful Dashboard added at /dashboard")
    return app
