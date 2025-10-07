# Vision API Complete Examples

## Basic Image Understanding

### Python - Image URL
```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg"
                    }
                }
            ]
        }
    ],
    max_tokens=300
)

print(response.choices[0].message.content)
```

### Python - Base64 Encoded Image
```python
import base64
from openai import OpenAI

client = OpenAI()

# Read and encode image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_path = "path/to/your/image.jpg"
base64_image = encode_image(image_path)

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    max_tokens=300
)

print(response.choices[0].message.content)
```

### Node.js - Image URL
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

const response = await openai.chat.completions.create({
  model: 'gpt-4.1-mini',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: "What's in this image?" },
        {
          type: 'image_url',
          image_url: {
            url: 'https://example.com/image.jpg',
          },
        },
      ],
    },
  ],
  max_tokens: 300,
});

console.log(response.choices[0].message.content);
```

### Node.js - Base64 Encoded Image
```javascript
import OpenAI from 'openai';
import fs from 'fs';

const openai = new OpenAI();

// Read and encode image
function encodeImage(imagePath) {
  const imageBuffer = fs.readFileSync(imagePath);
  return imageBuffer.toString('base64');
}

const imagePath = 'path/to/your/image.jpg';
const base64Image = encodeImage(imagePath);

const response = await openai.chat.completions.create({
  model: 'gpt-4.1-mini',
  messages: [
    {
      role: 'user',
      content: [
        { type: 'text', text: "What's in this image?" },
        {
          type: 'image_url',
          image_url: {
            url: `data:image/jpeg;base64,${base64Image}`,
          },
        },
      ],
    },
  ],
  max_tokens: 300,
});

console.log(response.choices[0].message.content);
```

## Multiple Images

### Python
```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Compare these two images. What are the differences?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image1.jpg"}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image2.jpg"}
                }
            ]
        }
    ],
    max_tokens=500
)

print(response.choices[0].message.content)
```

## Image Detail Levels

### Python - Low Detail (Faster, Cheaper)
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What color is this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "low"  # 85 tokens fixed cost
                    }
                }
            ]
        }
    ]
)
```

### Python - High Detail (More Accurate)
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Read all the text in this image."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/document.jpg",
                        "detail": "high"  # Variable cost based on image size
                    }
                }
            ]
        }
    ]
)
```

## Common Vision Tasks

### OCR (Optical Character Recognition)
```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all text from this image. Preserve formatting."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/document.jpg",
                        "detail": "high"
                    }
                }
            ]
        }
    ],
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### Image Captioning
```python
response = client.chat.completions.create(
    model="gpt-5-nano",  # Cheapest option for captioning
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Write a detailed caption for this image."},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/photo.jpg"}
                }
            ]
        }
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
```

### Object Detection/Counting
```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "How many people are in this image? Describe their positions."},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/crowd.jpg"}
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

### Visual Question Answering
```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What brand of car is shown in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/car.jpg"}
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

## Structured Output with Vision

### Python - JSON Mode
```python
import json

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": "Extract structured data from images. Return valid JSON only."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract: product_name, price, description"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/product.jpg"}
                }
            ]
        }
    ],
    response_format={"type": "json_object"}
)

data = json.loads(response.choices[0].message.content)
print(data)
```

## Multi-turn Conversation with Images

### Python
```python
messages = [
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

# First request
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

# Add assistant's response to conversation
messages.append({
    "role": "assistant",
    "content": response.choices[0].message.content
})

# Follow-up question (no need to send image again)
messages.append({
    "role": "user",
    "content": "What colors are prominent?"
})

# Second request
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

print(response.choices[0].message.content)
```

## Cost-Optimized Example

```python
# Use cheapest model for simple tasks
response = client.chat.completions.create(
    model="gpt-5-nano",  # $0.05 per 1M input tokens
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Classify this image: indoor or outdoor?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "low"  # Use low detail for simple tasks
                    }
                }
            ]
        }
    ],
    max_tokens=10  # Limit output tokens for classification
)

print(response.choices[0].message.content)
```
