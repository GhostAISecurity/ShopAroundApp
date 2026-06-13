#!/usr/bin/env python3
"""
SHOPAROUND OVERLAY SERVER
Imports your existing app and adds modules
Your original file is NOT modified
"""

import sys
import os

sys.path.insert(0, os.getcwd())

# Import YOUR existing app
try:
    from shoparound_professional import app as main_app
    print("✅ Loaded your ShopAround Professional app")
except ImportError:
    print("⚠️ Could not find shoparound_professional.py")
    from flask import Flask
    main_app = Flask(__name__)
    
    @main_app.route("/")
    def home():
        return {"status": "ShopAround Running"}

# Import add-ons
try:
    from real_maps import add_real_maps
    main_app = add_real_maps(main_app)
    print("✅ Maps module added")
except ImportError as e:
    print(f"⚠️ Maps module not found: {e}")

try:
    from online_shops import add_online_shops
    main_app = add_online_shops(main_app)
    print("✅ Online Mall added")
except ImportError as e:
    print(f"⚠️ Online Mall module not found: {e}")

try:
    from ghost_brain import add_ghost_brain
    main_app = add_ghost_brain(main_app)
    print("✅ Ghost Brain added")
except ImportError as e:
    print(f"⚠️ Ghost Brain module not found: {e}")

try:
    from neural_addon import add_neural_routes
    main_app = add_neural_routes(main_app)
    print("✅ Neural AI added")
except ImportError as e:
    print(f"⚠️ Neural addon not found: {e}")

print("="*50)
print("ALL MODULES ACTIVATED on port 5001")
print("Your original app stays on port 5000")
print("="*50)

if __name__ == "__main__":
    main_app.run(host="0.0.0.0", port=5001, debug=False)
