#!/usr/bin/env python3
"""
SHOPAROUND SECURE LAUNCHER
- Your original app UNCHANGED
- Supabase authentication added
- User isolation enforced
"""

import os
import sys

# Kill existing process
os.system("fuser -k 5000/tcp 2>/dev/null")

# Import your main app (UNCHANGED)
from shoparound_professional import app

# Import all add-ons (pure additions)
from ecosystem_manager import add_ecosystem_manager
from ghost_brain import add_ghost_brain
from supabase_auth import add_supabase_auth

# Register all features (adds to your app, doesn't change it)
app = add_ecosystem_manager(app)
app = add_ghost_brain(app)
app = add_supabase_auth(app)

print("="*60)
print("🛍️ SHOPAROUND SECURE ECOSYSTEM")
print("="*60)
print("✅ Your original app: UNCHANGED")
print("✅ User Isolation: ACTIVE (each user sees only their data)")
print("✅ Supabase Auth: READY (or local fallback)")
print("✅ Ghost Brain AI: ACTIVE")
print("✅ Ecosystem Manager: ACTIVE")
print("="*60)
print("🔐 NEW AUTH ENDPOINTS:")
print("   POST /api/auth/register - Create account")
print("   POST /api/auth/login - Login")
print("   POST /api/auth/logout - Logout")
print("   GET  /api/auth/me - Current user")
print("="*60)
print("🌐 Open: http://localhost:5000")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
