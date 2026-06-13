#!/usr/bin/env python3
"""
Integrate Ecosystem Manager into ShopAround
Creates a new launcher that adds ecosystem features
Your original file is NOT modified
"""

import os
import sys

# Check if ecosystem manager exists
if not os.path.exists("ecosystem_manager.py"):
    print("❌ ecosystem_manager.py not found")
    sys.exit(1)

# Create launcher that imports your app and adds ecosystem
launcher = '''#!/usr/bin/env python3
"""
SHOPAROUND WITH ECOSYSTEM MANAGER
Your original app + Self-healing + SHA3/Kyber security
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
from ecosystem_manager import add_ecosystem_manager

# Add ecosystem features (no changes to your app)
app = add_ecosystem_manager(app)

print("="*60)
print("🧠 SHOPAROUND with ECOSYSTEM MANAGEMENT")
print("="*60)
print("✅ Your original app: UNCHANGED")
print("✅ SHA3-512 / Kyber Security: ACTIVE")
print("✅ Self-Healing Database: ACTIVE")
print("✅ Auto-Restart Monitor: ACTIVE")
print("="*60)
print("🌐 Open: http://localhost:5000")
print("")
print("🔐 New API Endpoints:")
print("   GET  /api/ecosystem/health - System health")
print("   GET  /api/ecosystem/logs - View logs")
print("   POST /api/ecosystem/security/encrypt - Encrypt data")
print("   POST /api/ecosystem/security/hash - SHA3 hash")
print("   GET  /api/ecosystem/security/token - Secure token")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
'''

with open("shoparound_secured.py", "w") as f:
    f.write(launcher)

print("✅ Created shoparound_secured.py")
print("")
print("To run your secured system:")
print("  python3 shoparound_secured.py")
print("")
print("Your original shoparound_professional.py is UNCHANGED")
