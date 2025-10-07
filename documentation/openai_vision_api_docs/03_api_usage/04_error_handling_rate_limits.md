# Error Handling and Rate Limits

## Common Error Codes

### 401 - Authentication Error
**Cause:** Invalid or missing API key

**Example Error:**
```json
{
  "error": {
    "message": "Incorrect API key provided",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

**Solution:**
- Verify API key is correct
- Check that key hasn't been revoked
- Ensure proper Authorization header format

### 429 - Rate Limit Error
**Cause:** Too many requests or tokens per minute

**Example Error:**
```json
{
  "error": {
    "message": "Rate limit reached for requests",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded"
  }
}
```

**Solution:**
- Implement exponential backoff
- Reduce request frequency
- Upgrade to higher tier
- Use Batch API for bulk processing

### 400 - Bad Request
**Cause:** Invalid request format or parameters

**Example Error:**
```json
{
  "error": {
    "message": "Invalid model specified",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

**Solution:**
- Verify all required parameters are present
- Check parameter types and values
- Ensure model name is correct

### 500 - Server Error
**Cause:** OpenAI server issue

**Solution:**
- Retry request after brief delay
- Check OpenAI status page
- Contact support if persistent

### 503 - Service Unavailable
**Cause:** OpenAI servers overloaded

**Solution:**
- Implement retry logic with exponential backoff
- Consider using Priority tier for critical applications

## Error Handling - Python

### Basic Error Handling
```python
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Check API key
    
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Implement backoff strategy
    
except APIError as e:
    print(f"API error: {e}")
    # Handle other API errors
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Exponential Backoff Strategy
```python
import time
from openai import OpenAI, RateLimitError

client = OpenAI()

def make_request_with_backoff(max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "user", "content": "Hello!"}]
            )
            return response
            
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise  # Re-raise on final attempt
            
            wait_time = (2 ** attempt) + 1  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"Error: {e}")
            raise

response = make_request_with_backoff()
print(response.choices[0].message.content)
```

### Retry with Tenacity Library
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, RateLimitError, APIError

client = OpenAI()

@retry(
    retry=retry_if_exception_type((RateLimitError, APIError)),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(5)
)
def make_api_call():
    return client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": "Hello!"}]
    )

try:
    response = make_api_call()
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Failed after retries: {e}")
```

## Error Handling - Node.js

### Basic Error Handling
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

try {
  const response = await openai.chat.completions.create({
    model: 'gpt-4.1-mini',
    messages: [{ role: 'user', content: 'Hello!' }],
  });
  console.log(response.choices[0].message.content);
  
} catch (error) {
  if (error.status === 401) {
    console.error('Authentication error:', error.message);
  } else if (error.status === 429) {
    console.error('Rate limit exceeded:', error.message);
  } else if (error.status >= 500) {
    console.error('Server error:', error.message);
  } else {
    console.error('API error:', error.message);
  }
}
```

### Exponential Backoff - Node.js
```javascript
async function makeRequestWithBackoff(maxRetries = 5) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await openai.chat.completions.create({
        model: 'gpt-5-nano',
        messages: [{ role: 'user', content: 'Hello!' }],
      });
      return response;
      
    } catch (error) {
      if (error.status === 429 && attempt < maxRetries - 1) {
        const waitTime = Math.pow(2, attempt) * 1000 + 1000;
        console.log(`Rate limited. Waiting ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      } else {
        throw error;
      }
    }
  }
}

const response = await makeRequestWithBackoff();
console.log(response.choices[0].message.content);
```

## Rate Limits

### Rate Limit Types

1. **Requests Per Minute (RPM)**
   - Number of API requests per minute
   
2. **Tokens Per Minute (TPM)**
   - Total tokens (input + output) per minute
   
3. **Tokens Per Day (TPD)**
   - Total tokens per day (some models)

### Rate Limits by Tier

| Tier | RPM | TPM | Notes |
|---|---|---|---|
| Free | 3 | 40,000 | Limited models |
| Tier 1 | 500 | 200,000 | After $5 spent |
| Tier 2 | 5,000 | 2,000,000 | After $50 spent |
| Tier 3 | 10,000 | 10,000,000 | After $1,000 spent |
| Tier 4 | 30,000 | 80,000,000 | After $5,000 spent |
| Tier 5 | 60,000 | 300,000,000 | After $50,000 spent |

**Note:** Limits vary by model. Check your dashboard for specific limits.

### Checking Rate Limit Headers

Response headers include rate limit information:

```python
response = client.chat.completions.create(...)

# Access response headers (if using raw HTTP)
# x-ratelimit-limit-requests: 500
# x-ratelimit-remaining-requests: 499
# x-ratelimit-limit-tokens: 200000
# x-ratelimit-remaining-tokens: 199500
```

### Rate Limit Best Practices

1. **Implement Exponential Backoff**
   - Wait longer between each retry
   - Add jitter to prevent thundering herd

2. **Batch Requests**
   - Use Batch API for non-urgent tasks
   - Process multiple items per request when possible

3. **Monitor Usage**
   - Track token consumption
   - Set up alerts for approaching limits

4. **Use Appropriate Models**
   - Choose cheaper models for simple tasks
   - Reserve expensive models for complex tasks

5. **Optimize Token Usage**
   - Use shorter prompts when possible
   - Set appropriate max_tokens
   - Use prompt caching for repeated content

## Timeout Handling

### Python with Timeout
```python
from openai import OpenAI

client = OpenAI(
    timeout=30.0,  # 30 second timeout
)

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except TimeoutError:
    print("Request timed out")
```

### Node.js with Timeout
```javascript
const openai = new OpenAI({
  timeout: 30000,  // 30 second timeout
});

try {
  const response = await openai.chat.completions.create({
    model: 'gpt-4.1-mini',
    messages: [{ role: 'user', content: 'Hello!' }],
  });
} catch (error) {
  if (error.code === 'ETIMEDOUT') {
    console.error('Request timed out');
  }
}
```

## Content Policy Violations

If content violates OpenAI's usage policies:

```python
try:
    response = client.chat.completions.create(...)
except Exception as e:
    if "content_filter" in str(e):
        print("Content was filtered due to policy violation")
        # Handle appropriately
```

## Logging and Monitoring

### Python Logging Example
```python
import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI()

try:
    logger.info("Making API request...")
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    
    logger.info(f"Tokens used: {response.usage.total_tokens}")
    logger.info(f"Model: {response.model}")
    
except Exception as e:
    logger.error(f"API request failed: {e}", exc_info=True)
    raise
```

## Production-Ready Error Handler

```python
import time
import logging
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

logger = logging.getLogger(__name__)
client = OpenAI()

def robust_api_call(messages, model="gpt-5-nano", max_retries=3):
    """
    Production-ready API call with comprehensive error handling
    """
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=30.0
            )
            
            # Log successful request
            logger.info(f"API call successful. Tokens: {response.usage.total_tokens}")
            return response
            
        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise  # Don't retry auth errors
            
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error("Rate limit exceeded after all retries")
                raise
                
        except APIError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                logger.warning(f"Server error. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"API error: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    raise Exception("Max retries exceeded")

# Usage
try:
    response = robust_api_call(
        messages=[{"role": "user", "content": "Hello!"}],
        model="gpt-5-nano"
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Failed: {e}")
```
