#!/usr/bin/env python3
"""
Patch registration endpoint to use correct column names
"""

import re
import os

# Find the main app file that has the registration route
app_files = ["shoparound_complete_mall.py", "shoparound_with_neural.py", "shoparound.py", "app.py"]

for filename in app_files:
    if os.path.exists(filename):
        print(f"Checking {filename}...")
        with open(filename, 'r') as f:
            content = f.read()
        
        # Look for registration route
        if 'def register' in content and '@app.route' in content:
            print(f"   ✅ Found registration route in {filename}")
            
            # Fix the INSERT statement if needed
            new_content = re.sub(
                r'INSERT INTO users\s*\([^)]*name[^)]*\)',
                'INSERT INTO users (username, email, password_hash)',
                content
            )
            
            # Also fix the placeholders
            new_content = re.sub(
                r'INSERT INTO users\s*\(\s*username\s*,\s*email\s*,\s*password_hash\s*\)\s*VALUES\s*\(\s*name\s*,',
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                new_content
            )
            
            # Write backup and new file
            if new_content != content:
                backup = filename + ".backup"
                with open(backup, 'w') as f:
                    f.write(content)
                print(f"   📁 Backup saved as {backup}")
                
                with open(filename, 'w') as f:
                    f.write(new_content)
                print(f"   ✅ Fixed registration endpoint in {filename}")
            else:
                print(f"   ℹ️ No changes needed in {filename}")
            break
    else:
        print(f"⚠️ {filename} not found")

print("\n✅ Registration fix complete!")
