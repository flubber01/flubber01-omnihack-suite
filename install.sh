#!/bin/bash

echo "🚀 Installing OmniHack Suite on Kali Linux..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Installing..."
    sudo apt update
    sudo apt install -y nodejs npm
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Install Tailwind dependencies
npm install -D tailwindcss postcss autoprefixer

# Generate Tailwind config
npx tailwindcss init -p

# Run the development server
echo "✅ Installation complete! Starting OmniHack..."
npm run dev
