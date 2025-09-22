#!/bin/bash

# WSDL to Swagger Converter Startup Script

echo "🚀 Starting WSDL to Swagger Converter..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/pyvenv.cfg" ] || [ requirements.txt -nt venv/pyvenv.cfg ]; then
    echo "📚 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the application
echo "🌐 Starting web server..."
echo "📱 Open your browser and navigate to: http://localhost:5000"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

python app.py
