#!/bin/bash, run with: wsl -e bash ./build.sh

# Exit on error
set -e

echo "🔨 Building React frontend..."

# Go to frontend directory
cd frontend

# Install deps and build
npm install
npm run build

# Go back to root
cd ..

# Clear old static files
rm -rf backend/static/*

# Copy new build to Flask static directory
cp -r frontend/dist/* backend/static/

echo "✅ Build complete. React files are now in Flask's /static/ directory."