#!/usr/bin/env python3
"""
SHOPAROUND WITH MMAPATENG AI ASSISTANT
Your original app UNCHANGED - Mmapateng added as overlay
"""

import os
import sys

os.system("fuser -k 5000/tcp 2>/dev/null")

# Import your main app (UNCHANGED)
from shoparound_professional import app

# Import Mmapateng
from mmapateng_ai import add_mmapateng_routes, add_mmapateng_widget

# Add Mmapateng (pure addition)
app = add_mmapateng_routes(app)
app = add_mmapateng_widget(app)

# Import other add-ons
try:
    from dashboard_overlay import add_dashboard
    app = add_dashboard(app)
except: pass

try:
    from ecosystem_manager import add_ecosystem_manager
    app = add_ecosystem_manager(app)
except: pass

try:
    from ghost_brain import add_ghost_brain
    app = add_ghost_brain(app)
except: pass

print("="*60)
print("🧠 SHOPAROUND WITH MMAPATENG AI")
print("="*60)
print("✅ Your original app: UNCHANGED at /")
print("💬 Mmapateng Assistant: POST /api/mmapateng/chat")
print("🪄 Chat Widget: http://localhost:5000/mmapateng-widget")
print("📊 Dashboard: http://localhost:5000/dashboard")
print("="*60)
print("💬 Mmapateng 'The Real Johannah' is READY to chat!")
print("   • Confident, positive personality")
print("   • Learns from every conversation")
print("   • Helps with budgets, prices, stores")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
