import re

with open("shoparound_professional.py", "r") as f:
    content = f.read()

if "from ghost_brain import add_ghost_brain" in content:
    print("✅ Ghost Brain already added")
else:
    # Add import at top
    new_content = content.replace(
        "from online_shops import add_online_shops",
        "from online_shops import add_online_shops\nfrom ghost_brain import add_ghost_brain"
    )
    
    # Add registration
    new_content = new_content.replace(
        "app = add_online_shops(app)",
        "app = add_online_shops(app)\napp = add_ghost_brain(app)"
    )
    
    with open("shoparound_professional.py", "w") as f:
        f.write(new_content)
    
    print("✅ Ghost Brain added to your app")
    print("")
    print("New endpoints available:")
    print("  POST /api/ghost/think - Make a decision")
    print("  GET  /api/ghost/status - Brain status")
    print("  GET  /api/ghost/memory - Decision history")
    print("")
    print("Run: python3 shoparound_professional.py")
    print("Then test: curl -X POST http://localhost:5000/api/ghost/think -H 'Content-Type: application/json' -d '{\"objective\":\"Launch product\",\"risk_score\":0.3}'")

python3 add_ghost.py

