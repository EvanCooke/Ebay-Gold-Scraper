#!/bin/bash
# Deploy script for MeltWise

echo "🚀 Starting deployment..."

# Activate virtual environment
source /root/Ebay-Gold-Scraper/production_env/bin/activate

# Build frontend
echo "📦 Building frontend..."
cd /root/Ebay-Gold-Scraper/frontend
npm run build

# Copy build files to nginx directory
echo "📋 Copying files to web directory..."
sudo mkdir -p /var/www/meltwise.com
sudo cp -r dist/* /var/www/meltwise.com/

# Install/update backend dependencies
echo "🔧 Installing backend dependencies..."
cd /root/Ebay-Gold-Scraper/backend
pip install -r requirements.txt

# Restart backend service
echo "🔄 Restarting backend service..."
sudo systemctl restart meltwise-backend

# Check service status
if sudo systemctl is-active --quiet meltwise-backend; then
    echo "✅ Backend service is running"
else
    echo "❌ Backend service failed to start"
    sudo systemctl status meltwise-backend
    sudo journalctl -u meltwise-backend --no-pager -n 20
fi

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

# Test the API endpoint
echo "🧪 Testing API endpoint..."
sleep 2
if curl -s http://localhost:5000/api/listings > /dev/null; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding"
fi

echo "✅ Deployment complete!"
echo "🌐 Site should be available at: https://meltwise.com"