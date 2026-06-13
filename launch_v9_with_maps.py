#!/usr/bin/env python3
"""
SHOPAROUND V9 WITH MAPS - Launcher
Your existing v9 remains UNCHANGED. Maps are added on top.
"""

import os
import sys

# Kill existing processes
os.system("fuser -k 5000/tcp 2>/dev/null")
os.system("pkill -f 'python3.*shoparound' 2>/dev/null")

# Import your existing v9 app
try:
    from shoparound_ultimate_v9 import app
    print("✅ Loaded ShopAround Ultimate v9")
except ImportError:
    try:
        from shoparound_with_neural import app
        print("✅ Loaded ShopAround with Neural")
    except ImportError:
        from shoparound_complete_mall import app
        print("✅ Loaded ShopAround Complete Mall")

# Import maps patch and apply it (adds routes, doesn't remove anything)
from maps_patch import add_maps_to_v9
app = add_maps_to_v9(app)

print("="*70)
print("🏆 SHOPAROUND V9 WITH MAPS & MALL")
print("="*70)
print("✅ Your existing ShopAround: COMPLETELY UNCHANGED")
print("✅ Maps & Navigation: ADDED")
print("✅ Mall Aggregator: ADDED at /mall")
print("✅ Nearby Search: ADDED at /api/maps/nearby")
print("="*70)
print("🌐 Open Main App: http://localhost:5000")
print("🗺️ Open Mall View: http://localhost:5000/mall")
print("="*70)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
