"""
ADD MODERN UI - Preserves all existing functionality
Adds new homepage route without changing existing routes
"""

import re

with open("shoparound_professional.py", "r") as f:
    content = f.read()

# Check if modern UI already added
if "MODERN_UI_HTML" in content:
    print("✅ Modern UI already present")
else:
    # Add modern UI HTML template
    modern_ui = '''

MODERN_UI_HTML = \"\"\"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>ShopAround Nexus | Premium AI Shopping Mall</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            min-height: 100vh;
            color: #fff;
        }
        .glass-nav {
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
            background: linear-gradient(135deg, #a78bfa, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .nav-links {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        .nav-link {
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            color: #cbd5e1;
            transition: all 0.3s;
        }
        .nav-link:hover, .nav-link.active {
            background: linear-gradient(135deg, #7c3aed, #ec4899);
            color: white;
        }
        .container { max-width: 1400px; margin: 2rem auto; padding: 0 2rem; }
        .hero {
            background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(236,72,153,0.1));
            border-radius: 2rem;
            padding: 3rem;
            margin-bottom: 2rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
        .hero h1 span { background: linear-gradient(135deg, #a78bfa, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 1.5rem;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); background: rgba(255,255,255,0.08); }
        .stat-value { font-size: 2rem; font-weight: 800; color: #a78bfa; }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: rgba(255,255,255,0.03);
            border-radius: 1.5rem;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .feature-card:hover { transform: translateY(-5px); background: rgba(124,58,237,0.1); border-color: rgba(124,58,237,0.3); }
        .feature-icon { font-size: 2.5rem; margin-bottom: 1rem; }
        .feature-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; }
        .feature-desc { color: #94a3b8; font-size: 0.85rem; }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: rgba(124,58,237,0.2);
            border-radius: 20px;
            font-size: 0.7rem;
            margin-top: 0.75rem;
        }
        .footer { text-align: center; padding: 2rem; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 2rem; }
        @media (max-width: 768px) { .container { padding: 0 1rem; } .hero h1 { font-size: 2rem; } .hero { padding: 2rem; } }
    </style>
</head>
<body>
    <div class="glass-nav">
        <div class="nav-container">
            <div class="logo">🛍️ ShopAround Nexus</div>
            <div class="nav-links">
                <a class="nav-link active" href="/">Home</a>
                <a class="nav-link" href="/nearby">Maps</a>
                <a class="nav-link" href="/mall">Mall</a>
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/api/health">Status</a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="hero">
            <h1>Welcome to <span>ShopAround Nexus</span></h1>
            <p style="color: #94a3b8;">South Africa's AI-Powered Quantum Shopping Ecosystem</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card"><div class="stat-value">50+</div><div>Retailers</div></div>
            <div class="stat-card"><div class="stat-value">20+</div><div>Services</div></div>
            <div class="stat-card"><div class="stat-value">SHA3</div><div>Quantum Secure</div></div>
            <div class="stat-card"><div class="stat-value">AI</div><div>Neural Active</div></div>
        </div>
        
        <div class="feature-grid">
            <div class="feature-card" onclick="window.location.href='/nearby'">
                <div class="feature-icon">🗺️</div>
                <div class="feature-title">Real Maps & Navigation</div>
                <div class="feature-desc">Find nearby stores, get directions, GPS location</div>
                <div class="badge">Live</div>
            </div>
            <div class="feature-card" onclick="window.location.href='/mall'">
                <div class="feature-icon">🏪</div>
                <div class="feature-title">Online Mall Aggregator</div>
                <div class="feature-desc">50+ retailers • All categories • Best deals</div>
                <div class="badge">50+ Stores</div>
            </div>
            <div class="feature-card" onclick="window.location.href='/'">
                <div class="feature-icon">🛒</div>
                <div class="feature-title">Smart Shopping Planner</div>
                <div class="feature-desc">AI-powered budget optimization</div>
                <div class="badge">Smart</div>
            </div>
            <div class="feature-card" onclick="consultAI()">
                <div class="feature-icon">🧠</div>
                <div class="feature-title">Ghost Brain AI</div>
                <div class="feature-desc">Multi-agent consensus engine</div>
                <div class="badge">Consult</div>
            </div>
            <div class="feature-card" onclick="checkDeals()">
                <div class="feature-icon">🔥</div>
                <div class="feature-title">Hot Deals</div>
                <div class="feature-desc">Real-time specials and discounts</div>
                <div class="badge">Today's Best</div>
            </div>
            <div class="feature-card" onclick="optimizeBudget()">
                <div class="feature-icon">💰</div>
                <div class="feature-title">Budget Optimizer</div>
                <div class="feature-desc">Get personalized shopping advice</div>
                <div class="badge">AI Powered</div>
            </div>
        </div>
        
        <div class="footer">
            <p>🛡️ Quantum Secure • 🧠 Neural AI • 🇿🇦 South Africa's Premier Shopping Platform</p>
        </div>
    </div>
    
    <script>
        async function consultAI() {
            try {
                const res = await fetch('/api/ghost/think', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ objective: "Shopping advice", risk_score: 0.3 })
                });
                const data = await res.json();
                alert(`🧠 Ghost Brain AI Decision: ${data.verdict}\\nConfidence: ${(data.approval_score*100).toFixed(0)}%`);
            } catch(e) {
                alert("Ghost Brain AI is ready! Use the shopping planner for optimization.");
            }
        }
        
        function checkDeals() {
            window.location.href = '/mall';
        }
        
        async function optimizeBudget() {
            const budget = prompt("Enter your budget (R):");
            if (budget) {
                try {
                    const res = await fetch('/api/mmapateng/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: `I have R${budget} for groceries` })
                    });
                    const data = await res.json();
                    alert(`🧠 Shopping Advice:\\n\\n${data.response}`);
                } catch(e) {
                    alert("Visit the Shopping Planner for budget optimization!");
                }
            }
        }
    </script>
</body>
</html>
\"\"\"

# Insert the modern UI into the app
new_content = content.replace(
    '@app.route("/")',
    f'{modern_ui}\n\n@app.route("/modern")\ndef modern_home():\n    return MODERN_UI_HTML\n\n@app.route("/")'
)

with open("shoparound_professional.py", "w") as f:
    f.write(new_content)

print("✅ Modern UI added at /modern")
print("✅ Your original homepage at / remains UNCHANGED")
