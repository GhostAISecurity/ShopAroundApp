"""
ONLINE SHOPS MODULE - All South African online stores
Adds to your existing ShopAround without changing anything
"""

import json
from flask import request, jsonify, render_template_string

# COMPLETE DATABASE OF SOUTH AFRICAN ONLINE SHOPS
ONLINE_SHOPS = [
    # Grocery & Food
    {"name": "Checkers Sixty60", "url": "https://shop.checkers.co.za", "category": "grocery", "logo": "🛒", "delivery": "60min", "description": "Groceries delivered in 60 minutes"},
    {"name": "Pick n Pay ASAP", "url": "https://www.pnp.co.za", "category": "grocery", "logo": "🛒", "delivery": "60min", "description": "Fast grocery delivery"},
    {"name": "Woolworths Dash", "url": "https://www.woolworths.co.za", "category": "grocery", "logo": "🥩", "delivery": "60min", "description": "Premium grocery delivery"},
    {"name": "Shoprite", "url": "https://www.shoprite.co.za", "category": "grocery", "logo": "🛒", "delivery": "next-day", "description": "Affordable groceries"},
    {"name": "Spar2U", "url": "https://www.spar.co.za", "category": "grocery", "logo": "🛒", "delivery": "2-hour", "description": "Convenient grocery delivery"},
    {"name": "Food Lovers Market", "url": "https://www.foodloversmarket.co.za", "category": "grocery", "logo": "🥬", "delivery": "next-day", "description": "Fresh produce specialists"},
    {"name": "Takealot", "url": "https://www.takealot.com", "category": "ecommerce", "logo": "🛍️", "delivery": "next-day", "description": "South Africa's largest online store"},
    {"name": "Makro", "url": "https://www.makro.co.za", "category": "ecommerce", "logo": "🏪", "delivery": "2-3 days", "description": "Wholesale and retail"},
    {"name": "Game", "url": "https://www.game.co.za", "category": "ecommerce", "logo": "🎮", "delivery": "2-3 days", "description": "General merchandise"},
    {"name": "Loot", "url": "https://www.loot.co.za", "category": "ecommerce", "logo": "📦", "delivery": "2-3 days", "description": "Books, electronics, and more"},
    {"name": "Incredible Connection", "url": "https://www.incredible.co.za", "category": "electronics", "logo": "💻", "delivery": "2-3 days", "description": "Tech and electronics"},
    {"name": "Clicks", "url": "https://www.clicks.co.za", "category": "pharmacy", "logo": "💊", "delivery": "2-3 days", "description": "Health and beauty"},
    {"name": "Dischem", "url": "https://www.dischem.co.za", "category": "pharmacy", "logo": "💊", "delivery": "2-3 days", "description": "Pharmacy and health"},
    {"name": "Zando", "url": "https://www.zando.co.za", "category": "fashion", "logo": "👕", "delivery": "2-3 days", "description": "Clothing and accessories"},
    {"name": "Superbalist", "url": "https://www.superbalist.com", "category": "fashion", "logo": "👗", "delivery": "2-3 days", "description": "Trendy fashion"},
    {"name": "Builders", "url": "https://www.builders.co.za", "category": "hardware", "logo": "🔨", "delivery": "2-3 days", "description": "DIY and hardware"},
    {"name": "Baby City", "url": "https://www.babycity.co.za", "category": "baby", "logo": "👶", "delivery": "3-5 days", "description": "Baby products and nursery"},
    {"name": "Pet Heaven", "url": "https://www.petheaven.co.za", "category": "pet", "logo": "🐕", "delivery": "2-3 days", "description": "Pet supplies"},
    {"name": "Sportsmans Warehouse", "url": "https://www.sportsmanswarehouse.co.za", "category": "sports", "logo": "🏃", "delivery": "3-5 days", "description": "Outdoor and sports gear"},
    {"name": "Exclusive Books", "url": "https://www.exclusivebooks.co.za", "category": "books", "logo": "📚", "delivery": "2-3 days", "description": "Books and stationery"},
    {"name": "AutoTrader", "url": "https://www.autotrader.co.za", "category": "auto", "logo": "🚗", "delivery": "na", "description": "New and used cars"},
    {"name": "Amazon SA", "url": "https://www.amazon.co.za", "category": "international", "logo": "📦", "delivery": "2-5 days", "description": "International shipping to SA"},
    {"name": "Uber Eats", "url": "https://www.ubereats.com", "category": "food", "logo": "🚗", "delivery": "30-45min", "description": "Food delivery"},
]

