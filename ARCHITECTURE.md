# Wowasi_ya Architecture

## System Overview

Wowasi_ya is a hybrid AI documentation generator using:
- **Research:** Claude API with web search
- **Generation:** Llama 3.3 70B (local) via Cloudflare Tunnel
- **Fallback:** Automatic Claude usage when Mac unavailable

## Network Architecture

```
┌─────────────────────────────────────────────────────┐
│ M4 Mac (Anywhere with internet)                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Llama CPP Server                                 │ │
│ │ - localhost:8080                                 │ │
│ │ - Model: Llama-3.3-70B-Instruct-Q4_K_M          │ │
│ │                                                   │ │
│ │ Cloudflare Tunnel (cloudflared)                  │ │
│ │ - Public: https://llama.iyeska.net              │ │
│ │ - Target: localhost:8080                        │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↕
              Cloudflare Global Network
                        ↕
┌─────────────────────────────────────────────────────┐
│ Ubuntu Server (IYESKA - 192.168.11.20)               │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Wowasi Backend (Port 8001)                       │ │
│ │ - Research: Claude API                          │ │
│ │ - Generation: https://llama.iyeska.net          │ │
│ │                                                   │ │
│ │ Cloudflare Tunnel                                │ │
│ │ - Public: https://wowasi.iyeska.net             │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↕
                  End Users
```

### Key Benefits
- Works from **any location** (home office, coffee shop, hotel, conference)
- Mac only needs internet connection (no VPN required)
- Secure HTTPS via Cloudflare
- Automatic fallback when Mac offline

## LLM Provider Strategy

### Hybrid Architecture

**Phase 1: Research (Claude API)**
- File: `core/research.py`
- Provider: Claude API (Anthropic)
- Reason: Web search capability required
- Cost: ~$2-5 per project
- Usage: Research agents query web for current information

**Phase 2: Generation (Llama CPP Local)**
- File: `core/generator.py`
- Provider: Llama 3.3 70B via Cloudflare Tunnel
- Reason: Cost reduction (60-70%), data privacy
- Cost: $0 (local inference)
- Fallback: Claude API when Mac unavailable

### Cost Comparison

| Mode | Research | Generation | Cost per Project |
|------|----------|------------|------------------|
| Full Claude | Claude API | Claude API | $5-15 |
| Hybrid (current) | Claude API | Llama Local | $2-5 |
| Savings | - | - | 60-70% |

## Provider Abstraction Layer

### Architecture

All LLM calls go through `core/llm_client.py`:

```python
# Protocol definition
class BaseLLMClient(Protocol):
    async def generate(prompt, max_tokens, temperature) -> str
    def supports_web_search() -> bool
    async def health_check() -> bool

# Implementations
class ClaudeClient(BaseLLMClient)      # Anthropic API
class LlamaCPPClient(BaseLLMClient)    # Local via Cloudflare

# Factories
get_generation_client(settings) -> BaseLLMClient  # With fallback logic
get_research_client(settings) -> BaseLLMClient    # Always Claude for now
```

### Benefits
1. **Clean separation** - Business logic independent of provider
2. **Easy migration** - Swap providers without touching core code
3. **Testability** - Mock LLM clients in tests
4. **Flexibility** - Runtime provider switching

## Configuration

### Environment Variables

```bash
# Generation Provider
GENERATION_PROVIDER=llamacpp  # or "claude" for full Claude mode
LLAMACPP_BASE_URL=https://llama.iyeska.net
LLAMACPP_MODEL=Llama-3.3-70B-Instruct-Q4_K_M
LLAMACPP_TIMEOUT=300
LLAMACPP_FALLBACK_TO_CLAUDE=true

# Research Provider (fixed)
RESEARCH_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
ENABLE_WEB_SEARCH=true
```

### Fallback Behavior

```python
# Generation client factory logic
if GENERATION_PROVIDER == "llamacpp":
    llama = LlamaCPPClient(LLAMACPP_BASE_URL)
    if llama.health_check():
        return llama  # Use Llama
    elif LLAMACPP_FALLBACK_TO_CLAUDE:
        return ClaudeClient()  # Fallback
    else:
        raise Error  # Fail hard
else:
    return ClaudeClient()  # Explicit Claude mode
```

## Health Monitoring

### Health Check Endpoint

```bash
# Check system health
curl https://wowasi.iyeska.net/api/v1/health
```

Response when Mac available:
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

Response when Mac offline:
```json
{
  "status": "healthy",
  "service": "wowasi_ya",
  "generation_provider": "llamacpp",
  "research_provider": "claude",
  "llamacpp": {
    "available": false,
    "url": "https://llama.iyeska.net",
    "fallback_enabled": true,
    "fallback_status": "Will use Claude",
    "message": "Mac Llama server unreachable. Ensure Mac is online with Cloudflare tunnel running."
  }
}
```

## Data Flow

### Complete Project Generation

