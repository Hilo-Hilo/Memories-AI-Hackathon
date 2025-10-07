# Streaming Responses

## Overview

Streaming allows you to receive partial responses as they're generated, rather than waiting for the complete response. This is useful for:

- Improving perceived latency in user interfaces
- Displaying real-time progress
- Processing long responses incrementally

## Python Streaming

### Basic Streaming Example
```python
from openai import OpenAI

client = OpenAI()

stream = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[{"role": "user", "content": "Write a short story about a robot."}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### Streaming with Vision
```python
from openai import OpenAI

client = OpenAI()

stream = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in detail."},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"}
                }
            ]
        }
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)

print()  # New line at end
```

### Complete Streaming Handler
```python
from openai import OpenAI

client = OpenAI()

def stream_response(messages, model="gpt-5-nano"):
    """
    Stream response and collect full text
    """
    full_response = ""
    
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )
    
    for chunk in stream:
        # Check if there's content in this chunk
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            print(content, end="", flush=True)
        
        # Check for finish reason
        if chunk.choices[0].finish_reason is not None:
            print(f"\n[Finished: {chunk.choices[0].finish_reason}]")
    
    return full_response

# Usage
messages = [{"role": "user", "content": "Tell me a joke."}]
response_text = stream_response(messages)
```

### Streaming with Error Handling
```python
from openai import OpenAI, APIError

client = OpenAI()

try:
    stream = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": "Hello!"}],
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
            
except APIError as e:
    print(f"\nStreaming error: {e}")
except Exception as e:
    print(f"\nUnexpected error: {e}")
```

## Node.js Streaming

### Basic Streaming Example
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

const stream = await openai.chat.completions.create({
  model: 'gpt-5-nano',
  messages: [{ role: 'user', content: 'Write a short story about a robot.' }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

### Streaming with Vision
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

const stream = await openai.chat.completions.create({
  model: 'gpt-4.1-mini',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: 'Describe this image in detail.' },
        {
          type: 'image_url',
          image_url: { url: 'https://example.com/image.jpg' },
        },
      ],
    },
  ],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}

console.log();  // New line
```

### Complete Streaming Handler - Node.js
```javascript
async function streamResponse(messages, model = 'gpt-5-nano') {
  let fullResponse = '';
  
  const stream = await openai.chat.completions.create({
    model: model,
    messages: messages,
    stream: true,
  });
  
  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    fullResponse += content;
    process.stdout.write(content);
    
    if (chunk.choices[0]?.finish_reason) {
      console.log(`\n[Finished: ${chunk.choices[0].finish_reason}]`);
    }
  }
  
  return fullResponse;
}

// Usage
const messages = [{ role: 'user', content: 'Tell me a joke.' }];
const response = await streamResponse(messages);
```

## Streaming Response Structure

Each chunk in the stream has this structure:

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion.chunk",
  "created": 1677652288,
  "model": "gpt-5-nano",
  "choices": [
    {
      "index": 0,
      "delta": {
        "content": "Hello"
      },
      "finish_reason": null
    }
  ]
}
```

**Last chunk:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion.chunk",
  "created": 1677652288,
  "model": "gpt-5-nano",
  "choices": [
    {
      "index": 0,
      "delta": {},
      "finish_reason": "stop"
    }
  ]
}
```

## Web Application Integration

### Flask + Server-Sent Events (SSE)
```python
from flask import Flask, Response, stream_with_context
from openai import OpenAI
import json

app = Flask(__name__)
client = OpenAI()

@app.route('/stream')
def stream():
    def generate():
        stream = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "Tell me a story."}],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                data = {
                    "content": chunk.choices[0].delta.content,
                    "done": False
                }
                yield f"data: {json.dumps(data)}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI + SSE
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI
import json

app = FastAPI()
client = OpenAI()

@app.get("/stream")
async def stream():
    async def generate():
        stream = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": "Tell me a story."}],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                data = {
                    "content": chunk.choices[0].delta.content,
                    "done": False
                }
                yield f"data: {json.dumps(data)}\n\n"
        
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### Frontend JavaScript (EventSource)
```javascript
const eventSource = new EventSource('/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.done) {
    console.log('Stream complete');
    eventSource.close();
  } else {
    // Append content to UI
    document.getElementById('output').textContent += data.content;
  }
};

eventSource.onerror = (error) => {
  console.error('Stream error:', error);
  eventSource.close();
};
```

## Streaming with Token Counting

```python
from openai import OpenAI
import tiktoken

client = OpenAI()
encoding = tiktoken.encoding_for_model("gpt-5-nano")

def stream_with_token_count(messages, model="gpt-5-nano"):
    """
    Stream response and count tokens in real-time
    """
    full_response = ""
    token_count = 0
    
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            
            # Count tokens in this chunk
            chunk_tokens = len(encoding.encode(content))
            token_count += chunk_tokens
            
            print(content, end="", flush=True)
    
    print(f"\n\nTotal tokens: {token_count}")
    return full_response, token_count

# Usage
messages = [{"role": "user", "content": "Write a paragraph about AI."}]
text, tokens = stream_with_token_count(messages)
```

## Streaming Best Practices

1. **Always handle the last chunk**
   - Check for `finish_reason` to know when stream is complete

2. **Use flush for real-time display**
   ```python
   print(content, end="", flush=True)
   ```

3. **Handle errors gracefully**
   - Wrap streaming in try-except blocks
   - Close streams properly on errors

4. **Buffer for UI updates**
   - Don't update UI for every single character
   - Batch updates for better performance

5. **Implement timeouts**
   - Set reasonable timeouts for streams
   - Handle timeout errors

## Streaming vs Non-Streaming

### When to Use Streaming

✅ **Use streaming when:**
- Building chat interfaces
- Displaying long-form content
- User needs to see progress
- Processing can start before completion

❌ **Don't use streaming when:**
- Need complete response for processing
- Logging/storing full responses
- Batch processing
- Response needs validation before display

### Performance Comparison

**Streaming:**
- First token: ~200-500ms
- Perceived latency: Lower
- Total time: Same as non-streaming
- Use case: Interactive UIs

**Non-streaming:**
- First token: N/A
- Perceived latency: Higher
- Total time: Same as streaming
- Use case: Batch processing, APIs

## cURL Streaming Example

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-5-nano",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }' \
  --no-buffer
```

Output will be a series of `data:` lines with JSON chunks.
