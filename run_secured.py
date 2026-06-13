#!/usr/bin/env python3
"""
SHOPAROUND SECURED LAUNCHER
Your original app + Ecosystem Manager
Your original file is NOT modified
"""

import sys
import os

# Kill existing process
os.system("fuser -k 5000/tcp 2>/dev/null")

# Import your existing app
try:
    from shoparound_professional import app
    print("✅ Loaded your ShopAround app")
except ImportError:
    print("❌ Could not find shoparound_professional.py")
    sys.exit(1)

# Import ecosystem manager (add-on)
from ecosystem_manager import add_ecosystem

# Add ecosystem features (doesn't change your app)
app = add_ecosystem(app)

print("="*60)
print("🛍️ SHOPAROUND with Ecosystem Management")
print("="*60)
print("✅ Your original app: UNCHANGED")
print("✅ Ecosystem features: ADDED")
print("="*60)
print("🌐 Main app: http://localhost:5000")
print("🔐 New endpoints:")
print("   GET  /api/ecosystem/health")
print("   POST /api/ecosystem/hash")
print("   GET  /api/ecosystem/token")
print("   GET  /api/ecosystem/logs")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
