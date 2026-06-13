#!/usr/bin/env python3
"""
LAUNCH YOUR SHOPAROUND V9 WITH MAPS ADD-ON
Your original app stays EXACTLY the same. Maps is added on top.
"""

import os
import sys

# Kill existing processes
os.system("fuser -k 5000/tcp 2>/dev/null")
os.system("pkill -f 'python3.*shoparound' 2>/dev/null")

# Import YOUR existing app (choose the one that works)
app = None

# Try different possible file names
for app_name in ['shoparound_ultimate_v9', 'shoparound_v9_complete', 'shoparound_complete_mall', 'shoparound_with_neural']:
    try:
        module = __import__(app_name)
        if hasattr(module, 'app'):
            app = module.app
            print(f"✅ Loaded your app from {app_name}.py")
            break
    except ImportError:
        continue

if app is None:
    print("❌ Could not find your ShopAround app.")
    print("Make sure your app file is in this directory.")
    sys.exit(1)

# Import maps module and add routes (PURE ADDITION - no changes)
from maps_module import register_maps_routes
app = register_maps_routes(app)

print("="*60)
print("🛍️ SHOPAROUND V9 + MAPS")
print("="*60)
print("✅ Your original app: UNCHANGED")
print("✅ Maps & Navigation: ADDED")
print("✅ Mall Finder: ADDED")
print("="*60)
print("🌐 Main app: http://localhost:5000")
print("🗺️ Mall view: http://localhost:5000/mall")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