```
1. User Input
   ↓
2. Agent Discovery (local)
   - Parse keywords
   - Match domains
   - Generate agent definitions
   ↓
3. Privacy Check (local)
   - Scan for PII/PHI
   - User approval gate
   ↓
4. Research (Claude API)
   - Execute research agents
   - Web search for current info
   - Compile findings
   ↓
5. Generation (Llama via Cloudflare OR Claude fallback)
   - Generate 15 documents in 5 batches
   - Use research context
   - Maintain consistency
   ↓
6. Quality Check (local)
   - Cross-reference validation
   - Completeness check
   ↓
7. Output (local)
   - Write to filesystem
   - Optional: Obsidian vault
   - Optional: Git commit
```

## Future Migration Paths

### Research Layer

To swap Claude for another provider with web search:

1. **Add new client** in `llm_client.py`:
```python
class PerplexityClient(BaseLLMClient):
    def supports_web_search(self) -> bool:
        return True

    async def generate(self, prompt, max_tokens, temperature):
        # Call Perplexity API
        ...
```

2. **Update factory**:
```python
def get_research_client(settings) -> BaseLLMClient:
    if settings.research_provider == "perplexity":
        return PerplexityClient(settings)
    return ClaudeClient(settings)  # Default
```

3. **Update config**:
```python
RESEARCH_PROVIDER=perplexity
```

**No changes needed** in `core/research.py` business logic!

### Generation Layer

Already abstracted - just change `GENERATION_PROVIDER`:
- `llamacpp` - Use local Llama
- `claude` - Use Claude API
- Future: `openai`, `anthropic-opus`, etc.

## Deployment Scenarios

### Scenario 1: At Home Office
- Mac on same network as Ubuntu server
- Low latency to Cloudflare
- Hybrid mode works perfectly

### Scenario 2: Coffee Shop / Hotel
- Mac on public WiFi
- Ubuntu server accessible via internet
- Cloudflare Tunnel connects them
- Same hybrid mode, works identically

### Scenario 3: Conference / Travel
- Mac with you, connected to WiFi
- Hybrid mode works
- If Mac asleep/offline: Auto-fallback to Claude

### Scenario 4: Mac Left at Home
- Working remotely without Mac
- Option A: Set `GENERATION_PROVIDER=claude`
- Option B: Let fallback handle it automatically

## Security Considerations

### Privacy First
- All data passes through privacy layer before API calls
- User approval gate before any external communication
- Audit logging for all LLM interactions

### Network Security
- HTTPS only (Cloudflare Tunnel)
- No exposed ports on Mac or Ubuntu
- Cloudflare handles DDoS protection

### Data Sovereignty
- Llama inference: Fully local (Mac hardware)
- Claude API: Anthropic servers (research only)
- Generated docs: Stay on your infrastructure

## Performance Characteristics

### Llama 3.3 70B Q4_K_M on M4 Mac
- **Throughput:** ~15-30 tokens/second (estimate)
- **Latency:** 3-8 seconds for typical document
- **Memory:** ~40GB RAM usage
- **GPU:** M4 GPU acceleration enabled

### Claude API
- **Throughput:** Variable (API dependent)
- **Latency:** 1-5 seconds for typical document
- **Cost:** $3-15 per million tokens

### Cloudflare Tunnel Overhead
- **Latency:** +20-50ms (negligible)
- **Reliability:** 99.9% uptime
- **Bandwidth:** Unlimited

## Troubleshooting

### Mac Llama Unavailable

**Symptoms:**
- Health check shows `llamacpp.available: false`
- Logs: "Llama CPP unavailable, falling back to Claude"

**Solutions:**
1. Check Mac is on and connected to internet
2. Verify Llama CPP server running: `ps aux | grep llama`
3. Check Cloudflare tunnel: `cloudflared tunnel list`
4. Test locally: `curl http://localhost:8080/health`
5. Test via tunnel: `curl https://llama.iyeska.net/health`

### High Generation Costs

**Check:**
- Health endpoint shows which provider is being used
- Audit logs track Claude API calls
- If frequently falling back to Claude, check Mac availability

**Solutions:**
- Ensure Mac doesn't sleep: System Settings → Energy
- Keep Cloudflare tunnel running as service
- Monitor health endpoint before starting projects

### Slow Generation

**Llama:**
- Check M4 GPU layers: `--n-gpu-layers 35`
- Monitor Mac resource usage
- Ensure no other heavy processes running

**Claude:**
- Check Anthropic API status
- Review API rate limits
- Consider reducing concurrent requests

## Maintenance

### Regular Tasks
- Monitor Mac disk space (models are large)
- Check Cloudflare tunnel status
- Review audit logs for API usage
- Update Llama model as new versions release

### Upgrades
- Llama model updates: Download, replace, restart server
- Claude model updates: Change `CLAUDE_MODEL` env var
- Provider additions: Implement `BaseLLMClient`, update factory

## References

- **Llama CPP:** https://github.com/ggerganov/llama.cpp
- **Cloudflare Tunnel:** https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- **Claude API:** https://docs.anthropic.com/
- **Bartowski Models:** https://huggingface.co/bartowski
