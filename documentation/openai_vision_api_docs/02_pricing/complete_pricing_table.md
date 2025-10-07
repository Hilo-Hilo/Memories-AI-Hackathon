# Complete Pricing Table - Cheap Image Understanding Models

## Current OpenAI API Pricing (Per 1M Tokens) - Updated October 2025

| Model | Input Cost | Output Cost | Cache Read | Context Length | Release Date |
|---|---|---|---|---|---|
| **gpt-5-nano** | $0.05 | $0.40 | $0.0125 | 400,000 | Aug 2025 |
| **gpt-4.1-nano** | $0.10 | $0.40 | $0.025 | 1,047,576 | Apr 2025 |
| **gpt-4o-mini** | $0.15 | $0.60 | $0.075 | 128,000 | Jul 2024 |
| **gpt-4.1-mini** | $0.40 | $1.60 | $0.10 | 1,047,576 | Apr 2025 |
| **gpt-4.1** | $2.00 | $8.00 | $0.50 | 1,047,576 | Apr 2025 |
| **gpt-4o** | $2.50 | $10.00 | $1.25 | 128,000 | - |

## Key Observations

### Cheapest Options for Image Understanding

1. **gpt-5-nano** - **CHEAPEST** at $0.05 input / $0.40 output
2. **gpt-4.1-nano** - Second cheapest at $0.10 input / $0.40 output
3. **gpt-4o-mini** - Third cheapest at $0.15 input / $0.60 output
4. **gpt-4.1-mini** - Mid-range at $0.40 input / $1.60 output

### Cost Comparison (vs GPT-4o baseline)

- **gpt-5-nano** is 98% cheaper than gpt-4o (input tokens)
- **gpt-4.1-nano** is 96% cheaper than gpt-4o
- **gpt-4o-mini** is 94% cheaper than gpt-4o
- **gpt-4.1-mini** is 84% cheaper than gpt-4o

### Context Window Comparison

- **GPT-4.1 series:** 1,047,576 tokens (1M+ tokens) - **LARGEST**
- **GPT-5-nano:** 400,000 tokens
- **GPT-4o series:** 128,000 tokens

### Cache Pricing Benefits

All models support prompt caching for repeated inputs:
- **Cache read costs 25% of input token cost** (standard)
- **GPT-5-nano offers 90% discount** on cached inputs ($0.0125 vs $0.05)
- Significant savings for applications with repeated prompts

## Pricing Tier Multipliers

Remember that these are **Standard tier** prices. Apply these multipliers:

| Tier | Price Multiplier | Processing Time |
|---|---|---|
| **Batch API** | 50% of Standard | Up to 24 hours |
| **Flex** | 50% of Standard | Variable |
| **Standard** | 100% (base price) | Seconds |
| **Priority** | 100%+ (premium) | Fastest, SLA-backed |

## Example Cost Calculations

### Processing 1,000 images with text prompts (avg 500 tokens input, 200 tokens output per image)

| Model | Input Cost | Output Cost | Total Cost |
|---|---|---|---|
| **gpt-5-nano** | $0.025 | $0.08 | **$0.105** |
| **gpt-4.1-nano** | $0.05 | $0.08 | **$0.13** |
| **gpt-4o-mini** | $0.075 | $0.12 | **$0.195** |
| **gpt-4.1-mini** | $0.20 | $0.32 | **$0.52** |

**With Batch API (50% discount):**
- gpt-5-nano: **$0.0525**
- gpt-4.1-nano: **$0.065**
- gpt-4o-mini: **$0.0975**

## Recommendation by Use Case

| Use Case | Recommended Model | Reason |
|---|---|---|
| Maximum cost savings | gpt-5-nano | Cheapest option |
| Longest context needed | gpt-4.1-nano or gpt-4.1-mini | 1M+ token context |
| Balanced cost/performance | gpt-4o-mini | Well-tested, reliable |
| Complex vision tasks | gpt-4.1-mini | Better performance |
| Bulk processing | Any model + Batch API | 50% cost reduction |
