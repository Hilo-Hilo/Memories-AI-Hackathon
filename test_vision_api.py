"""
Test script for OpenAI Vision API with gpt-5-nano.

Tests to see what response format the API actually returns.
"""

import os
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not found in environment")
    exit(1)

client = OpenAI(api_key=api_key)

# Find a test image from recent session
data_dir = Path("data/sessions")
if data_dir.exists():
    # Find most recent session
    sessions = sorted(data_dir.glob("*/"), key=lambda x: x.stat().st_mtime, reverse=True)
    if sessions:
        test_session = sessions[0]
        snapshots = list((test_session / "snapshots").glob("cam_*.jpg"))
        if snapshots:
            test_image = snapshots[0]
            print(f"Using test image: {test_image}")
        else:
            print("No snapshots found")
            exit(1)
    else:
        print("No sessions found")
        exit(1)
else:
    print("No data directory found")
    exit(1)

# Read and encode image
with open(test_image, 'rb') as f:
    image_data = f.read()

base64_image = base64.b64encode(image_data).decode('utf-8')
print(f"Image encoded: {len(base64_image)} bytes")

# Test with gpt-5-nano
print("\n" + "="*60)
print("Testing gpt-5-nano...")
print("="*60)

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

try:
    response = client.chat.completions.create(
        model="gpt-5-nano",
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
        # Note: NOT setting temperature - gpt-5-nano only supports default (1)
    )
    
    print("\n✓ API call successful!")
    print(f"Model used: {response.model}")
    print(f"Tokens: {response.usage.total_tokens if response.usage else 'unknown'}")
    print(f"\nResponse content:")
    print("="*60)
    print(response.choices[0].message.content)
    print("="*60)
    
    # Try to parse as JSON
    import json
    import re
    
    content = response.choices[0].message.content
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        print("\n✓ Found JSON in response")
        result = json.loads(json_match.group())
        print(f"Parsed JSON: {json.dumps(result, indent=2)}")
    else:
        print("\n✗ No JSON found in response")
        print(f"Content type: {type(content)}")
        print(f"Content length: {len(content) if content else 0}")
        print(f"Content repr: {repr(content)}")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test with gpt-4o-mini for comparison
print("\n" + "="*60)
print("Testing gpt-4o-mini for comparison...")
print("="*60)

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
        temperature=0.1
    )
    
    print("\n✓ API call successful!")
    print(f"Model used: {response.model}")
    print(f"Tokens: {response.usage.total_tokens if response.usage else 'unknown'}")
    print(f"\nResponse content:")
    print("="*60)
    print(response.choices[0].message.content)
    print("="*60)
    
    # Try to parse as JSON
    content = response.choices[0].message.content
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        print("\n✓ Found JSON in response")
        result = json.loads(json_match.group())
        print(f"Parsed JSON: {json.dumps(result, indent=2)}")
    else:
        print("\n✗ No JSON found in response")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test complete!")
print("="*60)

