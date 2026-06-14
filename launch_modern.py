#!/usr/bin/env python3
"""
SHOPAROUND - MODERN DASHBOARD LAUNCHER
All features preserved - Beautiful new UI
"""

import os
import sys

os.system("fuser -k 5000/tcp 2>/dev/null")

from shoparound_professional import app
from modern_dashboard import add_modern_dashboard
from ecosystem_manager import add_ecosystem_manager
from ghost_brain import add_ghost_brain
from quantum_security import add_quantum_security
from supabase_auth import add_supabase_auth
from mmapateng_simple import add_mmapateng_routes

app = add_modern_dashboard(app)
app = add_ecosystem_manager(app)
app = add_ghost_brain(app)
app = add_quantum_security(app)
app = add_supabase_auth(app)
app = add_mmapateng_routes(app)

print("="*60)
print("🛍️ SHOPAROUND - MODERN DASHBOARD ACTIVE")
print("="*60)
print("🌐 MAIN DASHBOARD: http://localhost:5000/")
print("📊 CLASSIC VIEW: http://localhost:5000/dashboard")
print("🗺️ MAPS: http://localhost:5000/nearby")
print("🏪 MALL: http://localhost:5000/mall")
print("🧠 MMAPATENG AI: Chat widget bottom right")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
