# Complete API Parameters Reference

## Chat Completions Endpoint

**Endpoint:** `POST https://api.openai.com/v1/chat/completions`

## Required Parameters

### `model` (string)
The model to use for completion.

**Examples:**
- `"gpt-5-nano"` - Cheapest option
- `"gpt-4.1-nano"` - Fast and cheap
- `"gpt-4o-mini"` - Balanced
- `"gpt-4.1-mini"` - High performance

### `messages` (array)
Array of message objects forming the conversation.

**Message Structure:**
```json
{
  "role": "user|assistant|system",
  "content": "string or array"
}
```

**Text-only message:**
```json
{
  "role": "user",
  "content": "Hello, how are you?"
}
```

**Vision message:**
```json
{
  "role": "user",
  "content": [
    {"type": "text", "text": "What's in this image?"},
    {
      "type": "image_url",
      "image_url": {
        "url": "https://example.com/image.jpg",
        "detail": "auto"
      }
    }
  ]
}
```

## Optional Parameters

### `max_tokens` (integer)
Maximum number of tokens to generate in the completion.

**Default:** Model-specific (typically 4096 or unlimited)

**Example:**
```python
max_tokens=500  # Limit response to 500 tokens
```

**Cost Impact:** Directly affects output token cost

### `temperature` (number, 0-2)
Controls randomness in the output.

**Range:** 0.0 to 2.0
**Default:** 1.0

- `0.0` - Deterministic, focused output
- `1.0` - Balanced creativity
- `2.0` - Maximum randomness

**Example:**
```python
temperature=0.2  # More focused, consistent responses
temperature=1.5  # More creative, varied responses
```

**Use Cases:**
- `0.0-0.3` - Factual tasks, data extraction, classification
- `0.7-1.0` - General conversation, Q&A
- `1.0-2.0` - Creative writing, brainstorming

### `top_p` (number, 0-1)
Nucleus sampling parameter. Alternative to temperature.

**Range:** 0.0 to 1.0
**Default:** 1.0

**Example:**
```python
top_p=0.9  # Consider top 90% probability mass
```

**Note:** OpenAI recommends altering `temperature` OR `top_p`, not both.

### `n` (integer)
Number of completions to generate for each prompt.

**Default:** 1

**Example:**
```python
n=3  # Generate 3 different responses
```

**Cost Impact:** Multiplies output token cost by `n`

### `stream` (boolean)
Whether to stream partial responses.

**Default:** `false`

**Example:**
```python
stream=True  # Enable streaming
```

### `stop` (string or array)
Sequences where the API will stop generating.

**Example:**
```python
stop=["\n", "END"]  # Stop at newline or "END"
stop="."  # Stop at period
```

### `presence_penalty` (number, -2.0 to 2.0)
Penalizes tokens based on whether they appear in the text so far.

**Range:** -2.0 to 2.0
**Default:** 0

- Positive values encourage new topics
- Negative values encourage staying on topic

**Example:**
```python
presence_penalty=0.6  # Encourage diverse topics
```

### `frequency_penalty` (number, -2.0 to 2.0)
Penalizes tokens based on their frequency in the text so far.

**Range:** -2.0 to 2.0
**Default:** 0

- Positive values reduce repetition
- Negative values allow more repetition

**Example:**
```python
frequency_penalty=0.5  # Reduce repetitive text
```

### `logit_bias` (map)
Modify likelihood of specific tokens appearing.

**Example:**
```python
logit_bias={
    "50256": -100,  # Prevent specific token
    "1234": 100     # Encourage specific token
}
```

### `user` (string)
Unique identifier for the end-user (for abuse monitoring).

**Example:**
```python
user="user-12345"
```

### `response_format` (object)
Specify output format.

**Options:**
- `{"type": "text"}` - Default text output
- `{"type": "json_object"}` - JSON output (must prompt for JSON)

**Example:**
```python
response_format={"type": "json_object"}
```

**Note:** When using JSON mode, you must instruct the model to produce JSON in your prompt.

### `seed` (integer)
For deterministic sampling (beta feature).

**Example:**
```python
seed=12345  # Reproducible outputs
```

### `tools` (array)
Function calling tools available to the model.

**Example:**
```python
tools=[
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }
]
```

### `tool_choice` (string or object)
Controls which tool the model should use.

**Options:**
- `"none"` - Don't call any function
- `"auto"` - Model decides (default)
- `{"type": "function", "function": {"name": "my_function"}}` - Force specific function

## Vision-Specific Parameters

### `detail` (string)
Image detail level for vision models.

**Options:**
- `"auto"` - Model decides (default)
- `"low"` - 512x512, 85 tokens (GPT-4o series)
- `"high"` - Full resolution, variable tokens

**Example:**
```python
{
    "type": "image_url",
    "image_url": {
        "url": "https://example.com/image.jpg",
        "detail": "high"
    }
}
```

**Cost Impact:**
- `low`: Fixed 85 tokens (GPT-4o series)
- `high`: Variable based on image size

## Complete Example with All Common Parameters

### Python
```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    # Required
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant that analyzes images."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in detail."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high"
                    }
                }
            ]
        }
    ],
    
    # Optional
    max_tokens=500,
    temperature=0.7,
    top_p=1.0,
    n=1,
    stream=False,
    stop=None,
    presence_penalty=0.0,
    frequency_penalty=0.0,
    user="user-12345"
)

print(response.choices[0].message.content)
```

## Response Object Structure

```python
{
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4.1-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "The image shows..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 150,
        "completion_tokens": 50,
        "total_tokens": 200
    }
}
```

### Accessing Response Data

```python
# Get the response text
content = response.choices[0].message.content

# Get token usage
prompt_tokens = response.usage.prompt_tokens
completion_tokens = response.usage.completion_tokens
total_tokens = response.usage.total_tokens

# Calculate cost (for gpt-5-nano)
input_cost = (prompt_tokens / 1_000_000) * 0.05
output_cost = (completion_tokens / 1_000_000) * 0.40
total_cost = input_cost + output_cost

print(f"Cost: ${total_cost:.6f}")
```

## Finish Reasons

- `"stop"` - Natural completion
- `"length"` - Hit max_tokens limit
- `"content_filter"` - Content filtered
- `"tool_calls"` - Model called a function
