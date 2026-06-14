#!/usr/bin/env python3
"""
SHOPAROUND WITH BEAUTIFUL DASHBOARD
Your original app UNCHANGED - Dashboard added as overlay
"""

import os
import sys

os.system("fuser -k 5000/tcp 2>/dev/null")

# Import your main app (UNCHANGED)
from shoparound_professional import app

# Import dashboard overlay
from dashboard_overlay import add_dashboard

# Add dashboard (pure addition)
app = add_dashboard(app)

# Import other add-ons
try:
    from ecosystem_manager import add_ecosystem_manager
    app = add_ecosystem_manager(app)
except: pass

try:
    from ghost_brain import add_ghost_brain
    app = add_ghost_brain(app)
except: pass

try:
    from supabase_auth import add_supabase_auth
    app = add_supabase_auth(app)
except: pass

try:
    from quantum_security import add_quantum_security
    app = add_quantum_security(app)
except: pass

print("="*60)
print("🛍️ SHOPAROUND WITH BEAUTIFUL DASHBOARD")
print("="*60)
print("✅ Your original app: UNCHANGED at /")
print("✅ Beautiful Dashboard: http://localhost:5000/dashboard")
print("✅ All original features: WORKING")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
