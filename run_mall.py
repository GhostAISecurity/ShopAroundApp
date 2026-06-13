#!/usr/bin/env python3
"""
Simple launcher - just runs your existing app
"""

import os
import sys

# Kill existing processes
os.system("fuser -k 5000/tcp 2>/dev/null")
os.system("pkill -f 'python3.*shoparound' 2>/dev/null")

# Import your existing app (which already has neural routes)
from shoparound_with_neural import app

if __name__ == "__main__":
    print("="*60)
    print("🛍️  YOUR ShopAround Mall (with Neural AI already included)")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=False)
