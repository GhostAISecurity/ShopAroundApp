"""
MAPS PATCH - Adds to your existing ShopAround v9
Run this AFTER your v9 is running
"""

import requests
import math
from flask import request, jsonify, render_template_string

def add_maps_to_v9(app):
    """Add maps features to existing Flask app - NO CHANGES to existing routes"""
    
    # Simple place database
    PLACES = {
        "johannesburg": [
            {"name": "Checkers Sandton", "lat": -26.107, "lng": 28.055, "type": "grocery", "address": "Sandton City", "phone": "011 123 4567"},
            {"name": "Woolworths Rosebank", "lat": -26.146, "lng": 28.034, "type": "grocery", "address": "The Zone, Rosebank", "phone": "011 234 5678"},
            {"name": "Clicks Sandton", "lat": -26.107, "lng": 28.055, "type": "pharmacy", "address": "Sandton City", "phone": "011 345 6789"},
            {"name": "Dischem Rosebank", "lat": -26.146, "lng": 28.034, "type": "pharmacy", "address": "Rosebank Mall", "phone": "011 456 7890"},
            {"name": "Builders Warehouse", "lat": -26.107, "lng": 28.055, "type": "hardware", "address": "Bryanston", "phone": "011 567 8901"},
            {"name": "McDonald's Sandton", "lat": -26.107, "lng": 28.055, "type": "restaurant", "address": "Sandton", "phone": "011 678 9012"},
            {"name": "KFC Rosebank", "lat": -26.146, "lng": 28.034, "type": "restaurant", "address": "Rosebank", "phone": "011 789 0123"},
            {"name": "Pet Heaven", "lat": -26.107, "lng": 28.055, "type": "pet", "address": "Sandton", "phone": "011 890 1234"},
            {"name": "Baby City", "lat": -26.107, "lng": 28.055, "type": "baby", "address": "Sandton City", "phone": "011 901 2345"},
            {"name": "Incredible Connection", "lat": -26.107, "lng": 28.055, "type": "electronics", "address": "Sandton City", "phone": "011 012 3456"},
        ],
        "pretoria": [
            {"name": "Shoprite Hatfield", "lat": -25.754, "lng": 28.234, "type": "grocery", "address": "Hatfield Plaza", "phone": "012 123 4567"},
            {"name": "Pick n Pay Menlyn", "lat": -25.780, "lng": 28.275, "type": "grocery", "address": "Menlyn Park", "phone": "012 234 5678"},
            {"name": "Dischem Menlyn", "lat": -25.780, "lng": 28.275, "type": "pharmacy", "address": "Menlyn Park", "phone": "012 345 6789"},
            {"name": "Builders Menlyn", "lat": -25.780, "lng": 28.275, "type": "hardware", "address": "Menlyn", "phone": "012 456 7890"},
        ],
        "cape_town": [
            {"name": "Pick n Pay V&A", "lat": -33.906, "lng": 18.419, "type": "grocery", "address": "V&A Waterfront", "phone": "021 123 4567"},
            {"name": "Woolworths V&A", "lat": -33.906, "lng": 18.419, "type": "grocery", "address": "V&A Waterfront", "phone": "021 234 5678"},
            {"name": "Clicks V&A", "lat": -33.906, "lng": 18.419, "type": "pharmacy", "address": "V&A Waterfront", "phone": "021 345 6789"},
        ]
    }
    
    def haversine(lat1, lng1, lat2, lng2):
        R = 6371
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        return round(R * 2 * math.asin(min(1, math.sqrt(a))), 1)
    
    def find_closest_city(lat, lng):
        cities = {
            "johannesburg": (-26.2041, 28.0473),
            "pretoria": (-25.7461, 28.1881),
            "cape_town": (-33.9249, 18.4241),
        }
        closest = "johannesburg"
        min_dist = float('inf')
        for city, (clat, clng) in cities.items():
            dist = haversine(lat, lng, clat, clng)
            if dist < min_dist:
                min_dist = dist
                closest = city
        return closest
    
    def get_nearby_places(lat, lng, type_filter=None):
        city = find_closest_city(lat, lng)
        places = PLACES.get(city, PLACES["johannesburg"]).copy()
        for p in places:
            p["distance_km"] = haversine(lat, lng, p["lat"], p["lng"])
        if type_filter and type_filter != "all":
            places = [p for p in places if p["type"] == type_filter]
        places.sort(key=lambda x: x["distance_km"])
        return places[:30]
    
    # NEW ROUTES - These don't conflict with existing ones
    @app.route("/api/maps/nearby")
    def maps_nearby():
        lat = request.args.get("lat", type=float, default=-26.2041)
        lng = request.args.get("lng", type=float, default=28.0473)
        type_filter = request.args.get("type", "all")
        places = get_nearby_places(lat, lng, type_filter)
        return jsonify({"places": places, "count": len(places)})
    
    @app.route("/api/maps/route")
    def maps_route():
        start_lat = request.args.get("start_lat", type=float)
        start_lng = request.args.get("start_lng", type=float)
        end_lat = request.args.get("end_lat", type=float)
        end_lng = request.args.get("end_lng", type=float)
        if not all([start_lat, start_lng, end_lat, end_lng]):
            return jsonify({"error": "Missing coordinates"}), 400
        distance = haversine(start_lat, start_lng, end_lat, end_lng)
        duration = round(distance * 2, 1)
        return jsonify({"distance_km": distance, "duration_minutes": duration})
    
    @app.route("/api/maps/location")
    def maps_location():
        try:
            resp = requests.get("http://ip-api.com/json/", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return jsonify({"lat": data.get("lat"), "lng": data.get("lon"), "city": data.get("city")})
        except: pass
        return jsonify({"lat": -26.2041, "lng": 28.0473, "city": "Johannesburg"})
    
    @app.route("/mall")
    def mall_view():
        return render_template_string(MALL_HTML)
    
    print("✅ Maps & Mall features added to your ShopAround v9")
    return app

MALL_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Mall - Find Everything Near You</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:system-ui,sans-serif;background:#f0f4f0;padding:20px;}
        .container{max-width:1200px;margin:0 auto;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        h1{color:#1f8a4c;margin-bottom:0.5rem;}
        .subtitle{color:#666;margin-bottom:1.5rem;}
        .search-bar{display:flex;gap:0.5rem;margin-bottom:1rem;}
        .search-bar input{flex:1;padding:0.75rem;border:1px solid #ddd;border-radius:0.5rem;}
        .categories{display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;}
        .cat-btn{padding:0.5rem 1rem;background:#e8f5e9;border-radius:2rem;cursor:pointer;border:none;font-size:0.9rem;}
        .cat-btn:hover,.cat-btn.active{background:#1f8a4c;color:white;}
        .location-row{display:flex;gap:0.5rem;margin-bottom:1rem;align-items:center;}
        .location-row button{padding:0.75rem 1.5rem;background:#1f8a4c;color:white;border:none;border-radius:0.5rem;cursor:pointer;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem;}
        .place-card{padding:1rem;border:1px solid #eee;border-radius:0.5rem;cursor:pointer;transition:all 0.2s;}
        .place-card:hover{background:#f0f0f0;transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,0.1);}
        .place-name{font-weight:bold;color:#1f8a4c;font-size:1.1rem;}
        .place-type{display:inline-block;padding:0.2rem 0.5rem;background:#e8f5e9;border-radius:1rem;font-size:0.7rem;margin-left:0.5rem;}
        .place-dist{font-size:0.8rem;color:#666;margin-top:0.25rem;}
        .place-address{font-size:0.8rem;color:#888;margin-top:0.25rem;}
        .place-phone{font-size:0.8rem;color:#1f8a4c;margin-top:0.25rem;}
        .loading{text-align:center;padding:2rem;color:#666;}
        .route-panel{position:fixed;bottom:20px;right:20px;background:#1f8a4c;color:white;padding:1rem;border-radius:1rem;max-width:300px;display:none;z-index:1000;box-shadow:0 4px 12px rgba(0,0,0,0.2);}
        .route-panel button{margin-top:0.5rem;background:white;color:#1f8a4c;padding:0.5rem;width:100%;}
        .close-route{float:right;cursor:pointer;font-size:1.2rem;}
        @media (max-width:768px){.grid{grid-template-columns:1fr;}}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>🛍️ ShopAround Mall</h1>
        <div class="subtitle">Find shops, restaurants, and services near you</div>
        
        <div class="location-row">
            <div style="flex:1" id="locationDisplay">📍 Detecting your location...</div>
            <button onclick="getUserLocation()">📍 Update Location</button>
        </div>
        
        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search for shops, products, or services..." onkeyup="searchPlaces()">
        </div>
        
        <div class="categories" id="categories">
            <button class="cat-btn active" data-type="all">🏪 All</button>
            <button class="cat-btn" data-type="grocery">🛒 Grocery</button>
            <button class="cat-btn" data-type="pharmacy">💊 Pharmacy</button>
            <button class="cat-btn" data-type="hardware">🔨 Hardware</button>
            <button class="cat-btn" data-type="restaurant">🍔 Restaurant</button>
            <button class="cat-btn" data-type="electronics">📱 Electronics</button>
            <button class="cat-btn" data-type="pet">🐕 Pet</button>
            <button class="cat-btn" data-type="baby">👶 Baby</button>
        </div>
        
        <div id="results" class="grid"></div>
    </div>
</div>

<div id="routePanel" class="route-panel">
    <span class="close-route" onclick="closeRoute()">×</span>
    <div id="routeContent"></div>
</div>

<script>
let currentLat = -26.2041;
let currentLng = 28.0473;
let currentType = "all";
let currentPlaces = [];

async function getUserLocation() {
    document.getElementById('locationDisplay').innerHTML = '📍 Getting your location...';
    document.getElementById('results').innerHTML = '<div class="loading">🔍 Finding nearby places...</div>';
    
    // Try GPS first
    if (navigator.geolocation) {
        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject);
            });
            currentLat = position.coords.latitude;
            currentLng = position.coords.longitude;
            document.getElementById('locationDisplay').innerHTML = `📍 Location detected (GPS)`;
        } catch(e) {
            console.log("GPS failed, using IP");
            await loadIpLocation();
        }
    } else {
        await loadIpLocation();
    }
    await loadNearby();
}

async function loadIpLocation() {
    const res = await fetch('/api/maps/location');
    const data = await res.json();
    currentLat = data.lat;
    currentLng = data.lng;
    document.getElementById('locationDisplay').innerHTML = `📍 Approximate location: ${data.city || 'Johannesburg'}`;
}

async function loadNearby() {
    document.getElementById('results').innerHTML = '<div class="loading">🔍 Finding nearby places...</div>';
    
    const res = await fetch(`/api/maps/nearby?lat=${currentLat}&lng=${currentLng}&type=${currentType}`);
    const data = await res.json();
    currentPlaces = data.places || [];
    
    if (currentPlaces.length > 0) {
        document.getElementById('results').innerHTML = currentPlaces.map(place => `
            <div class="place-card" onclick="getDirections(${place.lat}, ${place.lng}, '${place.name}')">
                <div class="place-name">${place.name} <span class="place-type">${place.type}</span></div>
                <div class="place-dist">📍 ${place.distance_km}km away</div>
                <div class="place-address">🏠 ${place.address || 'Address available'}</div>
                ${place.phone ? `<div class="place-phone">📞 ${place.phone}</div>` : ''}
            </div>
        `).join('');
    } else {
        document.getElementById('results').innerHTML = '<div class="loading">No places found nearby. Try a different category.</div>';
    }
}

function searchPlaces() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    if (!query) {
        loadNearby();
        return;
    }
    const filtered = currentPlaces.filter(p => 
        p.name.toLowerCase().includes(query) || 
        (p.type && p.type.toLowerCase().includes(query)) ||
        (p.address && p.address.toLowerCase().includes(query))
    );
    document.getElementById('results').innerHTML = filtered.map(place => `
        <div class="place-card" onclick="getDirections(${place.lat}, ${place.lng}, '${place.name}')">
            <div class="place-name">${place.name} <span class="place-type">${place.type}</span></div>
            <div class="place-dist">📍 ${place.distance_km}km away</div>
            <div class="place-address">🏠 ${place.address || 'Address available'}</div>
            ${place.phone ? `<div class="place-phone">📞 ${place.phone}</div>` : ''}
        </div>
    `).join('');
}

async function getDirections(lat, lng, name) {
    const res = await fetch(`/api/maps/route?start_lat=${currentLat}&start_lng=${currentLng}&end_lat=${lat}&end_lng=${lng}`);
    const route = await res.json();
    
    document.getElementById('routeContent').innerHTML = `
        <strong>🚗 To: ${name}</strong><br>
        Distance: ${route.distance_km} km<br>
        Est. driving: ${route.duration_minutes} min<br>
        <button onclick="window.open('https://www.openstreetmap.org/directions?from=${currentLat},${currentLng}&to=${lat},${lng}', '_blank')">🌍 Open Maps</button>
        <button onclick="window.open('https://www.google.com/maps/dir/${currentLat},${currentLng}/${lat},${lng}', '_blank')">🗺️ Google Maps</button>
    `;
    document.getElementById('routePanel').style.display = 'block';
    setTimeout(() => {
        document.getElementById('routePanel').style.display = 'none';
    }, 15000);
}

function closeRoute() {
    document.getElementById('routePanel').style.display = 'none';
}

// Category buttons
document.querySelectorAll('.cat-btn').forEach(btn => {
    btn.onclick = () => {
        document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentType = btn.dataset.type;
        loadNearby();
    };
});

// Load on page load
getUserLocation();
</script>
</body>
</html>
'''

if __name__ == "__main__":
    print("This is a patch module - import and use add_maps_to_v9(app)")
