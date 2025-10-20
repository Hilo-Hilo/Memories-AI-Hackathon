"""Test gpt-5-mini with base64 images."""

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

print("="*70)
print("Testing gpt-5-mini with base64 images")
print("="*70)

prompt = """Analyze this webcam image and return a JSON object with distraction detection labels.

Detect if the user shows:
- HeadAway: Head turned significantly away from screen (>45 degrees)
- EyesOffScreen: Eyes not looking at screen but head forward
- Absent: No face visible in frame
- MicroSleep: Eyes closed, drowsy appearance
- PhoneLikely: User appears to be looking at or holding a phone
- Focused: User engaged with screen, good posture

Return ONLY a JSON object in this format:
{
  "labels": {"LabelName": confidence, ...},
  "reasoning": "brief explanation of what you see"
}"""

# Test 1: gpt-5-mini with base64
print("\nTest 1: gpt-5-mini with base64 (no response_format)")
try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_completion_tokens=300
    )
    
    print(f"✓ Success!")
    print(f"Model: {response.model}")
    print(f"Tokens: {response.usage.total_tokens}")
    print(f"\nResponse:")
    print("="*70)
    print(response.choices[0].message.content)
    print("="*70)
    
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: gpt-5-mini with response_format
print("\n\nTest 2: gpt-5-mini with base64 + response_format json_object")
try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_completion_tokens=300,
        response_format={"type": "json_object"}
    )
    
    print(f"✓ Success!")
    print(f"Model: {response.model}")
    print(f"Tokens: {response.usage.total_tokens}")
    print(f"\nResponse:")
    print("="*70)
    print(response.choices[0].message.content)
    print("="*70)
    
    # Parse JSON
    import json
    result = json.loads(response.choices[0].message.content)
    print(f"\n✓ Valid JSON parsed!")
    print(f"Labels found: {list(result.get('labels', {}).keys())}")
    
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Check pricing
print("\n\nTest 3: Cost comparison")
print("="*70)
print(f"gpt-5-mini tokens used: {response.usage.total_tokens if 'response' in locals() else 'N/A'}")
print(f"gpt-5-mini pricing: $0.10/1M input, $0.40/1M output")
print(f"\nFor comparison:")
print(f"gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output")
print(f"gpt-5-nano pricing: $0.05/1M input, $0.40/1M output (but doesn't work with base64!)")

print("\n" + "="*70)
print("Test complete!")

