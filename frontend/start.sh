#!/bin/bash
# Quick start script for Frameshift Frontend

echo "========================================"
echo "Frameshift Frontend - Quick Start"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    echo "   cd /home/ray/src/frameshift/frontend"
    exit 1
fi

# Check for API key
if [ -z "$GOOGLE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GOOGLE_API_KEY or GEMINI_API_KEY not set"
    echo "   The video editing step will fail without an API key"
    echo ""
    echo "   Set it with: export GOOGLE_API_KEY='your-api-key'"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Starting Flask server..."
echo "📱 Open http://localhost:5001 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py

