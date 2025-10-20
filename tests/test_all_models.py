"""Test all available models with base64 images to find cheapest working option."""

import os
import base64
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Find test image
test_image = Path("data/sessions/d307dfad-3d37-45e1-b303-4980eddef9bb/snapshots/cam_20251019_204801.jpg")

with open(test_image, 'rb') as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')

prompt = """Analyze this webcam image. Return JSON:
{
  "labels": {"Focused": 0.9, "HeadAway": 0.1},
  "reasoning": "explanation"
}"""

models_to_test = [
    ("gpt-4.1-nano", "$0.10/1M in, $0.40/1M out"),
    ("gpt-4.1-mini", "$0.40/1M in, $1.60/1M out"),
    ("gpt-4o-mini", "$0.15/1M in, $0.60/1M out"),
    ("gpt-5-nano", "$0.05/1M in, $0.40/1M out"),
    ("gpt-5-mini", "$0.10/1M in, $0.40/1M out"),
]

results = []

for model_name, pricing in models_to_test:
    print(f"\n{'='*70}")
    print(f"Testing: {model_name} ({pricing})")
    print(f"{'='*70}")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
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
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        if content and len(content) > 0:
            print(f"✅ WORKS! Response length: {len(content)} chars")
            print(f"Tokens used: {tokens}")
            print(f"Content preview: {content[:150]}...")
            
            # Try to parse JSON
            try:
                data = json.loads(content)
                print(f"✅ Valid JSON! Labels: {list(data.get('labels', {}).keys())}")
                results.append({
                    "model": model_name,
                    "pricing": pricing,
                    "status": "✅ WORKS",
                    "tokens": tokens,
                    "response_length": len(content)
                })
            except:
                print(f"⚠️ Response not valid JSON")
                results.append({
                    "model": model_name,
                    "pricing": pricing,
                    "status": "⚠️ Works but invalid JSON",
                    "tokens": tokens,
                    "response_length": len(content)
                })
        else:
            print(f"❌ EMPTY RESPONSE (same as gpt-5-nano issue)")
            print(f"Tokens used: {tokens} (consuming tokens but returning nothing)")
            results.append({
                "model": model_name,
                "pricing": pricing,
                "status": "❌ EMPTY RESPONSE",
                "tokens": tokens,
                "response_length": 0
            })
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results.append({
            "model": model_name,
            "pricing": pricing,
            "status": f"❌ ERROR: {str(e)[:50]}",
            "tokens": 0,
            "response_length": 0
        })

# Summary
print(f"\n\n{'='*70}")
print("SUMMARY: Which models work with base64 images?")
print(f"{'='*70}\n")

print(f"{'Model':<20} {'Pricing':<30} {'Status':<30}")
print(f"{'-'*70}")
for result in results:
    print(f"{result['model']:<20} {result['pricing']:<30} {result['status']}")

print(f"\n{'='*70}")
print("RECOMMENDATION:")
print(f"{'='*70}")

working_models = [r for r in results if "✅ WORKS" in r['status']]
if working_models:
    # Sort by cost (rough approximation)
    cost_order = {
        "gpt-5-nano": 1,
        "gpt-4.1-nano": 2,
        "gpt-5-mini": 2.5,
        "gpt-4o-mini": 3,
        "gpt-4.1-mini": 4
    }
    working_models.sort(key=lambda x: cost_order.get(x['model'], 99))
    
    best = working_models[0]
    print(f"Best option: {best['model']}")
    print(f"Pricing: {best['pricing']}")
    print(f"Average tokens: ~{best['tokens']}")
else:
    print("❌ NO WORKING MODELS FOUND!")
    print("This suggests a fundamental issue with the GPT-5 series and base64 images.")

