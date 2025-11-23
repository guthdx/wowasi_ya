#!/bin/bash
# Wowasi_ya Deployment Script for Ubuntu Server
# Run this on your Ubuntu server (IyeskaLLC)
#
# Usage: bash deploy.sh
#
# Prerequisites:
# - GitHub CLI authenticated (gh auth login)
# - sudo access for Cloudflare tunnel config

set -e  # Exit on error

echo "=========================================="
echo "  Wowasi_ya Deployment Script"
echo "=========================================="

# Variables
PROJECT_DIR="/home/guthdx/projects/wowasi_ya"
REPO_URL="https://github.com/guthdx/wowasi_ya.git"
PORT=8001

# Step 1: Check prerequisites
echo ""
echo "[1/7] Checking prerequisites..."

if ! command -v gh &> /dev/null; then
    echo "ERROR: GitHub CLI (gh) not installed"
    echo "Install with: sudo apt install gh"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "GitHub CLI not authenticated. Running 'gh auth login'..."
    gh auth login --web
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not installed"
    exit 1
fi

echo "✓ Prerequisites OK"

# Step 2: Clone or update repo
echo ""
echo "[2/7] Setting up repository..."

mkdir -p /home/guthdx/projects

if [ -d "$PROJECT_DIR" ]; then
    echo "Directory exists. Pulling latest changes..."
    cd "$PROJECT_DIR"
    git pull
else
    echo "Cloning repository..."
    cd /home/guthdx/projects
    gh repo clone guthdx/wowasi_ya
fi

cd "$PROJECT_DIR"
echo "✓ Repository ready at $PROJECT_DIR"

# Step 3: Set up Python virtual environment
echo ""
echo "[3/7] Setting up Python virtual environment..."

python3 -m venv .venv
source .venv/bin/activate
echo "✓ Virtual environment created"

# Step 4: Install dependencies
echo ""
echo "[4/7] Installing dependencies..."

pip install --upgrade pip
pip install -e .
echo "✓ Dependencies installed"

# Step 5: Configure environment
echo ""
echo "[5/7] Configuring environment..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your settings:"
    echo "    nano $PROJECT_DIR/.env"
    echo ""
    echo "    Required: ANTHROPIC_API_KEY"
    echo "    Recommended: Change SECRET_KEY and ADMIN_PASSWORD"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Step 6: Cloudflare tunnel configuration
echo ""
echo "[6/7] Cloudflare tunnel configuration..."

CLOUDFLARE_CONFIG="$HOME/.cloudflared/config.yml"

if [ -f "$CLOUDFLARE_CONFIG" ]; then
    if grep -q "wowasi.iyeska.net" "$CLOUDFLARE_CONFIG"; then
        echo "✓ Cloudflare tunnel already configured for wowasi.iyeska.net"
    else
        echo ""
        echo "⚠️  Add this to $CLOUDFLARE_CONFIG (before the http_status:404 line):"
        echo ""
        echo "  - hostname: wowasi.iyeska.net"
        echo "    service: http://localhost:8001"
        echo ""
        echo "Then run: sudo systemctl restart cloudflared"
        echo ""
        echo "Also add DNS CNAME record in Cloudflare:"
        echo "  Name: wowasi"
        echo "  Target: 1e02b2ec-7f02-4cf5-962f-0db3558e270c.cfargotunnel.com"
        echo ""
    fi
else
    echo "⚠️  Cloudflare config not found at $CLOUDFLARE_CONFIG"
fi

# Step 7: PM2 setup
echo ""
echo "[7/7] Setting up PM2..."

if ! command -v pm2 &> /dev/null; then
    echo "PM2 not found. Install with: sudo npm install -g pm2"
else
    # Create PM2 ecosystem file
    cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'wowasi_ya',
    script: '.venv/bin/python',
    args: '-m uvicorn wowasi_ya.main:app --host 0.0.0.0 --port 8001',
    cwd: '/home/guthdx/projects/wowasi_ya',
    env_file: '/home/guthdx/projects/wowasi_ya/.env',
    watch: false,
    instances: 1,
    autorestart: true,
    max_memory_restart: '500M'
  }]
}
EOF
    echo "✓ PM2 ecosystem.config.js created"
    echo ""
    echo "To start the service:"
    echo "  cd $PROJECT_DIR"
    echo "  pm2 start ecosystem.config.js"
    echo "  pm2 save"
fi

# Summary
echo ""
echo "=========================================="
echo "  Deployment Summary"
echo "=========================================="
echo ""
echo "Project location: $PROJECT_DIR"
echo "Port: $PORT"
echo "URL: https://wowasi.iyeska.net (after Cloudflare setup)"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your ANTHROPIC_API_KEY"
echo "  2. Configure Cloudflare tunnel (if not done)"
echo "  3. Start with: pm2 start ecosystem.config.js && pm2 save"
echo "  4. Test: curl http://localhost:8001/api/v1/health"
echo ""
echo "=========================================="
