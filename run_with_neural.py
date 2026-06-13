#!/usr/bin/env python3
"""
NEURAL LAUNCHER - Runs your existing mall and adds neural AI
NO DUPLICATES, NO CHANGES to your original app
"""

import sys
import importlib.util

# Try to import your existing app
app = None

# Try different possible app names
app_names = ['shoparound_with_neural', 'shoparound_complete_mall', 'shoparound', 'app']

for name in app_names:
    try:
        module = __import__(name)
        if hasattr(module, 'app'):
            app = module.app
            print(f"✅ Loaded app from {name}.py")
            break
    except ImportError:
        continue

if app is None:
    print("❌ Could not find your Flask app. Make sure your app file is in this directory.")
    sys.exit(1)

# Import neural addon
from neural_addon import add_neural_routes

# Add neural routes (safe, no duplicates)
app = add_neural_routes(app)

if __name__ == "__main__":
    print("="*70)
    print("🛍️  Your ShopAround Mall + Neural AI")
    print("="*70)
    print("✅ Your mall: ALL original features WORK")
    print("✅ Neural AI: ADDED at /api/neural/*")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=True)
