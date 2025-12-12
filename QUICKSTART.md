# Wowasi_ya Quickstart Guide

## What We Built

A **hybrid AI documentation generator** that:
- Uses **Claude API** for research (web search capability)
- Uses **Llama 3.3 70B** (local M4 Mac) for document generation
- **Saves 60-70%** on API costs vs full Claude
- **Works from anywhere** via Cloudflare Tunnels

## Next Steps

### 1. Configure Cloudflare Tunnel on Mac

You mentioned you already have a Cloudflare tunnel set up. Let's verify the configuration:

```bash
# Check your tunnel config
cat ~/.cloudflared/config.yml
```

It should look like:
```yaml
tunnel: <your-tunnel-id>
credentials-file: /Users/guthdx/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: llama.iyeska.net
    service: http://localhost:8080
  - service: http_status:404
```

If you need to add this hostname:
```bash
# Add the llama.iyeska.net route to your tunnel
cloudflared tunnel route dns <tunnel-name> llama.iyeska.net
```

### 2. Start Llama CPP Server on Mac

```bash
# Start the Llama server (bind to localhost only, Cloudflare will expose it)
llama-server \
  --model ~/path/to/bartowski_Llama-3.3-70B-Instruct-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --n-gpu-layers 35  # Adjust based on M4 GPU memory

# In another terminal, start the Cloudflare tunnel
cloudflared tunnel run <your-tunnel-name>
```

**Optional:** Set tunnel to auto-start:
```bash
cloudflared service install
```

### 3. Test the Connection

```bash
# Test locally on Mac
curl http://localhost:8080/health

# Test via Cloudflare (from anywhere)
curl https://llama.iyeska.net/health

# Should return health check response
```

### 4. Configure Ubuntu Server

On your Ubuntu server (192.168.11.20), create `.env` file:

```bash
cd /home/guthdx/projects/wowasi_ya

# Copy example
cp .env.example .env

# Edit with your settings
nano .env
```

Set these key variables:
```bash
# Generation Provider
GENERATION_PROVIDER=llamacpp
LLAMACPP_BASE_URL=https://llama.iyeska.net
LLAMACPP_FALLBACK_TO_CLAUDE=true

# Research Provider
RESEARCH_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
ENABLE_WEB_SEARCH=true

# Other settings
ENVIRONMENT=production
OUTPUT_DIR=/home/guthdx/projects/wowasi_ya/output
```

### 5. Install Dependencies

```bash
# On Ubuntu server
cd /home/guthdx/projects/wowasi_ya
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 6. Test the Integration

```bash
# Test from Ubuntu server CLI
source .venv/bin/activate
wowasi generate "Test Project" "A simple test to verify Llama integration"

# Watch the logs - you should see:
# "Using Llama CPP for document generation (via Cloudflare)"
```

### 7. Check Health Endpoint

```bash
# From Ubuntu server
curl http://localhost:8001/health

# Or via public URL
curl https://wowasi.iyeska.net/api/v1/health
```

Expected response (when Mac online):
```json
{
  "status": "healthy",
  "service": "wowasi_ya",
  "generation_provider": "llamacpp",
  "research_provider": "claude",
  "llamacpp": {
    "available": true,
    "url": "https://llama.iyeska.net",
    "fallback_enabled": true
  }
}
```

## Troubleshooting

### Mac Llama Shows Unavailable

**Check:**
```bash
# On Mac - is Llama running?
ps aux | grep llama-server

# On Mac - is tunnel running?
ps aux | grep cloudflared
cloudflared tunnel list

# Test locally
curl http://localhost:8080/health

# Test via tunnel
curl https://llama.iyeska.net/health
```

**Fix:**
- Start Llama server if not running
- Start Cloudflare tunnel if not running
- Check Mac firewall settings
- Verify `~/.cloudflared/config.yml` has correct hostname

### Documents Still Using Claude

**Check:**
```bash
# On Ubuntu, check which provider is active
curl http://localhost:8001/health | jq '.generation_provider'

# Should show "llamacpp"
```

**Fix:**
- Verify `.env` has `GENERATION_PROVIDER=llamacpp`
- Restart the Wowasi server: `systemctl restart wowasi` or restart PM2 process

### Generation Slow or Timeout

**Check:**
- Mac resources: Activity Monitor, check CPU/GPU/RAM
- Network latency: `curl -w "@-" https://llama.iyeska.net/health`
- Llama server logs on Mac

**Fix:**
- Increase `LLAMACPP_TIMEOUT` in `.env` (default: 300 seconds)
- Reduce `--n-gpu-layers` if Mac running out of memory
- Consider using smaller model (e.g., Q4_K_S instead of Q4_K_M)

## Working Remotely

### From Coffee Shop / Hotel / Conference

**Your setup works automatically!** Just ensure:
1. Mac is connected to any WiFi
2. Llama server is running
3. Cloudflare tunnel is running

The tunnel handles all routing - no VPN or network config needed.

### Mac Left at Home

**Option 1: Manual switch**
```bash
# On Ubuntu, edit .env
GENERATION_PROVIDER=claude
```

**Option 2: Auto-fallback (already configured)**
- Just let it fail health check
- Will automatically use Claude
- Health endpoint shows: `"fallback_status": "Will use Claude"`

## Monitoring

### Check System Status

```bash
# Quick health check
curl https://wowasi.iyeska.net/api/v1/health | jq

# Monitor logs (if using PM2)
pm2 logs wowasi

# Monitor logs (if using systemd)
journalctl -u wowasi -f
```

### Cost Tracking

- Check audit logs: `wowasi audit --limit 20`
- Research: ~$2-5 per project (Claude API)
- Generation: $0 (local Llama when Mac online)
- Fallback: ~$3-10 additional (when using Claude for generation)

## Next Steps

1. **Test the system** end-to-end with a real project
2. **Compare output quality** between Llama and Claude
3. **Tune Llama settings** (`--n-gpu-layers`, `temperature`, etc.)
4. **Set up monitoring** (optional: Grafana, alerts for Mac offline)
5. **Deploy to production** on Ubuntu server

## Files to Review

- `ARCHITECTURE.md` - Detailed architecture and migration guide
- `CLAUDE.md` - Updated with hybrid configuration
- `.env.example` - All configuration options
- `src/wowasi_ya/core/llm_client.py` - Provider abstraction
- `src/wowasi_ya/core/generator.py` - Updated to use abstraction

## Support

If you run into issues:
1. Check health endpoint first
2. Review logs on both Mac and Ubuntu
3. Test Llama locally before testing via tunnel
4. Verify `.env` configuration matches `.env.example`

Happy generating!
