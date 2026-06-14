#!/bin/bash
# ShopAround Deployment Script

echo "🚀 Deploying ShopAround..."

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export FLASK_APP=shoparound_professional.py
export FLASK_ENV=production

# Initialize database
python3 -c "from shoparound_professional import init_db; init_db()"

# Start the server with gunicorn
gunicorn shoparound_professional:app --bind 0.0.0.0:8000 --workers 4
