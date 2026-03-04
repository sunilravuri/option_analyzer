# GLD LEAP Agent — Cost Estimate

**Schedule:** Mon–Fri, every 15 min from 8:30–9:45 AM CST, then hourly from 10 AM–2 PM CST

## Per-Run Cost Breakdown

| Component | Detail | Cost |
|---|---|---|
| Input tokens | ~25,000 tokens @ $3.00/MTok | ~$0.075 |
| Output tokens | ~800 tokens @ $15.00/MTok | ~$0.012 |
| Web searches | ~6 searches @ $0.01 each | ~$0.060 |
| **Total per run** | | **~$0.15** |

## Schedule Math

| Window | Times (CST) | Runs/day |
|---|---|---|
| Every 15 min | 8:30, 8:45, 9:00, 9:15, 9:30, 9:45 AM | 6 |
| Every 1 hour | 10 AM, 11 AM, 12 PM, 1 PM, 2 PM | 5 |
| **Total** | | **11 runs/day** |

| Period | Runs | Cost |
|---|---|---|
| Per day | 11 runs | ~$1.65 |
| Per week | 55 runs (11 × 5 days) | ~$8.25 |
| Per month | 242 runs (~22 trading days) | ~$36 |

## Range

**$30–$45/month** depending on:
- Web search count per run (up to 10 allowed; more on volatile/news-heavy days)
- Occasional retry runs triggered by rate limit

## Model Pricing Reference (claude-sonnet-4-6)

- Input: $3.00 / million tokens
- Output: $15.00 / million tokens
- Web search tool: $0.01 per search (web_search_20250305)
