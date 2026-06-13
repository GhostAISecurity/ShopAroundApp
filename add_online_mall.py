import re

with open("shoparound_professional.py", "r") as f:
    content = f.read()

if "from online_shops import add_online_shops" in content:
    print("✅ Online Mall already added")
else:
    # Add import
    new_content = content.replace(
        "from real_maps import add_real_maps",
        "from real_maps import add_real_maps\nfrom online_shops import add_online_shops"
    )
    
    # Add registration
    new_content = new_content.replace(
        "app = add_real_maps(app)",
        "app = add_real_maps(app)\napp = add_online_shops(app)"
    )
    
    with open("shoparound_professional.py", "w") as f:
        f.write(new_content)
    
    print("✅ Online Mall added to your app")
    print("")
    print("Run: python3 shoparound_professional.py")
    print("Then open: http://localhost:5000/mall")
