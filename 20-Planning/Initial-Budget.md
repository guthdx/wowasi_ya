# Initial Budget

## Overview

Wowasi_ya is designed to minimize costs by leveraging existing infrastructure and using pay-as-you-go API services. No significant capital investment is required for MVP.

---

## One-Time Costs

| Category | Item | Estimated Cost | Notes |
|----------|------|----------------|-------|
| Infrastructure | None | $0 | Using existing Proxmox setup |
| Software | None | $0 | Open-source stack |
| Development | Time investment | $0 (self) | Building in-house |
| **Total One-Time** | | **$0** | |

---

## Recurring Costs (Monthly)

### API Costs

| Service | Usage Estimate | Unit Cost | Monthly Est. |
|---------|---------------|-----------|--------------|
| Claude Sonnet 4 - Input | ~1M tokens | $3/M tokens | $3.00 |
| Claude Sonnet 4 - Output | ~600K tokens | $15/M tokens | $9.00 |
| Claude Web Search | ~100 searches | $10/1K searches | $1.00 |
| **API Subtotal** | | | **~$13.00** |

*Estimates based on ~10 projects/month, 15 documents each*

### Infrastructure Costs

| Item | Cost | Notes |
|------|------|-------|
| Electricity (incremental) | ~$5-10 | VM running 24/7 |
| Storage | $0 | Using existing capacity |
| Network | $0 | Using existing connection |
| **Infrastructure Subtotal** | | **~$5-10** |

### Total Monthly Operating Cost

| Category | Amount |
|----------|--------|
| API Costs | ~$13 |
| Infrastructure | ~$5-10 |
| **Total Monthly** | **~$18-23** |

---

## Cost Scenarios

### Light Usage (5 projects/month)
- API: ~$7/month
- Infrastructure: ~$5/month
- **Total: ~$12/month**

### Moderate Usage (10 projects/month)
- API: ~$13/month
- Infrastructure: ~$7/month
- **Total: ~$20/month**

### Heavy Usage (25 projects/month)
- API: ~$30/month
- Infrastructure: ~$10/month
- **Total: ~$40/month**

---

## Cost Optimization Strategies

| Strategy | Potential Savings | Notes |
|----------|------------------|-------|
| Batch API | 50% on API costs | Process during off-peak |
| Prompt caching | Up to 90% on cached prompts | Reuse common context |
| Haiku for drafts | ~70% on draft generation | Use cheaper model for iteration |
| Local search backup | Reduce web search costs | Self-hosted SearXNG for some queries |

---

## Budget Uncertainty

| Item | Confidence | Notes |
|------|------------|-------|
| API pricing | Medium | Anthropic could change pricing |
| Usage volume | Low | Depends on actual project load |
| Infrastructure | High | Known, existing setup |

---

## Comparison: Build vs. Manual

| Approach | Time/Project | Monthly Cost (10 projects) |
|----------|--------------|---------------------------|
| Manual documentation | 4-8 hours | $0 (but ~40-80 hours labor) |
| Wowasi_ya | 15-30 minutes | ~$20 |

**Break-even:** If your time is worth more than ~$0.50/hour, Wowasi_ya saves money.
