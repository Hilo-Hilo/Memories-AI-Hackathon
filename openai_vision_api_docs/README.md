# OpenAI Vision API Documentation for Cheap Image Understanding Models

This documentation provides comprehensive information about OpenAI's cost-effective image understanding models, including GPT-5-nano, GPT-4.1-nano, GPT-4o-mini, and GPT-4.1-mini.

## Documentation Structure

### 01_models/
Contains detailed information about each model:
- `gpt-5-nano.md` - **CHEAPEST** GPT-5-nano model specifications and capabilities
- `gpt-4.1-nano.md` - GPT-4.1-nano model specifications and capabilities
- `gpt-4o-mini.md` - GPT-4o-mini model specifications and capabilities
- `gpt-4.1-mini.md` - GPT-4.1-mini model specifications and capabilities

### 02_pricing/
Contains pricing information:
- `pricing_tiers.md` - Explanation of Standard, Batch, Flex, and Priority tiers
- `complete_pricing_table.md` - Complete pricing comparison table for all cheap models

### 03_api_usage/
Contains API usage guides:
- `image_input.md` - Image input requirements, token calculation, and API syntax
- `batch_api.md` - Batch API usage for cost-effective bulk processing

## Quick Start

### Cheapest Model: GPT-5-nano ⭐
- **Cost:** $0.05 input / $0.40 output per 1M tokens
- **Context:** 400,000 tokens
- **Best for:** Maximum cost savings, summarization, classification
- **50% cheaper than GPT-4.1-nano**

### Second Cheapest: GPT-4.1-nano
- **Cost:** $0.10 input / $0.40 output per 1M tokens
- **Context:** 1,047,576 tokens (1M+)
- **Best for:** Classification, autocompletion, high-volume tasks with long context

### Most Balanced: GPT-4o-mini
- **Cost:** $0.15 input / $0.60 output per 1M tokens
- **Context:** 128,000 tokens
- **Best for:** General-purpose vision tasks, production deployments

### Best Performance: GPT-4.1-mini
- **Cost:** $0.40 input / $1.60 output per 1M tokens
- **Context:** 1,047,576 tokens
- **Best for:** Complex vision tasks, long context requirements

## Cost Savings Tips

1. **Use Batch API** for non-time-sensitive tasks (50% cost reduction)
2. **Use Flex tier** for background tasks (50% cost reduction)
3. **Enable prompt caching** for repeated prompts (75-90% cost reduction on cached portions)
4. **Choose the right detail level** for images (`low` vs `high`)
5. **Select the smallest model** that meets your requirements
6. **Use GPT-5-nano** for maximum cost savings (98% cheaper than GPT-4o)

## Cost Comparison

Processing 1,000 images (500 input tokens, 200 output tokens each):

| Model | Standard Cost | Batch API Cost | Savings |
|---|---|---|---|
| GPT-5-nano | $0.105 | $0.053 | 50% |
| GPT-4.1-nano | $0.130 | $0.065 | 50% |
| GPT-4o-mini | $0.195 | $0.098 | 50% |
| GPT-4.1-mini | $0.520 | $0.260 | 50% |

## Last Updated

October 2025

---

Created by **Manus AI**
