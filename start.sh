#!/bin/bash

echo "🔧 UK Lending Risk Dashboard - Startup"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "preprocess.py" ]; then
    echo "❌ Error: preprocess.py not found. Run this script from the Dashboard directory."
    exit 1
fi

echo "1️⃣  Running preprocessing..."
python3 preprocess.py

if [ ! -f "dashboard_data.json" ]; then
    echo "❌ Error: dashboard_data.json was not created."
    exit 1
fi

echo ""
echo "✅ Data preprocessing complete!"
echo ""
echo "2️⃣  Starting web server..."
echo "📖 Open your browser to: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m http.server 8000
