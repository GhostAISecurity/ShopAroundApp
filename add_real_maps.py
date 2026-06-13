import re

with open("shoparound_professional.py", "r") as f:
    content = f.read()

if "from real_maps import add_real_maps" in content:
    print("✅ Maps already added")
else:
    # Add import
    new_content = content.replace(
        "from flask import Flask, request, jsonify, g, render_template_string, session",
        "from flask import Flask, request, jsonify, g, render_template_string, session\nfrom real_maps import add_real_maps"
    )
    
    # Add registration before app.run
    new_content = new_content.replace(
        'if __name__ == "__main__":',
        'app = add_real_maps(app)\n\nif __name__ == "__main__":'
    )
    
    with open("shoparound_professional.py", "w") as f:
        f.write(new_content)
    
    print("✅ Real maps added to your app")
    print("")
    print("Run: python3 shoparound_professional.py")
    print("Then open: http://localhost:5000/nearby")
