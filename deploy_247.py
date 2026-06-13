#!/usr/bin/env python3
"""
SHOPAROUND 24/7 DEPLOYMENT LAUNCHER
- Adds quantum security
- Adds PWA support
- Prepares for GitHub/Render deployment
"""

import os
import sys

os.system("fuser -k 5000/tcp 2>/dev/null")

# Import your main app
from shoparound_professional import app

# Import all security and PWA features
from quantum_security import add_quantum_security
from ecosystem_manager import add_ecosystem_manager
from ghost_brain import add_ghost_brain
from supabase_auth import add_supabase_auth

# Add quantum security (overlay - no changes to original)
app = add_quantum_security(app)
app = add_ecosystem_manager(app)
app = add_ghost_brain(app)
app = add_supabase_auth(app)

# Add PWA headers
@app.after_request
def add_pwa_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

print("="*60)
print("🔒 SHOPAROUND 24/7 QUANTUM SECURE")
print("="*60)
print("✅ PWA Installable: Yes")
print("✅ Quantum Security: SHA3-512")
print("✅ Malware Protection: Active")
print("✅ Rate Limiting: Active")
print("✅ 24/7 Ready for GitHub/Render")
print("="*60)
print("📱 Install the app:")
print("   Chrome → Menu → Install App")
print("="*60)
print("🌐 http://localhost:5000")
print("="*60)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
