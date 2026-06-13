#!/usr/bin/env python3
"""
SHOPAROUND LAUNCHER - Runs YOUR app with Neural AI
NO CHANGES to your original files
"""

import os
import sys

# Kill any existing process on port 5000
os.system("fuser -k 5000/tcp 2>/dev/null")
os.system("pkill -f 'python3.*shoparound' 2>/dev/null")

# Import YOUR existing app (not modified)
from shoparound_with_neural import app

# Import neural addon
from neural_addon import add_neural_routes

# Add neural routes (doesn't remove anything)
app = add_neural_routes(app)

if __name__ == "__main__":
    print("="*60)
    print("🛍️  YOUR ShopAround Mall + Neural AI")
    print("="*60)
    print("✅ Your original mall: COMPLETELY UNCHANGED")
    print("✅ Neural AI: ADDED at /api/neural/*")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=False)
