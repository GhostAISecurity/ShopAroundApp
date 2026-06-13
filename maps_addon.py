"""
GOOGLE MAPS & NAVIGATION ADD-ON
Adds to your existing ShopAround without changing anything
"""

import requests
import math
from flask import request, jsonify

# OpenStreetMap API (FREE, no API key needed)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def haversine(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates in km"""
    R = 6371
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    return round(R * 2 * math.asin(min(1, math.sqrt(a))), 1)

def geocode_address(address):
    """Convert address to coordinates using OpenStreetMap"""
    params = {"q": address, "format": "json", "limit": 1}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": "ShopAround/1.0"}, timeout=10)
        if resp.status_code == 200 and resp.json():
            data = resp.json()[0]
            return {"lat": float(data["lat"]), "lng": float(data["lon"]), "display_name": data["display_name"]}
    except: pass
    return None

def reverse_geocode(lat, lng):
    """Get address from coordinates"""
    params = {"lat": lat, "lon": lng, "format": "json"}
    try:
        resp = requests.get(NOMINATIM_REVERSE, params=params, headers={"User-Agent": "ShopAround/1.0"}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("display_name")
    except: pass
    return None

def search_nearby_osm(lat, lng, radius_km=5, amenity_type=None):
    """Search nearby places using OpenStreetMap Overpass API"""
    radius_deg = radius_km / 111.0
    bbox = f"{lat - radius_deg},{lng - radius_deg},{lat + radius_deg},{lng + radius_deg}"
    
    amenity_map = {
        "grocery": ["supermarket", "convenience"],
        "pharmacy": ["pharmacy"],
        "restaurant": ["restaurant", "fast_food"],
        "cafe": ["cafe"],
        "hardware": ["hardware_store", "doityourself"],
        "clothing": ["clothes"],
        "electronics": ["electronics"],
        "all": ["shop", "amenity"]
    }
    
    tags = amenity_map.get(amenity_type, amenity_map["all"]) if amenity_type else amenity_map["all"]
    results = []
    
    for tag in tags:
        query = f"""[out:json][timeout:25];
        (node["{tag}"]{bbox}; way["{tag}"]{bbox};);
        out body;"""
        
        try:
            resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
            if resp.status_code == 200:
                for elem in resp.json().get("elements", []):
                    tags = elem.get("tags", {})
                    dist = haversine(lat, lng, elem.get("lat"), elem.get("lon")) if elem.get("lat") else None
                    results.append({
                        "name": tags.get("name", "Unnamed"),
                        "type": tag,
                        "latitude": elem.get("lat"),
                        "longitude": elem.get("lon"),
                        "address": tags.get("addr:street", ""),
                        "phone": tags.get("phone", ""),
                        "website": tags.get("website", ""),
                        "distance_km": dist,
                        "opening_hours": tags.get("opening_hours", "")
                    })
        except: pass
    
    results.sort(key=lambda x: x.get("distance_km") or 999)
    return results[:30]

def get_location_from_ip():
    """Get approximate location from IP address"""
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {"lat": data.get("lat"), "lng": data.get("lon"), "city": data.get("city"), "country": data.get("country")}
    except: pass
    return {"lat": -26.2041, "lng": 28.0473, "city": "Johannesburg", "country": "South Africa"}

def get_route(start_lat, start_lng, end_lat, end_lng):
    """Get route between two points using OSRM (Open Source Routing Machine)"""
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("routes"):
                route = data["routes"][0]
                return {
                    "distance_km": round(route["distance"] / 1000, 1),
                    "duration_minutes": round(route["duration"] / 60, 1),
                    "instructions": ["Route calculated successfully"]
                }
    except: pass
    return {"distance_km": haversine(start_lat, start_lng, end_lat, end_lng), "duration_minutes": round(haversine(start_lat, start_lng, end_lat, end_lng) * 2, 1)}

def add_maps_routes(app):
    """Add maps and navigation routes to existing Flask app"""
    
    @app.route("/api/maps/geocode", methods=["GET"])
    def maps_geocode():
        address = request.args.get("address", "")
        if not address:
            return jsonify({"error": "Address required"}), 400
        result = geocode_address(address)
        return jsonify(result or {"error": "Address not found"})
    
    @app.route("/api/maps/reverse", methods=["GET"])
    def maps_reverse():
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
        if not lat or not lng:
            return jsonify({"error": "Coordinates required"}), 400
        address = reverse_geocode(lat, lng)
        return jsonify({"address": address})
    
    @app.route("/api/maps/nearby", methods=["GET"])
    def maps_nearby():
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
        radius = request.args.get("radius", 5, type=int)
        type_filter = request.args.get("type", "all")
        
        if not lat or not lng:
            ip_loc = get_location_from_ip()
            lat, lng = ip_loc["lat"], ip_loc["lng"]
        
        places = search_nearby_osm(lat, lng, radius, type_filter)
        
        return jsonify({
            "location": {"lat": lat, "lng": lng},
            "radius_km": radius,
            "places": places[:30]
        })
    
    @app.route("/api/maps/route", methods=["GET"])
    def maps_route():
        start_lat = request.args.get("start_lat", type=float)
        start_lng = request.args.get("start_lng", type=float)
        end_lat = request.args.get("end_lat", type=float)
        end_lng = request.args.get("end_lng", type=float)
        
        if not all([start_lat, start_lng, end_lat, end_lng]):
            return jsonify({"error": "Start and end coordinates required"}), 400
        
        route = get_route(start_lat, start_lng, end_lat, end_lng)
        return jsonify(route)
    
    @app.route("/api/maps/location", methods=["GET"])
    def maps_location():
        ip_loc = get_location_from_ip()
        return jsonify({
            "latitude": ip_loc["lat"],
            "longitude": ip_loc["lng"],
            "city": ip_loc.get("city"),
            "country": ip_loc.get("country"),
            "source": "ip"
        })
    
    print("✅ Maps & Navigation add-on integrated")
    return app
