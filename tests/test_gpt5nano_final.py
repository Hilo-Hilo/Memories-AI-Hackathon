"""Final comprehensive test of gpt-5-nano vision capabilities."""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test with public image URL (from OpenAI examples)
test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

print("Testing various configurations with gpt-5-nano...")
print("="*70)

# Test 1: Absolute minimal
print("\n1. Absolute minimal (just text + URL)")
try:
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {"type": "image_url", "image_url": {"url": test_url}}
                ]
            }
        ]
    )
    print(f"Response: '{response.choices[0].message.content}'")
    print(f"Finish reason: {response.choices[0].finish_reason}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: With system message
print("\n2. With system message")
try:
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that describes images."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                    {"type": "image_url", "image_url": {"url": test_url}}
                ]
            }
        ]
    )
    print(f"Response: '{response.choices[0].message.content}'")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Text-only (no vision) - baseline
print("\n3. Text-only baseline (no vision)")
try:
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "user", "content": "Say hello"}
        ]
    )
    print(f"Response: '{response.choices[0].message.content}'")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Try o3-mini which also supports vision
print("\n4. Try o3-mini for comparison")
try:
    response = client.chat.completions.create(
        model="o3-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": test_url}}
                ]
            }
        ]
    )
    print(f"Response: '{response.choices[0].message.content}'")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70)
print("Test complete!")

