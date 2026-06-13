"""
MAPS MODULE - Adds location features to ShopAround
Import this into your existing app - NO CHANGES to your original code
"""

import math
import urllib.request
import json
from flask import request, jsonify, render_template_string

# Nearby places database (SA cities)
NEARBY_PLACES = {
    "johannesburg": [
        {"name": "Checkers Sandton", "lat": -26.107, "lng": 28.055, "type": "grocery", "address": "Sandton City", "phone": "011 123 4567"},
        {"name": "Woolworths Rosebank", "lat": -26.146, "lng": 28.034, "type": "grocery", "address": "The Zone, Rosebank", "phone": "011 123 4568"},
        {"name": "Clicks Sandton", "lat": -26.107, "lng": 28.055, "type": "pharmacy", "address": "Sandton City", "phone": "011 123 4569"},
        {"name": "Builders Warehouse", "lat": -26.107, "lng": 28.055, "type": "hardware", "address": "Bryanston", "phone": "011 123 4570"},
        {"name": "Pick n Pay Sandton", "lat": -26.107, "lng": 28.055, "type": "grocery", "address": "Sandton City", "phone": "011 123 4571"},
        {"name": "Dischem Sandton", "lat": -26.107, "lng": 28.055, "type": "pharmacy", "address": "Sandton City", "phone": "011 123 4572"},
        {"name": "Makro Silverlakes", "lat": -25.800, "lng": 28.333, "type": "wholesale", "address": "Silverlakes", "phone": "012 123 4573"},
        {"name": "Game Menlyn", "lat": -25.780, "lng": 28.275, "type": "electronics", "address": "Menlyn Park", "phone": "012 123 4574"},
        {"name": "McDonald's Sandton", "lat": -26.107, "lng": 28.055, "type": "restaurant", "address": "Sandton", "phone": "011 123 4575"},
        {"name": "KFC Sandton", "lat": -26.107, "lng": 28.055, "type": "restaurant", "address": "Sandton", "phone": "011 123 4576"},
    ],
    "pretoria": [
        {"name": "Shoprite Hatfield", "lat": -25.754, "lng": 28.234, "type": "grocery", "address": "Hatfield Plaza", "phone": "012 123 4577"},
        {"name": "Pick n Pay Menlyn", "lat": -25.780, "lng": 28.275, "type": "grocery", "address": "Menlyn Park", "phone": "012 123 4578"},
        {"name": "Dischem Menlyn", "lat": -25.780, "lng": 28.275, "type": "pharmacy", "address": "Menlyn Park", "phone": "012 123 4579"},
        {"name": "Woolworths Menlyn", "lat": -25.780, "lng": 28.275, "type": "grocery", "address": "Menlyn Park", "phone": "012 123 4580"},
        {"name": "Clicks Menlyn", "lat": -25.780, "lng": 28.275, "type": "pharmacy", "address": "Menlyn Park", "phone": "012 123 4581"},
    ],
    "cape_town": [
        {"name": "Pick n Pay V&A", "lat": -33.906, "lng": 18.419, "type": "grocery", "address": "V&A Waterfront", "phone": "021 123 4582"},
        {"name": "Woolworths V&A", "lat": -33.906, "lng": 18.419, "type": "grocery", "address": "V&A Waterfront", "phone": "021 123 4583"},
        {"name": "Clicks V&A", "lat": -33.906, "lng": 18.419, "type": "pharmacy", "address": "V&A Waterfront", "phone": "021 123 4584"},
    ],
    "durban": [
        {"name": "Checkers Gateway", "lat": -29.718, "lng": 31.052, "type": "grocery", "address": "Gateway Mall", "phone": "031 123 4585"},
        {"name": "Woolworths Gateway", "lat": -29.718, "lng": 31.052, "type": "grocery", "address": "Gateway Mall", "phone": "031 123 4586"},
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
        "durban": (-29.8587, 31.0218),
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
    places = NEARBY_PLACES.get(city, NEARBY_PLACES["johannesburg"]).copy()
    
    for p in places:
        p["distance_km"] = haversine(lat, lng, p["lat"], p["lng"])
    
    if type_filter and type_filter != "all":
        places = [p for p in places if p["type"] == type_filter]
    
    places.sort(key=lambda x: x["distance_km"])
    return places[:30]

def get_user_location():
    try:
        resp = urllib.request.urlopen("http://ip-api.com/json/", timeout=5)
        data = json.loads(resp.read().decode())
        if data.get("status") == "success":
            return {"lat": data.get("lat", -26.2041), "lng": data.get("lon", 28.0473), "city": data.get("city", "Johannesburg")}
    except:
        pass
    return {"lat": -26.2041, "lng": 28.0473, "city": "Johannesburg"}

def register_maps_routes(app):
    """Add maps routes to your existing Flask app - PURE ADDITION"""
    
    @app.route("/api/maps/nearby")
    def maps_nearby():
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
        type_filter = request.args.get("type", "all")
        
        if not lat or not lng:
            loc = get_user_location()
            lat, lng = loc["lat"], loc["lng"]
        
        places = get_nearby_places(lat, lng, type_filter)
        return jsonify({"places": places, "count": len(places), "location": {"lat": lat, "lng": lng}})
    
    @app.route("/api/maps/location")
    def maps_location():
        loc = get_user_location()
        return jsonify(loc)
    
    @app.route("/mall")
    def mall_view():
        return render_template_string(MALL_HTML)
    
    print("✅ Maps routes added to your ShopAround app")
    return app

MALL_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShopAround Mall - Find Nearby</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:system-ui,sans-serif;background:#f0f4f0;padding:20px;}
        .container{max-width:1200px;margin:0 auto;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
        h1{color:#1f8a4c;margin-bottom:0.5rem;}
        .categories{display:flex;flex-wrap:wrap;gap:0.5rem;margin:1rem 0;}
        .cat-btn{padding:0.5rem 1rem;background:#e8f5e9;border-radius:2rem;cursor:pointer;border:none;}
        .cat-btn:hover,.cat-btn.active{background:#1f8a4c;color:white;}
        .location-bar{display:flex;gap:0.5rem;margin:1rem 0;}
        .location-bar input{flex:1;padding:0.75rem;border:1px solid #ddd;border-radius:0.5rem;}
        button{padding:0.75rem 1.5rem;background:#1f8a4c;color:white;border:none;border-radius:0.5rem;cursor:pointer;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem;margin-top:1rem;}
        .place-card{padding:1rem;border-bottom:1px solid #eee;cursor:pointer;background:#f9f9f9;border-radius:0.5rem;}
        .place-card:hover{background:#e8f5e9;}
        .place-name{font-weight:bold;color:#1f8a4c;}
        .place-dist{font-size:0.8rem;color:#666;margin-top:0.25rem;}
        .route-info{margin-top:1rem;padding:1rem;background:#e8f5e9;border-radius:0.5rem;display:none;}
        .loading{text-align:center;padding:2rem;color:#666;}
        @media (max-width:768px){.grid{grid-template-columns:1fr;}}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>🛍️ ShopAround Mall</h1>
        <p>Find shops, restaurants, and services near you</p>
        
        <div class="location-bar">
            <input type="text" id="locationInput" placeholder="Enter location or use my location">
            <button onclick="getUserLocation()">📍 My Location</button>
        </div>
        
        <div class="categories" id="categories">
            <button class="cat-btn active" data-type="all">All</button>
            <button class="cat-btn" data-type="grocery">🛒 Grocery</button>
            <button class="cat-btn" data-type="pharmacy">💊 Pharmacy</button>
            <button class="cat-btn" data-type="hardware">🔨 Hardware</button>
            <button class="cat-btn" data-type="electronics">📱 Electronics</button>
            <button class="cat-btn" data-type="restaurant">🍔 Restaurant</button>
            <button class="cat-btn" data-type="wholesale">🏪 Wholesale</button>
        </div>
        
        <div id="results" class="grid"></div>
        <div id="routeInfo" class="route-info"></div>
    </div>
</div>

<script>
let currentLat = -26.2041;
let currentLng = 28.0473;
let currentType = "all";

async function getUserLocation() {
    if (navigator.geolocation) {
        document.getElementById('results').innerHTML = '<div class="loading">📍 Getting your location...</div>';
        navigator.geolocation.getCurrentPosition(async (pos) => {
            currentLat = pos.coords.latitude;
            currentLng = pos.coords.longitude;
            await loadNearby();
        }, async () => {
            await loadNearby();
        });
    } else {
        await loadNearby();
    }
}

async function loadNearby() {
    document.getElementById('results').innerHTML = '<div class="loading">🔍 Finding nearby places...</div>';
    
    const res = await fetch(`/api/maps/nearby?lat=${currentLat}&lng=${currentLng}&type=${currentType}`);
    const data = await res.json();
    
    if (data.places && data.places.length > 0) {
        document.getElementById('results').innerHTML = data.places.map(place => `
            <div class="place-card" onclick="showDirections(${place.lat}, ${place.lng}, '${place.name}')">
                <div class="place-name">${place.name}</div>
                <div>${place.address || 'Address available'}</div>
                <div>📞 ${place.phone || 'N/A'}</div>
                <div class="place-dist">📍 ${place.distance_km}km away</div>
            </div>
        `).join('');
    } else {
        document.getElementById('results').innerHTML = '<div class="loading">No places found nearby. Try a different category.</div>';
    }
}

function showDirections(lat, lng, name) {
    const mapsUrl = `https://www.openstreetmap.org/directions?from=${currentLat},${currentLng}&to=${lat},${lng}`;
    const googleMapsUrl = `https://www.google.com/maps/dir/${currentLat},${currentLng}/${lat},${lng}`;
    
    document.getElementById('routeInfo').innerHTML = `
        <strong>🚗 Directions to ${name}</strong><br>
        <button onclick="window.open('${mapsUrl}', '_blank')">🌍 Open OpenStreetMap</button>
        <button onclick="window.open('${googleMapsUrl}', '_blank')">🗺️ Open Google Maps</button>
        <button onclick="document.getElementById('routeInfo').style.display='none'">Close</button>
    `;
    document.getElementById('routeInfo').style.display = 'block';
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

// Load on page start
getUserLocation();
</script>
</body>
</html>
'''