def add_online_shops(app):
    @app.route("/mall")
    def online_mall():
        shops_json = json.dumps(ONLINE_SHOPS)
        html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Online Mall</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{font-family:system-ui;background:#f0f4f0;padding:20px;}}
        .container{{max-width:1400px;margin:0 auto;}}
        .header{{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1rem;text-align:center;}}
        h1{{color:#1f8a4c;margin-bottom:0.5rem;}}
        .stats{{background:#e8f5e9;padding:1rem;border-radius:0.5rem;margin:1rem 0;}}
        .categories{{display:flex;flex-wrap:wrap;gap:0.5rem;margin:1rem 0;justify-content:center;}}
        .cat-btn{{padding:0.5rem 1rem;background:#e8f5e9;border-radius:2rem;cursor:pointer;border:none;}}
        .cat-btn:hover,.cat-btn.active{{background:#1f8a4c;color:white;}}
        .search-bar{{display:flex;gap:0.5rem;margin-bottom:1rem;}}
        .search-bar input{{flex:1;padding:0.75rem;border:1px solid #ddd;border-radius:0.5rem;}}
        .search-bar button{{padding:0.75rem 1.5rem;background:#1f8a4c;color:white;border:none;border-radius:0.5rem;cursor:pointer;}}
        .shops-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;}}
        .shop-card{{background:white;border-radius:1rem;padding:1rem;cursor:pointer;border:1px solid #e5e7eb;}}
        .shop-card:hover{{transform:translateY(-3px);box-shadow:0 8px 16px rgba(0,0,0,0.1);}}
        .shop-logo{{font-size:2rem;margin-bottom:0.5rem;}}
        .shop-name{{font-weight:bold;color:#1f8a4c;}}
        .shop-category{{font-size:0.8rem;color:#666;margin:0.25rem 0;}}
        .shop-desc{{font-size:0.85rem;color:#555;}}
        .shop-delivery{{font-size:0.75rem;color:#888;margin-top:0.5rem;}}
        .badge{{display:inline-block;padding:0.2rem 0.5rem;background:#e8f5e9;border-radius:1rem;font-size:0.7rem;}}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🛍️ ShopAround Online Mall</h1>
        <p>Your gateway to South African online stores</p>
        <div class="stats">📦 <span id="shopCount">0</span> online stores</div>
    </div>
    <div class="search-bar">
        <input type="text" id="searchInput" placeholder="Search for a store..." onkeyup="filterShops()">
        <button onclick="filterShops()">🔍 Search</button>
    </div>
    <div class="categories" id="categories"></div>
    <div id="shopsGrid" class="shops-grid"></div>
</div>
<script>
    const allShops = {shops_json};
    let currentCategory = "all";
    function initCategories() {{
        const cats = {{}};
        allShops.forEach(s => cats[s.category] = true);
        const catList = Object.keys(cats).sort();
        document.getElementById('categories').innerHTML = '<button class="cat-btn active" data-category="all">All</button>' + 
            catList.map(c => `<button class="cat-btn" data-category="${{c}}">${{c.toUpperCase()}}</button>`).join('');
        document.querySelectorAll('.cat-btn').forEach(btn => {{
            btn.onclick = () => {{
                document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentCategory = btn.dataset.category;
                filterShops();
            }};
        }});
    }}
    function filterShops() {{
        const search = document.getElementById('searchInput').value.toLowerCase();
        let filtered = currentCategory === "all" ? allShops : allShops.filter(s => s.category === currentCategory);
        if (search) filtered = filtered.filter(s => s.name.toLowerCase().includes(search) || s.category.includes(search));
        document.getElementById('shopCount').innerText = filtered.length;
        document.getElementById('shopsGrid').innerHTML = filtered.map(shop => `
            <div class="shop-card" onclick="window.open('${{shop.url}}', '_blank')">
                <div class="shop-logo">${{shop.logo}}</div>
                <div class="shop-name">${{shop.name}}</div>
                <div class="shop-category"><span class="badge">${{shop.category}}</span></div>
                <div class="shop-desc">${{shop.description}}</div>
                <div class="shop-delivery">🚚 ${{shop.delivery}}</div>
            </div>
        `).join('');
    }}
    initCategories();
    filterShops();
</script>
</body>
</html>'''
        return render_template_string(html)
    
    @app.route("/api/online-shops")
    def api_online_shops():
        category = request.args.get("category", "")
        if category:
            filtered = [s for s in ONLINE_SHOPS if s["category"] == category]
        else:
            filtered = ONLINE_SHOPS
        return jsonify({"shops": filtered, "count": len(filtered)})
    
    print("✅ Online Mall added at /mall")
    return app
