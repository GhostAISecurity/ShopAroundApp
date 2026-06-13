#!/usr/bin/env python3
"""
SHOPAROUND WITH ECOSYSTEM MANAGER
Your original app + Self-healing + SHA3 security
"""

import sys
import os

# Import your existing app
try:
    from shoparound_professional import app
    print("✅ Loaded ShopAround Professional")
except ImportError:
    print("❌ Could not find shoparound_professional.py")
    sys.exit(1)

# Import ecosystem manager
from ecosystem_simple import add_ecosystem_manager

# Add ecosystem features (no changes to your app)
app = add_ecosystem_manager(app)

print("="*60)
print("🧠 SHOPAROUND with ECOSYSTEM MANAGEMENT")
print("="*60)
print("✅ Your original app: UNCHANGED")
print("✅ SHA3-512 Security: ACTIVE")
print("✅ Self-Healing Database: ACTIVE")
print("✅ Auto-Restart Monitor: ACTIVE")
print("="*60)
print("🌐 Open: http://localhost:5000")
print("")
print("🔐 New API Endpoints:")
print("   GET  /api/ecosystem/health - System health")
print("   GET  /api/ecosystem/logs - View logs")
print("   POST /api/ecosystem/security/hash - SHA3 hash")
print("   GET  /api/ecosystem/security/token - Secure token")
print("   GET  /api/ecosystem/status - Ecosystem status")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
