#!/usr/bin/env python3
"""
SHOPAROUND COMPLETE LAUNCHER
Runs your professional app with ALL ecosystem features
"""

import os
import sys

# Kill existing process
os.system("fuser -k 5000/tcp 2>/dev/null")

# Import your main app
from shoparound_professional import app

# Import and register ecosystem manager
try:
    from ecosystem_manager import add_ecosystem_manager
    app = add_ecosystem_manager(app)
    print("✅ Ecosystem Manager Active")
except ImportError:
    print("⚠️ Ecosystem Manager not found")

# Import and register ghost brain if available
try:
    from ghost_brain import add_ghost_brain
    app = add_ghost_brain(app)
    print("✅ Ghost Brain Active")
except ImportError:
    print("⚠️ Ghost Brain not found")

print("="*60)
print("🛍️ SHOPAROUND COMPLETE ECOSYSTEM")
print("="*60)
print("✅ Main app: http://localhost:5000")
print("✅ Nearby shops: http://localhost:5000/nearby")
print("✅ Online mall: http://localhost:5000/mall")
print("✅ Ghost Brain: POST /api/ghost/think")
print("✅ Ecosystem: GET /api/ecosystem/health")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
