"""
REAL MAPS MODULE - Uses OpenStreetMap, no hardcoding
"""

import requests
import math
from flask import request, jsonify, render_template_string

# REAL OpenStreetMap API endpoints (free, no API key)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    return round(R * 2 * math.asin(min(1, math.sqrt(a))), 1)

def search_nearby_shops(lat, lng, radius_km=5):
    """Search REAL shops from OpenStreetMap"""
    radius_deg = radius_km / 111.0
    bbox = f"{lat - radius_deg},{lng - radius_deg},{lat + radius_deg},{lng + radius_deg}"
    
    # Query for shops and amenities
    query = f"""
    [out:json][timeout:25];
    (
      node["shop"]{bbox};
      node["amenity"]{bbox};
      way["shop"]{bbox};
      way["amenity"]{bbox};
    );
    out body;
    """
    
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        if resp.status_code == 200:
            results = []
            for elem in resp.json().get("elements", []):
                tags = elem.get("tags", {})
                name = tags.get("name")
                if name and len(name) > 2:
                    shop_type = tags.get("shop") or tags.get("amenity") or "shop"
                    results.append({
                        "name": name,
                        "type": shop_type,
                        "lat": elem.get("lat"),
                        "lng": elem.get("lon"),
                        "address": tags.get("addr:street", ""),
                        "phone": tags.get("phone", ""),
                        "distance": haversine(lat, lng, elem.get("lat"), elem.get("lon"))
                    })
            results.sort(key=lambda x: x["distance"])
            return results[:30]
    except Exception as e:
        print(f"OSM error: {e}")
    
    return []

def get_user_location():
    """Get real location from IP"""
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "lat": data.get("lat", -26.2041),
                "lng": data.get("lon", 28.0473),
                "city": data.get("city", "Johannesburg"),
                "country": data.get("country", "South Africa")
            }
    except:
        pass
    return {"lat": -26.2041, "lng": 28.0473, "city": "Johannesburg", "country": "South Africa"}

MAPS_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nearby Shops - Real Map Search</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:system-ui;background:#f0f4f0;padding:20px;}
        .container{max-width:1200px;margin:0 auto;}
        .card{background:white;border-radius:1rem;padding:1.5rem;margin-bottom:1rem;}
        h1{color:#1f8a4c;}
        .map-container{height:400px;border-radius:1rem;margin-bottom:1rem;overflow:hidden;}
        .results{max-height:500px;overflow-y:auto;}
        .shop-item{padding:1rem;border-bottom:1px solid #eee;cursor:pointer;}
        .shop-item:hover{background:#e8f5e9;}
        .name{font-weight:bold;color:#1f8a4c;}
        .dist{color:#666;font-size:0.8rem;margin-top:0.25rem;}
        .controls{display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;}
        button{padding:0.75rem 1.5rem;background:#1f8a4c;color:white;border:none;border-radius:0.5rem;cursor:pointer;}
        .radius-select{padding:0.75rem;border:1px solid #ddd;border-radius:0.5rem;}
        .loading{text-align:center;padding:2rem;color:#666;}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>📍 Find Real Shops Near You</h1>
        <p>Powered by OpenStreetMap - Real shops, real locations</p>
        
        <div class="controls">
            <button onclick="getMyLocation()">📍 Use My Location</button>
            <select id="radius" class="radius-select">
                <option value="2">2 km radius</option>
                <option value="5" selected>5 km radius</option>
                <option value="10">10 km radius</option>
            </select>
        </div>
        
        <div class="map-container">
            <div id="map" style="height:100%;"></div>
        </div>
        
        <div id="results" class="results">
            <div class="loading">Click "Use My Location" to find nearby shops</div>
        </div>
    </div>
</div>

<script>
let map = null;
let markers = [];
let currentLat = null;
let currentLng = null;

function initMap() {
    map = L.map('map').setView([-26.2041, 28.0473], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
    }).addTo(map);
    
    // Add click handler
    map.on('click', async (e) => {
        currentLat = e.latlng.lat;
        currentLng = e.latlng.lng;
        await loadNearby();
    });
}

async function getMyLocation() {
    if (navigator.geolocation) {
        document.getElementById('results').innerHTML = '<div class="loading">📍 Getting your location...</div>';
        navigator.geolocation.getCurrentPosition(async (pos) => {
            currentLat = pos.coords.latitude;
            currentLng = pos.coords.longitude;
            map.setView([currentLat, currentLng], 14);
            L.marker([currentLat, currentLng]).addTo(map).bindPopup('You are here').openPopup();
            await loadNearby();
        }, async () => {
            await loadNearby();
        });
    } else {
        await loadNearby();
    }
}

async function loadNearby() {
    if (!currentLat || !currentLng) {
        await getMyLocation();
        return;
    }
    
    const radius = document.getElementById('radius').value;
    document.getElementById('results').innerHTML = '<div class="loading">🔍 Searching for shops...</div>';
    
    const res = await fetch(`/api/shops/nearby?lat=${currentLat}&lng=${currentLng}&radius=${radius}`);
    const data = await res.json();
    
    // Clear old markers
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    
    if (data.shops && data.shops.length > 0) {
        document.getElementById('results').innerHTML = data.shops.map(shop => `
            <div class="shop-item" onclick="window.open('https://www.openstreetmap.org/directions?from=${currentLat},${currentLng}&to=${shop.lat},${shop.lng}', '_blank')">
                <div class="name">🏪 ${shop.name}</div>
                <div>${shop.address || 'Address available'}</div>
                ${shop.phone ? `<div>📞 ${shop.phone}</div>` : ''}
                <div class="dist">📍 ${shop.distance} km away</div>
            </div>
        `).join('');
        
        // Add markers to map
        data.shops.forEach(shop => {
            if (shop.lat && shop.lng) {
                const marker = L.marker([shop.lat, shop.lng]).addTo(map);
                marker.bindPopup(`<b>${shop.name}</b><br>${shop.address || ''}<br><a href="https://www.openstreetmap.org/directions?from=${currentLat},${currentLng}&to=${shop.lat},${shop.lng}" target="_blank">Get Directions</a>`);
                markers.push(marker);
            }
        });
    } else {
        document.getElementById('results').innerHTML = '<div class="loading">No shops found nearby. Try a larger radius.</div>';
    }
}

initMap();
</script>
</body>
</html>
'''

def add_real_maps(app):
    @app.route("/nearby")
    def nearby_page():
        return render_template_string(MAPS_HTML)
    
    @app.route("/api/shops/nearby")
    def api_nearby():
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
        radius = request.args.get("radius", 5, type=int)
        
        if not lat or not lng:
            loc = get_user_location()
            lat, lng = loc["lat"], loc["lng"]
        
        shops = search_nearby_shops(lat, lng, radius)
        return jsonify({"shops": shops, "count": len(shops), "location": {"lat": lat, "lng": lng}})
    
    @app.route("/api/maps/location")
    def api_location():
        return jsonify(get_user_location())
    
    print("✅ Real maps added at /nearby")
    return app
