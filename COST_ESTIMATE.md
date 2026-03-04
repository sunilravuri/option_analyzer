# GLD LEAP Agent — Cost Estimate

**Schedule:** Every 15 minutes, 8:30 AM–3:00 PM CST, Monday–Friday

## Per-Run Cost Breakdown

| Component | Detail | Cost |
|---|---|---|
| Input tokens | ~25,000 tokens @ $3.00/MTok | ~$0.075 |
| Output tokens | ~800 tokens @ $15.00/MTok | ~$0.012 |
| Web searches | ~6 searches @ $0.01 each | ~$0.060 |
| **Total per run** | | **~$0.15** |

## Schedule Math

| Period | Runs | Cost |
|---|---|---|
| Per day | 26 runs (6.5 hrs ÷ 15 min) | ~$3.90 |
| Per week | 130 runs (26 × 5 days) | ~$19.50 |
| Per month | 572 runs (~22 trading days) | ~$86 |

## Range

**$75–$110/month** depending on:
- Web search count per run (up to 10 allowed; more on volatile/news-heavy days)
- Occasional retry runs triggered by rate limit (unlikely at 15-min spacing)

## Model Pricing Reference (claude-sonnet-4-6)

- Input: $3.00 / million tokens
- Output: $15.00 / million tokens
- Web search tool: $0.01 per search (web_search_20250305)
