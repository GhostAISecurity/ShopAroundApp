"""
Real Maps Module - Safe version (no duplicate routes)
"""
from flask import request, jsonify, render_template_string

MAPS_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Nearby Shops</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body{font-family:system-ui;background:#f0f4f0;padding:20px;}
.container{max-width:1000px;margin:0 auto;}
.card{background:white;border-radius:1rem;padding:1.5rem;}
h1{color:#1f8a4c;}
#map{height:400px;border-radius:1rem;margin-bottom:1rem;}
button{padding:0.75rem;background:#1f8a4c;color:white;border:none;border-radius:0.5rem;cursor:pointer;}
</style>
</head>
<body>
<div class="container"><div class="card">
<h1>📍 Nearby Shops</h1>
<div id="map"></div>
<button onclick="getLocation()">📍 Use My Location</button>
<div id="results"></div>
</div></div>
<script>
let map;
function initMap(lat,lng){if(map)map.remove();map=L.map('map').setView([lat,lng],14);L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);}
async function getLocation(){if(navigator.geolocation){navigator.geolocation.getCurrentPosition(async(pos)=>{initMap(pos.coords.latitude,pos.coords.longitude);await loadShops(pos.coords.latitude,pos.coords.longitude);});}}
async function loadShops(lat,lng){const res=await fetch(`/api/nearby?lat=${lat}&lng=${lng}`);const data=await res.json();const div=document.getElementById('results');if(data.shops&&data.shops.length){div.innerHTML=data.shops.map(s=>`<div onclick="window.open('https://www.google.com/maps/dir/${lat},${lng}/${s.lat},${s.lng}')"><strong>${s.name}</strong><br>📍 ${s.distance}km</div>`).join('');data.shops.forEach(s=>{if(s.lat&&s.lng)L.marker([s.lat,s.lng]).addTo(map).bindPopup(s.name);});}else div.innerHTML='<div>No shops found</div>';}
getLocation();
</script>
</body>
</html>
'''

def add_real_maps_safe(app):
    # Check if route exists
    routes = [r.rule for r in app.url_map.iter_rules()]
    
    if '/nearby' not in routes:
        @app.route('/nearby')
        def nearby_page():
            return render_template_string(MAPS_HTML)
        print("✅ Added /nearby route")
    
    if '/api/nearby' not in routes:
        @app.route('/api/nearby')
        def api_nearby():
            lat = request.args.get('lat', -26.2041, float)
            lng = request.args.get('lng', 28.0473, float)
            shops = [
                {"name": "Checkers Sandton", "lat": -26.107, "lng": 28.055, "distance": round(((lat+26.107)**2 + (lng-28.055)**2)**0.5*111,1)},
                {"name": "Woolworths Rosebank", "lat": -26.146, "lng": 28.034, "distance": round(((lat+26.146)**2 + (lng-28.034)**2)**0.5*111,1)},
                {"name": "Clicks Sandton", "lat": -26.107, "lng": 28.055, "distance": round(((lat+26.107)**2 + (lng-28.055)**2)**0.5*111,1)},
            ]
            return jsonify({"shops": shops})
        print("✅ Added /api/nearby route")
    
    return app
