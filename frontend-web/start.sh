#!/bin/bash
# HaliCred Frontend Startup Script

echo "🚀 Starting HaliCred Frontend Development Server"
echo "📍 URL: http://localhost:5173"
echo "🔧 Mode: Development"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
npm run dev
