# Deployment Guide

## Server Infrastructure

Wowasi_ya runs on port **8001** to avoid conflicts with existing services:
- 3333: Stoic Indian
- 5678: n8n
- 8088: RECAP Search

## Quick Start (Docker)

```bash
# 1. Copy environment file and configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 2. Build and run
docker compose up -d

# 3. Check status
docker compose logs -f
```

## Cloudflare Tunnel Setup (iyeska.net)

To expose Wowasi_ya at `wowasi.iyeska.net`:

### 1. Edit tunnel config
```bash
sudo nano ~/.cloudflared/config.yml
```

Add before the catch-all rule:
```yaml
  - hostname: wowasi.iyeska.net
    service: http://localhost:8001
```

Full config should look like:
```yaml
tunnel: 1e02b2ec-7f02-4cf5-962f-0db3558e270c
ingress:
  - hostname: n8n.iyeska.net
    service: http://localhost:5678
  - hostname: recap.iyeska.net
    service: http://localhost:8088
  - hostname: stoic.iyeska.net
    service: http://localhost:3333
  - hostname: wowasi.iyeska.net
    service: http://localhost:8001
  - service: http_status:404
```

### 2. Add DNS record in Cloudflare
- Type: CNAME
- Name: wowasi
- Target: 1e02b2ec-7f02-4cf5-962f-0db3558e270c.cfargotunnel.com
- Proxy: Yes (orange cloud)

### 3. Restart tunnel
```bash
sudo systemctl restart cloudflared
```

## Running Without Docker

### Using PM2 (like n8n)

```bash
# Install dependencies
cd /path/to/wowasi_ya
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'wowasi_ya',
    script: '.venv/bin/python',
    args: '-m uvicorn wowasi_ya.main:app --host 0.0.0.0 --port 8001',
    cwd: '/path/to/wowasi_ya',
    env: {
      ANTHROPIC_API_KEY: 'your-key-here',
      ENVIRONMENT: 'production',
      SECRET_KEY: 'your-secret-key',
    }
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
```

### Using systemd (like cloudflared)

```bash
# Create service file
sudo nano /etc/systemd/system/wowasi_ya.service
```

```ini
[Unit]
Description=Wowasi_ya API Server
After=network.target

[Service]
Type=simple
User=guthdx
WorkingDirectory=/home/guthdx/wowasi_ya
Environment="PATH=/home/guthdx/wowasi_ya/.venv/bin"
Environment="ANTHROPIC_API_KEY=your-key-here"
Environment="ENVIRONMENT=production"
ExecStart=/home/guthdx/wowasi_ya/.venv/bin/python -m uvicorn wowasi_ya.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable wowasi_ya
sudo systemctl start wowasi_ya
```

## CLI Usage

The CLI works independently of the server:

```bash
# Activate venv
source .venv/bin/activate

# Generate project documentation
wowasi generate "My Project" "A detailed description of my project..."

# Just run discovery (no API calls)
wowasi discover "Project Name" "Description"

# Check for PII/PHI
wowasi privacy-check "Text that might contain john.doe@email.com or 555-123-4567"

# Start the server
wowasi serve --port 8001
```

## API Endpoints

Once running at `wowasi.iyeska.net`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/projects` | POST | Create new project |
| `/api/v1/projects` | GET | List all projects |
| `/api/v1/projects/{id}/discovery` | GET | Get discovery results |
| `/api/v1/projects/{id}/approve` | POST | Approve and start generation |
| `/api/v1/projects/{id}/status` | GET | Check generation status |
| `/api/v1/projects/{id}/result` | GET | Get generated documents |

API docs available at: `https://wowasi.iyeska.net/docs`

## Ports Reference

| Port | Service | Status |
|------|---------|--------|
| 3333 | Stoic Indian | In use |
| 5678 | n8n | In use |
| 8001 | **Wowasi_ya** | New |
| 8088 | RECAP Search | In use |
