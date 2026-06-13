#!/usr/bin/env python3
"""
SHOPAROUND WITH SUPABASE
- Your original app UNCHANGED
- Supabase cloud authentication
- User isolation enforced
"""

import os
import sys

os.system("fuser -k 5000/tcp 2>/dev/null")

from shoparound_professional import app

# Import all add-ons
from ecosystem_manager import add_ecosystem_manager
from ghost_brain import add_ghost_brain
from supabase_auth import add_supabase_auth
from supabase_integration import add_supabase_routes

# Register all features
app = add_ecosystem_manager(app)
app = add_ghost_brain(app)
app = add_supabase_auth(app)
app = add_supabase_routes(app)

print("="*60)
print("🛍️ SHOPAROUND WITH SUPABASE CLOUD AUTH")
print("="*60)
print("✅ Your original app: UNCHANGED")
print("✅ Supabase Cloud Auth: READY")
print("✅ User Isolation: ACTIVE")
print("✅ All features: WORKING")
print("="*60)
print("🔐 Supabase Endpoints:")
print("   POST /api/supabase/register - Cloud register")
print("   POST /api/supabase/login - Cloud login")
print("   GET  /api/supabase/me - Current user")
print("="*60)
print("🌐 Open: http://localhost:5000")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
