import re

with open("shoparound_professional.py", "r") as f:
    content = f.read()

# Fix the import order
new_content = re.sub(
    r'from online_shops import add_online_shops\nfrom real_maps import add_real_maps',
    'from real_maps import add_real_maps\nfrom online_shops import add_online_shops',
    content
)

with open("shoparound_professional.py", "w") as f:
    f.write(new_content)

print("✅ Imports fixed")
