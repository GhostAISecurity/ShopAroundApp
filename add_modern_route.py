import re

with open("shoparound_professional.py", "r") as f:
    content = f.read()

# Check if route already exists
if "@app.route('/modern')" in content:
    print("✅ Modern route already exists")
else:
    # Find where to insert the new route (before the last @app.route or before if __name__)
    with open("modern_home.html", "r") as html_file:
        modern_html = html_file.read()
    
    # Escape the HTML for Python string
    modern_html_escaped = modern_html.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    
    new_route = f'''
@app.route('/modern')
def modern_home():
    from flask import render_template_string
    return render_template_string(\"\"\"{modern_html}\"\"\")
'''
    
    # Insert before the if __name__ block
    new_content = content.replace(
        "if __name__ == \"__main__\":",
        f"{new_route}\n\nif __name__ == \"__main__\":"
    )
    
    with open("shoparound_professional.py", "w") as f:
        f.write(new_content)
    
    print("✅ Modern UI added at /modern")

print("Your original homepage at / remains UNCHANGED")
