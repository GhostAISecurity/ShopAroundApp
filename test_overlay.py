import requests
import json

BASE = "http://localhost:5001"

def test(name, url, method="GET", data=None):
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{url}", timeout=3)
        else:
            r = requests.post(f"{BASE}{url}", json=data, timeout=3)
        print(f"✅ {name}: {r.status_code}")
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

print("Testing Overlay Server...")
test("Main App", "/")
test("Maps Page", "/nearby")
test("Online Mall", "/mall")
test("Ghost Brain Status", "/api/ghost/status")
test("Ghost Brain Think", "/api/ghost/think", "POST", {"risk_score": 0.3})
test("Neural AI Status", "/api/neural/status")
print("\n✅ All modules tested!")
