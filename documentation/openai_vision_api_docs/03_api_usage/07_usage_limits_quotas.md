# Usage Limits and Quotas

## Overview

OpenAI enforces several types of limits to ensure fair usage and system stability:

1. **Rate Limits** - Requests/tokens per minute
2. **Usage Quotas** - Monthly spending limits
3. **Model-specific limits** - Varies by model
4. **Image limits** - Size and count restrictions

## Rate Limit Tiers

### Tier Progression

Your tier is determined by total spend across your organization:

| Tier | Spend Required | Typical RPM | Typical TPM |
|---|---|---|---|
| **Free** | $0 | 3 | 40,000 |
| **Tier 1** | $5+ | 500 | 200,000 |
| **Tier 2** | $50+ | 5,000 | 2,000,000 |
| **Tier 3** | $1,000+ | 10,000 | 10,000,000 |
| **Tier 4** | $5,000+ | 30,000 | 80,000,000 |
| **Tier 5** | $50,000+ | 60,000 | 300,000,000 |

**Note:** Exact limits vary by model. Check your dashboard for specific limits.

### Rate Limit Types

**RPM (Requests Per Minute)**
- Number of API calls per minute
- Applies to all endpoints

**TPM (Tokens Per Minute)**
- Total tokens (input + output) per minute
- Calculated across all requests

**TPD (Tokens Per Day)**
- Some models have daily token limits
- Less common than RPM/TPM

**IPM (Images Per Minute)**
- For vision models
- Typically 50-100 images per minute

## Image-Specific Limits

### File Size Limits
- **Maximum file size:** 20 MB per image
- **Supported formats:** PNG, JPEG, WEBP, non-animated GIF

### Request Limits
- **Maximum images per request:** 500 images
- **Maximum total image bytes per request:** 50 MB

### Resolution Limits
- **Low detail:** 512px × 512px
- **High detail:** Up to 768px (short side) × 2000px (long side)

## Checking Your Limits

### Via Dashboard
1. Go to [https://platform.openai.com/account/limits](https://platform.openai.com/account/limits)
2. View current tier and limits
3. See usage statistics

### Via API Response Headers

```python
import requests

response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-5-nano",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)

# Check rate limit headers
print(f"RPM Limit: {response.headers.get('x-ratelimit-limit-requests')}")
print(f"RPM Remaining: {response.headers.get('x-ratelimit-remaining-requests')}")
print(f"TPM Limit: {response.headers.get('x-ratelimit-limit-tokens')}")
print(f"TPM Remaining: {response.headers.get('x-ratelimit-remaining-tokens')}")
```

## Managing Rate Limits

### Strategy 1: Exponential Backoff
```python
import time
from openai import OpenAI, RateLimitError

client = OpenAI()

def make_request_with_backoff(messages, max_retries=5):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="gpt-5-nano",
                messages=messages
            )
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + 1
            print(f"Rate limited, waiting {wait_time}s...")
            time.sleep(wait_time)
```

### Strategy 2: Token Bucket
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        now = time.time()
        
        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # If at limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                print(f"Rate limit reached, waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                self.wait_if_needed()  # Recursive check
        
        # Record this request
        self.requests.append(now)

# Usage
limiter = RateLimiter(max_requests=500)  # 500 RPM

for i in range(1000):
    limiter.wait_if_needed()
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": f"Request {i}"}]
    )
```

### Strategy 3: Parallel Processing with Limits
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import time

client = OpenAI()

def process_item(item, limiter):
    limiter.wait_if_needed()
    
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": item}]
    )
    
    return response.choices[0].message.content

# Process 1000 items with rate limiting
items = [f"Process item {i}" for i in range(1000)]
limiter = RateLimiter(max_requests=500)  # 500 RPM

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(process_item, item, limiter)
        for item in items
    ]
    
    for future in as_completed(futures):
        result = future.result()
        print(result)
```

## Usage Quotas

### Monthly Spending Limits

Set spending limits to prevent unexpected bills:

1. Go to [https://platform.openai.com/account/billing/limits](https://platform.openai.com/account/billing/limits)
2. Set monthly budget cap
3. Set email notification thresholds

### Monitoring Usage

```python
from openai import OpenAI

client = OpenAI()

# Get current usage (requires appropriate permissions)
# Note: This endpoint may not be available in all SDKs
# Check dashboard for detailed usage statistics
```

### Cost Tracking

```python
class CostTracker:
    def __init__(self):
        self.total_cost = 0.0
        self.model_costs = {
            "gpt-5-nano": {"input": 0.05, "output": 0.40},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
        }
    
    def track_request(self, model, prompt_tokens, completion_tokens):
        if model not in self.model_costs:
            print(f"Warning: Unknown model {model}")
            return
        
        input_cost = (prompt_tokens / 1_000_000) * self.model_costs[model]["input"]
        output_cost = (completion_tokens / 1_000_000) * self.model_costs[model]["output"]
        request_cost = input_cost + output_cost
        
        self.total_cost += request_cost
        
        print(f"Request cost: ${request_cost:.6f}")
        print(f"Total cost: ${self.total_cost:.4f}")
        
        return request_cost

# Usage
tracker = CostTracker()

response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": "Hello!"}]
)

tracker.track_request(
    model="gpt-5-nano",
    prompt_tokens=response.usage.prompt_tokens,
    completion_tokens=response.usage.completion_tokens
)
```

## Batch API Limits

- **No rate limits** on batch processing
- **24-hour completion window**
- **50% cost discount**
- Ideal for high-volume processing

## Best Practices

### 1. Choose the Right Model
```python
# Simple task? Use cheapest model
model = "gpt-5-nano"  # $0.05 input

# Complex task? Use better model
model = "gpt-4.1-mini"  # $0.40 input
```

### 2. Optimize Token Usage
```python
# Set max_tokens to prevent waste
response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": "Classify: positive or negative"}],
    max_tokens=5  # Only need 1 word
)
```

### 3. Use Batch API for Bulk Tasks
```python
# Instead of 10,000 individual requests...
# Use Batch API for 50% savings
```

### 4. Implement Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_response(prompt):
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Repeated prompts use cache
result1 = get_cached_response("What is 2+2?")
result2 = get_cached_response("What is 2+2?")  # Uses cache, no API call
```

### 5. Monitor and Alert
```python
import smtplib

def send_alert(message):
    # Send email/SMS alert when approaching limits
    pass

def check_usage(tracker, threshold=100.0):
    if tracker.total_cost > threshold:
        send_alert(f"Usage exceeded ${threshold}")
```

## Increasing Your Limits

1. **Spend more** - Automatic tier upgrades
2. **Contact support** - Request limit increases
3. **Use Batch API** - No rate limits
4. **Upgrade to Priority tier** - Higher limits + SLA

## Common Limit Errors

### 429 Rate Limit Error
```json
{
  "error": {
    "message": "Rate limit reached for requests",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded"
  }
}
```

**Solution:** Implement exponential backoff

### 429 Token Limit Error
```json
{
  "error": {
    "message": "Rate limit reached for tokens",
    "type": "tokens_limit_error"
  }
}
```

**Solution:** Reduce tokens per request or request frequency

### Quota Exceeded
```json
{
  "error": {
    "message": "You exceeded your current quota",
    "type": "insufficient_quota"
  }
}
```

**Solution:** Add payment method or increase quota
