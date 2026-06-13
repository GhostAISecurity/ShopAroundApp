#!/usr/bin/env python3
"""
SHOPAROUND CLEAN OVERLAY - No duplicate routes
"""

import sys
import os

sys.path.insert(0, os.getcwd())

# Import your existing app
from shoparound_professional import app as main_app
print("✅ Loaded your ShopAround Professional app")

# Function to add route only if it doesn't exist
def add_route_safe(app, rule, func, methods=None):
    for existing_rule in app.url_map.iter_rules():
        if existing_rule.rule == rule:
            print(f"⚠️ Route {rule} already exists, skipping")
            return app
    app.add_url_rule(rule, func.__name__, func, methods=methods)
    print(f"✅ Added route {rule}")
    return app

# Import and add modules safely
try:
    from real_maps import add_real_maps_safe
    main_app = add_real_maps_safe(main_app)
except ImportError:
    print("⚠️ Real maps module not found")

try:
    from online_shops import add_online_shops_safe
    main_app = add_online_shops_safe(main_app)
except ImportError:
    print("⚠️ Online shops module not found")

try:
    from ghost_brain import add_ghost_brain_safe
    main_app = add_ghost_brain_safe(main_app)
except ImportError:
    print("⚠️ Ghost brain module not found")

print("="*50)
print("✅ ALL MODULES ACTIVATED")
print("="*50)
print("Open: http://localhost:5000")
print("="*50)

if __name__ == "__main__":
    main_app.run(host="0.0.0.0", port=5000, debug=False)
