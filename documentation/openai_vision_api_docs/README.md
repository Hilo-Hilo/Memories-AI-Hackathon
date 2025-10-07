# OpenAI Vision API Documentation for Cheap Image Understanding Models

Comprehensive documentation for OpenAI's most cost-effective image understanding models: GPT-5-nano, GPT-4.1-nano, GPT-4o-mini, and GPT-4.1-mini.

## Documentation Structure

### 01_models/
Detailed specifications for each model:
- **gpt-5-nano.md** - ⭐ CHEAPEST ($0.05 input / $0.40 output per 1M tokens)
- **gpt-4.1-nano.md** - Fast and cheap ($0.10 input / $0.40 output per 1M tokens)
- **gpt-4o-mini.md** - Balanced option ($0.15 input / $0.60 output per 1M tokens)
- **gpt-4.1-mini.md** - High performance ($0.40 input / $1.60 output per 1M tokens)

### 02_pricing/
Complete pricing information:
- **pricing_tiers.md** - Standard, Batch, Flex, and Priority tier explanations
- **complete_pricing_table.md** - Full pricing comparison with cost calculations

### 03_api_usage/
Comprehensive API implementation guides:
- **01_setup_authentication.md** - API key setup, installation, authentication
- **02_vision_api_examples.md** - Complete code examples for vision tasks
- **03_api_parameters.md** - Full parameter reference with examples
- **04_error_handling_rate_limits.md** - Error handling and rate limit strategies
- **05_streaming_responses.md** - Streaming implementation guide
- **06_batch_api_complete.md** - Complete Batch API workflow for 50% savings
- **07_usage_limits_quotas.md** - Usage limits, quotas, and monitoring

## Quick Start

### 1. Installation
```bash
pip install openai  # Python
npm install openai  # Node.js
```

### 2. Authentication
```python
from openai import OpenAI
client = OpenAI(api_key="your-api-key")
```

### 3. Basic Vision Request
```python
response = client.chat.completions.create(
    model="gpt-5-nano",  # Cheapest option
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"}
                }
            ]
        }
    ]
)
print(response.choices[0].message.content)
```

## Model Comparison

| Model | Input Cost | Output Cost | Context | Best For |
|---|---|---|---|---|
| **gpt-5-nano** | $0.05 | $0.40 | 400K | Maximum savings |
| **gpt-4.1-nano** | $0.10 | $0.40 | 1M+ | Long context |
| **gpt-4o-mini** | $0.15 | $0.60 | 128K | Balanced |
| **gpt-4.1-mini** | $0.40 | $1.60 | 1M+ | Complex tasks |

## Cost Savings Strategies

### 1. Use GPT-5-nano (50% cheaper than GPT-4.1-nano)
```python
model="gpt-5-nano"  # $0.05 vs $0.10 input
```

### 2. Batch API (50% discount)
```python
# Process 1000 images
# Standard: $105
# Batch: $52.50 (50% savings)
```

### 3. Prompt Caching (75-90% discount on cached portions)
```python
# Repeated prompts get 75-90% discount
```

### 4. Low Detail for Simple Tasks
```python
"image_url": {
    "url": "...",
    "detail": "low"  # 85 tokens fixed (GPT-4o series)
}
```

### 5. Set max_tokens
```python
max_tokens=50  # Limit output for classification
```

## Cost Examples

### Processing 1,000 Images (500 input + 200 output tokens each)

| Model | Standard API | Batch API | Savings |
|---|---|---|---|
| gpt-5-nano | $0.105 | $0.053 | 50% |
| gpt-4.1-nano | $0.130 | $0.065 | 50% |
| gpt-4o-mini | $0.195 | $0.098 | 50% |
| gpt-4.1-mini | $0.520 | $0.260 | 50% |

### Processing 100,000 Images with Batch API

**Using gpt-5-nano:**
- Input: 50M tokens × $0.05 = $2,500
- Output: 20M tokens × $0.40 = $8,000
- Subtotal: $10,500
- **Batch discount (50%): $5,250**

**Compared to gpt-4o:**
- Standard cost: $210,000
- **Savings: $204,750 (97% cheaper!)**

## Common Use Cases

### Image Captioning
```python
model="gpt-5-nano"  # Cheapest for captions
max_tokens=100
```

### OCR (Text Extraction)
```python
model="gpt-4.1-mini"  # Better accuracy
detail="high"  # Full resolution
```

### Image Classification
```python
model="gpt-5-nano"  # Fast and cheap
max_tokens=10  # Just need category
```

### Visual Question Answering
```python
model="gpt-4.1-mini"  # Complex reasoning
```

### Bulk Processing
```python
# Use Batch API for 50% savings
# Perfect for: tagging, captioning, analysis
```

## Key Features Covered

✅ Complete setup and authentication  
✅ Vision API with URL and Base64 images  
✅ Multiple image processing  
✅ All API parameters explained  
✅ Error handling with retry logic  
✅ Rate limit management  
✅ Streaming responses  
✅ Batch API for 50% savings  
✅ Usage limits and quotas  
✅ Cost optimization strategies  
✅ Production-ready code examples  

## Pricing Tiers

| Tier | Speed | Cost | Best For |
|---|---|---|---|
| **Batch** | 24 hours | 50% off | Bulk processing |
| **Flex** | Variable | 50% off | Background tasks |
| **Standard** | Seconds | Full price | User-facing apps |
| **Priority** | Fastest | Premium | Mission-critical |

## Support

For questions about:
- **Pricing/Billing:** [OpenAI Help Center](https://help.openai.com)
- **API Issues:** Check error handling guide
- **Rate Limits:** See usage limits documentation

## Last Updated

October 2025

---

**Created by Manus AI**

This documentation is designed for AI agents and developers to quickly understand and implement OpenAI's cheap vision models with maximum cost efficiency.
