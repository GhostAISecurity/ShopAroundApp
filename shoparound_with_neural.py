#!/usr/bin/env python3
"""
ShopAround Complete Mall WITH Neural AI Integration
This imports your existing app and adds neural capabilities
"""

# Import your existing app
from shoparound_complete_mall import app

# Import neural addon
from neural_addon import add_neural_routes

# Add neural routes (your mall stays exactly the same)
app = add_neural_routes(app)

if __name__ == "__main__":
    print("="*70)
    print("🛍️ ShopAround Complete Mall WITH Neural AI")
    print("="*70)
    print("✅ All original features: Retailers, Services, Spaza, Pharmacies, Delivery")
    print("✅ Neural AI Brain Active - 5 Agents")
    print("✅ New endpoints: /api/neural/think, /api/neural/status, /api/neural/memory")
    print("="*70)
    print("🌐 Open: http://localhost:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=True)
