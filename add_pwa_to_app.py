import re

# Add PWA manifest link to the main HTML
with open("shoparound_professional.py", "r") as f:
    content = f.read()

# Add manifest link if not present
if '<link rel="manifest"' not in content:
    new_content = content.replace(
        '<head>',
        '<head>\n    <link rel="manifest" href="/static/manifest.json">\n    <meta name="theme-color" content="#1f8a4c">\n    <link rel="apple-touch-icon" href="/static/icon-192.png">'
    )
    with open("shoparound_professional.py", "w") as f:
        f.write(new_content)
    print("✅ PWA manifest added to app")
else:
    print("⚠️ PWA manifest already present")
