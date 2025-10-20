"""Test gpt-5-nano with simple vision prompt."""

import os
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Find test image
test_image = Path("data/sessions/d307dfad-3d37-45e1-b303-4980eddef9bb/snapshots/cam_20251019_204801.jpg")

with open(test_image, 'rb') as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')

print("="*60)
print("Test 1: Simple question (no JSON)")
print("="*60)

response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What do you see in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    max_completion_tokens=100
)

print(f"Response: '{response.choices[0].message.content}'")
print(f"Length: {len(response.choices[0].message.content)}")
print(f"Tokens used: {response.usage.total_tokens}")

print("\n" + "="*60)
print("Test 2: With 'detail' parameter")
print("="*60)

response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe what you see."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low"  # Try low detail
                    }
                }
            ]
        }
    ],
    max_completion_tokens=100
)

print(f"Response: '{response.choices[0].message.content}'")
print(f"Length: {len(response.choices[0].message.content)}")

print("\n" + "="*60)
print("Test 3: URL instead of base64")
print("="*60)

# Use a public URL instead
response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                    }
                }
            ]
        }
    ],
    max_completion_tokens=100
)

print(f"Response: '{response.choices[0].message.content}'")
print(f"Length: {len(response.choices[0].message.content)}")

